"""BL-34: the coverage report script formats results correctly."""
import importlib.util
from datetime import datetime
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / \
    "coverage_report.py"
spec = importlib.util.spec_from_file_location("coverage_report", SCRIPT)
coverage_report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coverage_report)

DATA = {
    "files": {
        "app\\routes\\b.py": {"summary": {"num_statements": 10,
                                          "missing_lines": 5,
                                          "percent_covered": 50.0}},
        "app/a.py": {"summary": {"num_statements": 10, "missing_lines": 0,
                                 "percent_covered": 100.0}},
    },
    "totals": {"num_statements": 20, "missing_lines": 5,
               "percent_covered": 75.0},
}
WHEN = datetime(2026, 10, 29, 12, 0)


def test_files_are_sorted_and_use_forward_slashes():
    rows = coverage_report.file_rows(DATA)
    assert [r[0] for r in rows] == ["app/a.py", "app/routes/b.py"]


def test_report_passes_at_or_above_target():
    text = coverage_report.build_report(DATA, 50, WHEN, "abc1234")
    assert "**Result: PASS**" in text
    assert "75.0%" in text and "`abc1234`" in text
    assert "| app/routes/b.py | 10 | 5 | 50% |" in text


def test_report_fails_below_target_or_with_failing_tests():
    low = dict(DATA, totals=dict(DATA["totals"], percent_covered=59.9))
    assert "**Result: FAIL**" in coverage_report.build_report(
        low, 50, WHEN, "abc")
    text = coverage_report.build_report(DATA, 50, WHEN, "abc",
                                        tests_failed=True)
    assert "**Result: FAIL**" in text and "some tests failed" in text
