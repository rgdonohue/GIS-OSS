# GIS-OSS — Privacy-First Geospatial Analytics with Built-In Governance

Offline-capable spatial reasoning. Consent-aware data governance. Self-hosted by design. Designed with Indigenous data sovereignty as the architectural driver; built for any organization that refuses to compromise on data control.

GIS-OSS is a **privacy-first geospatial platform** built on open-weight language models and deterministic PostGIS/GDAL tooling. It ships as Docker-based infrastructure with offline-ready datasets, pluggable governance protocols (consent workflows, approval chains, audit trails, time-bound access controls), and reproducible analytics — all running on hardware you control.

The governance architecture was designed for **Indigenous data sovereignty** — the most demanding data-control use case we know of. That same architecture serves conservation districts, rural health agencies, military and defense installations, humanitarian organizations, and municipal governments that need auditable, on-prem geospatial analytics with strict data residency.

> **Project Stage**: The spatial stack (PostGIS, TiTiler, vector tiles, FastAPI service) and governance scaffolding (consent metadata, audit logging, role-based access) are implemented. Tribal co-design partnerships are in planning — governance protocols for Indigenous-specific features (elder approval workflows, seasonal access windows, TK label enforcement) will be refined with tribal partners before those features ship. See [Community Process](docs/community_process.md) for our engagement framework.

![GIS OSS image](gis-oss.png)

## Executive Overview
- Privacy-first platform: open-weight LLMs, deterministic PostGIS/GDAL pipelines, and full audit trails — all self-hosted.
- Pluggable governance layer: consent-aware data access, hierarchical approval workflows, automatic redaction, and cryptographically signed audit logs.
- Offline-capable by default: local models, bundled CRS data, PMTiles basemaps, and air-gapped deployment paths.
- Integrates with existing GIS ecosystems: QGIS, ArcGIS Pro, Jupyter, OGC services, and FME Server.
- Initial design focus: Indigenous data sovereignty — with architecture applicable to any data-sensitive domain.

## Project Map
- [Architecture Overview](docs/architecture.md) — system layers, governance hooks, data/ops components.
- [Tribal Environmental Playbook](docs/tribal_environmental.md) — domain pillars, metrics, partner roadmap.
- [Indigenous Data Sovereignty Framework](docs/data_sovereignty.md) — classifications, consent, repatriation.
- [Community Governance & Engagement Process](docs/community_process.md) — advisory bodies, workshops, reciprocity.
- [Legal & Jurisdictional Architecture](docs/legal_architecture.md) — CARE/FPIC enforcement, treaty rights, liability.
- [Developer Experience Plan](docs/developer_experience.md) — SDKs, QA, integrations.
- [Project Status (Generated)](docs/project_status.md) — code-derived implementation snapshot (validated in CI).
- [Backlog & Milestones](TODO.md) — weekly execution plan.
- [Agent Instructions](AGENTS.md) — repository + path-scoped guidance for coding agents.
- [DB Authz Onboarding](docs/security_authz_onboarding.md) — provisioning and operating database-backed API key roles.
- [LLM Integration Plan](docs/llm_integration_plan.md) — local planner/provider approach and constraints.

## Why Now
- **Open-weight models** (Qwen 2.5, Llama 3.1) enable self-hosted reasoning without sending data to third-party APIs.
- **Data residency regulation is expanding**: CARE/FPIC for Indigenous data, NEPA/CEQA for environmental review, HIPAA for rural health, ITAR/CUI for defense — all demand on-prem analytics with provable chain of custody.
- **Funding tailwinds**: BIL/IRA, EPA, BIA, and DOJ grants prioritize climate resilience, habitat restoration, and environmental justice; conservation and municipal programs are scaling similarly.
- **Intended impact**: help analysts finish environmental reviews, compliance packets, and grant submissions faster — with citation trails, redaction controls, and approval workflows built in.

## Spatial Analysis Capabilities
- **Watershed & Water Quality Analysis**
  Streamflow modeling, water-quality dashboards, upstream contamination tracing, sensitive-area buffers excluded from exports, climate-change stress testing.
- **Habitat & Species Monitoring**
  Dual knowledge systems with role-based access, phenology tracking, wildlife corridor analysis, compliance-ready reporting with automatic redaction of sensitive locations.
