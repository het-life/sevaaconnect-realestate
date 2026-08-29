from __future__ import annotations

import os
import re
from contextlib import contextmanager
from typing import Any


_POSTGRES_PREFIXES = ("postgresql://", "postgres://")
_AUTO_ID = re.compile(r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b", re.IGNORECASE)


def configured_database_url() -> str:
    return os.getenv("SEVAA_DATABASE_URL", "").strip()


def is_postgres_url(value: str | None = None) -> bool:
    url = configured_database_url() if value is None else value.strip()
    return url.startswith(_POSTGRES_PREFIXES)


def database_backend() -> str:
    return "postgresql" if is_postgres_url() else "sqlite"


def _postgres_sql(sql: str) -> str:
    """Translate the small SQLite-flavoured SQL subset used by this project."""
    return sql.replace("?", "%s")


def _postgres_ddl(sql: str) -> str:
    # All generated IDs are INTEGER in the existing schema, so SERIAL preserves
    # foreign-key type compatibility while providing PostgreSQL sequences.
    return _AUTO_ID.sub("SERIAL PRIMARY KEY", sql)


class PostgresCursor:
    def __init__(self, cursor, connection) -> None:
        self._cursor = cursor
        self._connection = connection

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    @property
    def lastrowid(self) -> int:
        # Existing route code reads lastrowid immediately after inserts into
        # SERIAL-backed tables. lastval() returns that session's latest sequence
        # value without requiring every route to grow PostgreSQL-specific SQL.
        with self._connection.cursor() as cursor:
            cursor.execute("SELECT LASTVAL() AS id")
            row = cursor.fetchone()
        return int(row["id"])


class PostgresConnection:
    dialect = "postgresql"

    def __init__(self, connection) -> None:
        self._connection = connection

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> PostgresCursor:
        cursor = self._connection.cursor()
        cursor.execute(_postgres_sql(sql), params)
        return PostgresCursor(cursor, self._connection)

    def executescript(self, script: str) -> None:
        # Migration scripts contain plain CREATE TABLE/INDEX statements only;
        # splitting at semicolons keeps psycopg on one statement per execute.
        translated = _postgres_ddl(script)
        with self._connection.cursor() as cursor:
            for statement in translated.split(";"):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()


@contextmanager
def postgres_db(url: str | None = None):
    target = configured_database_url() if url is None else url.strip()
    if not is_postgres_url(target):
        raise RuntimeError("SEVAA_DATABASE_URL must use postgresql:// or postgres://")
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:  # pragma: no cover - dependency is installed in deployment/CI
        raise RuntimeError("PostgreSQL support requires psycopg[binary]") from exc

    connection = psycopg.connect(target, row_factory=dict_row)
    wrapped = PostgresConnection(connection)
    try:
        yield wrapped
        wrapped.commit()
    except Exception:
        wrapped.rollback()
        raise
    finally:
        wrapped.close()
