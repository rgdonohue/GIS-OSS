#!/usr/bin/env python3
"""Fetch a dataset declared in the provenance manifest and verify optional SHA-256."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import sys
import urllib.parse
import urllib.request
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config" / "sample_data_manifest.json"


def _load_manifest(path: pathlib.Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Manifest root must be a JSON object.")
    return payload


def _resolve_dataset(manifest: dict[str, Any], dataset_id: str) -> dict[str, Any]:
    datasets = manifest.get("datasets")
    if not isinstance(datasets, list):
        raise ValueError("Manifest must include a 'datasets' list.")

    for dataset in datasets:
        if isinstance(dataset, dict) and str(dataset.get("id", "")).strip() == dataset_id:
            return dataset

    raise ValueError(f"Dataset id '{dataset_id}' not found in manifest.")


def _resolve_local_path(local_relative_path: str) -> pathlib.Path:
    candidate = pathlib.Path(local_relative_path)
    if candidate.is_absolute():
        return candidate
    return ROOT / candidate


def _sha256(path: pathlib.Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as infile:
        for chunk in iter(lambda: infile.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _download(url: str, destination: pathlib.Path, *, timeout_seconds: int, allow_http: bool) -> None:
    parsed = urllib.parse.urlparse(url)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if parsed.scheme == "file":
        source_path = pathlib.Path(urllib.request.url2pathname(parsed.path))
        if not source_path.exists():
            raise ValueError(f"Source file does not exist: {source_path}")
        shutil.copyfile(source_path, destination)
        return

    if parsed.scheme not in {"https", "http"}:
        raise ValueError(f"Unsupported URL scheme '{parsed.scheme}'.")

    if parsed.scheme == "http" and not allow_http:
        raise ValueError("HTTP downloads are disabled by default. Use --allow-http to override.")

    with urllib.request.urlopen(url, timeout=timeout_seconds) as response, destination.open("wb") as out:
        shutil.copyfileobj(response, out)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and verify one authoritative dataset.")
    parser.add_argument(
        "--dataset-id",
        required=True,
        help="Dataset id from config/sample_data_manifest.json",
    )
    parser.add_argument(
        "--manifest",
        type=pathlib.Path,
        default=DEFAULT_MANIFEST,
        help=f"Manifest path (default: {DEFAULT_MANIFEST.relative_to(ROOT)})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the local file already exists.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=60,
        help="HTTP request timeout in seconds.",
    )
    parser.add_argument(
        "--allow-http",
        action="store_true",
        help="Allow non-TLS HTTP sources (disabled by default).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        manifest = _load_manifest(args.manifest)
        dataset = _resolve_dataset(manifest, args.dataset_id)

        source_url = str(dataset.get("source_url", "")).strip()
        local_relative_path = str(dataset.get("local_relative_path", "")).strip()
        if not source_url:
            raise ValueError(f"Dataset '{args.dataset_id}' is missing source_url.")
        if not local_relative_path:
            raise ValueError(f"Dataset '{args.dataset_id}' is missing local_relative_path.")

        local_path = _resolve_local_path(local_relative_path)
        if args.force or not local_path.exists():
            _download(
                source_url,
                local_path,
                timeout_seconds=args.timeout_seconds,
                allow_http=args.allow_http,
            )
            print(f"Downloaded: {source_url} -> {local_path}")
        else:
            print(f"Using existing file: {local_path}")

        actual_sha = _sha256(local_path)
        expected_sha = str(dataset.get("expected_sha256", "")).strip().lower()

        print(f"sha256: {actual_sha}")
        if expected_sha:
            if actual_sha != expected_sha:
                print(
                    f"ERROR: SHA-256 mismatch for dataset '{args.dataset_id}'. "
                    f"expected={expected_sha} actual={actual_sha}"
                )
                return 1
            print("SHA-256 matches manifest.")
        else:
            print(
                "No expected_sha256 set in manifest. "
                "Copy this SHA into config/sample_data_manifest.json to pin the dataset."
            )

        return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
