import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEST_DB = Path(__file__).with_name("test_revenue.db")
os.environ["SEVAA_DB_PATH"] = str(TEST_DB)

from fastapi.testclient import TestClient
import backend.app as base
from backend.runtime import app
import backend.revenue as revenue


def setup_function():
    base.DB_PATH = TEST_DB
    for key in (
        "SEVAA_FOUNDER_TOKEN",
        "SEVAA_AUTOMATION_TOKEN",
        "SEVAA_WEBHOOK_TOKEN",
        "SEVAA_ALLOW_LEGACY_V1",
        "RAZORPAY_KEY_ID",
        "RAZORPAY_KEY_SECRET",
        "RAZORPAY_WEBHOOK_SECRET",
    ):
        os.environ.pop(key, None)
    if TEST_DB.exists():
        TEST_DB.unlink()


def lead_payload():
    return {
        "name": "Revenue Buyer",
        "company": "Revenue Co",
        "phone": "+91 99999 12345",
        "email": "revenue@example.com",
        "requirement": "20ft modular retail unit",
        "budget_min": 600000,
        "budget_max": 800000,
        "timeline_days": 30,
        "site_ready": True,
    }


def approved_proposal(client, headers=None):
    headers = headers or {}
    lead = client.post("/api/v2/leads", json=lead_payload(), headers=headers)
    assert lead.status_code == 201
    proposal = client.post(
        f"/api/v2/leads/{lead.json()['id']}/proposals",
        json={"amount": 725000, "scope_summary": "Approved modular unit scope"},
        headers=headers,
    )
    assert proposal.status_code == 201
    submitted = client.post(
        f"/api/v2/proposals/{proposal.json()['id']}/submit", headers=headers
    )
    approval_id = submitted.json()["approval"]["id"]
    approved = client.post(
        f"/api/v2/approvals/{approval_id}/decision",
        json={"decision": "approved", "note": "checked"},
        headers=headers,
    )
    assert approved.status_code == 200
    return lead.json(), proposal.json()


def test_won_outcome_requires_approved_proposal_and_stage_route_cannot_bypass():
    with TestClient(app) as client:
        lead = client.post("/api/v2/leads", json=lead_payload()).json()
        bypass = client.patch(f"/api/v2/leads/{lead['id']}/stage", json={"stage": "won"})
        assert bypass.status_code == 409
        assert bypass.json()["detail"]["code"] == "outcome_route_required"

        no_proposal = client.post(
            f"/api/v2/leads/{lead['id']}/outcome", json={"outcome": "won"}
        )
        assert no_proposal.status_code == 409

        proposal = client.post(
            f"/api/v2/leads/{lead['id']}/proposals",
            json={"amount": 725000, "scope_summary": "Approved modular unit scope"},
        ).json()
        submitted = client.post(f"/api/v2/proposals/{proposal['id']}/submit").json()
        client.post(
            f"/api/v2/approvals/{submitted['approval']['id']}/decision",
            json={"decision": "approved"},
        )
        won = client.post(
            f"/api/v2/leads/{lead['id']}/outcome",
            json={"outcome": "won", "proposal_id": proposal["id"]},
        )
        assert won.status_code == 200
        assert won.json()["contract_value"] == 725000
        summary = client.get("/api/v2/revenue").json()
        assert summary["won_count"] == 1
        assert summary["won_value"] == 725000


def test_automation_cannot_create_payment_link_or_buyer_share(monkeypatch):
    os.environ["SEVAA_FOUNDER_TOKEN"] = "founder"
    os.environ["SEVAA_AUTOMATION_TOKEN"] = "automation"
    founder = {"Authorization": "Bearer founder"}
    automation = {"Authorization": "Bearer automation"}

    with TestClient(app) as client:
        lead, proposal = approved_proposal(client, founder)
        forbidden = client.post(
            f"/api/v2/proposals/{proposal['id']}/payment-links",
            json={"amount": 100000},
            headers=automation,
        )
        assert forbidden.status_code == 403
        share_forbidden = client.post(
            f"/api/v2/proposals/{proposal['id']}/share",
            json={"expires_days": 14},
            headers=automation,
        )
        assert share_forbidden.status_code == 403

        monkeypatch.setattr(
            revenue.payments,
            "create_payment_link",
            lambda **kwargs: {
                "id": "plink_12345678901234",
                "short_url": "https://rzp.io/i/test-safe-link",
                "status": "created",
            },
        )
        created = client.post(
            f"/api/v2/proposals/{proposal['id']}/payment-links",
            json={"amount": 100000},
            headers=founder,
        )
        assert created.status_code == 201
        assert created.json()["amount"] == 100000

        share = client.post(
            f"/api/v2/proposals/{proposal['id']}/share",
            json={"expires_days": 14},
            headers=founder,
        )
        assert share.status_code == 201
        assert "token" in share.json()
        page = client.get(share.json()["path"])
        assert page.status_code == 200
        assert "Approved modular unit scope" in page.text
        assert "Pay securely" in page.text
        assert "https://rzp.io/i/test-safe-link" in page.text


def test_signed_payment_webhook_records_cash_and_marks_won(monkeypatch):
    with TestClient(app) as client:
        lead, proposal = approved_proposal(client)
        monkeypatch.setattr(
            revenue.payments,
            "create_payment_link",
            lambda **kwargs: {
                "id": "plink_12345678901234",
                "short_url": "https://rzp.io/i/test-safe-link",
                "status": "created",
            },
        )
        link = client.post(
            f"/api/v2/proposals/{proposal['id']}/payment-links",
            json={"amount": 100000},
        )
        assert link.status_code == 201

        os.environ["RAZORPAY_KEY_ID"] = "rzp_test_x"
        os.environ["RAZORPAY_KEY_SECRET"] = "secret"
        os.environ["RAZORPAY_WEBHOOK_SECRET"] = "webhook-secret"
        event = {
            "event": "payment_link.paid",
            "payload": {
                "payment_link": {
                    "entity": {
                        "id": "plink_12345678901234",
                        "amount_paid": 10000000,
                    }
                },
                "payment": {"entity": {"id": "pay_123"}},
            },
        }
        raw = json.dumps(event, separators=(",", ":")).encode()
        signature = hmac.new(b"webhook-secret", raw, hashlib.sha256).hexdigest()
        paid = client.post(
            "/api/v2/payments/razorpay/webhook",
            content=raw,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": signature},
        )
        assert paid.status_code == 200

        summary = client.get("/api/v2/revenue").json()
        assert summary["collected_value"] == 100000
        assert summary["won_value"] == 725000
        assert summary["won_count"] == 1
        dashboard = client.get("/api/v2/dashboard").json()
        assert len(dashboard["stages"]["won"]) == 1

        replay = client.post(
            "/api/v2/payments/razorpay/webhook",
            content=raw,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": signature},
        )
        assert replay.status_code == 200
        assert client.get("/api/v2/revenue").json()["collected_value"] == 100000


def test_bad_webhook_signature_is_rejected():
    os.environ["RAZORPAY_KEY_ID"] = "rzp_test_x"
    os.environ["RAZORPAY_KEY_SECRET"] = "secret"
    os.environ["RAZORPAY_WEBHOOK_SECRET"] = "webhook-secret"
    with TestClient(app) as client:
        bad = client.post(
            "/api/v2/payments/razorpay/webhook",
            content=b'{"event":"payment_link.paid"}',
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": "bad"},
        )
        assert bad.status_code == 401
