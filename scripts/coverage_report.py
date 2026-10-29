"""BL-34 / MPMS-NF-006: run the tests with coverage and write the report.

    python scripts/coverage_report.py

Writes docs/testing/coverage-report.md (total %, per-file table, PASS/FAIL
against the 60% target). Needs the packages in requirements.txt.
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TARGET_PERCENT = 60.0
JSON_FILE = ROOT / "coverage.json"
REPORT = ROOT / "docs" / "testing" / "coverage-report.md"


def file_rows(data):
    """[(path, statements, missed, percent)] sorted by path."""
    rows = []
    for path, info in data.get("files", {}).items():
        summary = info["summary"]
        rows.append((path.replace("\\", "/"), summary["num_statements"],
                     summary["missing_lines"], summary["percent_covered"]))
    return sorted(rows)


def build_report(data, tests_passed, generated, commit, tests_failed=False):
    total = data["totals"]["percent_covered"]
    ok = total >= TARGET_PERCENT and not tests_failed
    verdict = "PASS" if ok else "FAIL"
    lines = [
        "# Test coverage report - BL-34 (MPMS-NF-006)", "",
        f"**Result: {verdict}** - {total:.1f}% of the application code is "
        f"covered by tests (target: at least {TARGET_PERCENT:g}%).", "",
        f"Generated: {generated.strftime('%d %b %Y %H:%M')} | Commit: "
        f"`{commit}` | Tests passed: {tests_passed}"
        + (" | **some tests failed**" if tests_failed else ""), "",
        "## How to reproduce", "",
        "    pip install -r requirements.txt",
        "    python scripts/coverage_report.py", "",
        "The same check runs in CI on every pull request "
        "(`pytest --cov=app`, configured in `.coveragerc`) and fails "
        "below the target.", "",
        "## Coverage per file", "",
        "| File | Statements | Missed | Covered |", "|---|---|---|---|"]
    for path, statements, missed, percent in file_rows(data):
        lines.append(f"| {path} | {statements} | {missed} | "
                     f"{percent:.0f}% |")
    totals = data["totals"]
    lines.append(f"| **Total** | **{totals['num_statements']}** | "
                 f"**{totals['missing_lines']}** | **{total:.1f}%** |")
    lines += ["", "Statement coverage only (a line counts as covered when a "
              "test runs it). The layering rules are checked separately by "
              "`tests/test_architecture.py`; the manual review is in "
              "`docs/code-review.md`.", ""]
    return "\n".join(lines)


def _git_commit():
    try:
        done = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              cwd=ROOT, capture_output=True, text=True)
        return done.stdout.strip() or "unknown"
    except OSError:
        return "unknown"


def main():
    command = [sys.executable, "-m", "pytest", "-q", "--cov=app",
               f"--cov-report=json:{JSON_FILE}", "--cov-fail-under=0",
               "-p", "no:cacheprovider"]
    done = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    sys.stdout.write(done.stdout[-600:])
    if not JSON_FILE.exists():
        print("Coverage data was not written. Is pytest-cov installed?")
        return 2
    data = json.loads(JSON_FILE.read_text())
    match = re.search(r"(\d+) passed", done.stdout)
    passed = int(match.group(1)) if match else 0
    failed = bool(re.search(r"\d+ failed", done.stdout))
    text = build_report(
        data, passed, datetime.now(), _git_commit(), tests_failed=failed)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print(f"\n{text.split(chr(10) + chr(10))[1].strip()}")
    print(f"Report written to {REPORT}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
