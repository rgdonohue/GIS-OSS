from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

import structlog
from psycopg2 import pool
from psycopg2.extensions import connection

from src.api.config import Settings

logger = structlog.get_logger(__name__)

_connection_pool: pool.ThreadedConnectionPool | None = None


def _build_conninfo_dsn(
    *,
    db_name: str,
    db_user: str,
    db_password: str,
    db_host: str,
    db_port: int,
) -> str:
    return (
        f"dbname={db_name} user={db_user} "
        f"password={db_password} host={db_host} "
        f"port={db_port}"
    )


def resolve_read_dsn(settings: Settings) -> str:
    read_dsn = settings.db_read_dsn.strip()
    if read_dsn:
        return read_dsn

    primary_dsn = settings.db_dsn.strip()
    if primary_dsn:
        return primary_dsn

    read_user = settings.db_read_user.strip() or settings.db_user
    read_password = settings.db_read_password or settings.db_password
    return _build_conninfo_dsn(
        db_name=settings.db_name,
        db_user=read_user,
        db_password=read_password,
        db_host=settings.db_host,
        db_port=settings.db_port,
    )


def initialize_pool(settings: Settings) -> None:
    """Create the global connection pool if it does not already exist.

    Uses ThreadedConnectionPool for thread-safe access, which is required
    when FastAPI runs sync endpoints in a threadpool (the default behavior
    with Uvicorn/Gunicorn).
    """

    global _connection_pool
    if _connection_pool is not None:
        return

    dsn = resolve_read_dsn(settings)
    logger.info(
        "db.pool.initialize",
        host=settings.db_host,
        db=settings.db_name,
        min=settings.db_pool_min,
        max=settings.db_pool_max,
    )
    _connection_pool = pool.ThreadedConnectionPool(
        minconn=settings.db_pool_min,
        maxconn=settings.db_pool_max,
        dsn=dsn,
    )


def release_pool() -> None:
    """Close the connection pool (used on application shutdown)."""

    global _connection_pool
    if _connection_pool is not None:
        logger.info("db.pool.close")
        _connection_pool.closeall()
        _connection_pool = None


@contextmanager
def connection_context(settings: Settings) -> Generator[connection, None, None]:
    """Context manager that yields a database connection from the pool."""

    if _connection_pool is None:
        initialize_pool(settings)
    assert _connection_pool is not None

    conn = _connection_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _connection_pool.putconn(conn)


def db_connection_dependency(settings: Settings) -> Generator[connection, None, None]:
    """FastAPI dependency wrapper around connection_context."""

    with connection_context(settings) as conn:
        yield conn
