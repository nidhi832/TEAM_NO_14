"""Give an existing account the Admin role (needed once, for the first admin).

    python create_admin.py you@example.com

Register normally first. After that the admin can change other users' roles
and deactivate/reactivate accounts at /admin/users.
"""
import sys

from app import create_app
from app.extensions import db
from app.models import User

if len(sys.argv) != 2:
    sys.exit("Usage: python create_admin.py <email>")

app = create_app()
with app.app_context():
    user = User.query.filter_by(email=sys.argv[1].strip().lower()).first()
    if user is None:
        sys.exit("No user with that email. Register first.")
    user.role = "Admin"
    db.session.commit()
    print(f"{user.name} <{user.email}> is now an Admin.")
