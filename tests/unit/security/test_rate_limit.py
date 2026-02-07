from __future__ import annotations

import pytest

from src.security.rate_limit import (
    NoOpRateLimiter,
    RateLimiter,
    RateLimitExceeded,
    build_rate_limiter,
)


def test_rate_limiter_blocks_when_tokens_exhausted():
    limiter = RateLimiter(max_requests=1, window_seconds=60)

    limiter.check("user-1")
    with pytest.raises(RateLimitExceeded):
        limiter.check("user-1")


def test_rate_limiter_evicts_lru_when_identifier_cap_reached(monkeypatch):
    now = 1_000.0

    def fake_monotonic() -> float:
        return now

    monkeypatch.setattr("src.security.rate_limit.time.monotonic", fake_monotonic)
    limiter = RateLimiter(
        max_requests=10,
        window_seconds=60,
        max_identifiers=2,
        bucket_ttl_seconds=3_600,
    )

    limiter.check("a")
    now += 1
    limiter.check("b")
    now += 1
    limiter.check("c")

    assert "a" not in limiter._buckets
    assert "b" in limiter._buckets
    assert "c" in limiter._buckets


def test_rate_limiter_evicts_stale_buckets(monkeypatch):
    now = 2_000.0

    def fake_monotonic() -> float:
        return now

    monkeypatch.setattr("src.security.rate_limit.time.monotonic", fake_monotonic)
    limiter = RateLimiter(
        max_requests=10,
        window_seconds=60,
        max_identifiers=2,
        bucket_ttl_seconds=5,
    )

    limiter.check("stale-user")
    now += 10
    limiter.check("fresh-user")

    assert "stale-user" not in limiter._buckets
    assert "fresh-user" in limiter._buckets


def test_build_rate_limiter_returns_noop_for_test_env():
    limiter = build_rate_limiter(
        enabled=True,
        environment="test",
        max_requests=60,
        window_seconds=60,
        max_identifiers=10_000,
        bucket_ttl_seconds=3_600,
    )

    assert isinstance(limiter, NoOpRateLimiter)
