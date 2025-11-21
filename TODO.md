# GIS-OSS Development Backlog

> **Status**: Week 1 Day 1-2 infrastructure tasks completed. Ready to implement spatial functions (Day 3-4).

## Feedback-Driven Priorities (June 2025 Reviews)

Incorporate the June 11 reviews (Claude & OpenAI) before new pilots.

### Governance & Legal Controls
- [ ] Add `/docs/legal/` with FPIC SOP, CARE→control map, TK/BC enforcement spec, and NAGPRA escalation flow; make CI block releases when this bundle is missing.
- [ ] Ship a consent ledger + elder approval workflow that records FPIC events (who/when/how) and provide reusable tribal consultation templates.
- [ ] Draft inter-tribal/federal data-sharing agreements, DPAs, and “no-train” covenants that forbid TEK/sacred data from model training; define breach classes with notification timelines.
- [ ] Map every TK/BC label to concrete RLS/ABAC policies, export tiers, masking behavior, and appeals/exception handling so enforcement is executable.
- [ ] Freeze a model usage policy by adding `/policy/model-allowlist.yaml`, generating a license SBOM for each weight, and blocking unapproved models at startup.

### Data Protection & Spatial Governance
- [ ] Implement Postgres RLS migrations (`policy_subject`, `policy_rule`, `label_state`, `season_window`) plus deterministic geometry redaction/watermarking and “no-train zone” filters for TEK text.
- [ ] Add jurisdiction-aware spatial layers for overlapping tribal/state/federal authorities and surface them to the NL→GIS planner.
- [ ] Build cultural sensitivity filters that detect tribal terminology/sacred placenames and route those queries through consultation workflows before execution/export.
- [ ] Document and enforce NAGPRA handling (classification, escalation, throttled access) for archaeologically sensitive datasets.
- [ ] Require STAC/assets to carry TK label + CARE metadata and enforce consent/license checks (folder-level permits) before downloads or exports.

### Spatial Tooling & Performance
- [ ] Expand the audited spatial tool library to include topology validation, raster analytics, and pgRouting-style network analysis so production use cases are covered.
- [ ] Add geodatabase versioning/conflict resolution workflows that mirror ArcGIS Enterprise expectations.
- [ ] Publish GPU sizing, spatial indexing, caching, and batch-processing strategies to mitigate the highlighted performance risks.
- [ ] Deliver the “walking skeleton” stack (PostGIS + pg_tileserv + TiTiler + STAC) alongside the three demo notebooks (`Treaty Defense`, `Sacred Site Storm`, `First Foods Forecast`) with NL→SQL/tool logs.
- [ ] Create `contrib/benchmarks/` housing SpatialBench-Tribal scenarios wired into CI so the LLM router and policy checks are regression-tested.

### Interop & Packaging
- [ ] Document ArcGIS/QGIS interoperability in detail (REST/service compatibility, schema translation, ArcPy migration paths, feature publication steps) for ESRI-heavy environments.
- [ ] Publish an OGC service recipe plus a signed ArcGIS Pro `.pyt` toolbox and sample Pro project that call GIS-OSS endpoints without bypassing TK/BC policy checks.
- [ ] Provide guidance for packaging offline/edge tiles (PMTiles/COGs to `.vtpk/.tpkx`) and define the OIDC-based identity boundary for ESRI clients.
- [ ] Ship instructions for composing the edge/offline stack (TiTiler, pg_tileserv, STAC) and validating low-bandwidth raster pyramids pre-pilot.
- [ ] Outline ESRI partnership/integration milestones to align with the suggested strategic positioning and partner outreach.

### Product & Partnership Readiness
- [ ] Define licensing, pricing, and support/maintenance structures so prospects can compare offerings against ArcGIS suites.
- [ ] Launch PoCs with 2–3 tribal nations (with tribal GIS program partnerships) to validate workflows and secure reference customers.
- [ ] Benchmark GIS-OSS outputs against ArcGIS Notebook/ArcPy workflows and publish the performance/accuracy deltas.
- [ ] Create a compliance officer/analyst certification program plus workshop kits to monetize enablement while reinforcing governance practice.
- [ ] Establish a standing advisory council, public changelog, and quarterly legal audit cadence to address community-trust risks.
- [ ] Build a regional GIS consultant partner network (value props, enablement kit, referral model) to extend delivery capacity.

