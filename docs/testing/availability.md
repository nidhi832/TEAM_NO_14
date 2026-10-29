# Availability - BL-30 (MPMS-NF-002)

**Requirement:** the system is available at least **99%** of the time during
working hours (Monday-Friday, 09:00-18:00).

99% of a 9-hour working day is about **5 minutes** of allowed downtime
(32 seconds per hour). Over a 30-minute test that is **18 seconds**.

## What "available" means
`GET /health` (no login needed) answers HTTP 200 with `{"status": "ok"}` only
when the app is running **and** the database answers a query. If the database
fails it answers HTTP 503 with `{"status": "error"}`. It never shows internal
details. A check that gets anything else (refused, timeout, 503, wrong
answer) counts as **down**.

## How it is measured
`scripts/uptime_monitor.py` calls `/health` at a fixed interval and writes one
row per check to `docs/testing/uptime-log.csv`.

    python run.py                                              # window 1
    python scripts/uptime_monitor.py watch --minutes 30 --interval 10   # window 2
    python scripts/uptime_monitor.py report                    # when it ends

`report` writes `docs/testing/uptime-report.md` with the result (PASS/FAIL
against 99%), the checks inside working hours, response times and a list of
outages. For a longer measurement, schedule `uptime_monitor.py once` every
minute with Windows Task Scheduler or cron and run `report` at the end.

Only checks inside the working-hours window count. If the test was run outside
it (evening or weekend), the report says so and uses all checks instead. Use
`--start`, `--end` and `--days` to change the window.

## What keeps the system available
- **Database locks:** busy timeout and WAL mode (BL-29, `app/db_tuning.py`)
  stop two users saving at once from crashing a request.
- **Backups:** a daily backup with a tested restore (BL-33).
- **Monitoring:** `/health` plus the monitor above show an outage as soon as
  it happens.
- **Restart on crash:** run the app under a process manager in production
  (for example `gunicorn` with systemd `Restart=always`, or the hosting
  platform's auto-restart). The Flask development server is for testing only.

## Limits of this measurement
The monitor runs on the same machine as the app unless pointed at another URL
with `--url`, so it cannot see network problems between users and the server.
The result is only as long as the measurement window; say that window in the
report with `--note`.
