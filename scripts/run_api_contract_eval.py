#!/usr/bin/env python3
"""Run API-level contract and grounding checks from fixture cases."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = ROOT / "evals" / "api_contract_cases.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("APP_ENV", "test")

from fastapi.testclient import TestClient  # noqa: E402

import src.api.main as api_main  # noqa: E402
from src.api.main import app, get_db_connection, settings  # noqa: E402


def _fake_db_conn() -> Generator[MagicMock, None, None]:
    conn = MagicMock(name="connection")
    yield conn


def _fake_buffer(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [[[-122.42, 37.77], [-122.41, 37.77], [-122.41, 37.78], [-122.42, 37.77]]],
    }


def _fake_nearest(*_args: Any, **_kwargs: Any) -> list[dict[str, Any]]:
    return [{"id": "fixture-1", "geometry": None, "distance_meters": 12.5}]


def _load_cases(path: pathlib.Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Contract fixture must be a JSON list.")
    return payload


def _assert_success_contract(case_id: str, body: dict[str, Any], expect: dict[str, Any]) -> str | None:
    expected_status = expect.get("status")
    if expected_status is not None and body.get("status") != expected_status:
        return f"status mismatch expected={expected_status!r} actual={body.get('status')!r}"

    expected_verification = expect.get("verification_status")
    if expected_verification is not None and body.get("verification_status") != expected_verification:
        return (
            "verification_status mismatch "
            f"expected={expected_verification!r} actual={body.get('verification_status')!r}"
        )

    request = body.get("request")
    if not isinstance(request, dict):
        return "response.request missing or not an object"

    expected_operation = expect.get("operation")
    if expected_operation is not None and request.get("operation") != expected_operation:
        return (
            "request.operation mismatch "
            f"expected={expected_operation!r} actual={request.get('operation')!r}"
        )

    evidence = body.get("evidence")
    if not isinstance(evidence, list):
        return "evidence missing or not a list"

    expected_evidence_len = expect.get("evidence_length")
    if expected_evidence_len is not None and len(evidence) != int(expected_evidence_len):
        return (
            "evidence length mismatch "
            f"expected={expected_evidence_len} actual={len(evidence)}"
        )

    return None


def run_cases(cases: list[dict[str, Any]]) -> tuple[int, int]:
    passed = 0
    failed = 0

    original_buffer = api_main.buffer_geometry
    original_nearest = api_main.nearest_neighbors
    original_enable_audit_log = settings.enable_audit_log
    original_enable_local_planner = settings.enable_local_llm_planner

    app.dependency_overrides[get_db_connection] = _fake_db_conn
    api_main.buffer_geometry = _fake_buffer
    api_main.nearest_neighbors = _fake_nearest
    settings.enable_audit_log = False
    settings.enable_local_llm_planner = False

    client = TestClient(app)

    try:
        for case in cases:
            case_id = str(case.get("id", "unknown"))
            endpoint = str(case.get("endpoint", "")).strip()
            payload = case.get("payload")
            expect = case.get("expect")

            if endpoint not in {"/query", "/query/natural"}:
                print(f"[FAIL] {case_id}: unsupported endpoint {endpoint!r}")
                failed += 1
                continue
            if not isinstance(payload, dict):
                print(f"[FAIL] {case_id}: payload must be an object")
                failed += 1
                continue
            if not isinstance(expect, dict):
                print(f"[FAIL] {case_id}: expect must be an object")
                failed += 1
                continue

            expected_status_code = int(expect.get("status_code", 200))
            response = client.post(endpoint, json=payload)

            if response.status_code != expected_status_code:
                print(
                    f"[FAIL] {case_id}: status_code mismatch "
                    f"expected={expected_status_code} actual={response.status_code}"
                )
                failed += 1
                continue

            body = response.json()
            expected_result = str(expect.get("result", "success"))

            if expected_result == "error":
                expected_substring = str(expect.get("error_contains", ""))
                detail = body.get("detail", "") if isinstance(body, dict) else ""
                if expected_substring and expected_substring not in str(detail):
                    print(
                        f"[FAIL] {case_id}: error detail mismatch "
                        f"expected_substring={expected_substring!r} actual={detail!r}"
                    )
                    failed += 1
                    continue
                print(f"[PASS] {case_id}")
                passed += 1
                continue

            if not isinstance(body, dict):
                print(f"[FAIL] {case_id}: success response is not an object")
                failed += 1
                continue

            contract_error = _assert_success_contract(case_id, body, expect)
            if contract_error is not None:
                print(f"[FAIL] {case_id}: {contract_error}")
                failed += 1
                continue

            print(f"[PASS] {case_id}")
            passed += 1
    finally:
        app.dependency_overrides.pop(get_db_connection, None)
        api_main.buffer_geometry = original_buffer
        api_main.nearest_neighbors = original_nearest
        settings.enable_audit_log = original_enable_audit_log
        settings.enable_local_llm_planner = original_enable_local_planner

    return passed, failed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run API contract eval fixture checks.")
    parser.add_argument(
        "--cases",
        type=pathlib.Path,
        default=DEFAULT_CASES_PATH,
        help=f"Path to fixture file (default: {DEFAULT_CASES_PATH.relative_to(ROOT)})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = _load_cases(args.cases)
    passed, failed = run_cases(cases)
    print(f"\nSummary: passed={passed} failed={failed} total={passed + failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
