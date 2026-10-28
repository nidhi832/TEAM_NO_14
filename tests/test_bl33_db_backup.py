"""BL-33: backup can be restored and the restored database is valid."""
import sqlite3

from scripts.db_backup import backup_database, restore_database


def test_backup_and_restore_round_trip(tmp_path):
    source = tmp_path / "source.db"
    backup_dir = tmp_path / "backups"
    restored = tmp_path / "restored.db"
    with sqlite3.connect(source) as conn:
        conn.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO sample(value) VALUES (?)", ("preserved",))

    backup = backup_database(source, backup_dir, timestamp="test")
    assert backup.exists()
    with sqlite3.connect(source) as conn:
        conn.execute("UPDATE sample SET value='changed'")
    restore_database(backup, restored)

    with sqlite3.connect(restored) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("SELECT value FROM sample").fetchone()[0] == "preserved"


def test_missing_database_fails_clearly(tmp_path):
    try:
        backup_database(tmp_path / "missing.db", tmp_path / "backups")
    except FileNotFoundError as exc:
        assert "Database not found" in str(exc)
    else:
        raise AssertionError("Expected a missing database to fail")


def test_restore_rejects_same_source_and_destination(tmp_path):
    source = tmp_path / "backup.db"
    with sqlite3.connect(source) as conn:
        conn.execute("CREATE TABLE sample (id INTEGER)")
    try:
        restore_database(source, source)
    except ValueError as exc:
        assert "different files" in str(exc)
    else:
        raise AssertionError("Expected same-path restore to fail")
