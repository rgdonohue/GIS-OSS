#!/usr/bin/env python3
"""
Download a small OSM extract, import it into PostGIS, and write a STAC item.

The defaults keep the download under 10 MB (District of Columbia extract) so we can
demonstrate the spatial toolchain without huge storage or bandwidth needs.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import logging
import os
import pathlib
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from typing import Dict, Any

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

LOGGER = logging.getLogger("load_sample_data")

DEFAULT_OSM_URL = (
    "https://download.geofabrik.de/north-america/us/district-of-columbia-latest.osm.pbf"
)
DEFAULT_DATA_DIR = pathlib.Path(os.environ.get("DATA_DIR", "./data")).resolve()
DEFAULT_STAC_DIR = DEFAULT_DATA_DIR / "stac"

STAC_TEMPLATE = {
    "type": "Feature",
    "stac_version": "1.0.0",
    "id": "osm-dc-sample",
    "properties": {
        "datetime": "2024-01-01T00:00:00Z",
        "start_datetime": "2024-01-01T00:00:00Z",
        "end_datetime": "2024-01-01T00:00:00Z",
        "title": "OpenStreetMap — District of Columbia Extract",
        "description": (
            "Small OSM extract (District of Columbia) for GIS-OSS demos. "
            "Useful for routing, permit overlays, and governance tests."
        ),
        "keywords": ["OSM", "District of Columbia", "transportation", "demo"],
        "mission": "GIS-OSS sample data",
        "providers": [
            {
                "name": "OpenStreetMap contributors",
                "roles": ["licensor", "producer"],
                "url": "https://www.openstreetmap.org",
            },
            {
                "name": "Geofabrik GmbH",
                "roles": ["processor", "host"],
                "url": "https://download.geofabrik.de/",
            },
        ],
        "license": "ODbL-1.0",
    },
    "geometry": {
        "type": "Polygon",
        "coordinates": [
            [
                [-77.1198, 38.7916],
                [-77.1198, 39.0004],
                [-76.9094, 39.0004],
                [-76.9094, 38.7916],
                [-77.1198, 38.7916],
            ]
        ],
    },
    "bbox": [-77.1198, 38.7916, -76.9094, 39.0004],
    "links": [],
    "assets": {},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and load a small OSM dataset into PostGIS."
    )
    parser.add_argument(
        "--osm-url",
        default=os.environ.get("OSM_PBF_URL", DEFAULT_OSM_URL),
        help="HTTP(S) URL to a .osm.pbf file (default: District of Columbia extract).",
    )
    parser.add_argument(
        "--data-dir",
        type=pathlib.Path,
        default=DEFAULT_DATA_DIR,
        help="Root directory for cached data (default: %(default)s).",
    )
    parser.add_argument(
        "--stac-dir",
        type=pathlib.Path,
        default=DEFAULT_STAC_DIR,
        help="Directory to store generated STAC artifacts (default: %(default)s).",
    )
    parser.add_argument(
        "--schema",
        default=os.environ.get("OSM_SCHEMA", "osm_sample"),
        help="Postgres schema to import into (default: %(default)s).",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Assume the .osm.pbf file already exists; skip downloading.",
    )
    parser.add_argument(
        "--skip-import",
        action="store_true",
        help="Skip the osm2pgsql import (useful for regenerating STAC only).",
    )
    parser.add_argument(
        "--skip-stac",
        action="store_true",
        help="Skip STAC metadata generation.",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("LOG_LEVEL", "INFO"),
        help="Logging level (default: %(default)s).",
    )
    return parser.parse_args()


def ensure_dependency(binary: str) -> None:
    if shutil.which(binary) is None:
        raise RuntimeError(
            f"Required dependency '{binary}' not found in PATH. "
            "Install it (e.g., `brew install osm2pgsql`) and re-run."
        )


def download_osm(url: str, dest: pathlib.Path) -> pathlib.Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        LOGGER.info("OSM extract already exists at %s (skipping download).", dest)
        return dest

    LOGGER.info("Downloading %s -> %s", url, dest)
    with urllib.request.urlopen(url) as response, open(dest, "wb") as out_file:
        shutil.copyfileobj(response, out_file)

    LOGGER.info("Download complete (%.2f MB).", dest.stat().st_size / (1024 * 1024))
    return dest


def run_osm2pgsql(pbf_path: pathlib.Path, schema: str, conn_info: Dict[str, str]) -> None:
    ensure_dependency("osm2pgsql")
    env = os.environ.copy()
    env["PGPASSWORD"] = conn_info["password"]

    cmd = [
        "osm2pgsql",
        "--create",
        "--database",
        conn_info["dbname"],
        "--host",
        conn_info["host"],
        "--port",
        str(conn_info["port"]),
        "--username",
        conn_info["user"],
        "--schema",
        schema,
        "--hstore",
        "--slim",
        "--latlong",
        "--extra-attributes",
        str(pbf_path),
    ]

    LOGGER.info("Importing %s into schema '%s'...", pbf_path.name, schema)
    subprocess.run(cmd, check=True, env=env)
    LOGGER.info("osm2pgsql import complete.")


def create_indexes(schema: str, conn_info: Dict[str, str]) -> None:
    LOGGER.info("Creating spatial indexes in schema '%s'...", schema)
    conn = psycopg2.connect(
        dbname=conn_info["dbname"],
        user=conn_info["user"],
        password=conn_info["password"],
        host=conn_info["host"],
        port=conn_info["port"],
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    from psycopg2 import sql
    
    # CREATE SCHEMA using sql.Identifier to prevent injection
    cur.execute(
        sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema))
    )
    
    # Check for expected tables using parameterized query
    cur.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = %s AND table_name = 'planet_osm_point'
            ) THEN
                RAISE NOTICE 'Expected osm2pgsql tables not found in schema %%.', %s;
            END IF;
        END $$;
        """,
        (schema, schema)
    )
    
    # Create indexes using sql.Identifier for schema and table names
    index_statements = [
        ("planet_osm_point_geom_idx", "planet_osm_point", "way"),
        ("planet_osm_line_geom_idx", "planet_osm_line", "way"),
        ("planet_osm_polygon_geom_idx", "planet_osm_polygon", "way"),
        ("planet_osm_roads_geom_idx", "planet_osm_roads", "way"),
    ]
    
    for idx_name, table_name, column_name in index_statements:
        cur.execute(
            sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {}.{} USING GIST({})").format(
                sql.Identifier(idx_name),
                sql.Identifier(schema),
                sql.Identifier(table_name),
                sql.Identifier(column_name)
            )
        )

    cur.close()
    conn.close()
    LOGGER.info("Spatial indexes ready.")