- **Climate Adaptation & Fire Management**
  Prescribed burn planning with fuel model analytics, evacuation routing prioritizing critical facilities, smoke impact modeling, post-fire restoration prioritization.
- **Food Systems & Agricultural Planning**
  Crop suitability analysis, pollinator corridor planning, water-efficient irrigation design, harvest monitoring, nutrition-access mapping.
- **Land Acquisition & Restoration Prioritization**
  Ownership analysis, conservation easement scouting, carbon sequestration calculators, historical land-use reconstruction, parcel acquisition scoring.
- **Environmental Compliance & Grant Intelligence**
  Auto-generated maps and statistics for grant applications, cumulative impact assessments, climate vulnerability indexing, community health overlays, evidence packs for data-to-grant workflows.

Each capability combines plain-language prompts with spatial analysis — buffers, joins, change detection — and wraps results with governance safeguards: sensitive-site redaction, consent tracking, and data provenance.

### Premier Use Case: Tribal Environmental Stewardship

The workflows above were designed around the needs of tribal environmental departments — the use case whose governance requirements shaped the platform's architecture. See the [Tribal Environmental Playbook](docs/tribal_environmental.md) for detailed workflows, prompts, data requirements, and success metrics specific to tribal stewardship. Additional domain playbooks (conservation, municipal planning, rural health) are planned.

## Demo Scenarios
1. **Sensitive Site Protection** — A severe weather event threatens a region with protected cultural or ecological sites: plan response operations that respect access restrictions and safeguard sensitive locations.
   *(Applicable: tribal sacred site protection, conservation easement management, military installation security)*
2. **Watershed Impact Assessment** — Monitor upstream permits and water withdrawals affecting protected waterways, then assemble a defense brief with citations and spatial evidence.
   *(Applicable: tribal treaty defense, municipal water utility planning, conservation district monitoring)*
3. **Seasonal Habitat Forecast** — Explore climate impacts on seasonal harvest areas or habitat ranges using ecological calendars and satellite data, with governed access to sensitive observations.
   *(Applicable: tribal first foods monitoring, wildlife refuge management, agricultural extension services)*
4. **Grant Support Toolkit** — Start with a local environmental concern and build maps, statistics, and narratives ready for EPA/USDA/FEMA submissions.
   *(Applicable: tribal EPA EJ grants, municipal FEMA hazard mitigation, conservation USDA programs)*
5. **Cumulative Impact Dashboard** — Aggregate air, water, noise, and socioeconomic indicators across jurisdictions to build a defensible environmental justice assessment.
   *(Applicable: tribal environmental justice, municipal health departments, humanitarian field offices)*
6. **Governed Data Export** — Package spatial analysis results with full audit metadata, consent status, and appropriate redactions for sharing with external agencies or legal proceedings.
   *(Applicable: tribal council submissions, inter-agency data sharing, defense/intelligence reporting)*

## Value Proposition
- Cut environmental review and compliance reporting time from weeks to days while retaining full audit trails.
- Package reusable analysis templates: each prompt maps a policy question to a map, report, and citation trail ready for agency or legal submission.
- Deploy an on-prem reference stack in a day, with approval workflows, audit logging, and data-residency guarantees built in.
- Track measurable outcomes: acres protected, grant dollars secured, compliance packets delivered, analyst hours saved.
- See [Tribal Decision-Maker Brief](docs/brief.md) and [Tribal Legal Counsel Brief](docs/attorney_brief.md) for audience-specific value summaries.

## Governance and Data Control Features (in design)
- **Consent-aware data layers**: collective consent, hierarchical approval workflows (e.g., elder approval for Indigenous data, supervisor sign-off for classified data), time-bound access windows (seasonal restrictions, embargo periods).
- **Automatic redaction and watermarking** of sensitive geometry in external exports.
- **Metadata licensing framework**: Traditional Knowledge labels, CARE principles, Creative Commons, custom organizational schemas.
- **Audit ledger** capturing who accessed what, under which consent agreement, with cryptographic signing.
- **Offline-first deployment path** (local models, proj.db, PMTiles) so air-gapped operations remain viable.
- See `docs/data_sovereignty.md`, `docs/community_process.md`, and `docs/legal_architecture.md` for Indigenous-specific governance, consultation, and legal frameworks.