## Week 1: Foundation Infrastructure

### Day 1-2: Environment Setup
- [x] Create docker-compose.yml with PostgreSQL 15 + PostGIS 3.4
- [x] Add pgvector extension to Postgres initialization
- [x] Set up .env.example with all required variables
- [x] Create basic .gitignore for Python/Node/Docker
- [x] Write setup_dev.sh script for one-command initialization

### Day 3-4: Spatial Functions
- [x] Create src/spatial/postgis_ops.py with 5 core functions:
  - [x] buffer_geometry(geom, distance, units)
  - [x] calculate_area(geom, units)
  - [x] find_intersections(geom1, geom2)
  - [x] nearest_neighbors(geom, table, limit)
  - [x] transform_crs(geom, from_epsg, to_epsg)
- [x] Add input validation for each function
- [x] Write pytest tests for each function

### Day 5: Data Loading
- [x] Create scripts/load_sample_data.py
- [x] Download small OSM extract (< 100MB)
- [x] Load into PostGIS with proper indexes
- [x] Create sample STAC catalog entry
- [x] Document data sources and licenses

## Week 2: API and Basic LLM

### Day 6-7: FastAPI Setup
- [x] Create src/api/main.py with basic app structure
- [x] Add /health and /ready endpoints
- [x] Create /query endpoint (stub, returns mock data)
- [x] Add request/response models with Pydantic
- [x] Set up structured logging
- [ ] Export OpenAPI schema (`scripts/export_openapi.py`)
- [ ] Add swagger/redoc route to serve documentation

### Day 8-9: Model Integration
- [ ] Document model selection rationale (Qwen vs Llama)
- [ ] Create scripts/download_model.py for model fetching
- [ ] Set up vLLM or llama.cpp server
- [ ] Create src/llm/client.py with inference wrapper
- [ ] Test basic prompt completion

### Day 10: Integration Testing
- [ ] Connect LLM to spatial functions
- [ ] Create 10 test queries with expected outputs
- [ ] Implement basic NL→SQL translation
- [ ] Add fallback handling for errors
- [ ] Document accuracy baseline

## Week 3: Governance & Security Foundation

### Audit & Attribution
- [ ] Create src/governance/audit_logger.py with structured event logging
- [ ] Implement src/governance/attribution.py for license tracking
- [ ] Add license field to all data ingestion pipelines
- [ ] Create attribution template for API responses
- [ ] Write tests for attribution engine

### Data Governance
- [ ] Design metadata schema for dual publishing (CC-BY vs ODbL)
- [ ] Create scripts/split_by_license.py for data separation
- [ ] Implement src/governance/license_validator.py
- [ ] Add STAC metadata enrichment with license info
- [ ] Document compliance workflow in docs/governance.md

### Security Basics
- [ ] Implement API key authentication middleware
- [ ] Add rate limiting with slowapi
- [ ] Create src/security/geometry_generalizer.py (>50m resolution)
- [ ] Set up basic request/response logging
- [ ] Document security model in docs/security.md

## Week 4: Offline Capabilities

### Offline Dependencies
- [ ] Bundle proj.db for offline CRS lookups
- [ ] Create scripts/download_offline_data.py
- [ ] Implement fallback logic for external APIs
- [ ] Set up response caching with Redis/SQLite
- [ ] Test air-gapped deployment scenario

### Local Services
- [ ] Set up Nominatim docker container (optional)
- [ ] Create static carbon intensity lookup table
- [ ] Implement offline model loading from ./models/
- [ ] Add PMTiles basemap support
- [ ] Document offline setup in docs/offline.md

## Week 5: Modern GIS Services

### Vector Tiles & Basemaps
- [ ] Enable TimescaleDB extension in Postgres container
- [ ] Add pg_tileserv (or martin) service to docker-compose.yml
- [ ] Create tiles configuration for sample datasets (admin boundaries, permits)
- [ ] Implement tile cache (Redis/Varnish) configuration
- [ ] Document MapLibre integration with hosted tiles & PMTiles fallback

