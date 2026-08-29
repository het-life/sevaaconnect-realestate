from __future__ import annotations

from fastapi import Depends, HTTPException, Response

from backend.phase2 import ActorContext, app, base, init_phase2_db, resolve_actor


def init_artifact_db() -> None:
    init_phase2_db()
    with base.db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS proposal_artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id INTEGER NOT NULL UNIQUE,
                format TEXT NOT NULL DEFAULT 'markdown',
                content TEXT NOT NULL,
                status_snapshot TEXT NOT NULL,
                generated_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(proposal_id) REFERENCES proposals(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_artifacts_proposal
                ON proposal_artifacts(proposal_id);
            """
        )


def proposal_markdown(proposal, lead) -> str:
    approved = proposal["status"] == "approved"
    banner = "APPROVED FOR INTERNAL USE" if approved else "DRAFT — NOT APPROVED FOR EXTERNAL USE"
    amount = f"₹{int(proposal['amount']):,}"
    client = lead["name"]
    company = lead["company"] or "—"
    city = lead["city"] or "—"
    requirement = lead["requirement"]
    scope = proposal["scope_summary"]
    return (
        f"# SEVAA Proposal #{proposal['id']}\n\n"
        f"**{banner}**\n\n"
        "## Client\n"
        f"- Contact: {client}\n"
        f"- Company: {company}\n"
        f"- City: {city}\n\n"
        f"## Requirement\n{requirement}\n\n"
        f"## Proposed Scope\n{scope}\n\n"
        "## Commercials\n"
        f"- Proposal amount: **{amount}**\n"
        f"- Approval status: **{proposal['status']}**\n\n"
        "## Control Note\n"
        "This document is generated only from fields already stored in SEVAA Sales OS. "
        "It does not add contractual terms, taxes, discounts, payment schedules or external commitments.\n"
    )


def artifact_dict(row) -> dict:
    return dict(row)


@app.post("/api/v2/proposals/{proposal_id}/artifact", status_code=201)
def generate_proposal_artifact(
    proposal_id: int,
    actor: ActorContext = Depends(resolve_actor),
):
    init_artifact_db()
    ts = base.now_iso()
    with base.db() as conn:
        proposal = conn.execute("SELECT * FROM proposals WHERE id=?", (proposal_id,)).fetchone()
        if proposal is None:
            raise HTTPException(404, "proposal not found")
        lead = conn.execute("SELECT * FROM leads WHERE id=?", (proposal["lead_id"],)).fetchone()
        content = proposal_markdown(proposal, lead)
        existing = conn.execute(
            "SELECT * FROM proposal_artifacts WHERE proposal_id=?", (proposal_id,)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE proposal_artifacts
                   SET content=?,status_snapshot=?,generated_by=?,updated_at=?
                   WHERE proposal_id=?""",
                (content, proposal["status"], actor.actor_id, ts, proposal_id),
            )
        else:
            conn.execute(
                """INSERT INTO proposal_artifacts(
                       proposal_id,format,content,status_snapshot,generated_by,created_at,updated_at
                   ) VALUES(?,'markdown',?,?,?,?,?)""",
                (proposal_id, content, proposal["status"], actor.actor_id, ts, ts),
            )
        base.audit(
            conn,
            proposal["lead_id"],
            "proposal.artifact_generated",
            f"Proposal #{proposal_id} markdown artifact generated at status={proposal['status']}",
            actor.actor_id,
        )
        row = conn.execute(
            "SELECT * FROM proposal_artifacts WHERE proposal_id=?", (proposal_id,)
        ).fetchone()
    return artifact_dict(row)


@app.get("/api/v2/proposals/{proposal_id}/artifact")
def get_proposal_artifact(
    proposal_id: int,
    actor: ActorContext = Depends(resolve_actor),
):
    init_artifact_db()
    with base.db() as conn:
        row = conn.execute(
            "SELECT * FROM proposal_artifacts WHERE proposal_id=?", (proposal_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(404, "proposal artifact not generated")
    return artifact_dict(row)


@app.get("/api/v2/proposals/{proposal_id}/artifact/download")
def download_proposal_artifact(
    proposal_id: int,
    actor: ActorContext = Depends(resolve_actor),
):
    init_artifact_db()
    with base.db() as conn:
        row = conn.execute(
            "SELECT * FROM proposal_artifacts WHERE proposal_id=?", (proposal_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(404, "proposal artifact not generated")
    filename = f"sevaa-proposal-{proposal_id}.md"
    return Response(
        content=row["content"],
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
