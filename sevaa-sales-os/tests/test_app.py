import os
from pathlib import Path

TEST_DB = Path(__file__).with_name("test_sevaa.db")
os.environ["SEVAA_DB_PATH"] = str(TEST_DB)

from fastapi.testclient import TestClient
import backend.app as base

app = base.app


def setup_function():
    # Tests share the imported backend module with the v2 suite. Reset the
    # database path explicitly so pytest collection order cannot leak state.
    base.DB_PATH = TEST_DB
    if TEST_DB.exists():
        TEST_DB.unlink()


def test_lead_flow():
    with TestClient(app) as client:
        r = client.post("/api/leads", json={
            "name": "Test Buyer",
            "requirement": "modular cafe",
            "budget_min": 600000,
            "budget_max": 800000,
            "timeline_days": 30,
            "site_ready": True,
            "phone": "+91-9999999999"
        })
        assert r.status_code == 201
        lead = r.json()
        assert lead["score"] >= 70
        assert lead["stage"] == "qualified"

        d = client.get("/api/dashboard")
        assert d.status_code == 200
        assert d.json()["kpis"]["lead_count"] == 1

        a = client.get("/api/audit")
        assert a.status_code == 200
        assert a.json()[0]["event_type"] == "lead.created"

        moved = client.patch(f"/api/leads/{lead['id']}/stage", json={"stage": "proposal"})
        assert moved.status_code == 200
        assert moved.json()["stage"] == "proposal"
