from __future__ import annotations

import sqlite3
from datetime import datetime, timezone


MIGRATIONS: tuple[tuple[int, str, str], ...] = (
    (
        1,
        "base_leads_and_audit",
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
        """,
    ),
    (
        2,
        "hardened_sales_workflow",
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
        """,
    ),
    (
        3,
        "proposal_artifacts",
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
        """,
    ),
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def apply_migrations(conn: sqlite3.Connection) -> list[int]:
    """Apply missing schema versions and return versions applied this call.

    Migrations use CREATE IF NOT EXISTS so an existing pre-migration SEVAA
    database can be adopted safely: existing tables are retained and the
    migration ledger is populated as each compatible version is observed.
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )
    applied = {
        row["version"] if isinstance(row, sqlite3.Row) else row[0]
        for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
    }
    newly_applied: list[int] = []
    for version, name, sql in MIGRATIONS:
        if version in applied:
            continue
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations(version,name,applied_at) VALUES(?,?,?)",
            (version, name, now_iso()),
        )
        newly_applied.append(version)
    return newly_applied
