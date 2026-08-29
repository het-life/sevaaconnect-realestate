from __future__ import annotations

import os

from fastapi import Request
from fastapi.responses import JSONResponse

from backend.phase2 import app


def hardened_auth_configured() -> bool:
    return bool(os.getenv("SEVAA_FOUNDER_TOKEN") or os.getenv("SEVAA_AUTOMATION_TOKEN"))


@app.middleware("http")
async def block_legacy_v1_when_hardened(request: Request, call_next):
    path = request.url.path
    is_legacy_api = path.startswith("/api/") and not path.startswith("/api/v2/")
    public_health = path == "/api/health"
    allow_legacy = os.getenv("SEVAA_ALLOW_LEGACY_V1") == "1"

    if is_legacy_api and not public_health and hardened_auth_configured() and not allow_legacy:
        return JSONResponse(
            status_code=410,
            content={
                "detail": {
                    "code": "legacy_v1_disabled",
                    "message": "Legacy unauthenticated API is disabled when hardened auth is configured. Use /api/v2 endpoints.",
                }
            },
            headers={"Deprecation": "true"},
        )
    return await call_next(request)
