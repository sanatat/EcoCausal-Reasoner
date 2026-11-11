import json
from pathlib import Path
import pytest
import numpy as np
from ecocausal.schema import Evidence,Claim
from ecocausal.cli import load_evidence
from ecocausal.extraction import entities,extract_claims
from ecocausal.retrieval import EvidenceRetriever,reciprocal_rank_fusion
from ecocausal.graph import make_graph,query_claims
from ecocausal.causal import (causal_dag,check_adjustment,sample_scm,estimate_ate,
                               intervention_experiment,true_intervention_effect)
from ecocausal.world_model import simulate_trajectory,fit_world_model
from ecocausal.evaluation import retrieval_metrics,evaluate_retriever,make_expert_template,score_human_ratings,LocalLLMJudge
from ecocausal.finetune import split_by_group,read_supervised
from ecocausal.openalex import restore_abstract
from ecocausal.agents import Orchestrator,PlannerAgent,ExtractionAgent,CriticAgent

ROOT=Path(__file__).resolve().parents[1]
@pytest.fixture
def corpus():return load_evidence(ROOT/'data/demo_evidence.jsonl')

def test_non_demo_requires_provenance():
    with pytest.raises(ValueError):Evidence(source_id='x',page=1,text='a',evidence_kind='pdf_text')

def test_demo_must_be_labeled():
    e=Evidence(source_id='x',page=1,text='a',evidence_kind='synthetic_demo')
    assert e.evidence_kind=='synthetic_demo'

def test_entities():assert {'phosphorus','chlorophyll-a'}<=entities('Phosphorus raises chlorophyll a')

def test_claims_not_automatically_causal(corpus):
    claims=extract_claims(corpus)
    assert len(claims)>1
    assert all(c.predicate=='co_mentioned_with' for c in claims)
    assert all(c.epistemic_status=='illustrative' for c in claims)

def test_retrieval_and_ranking(corpus):
    engine=EvidenceRetriever(corpus)
    hits=engine.query('zebra mussel water clarity',top_k=4)
    assert hits[0][0].source_id=='demo:zebra-a'
    assert len({h[0].source_id for h in hits})>=3

def test_invalid_retrieval_query(corpus):
    with pytest.raises(ValueError):EvidenceRetriever(corpus).query('')

def test_fusion_scores():
    scores=reciprocal_rank_fusion([[0,1],[1,0]])
    assert scores[0]==scores[1]

def test_rdf_prov_sparql(corpus,tmp_path):
    g=make_graph(extract_claims(corpus))
    rows=query_claims(g)
    assert rows and all('/source/' in r['source'] for r in rows)
    p=tmp_path/'data.ttl';g.serialize(destination=p,format='turtle')
    from rdflib import Graph
    assert len(Graph().parse(p,format='turtle'))==len(g)

def test_dag_and_adjustment():
    import networkx as nx
    assert nx.is_directed_acyclic_graph(causal_dag())
    assert check_adjustment({'land_use','temperature'})
    assert not check_adjustment({'temperature'})

def test_known_intervention_effect():
    a=sample_scm(n=3000,seed=4,do_phosphorus=.08)
    b=sample_scm(n=3000,seed=4,do_phosphorus=.12)
    assert np.allclose(b['chlorophyll_a']-a['chlorophyll_a'],true_intervention_effect())

def test_causal_estimator_recovers_true_effect():
    estimate=estimate_ate(sample_scm(n=8000,seed=5),bootstrap=50)
    assert abs(estimate['estimated_ate']-true_intervention_effect())<0.6

def test_scm_experiment():
    outcome=intervention_experiment(n=1500,bootstrap=30)
    assert outcome['scm_true_ate']==pytest.approx(3.2)
    assert outcome['observational_correlations_are_not_causal_evidence']

def test_world_model_synthetic():
    assert simulate_trajectory(steps=20,seed=2).shape==(20,3)
    r=fit_world_model(train_seeds=range(3),test_seeds=range(10,12),steps=28)
    assert r['one_step_rmse']>=0
    assert r['does_not_establish_real_ecosystem_prediction']

def test_retrieval_metrics():
    m=retrieval_metrics(['a','b','c'],{'a','c'},k=2)
    assert m['recall@2']==.5

def test_demo_evaluation(corpus):
    qrels=json.loads((ROOT/'data/demo_qrels.json').read_text())
    result=evaluate_retriever(corpus,qrels)
    assert 0<=result['mean_recall']<=1
    assert result['qrels_origin'].startswith('hand-constructed')

