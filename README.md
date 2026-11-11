# EcoCausal-Reasoner

**A provenance-first research prototype for scientific NLP, multi-agent workflows, RDF/SPARQL evidence graphs, and synthetic causal reasoning.**

*Research software portfolio, 2026. Original implementation. Author: Sana Tat.*

> **Evidence boundary:** The included demo texts and retrieval labels are **entirely invented synthetic fixtures**. The synthetic causal effect and world-model numbers are *not* estimates for any real lake. The offline demo is a **deterministic workflow of multiple software roles, not LLM multi-agent inference**. Hugging Face, semantic RAG, LoRA, scientific vision captioning, DoWhy and live Ollama are optional integration modules that require separate dependencies/model weights and real executions. No external expert ratings are included. Do not use this tool to make environmental management decisions.

## A single testable research question

Can an AI workflow assess the question **“Does reducing phosphorus change chlorophyll-a in lakes?”** while keeping retrieved documents, textual associations, causal *assumptions*, simulated interventions, and expert appraisals separate?

This repository addresses the *method* of evidence organization and evaluation. It does **not** establish an empirical causal ecological conclusion.

## What is genuinely reproducible offline

- **Source-aware ingestion:** PDF text blocks, embedded raster images, detected tables and CSV rows; page numbers and SHA-256 for local sources.
- **Hybrid lexical retrieval:** TF-IDF + BM25 with reciprocal-rank fusion and a synthetic-qrels retrieval benchmark.
- **Multi-role orchestration:** planner, evidence agent, extraction agent, graph agent, critic, causal agent; bounded critique-driven retry and JSON trace. Topic-coverage gates, lead-concept checks and a five-query adversarial test set now reject several kinds of misleading lexical matches; these heuristics have not been externally validated.
- **Source-linked *candidate* relations:** baseline co-mention extraction; optional LLM extracted relations must contain an exact quote mentioning both entities from an allowed source. This proves provenance of the quote, **not** entailment of the relation.
- **RDF Knowledge Graph:** RDFLib + PROV-O `wasDerivedFrom` links, explicit supporting quotes and executable SPARQL query; Turtle export.
- **Synthetic SCM:** explicit DAG; backdoor adjustment test by d-separation; observational OLS estimate, bootstrap 95% interval, and known interventional ground truth.
- **Controlled synthetic world model:** a Ridge state transition trained on state + exogenous intervention input, one-step vs persistence benchmark, multi-step rollout error and action-conditioned simulation.
- **Evaluation tools:** retrieval Recall@5/nDCG@5, five hard-negative queries with false-positive rate; schema-validated optional LLM-as-a-Judge; blank human review template and two-reviewer Cohen's kappa.
- **Tests and CI:** `pytest` tests with no external tokens, networks, or proprietary datasets. GitHub Actions supports Python 3.10/3.12.

## Optional real-model and data workflows (code implemented; not run in the shipped demo)

- Sentence Transformers (`all-MiniLM-L6-v2`) + FAISS for dense semantic search, alongside BM25+TF-IDF fusion.
- Cross-Encoder (`ms-marco-MiniLM-L6-v2`) for candidate reranking.
- Hugging Face **SciBERT** embedding extraction and independent group-holdout SciBERT classification fine-tuning.
- Hugging Face **Qwen2.5-0.5B-Instruct** with PEFT **LoRA** (manual training loop; no held-out improvement claimed).
- Ollama-backed independent **Planner, Extractor and Critic** inference with Pydantic validation and bounded re-query; not demonstrated against a running Ollama server in the shipped benchmark.
- Optional **BLIP** image caption generation from embedded PDF images; captions are explicitly marked unverified.
- Optional **DoWhy** causal identification/estimation on the declared synthetic model.
- **OpenAlex** API to retrieve attributable titles and reconstructed abstracts (not journal PDFs). EPA NLA 2022 and USGS NAS are *external data candidates*, not silently included in the demo.

## Install and run (Linux Mint / Ubuntu)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -q

ecocausal demo --output results/demo
ecocausal evaluate --output results/retrieval.json
ecocausal simulate --output results/simulation.json
```

The `demo` command writes:

- `results/demo/report.json` — cited evidence IDs, mode, per-agent trace and limitations.
- `results/demo/evidence.ttl` — provenance-linked RDF triples, SPARQL queryable.
- `results/demo/synthetic_causal.json` — estimated and known intervention effect on an invented SCM.

### Run against papers with real sources

```bash
# OpenAlex metadata/abstracts; requires internet and may require API key / quota.
export OPENALEX_API_KEY="your_key_if_required"
ecocausal fetch-openalex --query "lake phosphorus chlorophyll eutrophication" --limit 20 --jsonl data/openalex_evidence.jsonl

# Scientific PDF that you lawfully possess (never include restricted PDFs in Git).
ecocausal ingest-pdf /path/to/your_paper.pdf --out results/paper --jsonl results/paper/evidence.jsonl

