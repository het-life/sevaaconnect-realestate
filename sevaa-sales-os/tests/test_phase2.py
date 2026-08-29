import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEST_DB = Path(__file__).with_name("test_phase2.db")
os.environ["SEVAA_DB_PATH"] = str(TEST_DB)

from fastapi.testclient import TestClient
from backend.phase2 import app


def setup_function():
    if TEST_DB.exists():
        TEST_DB.unlink()


def payload(**overrides):
    data = {
        "name": "Phase Two Buyer",
        "company": "Phase Two Co",
        "phone": "+91 99999 99999",
        "email": "buyer@example.com",
        "requirement": "20ft modular cafe",
        "budget_min": 600000,
        "budget_max": 800000,
        "timeline_days": 30,
        "site_ready": True,
    }
    data.update(overrides)
    return data


def test_idempotent_duplicate_safe_ingestion():
    with TestClient(app) as client:
        first = client.post("/api/v2/leads", json=payload(), headers={"Idempotency-Key": "lead-001"})
        assert first.status_code == 201
        replay = client.post("/api/v2/leads", json=payload(), headers={"Idempotency-Key": "lead-001"})
        assert replay.status_code == 201
        assert replay.json()["id"] == first.json()["id"]
        assert replay.json()["idempotent_replay"] is True
        duplicate = client.post("/api/v2/leads", json=payload(name="Same Contact"))
        assert duplicate.status_code == 409
        assert duplicate.json()["detail"]["code"] == "duplicate_lead"


def test_proposal_requires_explicit_founder_decision():
    with TestClient(app) as client:
        lead = client.post("/api/v2/leads", json=payload()).json()
        proposal = client.post(
            f"/api/v2/leads/{lead['id']}/proposals",
            json={"amount": 725000, "scope_summary": "20ft modular cafe shell + interiors"},
        )
        assert proposal.status_code == 201
        submitted = client.post(f"/api/v2/proposals/{proposal.json()['id']}/submit")
        assert submitted.status_code == 200
        approval = submitted.json()["approval"]
        assert approval["status"] == "pending"
        dashboard = client.get("/api/v2/dashboard").json()
        assert dashboard["kpis"]["pending_approvals"] == 1
        decided = client.post(
            f"/api/v2/approvals/{approval['id']}/decision",
            json={"decision": "approved", "note": "Founder checked price and scope"},
        )
        assert decided.status_code == 200
        assert decided.json()["status"] == "approved"
        assert client.get("/api/v2/approvals?status=pending").json() == []
