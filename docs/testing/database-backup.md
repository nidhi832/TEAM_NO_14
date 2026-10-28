# Database backup and restore - BL-33

The utility `scripts/db_backup.py` creates a timestamped SQLite snapshot using
SQLite's online backup API and verifies it with `PRAGMA integrity_check`.

## Manual backup

Run from the repository root while the app is running or stopped:

```bash
python scripts/db_backup.py backup --output-dir backups
```

The default database URI is read from the Flask app configuration. An explicit
source can be supplied with `--database path/to/mpms.db`.

## Restore drill

Stop the application first, then restore a known backup:

```bash
python scripts/db_backup.py restore backups/mpms_YYYYMMDD_HHMMSS.db
```

For a non-default destination, add `--database path/to/restore.db`. Verify the
command reports success and, for a drill, start the app against the restored
copy and confirm expected projects and tasks are present. Keep backups on a
different disk or protected storage in production; a backup on the same disk
does not protect against disk loss.

## Daily scheduling

- **Windows:** create a daily Task Scheduler task that runs
  `python.exe scripts/db_backup.py backup --output-dir backups`, with the
  repository root as the task's working directory.
- **Linux/macOS:** add a daily cron entry using absolute paths, e.g.
  `0 2 * * * cd /path/to/repo && /path/to/python scripts/db_backup.py backup --output-dir /path/to/backups`.

The acceptance target is RPO <= 24 hours. Monitor scheduled task/cron results
and periodically perform a restore drill. The utility does not delete old
backups automatically; configure retention according to the team's storage
policy.
