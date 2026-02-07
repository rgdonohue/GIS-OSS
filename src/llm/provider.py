from __future__ import annotations

from typing import Any, Protocol


class LLMPlannerError(RuntimeError):
    """Base class for LLM planner failures."""


class LLMPlannerInputError(LLMPlannerError):
    """Raised when user input fails local validation before model invocation."""


class LLMPlannerUnavailableError(LLMPlannerError):
    """Raised when the configured model provider cannot be reached."""


class LLMPlannerOutputError(LLMPlannerError):
    """Raised when model output is malformed or cannot be validated."""


class PlannerProvider(Protocol):
    def generate_structured_operation(self, *, prompt: str) -> dict[str, Any]:
        """Return one structured operation candidate as a dictionary."""


def build_provider(settings: Any) -> PlannerProvider:
    provider_name = str(getattr(settings, "llm_provider", "ollama")).strip().lower()

    if provider_name == "ollama":
        from .ollama_client import OllamaPlannerClient

        return OllamaPlannerClient(
            base_url=str(getattr(settings, "llm_ollama_base_url", "http://localhost:11434")),
            model=str(getattr(settings, "llm_model", "qwen2.5:7b-instruct")),
            timeout_seconds=float(getattr(settings, "llm_timeout_seconds", 20)),
            max_retries=int(getattr(settings, "llm_max_retries", 1)),
        )

    raise LLMPlannerUnavailableError(
        f"Unsupported llm_provider '{provider_name}'. Supported: ollama."
    )
