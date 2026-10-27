"""BUSINESS layer for tasks and progress (BL-18, 21, 23, 24)."""
from datetime import date

from app.models import STATUSES


def is_overdue(task, today=None):
    """BL-24: due date has passed and the task is not Done."""
    today = today or date.today()
    return (task.due_date is not None and task.due_date < today
            and task.status != "Done")


def due_sort_key(task):
    """BL-21: earliest due date first, tasks without a date last."""
    return (task.due_date is None, task.due_date or date.max, task.id)


def status_counts(tasks):
    counts = {s: 0 for s in STATUSES}
    for t in tasks:
        counts[t.status] = counts.get(t.status, 0) + 1
    return counts


def percent_complete(tasks):
    """BL-23: 4 of 10 tasks Done -> 40."""
    if not tasks:
        return 0
    done = sum(1 for t in tasks if t.status == "Done")
    return round(done * 100 / len(tasks))


def project_summary(project, today=None):
    tasks = list(project.tasks)
    return {
        "project": project,
        "total": len(tasks),
        "counts": status_counts(tasks),
        "percent": percent_complete(tasks),
        "overdue": sum(1 for t in tasks if is_overdue(t, today)),
    }


MAX_COMMENT_LENGTH = 1000


def validate_comment(text):
    """BL-18: returns a list of problems (empty list = fine)."""
    text = (text or "").strip()
    if not text:
        return ["Comment cannot be empty."]
    if len(text) > MAX_COMMENT_LENGTH:
        return [f"Comment is too long (max {MAX_COMMENT_LENGTH} characters)."]
    return []
