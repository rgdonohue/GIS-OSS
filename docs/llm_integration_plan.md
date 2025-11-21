# NL→GIS via Ollama — Implementation Plan

Status: ready to build. This captures the weekend plan to wire natural-language queries to the existing GIS operations using Ollama + Qwen2.5.

## Goals
- Stand up an Ollama-backed LLM client that converts NL → structured operations (`buffer`, `calculate_area`, `find_intersections`, `nearest_neighbors`, `transform_crs`).
- Add a `/query/natural` endpoint that reuses the existing `_execute_structured_operation` path (rate limit + API key + permission checks stay intact).
- Add tribal-focused prompting scaffolds and validation/guardrails so responses are strict JSON.
- Ship unit tests (mocked) and a short usage doc with curl examples.

## Target Model (default)
- `qwen2.5:7b-instruct` via Ollama (≈4.7 GB, Apache 2.0, good JSON/SQL fidelity, runs on CPU).
- Fallbacks (parametrize model name): `llama3.2:3b` (smaller), `mistral:7b` (similar size).

## Files to Create/Update
- `src/llm/ollama_client.py` — HTTPX client, JSON-only generation, structured logging.
- `src/llm/prompts.py` — system prompt + tribal few-shots for treaty/jurisdiction/sacred-site contexts.
- `src/llm/parsers.py` — strict JSON schema/validation and normalization of LLM output to operation + params.
- `src/api/main.py` — add `/query/natural` endpoint that:
  - Calls the LLM parser,
  - Builds `QueryRequest`,
  - Reuses `_execute_structured_operation`,
  - Keeps rate limit + API key + permission dependencies.
- `tests/unit/llm/` — mocked HTTPX tests for client + parser behavior.
- `docs/llm_integration.md` — setup steps, curl examples, hardware notes.

## Guardrails
- Force `format: "json"` on the Ollama request.
- Parse/validate output with operation enum and required params per op; 400 on malformed outputs.
- Log `llm.parse_query` with input/parsed (no PII).

## Steps (suggested order)
1) Create `src/llm/ollama_client.py` with configurable `base_url`/`model`, timeout, JSON-only responses.  
2) Add `src/llm/prompts.py` (system prompt + tribal few-shots for treaty boundaries, sacred sites, jurisdiction).  
3) Add `src/llm/parsers.py` with a schema/validator to map LLM JSON → `{operation, parameters, intent}`; raise on invalid.  
4) Wire `/query/natural` in `src/api/main.py` to call client → parser → `_execute_structured_operation`; keep existing rate limit/authz.  
5) Tests: add mocked HTTPX tests for client/parsing; add endpoint test that stubs the client and asserts operation execution.  
6) Docs: `docs/llm_integration.md` with install + curl examples and model switches.  

## Ollama Quick Start (local sanity check)
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b-instruct
ollama run qwen2.5:7b-instruct "What is PostGIS?"
```

## Curl Smoke Test (after wiring)
```bash
# Start Ollama: ollama serve
# Start API: source venv/bin/activate && API_KEY=test123 uvicorn src.api.main:app --reload
curl -X POST "http://localhost:8000/query/natural" \
  -H "X-API-Key: test123" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Calculate the area of polygon [[0,0],[0,1],[1,1],[1,0],[0,0]] in acres"}'
```

## Testing Plan
- Unit: mock HTTPX responses to assert JSON parsing/validation and log fields.  
- Endpoint: stub the LLM client to return a known operation; assert `/query/natural` runs `_execute_structured_operation`.  
- Optional later: integration test marked slow that calls a running Ollama instance.

## Next-Weekend Options
- Swap Ollama for vLLM or llama.cpp if you need throughput/offline edge.  
- Add SQL generation path for richer queries.  
- Expand few-shots for tribal governance workflows (consent, seasonal access, sacred-site redaction).  
- Optional Redis-backed rate limiting if you scale to multiple API instances.
