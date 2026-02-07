from __future__ import annotations

import json
from unittest.mock import MagicMock

from src.governance.audit_logger import log_query_event


def _mock_connection():
    conn = MagicMock(name="connection")
    cursor = MagicMock(name="cursor")
    conn.cursor.return_value.__enter__.return_value = cursor
    return conn, cursor


def test_log_query_event_redacts_prompt_and_hashes_user_identifier():
    conn, cursor = _mock_connection()
    raw_prompt = "Sacred site near [12.34,56.78]"
    raw_user = "real-api-key-123"

    log_query_event(
        conn,
        user_identifier=raw_user,
        prompt=raw_prompt,
        query_type="buffer",
        execution_time_ms=42,
        status="completed",
        data_sources=["data.features"],
        metadata={"operation": "buffer", "geometry": {"type": "Point", "coordinates": [1, 2]}},
    )

    cursor.execute.assert_called_once()
    _, params = cursor.execute.call_args.args

    user_id = params[0]
    query_text = params[1]
    metadata_json = params[8]

    assert user_id.startswith("sha256:")
    assert raw_user not in user_id
    assert "Sacred site" not in query_text
    assert "redacted:sha256:" in query_text

    metadata = json.loads(metadata_json)
    assert metadata["geometry_summary"]["type"] == "Point"
    assert metadata["geometry_summary"]["has_coordinates"] is True
    assert "geometry" not in metadata


def test_log_query_event_sanitizes_error_message():
    conn, cursor = _mock_connection()
    raw_error = "bad input\nwith newline\tand tabs"

    log_query_event(
        conn,
        user_identifier="user",
        prompt="prompt",
        query_type="buffer",
        execution_time_ms=5,
        status="invalid_parameters",
        error_message=raw_error,
    )

    cursor.execute.assert_called_once()
    _, params = cursor.execute.call_args.args
    assert params[5] == "bad input with newline and tabs"
