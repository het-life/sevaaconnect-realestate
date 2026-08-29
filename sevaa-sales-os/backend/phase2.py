from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timezone
from typing import Literal

from fastapi import Depends, Header, HTTPException
from pydantic import BaseModel, Field

import backend.app as base

_original_init_db = base.init_db


def init_phase2_db() -> None:
    _original_init_db()
    with base.db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS ingestion_keys (
                idempotency_key TEXT PRIMARY KEY,
                payload_hash TEXT NOT NULL,
                lead_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                scope_summary TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS approvals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                object_type TEXT NOT NULL,
                object_id INTEGER NOT NULL,
                lead_id INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',
                note TEXT,
                requested_at TEXT NOT NULL,
                resolved_at TEXT,
                UNIQUE(object_type, object_id),
                FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE SET NULL
            );
            CREATE TABLE IF NOT EXISTS followups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                due_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                channel TEXT NOT NULL DEFAULT 'manual',
                draft_message TEXT,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                completion_note TEXT,
                FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
            CREATE INDEX IF NOT EXISTS idx_followups_status_due ON followups(status,due_at);
            """
        )


base.init_db = init_phase2_db
app = base.app


class LeadCreateV2(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    company: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=160)
    city: str | None = Field(default=None, max_length=120)
    requirement: str = Field(min_length=3, max_length=1000)
    budget_min: int | None = Field(default=None, ge=0)
    budget_max: int | None = Field(default=None, ge=0)
    timeline_days: int | None = Field(default=None, ge=0, le=3650)
    known_buyer: bool = False
    site_ready: bool = False
    source: str = Field(default="manual", max_length=80)
    allow_duplicate: bool = False


class ProposalCreate(BaseModel):
    amount: int = Field(ge=0)
    scope_summary: str = Field(min_length=3, max_length=3000)


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    note: str | None = Field(default=None, max_length=1000)


class FollowupCreate(BaseModel):
    due_at: datetime
    draft_message: str | None = Field(default=None, max_length=3000)
    channel: Literal["manual", "email", "whatsapp", "phone"] = "manual"


class FollowupComplete(BaseModel):
    note: str | None = Field(default=None, max_length=1000)


class ActorContext(BaseModel):
    actor_id: str
    role: Literal["founder", "automation"]
    auth_mode: Literal["local", "token"]


def resolve_actor(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_actor: str | None = Header(default=None, alias="X-Actor"),
) -> ActorContext:
    founder_token = os.getenv("SEVAA_FOUNDER_TOKEN")
    automation_token = os.getenv("SEVAA_AUTOMATION_TOKEN")
    if not founder_token and not automation_token:
        return ActorContext(actor_id=x_actor or "local-founder", role="founder", auth_mode="local")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "bearer token required")
    token = authorization.split(" ", 1)[1].strip()
    if founder_token and secrets.compare_digest(token, founder_token):
        return ActorContext(actor_id=x_actor or "founder", role="founder", auth_mode="token")
    if automation_token and secrets.compare_digest(token, automation_token):
        return ActorContext(actor_id=x_actor or "automation", role="automation", auth_mode="token")
    raise HTTPException(401, "invalid bearer token")


def require_founder(actor: ActorContext = Depends(resolve_actor)) -> ActorContext:
    if actor.role != "founder":
        raise HTTPException(403, "founder role required")
    return actor


def normalized_phone(value: str | None) -> str | None:
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    return digits[-10:] if len(digits) >= 10 else digits or None


def normalized_email(value: str | None) -> str | None:
    return value.strip().lower() if value else None


def payload_hash(payload: LeadCreateV2) -> str:
    body = payload.model_dump(exclude={"allow_duplicate"})
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def duplicate_candidate(conn, payload: LeadCreateV2):
    phone = normalized_phone(payload.phone)
    email = normalized_email(payload.email)
    company = (payload.company or "").strip().lower()
    requirement = re.sub(r"\s+", " ", payload.requirement.strip().lower())
    for row in conn.execute("SELECT * FROM leads ORDER BY id DESC LIMIT 250").fetchall():
        if email and normalized_email(row["email"]) == email:
            return row
        if phone and normalized_phone(row["phone"]) == phone:
            return row
        same_company = bool(company) and (row["company"] or "").strip().lower() == company
        same_requirement = re.sub(r"\s+", " ", row["requirement"].strip().lower()) == requirement
        if same_company and same_requirement:
            return row
    return None


def as_base_lead(payload: LeadCreateV2) -> base.LeadCreate:
    data = payload.model_dump(exclude={"allow_duplicate"})
    fields = getattr(base.LeadCreate, "model_fields", {})
    return base.LeadCreate(**{k: v for k, v in data.items() if k in fields})


def followup_dict(row) -> dict:
    out = dict(row)
    if out["status"] == "completed":
        out["state"] = "completed"
    else:
        due = datetime.fromisoformat(out["due_at"].replace("Z", "+00:00"))
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        out["state"] = "overdue" if due < datetime.now(timezone.utc) else "pending"
    return out


@app.get("/api/v2/auth/me")
def auth_me(actor: ActorContext = Depends(resolve_actor)):
    return actor.model_dump()


@app.post("/api/v2/leads", status_code=201)
def create_lead_v2(
    payload: LeadCreateV2,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    actor: ActorContext = Depends(resolve_actor),
):
    init_phase2_db()
    digest = payload_hash(payload)
    ts = base.now_iso()
    with base.db() as conn:
        if idempotency_key:
            replay = conn.execute("SELECT * FROM ingestion_keys WHERE idempotency_key=?", (idempotency_key,)).fetchone()
            if replay:
                if replay["payload_hash"] != digest:
                    raise HTTPException(409, "idempotency key reused with different payload")
                row = conn.execute("SELECT * FROM leads WHERE id=?", (replay["lead_id"],)).fetchone()
                result = base.lead_dict(row)
                result["idempotent_replay"] = True
                return result

        if not payload.allow_duplicate:
            duplicate = duplicate_candidate(conn, payload)
            if duplicate:
                raise HTTPException(409, detail={
                    "code": "duplicate_lead",
                    "message": "possible duplicate lead",
                    "existing_lead_id": duplicate["id"],
                    "existing_name": duplicate["name"],
                })

        base_payload = as_base_lead(payload)
        score = base.score_lead(base_payload)
        stage = base.stage_for_score(score)
        cur = conn.execute(
            """INSERT INTO leads(name,company,phone,email,city,requirement,budget_min,budget_max,timeline_days,known_buyer,site_ready,source,score,stage,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (payload.name, payload.company, payload.phone, payload.email, payload.city, payload.requirement,
             payload.budget_min, payload.budget_max, payload.timeline_days, int(payload.known_buyer), int(payload.site_ready),
             payload.source, score, stage, ts, ts),
        )
        lead_id = int(cur.lastrowid)
        if idempotency_key:
            conn.execute(
                "INSERT INTO ingestion_keys(idempotency_key,payload_hash,lead_id,created_at) VALUES(?,?,?,?)",
                (idempotency_key, digest, lead_id, ts),
            )
        base.audit(conn, lead_id, "lead.created", f"Lead created from {payload.source}; score={score}; stage={stage}", actor.actor_id)
        row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    return base.lead_dict(row)


