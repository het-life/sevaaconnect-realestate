from __future__ import annotations

import hashlib
import json
import re
from typing import Literal

from fastapi import Header, HTTPException
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
            CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals(status);
            """
        )


# The existing FastAPI lifespan resolves this global at runtime, so replacing it
# keeps the original startup path and adds phase-2 tables without rewriting v1.
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
    return base.LeadCreate(**payload.model_dump(exclude={"allow_duplicate"}))


@app.post("/api/v2/leads", status_code=201)
def create_lead_v2(payload: LeadCreateV2, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    init_phase2_db()
    digest = payload_hash(payload)
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
                    "existing_lead_id": duplicate["id"],
                    "existing_name": duplicate["name"],
                })

    created = base.create_lead(as_base_lead(payload))
    if idempotency_key:
        with base.db() as conn:
            conn.execute(
                "INSERT INTO ingestion_keys(idempotency_key,payload_hash,lead_id,created_at) VALUES(?,?,?,?)",
                (idempotency_key, digest, created["id"], base.now_iso()),
            )
            base.audit(conn, created["id"], "lead.idempotency_bound", f"Bound inbound key {idempotency_key[:32]}", "api")
    return created


@app.post("/api/v2/leads/{lead_id}/proposals", status_code=201)
def create_proposal(lead_id: int, payload: ProposalCreate):
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
        base.audit(conn, lead_id, "proposal.created", f"Proposal #{proposal_id} draft created for ₹{payload.amount}", "api")
        proposal = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
    return dict(proposal)


@app.post("/api/v2/proposals/{proposal_id}/submit")
def submit_proposal(proposal_id: int):
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
        base.audit(conn, proposal["lead_id"], "proposal.approval_requested", f"Proposal #{proposal_id} requires founder approval", "system")
        proposal = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        approval = conn.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
    return {"proposal": dict(proposal), "approval": dict(approval)}


@app.get("/api/v2/approvals")
def list_approvals(status: str = "pending"):
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
def decide_approval(approval_id: int, payload: ApprovalDecision):
    init_phase2_db()
    ts = base.now_iso()
    with base.db() as conn:
        approval = conn.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
        if approval is None:
            raise HTTPException(404, "approval not found")
        if approval["status"] != "pending":
            raise HTTPException(409, "approval already resolved")
        conn.execute(
            "UPDATE approvals SET status=?,note=?,resolved_at=? WHERE id=?",
            (payload.decision, payload.note, ts, approval_id),
        )
        conn.execute(
            "UPDATE proposals SET status=?,updated_at=? WHERE id=?",
            (payload.decision, ts, approval["object_id"]),
        )
        base.audit(conn, approval["lead_id"], "approval.resolved", f"proposal #{approval['object_id']} {payload.decision}", "founder")
        resolved = conn.execute("SELECT * FROM approvals WHERE id=?", (approval_id,)).fetchone()
    return dict(resolved)


@app.get("/api/v2/dashboard")
def dashboard_v2():
    init_phase2_db()
    base_dashboard = base.dashboard()
    with base.db() as conn:
        pending = [dict(row) for row in conn.execute(
            """SELECT a.*,p.amount,p.scope_summary,l.name AS lead_name,l.company AS lead_company
               FROM approvals a JOIN proposals p ON p.id=a.object_id
               LEFT JOIN leads l ON l.id=a.lead_id
               WHERE a.object_type='proposal' AND a.status='pending' ORDER BY a.id DESC"""
        ).fetchall()]
        proposal_count = conn.execute("SELECT COUNT(*) AS n FROM proposals").fetchone()["n"]
    result = dict(base_dashboard)
    result["pending_approvals"] = pending
    result["kpis"] = dict(result["kpis"])
    result["kpis"]["proposals"] = proposal_count
    result["kpis"]["pending_approvals"] = len(pending)
    result["kpis"]["founder_attention"] = result["kpis"]["founder_attention"] + len(pending)
    return result
