"""Fetch public OpenAlex metadata/abstracts with attributable source IDs, not copyrighted PDFs."""
from __future__ import annotations
import json, os, urllib.parse, urllib.request
from pathlib import Path
from .schema import Evidence


def restore_abstract(inverted_index:dict | None) -> str:
    if not inverted_index:return ''
    pos={int(i):word for word,inds in inverted_index.items() for i in inds}
    return ' '.join(pos[i] for i in sorted(pos))


def search_abstracts(query:str, *, limit:int=20, email:str | None=None) -> list[Evidence]:
    if not 1<=limit<=100:raise ValueError('limit must be 1..100')
    params={'search':query,'filter':'has_abstract:true','per_page':str(limit)}
    key=os.environ.get('OPENALEX_API_KEY')
    if key:params['api_key']=key
    if email:params['mailto']=email
    url='https://api.openalex.org/works?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={'User-Agent':'EcoCausal-Reasoner/0.1 (+research prototype)'})
    with urllib.request.urlopen(req,timeout=30) as resp:
        payload=json.load(resp)
    out=[]
    for obj in payload.get('results',[]):
        abstract=restore_abstract(obj.get('abstract_inverted_index'))
        if abstract:
            out.append(Evidence(source_id=obj['id'],page=1,
                 text=f"Title: {obj.get('title','')}\nAbstract: {abstract}",
                 evidence_kind='openalex_abstract',source_url=obj.get('doi') or obj['id']))
    return out


def export_jsonl(evidence:list[Evidence],path:str | Path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(''.join(json.dumps(e.model_dump(),ensure_ascii=False)+'\n' for e in evidence),encoding='utf8')
