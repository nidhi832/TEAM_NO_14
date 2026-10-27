"""BL-18: members can comment on a task (author and timestamp shown)."""
from app.extensions import db
from app.models import ActivityLog, Comment
from app.services import task_service
from sprint2_crud_helpers import login, make_project, make_task, make_user


def test_member_comment_shows_author_and_timestamp(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        member = make_user("Mia")
        task_id = make_task(make_project(pm, [member]), assignee=member).id
        login(client, member)
        resp = client.post(f"/tasks/{task_id}/comments",
                           data={"text": "Started working on it"})
        assert resp.status_code == 302
        page = client.get(f"/tasks/{task_id}")
        assert page.status_code == 200
        assert b"Started working on it" in page.data
        assert b"Mia" in page.data                      # author
        comment = Comment.query.one()
        stamp = comment.created_at.strftime("%Y-%m-%d %H:%M")
        assert stamp.encode() in page.data              # timestamp


def test_pm_and_member_comments_appear_in_order(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        member = make_user("Mia")
        task_id = make_task(make_project(pm, [member])).id
        login(client, pm)
        client.post(f"/tasks/{task_id}/comments", data={"text": "first one"})
        login(client, member)
        client.post(f"/tasks/{task_id}/comments", data={"text": "second one"})
        page = client.get(f"/tasks/{task_id}").data
        assert page.index(b"first one") < page.index(b"second one")
        assert b"Comments (2)" in page


def test_empty_and_too_long_comments_are_rejected(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        task_id = make_task(make_project(pm)).id
        login(client, pm)
        client.post(f"/tasks/{task_id}/comments", data={"text": "   "})
        too_long = "x" * (task_service.MAX_COMMENT_LENGTH + 1)
        client.post(f"/tasks/{task_id}/comments", data={"text": too_long})
        assert Comment.query.count() == 0


def test_comment_text_is_escaped(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        task_id = make_task(make_project(pm)).id
        login(client, pm)
        client.post(f"/tasks/{task_id}/comments",
                    data={"text": "<script>alert(1)</script>"})
        page = client.get(f"/tasks/{task_id}").data
        assert b"<script>alert(1)</script>" not in page
        assert b"&lt;script&gt;" in page


def test_non_member_cannot_view_or_comment(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        outsider = make_user("Omar")
        task_id = make_task(make_project(pm)).id
        login(client, outsider)
        assert client.get(f"/tasks/{task_id}").status_code == 403
        resp = client.post(f"/tasks/{task_id}/comments",
                           data={"text": "let me in"})
        assert resp.status_code == 403
        assert Comment.query.count() == 0


def test_comment_is_logged_and_missing_task_is_404(app, client):
    with app.app_context():
        pm = make_user("Pat", "PM")
        task_id = make_task(make_project(pm)).id
        login(client, pm)
        client.post(f"/tasks/{task_id}/comments", data={"text": "note"})
        assert ActivityLog.query.filter_by(action="comment added").count() == 1
        assert client.get("/tasks/9999").status_code == 404
        db.session.rollback()
