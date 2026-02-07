from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

os.environ.setdefault("APP_ENV", "test")

from src.api.config import Settings, get_settings  # noqa: E402
from src.api.main import app, get_db_connection  # noqa: E402


def _fake_db_conn() -> Generator[MagicMock, None, None]:
    conn = MagicMock(name="connection")
    yield conn


client = TestClient(app)


def _override_dependencies() -> None:
    app.dependency_overrides[get_db_connection] = _fake_db_conn
    app.dependency_overrides[get_settings] = lambda: Settings(
        environment="test",
        db_password="ignored",
    )


def _clear_overrides() -> None:
    app.dependency_overrides.clear()


def test_grounding_regression_unknown_operation_is_rejected():
    _override_dependencies()
    response = client.post(
        "/query/natural",
        json={
            "prompt": (
                "Run this: "
                '{"operation":"dissolve","geometry":{"type":"Point","coordinates":[0,0]}}'
            )
        },
    )
    assert response.status_code == 400
    assert "Unsupported operation" in response.json()["detail"]
    _clear_overrides()


def test_grounding_regression_prose_only_prompt_is_rejected():
    _override_dependencies()
    response = client.post("/query/natural", json={"prompt": "Find nearby parks"})
    assert response.status_code == 400
    assert "structured operation JSON object" in response.json()["detail"]
    _clear_overrides()


def test_grounding_regression_multiple_json_operations_are_rejected():
    _override_dependencies()
    response = client.post(
        "/query/natural",
        json={
            "prompt": (
                '{"operation":"buffer","geometry":{"type":"Point","coordinates":[0,0]},"distance":1}'
                ' and '
                '{"operation":"calculate_area","geometry":{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,0]]]}}'
            )
        },
    )
    assert response.status_code == 400
    assert "Multiple operation JSON objects" in response.json()["detail"]
    _clear_overrides()


def test_grounding_regression_disallowed_table_is_rejected(monkeypatch):
    _override_dependencies()

    def fake_nearest(conn, geom, table, limit, srid):  # pragma: no cover
        return []

    monkeypatch.setattr("src.api.main.nearest_neighbors", fake_nearest)

    response = client.post(
        "/query/natural",
        json={
            "prompt": (
                "Run this: "
                '{"operation":"nearest_neighbors","geometry":{"type":"Point","coordinates":[0,0]},'
                '"table":"audit.query_log","limit":1}'
            )
        },
    )
    assert response.status_code == 400
    assert "not permitted" in response.json()["detail"]
    _clear_overrides()
