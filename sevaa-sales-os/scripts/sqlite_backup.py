from __future__ import annotations

import argparse
import sqlite3
import sys
import tempfile
from pathlib import Path


class BackupError(RuntimeError):
    pass


def integrity_check(path: Path) -> None:
    if not path.exists():
        raise BackupError(f"database does not exist: {path}")
    uri = f"file:{path.resolve()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True) as conn:
            row = conn.execute("PRAGMA integrity_check").fetchone()
    except sqlite3.Error as exc:
        raise BackupError(f"cannot open database {path}: {exc}") from exc
    if not row or row[0] != "ok":
        raise BackupError(f"database integrity check failed: {row[0] if row else 'no result'}")


def _backup_connection(source: Path, destination: Path) -> None:
    source_uri = f"file:{source.resolve()}?mode=ro"
    try:
        with sqlite3.connect(source_uri, uri=True) as src, sqlite3.connect(destination) as dst:
            src.backup(dst)
    except sqlite3.Error as exc:
        raise BackupError(str(exc)) from exc


def backup_database(source: Path, destination: Path) -> Path:
    source = source.expanduser()
    destination = destination.expanduser()
    integrity_check(source)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
        delete=False,
    ) as tmp:
        temp_path = Path(tmp.name)

    try:
        temp_path.unlink(missing_ok=True)
        _backup_connection(source, temp_path)
        integrity_check(temp_path)
        temp_path.replace(destination)
    finally:
        temp_path.unlink(missing_ok=True)
    return destination


def restore_database(backup: Path, target: Path) -> Path:
    backup = backup.expanduser()
    target = target.expanduser()
    integrity_check(backup)
    target.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        prefix=f".{target.name}.",
        suffix=".restore.tmp",
        dir=target.parent,
        delete=False,
    ) as tmp:
        temp_path = Path(tmp.name)

    try:
        temp_path.unlink(missing_ok=True)
        _backup_connection(backup, temp_path)
        integrity_check(temp_path)
        temp_path.replace(target)
    finally:
        temp_path.unlink(missing_ok=True)
    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Integrity-checked SEVAA SQLite backup/restore")
    sub = parser.add_subparsers(dest="command", required=True)

    backup = sub.add_parser("backup")
    backup.add_argument("source", type=Path)
    backup.add_argument("destination", type=Path)

    restore = sub.add_parser("restore")
    restore.add_argument("backup", type=Path)
    restore.add_argument("target", type=Path)
    restore.add_argument(
        "--confirm-stop-app-first",
        action="store_true",
        help="Required acknowledgement: restore must not replace a database while the app is writing to it.",
    )

    check = sub.add_parser("check")
    check.add_argument("database", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "backup":
            path = backup_database(args.source, args.destination)
            print(path)
        elif args.command == "restore":
            if not args.confirm_stop_app_first:
                raise BackupError("restore requires --confirm-stop-app-first")
            path = restore_database(args.backup, args.target)
            print(path)
        elif args.command == "check":
            integrity_check(args.database)
            print("ok")
    except BackupError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
