"""BUSINESS layer for tasks and progress (BL-21, BL-23, BL-24)."""
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


def _clip(text, limit=100):
    """activity_logs.action is 100 characters long."""
    return text if len(text) <= limit else text[:limit - 3] + "..."


def assignment_log_text(old, new):
    """BL-20: text for the activity log when a task changes hands.
    old / new are users (or None for unassigned)."""
    if old is None and new is None:
        return "task assignment unchanged"
    if old is None:
        return _clip(f"task assigned to {new.name}")
    if new is None:
        return _clip(f"task unassigned (was {old.name})")
    return _clip(f"task reassigned: {old.name} -> {new.name}")


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
