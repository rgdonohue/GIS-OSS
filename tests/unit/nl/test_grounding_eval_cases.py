from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.api.main import QueryRequest, _build_grounding_evidence
from src.nl import NaturalQueryParseError, parse_natural_query_prompt

CASES_PATH = Path(__file__).resolve().parents[3] / "evals" / "grounding_cases.json"


@pytest.mark.parametrize("case", json.loads(CASES_PATH.read_text(encoding="utf-8")))
def test_grounding_eval_cases(case: dict[str, object]):
    prompt = str(case["prompt"])
    expect = case["expect"]
    assert isinstance(expect, dict)

    expected_status = str(expect["status"])

    if expected_status == "success":
        parsed = parse_natural_query_prompt(prompt)
        request = QueryRequest.model_validate({"prompt": prompt, **parsed})
        verification_status, _ = _build_grounding_evidence(request)

        assert parsed["operation"] == expect["operation"]
        assert verification_status == expect["verification_status"]
        return

    with pytest.raises(NaturalQueryParseError) as exc_info:
        parse_natural_query_prompt(prompt)

    expected_substring = str(expect["error_contains"])
    assert expected_substring in str(exc_info.value)
