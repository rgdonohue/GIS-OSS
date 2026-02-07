from __future__ import annotations

import json
import time
from typing import Any

import httpx

from .provider import LLMPlannerOutputError, LLMPlannerUnavailableError


class OllamaPlannerClient:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        timeout_seconds: float,
        max_retries: int,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._max_retries = max(max_retries, 0)

    def _payload(self, prompt: str) -> dict[str, Any]:
        return {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
            },
        }

    def generate_structured_operation(self, *, prompt: str) -> dict[str, Any]:
        payload = self._payload(prompt)
        delay_seconds = 0.2
        attempts = self._max_retries + 1

        for attempt in range(attempts):
            try:
                with httpx.Client(base_url=self._base_url, timeout=self._timeout_seconds) as client:
                    response = client.post("/api/generate", json=payload)
                    response.raise_for_status()
                    data = response.json()

                raw_response = data.get("response")
                if not isinstance(raw_response, str):
                    raise LLMPlannerOutputError("Ollama response missing string field 'response'.")

                parsed = json.loads(raw_response)
                if not isinstance(parsed, dict):
                    raise LLMPlannerOutputError("LLM output must be a JSON object.")

                return parsed
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                if attempt >= attempts - 1:
                    raise LLMPlannerUnavailableError("LLM provider unavailable.") from exc
                time.sleep(delay_seconds)
                delay_seconds *= 2
            except json.JSONDecodeError as exc:
                raise LLMPlannerOutputError("LLM output is not valid JSON.") from exc

        raise LLMPlannerUnavailableError("LLM provider unavailable.")
