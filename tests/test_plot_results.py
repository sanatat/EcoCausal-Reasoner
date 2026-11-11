"""Smoke-test that project diagrams are produced from data, not pasted numbers."""
import json
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def test_plot_results_cli_renders_data_driven_svg(tmp_path):
    results = tmp_path / "results"
    (results / "demo").mkdir(parents=True)
    for src, dst in [
        (ROOT / "results" / "retrieval.json", results / "retrieval.json"),
        (ROOT / "results" / "simulation.json", results / "simulation.json"),
        (ROOT / "results" / "demo" / "report.json", results / "demo" / "report.json"),
    ]:
        dst.write_bytes(src.read_bytes())

    output = tmp_path / "figures"
    cmd = [
        sys.executable, str(ROOT / "scripts" / "plot_results.py"),
        "--results-dir", str(results), "--out-dir", str(output),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    expected = [
        "retrieval_benchmark.svg",
        "synthetic_causal_effect.svg",
        "synthetic_world_model_rmse.svg",
        "evidence_provenance.svg",
    ]
    for name in expected:
        path = output / name
        assert path.is_file() and path.stat().st_size > 500
        root = ET.parse(path).getroot()
        assert root.tag.endswith("svg")

    original = (output / "synthetic_causal_effect.svg").read_text()
    doc = json.loads((results / "simulation.json").read_text())
    doc["synthetic_scm"]["estimated_ate"] = 5.74321
    (results / "simulation.json").write_text(json.dumps(doc))
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    changed = (output / "synthetic_causal_effect.svg").read_text()
    assert original != changed
    assert "5.743" in changed
