# From demo to genuine freshwater research (protocol, not completed experiment)

## A. Obtain appropriate source material

1. Download the EPA NLA 2022 dataset(s) from the official [NLA 2022 data portal](https://www.epa.gov/national-aquatic-resource-surveys/reports-and-data-national-lakes-assessment-2022), retaining its original methodology, survey weights, quality flags, lake identifiers and measurement units. Do not presume any specific field name or that every parameter is available for every lake.
2. Query OpenAlex for 20–30 high-relevance papers, and record OpenAlex ID, DOI, date, title and abstract. Obtain full-text PDFs only when accessible and legally reusable. A title/abstract corpus is not equivalent to a full-paper study.
3. For invasive species, the [USGS NAS](https://nas.er.usgs.gov/) occurrence records are candidate observational evidence, but occurrence records alone do not establish impact or temporally matched intervention.
4. Store `sha256`, source URL, sample-selection rule, corpus date and a manifest; do not upload copyrighted PDFs to a public repository.

## B. Build a real evaluation set

- Predefine specific ecological relations and a codebook: association, asserted causal mechanism, intervention study, and insufficient information.
- Two domain experts should independently annotate question-to-document relevance and the actual supporting excerpts.
- Split by **study/source**, not by random adjacent excerpts, to avoid leakage.
- Report separate results for source type (PDF, abstract, table and figure), plus failure cases.
- Any LLM judge should be calibrated against the expert adjudications, not treated as a replacement.

## C. Actual causal model needs

- Declare a DAG *before* fitting, identify potential confounders and whether they were measured.
- Treat measurement error, selection bias, survey weights, transportability across lakes and interventions explicitly.
- A single cross-sectional survey generally does not support unrestricted policy counterfactuals.
- Report failure to identify an effect where appropriate.

## D. Experimental comparisons to preregister

- BM25 only vs TF-IDF+BM25 vs semantic hybrid vs hybrid+rereanker.
- Base SciBERT vs tuned SciBERT; held-out macro F1 and per-label errors.
- Single agent vs Planner/Extractor/Critic multi-agent vs deterministic workflow; matched input budget and citations.
- Base vs LoRA model; held-out field extraction F1 and hallucination checks.
- Synthetic SCM estimated vs known ATE with CI coverage over multiple seeds.
- World model one-step, long-horizon, and intervention-vs-control errors, compared to persistence.
