import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEST_DB = Path(__file__).with_name("test_phase2.db")
os.environ["SEVAA_DB_PATH"] = str(TEST_DB)

from fastapi.testclient import TestClient
import backend.app as base
from backend.runtime import app


def setup_function():
    base.DB_PATH = TEST_DB
    os.environ.pop("SEVAA_FOUNDER_TOKEN", None)
    os.environ.pop("SEVAA_AUTOMATION_TOKEN", None)
    os.environ.pop("SEVAA_WEBHOOK_TOKEN", None)
    os.environ.pop("SEVAA_ALLOW_LEGACY_V1", None)
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


def test_idempotent_ingestion_and_overdue_followup():
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

        due_at = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        followup = client.post(
            f"/api/v2/leads/{first.json()['id']}/followups",
            json={"due_at": due_at, "channel": "phone", "draft_message": "Call buyer"},
        )
        assert followup.status_code == 201
        assert followup.json()["state"] == "overdue"

        dashboard = client.get("/api/v2/dashboard").json()
        assert dashboard["kpis"]["overdue_followups"] == 1
        assert dashboard["kpis"]["founder_attention"] >= 1

        completed = client.post(
            f"/api/v2/followups/{followup.json()['id']}/complete",
            json={"note": "Called and confirmed next step"},
        )
        assert completed.status_code == 200
        assert completed.json()["state"] == "completed"


def test_auth_founder_gate_and_daily_brief():
    os.environ["SEVAA_FOUNDER_TOKEN"] = "founder-test-token"
    os.environ["SEVAA_AUTOMATION_TOKEN"] = "automation-test-token"
    founder = {"Authorization": "Bearer founder-test-token", "X-Actor": "founder-test"}
    automation = {"Authorization": "Bearer automation-test-token", "X-Actor": "openclaw-test"}

    with TestClient(app) as client:
        assert client.get("/api/v2/auth/me").status_code == 401
        me = client.get("/api/v2/auth/me", headers=automation)
        assert me.status_code == 200
        assert me.json()["role"] == "automation"

        lead = client.post("/api/v2/leads", json=payload(), headers=automation)
        assert lead.status_code == 201

        proposal = client.post(
            f"/api/v2/leads/{lead.json()['id']}/proposals",
            json={"amount": 725000, "scope_summary": "20ft modular cafe shell + interiors"},
            headers=automation,
        )
        assert proposal.status_code == 201

        submitted = client.post(f"/api/v2/proposals/{proposal.json()['id']}/submit", headers=automation)
        assert submitted.status_code == 200
        approval_id = submitted.json()["approval"]["id"]

        forbidden = client.post(
            f"/api/v2/approvals/{approval_id}/decision",
            json={"decision": "approved", "note": "automation must not approve"},
            headers=automation,
        )
        assert forbidden.status_code == 403

        approved = client.post(
            f"/api/v2/approvals/{approval_id}/decision",
            json={"decision": "approved", "note": "Founder checked price and scope"},
            headers=founder,
        )
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"

        brief = client.get("/api/v2/internal/daily-brief", headers=automation)
        assert brief.status_code == 200
        assert brief.json()["actor"]["role"] == "automation"


def test_proposal_artifact_tracks_approval_state():
    with TestClient(app) as client:
        lead = client.post("/api/v2/leads", json=payload()).json()
        proposal = client.post(
            f"/api/v2/leads/{lead['id']}/proposals",
            json={"amount": 725000, "scope_summary": "20ft modular cafe shell + interiors"},
        ).json()

        draft = client.post(f"/api/v2/proposals/{proposal['id']}/artifact")
        assert draft.status_code == 201
        assert draft.json()["status_snapshot"] == "draft"
        assert "DRAFT — NOT APPROVED FOR EXTERNAL USE" in draft.json()["content"]
        assert "₹725,000" in draft.json()["content"]

        submitted = client.post(f"/api/v2/proposals/{proposal['id']}/submit").json()
        approval_id = submitted["approval"]["id"]
        approved = client.post(
            f"/api/v2/approvals/{approval_id}/decision",
            json={"decision": "approved", "note": "Founder approved"},
        )
        assert approved.status_code == 200

        regenerated = client.post(f"/api/v2/proposals/{proposal['id']}/artifact")
        assert regenerated.status_code == 201
        assert regenerated.json()["status_snapshot"] == "approved"
        assert "APPROVED FOR INTERNAL USE" in regenerated.json()["content"]

        download = client.get(f"/api/v2/proposals/{proposal['id']}/artifact/download")
        assert download.status_code == 200
        assert "attachment; filename=\"sevaa-proposal-" in download.headers["content-disposition"]
        assert "20ft modular cafe shell + interiors" in download.text


