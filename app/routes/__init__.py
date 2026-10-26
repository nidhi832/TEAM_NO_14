"""UI layer: one blueprint per module. Add your routes in each file."""
from app.routes.auth import bp as auth_bp
from app.routes.projects import bp as projects_bp
from app.routes.tasks import bp as tasks_bp
from app.routes.dashboard import bp as dashboard_bp
from app.routes.admin import bp as admin_bp
from app.routes.reports import bp as reports_bp


def register_blueprints(app):
    for bp in (auth_bp, projects_bp, tasks_bp, dashboard_bp, admin_bp,
               reports_bp):
        app.register_blueprint(bp)
