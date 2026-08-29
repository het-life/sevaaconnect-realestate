from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import Depends, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from backend import payments
from backend.phase2 import ActorContext, app, base, require_founder, resolve_actor
from backend.migrations import apply_migrations


class OutcomeCreate(BaseModel):
    outcome: Literal["won", "lost"]
    proposal_id: int | None = Field(default=None, ge=1)
    note: str | None = Field(default=None, max_length=1000)


class PaymentLinkCreate(BaseModel):
    amount: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=1000)


class ShareCreate(BaseModel):
    expires_days: int = Field(default=14, ge=1, le=90)


def init_revenue_db() -> None:
    with base.db() as conn:
        apply_migrations(conn)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _provider_status(entity: dict) -> str:
    status = str(entity.get("status") or "created").lower()
    if status in {"paid", "partially_paid", "cancelled", "expired", "created", "issued"}:
        return status
    return status[:40] or "unknown"


def _mark_paid(conn, payment_link_row, *, paid_amount: int, payment_id: str | None, actor: str) -> None:
    ts = base.now_iso()
    if payment_link_row["status"] == "paid":
        return
    conn.execute(
        """UPDATE payment_links
           SET status='paid', paid_amount=?, provider_payment_id=?, paid_at=?, updated_at=?
           WHERE id=?""",
        (paid_amount, payment_id, ts, ts, payment_link_row["id"]),
    )
    proposal = conn.execute(
        "SELECT * FROM proposals WHERE id=?", (payment_link_row["proposal_id"],)
    ).fetchone()
    if proposal is not None:
        existing = conn.execute(
            "SELECT * FROM sales_outcomes WHERE lead_id=?", (proposal["lead_id"],)
        ).fetchone()
        if existing is None:
            conn.execute(
                """INSERT INTO sales_outcomes(lead_id,proposal_id,outcome,contract_value,note,recorded_by,created_at,updated_at)
                   VALUES(?,?,'won',?,?,?,?,?)""",
                (
                    proposal["lead_id"],
                    proposal["id"],
                    proposal["amount"],
                    "Auto-recorded after verified payment",
                    actor,
                    ts,
                    ts,
                ),
            )
        elif existing["outcome"] != "won":
            conn.execute(
                """UPDATE sales_outcomes SET outcome='won',proposal_id=?,contract_value=?,note=?,recorded_by=?,updated_at=?
                   WHERE lead_id=?""",
                (
                    proposal["id"],
                    proposal["amount"],
                    "Updated after verified payment",
                    actor,
                    ts,
                    proposal["lead_id"],
                ),
            )
        conn.execute(
            "UPDATE leads SET stage='won',updated_at=? WHERE id=?",
            (ts, proposal["lead_id"]),
        )
        base.audit(
            conn,
            proposal["lead_id"],
            "payment.verified_paid",
            f"Payment link #{payment_link_row['id']} verified paid; collected ₹{paid_amount}",
            actor,
        )
        base.audit(
            conn,
            proposal["lead_id"],
            "lead.won",
            f"Lead marked won from verified payment; contract ₹{proposal['amount']}",
            actor,
        )


