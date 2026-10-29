"""BUSINESS layer: measuring availability (BL-30, MPMS-NF-002).

Requirement: the system is available at least 99% of the time during working
hours. We measure it by calling /health at a fixed interval and writing one
CSV row per check. Availability = successful checks / all checks.
Standard library only; no Flask or database imports, so it is easy to test.
"""
import csv
import json
import time
import urllib.error
import urllib.request
from datetime import datetime
from datetime import time as clock_time
from pathlib import Path

TARGET_PERCENT = 99.0
FIELDS = ("timestamp", "url", "ok", "status", "response_ms", "error")
DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


# ---- taking a measurement -------------------------------------------------
def _body_says_ok(body):
    try:
        return json.loads(body).get("status") == "ok"
    except (ValueError, AttributeError):
        return False


def check_once(url, timeout=5.0, opener=None, now=None):
    """Call the health URL once. Returns one log record (a dict)."""
    opener = opener or urllib.request.urlopen
    started = time.perf_counter()
    status, error, ok = 0, "", False
    try:
        with opener(url, timeout=timeout) as response:
            status = response.status
            body = response.read(2000).decode("utf-8", "replace")
        ok = status == 200 and _body_says_ok(body)
        if not ok:
            error = "unhealthy response"
    except urllib.error.HTTPError as exc:       # e.g. 503 from /health
        status, error = exc.code, f"HTTP {exc.code}"
    except Exception as exc:                    # refused, timeout, DNS ...
        error = type(exc).__name__
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    stamp = (now or datetime.now()).isoformat(timespec="seconds")
    return {"timestamp": stamp, "url": url, "ok": int(ok), "status": status,
            "response_ms": elapsed_ms, "error": error}


def append_record(path, record):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(record)


def read_records(path):
    """Read the log. Rows that cannot be understood are skipped."""
    records = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            try:
                records.append({
                    "timestamp": datetime.fromisoformat(row["timestamp"]),
                    "ok": row["ok"] == "1",
                    "status": int(row["status"]),
                    "response_ms": int(row["response_ms"]),
                    "error": row.get("error") or "",
                })
            except (KeyError, ValueError, TypeError):
                continue
    return sorted(records, key=lambda r: r["timestamp"])


# ---- working hours ----------------------------------------------------------
def parse_days(text):
    """'Mon-Fri' -> {0,1,2,3,4}; also 'Mon,Wed' or 'Sat'."""
    days = set()
    for part in text.split(","):
        part = part.strip().title()
        if "-" in part:
            first, last = (DAY_NAMES.index(x) for x in part.split("-"))
            index = first
            while True:
                days.add(index)
                if index == last:
                    break
                index = (index + 1) % 7
        else:
            days.add(DAY_NAMES.index(part))
    return days


def parse_clock(text):
    hour, minute = text.split(":")
    return clock_time(int(hour), int(minute))


def in_working_hours(stamp, start, end, days):
    return stamp.weekday() in days and start <= stamp.time() < end


# ---- the numbers ------------------------------------------------------------
def availability(records):
    total = len(records)
    up = sum(1 for r in records if r["ok"])
    percent = round(up * 100 / total, 2) if total else None
    return {"total": total, "up": up, "down": total - up, "percent": percent}


def outages(records):
    """Runs of failed checks. 'seconds' is an upper bound: first failed
    check until the next successful one."""
    found, current = [], None
    for record in sorted(records, key=lambda r: r["timestamp"]):
        if not record["ok"]:
            if current is None:
                current = {"start": record["timestamp"], "checks": 0,
                           "error": record["error"] or "failed"}
            current["checks"] += 1
            current["end"] = record["timestamp"]
        elif current is not None:
            current["end"] = record["timestamp"]
            found.append(current)
            current = None
    if current is not None:
        found.append(current)
    for item in found:
        item["seconds"] = int((item["end"] - item["start"]).total_seconds())
    return found


def _fmt(percent):
    return "n/a" if percent is None else f"{percent:.2f}%"


def build_report(records, start_text="09:00", end_text="18:00",
                 days_text="Mon-Fri", note="", generated=None):
    """Markdown availability report (the BL-30 'uptime report')."""
    start, end = parse_clock(start_text), parse_clock(end_text)
    days = parse_days(days_text)
    working = [r for r in records
               if in_working_hours(r["timestamp"], start, end, days)]
    overall, in_hours = availability(records), availability(working)
    basis, basis_name = ((in_hours, "during working hours")
                         if in_hours["total"] else (overall, "overall"))
    if basis["percent"] is None:
        verdict, headline = "NO DATA", "No checks were recorded."
    else:
        passed = basis["percent"] >= TARGET_PERCENT
        verdict = "PASS" if passed else "FAIL"
        headline = (f"{_fmt(basis['percent'])} available {basis_name} "
                    f"({basis['down']} failed of {basis['total']} checks)")
    generated = generated or datetime.now()
    label = f"{days_text} {start_text}-{end_text}"
    lines = [
        "# Availability report - BL-30 (MPMS-NF-002)", "",
        f"**Requirement:** available at least **{TARGET_PERCENT:g}%** of the "
        f"time during working hours ({label}).", "",
        f"**Result: {verdict}** - {headline}.", "",
        f"Generated: {generated.strftime('%d %b %Y %H:%M')} | Tool: "
        "`scripts/uptime_monitor.py`" + (f" | {note}" if note else ""), "",
        "## How it was measured",
        "- The monitor calls `GET /health` at a fixed interval. A check is "
        "**up** when it returns HTTP 200 with `status: ok` (which includes a "
        "working database query) within the timeout; anything else is "
        "**down**.",
        "- Availability = up checks / all checks. Every check is stored in "
        "the log file next to this report.",
        "- Only checks inside the working-hours window count towards the "
        "result. If no check fell inside it, all checks are used and the "
        "result says so.", ""]
    if records:
        lines += [f"Monitoring period: {records[0]['timestamp']} to "
                  f"{records[-1]['timestamp']}", ""]
    lines += [
        "## Results", "",
        "| Window | Checks | Up | Down | Availability |",
        "|---|---|---|---|---|",
        f"| Working hours ({label}) | {in_hours['total']} | "
        f"{in_hours['up']} | {in_hours['down']} | "
        f"{_fmt(in_hours['percent'])} |",
        f"| All hours | {overall['total']} | {overall['up']} | "
        f"{overall['down']} | {_fmt(overall['percent'])} |", ""]
    times = sorted(r["response_ms"] for r in records if r["ok"])
    if times:
        lines += [f"Response time of successful checks: median "
                  f"{times[len(times) // 2]} ms, slowest {times[-1]} ms.", ""]
    lines += ["## Outages", ""]
    found = outages(records)
    if found:
        lines += ["| Started | Failed checks | Up to (s) | Error |",
                  "|---|---|---|---|"]
        lines += [f"| {o['start']} | {o['checks']} | {o['seconds']} | "
                  f"{o['error']} |" for o in found[:10]]
    else:
        lines.append("No failed checks.")
    return "\n".join(lines) + "\n"
