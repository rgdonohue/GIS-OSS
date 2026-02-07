from __future__ import annotations

import os

import psycopg2
import pytest

from src.spatial import buffer_geometry, calculate_area, nearest_neighbors, transform_crs

POSTGRES_TEST_DSN = os.environ.get("POSTGRES_TEST_DSN", "").strip()

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def conn():
    if not POSTGRES_TEST_DSN:
        pytest.skip("POSTGRES_TEST_DSN is not set; skipping integration tests.")

    connection = psycopg2.connect(POSTGRES_TEST_DSN)
    connection.autocommit = True
    try:
        with connection.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            cur.execute("CREATE SCHEMA IF NOT EXISTS data;")
            cur.execute("DROP TABLE IF EXISTS data.features;")
            cur.execute(
                """
                CREATE TABLE data.features (
                    id TEXT PRIMARY KEY,
                    geom GEOMETRY(Point, 4326)
                );
                """
            )
            cur.execute(
                """
                INSERT INTO data.features (id, geom) VALUES
                ('a', ST_SetSRID(ST_MakePoint(0.0, 0.0), 4326)),
                ('b', ST_SetSRID(ST_MakePoint(0.01, 0.0), 4326)),
                ('c', ST_SetSRID(ST_MakePoint(0.02, 0.0), 4326));
                """
            )
    except Exception:
        connection.close()
        raise

    yield connection

    with connection.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS data.features;")
    connection.close()


def test_buffer_and_area_integration(conn):
    geom = {"type": "Point", "coordinates": [0.0, 0.0]}
    buffered = buffer_geometry(conn, geom, distance=100, units="meters")
    assert buffered["type"] in {"Polygon", "MultiPolygon"}

    area = calculate_area(conn, buffered, units="square_meters")
    assert area > 1.0


def test_nearest_neighbors_integration(conn):
    geom = {"type": "Point", "coordinates": [0.0, 0.0]}
    results = nearest_neighbors(conn, geom, table="data.features", limit=2, id_column="id")
    assert len(results) == 2
    assert results[0]["id"] == "a"
    assert results[1]["id"] == "b"
    assert results[0]["distance_meters"] <= results[1]["distance_meters"]


def test_transform_crs_integration(conn):
    geom = {"type": "Point", "coordinates": [1.0, 0.0]}
    transformed = transform_crs(conn, geom, from_epsg=4326, to_epsg=3857)
    x, y = transformed["coordinates"]
    assert abs(x - 111319.49) < 1000
    assert abs(y) < 10
