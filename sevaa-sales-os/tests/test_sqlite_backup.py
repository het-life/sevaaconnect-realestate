import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.sqlite_backup import backup_database, integrity_check, restore_database


def test_backup_and_restore_round_trip(tmp_path):
    source = tmp_path / "source.db"
    backup = tmp_path / "backups" / "snapshot.db"
    restored = tmp_path / "restored.db"

    with sqlite3.connect(source) as conn:
        conn.execute("CREATE TABLE events(id INTEGER PRIMARY KEY, note TEXT NOT NULL)")
        conn.execute("INSERT INTO events(note) VALUES(?)", ("verified-before-backup",))

    backup_database(source, backup)
    integrity_check(backup)

    with sqlite3.connect(source) as conn:
        conn.execute("INSERT INTO events(note) VALUES(?)", ("after-backup",))

    restore_database(backup, restored)
    integrity_check(restored)

    with sqlite3.connect(restored) as conn:
        rows = conn.execute("SELECT note FROM events ORDER BY id").fetchall()

    assert rows == [("verified-before-backup",)]
