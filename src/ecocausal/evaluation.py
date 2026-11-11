"""Evaluation and gold-standard templates. Self-created annotations != experts."""
from __future__ import annotations
import csv,json,math
from pathlib import Path
import numpy as np
from sklearn.metrics import cohen_kappa_score
from .retrieval import EvidenceRetriever
from .schema import Evidence


def retrieval_metrics(ranked:list[str],relevant:set[str],k=5)->dict:
    if not relevant:raise ValueError('Need labeled relevant evidence')
    cutoff=ranked[:k]
    recall=len(set(cutoff)&relevant)/len(relevant)
    dcg=sum((1 if doc in relevant else 0)/math.log2(i+2) for i,doc in enumerate(cutoff))
    idcg=sum(1/math.log2(i+2) for i in range(min(len(relevant),k)))
    return {f'recall@{k}':float(recall),f'ndcg@{k}':float(dcg/idcg) if idcg else 0.0}


def evaluate_retriever(evidence:list[Evidence],qrels:list[dict],*,semantic=False,rerank=False,k=5,negative_queries:list[str]|None=None):
    engine=EvidenceRetriever(evidence,semantic=semantic,rerank=rerank)
    metrics=[]
    for record in qrels:
        preds=[d.source_id for d,_ in engine.query(record['query'],top_k=k)]
        scores=retrieval_metrics(preds,set(record['relevant_ids']),k=k)
        metrics.append({'question':record['query'],'ranked_ids':preds,**scores})
    negatives=[{'query':query,'returned_ids':[d.source_id for d,_ in engine.query(query,top_k=k)]}
               for query in (negative_queries or [])]
    false_positive_rate=(sum(bool(r['returned_ids']) for r in negatives)/len(negatives)) if negatives else None
    return {'mode':'hybrid_semantic' if semantic else 'lexical_tfidf_bm25',
            'rerank_enabled':rerank,
            'questions':metrics,
            'hard_negative_queries':negatives,
            'hard_negative_false_positive_rate':false_positive_rate,
            'mean_recall':float(np.mean([r[f'recall@{k}'] for r in metrics])),
            'mean_ndcg':float(np.mean([r[f'ndcg@{k}'] for r in metrics])),
            'qrels_origin':'hand-constructed synthetic demonstrations, NOT expert-grounded'}


def make_expert_template(claim_ids:list[str],out:str|Path):
    with Path(out).open('w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f)
        writer.writerow(['claim_id','reviewer_id','evidence_grounding_1to5','causal_validity_1to5','notes'])
        for claim in claim_ids:
            for reviewer in ('', ''):
                writer.writerow([claim,reviewer,'','',''])


def score_human_ratings(path:str|Path):
    """Two real raters per claim; never fabricate missing expert judgments."""
    with Path(path).open(newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    grouped={}
    for r in rows:
        cid=r['claim_id'].strip()
        reviewer=r['reviewer_id'].strip()
        if not reviewer:
            continue
        scores=[]
        for field in ('evidence_grounding_1to5','causal_validity_1to5'):
            value=int(r[field])
            if value not in (1,2,3,4,5):
                raise ValueError('Ratings must be integers 1..5 for both criteria')
            scores.append(value)
        group=grouped.setdefault(cid,{})
        if reviewer in group:raise ValueError('Duplicate reviewer rating for same claim')
        group[reviewer]=scores
    reviewers=sorted({reviewer for group in grouped.values() for reviewer in group})
    if len(reviewers)!=2:raise ValueError('Require exactly two actual reviewers for Cohen kappa')
    if any(set(group)!=set(reviewers) for group in grouped.values()):
        raise ValueError('Every rated claim must have both reviewers')
    if len(grouped)<2:raise ValueError('At least two independently doubly-rated claims needed')
    results={}
    for col,name in enumerate(('weighted_quadratic_kappa','causal_validity_weighted_quadratic_kappa')):
        a=[group[reviewers[0]][col] for group in grouped.values()]
        b=[group[reviewers[1]][col] for group in grouped.values()]
        if len(set(a))==len(set(b))==1 and a[0]==b[0]:
            raise ValueError('Kappa undefined when both reviewers give only the same constant rating')
        score=float(cohen_kappa_score(a,b,weights='quadratic'))
        if not math.isfinite(score):
            raise ValueError('Kappa is undefined for this ratings distribution')
        results[name]=score
    return {**results,'paired_claims':len(grouped),'reviewer_ids':reviewers}

class LocalLLMJudge:
    def __init__(self,llm):self.llm=llm
    def score(self,question:str,answer:str,citations:list[Evidence]):
        sources={e.source_id:e.text[:1200] for e in citations}
        response=self.llm.json_response(
            'Act as a separate critical evaluator. Return JSON {"grounding_score":0-5,"causal_overclaim":true/false,"rationale":"..."}. Do not assume text is correct just because it is cited.',
            json.dumps({'question':question,'answer':answer,'sources':sources}))
        from pydantic import BaseModel,Field
        class Scores(BaseModel):
            grounding_score:int=Field(ge=0,le=5)
            causal_overclaim:bool
            rationale:str=Field(max_length=600)
        return Scores.model_validate(response).model_dump()
