from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "verify_sample_data_provenance.py"


def test_verify_sample_data_provenance_accepts_valid_manifest(tmp_path: Path):
    manifest = {
        "version": 1,
        "datasets": [
            {
                "id": "example",
                "title": "Example dataset",
                "source_url": "https://example.com/data.geojson",
                "license": "CC-BY-4.0",
                "attribution": "Example attribution",
                "local_relative_path": "data/example.geojson",
            }
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--manifest", str(manifest_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Verified 1 dataset definition" in result.stdout


def test_verify_sample_data_provenance_rejects_missing_required_fields(tmp_path: Path):
    manifest = {
        "version": 1,
        "datasets": [
            {
                "id": "broken",
                "title": "Broken dataset",
                "source_url": "https://example.com/data.geojson",
                "license": "CC-BY-4.0",
                "local_relative_path": "data/example.geojson",
            }
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--manifest", str(manifest_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "missing required fields" in result.stdout
