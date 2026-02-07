from __future__ import annotations

import json

import httpx
import pytest

from src.llm.ollama_client import OllamaPlannerClient
from src.llm.provider import LLMPlannerOutputError, LLMPlannerUnavailableError


class _FakeResponse:
    def __init__(self, *, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "http://localhost/api/generate")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError("error", request=request, response=response)

    def json(self) -> dict:
        return self._payload


class _ClientFactory:
    def __init__(self, sequence):
        self.sequence = list(sequence)

    def __call__(self, *args, **kwargs):
        outer = self

        class _FakeClient:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def post(self, path: str, json: dict):
                next_item = outer.sequence.pop(0)
                if isinstance(next_item, Exception):
                    raise next_item
                assert path == "/api/generate"
                assert json["format"] == "json"
                return next_item

        return _FakeClient()


def test_ollama_client_returns_parsed_json_object(monkeypatch):
    payload = {"operation": "buffer", "distance": 10}
    factory = _ClientFactory(
        [_FakeResponse(status_code=200, payload={"response": json.dumps(payload)})]
    )
    monkeypatch.setattr("src.llm.ollama_client.httpx.Client", factory)

    client = OllamaPlannerClient(
        base_url="http://localhost:11434",
        model="qwen2.5:7b-instruct",
        timeout_seconds=10,
        max_retries=0,
    )
    result = client.generate_structured_operation(prompt="buffer point")

    assert result == payload


def test_ollama_client_retries_then_raises_unavailable(monkeypatch):
    connect_error = httpx.ConnectError(
        "connect failed",
        request=httpx.Request("POST", "http://localhost/api/generate"),
    )
    factory = _ClientFactory([connect_error, connect_error])
    monkeypatch.setattr("src.llm.ollama_client.httpx.Client", factory)
    monkeypatch.setattr("src.llm.ollama_client.time.sleep", lambda _: None)

    client = OllamaPlannerClient(
        base_url="http://localhost:11434",
        model="qwen2.5:7b-instruct",
        timeout_seconds=10,
        max_retries=1,
    )

    with pytest.raises(LLMPlannerUnavailableError):
        client.generate_structured_operation(prompt="buffer point")


def test_ollama_client_rejects_non_json_output(monkeypatch):
    factory = _ClientFactory([_FakeResponse(status_code=200, payload={"response": "not-json"})])
    monkeypatch.setattr("src.llm.ollama_client.httpx.Client", factory)

    client = OllamaPlannerClient(
        base_url="http://localhost:11434",
        model="qwen2.5:7b-instruct",
        timeout_seconds=10,
        max_retries=0,
    )

    with pytest.raises(LLMPlannerOutputError):
        client.generate_structured_operation(prompt="buffer point")
