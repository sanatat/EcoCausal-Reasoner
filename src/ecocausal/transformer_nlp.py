"""Optional real Hugging Face SciBERT feature extraction; requires model download."""
from __future__ import annotations

class SciBERTEncoder:
    def __init__(self, model_id='allenai/scibert_scivocab_uncased', device='cpu'):
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError('Install pip install -e .[transformers] first') from exc
        self.torch=torch
        self.device=device
        self.tokenizer=AutoTokenizer.from_pretrained(model_id)
        self.model=AutoModel.from_pretrained(model_id).to(device).eval()
        self.model_id=model_id

    def encode(self,texts:list[str],max_length:int=256):
        if not texts:return []
        tokens=self.tokenizer(texts,return_tensors='pt',padding=True,truncation=True,max_length=max_length)
        tokens={k:v.to(self.device) for k,v in tokens.items()}
        with self.torch.no_grad():
            outputs=self.model(**tokens).last_hidden_state
            mask=tokens['attention_mask'].unsqueeze(-1)
            pooled=(outputs*mask).sum(1)/mask.sum(1).clamp(min=1)
        return pooled.cpu().numpy().tolist()
