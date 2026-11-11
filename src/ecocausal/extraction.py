"""Auditable baseline extraction. No generative model is claimed in offline mode."""
from __future__ import annotations
import re
from .schema import Evidence, Claim

PHRASE_PATTERNS=[
    (r'phosphor(?:us|ate)', 'phosphorus'),
    (r'chlorophyll[ -]?a|algal biomass', 'chlorophyll-a'),
    (r'water temperature|temperature', 'temperature'),
    (r'zebra mussel|dreissena', 'zebra_mussel'),
    (r'water clarity|secchi depth|transparency', 'water_clarity'),
]

def entities(text:str)->set[str]:
    return {canonical for pattern,canonical in PHRASE_PATTERNS if re.search(pattern,text,re.I)}


def extract_claims(evidence:list[Evidence])->list[Claim]:
    claims=[]
    # This is *co-mention extraction*, not relation/causal inference.
    for e in evidence:
        if e.evidence_kind=='image_caption':
            continue  # Machine-generated captions are not verified scientific claims.
        ents=sorted(entities(e.text))
        if len(ents)>=2:
            claims.append(Claim(claim_id=f'claim:{len(claims)+1}',subject=ents[0],predicate='co_mentioned_with',
                object=ents[1],polarity='uncertain',
                epistemic_status='illustrative' if e.evidence_kind=='synthetic_demo' else 'unverified_co_mention',
                evidence=e,quote=e.text[:1000]))
    return claims
