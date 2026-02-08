from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "fetch_authoritative_dataset.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fetch_authoritative_dataset_from_file_url(tmp_path: Path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"authoritative-source")

    destination = tmp_path / "download.bin"
    manifest = {
        "version": 1,
        "datasets": [
            {
                "id": "fixture",
                "source_url": source.resolve().as_uri(),
                "local_relative_path": str(destination),
                "expected_sha256": _sha256(source),
            }
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--dataset-id",
            "fixture",
            "--manifest",
            str(manifest_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert destination.exists()
    assert _sha256(destination) == _sha256(source)
    assert "SHA-256 matches manifest." in result.stdout


def test_fetch_authoritative_dataset_detects_sha_mismatch(tmp_path: Path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"authoritative-source")

    destination = tmp_path / "download.bin"
    manifest = {
        "version": 1,
        "datasets": [
            {
                "id": "fixture",
                "source_url": source.resolve().as_uri(),
                "local_relative_path": str(destination),
                "expected_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
            }
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--dataset-id",
            "fixture",
            "--manifest",
            str(manifest_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "SHA-256 mismatch" in result.stdout
