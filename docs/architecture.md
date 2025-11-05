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
│                 Spatial Engine                           │
│  • PostGIS for vector operations                         │
│  • GDAL/rasterio for raster processing                   │
│  • Projection management (EPSG)                          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                  Data Layer                              │
│  • PostgreSQL + PostGIS (geometries)                     │
│  • pgvector (embeddings)                                 │
│  • Object storage (COGs/STACs)                           │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### Query Processor
- Receives natural language queries
- Extracts spatial intent (buffer, intersect, nearest, etc.)
- Identifies referenced entities and parameters
- Routes to appropriate execution path

### LLM Service
- **Model**: Qwen 2.5 7B (dev) / 32B (production)
- **Serving**: vLLM with INT8 quantization
- **Context**: 32,768 tokens (Qwen 2.5 native support)
- **Effective Context**: ~16k tokens after tool schemas and system prompt
- **Tools**: Function calling via JSON schema
- **Batching**: Dynamic batching with 50ms aggregation window

### Spatial Engine
- **PostGIS Functions**: ST_Buffer, ST_Intersection, ST_Distance, etc.
- **Projections**: Auto-detect and transform via EPSG codes
- **Validation**: Geometry validity checks before operations
- **Offline CRS**: Bundled proj.db (150MB) for air-gapped deployments
- **Fallback Geocoding**: Local Pelias instance or nominatim-docker

### RAG System
- **Embedding Model**: BGE-small or all-MiniLM-L6-v2
- **Vector Store**: pgvector with HNSW indexing
- **Retrieval**: Hybrid search (spatial + semantic)

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
- **Carbon Metrics**: Static grid intensity lookup table (updated quarterly)
- **Models**: Pre-downloaded to ./models/ directory
- **Base Maps**: Local MBTiles or PMTiles for visualization

### Hybrid Mode
- Cache external API responses for 7 days
- Fallback to offline data when APIs unavailable
- Queue updates for when connectivity returns

## Deployment Options

### Development (Docker Compose)
- Single machine deployment
- All services in containers
- Shared volume for data

### Production (Kubernetes)
- Horizontal scaling for API/LLM
- Separate PostGIS cluster
- Distributed object storage

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

- [ ] Streaming data ingestion
- [ ] Multi-model ensemble
- [ ] Distributed processing
- [ ] Real-time collaboration
- [ ] Advanced visualization