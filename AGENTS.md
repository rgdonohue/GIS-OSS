# GIS-OSS Agent Instructions

This repository uses deterministic geospatial operations and explicit governance controls.  
Agent changes must prioritize factual grounding over feature expansion.

## Core Engineering Rules
- Do not add speculative features without an issue or explicit request.
- Prefer deterministic PostGIS/GDAL execution over probabilistic model output.
- Reject ambiguous natural-language requests instead of inferring missing parameters.
- Never bypass authorization, table allowlists, or audit logging paths.
- Keep all security-sensitive defaults fail-closed.

## Grounding and Provenance
- Query responses must include `verification_status` and `evidence`.
- If evidence is incomplete, return `unverified` rather than implied certainty.
- Do not store raw API keys or raw prompt text in audit logs.
- Geometry in logs must remain redacted/summarized.

## Testing and Validation
- Required local checks before commit:
  - `ruff check src tests scripts/generate_project_status.py`
  - `mypy src`
  - `pytest -q`
  - `python scripts/generate_project_status.py --check`
- Add regression tests for every parser, policy, or security behavior change.

## CI and Supply Chain
- Keep generated docs in sync (`docs/project_status.md`).
- Do not remove CodeQL/dependency-review/attestation workflows once added.
- Pin action versions and avoid unreviewed remote script execution in workflows.

## Scope-Specific Instructions
- `src/api/AGENTS.md` applies to API and request/response contract changes.
- `src/security/AGENTS.md` applies to authz, audit, and policy enforcement changes.
