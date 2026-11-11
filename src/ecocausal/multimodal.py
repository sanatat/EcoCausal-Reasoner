"""Optional figure captioning; first-party extraction alone is *not* image understanding."""
from __future__ import annotations
from pathlib import Path
from .schema import Figure,Evidence

def caption_figures(figures:list[Figure],model_id='Salesforce/blip-image-captioning-base')->list[Evidence]:
    if not figures:return []
    try:
        from transformers import pipeline
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError('pip install -e .[transformers] plus Pillow required') from exc
    captioner=pipeline('image-to-text',model=model_id,device=-1)
    results=[]
    for fig in figures:
        with Image.open(fig.path).convert('RGB') as im:
            generated=captioner(im,max_new_tokens=55)
        text=generated[0]['generated_text']
        results.append(Evidence(source_id=f'{fig.source_id}:figure:{fig.image_sha256[:12]}',
                page=fig.page,text=f'Unverified automated image caption: {text}',
                evidence_kind='image_caption',file_sha256=fig.document_sha256 or fig.image_sha256,confidence=None))
    return results
