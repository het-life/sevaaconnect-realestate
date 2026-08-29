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
        assert "SEVAA_AUTOMATION_TOKEN" not in page.text

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
        assert matches[0]["source"] == "public-quote"


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
