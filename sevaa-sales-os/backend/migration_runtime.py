"""Runtime migration binding for the hardened application.

The older modules retain their bootstrap helpers for compatibility, but the
hardened runtime binds every initializer to the versioned migration engine so
schema creation has one source of truth.
"""

from backend.migrations import apply_migrations
import backend.app as base
import backend.phase2 as phase2
import backend.proposal_artifacts as proposal_artifacts


def init_runtime_db() -> None:
    with base.db() as conn:
        apply_migrations(conn)


base.init_db = init_runtime_db
phase2.init_phase2_db = init_runtime_db
proposal_artifacts.init_phase2_db = init_runtime_db
proposal_artifacts.init_artifact_db = init_runtime_db

__all__ = ["init_runtime_db"]
