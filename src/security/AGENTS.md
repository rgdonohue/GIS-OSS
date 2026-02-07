# Security Agent Instructions

Applies to files under `src/security/`.

## Authorization
- Maintain explicit role-permission mappings; default deny for unknown permissions.
- Any role resolution fallback must be documented and tested.
- Do not add permissive shortcuts in production code paths.

## Secrets and Identity
- Never store raw secrets in source, logs, or test fixtures.
- If API keys are used for identity, compare hashed representations where possible.
- Prefer backend-resolved roles (DB/IdP) over key-prefix conventions.

## Regression Expectations
- Every security behavior change requires tests for both allow and deny paths.
- Include tests for malformed/unknown identity inputs.
