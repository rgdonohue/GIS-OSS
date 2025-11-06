# GIS-OSS Architecture

## Overview

GIS-OSS is a privacy-focused geospatial intelligence system that uses open-weight language models to orchestrate spatial data pipelines. The system prioritizes data sovereignty, deterministic spatial operations, and clear audit trails.

## Design Principles

1. **LLM as Orchestrator, Not Calculator**: The LLM interprets natural language and coordinates tools; all spatial calculations use PostGIS/GDAL
2. **Fail-Safe Degradation**: When the LLM is uncertain, fall back to deterministic SQL/functions
3. **Progressive Enhancement**: Start with basic NL→SQL, add capabilities incrementally
4. **Audit Everything**: Log all queries, tool calls, and data sources for compliance

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     User Interface                       │
│                   (CLI / Web / API)                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    API Gateway                           │
│                    (FastAPI)                             │
│  • Request validation                                    │
│  • Authentication                                        │
│  • Rate limiting                                         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│               Query Processor                            │
│  • Natural language parsing                              │
│  • Intent classification                                 │
│  • Parameter extraction                                  │
└─────────┬──────────┬──────────────┬────────────────────┘
          │          │              │
          ▼          ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ LLM Service  │ │   RAG    │ │ Tool Registry│
│ (Qwen/Llama) │ │ (pgvector)│ │   (Python)   │
└──────┬───────┘ └─────┬────┘ └──────┬───────┘
       │               │              │
       └───────────────┼──────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                Spatial & Temporal Engine                 │
│  • PostGIS + TimescaleDB for vector + time-series        │
│  • GDAL/rasterio + TiTiler for COG rasters               │
│  • Vector tiles via pg_tileserv/martin                   │
│  • Projection management (EPSG)                          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Data Layer                              │
│  • PostgreSQL + PostGIS + TimescaleDB (geometries/time)  │
│  • pgvector (embeddings)                                 │
│  • Object storage (COG, STAC collections, PMTiles)       │
│  • Streaming bus (Kafka/Redpanda) for real-time feeds    │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### Query Processor
- Receives natural language queries
- Extracts spatial intent (buffer, intersect, nearest, etc.)
- Identifies referenced entities and parameters
- Routes to appropriate execution path
- **Router Model**: Lightweight 3B-class LLM classifies user intent, chooses tool chains, and sets reasoning effort.
- **SQL/Tool Generator**: Fine-tuned CodeLlama/PostGIS model generates deterministic SQL and tool parameters.
- **Narrative/Report Writer**: Mid-tier model (13–20B) crafts summaries, action plans, and structured outputs for planners.
- **Fallback Generalist**: Larger reasoning model (20B+) handles edge cases or escalated queries when the specialized stack fails.
- **Confidence & Routing**: Router returns per-intent confidence; low confidence triggers deterministic fallback templates.

### LLM Service
- **Model Tiers**:
  - Router: 3B instruction-tuned model (e.g., distilled Qwen 3B) for intent classification and policy checks.
  - SQL Generator: CodeLlama/PostGIS fine-tune for NL→SQL and tool parameterization.
  - Report Writer: Qwen 2.5 7B/14B or Llama 3.1 8B with retrieval context for narrative outputs.
  - Fallback: Qwen 2.5 32B or Llama 3.1 70B for complex reasoning/escalations.
- **Serving**: vLLM with INT8 quantization
- **Context**: 32,768 tokens (Qwen 2.5 native support)
- **Effective Context**: ~16k tokens after tool schemas and system prompt
- **Tools**: Function calling via JSON schema
- **Batching**: Dynamic batching with 50ms aggregation window

### Spatial & Temporal Engine
- **Vector Processing**: PostGIS core functions (ST_Buffer, ST_Intersection, ST_Distance, ST_TileEnvelope) with TimescaleDB hypertables for change-detection/temporal joins.
- **Raster Serving**: GDAL/rasterio for batch operations, TiTiler for dynamic COG/WMTS, optional raster algebra via rio-tiler.
- **Vector Tiles**: pg_tileserv or martin serving MVT tiles straight from PostGIS, cached via Redis/Varnish for low-latency visualization.
- **Projection Control**: Auto-detect and transform via EPSG codes with bundled proj.db; CRS choice logged alongside every query.
- **Validation**: Geometry validity checks and topology cleaning using `ST_IsValidDetail` + `ST_MakeValid`.
- **Fallback Geocoding**: Local Pelias instance or nominatim-docker.

### RAG & Knowledge System
- **Embedding Model**: BGE-small or all-MiniLM-L6-v2; upgrade path to Instructor-large for domain tuning.
- **Vector Store**: pgvector with HNSW indexing; Timescale continuous aggregates expose temporal context windows.
- **Retrieval**: Hybrid search (spatial + semantic) plus STAC metadata queries for raster provenance.
- **Caching**: Redis layer for hot embeddings and tile metadata.
- **Model Prompt Router**: Embedding-based classifier steers responses to Router/SQL/Report models.

