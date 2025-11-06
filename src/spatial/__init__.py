"""
Spatial utilities and PostGIS helpers for GIS-OSS.

This package exposes safe, high-level wrappers around common spatial
operations. Each function delegates the heavy lifting to PostGIS while
returning friendly Python objects (GeoJSON dictionaries, numeric
measurements, etc.).
"""

from .postgis_ops import (
    buffer_geometry,
    calculate_area,
    find_intersections,
    nearest_neighbors,
    transform_crs,
)

__all__ = [
    "buffer_geometry",
    "calculate_area",
    "find_intersections",
    "nearest_neighbors",
    "transform_crs",
]
