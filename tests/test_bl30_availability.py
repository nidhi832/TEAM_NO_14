"""BL-30 (MPMS-NF-002): health check and availability measurement."""
import subprocess
import sys
import urllib.error
from datetime import datetime, time
from pathlib import Path

from app.extensions import db
from app.services import uptime_service as up

ROOT = Path(__file__).resolve().parent.parent


# ---- /health ----------------------------------------------------------------
def test_health_is_ok_without_login(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok", "database": "ok"}
    assert resp.headers["Cache-Control"] == "no-store"


def test_health_reports_503_when_database_is_down(app, client, monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("database file is gone")
    with app.app_context():
        monkeypatch.setattr(db.session, "execute", broken)
        resp = client.get("/health")
    assert resp.status_code == 503
    assert resp.get_json() == {"status": "error", "database": "unavailable"}
    assert b"gone" not in resp.data          # no internal details leak


# ---- check_once -------------------------------------------------------------
class FakeResponse:
    def __init__(self, status=200, body='{"status": "ok"}'):
        self.status, self._body = status, body

    def read(self, size=-1):
        return self._body.encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


NOW = datetime(2026, 10, 29, 10, 0, 0)


def test_check_once_up():
    rec = up.check_once("http://x/health", opener=lambda u, timeout:
                        FakeResponse(), now=NOW)
    assert rec["ok"] == 1 and rec["status"] == 200
    assert rec["timestamp"] == "2026-10-29T10:00:00"


def test_check_once_http_503_is_down():
    def opener(url, timeout):
        raise urllib.error.HTTPError(url, 503, "unavailable", {}, None)
    rec = up.check_once("http://x/health", opener=opener, now=NOW)
    assert rec["ok"] == 0 and rec["status"] == 503
    assert rec["error"] == "HTTP 503"


def test_check_once_connection_refused_is_down():
    def opener(url, timeout):
        raise ConnectionRefusedError()
    rec = up.check_once("http://x/health", opener=opener, now=NOW)
    assert rec["ok"] == 0 and rec["status"] == 0
    assert rec["error"] == "ConnectionRefusedError"


def test_check_once_200_with_wrong_body_is_down():
    rec = up.check_once("http://x/health", now=NOW, opener=lambda u, timeout:
                        FakeResponse(body="<html>proxy error</html>"))
    assert rec["ok"] == 0


# ---- the log file -----------------------------------------------------------
def test_log_round_trip_and_bad_rows_are_skipped(tmp_path):
    log = tmp_path / "sub" / "log.csv"
    up.append_record(log, up.check_once("u", opener=lambda u, timeout:
                                        FakeResponse(), now=NOW))
    with log.open("a") as handle:
        handle.write("garbage,row\n")
    records = up.read_records(log)
    assert len(records) == 1
    assert records[0]["ok"] is True
    assert log.read_text().count("timestamp") == 1       # one header only


# ---- working hours ----------------------------------------------------------
def test_parse_days_and_working_hours():
    assert up.parse_days("Mon-Fri") == {0, 1, 2, 3, 4}
    assert up.parse_days("Sat,Sun") == {5, 6}
    assert up.parse_days("Fri-Mon") == {4, 5, 6, 0}
    days, start, end = up.parse_days("Mon-Fri"), time(9), time(18)
    thursday = datetime(2026, 10, 29, 10, 0)
    assert up.in_working_hours(thursday, start, end, days)
    assert not up.in_working_hours(datetime(2026, 10, 29, 18, 0), start, end,
                                   days)                  # end is exclusive
    assert not up.in_working_hours(datetime(2026, 10, 31, 10, 0), start, end,
                                   days)                  # a Saturday


# ---- the numbers ------------------------------------------------------------
def make_records(flags, start=datetime(2026, 10, 29, 10, 0, 0)):
    return [{"timestamp": datetime.fromtimestamp(start.timestamp() + 10 * i),
             "ok": flag, "status": 200 if flag else 0, "response_ms": 5,
             "error": "" if flag else "URLError"}
            for i, flag in enumerate(flags)]


def test_availability_numbers():
    assert up.availability(make_records([True] * 99 + [False]))["percent"] \
        == 99.0
    assert up.availability(make_records([True] * 98 + [False] * 2))[
        "percent"] == 98.0
    assert up.availability([])["percent"] is None


def test_outages_are_grouped():
    recs = make_records([True, False, False, True, True, False])
    found = up.outages(recs)
    assert [o["checks"] for o in found] == [2, 1]
    assert found[0]["seconds"] == 20          # first failure -> recovery


def test_report_passes_at_99_percent():
    text = up.build_report(make_records([True] * 99 + [False]))
    assert "**Result: PASS**" in text
    assert "99.00%" in text


def test_report_fails_below_99_percent():
    text = up.build_report(make_records([True] * 98 + [False] * 2))
    assert "**Result: FAIL**" in text
    assert "## Outages" in text and "URLError" in text


def test_report_only_counts_working_hours():
    # 20 failed checks on a Saturday night must not hurt the result
    weekend = make_records([False] * 20, datetime(2026, 10, 31, 23, 0, 0))
    weekday = make_records([True] * 50)
    text = up.build_report(weekend + weekday)
    assert "**Result: PASS**" in text
    assert "during working hours" in text


def test_report_without_any_working_hours_check_uses_all_and_says_so():
    night = make_records([True] * 5, datetime(2026, 10, 31, 23, 0, 0))
    text = up.build_report(night)
    assert "overall" in text and "**Result: PASS**" in text


def test_report_with_no_data():
    assert "NO DATA" in up.build_report([])


# ---- the command-line script ------------------------------------------------
def test_report_command_writes_the_file(tmp_path):
    log, out = tmp_path / "log.csv", tmp_path / "report.md"
    for rec in make_records([True] * 20):
        up.append_record(log, {
            "timestamp": rec["timestamp"].isoformat(timespec="seconds"),
            "url": "u", "ok": 1, "status": 200, "response_ms": 5,
            "error": ""})
    done = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "uptime_monitor.py"),
         "report", "--log", str(log), "--out", str(out)],
        capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert "Result: PASS" in done.stdout
    assert "Availability report" in out.read_text()
