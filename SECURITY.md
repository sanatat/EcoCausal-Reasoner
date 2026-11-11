# Security policy

This repository is a **research prototype**, not a production service or a trusted scientific decision engine. Do not upload confidential studies, patient data, access tokens, or copyrighted PDFs to public issues or pull requests.

- **Do not publish credentials, model checkpoints, private PDF documents or raw data** without an explicit license/authorization review.
- `ingest-pdf` parses *local input documents*. Process only PDFs from sources you trust and in a suitably isolated environment; PDF extraction libraries can have security vulnerabilities.
- The optional Ollama connector only accepts loopback HTTP endpoints. It is not a remote hosted API service.
- Model-generated outputs and retrieved text are untrusted; quotation matching is not semantic verification.
- Dependency security updates should be reviewed before deployment. Offline tests do not constitute penetration tests.

If GitHub private vulnerability reporting is enabled after repository creation, use that route for non-public security reports. Avoid publicly sharing an exploit, sensitive documents, or keys.
