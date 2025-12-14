"""
High-level spatial utilities that delegate computations to PostGIS.

These helpers intentionally keep application code thin while giving us:
1. Type hints and unit conversions that make API responses predictable.
2. Centrally managed SQL to reduce the surface area for SQL injection.
3. A single location for handling GeoJSON ↔ PostGIS conversions.

Functions accept a psycopg2 connection that is managed by the caller.
This avoids hidden state, plays nicely with connection pools, and makes
the code straightforward to test using mocks.
"""

from __future__ import annotations

import json
from typing import Any, cast

from psycopg2 import sql
from psycopg2.extensions import connection

GeoJSON = dict[str, Any]
GeoJSONInput = GeoJSON | str

DISTANCE_TO_METERS: dict[str, float] = {
    "meter": 1.0,
    "meters": 1.0,
    "metre": 1.0,
    "metres": 1.0,
    "kilometer": 1_000.0,
    "kilometers": 1_000.0,
    "kilometre": 1_000.0,
    "kilometres": 1_000.0,
    "mile": 1_609.344,
    "miles": 1_609.344,
    "foot": 0.3048,
    "feet": 0.3048,
    "ft": 0.3048,
    "yard": 0.9144,
    "yards": 0.9144,
}

AREA_FROM_SQ_METERS: dict[str, float] = {
    "square_meter": 1.0,
    "square_meters": 1.0,
    "sqm": 1.0,
    "hectare": 0.0001,
    "hectares": 0.0001,
    "acre": 0.000247105,
    "acres": 0.000247105,
    "square_kilometer": 1e-6,
    "square_kilometers": 1e-6,
    "sqkm": 1e-6,
}


def buffer_geometry(
    conn: connection,
    geom: GeoJSONInput,
    distance: float,
    units: str = "meters",
    srid: int = 4326,
) -> GeoJSON:
    """
    Return a buffered polygon around the given geometry.

    The geometry is provided in GeoJSON (dict or JSON string). Distance is
    converted to meters before delegating to PostGIS. Uses geography type
    for accurate distance calculations regardless of latitude. The result
    is a GeoJSON polygon (or multipolygon) in the same SRID.
    """

    meters = _distance_to_meters(distance, units)
    geom_json = _ensure_geojson_str(geom)

    query = """
        SELECT ST_AsGeoJSON(
            ST_SetSRID(
                ST_Buffer(
                    ST_SetSRID(ST_GeomFromGeoJSON(%s), %s)::geography,
                    %s
                )::geometry,
                %s
            )
        )
    """
    with conn.cursor() as cur:
        cur.execute(query, (geom_json, srid, meters, srid))
        row = cur.fetchone()
    if not row or row[0] is None:
        raise ValueError("Buffer operation returned no geometry.")
    return cast(GeoJSON, json.loads(row[0]))


def calculate_area(
    conn: connection,
    geom: GeoJSONInput,
    units: str = "square_meters",
    srid: int = 4326,
) -> float:
    """
    Calculate the area of a geometry using PostGIS and return it in the
    specified units. Uses geography type for accurate area calculations
    regardless of latitude. Defaults to square meters.
    """

    geom_json = _ensure_geojson_str(geom)
    query = """
        SELECT ST_Area(
            ST_SetSRID(ST_GeomFromGeoJSON(%s), %s)::geography
        )
    """
    with conn.cursor() as cur:
        cur.execute(query, (geom_json, srid))
        row = cur.fetchone()
    if not row or row[0] is None:
        raise ValueError("Area calculation returned no result.")
    square_meters = float(row[0])
    return _area_from_square_meters(square_meters, units)