### Raster & COG Enhancements
- [ ] Extend TiTiler config for quad-keys/WMTS endpoints
- [ ] Generate sample COGs and register via STAC metadata
- [ ] Add raster algebra tool wrappers (e.g., NDVI computation)
- [ ] Script PMTiles packaging for offline demo basemaps

## Week 6: Data Pipeline & Streaming

### Batch & Transformation
- [ ] Introduce Airflow docker service with minimal DAG (COG ingest, STAC refresh)
- [ ] Bootstrap dbt project (`pipeline/dbt/`) with spatial models and tests
- [ ] Wire CI-style `dbt run`/`dbt test` commands into developer workflow
- [ ] Prototype ESRI geodatabase import/export bridge (supports BIA enterprise datasets)
- [ ] Define integration adapters for TAAMS/NIOGEMS metadata (read-only)

### Event-Driven & Streaming
- [ ] Add Kafka/Redpanda service for telemetry ingest
- [ ] Configure Kestra flow to react to new events (e.g., sensor updates → rebuffer)
- [ ] Prototype Timescale continuous aggregate for change detection
- [ ] Evaluate Apache Sedona Spark job for bulk raster/vector processing
- [ ] Instrument `/query` latency metrics (p50/p95/p99) via Prometheus + Grafana

## Week 7: Developer Experience

### API Documentation & Contracts
- [ ] Generate OpenAPI 3.1 spec from FastAPI (`python -m core.api export-openapi`)
- [ ] Publish Redoc/Swagger UI under `docs/site/`
- [ ] Establish versioning strategy and changelog (docs/CHANGELOG.md)
- [ ] Add contract tests ensuring SDK compatibility
- [ ] Create FME Server workspace template (HTTPCaller + PythonCaller) for GIS-OSS
- [ ] Publish REST connector guide leveraging OpenAPI spec

### SDK & Client Tooling
- [ ] Scaffold Python package `sdk/python/gis_oss`
- [ ] Implement `SpatialAssistant` with typed request/response models
- [ ] Add async client + retry/backoff utilities
- [ ] Publish initial package to internal index (or TestPyPI)
- [ ] Draft CLI wrapper for batch queries
- [ ] Create QGIS plugin skeleton (PyQGIS) with authentication + query UI
- [ ] Provide ArcGIS Pro toolbox template (ArcPy) hooking into `/query`
- [ ] Build Jupyter magic commands (`%gis_oss` / `%%gis_oss`) for data scientists
- [ ] Draft performance report template (latency, accuracy, throughput, cost savings)

## Week 8: Model Training Foundations

### Data Curation & Annotation
- [ ] Draft dataset acquisition plan (PostGIS docs, Tribal climate/water datasets, TEK-safe corpora, ESRI→PostGIS translations)
- [ ] Build scraper/notebook for PostGIS documentation extraction
- [ ] Collect 100 tribal environmental queries + annotate intents/domains/consent tags
- [ ] Curate ESRI ModelBuilder → PostGIS SQL mapping examples (watershed, habitat, fire)
- [ ] Define annotation schema (intent, tools, narrative, consent) in docs/model_training.md
- [ ] Evaluate labeling tools (Label Studio, Prodigy, custom Streamlit) for TEK permissions

### Fine-Tuning Experiments
- [ ] Prepare LoRA config templates for router, SQL, report tiers
- [ ] Run pilot router fine-tune (500 examples) and report accuracy/F1
- [ ] Create SQL evaluation harness (execute generated SQL against sample DB)
- [ ] Assemble narrative evaluation rubric (tone, completeness, citations)
- [ ] Document experiment tracking approach (Weights & Biases/MLflow)

### Serving Strategy
- [ ] Prototype multi-model routing (router + SQL generator) using vLLM or FastAPI middleware
- [ ] Define model versioning metadata in API responses
- [ ] Plan adapter storage/deployment layout (`models/finetuned/<tier>/<version>`)
- [ ] Document fallback escalation flow when router confidence is low
- [ ] Benchmark Phase 1 accuracy against GeoBench + Tribal stewardship scenario set

## Week 9: Community & Ecosystem

