"""Command-line interface. Offline demo requires no network or model weights."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from .schema import Evidence
from .agents import Orchestrator
from .graph import export_graph
from .causal import intervention_experiment
from .world_model import fit_world_model
from .evaluation import evaluate_retriever,make_expert_template
from .openalex import search_abstracts,export_jsonl
from .ingestion import pdf_ingest,csv_ingest

ROOT=Path(__file__).resolve().parents[2]

def load_evidence(path:str|Path)->list[Evidence]:
    return [Evidence.model_validate_json(line) for line in Path(path).read_text(encoding='utf8').splitlines() if line.strip()]

def write_json(obj,path):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf8')


def main(argv=None):
    p=argparse.ArgumentParser(prog='ecocausal',description='Evidence-grounded scientific AI research prototype')
    sub=p.add_subparsers(dest='action',required=True)
    d=sub.add_parser('demo');d.add_argument('--query',default='Does reducing phosphorus change chlorophyll-a in lakes?');d.add_argument('--corpus',default=str(ROOT/'data/demo_evidence.jsonl'))
    d.add_argument('--output',default='results/demo');d.add_argument('--llm',action='store_true');d.add_argument('--model',default='qwen2.5:3b')
    d.add_argument('--semantic',action='store_true');d.add_argument('--rerank',action='store_true')
    a=sub.add_parser('evaluate');a.add_argument('--corpus',default=str(ROOT/'data/demo_evidence.jsonl'))
    a.add_argument('--qrels',default=str(ROOT/'data/demo_qrels.json'));a.add_argument('--hard-negatives',default=str(ROOT/'data/demo_hard_negatives.json'));a.add_argument('--output',default='results/retrieval.json')
    a.add_argument('--semantic',action='store_true');a.add_argument('--rerank',action='store_true')
    s=sub.add_parser('simulate');s.add_argument('--output',default='results/simulation.json')
    ing=sub.add_parser('ingest-pdf');ing.add_argument('pdf');ing.add_argument('--out',default='results/pdf');ing.add_argument('--jsonl',default='results/pdf/evidence.jsonl');ing.add_argument('--caption-figures',action='store_true',help='Optional real vision-model image captioning')
    csvp=sub.add_parser('ingest-csv');csvp.add_argument('csv');csvp.add_argument('--columns',required=True,help='comma-separated existing column headers');csvp.add_argument('--jsonl',default='results/csv_evidence.jsonl')
    o=sub.add_parser('fetch-openalex');o.add_argument('--query',default='lake phosphorus chlorophyll eutrophication');o.add_argument('--limit',type=int,default=15)
    o.add_argument('--email');o.add_argument('--jsonl',default='data/openalex_evidence.jsonl')
    sc=sub.add_parser('encode-scibert');sc.add_argument('text');sc.add_argument('--out',default='results/scibert.json')
    tr=sub.add_parser('train-scibert');tr.add_argument('train_jsonl');tr.add_argument('--out',default='results/scibert_model')
    lo=sub.add_parser('train-lora');lo.add_argument('train_jsonl');lo.add_argument('--out',default='results/lora');lo.add_argument('--steps',type=int,default=5)
    ex=sub.add_parser('expert-template');ex.add_argument('--claims',default='results/demo/report.json');ex.add_argument('--out',default='results/expert_ratings_BLANK.csv')
    args=p.parse_args(argv)
    if args.action=='demo':
        corpus=load_evidence(args.corpus)
        from .llm import OllamaClient
        llm=OllamaClient(model=args.model) if args.llm else None
        orchestrator=Orchestrator(corpus,llm=llm,semantic=args.semantic,rerank=args.rerank)
        report,graph,causal=orchestrator.run(args.query,include_causal=True)
        out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
        write_json({'execution_mode':orchestrator.mode,'report':report.model_dump(),
                    'model_identifiers':{'embedding':orchestrator.retriever.embedding_model_id,
                                         'reranker':orchestrator.retriever.cross_encoder_id,'llm':args.model if args.llm else None}},out/'report.json')
        if causal is not None:
            write_json(causal,out/'synthetic_causal.json')
        else:
            (out/'synthetic_causal.json').unlink(missing_ok=True)
        export_graph(graph,out/'evidence.ttl')
        print(f'Mode: {orchestrator.mode}; evidence: {len(report.cited_evidence)}; RDF triples: {len(graph)}')
        print('Saved to:',out)
    elif args.action=='evaluate':
        items=load_evidence(args.corpus);qrels=json.loads(Path(args.qrels).read_text())
        negatives=json.loads(Path(args.hard_negatives).read_text(encoding='utf8')) if args.hard_negatives else []
        result=evaluate_retriever(items,qrels,semantic=args.semantic,rerank=args.rerank,negative_queries=negatives)
        write_json(result,args.output);print(json.dumps({k:v for k,v in result.items() if k!='questions'},indent=2))
    elif args.action=='simulate':
        result={'synthetic_scm':intervention_experiment(),'synthetic_world_model':fit_world_model()}
        write_json(result,args.output);print('Saved',args.output)
    elif args.action=='ingest-pdf':
        items,figs=pdf_ingest(args.pdf,args.out)
        if args.caption_figures:
            from .multimodal import caption_figures
            items += caption_figures(figs)
        export_jsonl(items,args.jsonl)
        write_json([f.model_dump() for f in figs],Path(args.out)/'figures.json')
        print('PDF chunks',len(items),'embedded figures',len(figs))
    elif args.action=='ingest-csv':
        rows=csv_ingest(args.csv,columns=args.columns.split(','));export_jsonl(rows,args.jsonl)
        print('CSV records',len(rows))
    elif args.action=='fetch-openalex':
        items=search_abstracts(args.query,limit=args.limit,email=args.email)
        export_jsonl(items,args.jsonl);print('Attributable abstract records',len(items))
    elif args.action=='encode-scibert':
        from .transformer_nlp import SciBERTEncoder
        enc=SciBERTEncoder();write_json({'model':enc.model_id,'embedding':enc.encode([args.text])[0]},args.out)
    elif args.action=='train-scibert':
        from .train_scibert import train_classifier
        print(train_classifier(args.train_jsonl,args.out))
    elif args.action=='train-lora':
        from .finetune import train_lora
        print(train_lora(args.train_jsonl,args.out,steps=args.steps))
    elif args.action=='expert-template':
        data=json.loads(Path(args.claims).read_text());claim_ids=data['report']['claim_ids']
        Path(args.out).parent.mkdir(parents=True,exist_ok=True)
        make_expert_template(claim_ids,args.out);print('Blank expert sheet:',args.out)

if __name__=='__main__':main()
