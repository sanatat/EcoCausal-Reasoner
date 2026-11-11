# Sixteen keyword audit — exact scope of shipped evidence

| Keyword | Implemented module | Evidence in this delivery | Remaining validation |
|---|---|---|---|
| Multi-Agent Orchestration | `agents.py` + `llm.py` | Offline 6-role trace; mocked LLM roles and source gate are unit-tested; not a live multi-agent validation | Live multi-agent Ollama run and expert comparison not executed |
| Hugging Face Transformers | `transformer_nlp.py`, `train_scibert.py` | Actual SciBERT `AutoModel`/`AutoModelForSequenceClassification` code | Weights not downloaded/tested in this container |
| Transformer-based NLP | `train_scibert.py` | Training and group-holdout macro-F1 pipeline | Need actual labelled studies and training run |
| Advanced RAG | `retrieval.py` | TF-IDF + BM25 + rank fusion runs offline | Dense search/reranker code optional, not executed here |
| Semantic Retrieval / Reranking | `retrieval.py` | Optional SentenceTransformer, FAISS IndexFlatIP, CrossEncoder | Download weights and measure held-out retrieval gains |
| LLM Fine-Tuning | `finetune.py` | Real PEFT LoRA training code with answer-only labels and grouped split | Needs memory, downloaded weights, measured holdout comparison |
| Knowledge Graphs | `graph.py` | 56 triples from synthetic default demo with quote- and source-provenance | Need accurate real relations and entity normalization |
| Semantic Web / RDF / SPARQL | `graph.py` | RDFLib, PROV-O, SPARQL query tested | Ontology alignment against external systems |
| Causal Inference | `causal.py` | OLS backdoor estimator with adjustment check and bootstrapped intervals | Observational ecology identification/validation not established |
| Structural Causal Models | `causal.py` | Executed synthetic generating SCM; known ground truth | No field-calibrated mechanism |
| Intervention-based Reasoning | `causal.py`, `world_model.py` | Paired synthetic `do(phosphorus)` and action-conditioned rollouts | Real interventions unavailable |
| World Models | `world_model.py` | Controlled learned dynamics and holdout/persistence baseline run | No real-lake forecasting validation |
| LLM-as-a-Judge | `evaluation.py` | Typed score rubric with fake-LLM unit test | No live model judged human-labeled records |
| Expert-Grounded Evaluation | `evaluation.py` | Blank expert rating CSV and 2-reviewer agreement calculator | Independent human ratings absent |
| Multimodal Information Integration | `ingestion.py`, `multimodal.py` | Page-aware PDF figures/tables/text, optional BLIP captions | Real scientific vision-caption inference not executed |
| Uncertainty Modeling | `causal.py`, `world_model.py` | Bootstrapped effect CI + holdout forecasting error | Real-data interval calibration not established |

## Verification rules

- **Implemented** does not equal **executed**.
- **Executed on synthetic** does not equal **validated on real data**.
- **LLM API wiring** does not equal **scientifically effective autonomous agents**.
- **Expert evaluation code** does not equal **expert evaluations already collected**.
- Every empirical value needs an authentic source, source licensing review, and predeclared evaluation.

**Pre-publication status (v0.2.0): 7 synthetic/offline prototypes, 4 partial implementations, 5 not demonstrated.** See [full audit](PREPUBLISH_AUDIT.md).
