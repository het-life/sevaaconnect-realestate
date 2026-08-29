import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEST_DB = Path(__file__).with_name("test_rate_limit.db")
os.environ["SEVAA_DB_PATH"] = str(TEST_DB)

from fastapi.testclient import TestClient

import backend.app as base
from backend.runtime import app
from backend.rate_limit import SlidingWindowLimiter, reset_rate_limiter


def setup_function():
    base.DB_PATH = TEST_DB
    os.environ["SEVAA_FOUNDER_TOKEN"] = "founder-rate-test"
    os.environ["SEVAA_AUTOMATION_TOKEN"] = "automation-rate-test"
    os.environ.pop("SEVAA_WEBHOOK_TOKEN", None)
    os.environ.pop("SEVAA_ALLOW_LEGACY_V1", None)
    os.environ.pop("SEVAA_RATE_LIMIT_WINDOW_SECONDS", None)
    os.environ.pop("SEVAA_RATE_LIMIT_WEBHOOK_PER_WINDOW", None)
    os.environ.pop("SEVAA_RATE_LIMIT_SERVICE_PER_WINDOW", None)
    reset_rate_limiter()
    if TEST_DB.exists():
        TEST_DB.unlink()


def test_sliding_window_blocks_then_recovers():
    limiter = SlidingWindowLimiter()
    assert limiter.check("a", limit=2, window_seconds=10, now=0).allowed
    assert limiter.check("a", limit=2, window_seconds=10, now=1).allowed
    blocked = limiter.check("a", limit=2, window_seconds=10, now=2)
    assert blocked.allowed is False
    assert blocked.retry_after == 8
    recovered = limiter.check("a", limit=2, window_seconds=10, now=11)
    assert recovered.allowed is True


def test_authenticated_v2_requests_return_429_after_limit():
    os.environ["SEVAA_RATE_LIMIT_SERVICE_PER_WINDOW"] = "2"
    os.environ["SEVAA_RATE_LIMIT_WINDOW_SECONDS"] = "60"
    reset_rate_limiter()
    headers = {
        "Authorization": "Bearer automation-rate-test",
        "X-Actor": "rate-limit-test",
    }

    try:
        with TestClient(app) as client:
            first = client.get("/api/v2/auth/me", headers=headers)
            second = client.get("/api/v2/auth/me", headers=headers)
            third = client.get("/api/v2/auth/me", headers=headers)

        assert first.status_code == 200
        assert second.status_code == 200
        assert third.status_code == 429
        assert third.headers["retry-after"]
        assert third.headers["x-ratelimit-limit"] == "2"
    finally:
        os.environ.pop("SEVAA_RATE_LIMIT_SERVICE_PER_WINDOW", None)
        os.environ.pop("SEVAA_RATE_LIMIT_WINDOW_SECONDS", None)
        reset_rate_limiter()
