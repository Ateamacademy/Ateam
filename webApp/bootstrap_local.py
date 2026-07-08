"""
One-time local DB bootstrap for webApp.

Creates all tables, optionally runs the sample-data seeder (db_init), and
ALWAYS creates an 'admin' role + admin login user with every permission
granted (so you don't hit the 503 maintenance wall or 403s).

Run from the OUTER webApp directory (contains the `webApp` package):

    PYTHONPATH=/var/www/webApp python3 bootstrap_local.py

Then log in at http://127.0.0.1:5000/ with:
    email:    admin@local
    password: password
"""
from sqlalchemy import Boolean
from webApp import app, db
from Schema import Roles, User, Centre, db_init
from werkzeug.security import generate_password_hash

ADMIN_EMAIL = "admin@local"
ADMIN_PASSWORD = "AdminLocal1"
SEED_SAMPLE_DATA = False   # real data restored from prod dump; no seeding needed


def _grant_all_permissions(obj):
    """Set every Boolean column on a Roles/User instance to True."""
    for column in obj.__table__.columns:
        if isinstance(column.type, Boolean):
            setattr(obj, column.name, True)


# Columns added after the initial deploy. db.create_all() creates missing *tables*
# but never alters an existing one, so on an already-provisioned database (e.g.
# Render's) these have to be added by hand. Idempotent: only adds what's missing.
_ADDED_COLUMNS = {
    "exam_rooms": [("centreID", "INTEGER")],
    "exam_student": [("centreID", "INTEGER"), ("requested_exams", "TEXT")],
}


def _ensure_columns():
    from sqlalchemy import inspect as sa_inspect, text
    try:
        inspector = sa_inspect(db.engine)
    except Exception as exc:
        print(f"[migrate] could not inspect schema (skipped): {exc}")
        return
    for table, columns in _ADDED_COLUMNS.items():
        try:
            if not inspector.has_table(table):
                continue
            existing = {c["name"] for c in inspector.get_columns(table)}
            for name, coltype in columns:
                if name not in existing:
                    db.session.execute(
                        text(f'ALTER TABLE {table} ADD COLUMN "{name}" {coltype}')
                    )
                    db.session.commit()
                    print(f"[migrate] added {table}.{name}")
        except Exception as exc:
            db.session.rollback()
            print(f"[migrate] {table} column check failed (non-fatal): {exc}")


def main():
    with app.app_context():
        db.create_all()
        print("Tables created.")
        _ensure_columns()

        # admin role
        admin_role = Roles.query.filter_by(name="admin").first()
        if not admin_role:
            admin_role = Roles(name="admin", level=100)
            db.session.add(admin_role)
        _grant_all_permissions(admin_role)

        # admin user (created FIRST so FKs like centres.admin_id resolve)
        admin_user = User.query.filter_by(email=ADMIN_EMAIL).first()
        if not admin_user:
            admin_user = User(
                role="admin",
                otherID=1,
                email=ADMIN_EMAIL,
                password=generate_password_hash(ADMIN_PASSWORD),
            )
            db.session.add(admin_user)
        else:
            admin_user.password = generate_password_hash(ADMIN_PASSWORD)
        _grant_all_permissions(admin_user)
        db.session.commit()
        print(f"Admin ready -> email: {ADMIN_EMAIL}  password: {ADMIN_PASSWORD}")

        # sample data (best-effort; the seeder has FK-ordering quirks)
        if SEED_SAMPLE_DATA and Centre.query.count() == 0:
            try:
                db_init()
                print("Sample data seeded (db_init).")
            except Exception as e:
                db.session.rollback()
                print(f"db_init skipped/failed (non-fatal): {e}")


if __name__ == "__main__":
    main()