def test_expert_requires_real_ratings(tmp_path):
    p=tmp_path/'ratings.csv';make_expert_template(['c1','c2'],p)
    with pytest.raises(ValueError):score_human_ratings(p)

def test_lora_group_split():
    data=read_supervised(ROOT/'data/demo_lora_train.jsonl')
    a,b=split_by_group(data)
    assert {x['group_id'] for x in a}.isdisjoint({x['group_id'] for x in b})

def test_openalex_inverted_index():
    assert restore_abstract({'green':[1],'lakes':[0]})=='lakes green'

def test_offline_agent_truthful_mode(corpus):
    engine=Orchestrator(corpus)
    report,graph,scm=engine.run('phosphorus chlorophyll-a',include_causal=True)
    assert engine.mode=='deterministic_offline_baseline'
    assert len(report.agent_trace)>=6
    assert report.claim_ids
    assert len(graph)>0
    assert scm['scm_true_ate']==pytest.approx(3.2)
    assert any('synthetic demo' in s.lower() for s in report.limitations)

class FakeLLM:
    def __init__(self):self.calls=0
    def json_response(self,system,user):
        self.calls+=1
        if 'planner' in system:return {'query':'phosphorus chlorophyll-a','motivation':'look for source'}
        if 'Extract scientific relations' in system:
            ctx=json.loads(user);return {'claims':[{'source_id':ctx[0]['id'],
                    'quote':ctx[0]['text'], 'subject':'phosphorus','predicate':'is_associated_with','object':'chlorophyll-a'}]}
        if 'critic' in system:return {'accept':True,'problems':[],'revised_query':None}
        raise AssertionError(system)

def test_llm_multi_agent_with_mock(corpus):
    llm=FakeLLM();runner=Orchestrator(corpus,llm=llm)
    report,graph,_=runner.run('What about phosphorus and chlorophyll-a?')
    assert runner.mode=='llm_multi_agent'
    assert llm.calls==3
    assert len(report.claim_ids)==1
    assert len(graph)>0

def test_extractor_rejects_hallucinated_source(corpus):
    class BadLLM:
        def json_response(self,*_):return {'claims':[{'source_id':'invented','quote':'imaginary sentence',
                     'subject':'unknown','predicate':'is_associated_with','object':'imagined'}]}
    assert ExtractionAgent(BadLLM()).run(corpus[:2])==[]

def test_critic_rejects_unsupported_source(corpus):
    bad=Claim(claim_id='bad',subject='alpha',predicate='co_mentioned_with',object='beta',evidence=corpus[0])
    assert not CriticAgent().run('x',[bad],corpus[1:]).accept

def test_judge_schema_validation(corpus):
    class Good:
        def json_response(self,*_):return {'grounding_score':3,'causal_overclaim':True,'rationale':'requires evidence'}
    assert LocalLLMJudge(Good()).score('q','a',corpus[:1])['grounding_score']==3
    class Bad:
        def json_response(self,*_):return {'grounding_score':99,'causal_overclaim':False,'rationale':'bad'}
    with pytest.raises(ValueError):LocalLLMJudge(Bad()).score('q','a',corpus[:1])


def test_unrelated_query_does_not_retrieve_arbitrary_documents(corpus):
    assert EvidenceRetriever(corpus).query('quantum tunneling in brown dwarfs') == []


def test_unrelated_question_must_abstain(corpus):
    report,graph,_=Orchestrator(corpus).run('quantum tunneling in brown dwarfs')
    assert report.status=='insufficient_evidence'
    assert report.cited_evidence==[]
    assert report.candidate_claims==[]
    assert len(graph)<=1


def test_candidate_relation_needs_claim_and_quote(corpus):
    r,g,_=Orchestrator(corpus).run('phosphorus chlorophyll-a')
    assert r.candidate_claims
    assert all(c.quote for c in r.candidate_claims)
    from ecocausal.graph import EC
    assert list(g.triples((None,EC.supportingQuote,None)))


def test_critic_abstains_when_retrieved_evidence_has_no_relation(corpus):
    candidate=corpus[:1]
    result=CriticAgent().run('Does this establish causation?',[],candidate)
    assert not result.accept


def test_llm_predicate_cannot_silently_assert_causation(corpus):
    class Unsafe:
        def json_response(self,*_):return {'claims':[{'source_id':corpus[0].source_id,
            'quote':corpus[0].text[:30], 'subject':'phosphorus',
            'predicate':'causes','object':'chlorophyll-a'}]}
    assert ExtractionAgent(Unsafe()).run(corpus[:1])==[]
