from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from psycopg2.extensions import connection as PGConnection
from pydantic import BaseModel, Field

from src.db.session import db_connection_dependency, initialize_pool, release_pool
from src.logging_config import configure_logging
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
    limit: int = Field(default=5, description="Number of results to return.")
    distance: float | None = Field(
        None, description="Distance for buffer or nearest-neighbor operations."
    )
    units: str | None = Field(
        None, description="Units for distance/area (default meters)."
    )
    srid: int = Field(
        default=4326, description="SRID of provided GeoJSON geometry."
    )
    from_epsg: int | None = Field(
        None, description="Source EPSG for CRS transformations."
    )
    to_epsg: int | None = Field(
        None, description="Target EPSG for CRS transformations."
    )


class QueryResponse(BaseModel):
    status: str
    message: str
    request: QueryRequest
    result: Any | None = None


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
rate_limiter = build_rate_limiter(
    enabled=settings.rate_limit_enabled,
    environment=settings.environment,
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)


def get_rate_limiter():
    return rate_limiter


def enforce_rate_limit(
    request: Request,
    x_api_key: str = Header(default="", alias="X-API-Key"),
    limiter=Depends(get_rate_limiter),  # noqa: B008
) -> None:
    identifier = x_api_key.strip() if x_api_key else ""
    if not identifier:
        client_host = request.client.host if request and request.client else "anonymous"
        identifier = f"ip:{client_host}"
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
    return {"status": "ready"}


@app.post("/query", response_model=QueryResponse, tags=["query"])
def query(
    request: QueryRequest,
    __: None = Depends(enforce_rate_limit),  # noqa: B008
    _: None = Depends(require_api_key),  # noqa: B008
    ___: None = Depends(enforce_permission(Permission.QUERY_PUBLIC)),  # noqa: B008
    conn: PGConnection = Depends(get_db_connection),  # noqa: B008
) -> QueryResponse:
    logger.info(
        "query.received",
        operation=request.operation,
        prompt=request.prompt,
        return_format=request.return_format,
    )

    if request.operation:
        try:
            result = _execute_structured_operation(request, conn)
        except ValueError as exc:
            logger.warning(
                "query.invalid_parameters",
                operation=request.operation,
                error=str(exc),
            )
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        logger.info("query.completed", operation=request.operation)
        return QueryResponse(
            status="completed",
            message="Structured operation executed successfully.",
            request=request,
            result=result,
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
        limit = max(1, request.limit)
        features = nearest_neighbors(
            conn,
            geom=request.geometry,
            table=request.table,
            limit=limit,
            srid=request.srid,
        )
        return {"features": features, "limit": limit}

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
