"""Opt-in actual LoRA for a causal LM. Needs curated, non-leaking train JSONL & significant RAM.

This module is not executed in offline CI; its presence does not establish fine-tuning success.
"""
from __future__ import annotations
import json
from pathlib import Path


def read_supervised(path:str|Path)->list[dict]:
    records=[]
    for i,line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(),1):
        if not line.strip():continue
        item=json.loads(line)
        if not item.get('question') or not item.get('answer') or not item.get('group_id'):
            raise ValueError(f'Line {i} requires question, answer, group_id')
        records.append(item)
    if len(records)<4:raise ValueError('At least four examples required for demonstration')
    return records


def split_by_group(items:list[dict],test_fraction=.25,seed=42)->tuple[list[dict],list[dict]]:
    import numpy as np
    groups=sorted({r['group_id'] for r in items})
    if len(groups)<2:raise ValueError('Need at least two independent source groups')
    rng=np.random.default_rng(seed);rng.shuffle(groups)
    test=set(groups[:max(1,round(test_fraction*len(groups)))])
    train=[r for r in items if r['group_id'] not in test]
    valid=[r for r in items if r['group_id'] in test]
    assert {r['group_id'] for r in train}.isdisjoint({r['group_id'] for r in valid})
    return train,valid


def build_answer_only_tokens(tokenizer, question: str, answer: str, max_length: int = 384):
    """Token-boundary-safe teacher forcing: prompt tokens contribute ZERO loss.

    Tokenizing the concatenation and masking by separately tokenized prefix
    length is unsafe under some subword tokenizers; tokenize parts explicitly.
    """
    prefix = f"Question: {question}\nAnswer: "
    prompt_ids = tokenizer(prefix, add_special_tokens=False)['input_ids']
    answer_ids = tokenizer(answer, add_special_tokens=False)['input_ids']
    eos = getattr(tokenizer, 'eos_token_id', None)
    if eos is not None:
        answer_ids = answer_ids + [eos]
    if len(prompt_ids) >= max_length:
        raise ValueError('Prompt exhausts max_length; no answer tokens can be learned')
    answer_ids = answer_ids[:max_length-len(prompt_ids)]
    if not answer_ids:
        raise ValueError('No answer tokens remain after truncation')
    return prompt_ids + answer_ids, [-100]*len(prompt_ids) + answer_ids


def train_lora(data_path:str|Path,out_dir:str|Path,model_id='Qwen/Qwen2.5-0.5B-Instruct',steps=5):
    if not 1<=steps<=300:raise ValueError('steps must be 1..300')
    try:
        import torch
        from peft import LoraConfig,get_peft_model,TaskType
        from transformers import AutoTokenizer,AutoModelForCausalLM
    except ImportError as exc:
        raise RuntimeError('Install pip install -e .[finetune] first') from exc
    records=read_supervised(data_path)
    train,valid=split_by_group(records)
    tokenizer=AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:tokenizer.pad_token=tokenizer.eos_token
    model=AutoModelForCausalLM.from_pretrained(model_id)
    model=get_peft_model(model,LoraConfig(task_type=TaskType.CAUSAL_LM,
                     r=4,lora_alpha=8,lora_dropout=.05,target_modules=['q_proj','v_proj']))
    model.train();opt=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=3e-4)
    losses=[]
    # No teacher label from the question portion: loss is only on the answer span.
    for i in range(steps):
        row=train[i%len(train)]
        token_ids, target_ids = build_answer_only_tokens(tokenizer,row['question'],row['answer'])
        ids=torch.tensor([token_ids],dtype=torch.long)
        labels=torch.tensor([target_ids],dtype=torch.long)
        out=model(input_ids=ids,attention_mask=torch.ones_like(ids),labels=labels)
        out.loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0)
        opt.step();opt.zero_grad()
        losses.append(float(out.loss.detach()))
    dest=Path(out_dir);dest.mkdir(parents=True,exist_ok=True)
    model.save_pretrained(dest/'adapter');tokenizer.save_pretrained(dest/'adapter')
    report={'model_id':model_id,'steps':steps,'train_examples':len(train),'holdout_examples':len(valid),
            'train_loss_trace':losses,'evaluated_on_holdout':False,
            'limitations':'No held-out fine-tuning improvement claim. Run separate inference benchmarking.'}
    (dest/'training_report.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    (dest/'holdout_questions.jsonl').write_text(''.join(json.dumps({'question':r['question'],'group_id':r['group_id']})+'\n' for r in valid),encoding='utf8')
    return report
