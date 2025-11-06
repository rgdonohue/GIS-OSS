# Developer Experience Strategy

## Goals
- Make GIS-OSS consumable through clear APIs, typed SDKs, and turnkey sandboxes.
- Provide reference integrations for ESRI and open-source GIS tooling.
- Offer guardrails (validation, auditing) without constraining advanced users.

## API Documentation
- **Specification**: OpenAPI 3.1, generated from FastAPI routes; committed to `docs/openapi.yaml`.
- **Docs site**: Redocly or Stoplight build served from `docs/site/`; updated via CI on each release.
- **Playground**: Swagger UI and a custom map-centric explorer (`web/playground`) with query history, map preview, and cURL/Python snippets.
- **Change management**: Versioned endpoints (e.g., `/v1/query`) with changelog maintained in `docs/CHANGELOG.md`.

## SDKs & Client Libraries
- **Python (priority)**: `gis-oss-sdk` package providing `SpatialAssistant` with typed models (Pydantic), sync/async clients, and query builders.
  ```python
  from gis_oss import SpatialAssistant

  assistant = SpatialAssistant(base_url="http://localhost:8000", api_key="dev-key")
  result = assistant.query(
      "Find parcels within 500ft of schools",
      return_format="geojson",
      include_confidence=True,
  )
  ```
- **JavaScript**: Lightweight client for browser apps (MapLibre integration, token management).
- **CLI**: `gis-oss` command for scripting (CSV/GeoJSON output, batch jobs).
- **Auth**: API keys initially, OIDC in Phase 2; SDK handles token refresh and retries.
- **Jupyter Integration**: `%gis_oss` line magic and `%%gis_oss` cell magic for querying PostGIS and visualizing results via folium/kepler.gl.
- **FME Connector**: REST transformer sample project using the OpenAPI spec (custom PythonCaller + HTTPCaller combo).

## Playground & Sandbox
- **Web sandbox**: MapLibre UI with NL query panel, LLM trace viewer, tile overlay selector.
- **Notebook kits**: Jupyter templates (`notebooks/`) invoking the SDK for workshop exercises.
- **Sample datasets**: GeoParquet, COG, PMTiles curated in `data/samples/` with licensing metadata.
- **Scenario bundles**: Ready-to-run demos (e.g., emergency response, urban planning) packaged with instructions.
- **Enterprise Hooks**: FME Server workspace template, ArcGIS Pro add-in library, and REST connectors with signed requests.

## Integration Paths
- **ESRI**: REST connector examples (ArcGIS Pro Python toolbox, Feature Service exports).
- **QGIS**: Plugin skeleton calling the API/SDK, with offline support via PMTiles.
- **Workflow engines**: FME/Kestra recipes for ingest and automation.
- **CI/CD**: GitHub Actions template running lint, tests, dbt, and contract tests against the API.
- **Data Science**: Jupyter notebooks + papermill pipelines leveraging the SDK for reproducible analyses.

## Developer Experience Roadmap
1. Generate initial OpenAPI spec + Redoc documentation.
2. Scaffold Python SDK (`sdk/python/`) with basic query/response types and unit tests.
3. Launch Swagger/Redoc portal and web playground.
4. Release QGIS plugin template and ArcGIS Pro toolbox sample.
5. Publish comprehensive integration guide in `docs/integration.md`.
