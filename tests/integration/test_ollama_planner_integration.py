from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")

from src.api.main import app, get_db_connection  # noqa: E402

pytestmark = pytest.mark.integration


def _fake_db_conn() -> Generator[MagicMock, None, None]:
    conn = MagicMock(name="connection")
    yield conn


def _ollama_ready(base_url: str, model: str) -> tuple[bool, str]:
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=2)
        response.raise_for_status()
    except Exception as exc:  # pragma: no cover - integration-only skip path
        return False, f"Ollama not reachable at {base_url}: {exc}"

    payload = response.json()
    models = payload.get("models", []) if isinstance(payload, dict) else []
    names = [item.get("name") for item in models if isinstance(item, dict)]
    names = [name for name in names if isinstance(name, str)]

    if not names:
        return False, "Ollama is reachable but no models are installed."

    if model in names:
        return True, ""

    model_base = model.split(":", 1)[0]
    if any(name == model_base or name.startswith(f"{model_base}:") for name in names):
        return True, ""

    return False, f"Required model '{model}' not present. Available: {', '.join(names)}"


def test_query_local_planner_with_live_ollama(monkeypatch):
    if os.environ.get("ENABLE_OLLAMA_INTEGRATION", "0") != "1":
        pytest.skip("Set ENABLE_OLLAMA_INTEGRATION=1 to run live Ollama integration test.")

    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")

    ready, reason = _ollama_ready(base_url, model)
    if not ready:
        pytest.skip(reason)

    app.dependency_overrides[get_db_connection] = _fake_db_conn

    monkeypatch.setattr("src.api.main.settings.enable_local_llm_planner", True)
    monkeypatch.setattr("src.api.main.settings.llm_provider", "ollama")
    monkeypatch.setattr("src.api.main.settings.llm_ollama_base_url", base_url)
    monkeypatch.setattr("src.api.main.settings.llm_model", model)
    monkeypatch.setattr("src.api.main.settings.llm_timeout_seconds", 20)
    monkeypatch.setattr("src.api.main.settings.llm_max_retries", 0)
    monkeypatch.setattr("src.api.main.settings.enable_audit_log", False)

    monkeypatch.setattr(
        "src.api.main.buffer_geometry",
        lambda *args, **kwargs: {
            "type": "Polygon",
            "coordinates": [[[-122.42, 37.77], [-122.41, 37.77], [-122.41, 37.78], [-122.42, 37.77]]],
        },
    )

    client = TestClient(app)
    try:
        response = client.post(
            "/query",
            headers={"X-API-Key": ""},
            json={
                "prompt": (
                    "Create a buffer operation around point longitude -122.42 latitude 37.77 "
                    "with distance 250 meters. Return a JSON operation object only."
                )
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["status"] == "completed"
    assert payload["request"]["operation"] == "buffer"
    assert payload["request"]["geometry"]["type"] == "Point"
    assert payload["request"]["distance"] > 0
    assert payload["verification_status"] == "verified"
