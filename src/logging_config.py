"""
Central logging configuration for the GIS-OSS stack.

We rely on structlog for structured (JSON-friendly) logs while keeping
standard logging compatibility for third-party libraries.
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(level: str | None = None) -> None:
    """Configure structlog + standard logging."""

    log_level = level or "INFO"
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="ISO", key="timestamp"),
            structlog.stdlib.filter_by_level,
            structlog.processors.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )
