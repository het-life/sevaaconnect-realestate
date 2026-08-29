from __future__ import annotations

import os
from pathlib import Path

APP_UID = 10001
APP_GID = 10001


def resolve_port() -> int:
    raw = (os.getenv("PORT") or os.getenv("SEVAA_PORT") or "8000").strip()
    try:
        port = int(raw)
    except ValueError as exc:
        raise SystemExit(f"invalid application port: {raw!r}") from exc
    if not 1 <= port <= 65535:
        raise SystemExit(f"application port out of range: {port}")
    return port


def prepare_database_permissions() -> None:
    db_path = Path(os.getenv("SEVAA_DB_PATH", "/data/sevaa.db")).expanduser().resolve()
    parent = db_path.parent
    parent.mkdir(parents=True, exist_ok=True)

    if os.geteuid() != 0:
        return

    # Persistent volumes are commonly mounted root-owned. Take ownership only
    # of the configured database directory and known SQLite sidecar files,
    # then permanently drop privileges before starting the web server.
    os.chown(parent, APP_UID, APP_GID)
    for candidate in (
        db_path,
        Path(f"{db_path}-wal"),
        Path(f"{db_path}-shm"),
        Path(f"{db_path}-journal"),
    ):
        if candidate.exists():
            os.chown(candidate, APP_UID, APP_GID)

    os.setgroups([])
    os.setgid(APP_GID)
    os.setuid(APP_UID)


def main() -> None:
    port = resolve_port()
    prepare_database_permissions()
    os.execvp(
        "python",
        [
            "python",
            "-m",
            "uvicorn",
            "backend.runtime:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
        ],
    )


if __name__ == "__main__":
    main()
