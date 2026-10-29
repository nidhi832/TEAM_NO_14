# Availability report - BL-30 (MPMS-NF-002)

**Requirement:** available at least **99%** of the time during working hours (Mon-Fri 09:00-18:00).

**Result: PASS** - 100.00% available overall (0 failed of 180 checks).

Generated: 29 Oct 2026 19:55 | Tool: `scripts/uptime_monitor.py`

## How it was measured
- The monitor calls `GET /health` at a fixed interval. A check is **up** when it returns HTTP 200 with `status: ok` (which includes a working database query) within the timeout; anything else is **down**.
- Availability = up checks / all checks. Every check is stored in the log file next to this report.
- Only checks inside the working-hours window count towards the result. If no check fell inside it, all checks are used and the result says so.

Monitoring period: 2026-10-29 19:24:41 to 2026-10-29 19:54:34

## Results

| Window | Checks | Up | Down | Availability |
|---|---|---|---|---|
| Working hours (Mon-Fri 09:00-18:00) | 0 | 0 | 0 | n/a |
| All hours | 180 | 180 | 0 | 100.00% |

Response time of successful checks: median 8 ms, slowest 45 ms.

## Outages

No failed checks.
