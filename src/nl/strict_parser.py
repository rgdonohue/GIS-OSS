from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator

from src.spatial.postgis_ops import AREA_FROM_SQ_METERS, DISTANCE_TO_METERS

ALLOWED_OPERATIONS = {
    "buffer",
    "calculate_area",
    "find_intersections",
    "nearest_neighbors",
    "transform_crs",
}


class NaturalQueryParseError(ValueError):
    """Raised when a natural-language prompt cannot be parsed safely."""


class StructuredOperationCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: str
    geometry: dict[str, Any] | None = None
    geometry_b: dict[str, Any] | None = None
    table: str | None = None
    limit: int | None = None
    distance: float | None = None
    units: str | None = None
    srid: int | None = None
    from_epsg: int | None = None
    to_epsg: int | None = None

    @field_validator("operation")
    @classmethod
    def _validate_operation(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_OPERATIONS:
            allowed = ", ".join(sorted(ALLOWED_OPERATIONS))
            raise ValueError(f"Unsupported operation '{value}'. Allowed: {allowed}.")
        return normalized

    @field_validator("units")
    @classmethod
    def _normalize_units(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().lower()

    @field_validator("table")
    @classmethod
    def _normalize_table(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def _validate_requirements(self) -> StructuredOperationCandidate:
        op = self.operation

        if op == "buffer":
            if self.geometry is None or self.distance is None:
                raise ValueError("Buffer requires 'geometry' and 'distance'.")
            if self.units is not None and self.units not in DISTANCE_TO_METERS:
                raise ValueError(f"Unsupported distance unit '{self.units}'.")

        if op == "calculate_area":
            if self.geometry is None:
                raise ValueError("Area calculation requires 'geometry'.")
            if self.units is not None and self.units not in AREA_FROM_SQ_METERS:
                raise ValueError(f"Unsupported area unit '{self.units}'.")

        if op == "find_intersections":
            if self.geometry is None or self.geometry_b is None:
                raise ValueError("Intersection requires both 'geometry' and 'geometry_b'.")

        if op == "nearest_neighbors":
            if self.geometry is None:
                raise ValueError("Nearest neighbors requires 'geometry'.")
            if self.limit is not None and self.limit <= 0:
                raise ValueError("Nearest neighbors requires 'limit' > 0.")

        if op == "transform_crs":
            if self.geometry is None or self.from_epsg is None or self.to_epsg is None:
                raise ValueError(
                    "CRS transformation requires 'geometry', 'from_epsg', and 'to_epsg'."
                )

        return self


def _extract_json_objects(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    found: list[dict[str, Any]] = []
    index = 0
    while index < len(text):
        if text[index] != "{":
            index += 1
            continue
        try:
            parsed, consumed = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            index += 1
            continue
        if isinstance(parsed, dict):
            found.append(parsed)
        index += consumed
    return found


def _format_validation_error(exc: ValidationError) -> str:
    messages = []
    for issue in exc.errors():
        field = ".".join(str(part) for part in issue.get("loc", ()))
        detail = issue.get("msg", "invalid value")
        if field:
            messages.append(f"{field}: {detail}")
        else:
            messages.append(detail)
    return "; ".join(messages)


def parse_natural_query_prompt(prompt: str) -> dict[str, Any]:
    """
    Parse a natural-language prompt by extracting exactly one JSON operation object.

    To avoid guesswork, this parser refuses to infer parameters from prose. The
    prompt must include one JSON object with an `operation` key and required fields.
    """

    candidates = [obj for obj in _extract_json_objects(prompt) if "operation" in obj]
    if not candidates:
        raise NaturalQueryParseError(
            "Could not parse a structured operation JSON object from prompt. "
            "Embed exactly one JSON object with 'operation' and required fields."
        )
    if len(candidates) > 1:
        raise NaturalQueryParseError(
            "Multiple operation JSON objects found in prompt. "
            "Provide exactly one operation object."
        )

    try:
        candidate = StructuredOperationCandidate.model_validate(candidates[0])
    except ValidationError as exc:
        raise NaturalQueryParseError(_format_validation_error(exc)) from exc

    return candidate.model_dump(exclude_none=True)
