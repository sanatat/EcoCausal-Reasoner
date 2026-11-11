# Pre-publication audit — EcoCausal-Reasoner v0.2.0

**Date:** 2026-11-11. **Decision:** Release only as a transparent **synthetic/offline research prototype**. It is **not** evidence that all 16 PhD keyword gaps have been closed. No GitHub publishing action was performed in this review.

## Correctness fixes tested in this release

1. **Off-topic retrieval:** lexical results require sufficient topic coverage, and multi-concept questions are gated against unrelated lead concepts. An entirely off-topic query and four deliberately misleading hard negatives now retrieve no documents in the synthetic test corpus. Semantic-only hits require a conservative similarity threshold. The thresholds are heuristics; false rejection of real synonyms is possible.
2. **LLM topic drift:** planner query rewrites and critic retries must preserve the original question topic. Invalid planner JSON falls back to the original query; malformed claim or critic schemas fail closed.
3. **Hallucinated relations:** quotes must be verbatim source substrings, mention the claim subject and object, and originate from an allowed source. LLM predicates without a relationship cue are downgraded to co-mentions. A correct quote still does **not** prove entailment or scientific truth.
4. **Critic rejection:** rejected claims do not enter the final RDF graph or `candidate_claims`. An unanswered question has an empty graph and does not receive a spurious synthetic causal-effect attachment. The standalone `simulate` command remains independent.
5. **Evidence provenance:** duplicate evidence IDs are rejected; same-named CSVs use content-digest-qualified row IDs; PDF figures include source PDF hash. Generated image captions use a distinct `image_caption` type and cannot create causal/scientific relation claims without independent validation.
6. **Training / human review:** answer-only LoRA labels are now constructed at token boundaries rather than inferred from potentially mismatched tokenized strings. Both expert-rating fields must be present for both independent reviewers, with duplicate/partial ratings rejected.
7. **Quality of evidence:** observational co-mentions are no longer labeled `reported_association`. PDF table extraction failures are recorded in the ingestion manifest.

## 16-keyword evidence tiers

**Offline prototype** = code tested on authored synthetic data; **Partial** = adapter or mock tested but advertised live capability not demonstrated; **Not demonstrated** = model/protocol code exists with no live model run or evaluation result.

| Keyword | Evidence tier | Remaining evidence to claim completion |
|---|---|---|
| Multi-Agent Orchestration | Partial | Ollama-backed planner/extractor/critic, actual traces and single-vs-multi-agent comparison |
| Hugging Face Transformers | Not demonstrated | Download, run and log SciBERT inference |
| Transformer-based NLP | Not demonstrated | Human-labeled study-wise split and held-out evaluation |
| Advanced RAG | Partial | Real dense retrieval + reranker + cited-answer evaluation |
| Semantic Retrieval / Reranking | Not demonstrated | FAISS and CrossEncoder live benchmarks on real qrels |
| LLM Fine-Tuning | Not demonstrated | Successful LoRA training, separate held-out base-vs-adapter benchmark |
| Knowledge Graphs | Offline prototype | Normalized, independently evaluated scientific relations |
| Semantic Web / RDF / SPARQL | Offline prototype | Real ontology alignment and entity-linked graph tests |
| Causal Inference | Offline prototype | Defensible real causal estimand, assumptions and sensitivity checks |
| Structural Causal Models | Offline prototype | Validated non-synthetic mechanism/benchmarks |
| Intervention-based Reasoning | Offline prototype | Justified interventions and credible evaluation |
| World Models | Offline prototype | Real held-out system dynamics and generalization |
| LLM-as-a-Judge | Partial | Live independent judge, bias and human-agreement studies |
| Expert-Grounded Evaluation | Not demonstrated | Ratings from real independent qualified reviewers |
| Multimodal Information Integration | Partial | Evaluated scientific figure/text/table alignment |
| Uncertainty Modeling | Offline prototype | Interval coverage and robustness on real data |

**Counts:** 7 offline prototypes, 4 partial, 5 not demonstrated. The counts are about code evidence, *not* a measurement of career proficiency.

## Locally verified release evidence

- **59 passing pytest cases** on this container's Python runtime, including adversarial negative-query and malformed-LLM-output tests. GitHub Actions for Python 3.10/3.12 is configured but was not executed as part of this local review.
- Default demo: **5 fictional evidence records**, **5 candidate co-mentions**, **56 RDF triples**. All records are synthetic.
- Hand-authored synthetic relevance queries (n=3): mean **Recall@5 1.000** and **nDCG@5 1.000**.
- Hand-authored synthetic hard negatives (n=5): **0/5 false positives** on lexical retrieval. This is not a verified rate on real scientific documents.
- Completely unrelated question: **0 documents**, **0 claims**, **0 graph triples**, **`insufficient_evidence`**, and **no causal-effect attachment**.
- Synthetic backdoor study: true ATE **3.20**, estimated ATE approximately **3.18** (model/seed-specific; no ecological interpretation).
- World model: synthetic numerical verification only; no environmental dataset.

## Remaining hard scientific gaps

- No downloaded or executed SciBERT/Qwen/BLIP/FAISS/CrossEncoder models in this release environment.
- No actual Ollama agents or PEFT fine-tuning results; mock tests verify orchestration contracts only.
- No real-paper gold standard, expert evaluations, external causal identification, or ecology field validation.
- Heuristic relevance and quote checks can still fail on negation, indirect references, domain synonyms, ambiguous relations and adversarial documents. They do not establish textual entailment.
- The RDF graph is a record of candidate textual relations, **not** the separately assumed causal DAG.

**Safe public positioning:** “An offline, provenance-aware scientific evidence workflow with deterministic multi-role orchestration, RDF/SPARQL, explicit abstention gates, and synthetic causal/world-model validation; optional, unverified adapters for SciBERT, semantic RAG, Ollama and LoRA.”
