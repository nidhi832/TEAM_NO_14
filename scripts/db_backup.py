"""SQLite backup/restore utility for BL-33.

Usage:
  python scripts/db_backup.py backup [--output-dir backups]
  python scripts/db_backup.py restore path/to/backup.db [--database path/to/mpms.db]

Schedule the backup command daily with Windows Task Scheduler or cron.
"""
import argparse
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse


def sqlite_path(database_uri):
    """Resolve a SQLite URI to a filesystem path; reject other DB engines."""
    if not database_uri.startswith("sqlite:///"):
        raise ValueError("Backup utility currently supports SQLite databases only.")
    raw = database_uri[len("sqlite:///"):]
    if raw == ":memory:":
        raise ValueError("In-memory databases cannot be backed up by this utility.")
    path = Path(unquote(raw))
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def backup_database(source, output_dir="backups", timestamp=None):
    source = Path(source).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Database not found: {source}")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = output / f"mpms_{stamp}.db"

    # SQLite's backup API safely snapshots a live database, including WAL data.
    with sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True) as src:
        with sqlite3.connect(destination) as dst:
            src.backup(dst)
            result = dst.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise RuntimeError(f"Backup integrity check failed: {result}")

    return destination


def restore_database(backup, destination):
    backup = Path(backup).resolve()
    destination = Path(destination).resolve()

    if not backup.is_file():
        raise FileNotFoundError(f"Backup not found: {backup}")
    if backup == destination:
        raise ValueError("Backup and destination must be different files.")

    with sqlite3.connect(f"file:{backup.as_posix()}?mode=ro", uri=True) as src:
        integrity = src.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Backup integrity check failed: {integrity}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".restore-tmp")

        try:
            dst = sqlite3.connect(temporary)
            try:
                src.backup(dst)
                restored_integrity = dst.execute(
                    "PRAGMA integrity_check"
                ).fetchone()[0]

                if restored_integrity != "ok":
                    raise RuntimeError(
                        "Restored database failed integrity check."
                    )
            finally:
                dst.close()

            # The temporary database must be closed before replacing the target.
            os.replace(temporary, destination)
        finally:
            if temporary.exists():
                temporary.unlink()

    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    backup = sub.add_parser("backup", help="create a timestamped database backup")
    backup.add_argument("--database", default=None)
    backup.add_argument("--output-dir", default="backups")

    restore = sub.add_parser("restore", help="restore a backup to a database path")
    restore.add_argument("backup")
    restore.add_argument("--database", default=None)

    args = parser.parse_args(argv)

    from app import create_app
    app = create_app()

    with app.app_context():
        uri = app.config["SQLALCHEMY_DATABASE_URI"]

    default_db = sqlite_path(uri)

    try:
        if args.command == "backup":
            source = Path(args.database).resolve() if args.database else default_db
            result = backup_database(source, args.output_dir)
        else:
            destination = (
                Path(args.database).resolve()
                if args.database
                else default_db
            )
            result = restore_database(args.backup, destination)
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as exc:
        print(f"Database {args.command} failed: {exc}", file=sys.stderr)
        return 1

    print(f"Database {args.command} completed: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