@app.post("/api/v2/leads/{lead_id}/proposals", status_code=201)
def create_proposal(lead_id: int, payload: ProposalCreate, actor: ActorContext = Depends(resolve_actor)):
    init_phase2_db()
    ts = base.now_iso()
    with base.db() as conn:
        lead = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        if lead is None:
            raise HTTPException(404, "lead not found")
        cur = conn.execute(
            "INSERT INTO proposals(lead_id,amount,scope_summary,status,created_at,updated_at) VALUES(?,?,?,?,?,?)",
            (lead_id, payload.amount, payload.scope_summary, "draft", ts, ts),
        )
        proposal_id = int(cur.lastrowid)
        if lead["stage"] not in ("won", "lost"):
            conn.execute("UPDATE leads SET stage='proposal',updated_at=? WHERE id=?", (ts, lead_id))
        base.audit(conn, lead_id, "proposal.created", f"Proposal #{proposal_id} draft created for ₹{payload.amount}", actor.actor_id)
        proposal = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
    return dict(proposal)


@app.post("/api/v2/proposals/{proposal_id}/submit")
def submit_proposal(proposal_id: int, actor: ActorContext = Depends(resolve_actor)):
    init_phase2_db()
    ts = base.now_iso()
    with base.db() as conn:
        proposal = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        if proposal is None:
            raise HTTPException(404, "proposal not found")
        if proposal["status"] == "pending_approval":
            approval = conn.execute("SELECT * FROM approvals WHERE object_type='proposal' AND object_id=?", (proposal_id,)).fetchone()
            return {"proposal": dict(proposal), "approval": dict(approval)}
        if proposal["status"] != "draft":
            raise HTTPException(409, f"proposal cannot be submitted from {proposal['status']}")
        conn.execute("UPDATE proposals SET status='pending_approval',updated_at=? WHERE id=?", (ts, proposal_id))
        cur = conn.execute(
            "INSERT INTO approvals(object_type,object_id,lead_id,status,requested_at) VALUES('proposal',?,?,'pending',?)",
            (proposal_id, proposal["lead_id"], ts),
        )
        approval_id = int(cur.lastrowid)
        base.audit(conn, proposal["lead_id"], "proposal.approval_requested", f"Proposal #{proposal_id} requires founder approval", actor.actor_id)
        proposal = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        approval = conn.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
    return {"proposal": dict(proposal), "approval": dict(approval)}


