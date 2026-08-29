from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class PaymentProviderError(RuntimeError):
    """Raised when the configured payment provider cannot complete a request."""


@dataclass(frozen=True)
class RazorpayConfig:
    key_id: str
    key_secret: str
    webhook_secret: str


def get_razorpay_config() -> RazorpayConfig | None:
    key_id = os.getenv("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "").strip()
    if not key_id or not key_secret:
        return None
    return RazorpayConfig(key_id=key_id, key_secret=key_secret, webhook_secret=webhook_secret)


def _auth_header(config: RazorpayConfig) -> str:
    raw = f"{config.key_id}:{config.key_secret}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def _request_json(method: str, path: str, config: RazorpayConfig, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.razorpay.com{path}",
        data=body,
        method=method,
        headers={
            "Authorization": _auth_header(config),
            "Content-Type": "application/json",
            "User-Agent": "sevaa-sales-os/0.2",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise PaymentProviderError(f"Razorpay HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise PaymentProviderError(f"Razorpay request failed: {type(exc).__name__}") from exc


def create_payment_link(
    *,
    amount_rupees: int,
    reference_id: str,
    description: str,
    customer_name: str | None,
    customer_email: str | None,
    customer_phone: str | None,
) -> dict[str, Any]:
    config = get_razorpay_config()
    if config is None:
        raise PaymentProviderError("Razorpay credentials are not configured")
    customer = {
        key: value
        for key, value in {
            "name": customer_name,
            "email": customer_email,
            "contact": customer_phone,
        }.items()
        if value
    }
    payload: dict[str, Any] = {
        "amount": int(amount_rupees) * 100,
        "currency": "INR",
        "reference_id": reference_id[:40],
        "description": description[:2048],
        "notify": {"sms": False, "email": False},
        "reminder_enable": False,
        "notes": {"source": "sevaa-sales-os"},
    }
    if customer:
        payload["customer"] = customer
    return _request_json("POST", "/v1/payment_links", config, payload)


def fetch_payment_link(provider_payment_link_id: str) -> dict[str, Any]:
    config = get_razorpay_config()
    if config is None:
        raise PaymentProviderError("Razorpay credentials are not configured")
    safe_id = provider_payment_link_id.strip()
    if not safe_id.startswith("plink_"):
        raise PaymentProviderError("invalid Razorpay payment-link id")
    return _request_json("GET", f"/v1/payment_links/{safe_id}", config)


def verify_webhook_signature(raw_body: bytes, signature: str | None) -> bool:
    config = get_razorpay_config()
    if config is None or not config.webhook_secret or not signature:
        return False
    expected = hmac.new(
        config.webhook_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature.strip())
