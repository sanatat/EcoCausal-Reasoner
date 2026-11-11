#!/usr/bin/env bash
set -euo pipefail
python3 -m pytest -q
python3 -m ecocausal demo --output results/demo
python3 -m ecocausal evaluate --output results/retrieval.json
python3 -m ecocausal simulate --output results/simulation.json
python3 -m ecocausal expert-template --claims results/demo/report.json --out results/expert_ratings_BLANK.csv
