# GIS-OSS — Private Geospatial Intelligence Sandbox

## Executive Overview
- Builds an on-prem, privacy-preserving spatial assistant driven by open-weight LLMs.
- Orchestrates deterministic PostGIS/GDAL tooling so every result is auditable.
- Targets ESRI-heavy teams that need a sandboxed AI copilot without sending data offsite.
- Delivers training-ready playbooks and demos aligned with modernization engagements.

## Why This Matters Now
- **Open-weight models** like Qwen 2.5 (Apache 2.0) and Llama 3.1 enable private hosting with strong reasoning capabilities.
- **Client pressure**: regulated utilities, cities, and transportation agencies are asking for AI augmentation but require data residency and reproducible workflows.
- **Modernization gap**: most ESRI shops lack a controlled environment to experiment with NL→GIS automation; we can supply both the platform and the enablement content.

## Solution Snapshot
- **LLM as orchestrator**: natural-language parsing and task planning only; spatial math delegated to trusted engines.
- **Deterministic spatial core**: PostGIS 3.4, GDAL/rasterio, and TiTiler for rasters; pgvector augments search with semantic context.
- **Governance built-in**: license-aware STAC catalog, audit logging, optional carbon tracking, and scripted dual-publishing workflows.
- **Deployment flexibility**: Docker Compose for field demos, Kubernetes for production, and a lightweight edge profile (SpatiaLite + ONNX) for disconnected sites.

See `docs/architecture.md` for the full component breakdown.

## Use Cases We Can Demo Quickly
- **Emergency response**: “List shelters within 1 km of schools, avoiding flood zones.”
- **Urban planning**: “Summarize by neighborhood where permits jumped since 2020 and map the hotspots.”
- **Environmental compliance**: “Flag parcels intersecting riparian buffers and return a permit-ready report.”

Each scenario exercises NL→SQL translation, spatial joins, and narrative reporting that technical trainers can teach hands-on.

## Current Status
- Draft backlog in `TODO.md` covering the first four weeks (environment, spatial functions, NL interface, governance).
- Architecture note completed with realistic specifications (`docs/architecture.md`).
- Docker Compose + PostGIS scaffold ready; model selection: Qwen 2.5 7B/32B or Llama 3.1 8B/70B.

## Roadmap (Phase 0 Pilot)
1. **Step 1** – Stand up PostGIS/pgvector stack, load sample datasets, expose five audited spatial tools.
2. **Step 2** – Wire FastAPI façade, connect LLM orchestrator, capture baseline accuracy/latency on ten scripted queries.
3. **Step 3** – Layer retrieval augmentation, enrich attribution pipeline, and ship trainer-friendly notebooks.
4. **Step 4** – Package demo runbook + workshop deck for client pilots; decision gate on extending to 120B model.

## Value for Technical Training & Services
- Provides a ready-made lab for AI-in-GIS workshops, with deterministic outputs your trainers can trust.
- Enables reusable lesson content: each golden-path query in code + notebook format for participants.
- Positions the services team to upsell managed deployments (Kubernetes profile, audit automation, carbon reporting).
- Creates a reference architecture that doubles as marketing collateral for modernization engagements.

## Getting Started (Developers)
1. Install Docker & Docker Compose (v2+).
2. Clone this repository and copy `.env.example` to `.env` with local credentials.
3. Run `./scripts/setup_dev.sh` to launch PostGIS, TiTiler, and auxiliary services.
4. Execute `pytest` to validate spatial tool wrappers before integrating the LLM service.

### For Offline/Air-gapped Deployment
1. On a connected machine, run `./scripts/prepare_offline.sh` to download all dependencies.
2. Transfer the entire project directory including `offline-deps/` to the target system.
3. Set `ENABLE_OFFLINE_MODE=true` in `.env` and follow `offline-deps/OFFLINE_INSTALL.md`.

> Note: Model weights are large (7B-70B parameters). We recommend starting with Qwen 2.5 7B (INT8) for development on single GPU, scaling to 32B/70B models for production accuracy.

## Repository Layout
- `docs/` — Architecture overview, deployment notes (expanding with governance/security playbooks).
- `core/` *(planned)* — FastAPI backend, LLM orchestration, spatial engine modules.
- `web/` *(planned)* — MapLibre-based UI for demos and workshops.
- `data/` *(planned)* — Sample GeoParquet/COG assets with clear licensing.
- `tests/` *(planned)* — Unit + integration harness, plus benchmark scripts.
- `scripts/` *(planned)* — Setup, model download, and data seeding utilities.

## Next Executive Checkpoint
- Validate the Week 1 deliverables (running spatial stack + tested tooling).
- Review demo storyboard and training outline.
- Approve resource plan for GPU hardware and client pilot scheduling.

With the groundwork above, we can walk into funding conversations with a tangible sandbox, a believable execution plan, and ready-to-deliver training assets. This keeps us ahead of competitors still pitching generic “AI copilots” without respecting geospatial compliance realities.
