"""Schema-first records. Synthetic text never becomes empirical evidence silently."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class Evidence(BaseModel):
    source_id: str = Field(min_length=1)
    page: int = Field(ge=1)
    text: str = Field(min_length=1)
    evidence_kind: Literal['synthetic_demo', 'openalex_abstract', 'pdf_text', 'pdf_table', 'csv_data', 'image_caption']
    source_url: str | None = None
    file_sha256: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    @model_validator(mode='after')
    def check_source(self):
        if self.evidence_kind not in ('synthetic_demo',) and not (self.source_url or self.file_sha256):
            raise ValueError('Non-demo evidence requires source_url or content hash')
        return self

class Claim(BaseModel):
    claim_id: str = Field(min_length=1)
    subject: str = Field(min_length=2)
    predicate: str = Field(min_length=2)
    object: str = Field(min_length=2)
    polarity: Literal['positive', 'negative', 'uncertain'] = 'uncertain'
    epistemic_status: Literal['illustrative', 'unverified_co_mention', 'reported_association', 'author_causal_claim', 'established_under_assumptions'] = 'illustrative'
    evidence: Evidence
    quote: str | None = None  # Exact evidence span; absence never implies verified entailment.
    conditions: str = ''
    @model_validator(mode='after')
    def check_quote_provenance(self):
        if self.quote is not None and self.quote not in self.evidence.text:
            raise ValueError('Claim quote is not a verbatim substring of evidence')
        return self

class Figure(BaseModel):
    image_sha256: str
    document_sha256: str | None = None
    source_id: str
    page: int
    path: str
    caption: str | None = None

class AgentStep(BaseModel):
    agent: str
    action: str
    status: Literal['ok', 'skipped', 'error']
    details: dict = Field(default_factory=dict)

class HypothesisReport(BaseModel):
    question: str
    status: Literal['insufficient_evidence', 'descriptive_only', 'assumptions_required']
    cited_evidence: list[Evidence]
    summary: str
    limitations: list[str]
    agent_trace: list[AgentStep]
    claim_ids: list[str] = Field(default_factory=list)
    candidate_claims: list[Claim] = Field(default_factory=list)
