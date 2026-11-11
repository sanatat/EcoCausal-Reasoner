"""Local Ollama transport. No silent fallback or unvalidated JSON acceptance."""
from __future__ import annotations
import json, urllib.request
from urllib.parse import urlparse

class OllamaClient:
    def __init__(self,model='qwen2.5:3b',url='http://127.0.0.1:11434/api/chat',timeout=120):
        parsed=urlparse(url)
        if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost','::1'):
            raise ValueError('Only explicitly local HTTP Ollama endpoints are supported')
        self.model=model;self.url=url;self.timeout=timeout

    def json_response(self,system:str,user:str)->dict:
        req=urllib.request.Request(self.url,
             data=json.dumps({'model':self.model,'stream':False,'format':'json',
                              'options':{'temperature':0},
                              'messages':[{'role':'system','content':system},
                                          {'role':'user','content':user}]}).encode(),
             headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=self.timeout) as res:
            payload=json.load(res)
        raw=payload.get('message',{}).get('content','')
        if not raw:raise ValueError('Empty Ollama model response')
        out=json.loads(raw)
        if not isinstance(out,dict):raise ValueError('Expected a JSON object')
        return out
