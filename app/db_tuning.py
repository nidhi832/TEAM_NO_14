"""SQLite settings for many users at once (BL-29, found by the load test).

Without these, two users saving at the same moment can crash a request with
"sqlite3.OperationalError: database is locked" (HTTP 500).
- busy timeout: wait up to 15 s for the other write to finish instead of failing
- WAL journal mode: readers no longer block writers (and the other way round)
"""
from sqlalchemy import event
from sqlalchemy.engine import Engine

BUSY_TIMEOUT_MS = 15000


@event.listens_for(Engine, "connect")
def _sqlite_pragmas(dbapi_connection, _record):
    module = type(dbapi_connection).__module__
    if not module.startswith("sqlite3"):
        return                                    # only for SQLite
    cursor = dbapi_connection.cursor()
    cursor.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.close()
