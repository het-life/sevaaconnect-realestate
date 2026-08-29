import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEST_DB = Path(__file__).with_name("test_openclaw_client.db")
os.environ["SEVAA_DB_PATH"] = str(TEST_DB)

from fastapi.testclient import TestClient

import backend.app as base
from backend.runtime import app
from scripts.openclaw_client import OpenClawClient, OpenClawClientError


def setup_function():
    base.DB_PATH = TEST_DB
    os.environ["SEVAA_FOUNDER_TOKEN"] = "founder-openclaw-test"
    os.environ["SEVAA_AUTOMATION_TOKEN"] = "automation-openclaw-test"
    os.environ.pop("SEVAA_WEBHOOK_TOKEN", None)
    os.environ.pop("SEVAA_ALLOW_LEGACY_V1", None)
    if TEST_DB.exists():
        TEST_DB.unlink()


def transport_for(client: TestClient):
    def transport(method, path, headers, payload):
        response = client.request(method, path, headers=headers, json=payload)
        if response.status_code >= 400:
            raise OpenClawClientError(f"HTTP {response.status_code}: {response.text}")
        if not response.content:
            return None
        return response.json()

    return transport


def test_openclaw_client_runs_safe_automation_workflow():
    with TestClient(app) as api:
        client = OpenClawClient(
            "http://testserver",
            "automation-openclaw-test",
            actor="openclaw-test",
            transport=transport_for(api),
        )

        identity = client.ensure_automation_identity()
        assert identity["role"] == "automation"
        assert identity["actor_id"] == "openclaw-test"

        lead = client.create_lead(
            {
                "name": "Automation Buyer",
                "company": "Automation Co",
                "requirement": "modular sales office",
                "budget_min": 650000,
                "timeline_days": 30,
                "source": "openclaw-test",
            },
            idempotency_key="openclaw-client-1",
        )
        assert lead["id"] > 0

        proposal = client.create_proposal(
            lead["id"],
            725000,
            "Modular sales office shell and interiors",
        )
        submitted = client.submit_proposal(proposal["id"])
        assert submitted["approval"]["status"] == "pending"

        approvals = client.list_approvals("pending")
        assert approvals[0]["object_id"] == proposal["id"]

        due_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        followup = client.schedule_followup(
            lead["id"],
            due_at,
            channel="manual",
            draft_message="Founder should review buyer response before any external send.",
        )
        assert followup["state"] == "pending"

        brief = client.daily_brief()
        assert brief["actor"]["role"] == "automation"
        assert brief["proposals_awaiting_approval"] == 1
        assert brief["pending_followups"] == 1

        completed = client.complete_followup(followup["id"], "Reviewed internally")
        assert completed["state"] == "completed"

        assert not hasattr(client, "decide_approval")


def test_openclaw_client_rejects_founder_identity():
    with TestClient(app) as api:
        client = OpenClawClient(
            "http://testserver",
            "founder-openclaw-test",
            actor="misconfigured-openclaw",
            transport=transport_for(api),
        )
        try:
            client.ensure_automation_identity()
        except OpenClawClientError as exc:
            assert "automation credential required" in str(exc)
        else:
            raise AssertionError("founder identity must not be accepted by the OpenClaw client")
