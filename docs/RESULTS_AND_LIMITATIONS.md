# Reproducible offline results — 11 November 2026 (v0.2.0)

All source texts and qrels in the offline demo are **invented fixtures**. No external studies or real ecology estimates were used. `--llm`, `--semantic`, `--rerank` and LoRA require separate environments/weights and **were not executed** here.

| Local observation | Measured result | Caveat |
|---|---:|---|
| Pytest | **59 passed** | Tested software paths only; no real-model CI |
| Default demo retrieved documents | **5** | Fictional texts |
| Candidate textual co-mentions | **5** | No relation entailment or causal proof |
| RDF triples | **56** | From fictional text, with provenance |
| Synthetic retrieval Recall@5 | **1.000** | 3 hand-authored query/label pairs |
| Synthetic retrieval nDCG@5 | **1.000** | Same trivial small data |
| Hard-negative false positive rate | **0/5** | Hand-authored adversarial toy queries only |
| Off-topic question | **0 docs, 0 claims, 0 triples** | Correct `insufficient_evidence` abstention, no SCM attachment |
| Specified synthetic true ATE | **3.2000** | Invented generating model |
| Synthetic OLS adjusted ATE (default `demo`) | **3.1766** | Toy model; demo seed/path
| Synthetic OLS adjusted ATE (`simulate`) | **3.2414** | Same toy estimand, independently generated run/seed |
| Synthetic world-model 1-step RMSE | **0.3441** | Mixed units, invented dynamics |
| Synthetic world-model rollout RMSE | **1.0534** | Predictive error on synthetic holdouts |

## Release artifacts

- `results/demo/report.json`, `results/demo/evidence.ttl`, `results/demo/synthetic_causal.json`
- `results/negative_query/report.json`, `results/negative_query/evidence.ttl`
- `results/retrieval.json`, `results/simulation.json`
- `data/demo_hard_negatives.json` (five held-out style negative tests)
- `tests/test_safety_and_scientific_gates.py` (adversarial and tokenization tests)

## Reproduction

```bash
python -m pytest -q --disable-warnings
python -m ecocausal demo --output results/demo
python -m ecocausal demo --query 'Quantum tunneling in brown dwarfs' --output results/negative_query
python -m ecocausal evaluate --output results/retrieval.json
python -m ecocausal simulate --output results/simulation.json
```

See `PREPUBLISH_AUDIT.md` for the 16-keyword verdict and outstanding live-model, scientific-data and human-evaluation work. Passing synthetic tests **does not** validate real-world ecological reasoning.
