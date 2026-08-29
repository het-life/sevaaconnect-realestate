from __future__ import annotations

import os
import secrets

from fastapi import Header, HTTPException

from backend.phase2 import ActorContext, LeadCreateV2, app, create_lead_v2


def require_webhook_secret(value: str | None) -> None:
    configured = os.getenv("SEVAA_WEBHOOK_TOKEN")
    if not configured:
        raise HTTPException(503, "inbound webhooks are disabled")
    if not value or not secrets.compare_digest(value, configured):
        raise HTTPException(401, "invalid webhook token")


@app.post("/api/v2/webhooks/leads/{source}", status_code=201)
def ingest_lead_webhook(
    source: str,
    payload: LeadCreateV2,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    webhook_token: str | None = Header(default=None, alias="X-SEVAA-Webhook-Token"),
):
    require_webhook_secret(webhook_token)
    source = source.strip().lower()
    if not source or len(source) > 50 or not all(c.isalnum() or c in "-_" for c in source):
        raise HTTPException(400, "invalid webhook source")
    if not idempotency_key or len(idempotency_key) > 200:
        raise HTTPException(400, "Idempotency-Key is required")

    normalized = payload.model_copy(update={"source": f"webhook:{source}"})
    actor = ActorContext(actor_id=f"webhook:{source}", role="automation", auth_mode="token")
    return create_lead_v2(normalized, idempotency_key=idempotency_key, actor=actor)