@app.post("/api/v2/leads/{lead_id}/outcome")
def record_outcome(
    lead_id: int,
    payload: OutcomeCreate,
    actor: ActorContext = Depends(require_founder),
):
    init_revenue_db()
    ts = base.now_iso()
    with base.db() as conn:
        lead = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        if lead is None:
            raise HTTPException(404, "lead not found")
        if payload.outcome == "lost":
            collected = conn.execute(
                """SELECT COALESCE(SUM(pl.paid_amount),0) AS n
                   FROM payment_links pl JOIN proposals p ON p.id=pl.proposal_id
                   WHERE p.lead_id=? AND pl.status='paid'""",
                (lead_id,),
            ).fetchone()["n"]
            if collected:
                raise HTTPException(409, "a lead with verified collected payment cannot be marked lost")
        proposal = None
        contract_value = 0
        if payload.outcome == "won":
            if payload.proposal_id is None:
                proposal = conn.execute(
                    "SELECT * FROM proposals WHERE lead_id=? AND status='approved' ORDER BY id DESC LIMIT 1",
                    (lead_id,),
                ).fetchone()
            else:
                proposal = conn.execute(
                    "SELECT * FROM proposals WHERE id=? AND lead_id=?",
                    (payload.proposal_id, lead_id),
                ).fetchone()
            if proposal is None or proposal["status"] != "approved":
                raise HTTPException(409, "won outcome requires an approved proposal")
            contract_value = int(proposal["amount"])
        existing = conn.execute(
            "SELECT * FROM sales_outcomes WHERE lead_id=?", (lead_id,)
        ).fetchone()
        proposal_id = proposal["id"] if proposal else payload.proposal_id
        if existing:
            conn.execute(
                """UPDATE sales_outcomes
                   SET proposal_id=?,outcome=?,contract_value=?,note=?,recorded_by=?,updated_at=?
                   WHERE lead_id=?""",
                (proposal_id, payload.outcome, contract_value, payload.note, actor.actor_id, ts, lead_id),
            )
        else:
            conn.execute(
                """INSERT INTO sales_outcomes(lead_id,proposal_id,outcome,contract_value,note,recorded_by,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (lead_id, proposal_id, payload.outcome, contract_value, payload.note, actor.actor_id, ts, ts),
            )
        conn.execute(
            "UPDATE leads SET stage=?,updated_at=? WHERE id=?",
            (payload.outcome, ts, lead_id),
        )
        base.audit(
            conn,
            lead_id,
            f"lead.{payload.outcome}",
            f"Outcome recorded; contract_value=₹{contract_value}",
            actor.actor_id,
        )
        row = conn.execute("SELECT * FROM sales_outcomes WHERE lead_id=?", (lead_id,)).fetchone()
    return dict(row)


@app.post("/api/v2/proposals/{proposal_id}/payment-links", status_code=201)
def create_proposal_payment_link(
    proposal_id: int,
    payload: PaymentLinkCreate,
    actor: ActorContext = Depends(require_founder),
):
    init_revenue_db()
    with base.db() as conn:
        proposal = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        if proposal is None:
            raise HTTPException(404, "proposal not found")
        if proposal["status"] != "approved":
            raise HTTPException(409, "payment link requires an approved proposal")
        if payload.amount > int(proposal["amount"]):
            raise HTTPException(409, "payment amount cannot exceed approved proposal amount")
        lead = conn.execute("SELECT * FROM leads WHERE id=?", (proposal["lead_id"],)).fetchone()
    reference = f"sevaa-p{proposal_id}-{secrets.token_hex(4)}"[:40]
    try:
        provider = payments.create_payment_link(
            amount_rupees=payload.amount,
            reference_id=reference,
            description=payload.description or f"SEVAA proposal #{proposal_id}",
            customer_name=lead["name"],
            customer_email=lead["email"],
            customer_phone=lead["phone"],
        )
    except payments.PaymentProviderError as exc:
        raise HTTPException(503, str(exc)) from exc
    provider_id = str(provider.get("id") or "")
    short_url = str(provider.get("short_url") or "")
    if not provider_id or not short_url:
        raise HTTPException(502, "payment provider returned an incomplete payment link")
    ts = base.now_iso()
    with base.db() as conn:
        cur = conn.execute(
            """INSERT INTO payment_links(
                   proposal_id,provider,provider_payment_link_id,reference_id,amount,currency,status,short_url,
                   created_by,created_at,updated_at
               ) VALUES(?,?,?,?,?,'INR',?,?,?,?,?)""",
            (
                proposal_id,
                "razorpay",
                provider_id,
                reference,
                payload.amount,
                _provider_status(provider),
                short_url,
                actor.actor_id,
                ts,
                ts,
            ),
        )
        link_id = int(cur.lastrowid)
        base.audit(
            conn,
            proposal["lead_id"],
            "payment_link.created",
            f"Founder created payment link #{link_id} for ₹{payload.amount}; provider notifications disabled",
            actor.actor_id,
        )
        row = conn.execute("SELECT * FROM payment_links WHERE id=?", (link_id,)).fetchone()
    return dict(row)


@app.get("/api/v2/payment-links")
def list_payment_links(actor: ActorContext = Depends(resolve_actor)):
    init_revenue_db()
    with base.db() as conn:
        rows = conn.execute(
            """SELECT pl.*,p.lead_id,l.name AS lead_name,l.company AS lead_company
               FROM payment_links pl JOIN proposals p ON p.id=pl.proposal_id
               JOIN leads l ON l.id=p.lead_id ORDER BY pl.id DESC"""
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/v2/payment-links/{payment_link_id}/refresh")
def refresh_payment_link(
    payment_link_id: int,
    actor: ActorContext = Depends(resolve_actor),
):
    init_revenue_db()
    with base.db() as conn:
        row = conn.execute("SELECT * FROM payment_links WHERE id=?", (payment_link_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "payment link not found")
    try:
        provider = payments.fetch_payment_link(row["provider_payment_link_id"])
    except payments.PaymentProviderError as exc:
        raise HTTPException(503, str(exc)) from exc
    status = _provider_status(provider)
    amount_paid = int(provider.get("amount_paid") or 0) // 100
    ts = base.now_iso()
    with base.db() as conn:
        current = conn.execute("SELECT * FROM payment_links WHERE id=?", (payment_link_id,)).fetchone()
        if status == "paid":
            _mark_paid(
                conn,
                current,
                paid_amount=amount_paid or int(current["amount"]),
                payment_id=None,
                actor=actor.actor_id,
            )
        else:
            conn.execute(
                "UPDATE payment_links SET status=?,paid_amount=?,updated_at=? WHERE id=?",
                (status, amount_paid, ts, payment_link_id),
            )
        updated = conn.execute("SELECT * FROM payment_links WHERE id=?", (payment_link_id,)).fetchone()
    return dict(updated)


@app.post("/api/v2/proposals/{proposal_id}/share", status_code=201)
def create_proposal_share(
    proposal_id: int,
    payload: ShareCreate,
    actor: ActorContext = Depends(require_founder),
):
    init_revenue_db()
    with base.db() as conn:
        proposal = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        if proposal is None:
            raise HTTPException(404, "proposal not found")
        if proposal["status"] != "approved":
            raise HTTPException(409, "only approved proposals can be shared")
    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    ts = base.now_iso()
    expires_at = (_now() + timedelta(days=payload.expires_days)).isoformat()
    with base.db() as conn:
        conn.execute(
            "UPDATE proposal_share_tokens SET revoked_at=? WHERE proposal_id=? AND revoked_at IS NULL",
            (ts, proposal_id),
        )
        cur = conn.execute(
            """INSERT INTO proposal_share_tokens(
                   proposal_id,token_hash,expires_at,created_by,created_at
               ) VALUES(?,?,?,?,?)""",
            (proposal_id, token_hash, expires_at, actor.actor_id, ts),
        )
        share_id = int(cur.lastrowid)
        base.audit(
            conn,
            proposal["lead_id"],
            "proposal.share_created",
            f"Secure buyer share #{share_id} created for proposal #{proposal_id}; expires {expires_at}",
            actor.actor_id,
        )
    return {"id": share_id, "proposal_id": proposal_id, "token": token, "expires_at": expires_at, "path": f"/p/{token}"}


@app.post("/api/v2/proposal-shares/{share_id}/revoke")
def revoke_share(share_id: int, actor: ActorContext = Depends(require_founder)):
    init_revenue_db()
    ts = base.now_iso()
    with base.db() as conn:
        share = conn.execute("SELECT * FROM proposal_share_tokens WHERE id=?", (share_id,)).fetchone()
        if share is None:
            raise HTTPException(404, "share not found")
        conn.execute("UPDATE proposal_share_tokens SET revoked_at=? WHERE id=?", (ts, share_id))
        proposal = conn.execute("SELECT * FROM proposals WHERE id=?", (share["proposal_id"],)).fetchone()
        base.audit(conn, proposal["lead_id"], "proposal.share_revoked", f"Share #{share_id} revoked", actor.actor_id)
    return {"id": share_id, "revoked": True}


def _share_record(conn, token: str):
    return conn.execute(
        """SELECT s.*,p.amount,p.scope_summary,p.status AS proposal_status,p.lead_id,
                  l.name,l.company,l.requirement,l.city
           FROM proposal_share_tokens s JOIN proposals p ON p.id=s.proposal_id
           JOIN leads l ON l.id=p.lead_id WHERE s.token_hash=?""",
        (_hash_token(token),),
    ).fetchone()


@app.get("/p/{token}", response_class=HTMLResponse)
def public_proposal_share(token: str):
    init_revenue_db()
    with base.db() as conn:
        row = _share_record(conn, token)
        if row is None or row["revoked_at"] is not None:
            raise HTTPException(404, "proposal share not found")
        expiry = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry < _now():
            raise HTTPException(410, "proposal share expired")
        if row["proposal_status"] != "approved":
            raise HTTPException(409, "proposal is no longer approved")
        payment = conn.execute(
            """SELECT * FROM payment_links WHERE proposal_id=? AND status NOT IN ('cancelled','expired')
               ORDER BY id DESC LIMIT 1""",
            (row["proposal_id"],),
        ).fetchone()
    import html
    def esc(value):
        return html.escape(str(value or "—"), quote=True)
    pay_html = ""
    if payment is not None and payment["short_url"]:
        pay_html = f'<p><a class="pay" href="{esc(payment["short_url"])}" rel="noopener">Pay securely</a></p>'
    body = f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>SEVAA Proposal #{row['proposal_id']}</title><style>body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:760px;margin:0 auto;padding:32px 20px;background:#07100e;color:#eef7f3}}.card{{background:#101b18;border:1px solid #294139;border-radius:18px;padding:24px}}h1{{font-size:24px}}.muted{{color:#9ab0a8}}.amount{{font-size:30px;font-weight:800;color:#9df5c9}}.pay{{display:inline-block;background:#9df5c9;color:#062015;padding:12px 18px;border-radius:10px;text-decoration:none;font-weight:750}}</style></head>
    <body><div class='card'><div class='muted'>Approved proposal</div><h1>{esc(row['company'] or row['name'])}</h1><p>{esc(row['scope_summary'])}</p><p class='amount'>₹{int(row['amount']):,}</p><p><b>Requirement</b><br>{esc(row['requirement'])}</p>{pay_html}<p class='muted'>This secure link expires {esc(row['expires_at'])}. Payment availability is controlled by the founder.</p></div></body></html>"""
    return HTMLResponse(body)


@app.post("/api/v2/payments/razorpay/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None, alias="X-Razorpay-Signature"),
):
    raw = await request.body()
    if not payments.verify_webhook_signature(raw, x_razorpay_signature):
        raise HTTPException(401, "invalid webhook signature")
    try:
        event = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(400, "invalid webhook payload") from exc
    event_name = str(event.get("event") or "")
    if event_name not in {"payment_link.paid", "payment_link.partially_paid", "payment_link.cancelled", "payment_link.expired"}:
        return {"ok": True, "ignored": True, "event": event_name}
    entity = (((event.get("payload") or {}).get("payment_link") or {}).get("entity") or {})
    provider_id = str(entity.get("id") or "")
    if not provider_id:
        raise HTTPException(400, "payment link id missing")
    init_revenue_db()
    with base.db() as conn:
        row = conn.execute(
            "SELECT * FROM payment_links WHERE provider_payment_link_id=?", (provider_id,)
        ).fetchone()
        if row is None:
            return {"ok": True, "ignored": True, "reason": "unknown payment link"}
        status = {
            "payment_link.paid": "paid",
            "payment_link.partially_paid": "partially_paid",
            "payment_link.cancelled": "cancelled",
            "payment_link.expired": "expired",
        }[event_name]
        amount_paid = int(entity.get("amount_paid") or 0) // 100
        payment_entity = (((event.get("payload") or {}).get("payment") or {}).get("entity") or {})
        payment_id = str(payment_entity.get("id") or "") or None
        if status == "paid":
            _mark_paid(
                conn,
                row,
                paid_amount=amount_paid or int(row["amount"]),
                payment_id=payment_id,
                actor="razorpay-webhook",
            )
        else:
            conn.execute(
                "UPDATE payment_links SET status=?,paid_amount=?,provider_payment_id=?,updated_at=? WHERE id=?",
                (status, amount_paid, payment_id, base.now_iso(), row["id"]),
            )
    return {"ok": True, "event": event_name}


@app.get("/api/v2/revenue")
def revenue_summary(actor: ActorContext = Depends(resolve_actor)):
    init_revenue_db()
    with base.db() as conn:
        wins = conn.execute(
            "SELECT COUNT(*) AS n,COALESCE(SUM(contract_value),0) AS value FROM sales_outcomes WHERE outcome='won'"
        ).fetchone()
        losses = conn.execute(
            "SELECT COUNT(*) AS n FROM sales_outcomes WHERE outcome='lost'"
        ).fetchone()
        cash = conn.execute(
            "SELECT COALESCE(SUM(paid_amount),0) AS value FROM payment_links WHERE status='paid'"
        ).fetchone()
        open_links = conn.execute(
            "SELECT COUNT(*) AS n,COALESCE(SUM(amount),0) AS value FROM payment_links WHERE status NOT IN ('paid','cancelled','expired')"
        ).fetchone()
    return {
        "won_count": wins["n"],
        "won_value": wins["value"],
        "lost_count": losses["n"],
        "collected_value": cash["value"],
        "open_payment_links": open_links["n"],
        "open_payment_value": open_links["value"],
    }
