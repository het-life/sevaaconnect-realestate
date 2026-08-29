"""Runtime migration binding for the hardened application.

Core runtime eagerly applies stable workflow migrations through v3. Revenue v4
is lazy-applied by backend.revenue immediately before revenue/payment routes are
used, which preserves compatibility with older branch tests and databases.
"""

from backend.migrations import apply_migrations
import backend.app as base
import backend.phase2 as phase2
import backend.proposal_artifacts as proposal_artifacts


def init_runtime_db() -> None:
    with base.db() as conn:
        apply_migrations(conn, max_version=3)


base.init_db = init_runtime_db
phase2.init_phase2_db = init_runtime_db
proposal_artifacts.init_phase2_db = init_runtime_db
proposal_artifacts.init_artifact_db = init_runtime_db

__all__ = ["init_runtime_db"]
