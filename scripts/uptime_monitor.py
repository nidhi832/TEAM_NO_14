"""BL-30 / MPMS-NF-002: measure availability and write the uptime report.

Start the app first (python run.py), then in a second window:

  python scripts/uptime_monitor.py watch --minutes 30 --interval 10
  python scripts/uptime_monitor.py once            (one check; for a scheduler)
  python scripts/uptime_monitor.py report          (writes the report file)

Every check is appended to docs/testing/uptime-log.csv. The report is
written to docs/testing/uptime-report.md. Standard library only.
"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services import uptime_service as up  # noqa: E402

DEFAULT_URL = "http://127.0.0.1:5000/health"
DEFAULT_LOG = ROOT / "docs" / "testing" / "uptime-log.csv"
DEFAULT_REPORT = ROOT / "docs" / "testing" / "uptime-report.md"


def _line(record, up_count, total):
    state = "UP  " if record["ok"] else "DOWN"
    clock = record["timestamp"][11:]
    return (f"[{clock}] {state} status={record['status']} "
            f"{record['response_ms']} ms  {record['error']}  "
            f"(running {up_count * 100 / total:.2f}%)")


def cmd_once(args):
    record = up.check_once(args.url, args.timeout)
    up.append_record(args.log, record)
    print(_line(record, int(record["ok"]), 1))
    return 0 if record["ok"] else 1


def cmd_watch(args):
    deadline = time.time() + args.minutes * 60
    total = good = 0
    print(f"Checking {args.url} every {args.interval} s for "
          f"{args.minutes} min. Press Ctrl+C to stop early.")
    try:
        while time.time() < deadline:
            record = up.check_once(args.url, args.timeout)
            up.append_record(args.log, record)
            total += 1
            good += int(record["ok"])
            print(_line(record, good, total), flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")
    if total:
        print(f"Done: {good}/{total} checks up "
              f"({good * 100 / total:.2f}%). "
              "Now run: python scripts/uptime_monitor.py report")
    return 0


def cmd_report(args):
    try:
        records = up.read_records(args.log)
    except FileNotFoundError:
        print(f"No log found at {args.log}. Run the 'watch' command first.")
        return 2
    text = up.build_report(records, args.start, args.end, args.days,
                           args.note, datetime.now())
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text.split("\n\n")[2].strip())      # the "Result: ..." line
    print(f"Report written to {out}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name, func in (("once", cmd_once), ("watch", cmd_watch)):
        cmd = sub.add_parser(name)
        cmd.add_argument("--url", default=DEFAULT_URL)
        cmd.add_argument("--timeout", type=float, default=5.0)
        cmd.add_argument("--log", default=str(DEFAULT_LOG))
        cmd.set_defaults(func=func)
        if name == "watch":
            cmd.add_argument("--minutes", type=float, default=30)
            cmd.add_argument("--interval", type=float, default=10)
    cmd = sub.add_parser("report")
    cmd.add_argument("--log", default=str(DEFAULT_LOG))
    cmd.add_argument("--out", default=str(DEFAULT_REPORT))
    cmd.add_argument("--start", default="09:00")
    cmd.add_argument("--end", default="18:00")
    cmd.add_argument("--days", default="Mon-Fri")
    cmd.add_argument("--note", default="")
    cmd.set_defaults(func=cmd_report)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