## Developer Experience (planned)
- OpenAPI 3.1 spec + Redoc portal generated from the FastAPI service (targeting `/docs/openapi.yaml`).
- Typed Python SDK (`gis-oss-sdk`) with sync/async clients and Pydantic models.
- MapLibre playground for composing queries, visualizing tiles, and exporting cURL/Python snippets.
- QGIS plugin template, ArcGIS Pro Python toolbox, and FME Server connector for enterprise workflows.
- Jupyter "magic" commands (`%%gis_oss`) for rapid spatial prototyping in notebooks.
- See `docs/developer_experience.md` for the full DevEx roadmap.

```bash
curl -X POST "http://localhost:8000/query" \
  -H "X-API-Key: dev_key_change_in_production" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Buffer this point by 500 meters",
    "operation": "buffer",
    "geometry": {"type": "Point", "coordinates": [-122.42, 37.77]},
    "distance": 500,
    "units": "meters"
  }'
```

## Benchmarks & Targets
- **Latency**: 1.5 s (p50) / 3.0 s (p95) / 6.0 s (p99) for core spatial queries on 200 GB vector + 5 TB raster stack; Phase 2 → 1.0/2.0/4.0 s.
- **Accuracy**: ≥85 % on domain-specific QA sets (watersheds, habitat change, compliance overlays); ≥92 % with fine-tuned SQL model.
- **Throughput**: Sustain 3 structured queries/sec per GPU; autoscale to 30 analysts during peak operations (fire season, grant deadlines, field campaigns).
- **Impact metrics**: Acres protected/restored, grant dollars secured, compliance packets delivered, water-quality improvements, carbon sequestered, analyst hours saved.

## Modern GIS Component Map
- **Spatial storage**: PostgreSQL + PostGIS + TimescaleDB for vector and temporal analytics.
- **Raster services**: Cloud-optimized GeoTIFFs (COG) via TiTiler; PMTiles/MBTiles for offline basemaps.
- **Vector delivery**: pg_tileserv (or martin) provides MVT tiles for MapLibre, cached via Redis/Varnish.
- **Streaming**: Kafka/Redpanda topics for field telemetry; Kestra triggers downstream processing and alerting.
- **Batch pipeline**: Airflow orchestrates ETL, dbt manages analytical models, Apache Sedona handles large-scale raster/vector crunching.
- **Toolchain**: FastAPI + LLM orchestrator + deterministic PostGIS/GDAL tooling.
- **Integrations**: QGIS plugin, ArcGIS Pro add-in, FME Server webhooks, Jupyter magics ensure humans stay in the loop.

## Architecture Overview

### Conceptual Flow: From Query to Governed Output

![Conceptual diagram showing the workflow from an analyst query, through governance checks verifying consent and protecting sensitive sites, to spatial analysis with PostGIS and LLM, report generation with audit logging, and final delivery ready for decision-makers or agency submission](./docs/diagrams/conceptual-flow.svg)

*How GIS-OSS processes queries while enforcing data governance at every step*

### Technical Architecture

![Detailed technical architecture diagram showing six layers: User Interfaces (QGIS, Web UI, API clients, Jupyter), Gateway (FastAPI, GraphQL, Streaming), Intelligence (Router LLM, SQL Generator, Spatial Orchestrator, Report Writer, vLLM Pool), Execution (PostGIS, TiTiler, tile servers, Apache Sedona, orchestration), Data & Governance (PostgreSQL, vector stores, object storage, STAC catalog, audit ledger, carbon metrics, event streaming), and Enablement & Ops (Auth/Policy, Observability, Config, Offline Assets)](./docs/diagrams/architecture.svg)

*Layered architecture emphasizing governance, auditability, and offline-first operations*

📝 **[View/Edit Diagrams](./docs/diagrams/)** — Source files and rendering instructions for contributors

### Layer Responsibilities

