# v0.2.0 — Offline evidence and synthetic causal research prototype

## What is included

- Python package and CLI with three offline experiment commands.
- Tested TF-IDF/BM25 retrieval, strict abstention checks, mockable multi-role orchestration, RDF/SPARQL candidate graph, source IDs and quotes.
- Synthetic structural causal model, intervention and action-conditioned dynamic simulation.
- Audited software tests with negative and provenance-safety cases.
- Optional adapters for transformer, FAISS/CrossEncoder, Ollama, LoRA, DoWhy and multimodal captions, not validated by this release.

## Evidence boundary

The bundled source documents and relevance labels are invented. No claim is made about real ecological causal effects, real agent or language-model accuracy, or expert review. See [audit](PREPUBLISH_AUDIT.md) and [data policy](DATA_AND_MODEL_POLICY.md).

## How to reproduce

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q
ecocausal demo --output results/demo
ecocausal evaluate --output results/retrieval.json
ecocausal simulate --output results/simulation.json
```

Tagging or pushing this release has not been done as part of preparation; check the new GitHub repository's CI before tagging `v0.2.0`.
