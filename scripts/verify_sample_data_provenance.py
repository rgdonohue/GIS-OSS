#!/usr/bin/env python3
"""Validate sample data provenance metadata and optional local file hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config" / "sample_data_manifest.json"
_REQUIRED_DATASET_FIELDS = {
    "id",
    "title",
    "source_url",
    "license",
    "attribution",
    "local_relative_path",
}


def _load_manifest(path: pathlib.Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manifest root must be a JSON object.")
    return payload


def _sha256(path: pathlib.Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as infile:
        for chunk in iter(lambda: infile.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _validate_dataset(
    dataset: dict[str, Any],
    *,
    require_local: bool,
) -> list[str]:
    errors: list[str] = []

    missing = sorted(field for field in _REQUIRED_DATASET_FIELDS if not dataset.get(field))
    dataset_id = str(dataset.get("id", "unknown"))
    if missing:
        errors.append(f"[{dataset_id}] missing required fields: {', '.join(missing)}")

    source_url = str(dataset.get("source_url", ""))
    if source_url and not source_url.startswith(("http://", "https://")):
        errors.append(f"[{dataset_id}] source_url must be http/https")

    local_relative_path = str(dataset.get("local_relative_path", ""))
    if local_relative_path:
        local_path = ROOT / local_relative_path
        exists = local_path.exists()
        if require_local and not exists:
            errors.append(f"[{dataset_id}] local file missing: {local_relative_path}")

        expected_sha = str(dataset.get("expected_sha256", "")).strip().lower()
        if expected_sha:
            if not exists:
                errors.append(
                    f"[{dataset_id}] expected_sha256 set but local file missing: {local_relative_path}"
                )
            else:
                actual_sha = _sha256(local_path)
                if actual_sha != expected_sha:
                    errors.append(
                        f"[{dataset_id}] sha256 mismatch expected={expected_sha} actual={actual_sha}"
                    )

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify sample data provenance manifest.")
    parser.add_argument(
        "--manifest",
        type=pathlib.Path,
        default=DEFAULT_MANIFEST,
        help=f"Manifest path (default: {DEFAULT_MANIFEST.relative_to(ROOT)})",
    )
    parser.add_argument(
        "--require-local",
        action="store_true",
        help="Fail if local data files in manifest are missing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = _load_manifest(args.manifest)

    datasets = manifest.get("datasets")
    if not isinstance(datasets, list):
        print("Manifest must include a 'datasets' list.")
        return 1

    all_errors: list[str] = []
    for entry in datasets:
        if not isinstance(entry, dict):
            all_errors.append("Dataset entries must be objects.")
            continue
        all_errors.extend(_validate_dataset(entry, require_local=args.require_local))

    if all_errors:
        for error in all_errors:
            print(f"ERROR: {error}")
        print(f"\nVerification failed with {len(all_errors)} error(s).")
        return 1

    print(f"Verified {len(datasets)} dataset definition(s) in {args.manifest}.")
    if not args.require_local:
        print("Note: local file existence not enforced. Use --require-local for strict checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
