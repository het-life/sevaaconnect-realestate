import os
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


pytestmark = pytest.mark.skipif(
    not os.getenv("SEVAA_DATABASE_URL", "").startswith(("postgresql://", "postgres://")),
    reason="PostgreSQL integration requires SEVAA_DATABASE_URL",
)


def test_hardened_runtime_round_trip_on_postgresql():
    from backend import database
    import backend.app as base
    from backend.runtime import app

    assert database.database_backend() == "postgresql"

    automation = {
        "Authorization": f"Bearer {os.environ['SEVAA_AUTOMATION_TOKEN']}",
        "X-Actor": "postgres-ci-automation",
    }
    founder = {
        "Authorization": f"Bearer {os.environ['SEVAA_FOUNDER_TOKEN']}",
        "X-Actor": "postgres-ci-founder",
    }
    unique = uuid.uuid4().hex[:12]
    idempotency_key = f"postgres-ci-{unique}"

    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        identity = client.get("/api/v2/auth/me", headers=automation)
        assert identity.status_code == 200
        assert identity.json()["role"] == "automation"

        payload = {
            "name": f"Postgres Buyer {unique}",
            "company": f"Postgres Co {unique}",
            "email": f"pg-{unique}@example.test",
            "requirement": "modular site office with 45 day delivery",
            "budget_min": 700000,
            "budget_max": 850000,
            "timeline_days": 45,
            "site_ready": True,
            "source": "postgres-ci",
        }
        lead = client.post(
            "/api/v2/leads",
            json=payload,
            headers={**automation, "Idempotency-Key": idempotency_key},
        )
        assert lead.status_code == 201, lead.text
        lead_id = lead.json()["id"]

        replay = client.post(
            "/api/v2/leads",
            json=payload,
            headers={**automation, "Idempotency-Key": idempotency_key},
        )
        assert replay.status_code == 201, replay.text
        assert replay.json()["id"] == lead_id
        assert replay.json()["idempotent_replay"] is True

        proposal = client.post(
            f"/api/v2/leads/{lead_id}/proposals",
            json={"amount": 749000, "scope_summary": "PostgreSQL integration pilot scope"},
            headers=automation,
        )
        assert proposal.status_code == 201, proposal.text
        proposal_id = proposal.json()["id"]

        submitted = client.post(f"/api/v2/proposals/{proposal_id}/submit", headers=automation)
        assert submitted.status_code == 200, submitted.text
        approval_id = submitted.json()["approval"]["id"]
        assert submitted.json()["approval"]["status"] == "pending"

        denied = client.post(
            f"/api/v2/approvals/{approval_id}/decision",
            json={"decision": "approved", "note": "automation must not approve"},
            headers=automation,
        )
        assert denied.status_code == 403

        approved = client.post(
            f"/api/v2/approvals/{approval_id}/decision",
            json={"decision": "approved", "note": "PostgreSQL CI founder approval"},
            headers=founder,
        )
        assert approved.status_code == 200, approved.text
        assert approved.json()["status"] == "approved"

        artifact = client.post(f"/api/v2/proposals/{proposal_id}/artifact", headers=automation)
        assert artifact.status_code == 201, artifact.text
        assert artifact.json()["status_snapshot"] == "approved"

        followup = client.post(
            f"/api/v2/leads/{lead_id}/followups",
            json={
                "due_at": "2030-01-02T09:30:00+00:00",
                "channel": "manual",
                "draft_message": "CI draft only; no external send",
            },
            headers=automation,
        )
        assert followup.status_code == 201, followup.text
        completed = client.post(
            f"/api/v2/followups/{followup.json()['id']}/complete",
            json={"note": "PostgreSQL CI completion"},
            headers=automation,
        )
        assert completed.status_code == 200, completed.text
        assert completed.json()["state"] == "completed"

        share = client.post(
            f"/api/v2/proposals/{proposal_id}/share",
            json={"expires_days": 1},
            headers=founder,
        )
        assert share.status_code == 201, share.text
        public_share = client.get(share.json()["path"])
        assert public_share.status_code == 200, public_share.text
        assert "PostgreSQL integration pilot scope" in public_share.text

        outcome = client.post(
            f"/api/v2/leads/{lead_id}/outcome",
            json={"outcome": "won", "proposal_id": proposal_id, "note": "PostgreSQL CI only"},
            headers=founder,
        )
        assert outcome.status_code == 200, outcome.text
        assert outcome.json()["outcome"] == "won"
        assert outcome.json()["contract_value"] == 749000

    with base.db() as conn:
        versions = [row["version"] for row in conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()]
    assert versions == [1, 2, 3, 4]
