"""
Lightweight, in-memory rate limiter scaffold.

This keeps the surface area small (no external dependencies) while giving us
a predictable hook we can swap for Redis/Redis-JSON or an API gateway later.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict


class RateLimitExceeded(Exception):
    """Raised when a caller exceeds the configured rate limit."""


class NoOpRateLimiter:
    """A placeholder limiter that never blocks."""

    def check(self, identifier: str) -> None:
        return


class RateLimiter:
    """
    Token-bucket rate limiter keyed by caller identifier (API key or IP).

    Parameters:
    - max_requests: tokens refilled per window
    - window_seconds: time window for full refill
    - burst: optional burst capacity; defaults to max_requests
    - max_identifiers: cap on tracked caller keys to bound memory use
    - bucket_ttl_seconds: idle time before old caller buckets are evicted
    """

    def __init__(
        self,
        max_requests: int,
        window_seconds: int,
        burst: int | None = None,
        max_identifiers: int = 10_000,
        bucket_ttl_seconds: int = 3_600,
    ) -> None:
        if max_requests <= 0 or window_seconds <= 0:
            raise ValueError("Rate limiter requires positive max_requests and window_seconds.")
        if max_identifiers <= 0 or bucket_ttl_seconds <= 0:
            raise ValueError("Rate limiter requires positive max_identifiers and bucket_ttl_seconds.")

        capacity = burst if burst is not None else max_requests
        self.capacity = float(capacity)
        self.refill_rate = float(max_requests) / float(window_seconds)
        self.max_identifiers = max_identifiers
        self.bucket_ttl_seconds = float(bucket_ttl_seconds)
        self._buckets: OrderedDict[str, dict[str, float]] = OrderedDict()
        self._lock = threading.Lock()

    def _refill(self, bucket: dict[str, float], now: float) -> None:
        elapsed = now - bucket["updated"]
        if elapsed <= 0:
            return
        bucket["tokens"] = min(self.capacity, bucket["tokens"] + elapsed * self.refill_rate)
        bucket["updated"] = now

    def _evict_stale(self, now: float) -> None:
        stale_keys = [
            key
            for key, bucket in self._buckets.items()
            if now - bucket["updated"] >= self.bucket_ttl_seconds
        ]
        for key in stale_keys:
            self._buckets.pop(key, None)

    def check(self, identifier: str) -> None:
        """
        Consume one token for the given identifier or raise RateLimitExceeded.
        """

        now = time.monotonic()
        with self._lock:
            self._evict_stale(now)

            bucket = self._buckets.get(identifier)
            if bucket is None:
                if len(self._buckets) >= self.max_identifiers:
                    # Evict least-recently used identifier to bound memory.
                    self._buckets.popitem(last=False)
                bucket = {"tokens": self.capacity, "updated": now}

            self._refill(bucket, now)
            if bucket["tokens"] < 1.0:
                raise RateLimitExceeded("Rate limit exceeded.")
            bucket["tokens"] -= 1.0
            self._buckets[identifier] = bucket
            self._buckets.move_to_end(identifier)


def build_rate_limiter(
    enabled: bool,
    environment: str,
    max_requests: int,
    window_seconds: int,
    max_identifiers: int,
    bucket_ttl_seconds: int,
) -> RateLimiter | NoOpRateLimiter:
    """
    Construct an appropriate limiter instance for the running environment.
    """

    if not enabled or environment.lower() in ("test", "testing"):
        return NoOpRateLimiter()
    return RateLimiter(
        max_requests=max_requests,
        window_seconds=window_seconds,
        max_identifiers=max_identifiers,
        bucket_ttl_seconds=bucket_ttl_seconds,
    )
