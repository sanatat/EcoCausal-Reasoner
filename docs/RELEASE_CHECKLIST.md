# GitHub release checklist — v0.2.0

- [x] Author/license/citation information included (MIT, `CITATION.cff`).
- [x] Python package metadata, requirements, English and Persian documentation.
- [x] Source, synthetic fixtures, tests and GitHub Actions CI included.
- [x] `.gitignore` excludes local outputs, credentials, model weights, licensed source PDFs and caches.
- [x] Run offline pytest, CLI smoke tests and unrelated-question abstention test.
- [x] Scan tracked file list for binary/private files and obvious credential patterns via `python scripts/prepublish_check.py`.
- [x] Fresh extraction of GitHub-upload ZIP and repeat offline tests.
- [ ] Create GitHub repository under the owner's account and push.
- [ ] Inspect **remote** GitHub Actions (Python 3.10 and 3.12) after push.
- [ ] Add tags/releases only after remote CI succeeds.
- [ ] Real Hugging Face, FAISS, Ollama and LoRA model runs with licensed datasets (future research; **not** needed to publish a clearly labelled offline prototype).
- [ ] Genuine independent expert review and real-data causal evaluation (future research).

**Release classification:** Ready to publish *only* as a clearly bounded, synthetic/offline research software prototype. **Not** a validated system closing all 16 PhD-skill gaps.