def find_intersections(
    conn: connection,
    geom_a: GeoJSONInput,
    geom_b: GeoJSONInput,
    srid: int = 4326,
) -> GeoJSON | None:
    """
    Compute the intersection between two geometries. Returns GeoJSON or None
    if there is no overlap.
    """

    geom_a_json = _ensure_geojson_str(geom_a)
    geom_b_json = _ensure_geojson_str(geom_b)
    query = """
        SELECT ST_AsGeoJSON(
            ST_Intersection(
                ST_SetSRID(ST_GeomFromGeoJSON(%s), %s),
                ST_SetSRID(ST_GeomFromGeoJSON(%s), %s)
            )
        )
    """
    with conn.cursor() as cur:
        cur.execute(query, (geom_a_json, srid, geom_b_json, srid))
        row = cur.fetchone()
    if not row or row[0] is None:
        return None
    return cast(GeoJSON, json.loads(row[0]))


def nearest_neighbors(
    conn: connection,
    geom: GeoJSONInput,
    table: str,
    limit: int = 5,
    geom_column: str = "geom",
    id_column: str = "id",
    srid: int = 4326,
) -> list[dict[str, Any]]:
    """
    Find the nearest features in a table to the provided geometry.

    Results include the identifier, distance (meters), and GeoJSON geometry.
    Uses geography type for both ordering and distance calculation to ensure
    accurate spherical distances and consistent results.
    """

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    geom_json = _ensure_geojson_str(geom)
    # Use geography type for accurate spherical distance in meters.
    # Both the ORDER BY (<->) and ST_Distance use the same geography-based
    # calculation to ensure ordering matches reported distances.
    query = sql.SQL(
        """
        SELECT
            {id_column},
            ST_AsGeoJSON({geom_column}) AS geom_json,
            ST_Distance(
                ST_Transform({geom_column}, 4326)::geography,
                ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(%s), %s), 4326)::geography
            ) AS distance_m
        FROM {table}
        ORDER BY ST_Transform({geom_column}, 4326)::geography <->
                 ST_Transform(ST_SetSRID(ST_GeomFromGeoJSON(%s), %s), 4326)::geography
        LIMIT %s
        """
    ).format(
        id_column=sql.Identifier(id_column),
        geom_column=sql.Identifier(geom_column),
        table=sql.Identifier(*(table.split(".")) if "." in table else (table,)),
    )

    params = (geom_json, srid, geom_json, srid, limit)
    with conn.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        feature_id, geom_result, distance_m = row
        results.append(
            {
                "id": feature_id,
                "geometry": json.loads(geom_result) if geom_result else None,
                "distance_meters": float(distance_m) if distance_m is not None else None,
            }
        )
    return results


def transform_crs(
    conn: connection,
    geom: GeoJSONInput,
    from_epsg: int,
    to_epsg: int,
) -> GeoJSON:
    """
    Transform a geometry from one CRS to another.
    """

    geom_json = _ensure_geojson_str(geom)
    query = """
        SELECT ST_AsGeoJSON(
            ST_Transform(
                ST_SetSRID(ST_GeomFromGeoJSON(%s), %s),
                %s
            )
        )
    """
    with conn.cursor() as cur:
        cur.execute(query, (geom_json, from_epsg, to_epsg))
        row = cur.fetchone()
    if not row or row[0] is None:
        raise ValueError("CRS transformation returned no geometry.")
    return cast(GeoJSON, json.loads(row[0]))


# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def _ensure_geojson_str(geom: GeoJSONInput) -> str:
    if isinstance(geom, str):
        return geom
    return json.dumps(geom)


def _distance_to_meters(distance: float, units: str) -> float:
    if distance < 0:
        raise ValueError("distance must be non-negative.")
    factor = DISTANCE_TO_METERS.get(units.lower())
    if factor is None:
        raise ValueError(f"Unsupported distance unit '{units}'.")
    return float(distance) * factor


def _area_from_square_meters(area_m2: float, units: str) -> float:
    factor = AREA_FROM_SQ_METERS.get(units.lower())
    if factor is None:
        raise ValueError(f"Unsupported area unit '{units}'.")
    return area_m2 * factor
