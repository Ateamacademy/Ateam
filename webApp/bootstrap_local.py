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


def main():
    with app.app_context():
        db.create_all()
        print("Tables created.")

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
