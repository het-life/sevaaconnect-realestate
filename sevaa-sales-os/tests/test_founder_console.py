import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEST_DB = Path(__file__).with_name("test_founder_console.db")

import backend.app as base
from backend.runtime import app
from fastapi.testclient import TestClient


def setup_function():
    base.DB_PATH = TEST_DB
    for key in (
        "SEVAA_FOUNDER_TOKEN",
        "SEVAA_AUTOMATION_TOKEN",
        "SEVAA_WEBHOOK_TOKEN",
        "SEVAA_ALLOW_LEGACY_V1",
    ):
        os.environ.pop(key, None)
    if TEST_DB.exists():
        TEST_DB.unlink()


def test_founder_console_uses_hardened_v2_and_stage_route():
    with TestClient(app) as client:
        lead = client.post(
            "/api/v2/leads",
            json={
                "name": "Console Buyer",
                "company": "Console Co",
                "requirement": "modular site office",
                "budget_min": 500000,
                "timeline_days": 45,
            },
            headers={"Idempotency-Key": "console-1", "X-Actor": "founder-dashboard"},
        )
        assert lead.status_code == 201

        moved = client.patch(
            f"/api/v2/leads/{lead.json()['id']}/stage",
            json={"stage": "follow_up"},
            headers={"X-Actor": "founder-dashboard"},
        )
        assert moved.status_code == 200
        assert moved.json()["stage"] == "follow_up"

        page = client.get("/")
        assert page.status_code == 200
        assert "/api/v2/dashboard" in page.text
        assert "/api/v2/approvals/" in page.text
        assert "sessionStorage" in page.text
        assert "No autonomous external messaging" in page.text
