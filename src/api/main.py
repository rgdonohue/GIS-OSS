from __future__ import annotations

import hashlib
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Any

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from psycopg2 import Error as PsycopgError
from psycopg2.extensions import connection as PGConnection
from pydantic import BaseModel, Field

from src.db.session import (
    connection_context,
    db_connection_dependency,
    initialize_pool,
    release_pool,
)
from src.governance.audit_logger import log_query_event
from src.logging_config import configure_logging
from src.nl import NaturalQueryParseError, parse_natural_query_prompt
from src.security.authorization import Permission, enforce_permission
from src.security.rate_limit import RateLimitExceeded, build_rate_limiter
from src.spatial import (
    buffer_geometry,
    calculate_area,
    find_intersections,
    nearest_neighbors,
    transform_crs,
)

from .config import Settings, get_settings


class QueryRequest(BaseModel):
    prompt: str = Field(..., description="Natural-language geospatial question.")
    return_format: str = Field(
        "geojson",
        description="Desired response format (e.g., geojson, table, summary).",
    )
    include_confidence: bool = Field(
        False, description="Whether to include confidence scores when available."
    )
    operation: str | None = Field(
        None,
        description="Structured operation (buffer, calculate_area, find_intersections, nearest_neighbors, transform_crs).",
    )
    geometry: dict[str, Any] | None = Field(
        None, description="Primary geometry in GeoJSON format."
    )
    geometry_b: dict[str, Any] | None = Field(
        None, description="Secondary geometry for operations like intersection."
    )
    table: str = Field(
        default="data.features",
        description="Target table for query-based operations.",
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Number of results to return (1-100).",
    )
    distance: float | None = Field(
        None,
        ge=0,
        description="Distance for buffer or nearest-neighbor operations.",
    )
    units: str | None = Field(
        None, description="Units for distance/area (default meters)."
    )
    srid: int = Field(default=4326, ge=1, le=999_999, description="Input geometry SRID.")
    from_epsg: int | None = Field(
        None,
        ge=1,
        le=999_999,
        description="Source EPSG for CRS transformations.",
    )
    to_epsg: int | None = Field(None, ge=1, le=999_999, description="Target EPSG.")


class QueryResponse(BaseModel):
    status: str
    message: str
    request: QueryRequest
    result: Any | None = None


class NaturalQueryRequest(BaseModel):
    prompt: str = Field(..., description="Natural-language query with embedded operation JSON.")
    return_format: str = Field(
        "geojson",
        description="Desired response format (e.g., geojson, table, summary).",
    )
    include_confidence: bool = Field(
        False, description="Whether to include confidence scores when available."
    )


def require_api_key(
    x_api_key: str = Header(default="", alias="X-API-Key"),
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> None:
    expected = settings.api_key.strip()
    # In non-test environments, enforce that an API key is configured
    if settings.environment.lower() not in ("test", "testing"):
        if not expected:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API key not configured. Set API_KEY environment variable.",
            )
    if expected and x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )


def get_db_connection(settings: Settings = Depends(get_settings)):  # noqa: B008
    yield from db_connection_dependency(settings)


settings = get_settings()
configure_logging(settings.log_level)
logger = structlog.get_logger(__name__)
allowed_query_tables = {
    table.strip() for table in settings.allowed_query_tables.split(",") if table.strip()
} or {"data.features"}
rate_limiter = build_rate_limiter(
    enabled=settings.rate_limit_enabled,
    environment=settings.environment,
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
    max_identifiers=settings.rate_limit_max_identifiers,
    bucket_ttl_seconds=settings.rate_limit_bucket_ttl_seconds,
)


def get_rate_limiter():
    return rate_limiter


def _rate_limit_identifier(request: Request, x_api_key: str) -> str:
    raw_identifier = x_api_key.strip() if x_api_key else ""
    if not raw_identifier:
        client_host = request.client.host if request and request.client else "anonymous"
        raw_identifier = f"ip:{client_host}"
    trimmed = raw_identifier[:256]
    return hashlib.sha256(trimmed.encode("utf-8", errors="ignore")).hexdigest()


