"""Adversarial and scientific-integrity regression checks.

These are synthetic adversarial fixtures, not real-world scientific validation.
"""
import json
from pathlib import Path
import numpy as np
import pytest
from ecocausal.cli import load_evidence
from ecocausal.agents import Orchestrator, PlannerAgent, ExtractionAgent, CriticAgent
from ecocausal.schema import Evidence, Claim
from ecocausal.retrieval import EvidenceRetriever
from ecocausal.extraction import extract_claims
from ecocausal.evaluation import evaluate_retriever, score_human_ratings
from ecocausal.openalex import export_jsonl

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def corpus():
    return load_evidence(ROOT/'data/demo_evidence.jsonl')

@pytest.mark.parametrize('query',json.loads((ROOT/'data/demo_hard_negatives.json').read_text()))
def test_hard_negative_query_abstains(corpus,query):
    assert EvidenceRetriever(corpus).query(query)==[]
    report,graph,causal=Orchestrator(corpus).run(query,include_causal=True)
    assert report.status=='insufficient_evidence'
    assert not report.claim_ids
    assert not report.candidate_claims
    assert not report.cited_evidence
    assert len(graph)==0
    assert causal is None


def test_negative_benchmark_tracks_false_positives(corpus):
    negatives=json.loads((ROOT/'data/demo_hard_negatives.json').read_text())
    qrels=json.loads((ROOT/'data/demo_qrels.json').read_text())
    report=evaluate_retriever(corpus,qrels,negative_queries=negatives)
    assert report['hard_negative_false_positive_rate']==0
    assert len(report['hard_negative_queries'])==len(negatives)


def test_retriever_rejects_ambiguous_provenance(corpus):
    with pytest.raises(ValueError,match='Duplicate source_id'):
        EvidenceRetriever(corpus+[corpus[0]])


class FixedLLM:
    def __init__(self,output):self.output=output
    def json_response(self,*_):return self.output


def test_planner_prevents_topic_hijack():
    p=PlannerAgent(FixedLLM({'query':'phosphorus chlorophyll-a', 'motivation':'irrelevant'}))
    plan=p.run('Quantum tunneling in brown dwarfs')
    assert plan.query=='Quantum tunneling in brown dwarfs'
    assert 'rejected' in plan.motivation


def test_planner_invalid_output_fails_closed():
    p=PlannerAgent(FixedLLM({'query':3, 'motivation':'bad'}))
    assert p.run('Does phosphorus change chlorophyll?').query=='Does phosphorus change chlorophyll?'


def test_multiagent_llm_cannot_rewrite_unrelated_question(corpus):
    class RewriteLLM:
        def json_response(self,system,user):
            if 'planner' in system:
                return {'query':'phosphorus chlorophyll-a','motivation':'wrong subject'}
            raise AssertionError('LLM should not extract or critique evidence for off-topic rewrite')
    report,graph,_=Orchestrator(corpus,llm=RewriteLLM()).run('Quantum tunneling in brown dwarfs')
    assert report.status=='insufficient_evidence'
    assert report.cited_evidence==[] and len(graph)==0


def test_llm_quote_must_mention_both_entities(corpus):
    item=corpus[0]
    # Verbatim quote exists but supports neither alleged entity.
    proposal={'claims':[{'source_id':item.source_id,'quote':'A hypothetical lake management study',
                         'subject':'phosphorus','predicate':'is_associated_with','object':'chlorophyll-a'}]}
    assert ExtractionAgent(FixedLLM(proposal)).run([item])==[]


def test_extractor_downgrades_unsubstantiated_relation():
    e=Evidence(source_id='real:one',page=1,evidence_kind='openalex_abstract',
               source_url='https://example.org/one',text='Phosphorus and chlorophyll-a were measured at the same site.')
    proposal={'claims':[{'source_id':e.source_id,'quote':e.text,
                         'subject':'phosphorus','predicate':'is_associated_with','object':'chlorophyll-a'}]}
    claims=ExtractionAgent(FixedLLM(proposal)).run([e])
    assert len(claims)==1
    assert claims[0].predicate=='co_mentioned_with'
    assert claims[0].epistemic_status=='unverified_co_mention'


def test_offline_real_co_mentions_are_not_reported_associations():
    e=Evidence(source_id='real:one',page=1,evidence_kind='pdf_text',file_sha256='abc',
               text='Phosphorus and chlorophyll-a: both recorded in Table 1.')
    claims=extract_claims([e])
    assert len(claims)==1
    assert claims[0].epistemic_status=='unverified_co_mention'


def test_unverified_caption_cannot_support_scientific_relation():
    e=Evidence(source_id='figure:one',page=3,evidence_kind='image_caption',file_sha256='abc',
               text='Unverified automated image caption: phosphorus and chlorophyll-a levels.')
    assert extract_claims([e])==[]
    p={'claims':[{'source_id':e.source_id,'quote':e.text,'subject':'phosphorus',
                  'predicate':'is_associated_with','object':'chlorophyll-a'}]}
    assert ExtractionAgent(FixedLLM(p)).run([e])==[]


def test_no_claim_is_accepted_for_off_topic_question(corpus):
    claim=Claim(claim_id='claim:test',subject='phosphorus',predicate='co_mentioned_with',
                object='chlorophyll-a',evidence=corpus[0],quote=corpus[0].text)
    assert not CriticAgent().run('Stellar quantum mechanics',[claim],corpus[:1]).accept


def test_quote_schema_rejects_nonverbatim(corpus):
    with pytest.raises(ValueError,match='verbatim'):
        Claim(claim_id='bad',subject='phosphorus',predicate='co_mentioned_with',
              object='chlorophyll-a',evidence=corpus[0],quote='I invented a causal study')


def test_bad_extractor_json_batch_abstains(corpus):
    invalid={'claims':[{'source_id':corpus[0].source_id,'quote':'bad',
                        'subject':'x','predicate':'causes','object':'y'}]}
    assert ExtractionAgent(FixedLLM(invalid)).run(corpus[:1])==[]


def test_bad_critic_json_batch_rejects(corpus):
    claims=extract_claims(corpus[:2])
    critic=CriticAgent(FixedLLM({'accept':'unparseable','problems':{'wrong':'type'}}))
    assert not critic.run('phosphorus chlorophyll-a',claims,corpus[:2]).accept


def test_bad_critic_cannot_publish_rejected_claims(corpus):
    class RejectLLM:
        def json_response(self,system,user):
            if 'planner' in system:return {'query':'phosphorus chlorophyll-a','motivation':'same topic'}
            if 'Extract scientific relations' in system:
                src=json.loads(user)[0]
                return {'claims':[{'source_id':src['id'],'quote':src['text'],'subject':'phosphorus',
                                   'predicate':'is_associated_with','object':'chlorophyll-a'}]}
            if 'critic' in system:return {'accept':False,'problems':['Not independently verified'],'revised_query':None}
            raise AssertionError(system)
    report,graph,_=Orchestrator(corpus,llm=RejectLLM()).run('phosphorus chlorophyll-a')
    assert report.status=='insufficient_evidence'
    assert report.claim_ids==[] and report.candidate_claims==[]
    assert len(graph)==0


def test_semantic_mode_rejects_low_similarity_without_model_download(corpus):
    engine=EvidenceRetriever(corpus)
    class FakeEmbed:
        def encode(self,text,normalize_embeddings=True):return np.array([[1.,0.]],dtype='float32')
    class FakeIndex:
        def search(self,vectors,n):
            return np.full((1,n),.2,dtype='float32'),np.arange(n,dtype='int64')[None,:]
    engine.semantic=True
    engine.embedder=FakeEmbed()
    engine.index=FakeIndex()
    assert engine.query('Quantum tunneling in brown dwarfs')==[]


def test_expert_duplicate_reviews_rejected(tmp_path):
    path=tmp_path/'ratings.csv'
    path.write_text('claim_id,reviewer_id,evidence_grounding_1to5,causal_validity_1to5,notes\n'
                    'a,reviewer1,3,3,\na,reviewer1,4,4,\nb,reviewer2,4,4,\n')
    with pytest.raises(ValueError,match='Duplicate'):
        score_human_ratings(path)


def test_export_jsonl_creates_nested_destination(tmp_path,corpus):
    dest=tmp_path/'nested/dir/corpus.jsonl'
    export_jsonl(corpus,dest)
    assert len(load_evidence(dest))==len(corpus)


def test_lora_answer_only_mask_prevents_prompt_loss():
    from ecocausal.finetune import build_answer_only_tokens
    class DummyTokenizer:
        eos_token_id=9
        def __call__(self,value,add_special_tokens=False):
            return {'input_ids':[ord(c)%80+10 for c in value]}
    tok=DummyTokenizer()
    ids, labels=build_answer_only_tokens(tok,'Q','yes',max_length=128)
    assert len(ids)==len(labels)
    assert len([x for x in labels if x!=-100])==4
    assert labels[-1]==9
    assert all(x==-100 for x in labels[:-4])


def test_lora_rejects_truncated_prompt():
    from ecocausal.finetune import build_answer_only_tokens
    class DummyTokenizer:
        eos_token_id=2
        def __call__(self,value,add_special_tokens=False):return {'input_ids':[1]*len(value)}
    with pytest.raises(ValueError,match='Prompt exhausts'):
        build_answer_only_tokens(DummyTokenizer(),'long question','answer',max_length=8)


def test_expert_score_requires_complete_pair(tmp_path):
    p=tmp_path/'review.csv'
    p.write_text('claim_id,reviewer_id,evidence_grounding_1to5,causal_validity_1to5,notes\n'
                 'a,r1,1,2,\na,r2,2,3,\nb,r1,2,3,\n')
    with pytest.raises(ValueError,match='both reviewers'):
        score_human_ratings(p)


def test_expert_score_both_criteria(tmp_path):
    p=tmp_path/'review.csv'
    p.write_text('claim_id,reviewer_id,evidence_grounding_1to5,causal_validity_1to5,notes\n'
                 'a,r1,1,2,\na,r2,2,3,\nb,r1,4,1,\nb,r2,3,2,\nc,r1,5,5,\nc,r2,5,4,\n')
    result=score_human_ratings(p)
    assert -1<=result['weighted_quadratic_kappa']<=1
    assert -1<=result['causal_validity_weighted_quadratic_kappa']<=1
