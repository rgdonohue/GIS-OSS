from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.llm.planner import plan_operation_from_prompt
from src.llm.provider import (
    LLMPlannerInputError,
    LLMPlannerOutputError,
    LLMPlannerUnavailableError,
)


@dataclass
class _Settings:
    llm_prompt_max_chars: int = 4000


class _FakeProvider:
    def __init__(self, payload):
        self.payload = payload

    def generate_structured_operation(self, *, prompt: str):
        assert "Return exactly one JSON object" in prompt
        return self.payload


class _UnavailableProvider:
    def generate_structured_operation(self, *, prompt: str):
        raise LLMPlannerUnavailableError("unreachable")


def test_plan_operation_from_prompt_validates_and_normalizes_payload():
    planned = plan_operation_from_prompt(
        prompt="Find the area of this polygon",
        settings=_Settings(),
        provider=_FakeProvider(
            {
                "operation": "calculate_area",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]],
                },
                "units": "Acres",
            }
        ),
    )

    assert planned["operation"] == "calculate_area"
    assert planned["units"] == "acres"


def test_plan_operation_from_prompt_rejects_empty_prompt():
    with pytest.raises(LLMPlannerInputError):
        plan_operation_from_prompt(
            prompt="   ",
            settings=_Settings(),
            provider=_FakeProvider({"operation": "buffer"}),
        )


def test_plan_operation_from_prompt_rejects_control_chars():
    with pytest.raises(LLMPlannerInputError):
        plan_operation_from_prompt(
            prompt="Find parks\x00",
            settings=_Settings(),
            provider=_FakeProvider({"operation": "buffer"}),
        )


def test_plan_operation_from_prompt_surfaces_output_validation_errors():
    with pytest.raises(LLMPlannerOutputError):
        plan_operation_from_prompt(
            prompt="Find nearby parks",
            settings=_Settings(),
            provider=_FakeProvider({"operation": "dissolve"}),
        )


def test_plan_operation_from_prompt_surfaces_provider_unavailable():
    with pytest.raises(LLMPlannerUnavailableError):
        plan_operation_from_prompt(
            prompt="Find nearby parks",
            settings=_Settings(),
            provider=_UnavailableProvider(),
        )
