# Sample Data Sources & Licenses

This document tracks the demo datasets bundled with GIS-OSS so we can prove where the data came from, what the license terms are, and how to refresh them safely.

- Canonical machine-readable manifest: `config/sample_data_manifest.json`
- Validation command: `python scripts/verify_sample_data_provenance.py`
- Fetch-by-id command: `python scripts/fetch_authoritative_dataset.py --dataset-id <id>`

## OpenStreetMap — District of Columbia Extract

- **Purpose**: Lightweight (<10 MB) dataset for local smoke-tests of PostGIS, STAC metadata, and NL→SQL demos without handling gigabyte-scale files.
- **Download URL**: `https://download.geofabrik.de/north-america/us/district-of-columbia-latest.osm.pbf`
- **Fetched Via**: `scripts/load_sample_data.py` (defaults to this URL).
- **License**: [Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
- **Attribution**: “© OpenStreetMap contributors” + link to [openstreetmap.org](https://www.openstreetmap.org). Geofabrik hosts the prepared extract.
- **Recommended Use**: Routing, land-use overlays, governance/RLS exercises, and sample STAC catalog entries.
- **Refresh Cadence**: Optional monthly refresh or whenever we need a newer timestamp for demos. Use the script’s `--skip-download` flag to reuse an existing copy.

## U.S. Census — Cartographic Boundary States (2024, 1:20m)

- **Purpose**: Authoritative U.S. administrative boundaries for baseline overlays, regional summaries, and governance testing.
- **Download URL**: `https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_20m.zip`
- **Fetched Via**: `scripts/fetch_authoritative_dataset.py --dataset-id us-census-states-cb-2024-20m`
- **License**: Public domain U.S. government work (17 U.S.C. § 105).
- **Attribution**: U.S. Census Bureau TIGER/Line cartographic boundary files.
- **Local Path**: `data/authoritative/us_census/cb_2024_us_state_20m.zip`
- **Pinning Workflow**:
  1. Run the fetch command and capture the printed `sha256`.
  2. Set `expected_sha256` for this dataset in `config/sample_data_manifest.json`.
  3. Re-run `python scripts/verify_sample_data_provenance.py --require-local`.

## How to Regenerate
1. Ensure Docker/PostGIS services are running (`./scripts/setup_dev.sh`).
2. Run `python scripts/load_sample_data.py` (optionally pass a different `--osm-url` under 100 MB).
3. The script downloads the `.osm.pbf`, runs `osm2pgsql`, adds spatial indexes, and writes a STAC catalog under `data/stac/`.
4. Review `docs/data_sources.md` after adding new datasets so licenses stay transparent.

## Adding Future Samples
- Keep each dataset under 100 MB unless a larger asset is explicitly needed for a scenario.
- Record the URL, license, attribution text, and refresh expectations here.
- Update the STAC catalog to include new collections/items with the same transparency.
