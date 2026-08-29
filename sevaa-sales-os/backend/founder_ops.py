from __future__ import annotations

from fastapi import Depends, HTTPException

from backend.phase2 import ActorContext, app, base, init_phase2_db, resolve_actor
from backend.app import StageUpdate


@app.patch("/api/v2/leads/{lead_id}/stage")
def update_stage_v2(
    lead_id: int,
    payload: StageUpdate,
    actor: ActorContext = Depends(resolve_actor),
):
    init_phase2_db()
    with base.db() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "lead not found")
        previous = row["stage"]
        conn.execute(
            "UPDATE leads SET stage=?, updated_at=? WHERE id=?",
            (payload.stage, base.now_iso(), lead_id),
        )
        base.audit(
            conn,
            lead_id,
            "lead.stage_changed",
            f"{previous} -> {payload.stage}",
            actor.actor_id,
        )
        updated = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    return base.lead_dict(updated)