| Layer | Core Components | Responsibilities |
|-------|-----------------|------------------|
| User | QGIS plugin, Web UI, API clients, Jupyter/CLI | Capture NL queries, render maps/reports, integrate with analyst workflows |
| Gateway | FastAPI gateway, optional GraphQL adapter, streaming endpoints | Authentication, rate limiting, request validation, multi-protocol surface |
| Intelligence | Router LLM, SQL generator, tool orchestrator, report writer, vLLM serving pool | Intent detection, NL→SQL/tool translation, reasoning chains, structured narrative output |
| Execution | PostGIS + TimescaleDB, TiTiler/GDAL, pg_tileserv/martin, Apache Sedona, Airflow/dbt/Kestra | Execute spatial analytics, manage tiles/rasters, schedule ETL, scale out heavy workloads |
| Data & Governance | PostgreSQL schemas, pgvector + Redis, object storage (COGs/PMTiles), STAC catalog, audit ledger, carbon metrics, Kafka/Redpanda | Persist datasets, manage embeddings/caches, track lineage/licensing, stream updates, measure sustainability |
| Enablement & Ops | Auth/OIDC, observability stack, configuration/feature flags, offline asset prep | Security/policy enforcement, monitoring/alerting, configuration management, air-gapped readiness |

## Community & Ecosystem
- Launch **SpatialBench** — an open benchmark suite for geospatial LLM evaluation, covering watershed analysis, habitat monitoring, climate adaptation, compliance reporting, and governed data workflows.
- Publish a prompt & scenario library (25+ vetted prompts) with notebooks that show expected SQL/tool chains and report templates.
- Partner with tribal colleges and Indigenous data sovereignty networks (founding community), university GIS programs, conservation organizations, and municipal planning departments.
- Keep the core stack Apache-licensed while offering enterprise add-ons (HA tooling, enhanced governance, managed hosting).
- See `docs/ecosystem.md` for the detailed community roadmap and success metrics.

## Getting Started (Developers)
1. Install Docker & Docker Compose (v2+).
2. Clone this repository and copy `.env.example` to `.env` with local credentials.
   Set both `POSTGRES_PASSWORD` and `POSTGRES_READONLY_PASSWORD` (or set `READONLY_DATABASE_URL`).
3. Run `./scripts/setup_dev.sh` to launch PostGIS, TiTiler, and auxiliary services.
   If your Postgres volume already existed before this change, run `./scripts/migrate_readonly_role.sh` once.
4. Execute `pytest` to validate spatial tool wrappers before integrating the LLM service.
5. Run quality grounding checks:
   - `python scripts/run_grounding_eval.py`
   - `python scripts/verify_sample_data_provenance.py`

### For Offline/Air-gapped Deployment
1. On a connected machine, run `./scripts/prepare_offline.sh` to download all dependencies.
2. Transfer the entire project directory including `offline-deps/` to the target system.
3. Set `ENABLE_OFFLINE_MODE=true` in `.env` and follow `offline-deps/OFFLINE_INSTALL.md`.

> Note: Model weights are large (7B–70B parameters). Start with Qwen 2.5 7B (INT8) for development on a single GPU, scaling to 32B/70B models for production accuracy. LoRA adapters for router/SQL/report tiers live under `models/finetuned/`.

## Repository Layout
- `src/` — FastAPI service, security hooks, DB session management, and PostGIS tool wrappers (implemented).
- `tests/` — Unit tests for API and spatial helpers (implemented).
- `scripts/` — Setup/offline prep/data loading/diagram rendering scripts (implemented).
- `config/` — Postgres Docker image and initialization SQL (implemented).
- `docs/` — Architecture overview, domain playbooks, data sovereignty, community process, legal architecture, deployment notes.
- `core/` *(planned)* — Expanded backend modules beyond the current `src/` scaffold.
- `pipeline/` *(planned)* — Airflow DAGs, dbt project, Kestra flows.
- `web/` *(planned)* — MapLibre-based UI for demos and workshops.
- `data/` *(planned)* — Additional sample GeoParquet/COG/PMTiles assets with clear licensing metadata.
- `prompts/` *(planned)* — Prompt & scenario library organized by domain.
- `benchmarks/` *(planned)* — SpatialBench harness and evaluation scripts.

## Next Executive Checkpoint
- Validate the Week 1 deliverables (running spatial stack + tested tooling).
- Review demo scenarios across target domains (tribal stewardship, conservation, municipal planning).
- Approve partner engagement plan: tribal co-design outreach, university partnerships, conservation district pilots, conference schedule (FOSS4G, URISA, AGU, Indigenous Mapping Workshop).

The governance architecture is not a feature layer. It is the foundation. Every query, every export, every cached result passes through consent checks, audit logging, and policy enforcement — not because governance was bolted on, but because the most demanding use case (Indigenous data sovereignty) required it from the start. That architectural decision benefits every organization that deploys GIS-OSS.
