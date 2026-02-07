from __future__ import annotations

import hashlib
import json
from typing import Any

from psycopg2.extensions import connection as PGConnection


def _hash_identifier(value: str) -> str:
    normalized = value.strip() or "anonymous"
    digest = hashlib.sha256(normalized.encode("utf-8", errors="ignore")).hexdigest()
    return f"sha256:{digest}"


def _redacted_query_text(prompt: str) -> str:
    normalized = prompt.strip()
    digest = hashlib.sha256(normalized.encode("utf-8", errors="ignore")).hexdigest()
    return f"redacted:sha256:{digest}:len:{len(normalized)}"


def _sanitize_error_message(error_message: str | None) -> str | None:
    if error_message is None:
        return None
    flattened = " ".join(error_message.split())
    return flattened[:300]


def _summarize_geometry(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    geometry_type = value.get("type")
    return {
        "type": geometry_type if isinstance(geometry_type, str) else "unknown",
        "has_coordinates": "coordinates" in value,
    }


def _redact_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if metadata is None:
        return {}

    redacted: dict[str, Any] = {}
    for key, value in metadata.items():
        lowered = key.lower()
        if lowered in {"prompt", "query_text", "api_key", "x_api_key"}:
            continue
        if key in {"geometry", "geometry_b"}:
            redacted[f"{key}_summary"] = _summarize_geometry(value)
            continue
        redacted[key] = value
    return redacted


def log_query_event(
    conn: PGConnection,
    *,
    user_identifier: str,
    prompt: str,
    query_type: str | None,
    execution_time_ms: int,
    status: str,
    error_message: str | None = None,
    data_sources: list[str] | None = None,
    attribution: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Persist an audit event for an incoming query.

    Sensitive fields are redacted/hardened:
    - User identifiers are hashed.
    - Prompt text is not stored in cleartext.
    - Geometry payloads in metadata are summarized without coordinates.
    """

    safe_user_id = _hash_identifier(user_identifier)
    safe_query_text = _redacted_query_text(prompt)
    safe_error = _sanitize_error_message(error_message)
    safe_sources = data_sources or []
    safe_attribution = attribution or {"prompt_policy": "redacted", "user_policy": "hashed"}
    safe_metadata = _redact_metadata(metadata)

    query = """
        INSERT INTO audit.query_log (
            user_id,
            query_text,
            query_type,
            execution_time_ms,
            status,
            error_message,
            data_sources,
            attribution,
            metadata
        ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb)
    """

    with conn.cursor() as cur:
        cur.execute(
            query,
            (
                safe_user_id,
                safe_query_text,
                query_type,
                execution_time_ms,
                status,
                safe_error,
                json.dumps(safe_sources),
                json.dumps(safe_attribution),
                json.dumps(safe_metadata),
            ),
        )
