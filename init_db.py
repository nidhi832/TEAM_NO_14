"""Creates the database tables (migration script for BL-03).

    python init_db.py           create any missing tables
    python init_db.py --reset   drop everything and recreate (loses data)
"""
import sys

from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    if "--reset" in sys.argv:
        db.drop_all()
        print("Dropped all tables.")
    db.create_all()
    print("Tables ready:", ", ".join(sorted(db.metadata.tables)))