def enforce_rate_limit(
    request: Request,
    x_api_key: str = Header(default="", alias="X-API-Key"),
    limiter=Depends(get_rate_limiter),  # noqa: B008
) -> None:
    identifier = _rate_limit_identifier(request, x_api_key)
    try:
        limiter.check(identifier)
    except RateLimitExceeded as exc:
        logger.warning("rate_limit.exceeded", identifier=identifier)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.environment.lower() not in ("test", "testing"):
        initialize_pool(settings)
    try:
        yield
    finally:
        if settings.environment.lower() not in ("test", "testing"):
            release_pool()


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="GIS-OSS sandbox API",
    lifespan=lifespan,
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["system"])
def ready() -> dict[str, str]:
    if settings.environment.lower() in ("test", "testing"):
        return {"status": "ready"}
    try:
        with connection_context(settings) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
    except Exception as exc:
        logger.warning("ready.failed", error_type=type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not ready.",
        ) from exc
    return {"status": "ready"}


@app.post("/query", response_model=QueryResponse, tags=["query"])
def query(
    request: QueryRequest,
    _: None = Depends(require_api_key),  # noqa: B008
    __: None = Depends(enforce_rate_limit),  # noqa: B008
    ___: None = Depends(enforce_permission(Permission.QUERY_PUBLIC)),  # noqa: B008
    x_api_key: str = Header(default="", alias="X-API-Key"),
    conn: PGConnection = Depends(get_db_connection),  # noqa: B008
) -> QueryResponse:
    start_time = perf_counter()
    logger.info(
        "query.received",
        operation=request.operation,
        prompt_length=len(request.prompt),
        return_format=request.return_format,
    )

    if request.operation:
        try:
            result = _execute_structured_operation(request, conn)
        except ValueError as exc:
            _write_audit_log(
                conn=conn,
                request=request,
                x_api_key=x_api_key,
                status="invalid_parameters",
                started_at=start_time,
                error_message=str(exc),
            )
            logger.warning(
                "query.invalid_parameters",
                operation=request.operation,
                error=str(exc),
            )
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PsycopgError as exc:
            error_message = "Invalid geometry, CRS, or query parameters."
            _write_audit_log(
                conn=conn,
                request=request,
                x_api_key=x_api_key,
                status="db_error",
                started_at=start_time,
                error_message=error_message,
            )
            logger.warning(
                "query.db_error",
                operation=request.operation,
                error_type=type(exc).__name__,
            )
            raise HTTPException(
                status_code=400,
                detail=error_message,
            ) from exc

        _write_audit_log(
            conn=conn,
            request=request,
            x_api_key=x_api_key,
            status="completed",
            started_at=start_time,
        )
        logger.info("query.completed", operation=request.operation)
        return QueryResponse(
            status="completed",
            message="Structured operation executed successfully.",
            request=request,
            result=result,
        )

    _write_audit_log(
        conn=conn,
        request=request,
        x_api_key=x_api_key,
        status="pending",
        started_at=start_time,
    )
    logger.info("query.pending", reason="operation_not_provided")
    return QueryResponse(
        status="pending",
        message=(
            "LLM orchestration not yet implemented. "
            "Provide 'operation' for structured tool execution."
        ),
        request=request,
    )


