#!/usr/bin/env python3
"""
Create or update hashed API key role mappings in governance.api_keys.
"""

from __future__ import annotations

import argparse
import os
import sys

import psycopg2

from src.security.authorization import api_key_fingerprint

ALLOWED_ROLES = {"public", "member", "elder", "admin"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage API key role mappings.")
    parser.add_argument("--api-key", required=True, help="Plain API key to hash and store.")
    parser.add_argument(
        "--role",
        required=True,
        choices=sorted(ALLOWED_ROLES),
        help="Role to assign to this API key.",
    )
    parser.add_argument(
        "--active",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether this key is active (default: true).",
    )
    return parser.parse_args()


def db_conn_kwargs() -> dict[str, object]:
    return {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": int(os.environ.get("POSTGRES_PORT", "5432")),
        "dbname": os.environ.get("POSTGRES_DB", "gis_oss"),
        "user": os.environ.get("POSTGRES_USER", "gis_user"),
        "password": os.environ.get("POSTGRES_PASSWORD", ""),
    }


def upsert_api_key_role(api_key: str, role: str, active: bool) -> None:
    key_hash = api_key_fingerprint(api_key)
    query = """
        INSERT INTO governance.api_keys (key_hash, role, active)
        VALUES (%s, %s, %s)
        ON CONFLICT (key_hash)
        DO UPDATE SET
            role = EXCLUDED.role,
            active = EXCLUDED.active,
            updated_at = NOW()
    """
    with psycopg2.connect(**db_conn_kwargs()) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (key_hash, role, active))
        conn.commit()


def main() -> int:
    args = parse_args()
    api_key = args.api_key.strip()
    if not api_key:
        print("Error: --api-key cannot be blank.", file=sys.stderr)
        return 2
    upsert_api_key_role(api_key=api_key, role=args.role, active=args.active)
    print(f"Upserted key role mapping: role={args.role}, active={args.active}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