def test_webhook_is_disabled_by_default_and_idempotent_when_enabled():
    headers = {
        "Idempotency-Key": "web-1",
        "X-SEVAA-Webhook-Token": "webhook-test-token",
    }
    with TestClient(app) as client:
        disabled = client.post("/api/v2/webhooks/leads/website", json=payload(), headers=headers)
        assert disabled.status_code == 503

    os.environ["SEVAA_WEBHOOK_TOKEN"] = "webhook-test-token"
    try:
        with TestClient(app) as client:
            missing_key = client.post(
                "/api/v2/webhooks/leads/website",
                json=payload(),
                headers={"X-SEVAA-Webhook-Token": "webhook-test-token"},
            )
            assert missing_key.status_code == 400

            wrong = client.post(
                "/api/v2/webhooks/leads/website",
                json=payload(),
                headers={"Idempotency-Key": "bad-1", "X-SEVAA-Webhook-Token": "wrong"},
            )
            assert wrong.status_code == 401

            first = client.post("/api/v2/webhooks/leads/website", json=payload(), headers=headers)
            assert first.status_code == 201
            assert first.json()["source"] == "webhook:website"

            replay = client.post("/api/v2/webhooks/leads/website", json=payload(), headers=headers)
            assert replay.status_code == 201
            assert replay.json()["id"] == first.json()["id"]
            assert replay.json()["idempotent_replay"] is True

            conflict = client.post(
                "/api/v2/webhooks/leads/website",
                json=payload(requirement="Different requirement"),
                headers=headers,
            )
            assert conflict.status_code == 409

            duplicate_override = client.post(
                "/api/v2/webhooks/leads/website",
                json=payload(name="Duplicate Override", allow_duplicate=True),
                headers={
                    "Idempotency-Key": "web-2",
                    "X-SEVAA-Webhook-Token": "webhook-test-token",
                },
            )
            assert duplicate_override.status_code == 409
            assert duplicate_override.json()["detail"]["code"] == "duplicate_lead"
    finally:
        os.environ.pop("SEVAA_WEBHOOK_TOKEN", None)


def test_legacy_v1_is_blocked_when_hardened_auth_is_configured():
    os.environ["SEVAA_FOUNDER_TOKEN"] = "founder-test-token"
    os.environ["SEVAA_AUTOMATION_TOKEN"] = "automation-test-token"
    founder = {"Authorization": "Bearer founder-test-token"}

    with TestClient(app) as client:
        legacy = client.get("/api/leads")
        assert legacy.status_code == 410
        assert legacy.json()["detail"]["code"] == "legacy_v1_disabled"
        assert legacy.headers["deprecation"] == "true"

        health = client.get("/api/health")
        assert health.status_code == 200

        hardened = client.get("/api/v2/auth/me", headers=founder)
        assert hardened.status_code == 200
        assert hardened.json()["role"] == "founder"


def test_runtime_schema_migrations_are_versioned_and_idempotent():
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200

    with base.db() as conn:
        versions = [
            row["version"]
            for row in conn.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            ).fetchall()
        ]
    assert versions == [1, 2, 3]

    base.init_db()
    base.init_db()
    with base.db() as conn:
        rows = conn.execute(
            "SELECT version, COUNT(*) AS n FROM schema_migrations GROUP BY version ORDER BY version"
        ).fetchall()
    assert [(r["version"], r["n"]) for r in rows] == [(1, 1), (2, 1), (3, 1)]
