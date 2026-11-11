# Contributing

This is a personal academic research prototype. Reproducibility and evidence boundaries come before feature count.

1. Open an issue describing the research question, expected behavior and whether your data are **synthetic or real**.
2. Keep optional online/model dependencies behind explicit user choices and preserve an offline test path.
3. Add deterministic tests for expected successes and *negative* cases, especially unsupported conclusions, unrelated retrieval, forged source IDs and bad LLM outputs.
4. Include provenance for external data, model IDs, dataset licenses, evaluation splits and limitations. Do not upload private or restricted content.
5. Run `python -m pytest -q` and the three CLI smoke commands described in `README.md`.
6. Do not claim causal truth from citations, a word overlap, model outputs, or an assumed graph.

Publishing a new optional adapter without a real-model test does not count as verified skill coverage. Human/expert ratings must come from real independent reviewers.
