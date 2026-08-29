from __future__ import annotations

import hashlib
import math
import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import JSONResponse

from backend.phase2 import app


@dataclass(frozen=True)
class LimitDecision:
    allowed: bool
    remaining: int
    retry_after: int


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int, window_seconds: int, now: float | None = None) -> LimitDecision:
        if limit <= 0 or window_seconds <= 0:
            return LimitDecision(True, 0, 0)
        current = time.monotonic() if now is None else now
        cutoff = current - window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry = max(1, math.ceil(window_seconds - (current - events[0])))
                return LimitDecision(False, 0, retry)
            events.append(current)
            return LimitDecision(True, max(0, limit - len(events)), 0)

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


limiter = SlidingWindowLimiter()


def reset_rate_limiter() -> None:
    limiter.reset()


def _int_env(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def _subject(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    if authorization:
        return f"auth:{_fingerprint(authorization)}"
    webhook = request.headers.get("X-SEVAA-Webhook-Token", "")
    if webhook:
        return f"webhook:{_fingerprint(webhook)}"
    client_host = request.client.host if request.client else "unknown"
    return f"ip:{client_host}"


def _policy(path: str) -> tuple[str, int, int] | None:
    if not path.startswith("/api/v2/"):
        return None
    window = _int_env("SEVAA_RATE_LIMIT_WINDOW_SECONDS", 60)
    if path.startswith("/api/v2/webhooks/"):
        return "webhook", _int_env("SEVAA_RATE_LIMIT_WEBHOOK_PER_WINDOW", 30), window
    return "service", _int_env("SEVAA_RATE_LIMIT_SERVICE_PER_WINDOW", 300), window


@app.middleware("http")
async def enforce_rate_limits(request: Request, call_next):
    policy = _policy(request.url.path)
    if policy is None:
        return await call_next(request)

    bucket, limit, window = policy
    key = f"{bucket}:{_subject(request)}"
    decision = limiter.check(key, limit, window)
    headers = {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(decision.remaining),
    }
    if not decision.allowed:
        headers["Retry-After"] = str(decision.retry_after)
        return JSONResponse(
            status_code=429,
            content={"detail": "rate limit exceeded"},
            headers=headers,
        )

    response = await call_next(request)
    response.headers.update(headers)
    return response


__all__ = ["LimitDecision", "SlidingWindowLimiter", "reset_rate_limiter"]
