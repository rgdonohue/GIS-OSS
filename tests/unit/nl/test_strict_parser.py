from __future__ import annotations

import pytest

from src.nl.strict_parser import NaturalQueryParseError, parse_natural_query_prompt


def test_parse_natural_query_prompt_buffer_success():
    prompt = (
        "Please execute this operation: "
        '{"operation":"buffer","geometry":{"type":"Point","coordinates":[0,0]},'
        '"distance":100,"units":"meters"}'
    )

    parsed = parse_natural_query_prompt(prompt)

    assert parsed["operation"] == "buffer"
    assert parsed["distance"] == 100
    assert parsed["units"] == "meters"
    assert parsed["geometry"]["type"] == "Point"


def test_parse_natural_query_prompt_rejects_missing_json():
    with pytest.raises(NaturalQueryParseError) as exc_info:
        parse_natural_query_prompt("buffer this point by 100 meters")

    assert "structured operation JSON object" in str(exc_info.value)


def test_parse_natural_query_prompt_rejects_unknown_operation():
    prompt = '{"operation":"dissolve","geometry":{"type":"Point","coordinates":[0,0]}}'
    with pytest.raises(NaturalQueryParseError) as exc_info:
        parse_natural_query_prompt(prompt)

    assert "Unsupported operation" in str(exc_info.value)


def test_parse_natural_query_prompt_rejects_multiple_operation_objects():
    prompt = (
        '{"operation":"buffer","geometry":{"type":"Point","coordinates":[0,0]},"distance":1}'
        ' and '
        '{"operation":"calculate_area","geometry":{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,0]]]}}'
    )

    with pytest.raises(NaturalQueryParseError) as exc_info:
        parse_natural_query_prompt(prompt)

    assert "Multiple operation JSON objects" in str(exc_info.value)
