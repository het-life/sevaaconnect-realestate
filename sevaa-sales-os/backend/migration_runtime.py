"""Runtime database binding for the hardened application.

SQLite remains the zero-configuration local default. When
SEVAA_DATABASE_URL points at PostgreSQL, the same hardened route code runs
through a small DB-API compatibility adapter. Core workflow migrations are
eagerly applied through v3; revenue v4 remains lazy-applied by backend.revenue.
"""

from contextlib import contextmanager

from backend.database import is_postgres_url, postgres_db
from backend.migrations import apply_migrations
import backend.app as base
import backend.phase2 as phase2
import backend.proposal_artifacts as proposal_artifacts

_sqlite_db = base.db


@contextmanager
def runtime_db():
    if is_postgres_url():
        with postgres_db() as conn:
            yield conn
        return
    with _sqlite_db() as conn:
        yield conn


def init_runtime_db() -> None:
    with base.db() as conn:
        apply_migrations(conn, max_version=3)


base.db = runtime_db
base.init_db = init_runtime_db
phase2.init_phase2_db = init_runtime_db
proposal_artifacts.init_phase2_db = init_runtime_db
proposal_artifacts.init_artifact_db = init_runtime_db

__all__ = ["init_runtime_db", "runtime_db"]
