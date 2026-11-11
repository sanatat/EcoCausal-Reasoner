# Changelog

## v0.2.0 — Pre-publication scientific-integrity hardening (2026-11-11)

- Added conservative lexical topic/lead-concept coverage and uncalibrated semantic abstention gates.
- Added five adversarial hard-negative retrieval queries; added measured false-positive rate to evaluator.
- Prevented LLM planner/critic topic drift and rejected malformed role outputs.
- Required quoted evidence to mention both claim entities; demoted relation predicates without a cue.
- Ensured rejected candidate claims cannot contaminate the RDF graph or report.
- Prevented off-topic reports from getting synthetic causal-effect attachments.
- Reclassified real-source deterministic co-mentions as unverified, not reported associations.
- Added PDF source digest to extracted figures and explicit unverified caption evidence type.
- Strengthened LoRA teacher-label token boundary masking and SciBERT baseline report.
- Strengthened human review checks and PDF error manifest.
- Added adversarial test module: 59 local tests pass; optional model weights are not exercised.

## v0.1.1

- Initial prepublication review and minimal unrelated-query abstention/provenance improvements.

## v0.1.0

- Initial offline synthetic prototype and optional model adapters.
