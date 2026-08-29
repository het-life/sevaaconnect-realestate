from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("SEVAA_DB_PATH", ROOT / "data" / "sevaa.db"))
WEB_DIR = ROOT / "web"

STAGES = ("new", "qualified", "proposal", "follow_up", "won", "lost")


class LeadCreate(BaseModel):
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


class StageUpdate(BaseModel):
    stage: Literal["new", "qualified", "proposal", "follow_up", "won", "lost"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                company TEXT,
                phone TEXT,
                email TEXT,
                city TEXT,
                requirement TEXT NOT NULL,
                budget_min INTEGER,
                budget_max INTEGER,
                timeline_days INTEGER,
                known_buyer INTEGER NOT NULL DEFAULT 0,
                site_ready INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT 'manual',
                score INTEGER NOT NULL,
                stage TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER,
                event_type TEXT NOT NULL,
                detail TEXT NOT NULL,
                actor TEXT NOT NULL DEFAULT 'system',
                created_at TEXT NOT NULL,
                FOREIGN KEY(lead_id) REFERENCES leads(id) ON DELETE SET NULL
            );
            """
        )


def score_lead(payload: LeadCreate) -> int:
    score = 25
    req = payload.requirement.lower()
    if payload.budget_min is not None or payload.budget_max is not None:
        score += 15
    if payload.timeline_days is not None:
        if payload.timeline_days <= 30:
            score += 18
        elif payload.timeline_days <= 90:
            score += 12
        elif payload.timeline_days <= 180:
            score += 6
    if payload.known_buyer:
        score += 20
    if payload.site_ready:
        score += 10
    if payload.phone or payload.email:
        score += 5
    if any(k in req for k in ("modular", "prefab", "container", "cafe", "site office", "shop", "resort")):
        score += 7
    return max(0, min(100, score))


def stage_for_score(score: int) -> str:
    return "qualified" if score >= 70 else "new"


def audit(conn: sqlite3.Connection, lead_id: int | None, event_type: str, detail: str, actor: str = "system") -> None:
    conn.execute(
        "INSERT INTO audit_events(lead_id,event_type,detail,actor,created_at) VALUES(?,?,?,?,?)",
        (lead_id, event_type, detail, actor, now_iso()),
    )


def lead_dict(row: sqlite3.Row) -> dict:
    out = dict(row)
    out["known_buyer"] = bool(out["known_buyer"])
    out["site_ready"] = bool(out["site_ready"])
    return out


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="SEVAA Sales OS API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    init_db()
    with db() as conn:
        conn.execute("SELECT 1").fetchone()
    return {"status": "ok", "database": str(DB_PATH.name), "time": now_iso()}


@app.post("/api/leads", status_code=201)
def create_lead(payload: LeadCreate):
    score = score_lead(payload)
    stage = stage_for_score(score)
    ts = now_iso()
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO leads(name,company,phone,email,city,requirement,budget_min,budget_max,timeline_days,known_buyer,site_ready,source,score,stage,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (payload.name, payload.company, payload.phone, payload.email, payload.city, payload.requirement,
             payload.budget_min, payload.budget_max, payload.timeline_days, int(payload.known_buyer), int(payload.site_ready),
             payload.source, score, stage, ts, ts),
        )
        lead_id = int(cur.lastrowid)
        audit(conn, lead_id, "lead.created", f"Lead created from {payload.source}; score={score}; stage={stage}", "api")
        row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    return lead_dict(row)


@app.get("/api/leads")
def list_leads(stage: str | None = None):
    with db() as conn:
        if stage:
            if stage not in STAGES:
                raise HTTPException(400, "invalid stage")
            rows = conn.execute("SELECT * FROM leads WHERE stage=? ORDER BY score DESC, id DESC", (stage,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM leads ORDER BY score DESC, id DESC").fetchall()
    return [lead_dict(r) for r in rows]


@app.patch("/api/leads/{lead_id}/stage")
def update_stage(lead_id: int, payload: StageUpdate):
    with db() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "lead not found")
        previous = row["stage"]
        conn.execute("UPDATE leads SET stage=?, updated_at=? WHERE id=?", (payload.stage, now_iso(), lead_id))
        audit(conn, lead_id, "lead.stage_changed", f"{previous} -> {payload.stage}", "api")
        updated = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    return lead_dict(updated)


@app.get("/api/audit")
def list_audit(limit: int = 20):
    limit = max(1, min(limit, 100))
    with db() as conn:
        rows = conn.execute(
            """SELECT a.*, l.name AS lead_name FROM audit_events a
               LEFT JOIN leads l ON l.id=a.lead_id
               ORDER BY a.id DESC LIMIT ?""", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/dashboard")
def dashboard():
    with db() as conn:
        leads = [lead_dict(r) for r in conn.execute("SELECT * FROM leads ORDER BY score DESC, id DESC").fetchall()]
        audit_rows = [dict(r) for r in conn.execute(
            """SELECT a.*, l.name AS lead_name FROM audit_events a LEFT JOIN leads l ON l.id=a.lead_id
               ORDER BY a.id DESC LIMIT 8""").fetchall()]

    stages = {s: [] for s in STAGES}
    for lead in leads:
        stages[lead["stage"]].append(lead)
    qualified = sum(1 for x in leads if x["score"] >= 70 and x["stage"] not in ("lost",))
    proposals = len(stages["proposal"])
    founder_attention = len(stages["proposal"]) + sum(1 for x in stages["follow_up"] if x["score"] >= 70)
    pipeline_min = sum((x["budget_min"] or 0) for x in leads if x["stage"] not in ("lost", "won"))
    pipeline_max = sum((x["budget_max"] or x["budget_min"] or 0) for x in leads if x["stage"] not in ("lost", "won"))
    return {
        "kpis": {
            "lead_count": len(leads),
            "qualified": qualified,
            "proposals": proposals,
            "founder_attention": founder_attention,
            "pipeline_min": pipeline_min,
            "pipeline_max": pipeline_max,
        },
        "stages": stages,
        "audit": audit_rows,
    }


@app.post("/api/demo/seed")
def seed_demo():
    samples = [
        LeadCreate(name="Aster Organics", company="Aster Organics", city="Surat", requirement="Repeat modular retail shop unit", budget_min=850000, budget_max=900000, timeline_days=30, known_buyer=True, site_ready=True, source="demo"),
        LeadCreate(name="Riverstone Café", company="Riverstone Cafe", city="Surat", requirement="20ft modular cafe needs fast delivery", budget_min=600000, budget_max=800000, timeline_days=45, site_ready=True, source="demo"),
        LeadCreate(name="Northline Resorts", company="Northline Resorts", requirement="2-key prefab resort trial", budget_min=1800000, budget_max=2200000, timeline_days=90, site_ready=True, source="demo"),
    ]
    created = []
    with db() as conn:
        exists = conn.execute("SELECT COUNT(*) AS n FROM leads").fetchone()["n"]
    if exists:
        return {"created": 0, "message": "database already contains leads"}
    for sample in samples:
        created.append(create_lead(sample))
    return {"created": len(created), "leads": created}


if WEB_DIR.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")


@app.get("/")
def index():
    if not (WEB_DIR / "index.html").exists():
        raise HTTPException(404, "dashboard not built")
    return FileResponse(WEB_DIR / "index.html")