def write_stac_item(stac_dir: pathlib.Path, asset_path: pathlib.Path) -> None:
    stac_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = stac_dir / "catalog.json"
    collection_path = stac_dir / "osm_sample_collection.json"
    item_path = stac_dir / "osm_dc_sample_item.json"

    now = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    item = copy.deepcopy(STAC_TEMPLATE)
    item["properties"] = {**item["properties"], "created": now}
    asset_rel_path = os.path.relpath(asset_path, stac_dir)
    item["assets"] = {
        "osm_pbf": {
            "href": asset_rel_path,
            "type": "application/octet-stream",
            "roles": ["data"],
            "title": "District of Columbia OSM extract (.pbf)",
        }
    }

    collection = {
        "type": "Collection",
        "stac_version": "1.0.0",
        "id": "osm-sample",
        "description": "OpenStreetMap District of Columbia sample for GIS-OSS demos.",
        "license": "ODbL-1.0",
        "extent": {
            "spatial": {"bbox": [item["bbox"]]},
            "temporal": {
                "interval": [
                    [
                        item["properties"]["start_datetime"],
                        item["properties"]["end_datetime"],
                    ]
                ]
            },
        },
        "links": [
            {"rel": "root", "href": "catalog.json", "type": "application/json"},
            {"rel": "item", "href": item_path.name, "type": "application/geo+json"},
        ],
    }

    catalog = {
        "type": "Catalog",
        "id": "gis-oss-sample-data",
        "stac_version": "1.0.0",
        "description": "Sample datasets bundled with GIS-OSS for demos and smoke-tests.",
        "links": [
            {"rel": "self", "href": "catalog.json", "type": "application/json"},
            {
                "rel": "child",
                "href": collection_path.name,
                "type": "application/json",
                "title": "OSM Sample Collection",
            },
        ],
    }

    item["links"] = [
        {"rel": "self", "href": item_path.name, "type": "application/geo+json"},
        {"rel": "parent", "href": collection_path.name, "type": "application/json"},
        {"rel": "collection", "href": collection_path.name, "type": "application/json"},
        {"rel": "root", "href": catalog_path.name, "type": "application/json"},
    ]

    LOGGER.info("Writing STAC catalog to %s", catalog_path)
    catalog_path.write_text(json.dumps(catalog, indent=2))
    LOGGER.info("Writing STAC collection to %s", collection_path)
    collection_path.write_text(json.dumps(collection, indent=2))
    LOGGER.info("Writing STAC item to %s", item_path)
    item_path.write_text(json.dumps(item, indent=2))


def get_conn_info() -> Dict[str, Any]:
    return {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": int(os.environ.get("POSTGRES_PORT", 5432)),
        "dbname": os.environ.get("POSTGRES_DB", "gis_oss"),
        "user": os.environ.get("POSTGRES_USER", "gis_user"),
        "password": os.environ.get("POSTGRES_PASSWORD", "changeme_in_production"),
    }


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
    )

    data_dir = args.data_dir
    osm_dir = data_dir / "osm"
    parsed_url = urllib.parse.urlparse(args.osm_url)
    pbf_filename = pathlib.Path(parsed_url.path).name or "osm_sample.osm.pbf"
    pbf_path = osm_dir / pbf_filename

    conn_info = get_conn_info()

    if not args.skip_download:
        try:
            download_osm(args.osm_url, pbf_path)
        except Exception as exc:
            LOGGER.error("Failed to download OSM extract: %s", exc)
            sys.exit(1)
    else:
        LOGGER.info("Skipping download step.")

    if not args.skip_import:
        try:
            run_osm2pgsql(pbf_path, args.schema, conn_info)
            create_indexes(args.schema, conn_info)
        except FileNotFoundError as exc:
            LOGGER.error("Import failed; dependency missing: %s", exc)
            sys.exit(2)
        except subprocess.CalledProcessError as exc:
            LOGGER.error("osm2pgsql exited with status %s", exc.returncode)
            sys.exit(exc.returncode)
        except Exception as exc:
            LOGGER.error("Unexpected import/indexing error: %s", exc)
            sys.exit(3)
    else:
        LOGGER.info("Skipping PostGIS import/index creation.")

    if not args.skip_stac:
        try:
            write_stac_item(args.stac_dir, pbf_path)
        except Exception as exc:
            LOGGER.error("Failed to write STAC metadata: %s", exc)
            sys.exit(4)
    else:
        LOGGER.info("Skipping STAC generation.")

    LOGGER.info("Sample data workflow completed successfully.")


if __name__ == "__main__":
    main()
