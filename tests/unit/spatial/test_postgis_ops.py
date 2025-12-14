from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from src.spatial import (
    buffer_geometry,
    calculate_area,
    find_intersections,
    nearest_neighbors,
    transform_crs,
)


def _mock_connection(fetchone=None, fetchall=None):
    conn = MagicMock(name="connection")
    cursor = MagicMock(name="cursor")
    conn.cursor.return_value.__enter__.return_value = cursor
    if fetchone is not None:
        cursor.fetchone.return_value = fetchone
    if fetchall is not None:
        cursor.fetchall.return_value = fetchall
    return conn, cursor


def test_buffer_geometry_returns_geojson():
    geom = {"type": "Point", "coordinates": [-75.0, 40.0]}
    fake_polygon = {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}
    conn, cursor = _mock_connection(fetchone=(json.dumps(fake_polygon),))

    result = buffer_geometry(conn, geom, distance=100, units="meters")

    cursor.execute.assert_called_once()
    assert result["type"] == "Polygon"
    assert result["coordinates"] == fake_polygon["coordinates"]


def test_buffer_geometry_invalid_unit_raises():
    geom = {"type": "Point", "coordinates": [0, 0]}
    conn, _ = _mock_connection()
    with pytest.raises(ValueError):
        buffer_geometry(conn, geom, distance=100, units="parsecs")


def test_calculate_area_converts_units():
    geom = {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [0, 0]]]}
    conn, cursor = _mock_connection(fetchone=(10_000.0,))

    hectares = calculate_area(conn, geom, units="hectares")

    cursor.execute.assert_called_once()
    assert pytest.approx(hectares, rel=1e-3) == 1.0


def test_calculate_area_invalid_units():
    geom = {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [0, 0]]]}
    conn, _ = _mock_connection(fetchone=(10_000.0,))

    with pytest.raises(ValueError):
        calculate_area(conn, geom, units="square-furlongs")


def test_find_intersections_returns_none_on_empty():
    geom_a = {"type": "Point", "coordinates": [0, 0]}
    geom_b = {"type": "Point", "coordinates": [10, 10]}
    conn, cursor = _mock_connection(fetchone=(None,))

    result = find_intersections(conn, geom_a, geom_b)

    cursor.execute.assert_called_once()
    assert result is None


def test_nearest_neighbors_returns_list():
    geom = {"type": "Point", "coordinates": [0, 0]}
    rows = [
        ("feature-1", json.dumps({"type": "Point", "coordinates": [0.1, 0.1]}), 25.0),
        ("feature-2", json.dumps({"type": "Point", "coordinates": [0.2, 0.2]}), 55.0),
    ]
    conn, cursor = _mock_connection(fetchall=rows)

    results = nearest_neighbors(conn, geom, table="data.features", limit=2)

    cursor.execute.assert_called_once()
    assert len(results) == 2
    assert results[0]["id"] == "feature-1"
    assert results[0]["geometry"]["type"] == "Point"
    assert pytest.approx(results[1]["distance_meters"], rel=1e-3) == 55.0


def test_nearest_neighbors_invalid_limit():
    geom = {"type": "Point", "coordinates": [0, 0]}
    conn, _ = _mock_connection(fetchall=[])

    with pytest.raises(ValueError):
        nearest_neighbors(conn, geom, table="data.features", limit=0)


def test_transform_crs_returns_geojson():
    geom = {"type": "Point", "coordinates": [0, 0]}
    transformed = {"type": "Point", "coordinates": [1000, 1000]}
    conn, cursor = _mock_connection(fetchone=(json.dumps(transformed),))

    result = transform_crs(conn, geom, from_epsg=4326, to_epsg=3857)

    cursor.execute.assert_called_once()
    assert result["coordinates"] == transformed["coordinates"]