# Run the evidence workflow against your real corpus.
ecocausal demo --corpus data/openalex_evidence.jsonl --query "phosphorus chlorophyll lake" --output results/real_papers
```

**Important:** neither OpenAlex metadata nor ordinary PDF extraction guarantees that the supplied studies are comparable or that their claims are causally identified.

### Use the actual deep-learning NLP/RAG stack

```bash
pip install -e '.[semantic,transformers]'
ecocausal demo --corpus data/openalex_evidence.jsonl --semantic --rerank --output results/semantic

ecocausal encode-scibert "Phosphorus and chlorophyll-a are associated in an observational lake survey."
# The following classifier experiment uses deliberately fabricated labels by default.
ecocausal train-scibert data/demo_nlp_labels.jsonl --out results/scibert_model
```

Model weights can be large. CPU-only runs can be slow and require sufficient memory; verify device availability first.

### Local LLM multi-agent run

```bash
# Separately install/start Ollama and pull a model supporting instruction following.
ollama pull qwen2.5:3b
ollama serve  # only if not already running

ecocausal demo --llm --model qwen2.5:3b --corpus data/openalex_evidence.jsonl --output results/llm_agents
```

Do not treat the existence of optional adapter code as proof that this live mode passed scientific evaluations. The offline fixture-based fake-LLM tests establish software wiring only.

### Optional real LoRA training

```bash
pip install -e '.[finetune]'
ecocausal train-lora data/demo_lora_train.jsonl --out results/lora --steps 5
```

The sample dataset is only for **technical demonstration**. To produce defensible NLP improvement evidence, replace it with source-group-disjoint human-annotated examples and evaluate frozen holdouts against the base model. The `.pt`/`.safetensors` weights and source PDFs should not be pushed without license and provenance review.

### More evaluation

```bash
# Creates a BLANK human-review CSV. No scores are invented.
ecocausal expert-template --claims results/demo/report.json --out results/expert_ratings_BLANK.csv
```

## Folder map

`src/ecocausal/{agents,llm,retrieval,extraction,transformer_nlp,graph,causal,world_model,multimodal,finetune,train_scibert,evaluation,ingestion,openalex}.py`

`tests/` contains repeatable software checks. `data/demo*` are all fake fixtures. `results/` contains illustrative outputs only. `docs/KEYWORD_COVERAGE.md` maps the 16 requested skills to testable evidence and gaps.

## Repository and release integrity

- [Release checklist](docs/RELEASE_CHECKLIST.md) · [Data/model publication rules](docs/DATA_AND_MODEL_POLICY.md) · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Citation](CITATION.cff).
- This is a **source repository**, not a wheel distribution. Use `pip install -e .` from a Git clone; some default demo assets are loaded relative to the project directory.
- GitHub CI on Python 3.10/3.12 must still be verified **after first push**. Local tests in this release do not imply remote CI has run.

## External scientific data pointers

- [US EPA, National Lakes Assessment 2022](https://www.epa.gov/national-aquatic-resource-surveys/reports-and-data-national-lakes-assessment-2022) — official environmental data; not packaged here.
- [USGS Nonindigenous Aquatic Species](https://nas.er.usgs.gov/) — observational species records; do not equate occurrence with causal impact.
- [OpenAlex API](https://help.openalex.org/api/) — scholarly discovery metadata; check current API quotas.

## Scientific limitations

1. Graph edges extracted from co-mentions or LLM relations do **not** prove causality.
2. Pearl backdoor criteria operate under an **assumed correct DAG**; synthetic ground truth is not ecological ground truth.
3. The world model learns a toy dynamic system; action-conditioned rollouts do not establish transportability to real lakes.
4. Retrieved texts may be wrong, biased, incomplete, or maliciously prompt-injecting; LLM output is never trusted without source checks.
5. The LLM critic is **not** a human expert; no fabricated expert rating is included.
6. No real Transformer/LoRA/semantic model run is asserted by the offline CI.
7. Observational datasets need appropriate sampling design and adjustment variables before causal identification.

MIT-licensed original code; external source datasets and model weights retain their own terms.

## Independent pre-publication audit (v0.2.0)

The current offline release passes **59 automated checks** including adversarial citation/topic tests.
On the tiny *synthetic* fixture benchmark, 5/5 hard-negative queries abstain and
3/3 authored retrieval queries score Recall@5=1.0. These results **must not**
be described as real-paper retrieval accuracy, semantic entailment, or LLM agent success.
The offline system is intentionally conservative: it may also reject truly
relevant but lexically distant papers (false abstention). Calibrate on an
independent labeled corpus before any real-world scientific claims.


See [`docs/PREPUBLISH_AUDIT.md`](docs/PREPUBLISH_AUDIT.md) for an evidence-tier verdict across all 16 keywords. **No demonstrated live NLP transformer, fine-tuning, dense RAG, LLM multi-agent, human expert review or real-ecology inference** is claimed by this archive. The synthetic offline fixture cannot prove those skills.
