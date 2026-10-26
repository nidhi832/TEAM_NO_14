"""BUSINESS layer: task filter/search and CSV progress report (BL-25, BL-26)."""
import csv
import io
from datetime import date

from app.auth_utils import can_manage_project, visible_projects
from app.models import PRIORITIES, STATUSES, Task
from app.services import task_service


def parse_filters(args):
    """Turn query-string values into clean filters. Returns (filters, errors)."""
    errors = []
    filters = {"q": (args.get("q") or "").strip()[:100]}
    status = args.get("status") or ""
    filters["status"] = status if status in STATUSES else ""
    priority = args.get("priority") or ""
    filters["priority"] = priority if priority in PRIORITIES else ""
    for key in ("assignee_id", "project_id"):
        raw = args.get(key) or ""
        filters[key] = int(raw) if raw.isdigit() else None
    raw_due = args.get("due_before") or ""
    filters["due_before"] = None
    if raw_due:
        try:
            filters["due_before"] = date.fromisoformat(raw_due)
        except ValueError:
            errors.append("Due date must be a valid date (YYYY-MM-DD).")
    return filters, errors


def search_tasks(user, filters):
    """Only tasks in projects the user can see (BL-14), then the filters."""
    project_ids = [p.id for p in visible_projects(user).all()]
    if not project_ids:
        return []
    query = Task.query.filter(Task.project_id.in_(project_ids))
    if filters.get("project_id"):
        query = query.filter(Task.project_id == filters["project_id"])
    if filters.get("q"):
        # SQLAlchemy binds this as a parameter, so it is safe from SQL injection
        query = query.filter(Task.title.ilike(f"%{filters['q']}%"))
    if filters.get("status"):
        query = query.filter(Task.status == filters["status"])
    if filters.get("priority"):
        query = query.filter(Task.priority == filters["priority"])
    if filters.get("assignee_id"):
        query = query.filter(Task.assignee_id == filters["assignee_id"])
    if filters.get("due_before"):
        query = query.filter(Task.due_date <= filters["due_before"])
    return sorted(query.all(), key=task_service.due_sort_key)


def assignee_choices(user):
    seen = {}
    for project in visible_projects(user).all():
        for member in project.members:
            seen[member.id] = member
    return sorted(seen.values(), key=lambda u: u.name)


def can_download_report(user, project):
    """Same rule as managing the project: owner PM or Admin."""
    return can_manage_project(user, project)


def _cell(value):
    """Stop spreadsheet formula injection: =, +, -, @ at the start become text."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


def project_report_csv(project, today=None):
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Task ID", "Title", "Assignee", "Status", "Priority",
                     "Due date", "Overdue"])
    for t in sorted(project.tasks, key=task_service.due_sort_key):
        writer.writerow([t.id, _cell(t.title),
                         _cell(t.assignee.name if t.assignee else ""),
                         t.status, t.priority,
                         t.due_date.isoformat() if t.due_date else "",
                         "Yes" if task_service.is_overdue(t, today) else "No"])
    summary = task_service.project_summary(project, today)
    done = summary["counts"].get("Done", 0)
    writer.writerow([])
    writer.writerow(["Summary", f"{done} of {summary['total']} tasks Done",
                     f"{summary['percent']}%"])
    return out.getvalue()
