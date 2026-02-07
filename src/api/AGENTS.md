# API Agent Instructions

Applies to files under `src/api/`.

## Contract Stability
- Treat Pydantic request/response models as external contracts.
- Add fields in backward-compatible ways; do not silently remove fields.
- Keep `/query` deterministic and `/query/natural` strict (no implicit inference).

## Grounding Requirements
- Successful responses must include `verification_status` and `evidence`.
- Use `unverified` when provenance is incomplete.
- Error responses should be specific enough to fix input, without leaking sensitive internals.

## Operational Safety
- Keep rate limiting and auth checks on all query execution endpoints.
- Preserve audit logging calls on success and failure paths.
- Avoid logging raw geometry or API key material.
