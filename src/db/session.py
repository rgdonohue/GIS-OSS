from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

import structlog
from psycopg2 import pool
from psycopg2.extensions import connection

from src.api.config import Settings

logger = structlog.get_logger(__name__)

_connection_pool: Optional[pool.SimpleConnectionPool] = None


def initialize_pool(settings: Settings) -> None:
    """Create the global connection pool if it does not already exist."""

    global _connection_pool
    if _connection_pool is not None:
        return

    dsn = (
        f"dbname={settings.db_name} user={settings.db_user} "
        f"password={settings.db_password} host={settings.db_host} "
        f"port={settings.db_port}"
    )
    logger.info(
        "db.pool.initialize",
        host=settings.db_host,
        db=settings.db_name,
        min=settings.db_pool_min,
        max=settings.db_pool_max,
    )
    _connection_pool = pool.SimpleConnectionPool(
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