### Benchmarks & Prompt Library
- [ ] Design SpatialBench-Tribal task list (10 initial scenarios) and licensing review
- [ ] Build benchmark harness under `benchmarks/spatialbench/` with CI hooks
- [ ] Publish prompt library structure (`prompts/`) with metadata schema (intent, consent, TEK labels)
- [ ] Seed 25 prompts covering watershed defense, cultural resources, climate/fire, food sovereignty, restoration, EJ grants

### Partnerships & Outreach
- [ ] Draft tribal partnership brief (pilot tribe shortlist + value props)
- [ ] Prepare Docker-based lab kit for academic pilots
- [ ] Set up community channels (GitHub Discussions, Slack) and contribution guidelines
- [ ] Outline open-core vs enterprise feature matrix for public roadmap
- [ ] Create conference engagement calendar (Indigenous Mapping Workshop, NCAI, Native American Fish & Wildlife Society)

### Playground & Integrations
- [ ] Build MapLibre web sandbox with NL query panel and tile overlays
- [ ] Provide QGIS plugin template consuming the API
- [ ] Author ArcGIS Pro Python toolbox example
- [ ] Document integration patterns in `docs/integration.md`
- [ ] Add story-map/temporal narrative support (audio narratives, seasonal layers)

## Prioritization Notes

**Must Have (Week 1)**:
- Working PostGIS with sample data
- 5 tested spatial functions
- Basic API structure

**Should Have (Week 2)**:
- LLM integration with small model
- Simple NL→SQL translation
- Error handling

**Week 3 (Governance)**:
- Audit logging system
- License attribution
- Basic security (auth, rate limit)

**Week 4 (Offline)**:
- Bundled offline data
- Fallback mechanisms
- Air-gapped testing

**Week 5 (Spatial Services)**:
- Vector tile service online
- Timescale hypertables for temporal queries
- Raster/COG tooling verified

**Week 6 (Pipelines & Streaming)**:
- Batch orchestration (Airflow + dbt)
- Streaming ingest demo (Kafka + Kestra)
- Sedona evaluation for scale-out workloads

**Week 7 (Developer Experience)**:
- OpenAPI + documentation portal live
- Python SDK + CLI published
- Playground + integration templates available

**Week 8 (Model Training & Serving)**:
- Dataset plan, pilot fine-tunes
- Multi-model routing
- Accuracy benchmark harness

**Week 9 (Community & Ecosystem)**:
- SpatialBench-Tribal + prompt library seeded
- Partnership outreach kit prepared
- Community channels and roadmap artifacts ready

**Week 10 (Governance & Cultural Protocols)**:
- Consent engine + classification schema implemented
- Cultural audit logging, seasonal/gender access controls working
- FPIC/IRB workflow prototype & legal templates drafted
- Advisory committee engagement plan operational

**Defer to Phase 2**:
- OAuth/OIDC integration
- Advanced PII protection
- Production carbon tracking
- Multi-tenant RLS

## Success Criteria

### Week 1 Checkpoint
- [ ] `docker-compose up` starts all services
- [ ] Can query PostGIS directly via psql
- [ ] Spatial functions pass unit tests
- [ ] Sample data loads successfully

### Week 2 Checkpoint
- [ ] API responds to health checks
- [ ] LLM model loads and infers
- [ ] 5/10 test queries return correct results
- [ ] Errors handled gracefully

## Risk Register

| Risk | Mitigation |
|------|------------|
| Model too large for hardware | Use smaller model (7B) or aggressive quantization |
| PostGIS complexity | Start with just 3 functions, expand later |
| LLM hallucinations | Implement strict output validation |
| Data licensing issues | Use only CC0/OpenData sources initially |

## Dependencies

### External Services
- [ ] EPSG.io for CRS metadata (mock for offline)
- [ ] OSM Nominatim for geocoding (optional)
- [ ] WattTime API (mock for development)

### Python Packages
```
fastapi==0.104.0
pydantic==2.5.0
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
geoalchemy2==0.14.2
shapely==2.0.2
rasterio==1.3.9
vllm==0.2.7  # or llama-cpp-python
pytest==7.4.3
```

### System Requirements
- Docker & Docker Compose
- 16GB+ RAM
- 50GB+ disk space
- NVIDIA GPU with 24GB+ VRAM (optional for Week 1)
