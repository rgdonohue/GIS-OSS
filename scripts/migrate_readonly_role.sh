#!/bin/bash

set -euo pipefail

if command -v docker-compose &>/dev/null; then
    COMPOSE_CMD=(docker-compose)
elif docker compose version &>/dev/null; then
    COMPOSE_CMD=(docker compose)
else
    echo "Error: Docker Compose is not installed"
    exit 1
fi

if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

POSTGRES_DB="${POSTGRES_DB:-gis_oss}"
POSTGRES_USER="${POSTGRES_USER:-gis_user}"
POSTGRES_READONLY_USER="${POSTGRES_READONLY_USER:-gis_readonly}"
POSTGRES_READONLY_PASSWORD="${POSTGRES_READONLY_PASSWORD:-changeme_readonly_in_production}"

"${COMPOSE_CMD[@]}" exec -T postgres psql -v ON_ERROR_STOP=1 \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --set=readonly_user="${POSTGRES_READONLY_USER}" \
    --set=readonly_password="${POSTGRES_READONLY_PASSWORD}" \
    --set=database_name="${POSTGRES_DB}" <<'SQL'
SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'readonly_user', :'readonly_password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'readonly_user')
\gexec

SELECT format('ALTER ROLE %I WITH LOGIN PASSWORD %L', :'readonly_user', :'readonly_password')
\gexec

SELECT format('GRANT CONNECT ON DATABASE %I TO %I', :'database_name', :'readonly_user')
\gexec

SELECT format('GRANT USAGE ON SCHEMA data TO %I', :'readonly_user')
\gexec
SELECT format('GRANT SELECT ON ALL TABLES IN SCHEMA data TO %I', :'readonly_user')
\gexec
SELECT format('ALTER DEFAULT PRIVILEGES IN SCHEMA data GRANT SELECT ON TABLES TO %I', :'readonly_user')
\gexec

SELECT format('GRANT USAGE ON SCHEMA governance TO %I', :'readonly_user')
\gexec
SELECT format('GRANT SELECT ON ALL TABLES IN SCHEMA governance TO %I', :'readonly_user')
\gexec
SELECT format('ALTER DEFAULT PRIVILEGES IN SCHEMA governance GRANT SELECT ON TABLES TO %I', :'readonly_user')
\gexec

SELECT format('REVOKE ALL ON SCHEMA audit FROM %I', :'readonly_user')
\gexec
SELECT format('REVOKE ALL ON ALL TABLES IN SCHEMA audit FROM %I', :'readonly_user')
\gexec
SQL

echo "Read-only role migration applied for user '${POSTGRES_READONLY_USER}'."