@app.get("/api/v2/approvals")
def list_approvals(status: str = "pending", actor: ActorContext = Depends(resolve_actor)):
    if status not in ("pending", "approved", "rejected", "all"):
        raise HTTPException(400, "invalid approval status")
    init_phase2_db()
    with base.db() as conn:
        query = """SELECT a.*,p.amount,p.scope_summary,p.status AS proposal_status,
                          l.name AS lead_name,l.company AS lead_company
                   FROM approvals a
                   JOIN proposals p ON a.object_type='proposal' AND p.id=a.object_id
                   LEFT JOIN leads l ON l.id=a.lead_id"""
        args = ()
        if status != "all":
            query += " WHERE a.status=?"
            args = (status,)
        query += " ORDER BY a.id DESC"
        rows = conn.execute(query, args).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/v2/approvals/{approval_id}/decision")
def decide_approval(approval_id: int, payload: ApprovalDecision, actor: ActorContext = Depends(require_founder)):
    init_phase2_db()
    ts = base.now_iso()
    with base.db() as conn:
        approval = conn.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
        if approval is None:
            raise HTTPException(404, "approval not found")
        if approval["status"] != "pending":
            raise HTTPException(409, "approval already resolved")
        conn.execute("UPDATE approvals SET status=?,note=?,resolved_at=? WHERE id=?", (payload.decision, payload.note, ts, approval_id))
        conn.execute("UPDATE proposals SET status=?,updated_at=? WHERE id=?", (payload.decision, ts, approval["object_id"]))
        base.audit(conn, approval["lead_id"], "approval.resolved", f"proposal #{approval['object_id']} {payload.decision}", actor.actor_id)
        resolved = conn.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
    return dict(resolved)


@app.post("/api/v2/leads/{lead_id}/followups", status_code=201)
def create_followup(lead_id: int, payload: FollowupCreate, actor: ActorContext = Depends(resolve_actor)):
    init_phase2_db()
    ts = base.now_iso()
    due = payload.due_at if payload.due_at.tzinfo else payload.due_at.replace(tzinfo=timezone.utc)
    due_iso = due.astimezone(timezone.utc).isoformat()
    with base.db() as conn:
        lead = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        if lead is None:
            raise HTTPException(404, "lead not found")
        cur = conn.execute(
            """INSERT INTO followups(lead_id,due_at,status,channel,draft_message,created_by,created_at)
               VALUES(?,?,'pending',?,?,?,?)""",
            (lead_id, due_iso, payload.channel, payload.draft_message, actor.actor_id, ts),
        )
        followup_id = int(cur.lastrowid)
        if lead["stage"] not in ("won", "lost"):
            conn.execute("UPDATE leads SET stage='follow_up',updated_at=? WHERE id=?", (ts, lead_id))
        base.audit(conn, lead_id, "followup.scheduled", f"Follow-up #{followup_id} due {due_iso} via {payload.channel}", actor.actor_id)
        row = conn.execute("SELECT f.*,l.name AS lead_name,l.company AS lead_company FROM followups f JOIN leads l ON l.id=f.lead_id WHERE f.id=?", (followup_id,)).fetchone()
    return followup_dict(row)


@app.get("/api/v2/followups")
def list_followups(state: str = "all", actor: ActorContext = Depends(resolve_actor)):
    if state not in ("all", "pending", "overdue", "completed"):
        raise HTTPException(400, "invalid follow-up state")
    init_phase2_db()
    with base.db() as conn:
        rows = conn.execute(
            """SELECT f.*,l.name AS lead_name,l.company AS lead_company
               FROM followups f JOIN leads l ON l.id=f.lead_id ORDER BY f.due_at ASC,f.id ASC"""
        ).fetchall()
    items = [followup_dict(row) for row in rows]
    return items if state == "all" else [x for x in items if x["state"] == state]


