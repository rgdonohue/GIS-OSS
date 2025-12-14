import os
from collections.abc import Generator
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")

from src.api.config import Settings, get_settings
from src.api.main import app, get_db_connection


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