### Data Pipeline & Orchestration
- **Batch ETL**: Apache Airflow orchestrates nightly/weekly loads (COG generation, STAC catalog refreshes, pg_tileserv materialized views).
- **Transformations**: dbt (with dbt-postgres + dbt-snowplow-spatial packages) manages versioned SQL models, documentation, and tests.
- **Event-Driven Workflows**: Kestra handles reactive pipelines (e.g., ingesting incoming sensor feeds, triggering re-tiling).
- **Distributed Processing**: Apache Sedona (Spark) for large-scale raster/vector processing when datasets exceed single-node capacity.
- **Streaming Ingestion**: Kafka/Redpanda topics capture IoT/telemetry; ksqlDB or Materialize create real-time aggregates surfaced through the LLM tools.

## Data Flow

### Simple Query Flow
```
1. User: "Show parks within 1km of Main Street"
2. Parse: Extract entity="Main Street", operation=buffer, distance=1km
3. Geocode: Main Street → LineString geometry
4. Execute: ST_Buffer(geom, 1000) then ST_Intersection
5. Return: GeoJSON with park polygons
```

### Complex Query Flow
```
1. User: "Which neighborhoods have seen the most development since 2020?"
2. LLM: Break into sub-queries:
   - Get neighborhoods polygons
   - Get building permits since 2020
   - Count permits per neighborhood
   - Calculate change metrics
3. Execute: Chain of SQL + tool calls
4. LLM: Synthesize results into narrative
5. Return: Formatted answer with citations
```

## Offline Dependencies Management

### Online Mode (Default)
- EPSG.io API for CRS lookups
- OSM Nominatim for geocoding
- WattTime API for carbon metrics
- Model downloads from HuggingFace

### Offline/Air-gapped Mode
- **CRS Data**: Bundled proj.db with full EPSG dataset
- **Geocoding**: Local Pelias or Nominatim container with pre-loaded region
- **Vector Tiles**: Pre-generated PMTiles (or martin cache) stored locally; MapLibre consumes from file system/HTTP.
- **COG/PMTiles**: `scripts/prepare_offline.sh` downloads sample COGs and PMTiles; users can swap in proprietary data.
- **Carbon Metrics**: Static grid intensity lookup table (updated quarterly)
- **Models**: Pre-downloaded to ./models/ directory
- **Base Maps**: Local MBTiles or PMTiles for visualization
- **Preparation**: Run `scripts/prepare_offline.sh` to download all dependencies

### Hybrid Mode
- Cache external API responses for 7 days
- Fallback to offline data when APIs unavailable
- Queue updates for when connectivity returns

## Deployment Options

### Development (Docker Compose)
- Single machine deployment
- All services in containers
- Shared volume for data
- Optional adapters: QGIS plugin dev mode, Jupyter notebook environment with magic commands, mock OpenAPI validation server.

### Production (Kubernetes)
- Horizontal scaling for API/LLM
- Separate PostGIS cluster
- TimescaleDB extension enabled for temporal workloads
- Martin/pg_tileserv pods for vector tiles
- TiTiler deployment for COG tiles
- Airflow/Kestra namespaces for orchestration
- Distributed object storage (MinIO/S3 compatible) for COG/STAC/PMTiles
- Integration services: API gateway exposing OpenAPI docs, FME Server webhook endpoints, managed JupyterHub for data science teams.

### Edge (Embedded)
- SQLite with SpatiaLite
- ONNX quantized models
- Local file storage

## Security & Governance

### Current Implementation (Phase 1)
- **Data Residency**: All processing on-premises
- **Basic Auth**: API key authentication via headers
- **Audit Logging**: Structured logs to file/stdout
- **License Tracking**: Manual attribution in responses

### Planned Security (Phase 2+)
- **Access Control**: OAuth 2.0 / OpenID Connect integration
- **Row-Level Security**: PostGIS RLS policies per tenant
- **Audit Trail**: Immutable event log with cryptographic signing
- **PII Protection**: Geometry generalization (simplify to >50m resolution)
- **Rate Limiting**: Per-user quotas via Redis

### Governance Automation
- **License Matrix**: STAC metadata with license fields
- **Attribution Engine**: Automatic citation generation
- **Dual Publishing**: Separate branches for CC-BY vs ODbL data
- **Compliance Reporting**: GDPR Article 17 erasure tracking

## Performance Targets

| Metric | Phase 1 Target | Phase 2 Target | Current |
|--------|---------------|----------------|---------|
| Simple query latency | < 3s | < 2s | TBD |
| Complex query latency | < 15s | < 10s | TBD |
| Throughput (per GPU) | 2-3 RPS | 5-10 RPS | TBD |
| Model accuracy | > 70% | > 85% | TBD |
| Concurrent users | 5 | 25 | TBD |

**Note**: Throughput scales linearly with GPU count in production deployment

## Future Enhancements

- [ ] Real-time collaboration
- [ ] Multi-model ensemble (LLM routing, guarded reasoning modes)
- [ ] Advanced visualization (deck.gl analytics)
- [ ] GPU-accelerated raster analytics (CUDA-enabled GDAL or rasterframes)
- [ ] Edge streaming support (MQTT ingestion mapped to Kafka topics)
