from __future__ import annotations

from typing import Any

_TRACING_CONFIGURED = False


def configure_tracing(settings: Any) -> bool:
    """
    Configure OpenTelemetry tracing if enabled and dependencies are installed.
    """

    global _TRACING_CONFIGURED
    if _TRACING_CONFIGURED:
        return True
    if not bool(getattr(settings, "otel_enabled", False)):
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    except Exception:
        return False

    service_name = getattr(settings, "otel_service_name", "") or getattr(
        settings, "app_name", "gis-oss-api"
    )
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _TRACING_CONFIGURED = True
    return True


def instrument_fastapi_app(app: Any, settings: Any) -> bool:
    """
    Instrument a FastAPI app when tracing is enabled and dependencies exist.
    """

    if not bool(getattr(settings, "otel_enabled", False)):
        return False

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except Exception:
        return False

    FastAPIInstrumentor.instrument_app(app)
    return True


def current_trace_id() -> str | None:
    """
    Return the active trace id as 32-char hex when available.
    """

    try:
        from opentelemetry import trace
    except Exception:
        return None

    span = trace.get_current_span()
    if span is None:
        return None
    context = span.get_span_context()
    if context is None or not getattr(context, "is_valid", False):
        return None
    return f"{context.trace_id:032x}"
