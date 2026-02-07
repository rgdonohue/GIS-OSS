import os
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")

from src.api.config import Settings, get_settings  # noqa: E402
from src.api.main import app, get_db_connection, require_api_key  # noqa: E402


def _fake_db_conn() -> Generator[MagicMock, None, None]:
    """Fake DB connection generator for testing."""
    conn = MagicMock(name="connection")
    yield conn


client = TestClient(app)


def _override_dependencies(api_key: str = "") -> None:
    app.dependency_overrides[get_db_connection] = _fake_db_conn
    app.dependency_overrides[get_settings] = lambda: Settings(
        api_key=api_key,
        environment="test",
        authz_backend="static",
        db_password="ignored",
    )


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_query_requires_api_key():
    _override_dependencies(api_key="secret")
    response = client.post(
        "/query",
        json={"prompt": "Hi", "return_format": "geojson"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key."
    _clear_overrides()


def test_require_api_key_database_mode_rejects_empty_when_public_disabled(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    settings = Settings(
        environment="development",
        authz_backend="database",
        allow_public_api=False,
        api_key="",
    )
    with pytest.raises(HTTPException) as exc_info:
        require_api_key(x_api_key="", settings=settings)

    assert "Invalid API key" in str(exc_info.value.detail)


def test_require_api_key_database_mode_allows_empty_when_public_enabled(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    settings = Settings(
        environment="development",
        authz_backend="database",
        allow_public_api=True,
        api_key="",
    )
    require_api_key(x_api_key="", settings=settings)


def test_require_api_key_static_mode_requires_configured_key(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    settings = Settings(
        environment="development",
        authz_backend="static",
        api_key="",
    )
    with pytest.raises(HTTPException) as exc_info:
        require_api_key(x_api_key="any", settings=settings)

    assert "API key not configured" in str(exc_info.value.detail)


def test_query_pending_when_operation_missing():
    _override_dependencies()
    response = client.post(
        "/query",
        headers={"X-API-Key": ""},
        json={"prompt": "Summarize parks", "return_format": "geojson"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert "Provide 'operation'" in data["message"]
    assert data["verification_status"] == "unverified"
    assert data["evidence"] == []
    _clear_overrides()


def test_query_pending_writes_audit_event(monkeypatch):
    _override_dependencies()
    calls: list[dict[str, object]] = []

    def fake_log_query_event(conn, **kwargs):
        calls.append(kwargs)

    monkeypatch.setattr("src.api.main.log_query_event", fake_log_query_event)

    response = client.post(
        "/query",
        headers={"X-API-Key": "demo-key"},
        json={"prompt": "Summarize parks", "return_format": "geojson"},
    )
    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0]["status"] == "pending"
    assert calls[0]["query_type"] == "nl_pending"
    assert calls[0]["user_identifier"] == "demo-key"
    _clear_overrides()


def test_query_natural_rejects_unparseable_prompt():
    _override_dependencies()
    response = client.post(
        "/query/natural",
        headers={"X-API-Key": ""},
        json={"prompt": "Find nearby parks", "return_format": "geojson"},
    )
    assert response.status_code == 400
    assert "structured operation JSON object" in response.json()["detail"]
    _clear_overrides()


def test_query_natural_writes_parse_error_audit_event(monkeypatch):
    _override_dependencies()
    calls: list[dict[str, object]] = []

    def fake_log_query_event(conn, **kwargs):
        calls.append(kwargs)

    monkeypatch.setattr("src.api.main.log_query_event", fake_log_query_event)

    response = client.post(
        "/query/natural",
        headers={"X-API-Key": "demo-key"},
        json={"prompt": "Find nearby parks", "return_format": "geojson"},
    )
    assert response.status_code == 400
    assert len(calls) == 1
    assert calls[0]["status"] == "parse_error"
    _clear_overrides()


def test_query_natural_executes_parsed_operation(monkeypatch):
    _override_dependencies()
    fake_geometry = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}

    def fake_buffer(conn, geom, distance, units, srid):
        return fake_geometry

    monkeypatch.setattr("src.api.main.buffer_geometry", fake_buffer)

    response = client.post(
        "/query/natural",
        headers={"X-API-Key": ""},
        json={
            "prompt": (
                "Run this: "
                '{"operation":"buffer","geometry":{"type":"Point","coordinates":[0,0]},'
                '"distance":100,"units":"meters"}'
            ),
            "return_format": "geojson",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["result"]["geometry"] == fake_geometry
    assert data["request"]["operation"] == "buffer"
    assert data["verification_status"] == "verified"
    assert data["evidence"][0]["source_kind"] == "input_geometry"
    _clear_overrides()


def test_query_buffer_operation(monkeypatch):
    _override_dependencies()
    fake_geometry = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}

    def fake_buffer(conn, geom, distance, units, srid):
        return fake_geometry

    monkeypatch.setattr("src.api.main.buffer_geometry", fake_buffer)

    response = client.post(
        "/query",
        headers={"X-API-Key": ""},
        json={
            "prompt": "Buffer a point",
            "operation": "buffer",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "distance": 100,
            "units": "meters",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["result"]["geometry"] == fake_geometry
    assert data["verification_status"] == "verified"
    assert data["evidence"][0]["source_id"] == "request.geometry"
    _clear_overrides()


def test_query_invalid_parameters(monkeypatch):
    _override_dependencies()

    response = client.post(
        "/query",
        headers={"X-API-Key": ""},
        json={
            "prompt": "Buffer missing distance",
            "operation": "buffer",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
        },
    )
    assert response.status_code == 400
    assert "requires 'geometry' and 'distance'" in response.json()["detail"]
    _clear_overrides()


def test_query_invalid_parameters_writes_audit_event(monkeypatch):
    _override_dependencies()
    calls: list[dict[str, object]] = []

    def fake_log_query_event(conn, **kwargs):
        calls.append(kwargs)

    monkeypatch.setattr("src.api.main.log_query_event", fake_log_query_event)

    response = client.post(
        "/query",
        headers={"X-API-Key": "demo-key"},
        json={
            "prompt": "Buffer missing distance",
            "operation": "buffer",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
        },
    )
    assert response.status_code == 400
    assert len(calls) == 1
    assert calls[0]["status"] == "invalid_parameters"
    assert "requires 'geometry' and 'distance'" in str(calls[0]["error_message"])
    _clear_overrides()


def test_query_rejects_non_allowlisted_table():
    _override_dependencies()
    response = client.post(
        "/query",
        headers={"X-API-Key": ""},
        json={
            "prompt": "Find nearest features",
            "operation": "nearest_neighbors",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "table": "audit.query_log",
            "limit": 1,
        },
    )
    assert response.status_code == 400
    assert "not permitted" in response.json()["detail"]
    _clear_overrides()


def test_query_nearest_neighbors_marks_response_unverified(monkeypatch):
    _override_dependencies()

    def fake_nearest(conn, geom, table, limit, srid):
        return [{"id": "feature-1", "geometry": None, "distance_meters": 1.0}]

    monkeypatch.setattr("src.api.main.nearest_neighbors", fake_nearest)

    response = client.post(
        "/query",
        headers={"X-API-Key": ""},
        json={
            "prompt": "Find nearest features",
            "operation": "nearest_neighbors",
            "geometry": {"type": "Point", "coordinates": [0, 0]},
            "table": "data.features",
            "limit": 1,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["verification_status"] == "unverified"
    assert data["evidence"][0]["source_id"] == "data.features"
    assert data["evidence"][0]["verification"] == "unverified"
    _clear_overrides()
