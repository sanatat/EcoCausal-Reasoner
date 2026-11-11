"""Optional genuine Transformer classification fine-tuning with group-disjoint evaluation."""
from __future__ import annotations
import json,random
from pathlib import Path
from .finetune import split_by_group


def train_classifier(path:str|Path,out_dir:str|Path,model_id='allenai/scibert_scivocab_uncased',epochs=1):
    try:
        import torch
        from transformers import AutoTokenizer,AutoModelForSequenceClassification
        from sklearn.metrics import f1_score
    except ImportError as exc:
        raise RuntimeError('Install pip install -e .[transformers]') from exc
    records=[json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
    if not all('label' in r and 'text' in r for r in records):raise ValueError('Each row needs label,text,group_id')
    tr,te=split_by_group([{'group_id':r['group_id'],'question':r['text'],'answer':r['label'],**r} for r in records])
    labels=sorted({r['label'] for r in records})
    if len(labels)<2 or set(labels)!=set(r['label'] for r in tr):
        raise ValueError('Need at least two labels represented in training groups')
    mapping={s:i for i,s in enumerate(labels)}
    random.seed(42);torch.manual_seed(42)
    tokenizer=AutoTokenizer.from_pretrained(model_id)
    model=AutoModelForSequenceClassification.from_pretrained(model_id,num_labels=len(labels))
    optim=torch.optim.AdamW(model.parameters(),lr=2e-5)
    model.train()
    for _ in range(epochs):
        for row in tr:
            tokens=tokenizer(row['text'],return_tensors='pt',truncation=True,max_length=256)
            result=model(**tokens,labels=torch.tensor([mapping[row['label']]]))
            result.loss.backward();optim.step();optim.zero_grad()
    model.eval();pred=[];gold=[]
    with torch.no_grad():
        for row in te:
            tokens=tokenizer(row['text'],return_tensors='pt',truncation=True,max_length=256)
            pred.append(int(model(**tokens).logits.argmax(-1).item()));gold.append(mapping[row['label']])
    dest=Path(out_dir);dest.mkdir(parents=True,exist_ok=True)
    model.save_pretrained(dest);tokenizer.save_pretrained(dest)
    from collections import Counter
    majority=mapping[Counter(r['label'] for r in tr).most_common(1)[0][0]]
    report={'model':model_id,'train_n':len(tr),'holdout_n':len(te),
            'macro_f1':float(f1_score(gold,pred,average='macro',zero_division=0)),
            'majority_class_baseline_macro_f1':float(f1_score(gold,[majority]*len(gold),average='macro',zero_division=0)),
            'dataset_limitations':'Check study-level label validity and sample size before scientific interpretation.'}
    (dest/'benchmark.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    return report