@app.post("/api/v2/followups/{followup_id}/complete")
def complete_followup(followup_id: int, payload: FollowupComplete, actor: ActorContext = Depends(resolve_actor)):
    init_phase2_db()
    ts = base.now_iso()
    with base.db() as conn:
        row = conn.execute("SELECT * FROM followups WHERE id=?", (followup_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "follow-up not found")
        if row["status"] == "completed":
            raise HTTPException(409, "follow-up already completed")
        conn.execute("UPDATE followups SET status='completed',completed_at=?,completion_note=? WHERE id=?", (ts, payload.note, followup_id))
        base.audit(conn, row["lead_id"], "followup.completed", f"Follow-up #{followup_id} completed", actor.actor_id)
        updated = conn.execute("SELECT f.*,l.name AS lead_name,l.company AS lead_company FROM followups f JOIN leads l ON l.id=f.lead_id WHERE f.id=?", (followup_id,)).fetchone()
    return followup_dict(updated)


@app.get("/api/v2/dashboard")
def dashboard_v2(actor: ActorContext = Depends(resolve_actor)):
    init_phase2_db()
    with base.db() as conn:
        leads = [base.lead_dict(r) for r in conn.execute("SELECT * FROM leads ORDER BY score DESC,id DESC").fetchall()]
        pending = [dict(r) for r in conn.execute(
            """SELECT a.*,p.amount,p.scope_summary,l.name AS lead_name,l.company AS lead_company
               FROM approvals a JOIN proposals p ON p.id=a.object_id LEFT JOIN leads l ON l.id=a.lead_id
               WHERE a.object_type='proposal' AND a.status='pending' ORDER BY a.id DESC"""
        ).fetchall()]
        followups = [followup_dict(r) for r in conn.execute(
            """SELECT f.*,l.name AS lead_name,l.company AS lead_company FROM followups f JOIN leads l ON l.id=f.lead_id
               WHERE f.status='pending' ORDER BY f.due_at ASC"""
        ).fetchall()]
        audits = [dict(r) for r in conn.execute(
            """SELECT a.*,l.name AS lead_name FROM audit_events a LEFT JOIN leads l ON l.id=a.lead_id ORDER BY a.id DESC LIMIT 8"""
        ).fetchall()]
        proposal_count = conn.execute("SELECT COUNT(*) AS n FROM proposals").fetchone()["n"]
    stages = {s: [] for s in base.STAGES}
    for lead in leads:
        stages[lead["stage"]].append(lead)
    qualified = sum(1 for x in leads if x["score"] >= 70 and x["stage"] != "lost")
    overdue = sum(1 for x in followups if x["state"] == "overdue")
    pipeline_min = sum((x["budget_min"] or 0) for x in leads if x["stage"] not in ("lost", "won"))
    pipeline_max = sum((x["budget_max"] or x["budget_min"] or 0) for x in leads if x["stage"] not in ("lost", "won"))
    return {
        "kpis": {
            "lead_count": len(leads),
            "qualified": qualified,
            "proposals": proposal_count,
            "pending_approvals": len(pending),
            "pending_followups": len(followups),
            "overdue_followups": overdue,
            "founder_attention": len(pending) + overdue,
            "pipeline_min": pipeline_min,
            "pipeline_max": pipeline_max,
        },
        "stages": stages,
        "pending_approvals": pending,
        "followups": followups[:8],
        "audit": audits,
    }


@app.get("/api/v2/internal/daily-brief")
def daily_brief(actor: ActorContext = Depends(resolve_actor)):
    data = dashboard_v2(actor)
    k = data["kpis"]
    return {
        "actor": actor.model_dump(),
        "new_leads": len(data["stages"]["new"]),
        "high_score_leads": k["qualified"],
        "proposals": k["proposals"],
        "proposals_awaiting_approval": k["pending_approvals"],
        "pending_followups": k["pending_followups"],
        "overdue_followups": k["overdue_followups"],
        "pipeline_min": k["pipeline_min"],
        "pipeline_max": k["pipeline_max"],
        "founder_attention": k["founder_attention"],
        "system_failures": 0,
    }