@app.post("/query/natural", response_model=QueryResponse, tags=["query"])
def query_natural(
    request: NaturalQueryRequest,
    _: None = Depends(require_api_key),  # noqa: B008
    __: None = Depends(enforce_rate_limit),  # noqa: B008
    ___: None = Depends(enforce_permission(Permission.QUERY_PUBLIC)),  # noqa: B008
    x_api_key: str = Header(default="", alias="X-API-Key"),
    conn: PGConnection = Depends(get_db_connection),  # noqa: B008
) -> QueryResponse:
    start_time = perf_counter()
    logger.info("query_natural.received", prompt_length=len(request.prompt))

    try:
        parsed_fields = parse_natural_query_prompt(request.prompt)
    except NaturalQueryParseError as exc:
        parsed_request = QueryRequest.model_validate(
            {
                "prompt": request.prompt,
                "return_format": request.return_format,
                "include_confidence": request.include_confidence,
            }
        )
        _write_audit_log(
            conn=conn,
            request=parsed_request,
            x_api_key=x_api_key,
            status="parse_error",
            started_at=start_time,
            error_message=str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    structured_request = QueryRequest.model_validate(
        {
            "prompt": request.prompt,
            "return_format": request.return_format,
            "include_confidence": request.include_confidence,
            **parsed_fields,
        }
    )

    try:
        result = _execute_structured_operation(structured_request, conn)
    except ValueError as exc:
        _write_audit_log(
            conn=conn,
            request=structured_request,
            x_api_key=x_api_key,
            status="invalid_parameters",
            started_at=start_time,
            error_message=str(exc),
        )
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PsycopgError as exc:
        error_message = "Invalid geometry, CRS, or query parameters."
        _write_audit_log(
            conn=conn,
            request=structured_request,
            x_api_key=x_api_key,
            status="db_error",
            started_at=start_time,
            error_message=error_message,
        )
        raise HTTPException(status_code=400, detail=error_message) from exc

    _write_audit_log(
        conn=conn,
        request=structured_request,
        x_api_key=x_api_key,
        status="completed",
        started_at=start_time,
    )
    return QueryResponse(
        status="completed",
        message="Natural-language query parsed and executed successfully.",
        request=structured_request,
        result=result,
    )


def _query_data_sources(request: QueryRequest) -> list[str]:
    if request.operation and request.operation.lower() == "nearest_neighbors":
        table = request.table.strip()
        return [table] if table else []
    return []


def _audit_metadata(request: QueryRequest) -> dict[str, Any]:
    return {
        "operation": request.operation,
        "return_format": request.return_format,
        "include_confidence": request.include_confidence,
        "table": request.table,
        "limit": request.limit,
        "distance": request.distance,
        "units": request.units,
        "srid": request.srid,
        "from_epsg": request.from_epsg,
        "to_epsg": request.to_epsg,
        "geometry": request.geometry,
        "geometry_b": request.geometry_b,
    }


def _write_audit_log(
    *,
    conn: PGConnection,
    request: QueryRequest,
    x_api_key: str,
    status: str,
    started_at: float,
    error_message: str | None = None,
) -> None:
    if not settings.enable_audit_log:
        return

    try:
        duration_ms = max(int((perf_counter() - started_at) * 1000), 0)
        query_type = request.operation.lower() if request.operation else "nl_pending"
        log_query_event(
            conn,
            user_identifier=x_api_key,
            prompt=request.prompt,
            query_type=query_type,
            execution_time_ms=duration_ms,
            status=status,
            error_message=error_message,
            data_sources=_query_data_sources(request),
            metadata=_audit_metadata(request),
        )
    except Exception as exc:
        logger.warning("audit.log_failed", error_type=type(exc).__name__)


def _execute_structured_operation(
    request: QueryRequest, conn: PGConnection
) -> dict[str, Any]:
    assert request.operation is not None
    op = request.operation.lower()

    if op == "buffer":
        if request.geometry is None or request.distance is None:
            raise ValueError("Buffer requires 'geometry' and 'distance'.")
        units = request.units or "meters"
        buffered_geometry = buffer_geometry(
            conn,
            geom=request.geometry,
            distance=request.distance,
            units=units,
            srid=request.srid,
        )
        return {"geometry": buffered_geometry, "units": units}

    if op == "calculate_area":
        if request.geometry is None:
            raise ValueError("Area calculation requires 'geometry'.")
        units = request.units or "square_meters"
        area = calculate_area(
            conn,
            geom=request.geometry,
            units=units,
            srid=request.srid,
        )
        return {"area": area, "units": units}

    if op == "find_intersections":
        if request.geometry is None or request.geometry_b is None:
            raise ValueError(
                "Intersection requires both 'geometry' and 'geometry_b'."
            )
        intersection_geometry = find_intersections(
            conn,
            request.geometry,
            request.geometry_b,
            srid=request.srid,
        )
        return {"geometry": intersection_geometry}

    if op == "nearest_neighbors":
        if request.geometry is None:
            raise ValueError("Nearest neighbors requires 'geometry'.")
        table = request.table.strip()
        if table not in allowed_query_tables:
            allowed = ", ".join(sorted(allowed_query_tables))
            raise ValueError(
                f"Table '{table}' is not permitted. Allowed tables: {allowed}."
            )
        features = nearest_neighbors(
            conn,
            geom=request.geometry,
            table=table,
            limit=request.limit,
            srid=request.srid,
        )
        return {"features": features, "limit": request.limit}

    if op == "transform_crs":
        if (
            request.geometry is None
            or request.from_epsg is None
            or request.to_epsg is None
        ):
            raise ValueError(
                "CRS transformation requires 'geometry', 'from_epsg', and 'to_epsg'."
            )
        geometry = transform_crs(
            conn,
            geom=request.geometry,
            from_epsg=request.from_epsg,
            to_epsg=request.to_epsg,
        )
        return {"geometry": geometry}

    raise ValueError(f"Unsupported operation '{request.operation}'.")
