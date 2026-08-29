import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEST_DB = Path(__file__).with_name("test_public_enquiry.db")
os.environ["SEVAA_DB_PATH"] = str(TEST_DB)

from fastapi.testclient import TestClient

import backend.app as base
from backend.runtime import app
from backend.rate_limit import reset_rate_limiter


def setup_function():
    base.DB_PATH = TEST_DB
    os.environ["SEVAA_FOUNDER_TOKEN"] = "founder-public-test"
    os.environ["SEVAA_AUTOMATION_TOKEN"] = "automation-public-test"
    os.environ.pop("SEVAA_WEBHOOK_TOKEN", None)
    os.environ.pop("SEVAA_ALLOW_LEGACY_V1", None)
    os.environ.pop("SEVAA_PUBLIC_CONTACT_EMAIL", None)
    reset_rate_limiter()
    if TEST_DB.exists():
        TEST_DB.unlink()


def enquiry(**overrides):
    payload = {
        "name": "Public Buyer",
        "company": "Public Co",
        "phone": "+91 99999 11111",
        "email": "public@example.com",
        "city": "Surat",
        "requirement": "20ft modular sales office",
        "budget_min": 600000,
        "timeline_days": 45,
        "privacy_acknowledged": True,
    }
    payload.update(overrides)
    return payload


def test_public_quote_accepts_lead_with_hardened_auth_enabled():
    automation = {
        "Authorization": "Bearer automation-public-test",
        "X-Actor": "public-enquiry-test",
    }
    with TestClient(app) as client:
        page = client.get("/quote")
        assert page.status_code == 200
        assert "Request a project quote" in page.text
        assert 'href="/privacy"' in page.text
        assert 'name="privacy_acknowledged"' in page.text
        assert "SEVAA_AUTOMATION_TOKEN" not in page.text

        privacy = client.get("/privacy")
        assert privacy.status_code == 200
        assert "Quote enquiry privacy notice" in privacy.text
        assert "Information you choose to provide" in privacy.text
        assert "consent-withdrawal" in privacy.text

        created = client.post(
            "/api/v2/public/enquiries",
            json=enquiry(),
            headers={"Idempotency-Key": "public-enquiry-1"},
        )
        assert created.status_code == 202
        assert created.json()["accepted"] is True
        assert created.json()["reference"].startswith("L")

        replay = client.post(
            "/api/v2/public/enquiries",
            json=enquiry(),
            headers={"Idempotency-Key": "public-enquiry-1"},
        )
        assert replay.status_code == 202
        assert replay.json()["idempotent_replay"] is True

        dashboard = client.get("/api/v2/dashboard", headers=automation)
        assert dashboard.status_code == 200
        leads = [lead for stage in dashboard.json()["stages"].values() for lead in stage]
        matches = [lead for lead in leads if lead["email"] == "public@example.com"]
        assert len(matches) == 1
        assert matches[0]["source"] == "public-quote"\n\n        with base.db() as conn:\n            events = conn.execute(\n                "SELECT event_type,detail,actor FROM audit_events WHERE lead_id=? ORDER BY id",\n                (matches[0]["id"],),\n            ).fetchall()\n        privacy_events = [event for event in events if event["event_type"] == "privacy.notice_acknowledged"]\n        assert len(privacy_events) == 1\n        assert "version=2026-08-30" in privacy_events[0]["detail"]\n        assert privacy_events[0]["actor"] == "public-quote"


def test_public_enquiry_rejects_missing_privacy_acknowledgement():
    with TestClient(app) as client:
        missing = enquiry()
        missing.pop("privacy_acknowledged")
        response = client.post("/api/v2/public/enquiries", json=missing)
        assert response.status_code == 422
        assert "privacy notice acknowledgement is required" in response.text

        rejected = client.post(
            "/api/v2/public/enquiries",
            json=enquiry(privacy_acknowledged=False),
        )
        assert rejected.status_code == 422
        assert "privacy notice acknowledgement is required" in rejected.text


def test_privacy_notice_uses_configured_contact_without_exposing_secret_values():
    os.environ["SEVAA_PUBLIC_CONTACT_EMAIL"] = "privacy@example.com"
    try:
        with TestClient(app) as client:
            page = client.get("/privacy")
        assert page.status_code == 200
        assert 'mailto:privacy@example.com' in page.text
        assert "privacy@example.com" in page.text
        assert "SEVAA_PUBLIC_CONTACT_EMAIL" not in page.text
    finally:
        os.environ.pop("SEVAA_PUBLIC_CONTACT_EMAIL", None)


def test_public_quote_honeypot_is_acknowledged_but_not_persisted():
    automation = {
        "Authorization": "Bearer automation-public-test",
        "X-Actor": "public-enquiry-test",
    }
    with TestClient(app) as client:
        spam = client.post(
            "/api/v2/public/enquiries",
            json=enquiry(email="bot@example.com", website="https://spam.example"),
        )
        assert spam.status_code == 202
        assert spam.json() == {"accepted": True}

        dashboard = client.get("/api/v2/dashboard", headers=automation)
        assert dashboard.status_code == 200
        assert dashboard.json()["kpis"]["lead_count"] == 0
