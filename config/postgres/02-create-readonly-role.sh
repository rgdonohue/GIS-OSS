#!/bin/bash

set -euo pipefail

readonly_user="${POSTGRES_READONLY_USER:-gis_readonly}"
readonly_password="${POSTGRES_READONLY_PASSWORD:-}"
database_name="${POSTGRES_DB:-gis_oss}"

if [ -z "${readonly_password}" ]; then
    echo "POSTGRES_READONLY_PASSWORD is empty; skipping read-only role bootstrap."
    exit 0
fi

psql -v ON_ERROR_STOP=1 \
    --username "${POSTGRES_USER}" \
    --dbname "${database_name}" \
    --set=readonly_user="${readonly_user}" \
    --set=readonly_password="${readonly_password}" \
    --set=database_name="${database_name}" <<'SQL'
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

