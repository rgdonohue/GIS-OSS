# Database Authorization Onboarding

This guide covers enabling database-backed role resolution for API keys.

## Overview
- Auth mode is controlled by `AUTHZ_BACKEND`.
- Default is `database` (with static fallback).
- API keys are never stored in plaintext. `governance.api_keys` stores SHA-256 hashes.

## 1. Configure Environment
Set the following in `.env`:

```bash
AUTHZ_BACKEND=database
ALLOW_PUBLIC_API=false
```

Optional fallback mode:

```bash
AUTHZ_BACKEND=static
API_KEY=your_single_static_key
```

## 2. Ensure Database Schema Is Present
`config/postgres/01-init-postgis.sql` now creates:
- `governance.api_keys`
  - `key_hash` (unique SHA-256 fingerprint)
  - `role` (`public|member|elder|admin`)
  - `active` flag

If your Postgres volume predates this schema, apply migration manually or recreate the dev DB.

## 3. Add or Update API Key Roles
Use the helper script:

```bash
python scripts/manage_api_key_role.py --api-key "member:demo_key_123" --role member
python scripts/manage_api_key_role.py --api-key "elder:demo_key_456" --role elder
python scripts/manage_api_key_role.py --api-key "admin:demo_key_789" --role admin
```

Deactivate a key:

```bash
python scripts/manage_api_key_role.py --api-key "member:demo_key_123" --role member --no-active
```

## 4. Verify Behavior
`/query` and `/query/natural` enforce:
- API key presence (when `ALLOW_PUBLIC_API=false`)
- role-based permission checks
- audit logging with resolved role and trace correlation metadata

Quick check:

```bash
curl -X POST "http://localhost:8000/query" \
  -H "X-API-Key: member:demo_key_123" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Buffer this point by 100 meters",
    "operation": "buffer",
    "geometry": {"type":"Point","coordinates":[-122.42,37.77]},
    "distance": 100,
    "units": "meters"
  }'
```

## 5. Operational Notes
- Keep `ALLOW_PUBLIC_API=false` in non-test environments.
- Rotate keys by upserting a new key and disabling old key rows.
- Prefer DB-backed keys over prefix-only conventions during rollout.
- Do not log plaintext API keys or raw prompt/geometry in audit sinks.
