"""BUSINESS layer for projects and tasks: validation rules (BL-10, BL-15)."""
from datetime import date

from app.models import PRIORITIES


def parse_date(value):
    """'2026-10-30' -> date, '' -> None. Raises ValueError for bad text."""
    value = (value or "").strip()
    return date.fromisoformat(value) if value else None


def validate_project(name, start_text, end_text):
    """BL-10: returns (problems, start, end). End date may not be before start."""
    problems, start, end = [], None, None
    if not (name or "").strip():
        problems.append("Project name is required.")
    try:
        start = parse_date(start_text)
        end = parse_date(end_text)
    except ValueError:
        problems.append("Dates must look like YYYY-MM-DD.")
        return problems, None, None
    if start and end and end < start:
        problems.append("End date cannot be before the start date.")
    return problems, start, end


def validate_task(title, priority, due_text):
    """BL-15: returns (problems, due_date)."""
    problems, due = [], None
    if not (title or "").strip():
        problems.append("Task title is required.")
    if priority not in PRIORITIES:
        problems.append("Choose a valid priority.")
    try:
        due = parse_date(due_text)
    except ValueError:
        problems.append("Due date must look like YYYY-MM-DD.")
    return problems, due
