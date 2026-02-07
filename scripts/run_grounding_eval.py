#!/usr/bin/env python3
"""Run deterministic grounding regression cases from eval fixtures."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = ROOT / "evals" / "grounding_cases.json"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.main import QueryRequest, _build_grounding_evidence  # noqa: E402
from src.nl import NaturalQueryParseError, parse_natural_query_prompt  # noqa: E402


def _load_cases(path: pathlib.Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Eval fixture must be a JSON list.")
    return payload


def run_cases(cases: list[dict[str, object]]) -> tuple[int, int]:
    passed = 0
    failed = 0

    for case in cases:
        case_id = str(case.get("id", "unknown"))
        prompt = str(case.get("prompt", ""))
        expect = case.get("expect")
        if not isinstance(expect, dict):
            print(f"[FAIL] {case_id}: missing 'expect' object")
            failed += 1
            continue

        expected_status = str(expect.get("status", ""))
        try:
            parsed = parse_natural_query_prompt(prompt)
            request = QueryRequest.model_validate({"prompt": prompt, **parsed})
            verification_status, _ = _build_grounding_evidence(request)

            if expected_status != "success":
                print(f"[FAIL] {case_id}: expected error but parser succeeded")
                failed += 1
                continue

            expected_operation = str(expect.get("operation", ""))
            expected_verification = str(expect.get("verification_status", ""))

            if parsed.get("operation") != expected_operation:
                print(
                    f"[FAIL] {case_id}: operation mismatch "
                    f"expected={expected_operation} actual={parsed.get('operation')}"
                )
                failed += 1
                continue
            if verification_status != expected_verification:
                print(
                    f"[FAIL] {case_id}: verification mismatch "
                    f"expected={expected_verification} actual={verification_status}"
                )
                failed += 1
                continue

            print(f"[PASS] {case_id}")
            passed += 1
        except NaturalQueryParseError as exc:
            if expected_status != "error":
                print(f"[FAIL] {case_id}: unexpected parse error: {exc}")
                failed += 1
                continue

            expected_substring = str(expect.get("error_contains", ""))
            if expected_substring and expected_substring not in str(exc):
                print(
                    f"[FAIL] {case_id}: error mismatch "
                    f"expected substring={expected_substring!r} actual={str(exc)!r}"
                )
                failed += 1
                continue

            print(f"[PASS] {case_id}")
            passed += 1

    return passed, failed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run grounding eval fixture checks.")
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
