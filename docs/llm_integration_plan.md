# NL→GIS via Ollama — Updated Implementation Plan

Status: Partially implemented (opt-in local planner + strict validation scaffolding).

## Targets (MVP, still weekend-sized)
- NL → structured ops (`buffer`, `calculate_area`, `find_intersections`, `nearest_neighbors`, `transform_crs`) using Ollama by default.
- `/query/natural` reuses `_execute_structured_operation` with existing rate limit, API key, and permission dependencies.
- Provider abstraction so we can swap Ollama/vLLM/llama.cpp without touching the endpoint.
- Strict JSON validation + guardrails for inputs/outputs; bounded retries and graceful errors.

Implemented now:
- `src/llm/provider.py`, `src/llm/ollama_client.py`, `src/llm/planner.py`.
- `/query` can invoke local planner when `ENABLE_LOCAL_LLM_PLANNER=true`.
- Grounding regression fixtures in `evals/grounding_cases.json` + runner `scripts/run_grounding_eval.py`.

## Model
- Default: `qwen2.5:7b-instruct` (≈4.7 GB, Apache 2.0, good JSON/SQL). Parametrize model name.
- Fallbacks: `llama3.2:3b` (smaller), `mistral:7b` (similar size). Document quantization (4/8-bit) in the integration doc.

## Files to Create/Update
- `src/llm/provider.py` — `LLMProvider` interface (`generate_structured(prompt) -> dict`), provider factory.
- `src/llm/ollama_client.py` — implements provider; HTTPX client with timeout + bounded retries/backoff; JSON-only requests; optional TLS verify flag.
- `src/llm/prompts.py` — system prompt + tribal few-shots (treaty/jurisdiction/sacred-site/consent).
- `src/llm/parsers.py` — strict schema/validation (allowlisted operations/units, required params, SRID defaults, unit normalization); rejects unknown fields.
- `src/api/main.py` — `/query/natural` endpoint that calls provider → parser → `_execute_structured_operation`; add LLM-call rate limit (cheaper RPS) on this route.
- `tests/unit/llm/` — mocked HTTPX tests for retries, malformed JSON, unknown op/unit, and happy path; endpoint test with stubbed provider.
- `docs/llm_integration.md` — setup, curl examples, model/quantization notes, perf expectations, TLS guidance.

## Guardrails & Security (MVP scope)
- Inputs: cap prompt length, reject non-UTF-8/control tokens; trim whitespace.
- Outputs: force `format: "json"`; validate against allowlisted ops/units; 400 on malformed/ambiguous/unknown op.
- Prompt injection: constrained system prompt + strict post-validation; drop extra keys.
- Sensitive data: no raw geometry in error logs; add `sensitivity` tag stub for future governance gating (sacred/sensitive/public).
- LLM rate limit: separate limiter on `/query/natural` to protect the LLM backend.
- Transport: if remote Ollama, enable TLS verify and document it; default to localhost (no data leaves box).

## Reliability
- Retries: bounded attempts with exponential backoff on 5xx/timeouts; fail fast with clear error.
- Circuit-breaker (next iteration): short-circuit to 503 after repeated failures.
- Caching (optional next): LRU on parsed intents per API key for identical prompts.
- Observability: counters for calls/failures/parse errors/unknown ops; latency histogram; redacted logs.

## Governance Hooks (scaffold now)
- Few-shots that mention consent/sacred/seasonal.
- `sensitivity` field in parsed output (stub classifier).
- Permission hook already on `/query`; later can enforce stricter perms when `sensitivity != public`.
- Audit logging (future): log operation/table hints, sensitivity, and api_key/user (no raw geom).

## Steps (order of work)
1) Interface: `LLMProvider` + factory in `src/llm/provider.py`.
2) Client: `ollama_client.py` with retries/timeouts, TLS option, JSON-only requests.
3) Prompts: add base system prompt + tribal few-shots in `prompts.py`.
4) Parser: strict schema in `parsers.py` (ops/units/SRID defaults, unit normalization, drop extras).
5) Endpoint: `/query/natural` uses provider → parser → `_execute_structured_operation`; add LLM-specific rate limit dependency.
6) Tests: mock HTTPX; assert retries; assert 400 on bad JSON/unknown op/unknown unit; endpoint stub test.
7) Docs: `docs/llm_integration.md` with install, curl, model swap, quantization, TLS notes.

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

## Testing Plan (MVP)
- Unit: HTTPX mocked; retries/backoff; bad JSON; unknown op/unit; happy path.
- Endpoint: stub provider; assert `_execute_structured_operation` is invoked; 400s on validation failures.
- (Next) Slow integration test against live Ollama; prompt regression suite later.

## Next Iterations (post-MVP)
- Real sensitivity classifier + permission enforcement before execution.
- Circuit breaker + caching + Redis-backed rate limiting for multi-instance.
- Streaming responses; batching (if needed).
- Perf/gov benchmarks; prompt regression suite; A/B testing for prompt changes.
