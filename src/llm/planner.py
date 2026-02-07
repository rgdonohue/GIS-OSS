from __future__ import annotations

from typing import Any

from src.nl.strict_parser import NaturalQueryParseError, validate_structured_operation_payload

from .provider import (
    LLMPlannerInputError,
    LLMPlannerOutputError,
    LLMPlannerUnavailableError,
    PlannerProvider,
    build_provider,
)

_ALLOWED_PROMPT_CONTROL_CHARS = {"\n", "\t", "\r"}

_PLANNER_SYSTEM_PROMPT = """You are a strict GIS operation planner.
Return exactly one JSON object and no additional text.
Allowed keys: operation, geometry, geometry_b, table, limit, distance, units, srid, from_epsg, to_epsg.
Allowed operations: buffer, calculate_area, find_intersections, nearest_neighbors, transform_crs.
Never invent unavailable fields; use only values supported by the user request.
"""


def _sanitize_prompt(raw_prompt: str, *, max_chars: int) -> str:
    prompt = raw_prompt.strip()
    if not prompt:
        raise LLMPlannerInputError("Prompt is empty.")
    if len(prompt) > max_chars:
        raise LLMPlannerInputError(
            f"Prompt exceeds max length of {max_chars} characters."
        )

    for char in prompt:
        if ord(char) < 32 and char not in _ALLOWED_PROMPT_CONTROL_CHARS:
            raise LLMPlannerInputError("Prompt contains unsupported control characters.")

    return prompt


def _compose_planner_prompt(prompt: str) -> str:
    return f"{_PLANNER_SYSTEM_PROMPT}\nUser request:\n{prompt}\nJSON:"


def plan_operation_from_prompt(
    *,
    prompt: str,
    settings: Any,
    provider: PlannerProvider | None = None,
) -> dict[str, Any]:
    sanitized_prompt = _sanitize_prompt(
        prompt,
        max_chars=int(getattr(settings, "llm_prompt_max_chars", 4000)),
    )
    planner_provider = provider or build_provider(settings)

    try:
        candidate = planner_provider.generate_structured_operation(
            prompt=_compose_planner_prompt(sanitized_prompt)
        )
    except LLMPlannerUnavailableError:
        raise
    except LLMPlannerOutputError:
        raise
    except Exception as exc:
        raise LLMPlannerOutputError("LLM planner call failed.") from exc

    try:
        return validate_structured_operation_payload(candidate)
    except NaturalQueryParseError as exc:
        raise LLMPlannerOutputError(str(exc)) from exc
