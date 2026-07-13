"""Production-safe schema migration for the A-Team webApp.

Run ONCE per deploy on the live server, AFTER pulling new code and BEFORE
reloading Apache:

    cd /var/www/webApp
    DATABASE_URL="<the live connection string>" PYTHONPATH=/var/www/webApp \
        python3 migrate_production.py

What it does (and ONLY this):
  1. db.create_all()   — creates any brand-new TABLES the new code needs
                         (exam_rooms, seating_arrangement, seed_flags, ...).
                         create_all never drops or alters existing tables, so
                         it cannot touch or lose current data.
  2. _ensure_columns() — adds the new nullable COLUMNS to existing tables
                         (exam price, centre times, ghl_contact_id, ...) via
                         idempotent ALTER TABLE ... ADD COLUMN. Re-running is a
                         no-op once the columns exist.

What it deliberately does NOT do (unlike bootstrap_local.py):
  * It never creates or password-resets the admin@local backdoor account.
  * It never seeds demo/sample data.
  * It never deletes, drops or overwrites a single existing row.

It prints row counts before and after so you can confirm live data is intact.
Safe to run more than once.
"""
import os
import sys

# Some hosts hand out the deprecated "postgres://" scheme; SQLAlchemy needs
# "postgresql://". Normalise before the app reads it.
_db_url = os.environ.get("DATABASE_URL", "")
if _db_url.startswith("postgres://"):
    os.environ["DATABASE_URL"] = "postgresql://" + _db_url[len("postgres://"):]

from webApp import app, db                      # noqa: E402
from bootstrap_local import _ensure_columns     # reuse; importing does NOT create admin
from Schema import Students, exam_student, ExamRoom, Centre, Exams, User  # noqa: E402


def _count(model):
    """Count one table in isolation. On the drifted prod DB some tables don't
    exist yet — return None for those AND roll the failed statement back so it
    can't poison the shared session (which would make the later ALTERs abort)."""
    try:
        return model.query.count()
    except Exception:
        db.session.rollback()
        return None


def _counts():
    return {name: _count(m) for name, m in (
        ("users", User), ("students", Students), ("exam_students", exam_student),
        ("centres", Centre), ("exams", Exams), ("exam_rooms", ExamRoom))}


def main():
    with app.app_context():
        print("DB target:", app.config.get("SQLALCHEMY_DATABASE_URI", "?").split("@")[-1])
        before = _counts()
        print("[before]", before)
        db.session.rollback()          # clean session before any DDL

        db.create_all()
        print("[migrate] create_all done — any missing tables created")

        _ensure_columns()
        print("[migrate] column migration done")

        after = _counts()
        print("[after] ", after)

        # compare only core tables that had a real count on both sides
        lost = {k: (before[k], after[k]) for k in ("users", "students", "centres", "exams")
                if before.get(k) is not None and after.get(k) is not None
                and after[k] < before[k]}
        if lost:
            print("!! ROW COUNT DROPPED — investigate before serving traffic:", lost)
            sys.exit(2)

        # surface any column that failed to migrate rather than reporting a false OK
        missing = _unmigrated_columns()
        if missing:
            print("!! COLUMNS STILL MISSING after migration — do NOT reload Apache:", missing)
            sys.exit(3)

        print("[migrate] OK — schema is up to date and no core rows were lost.")


def _unmigrated_columns():
    """Re-inspect and confirm every expected new column now exists."""
    from sqlalchemy import inspect as sa_inspect
    from bootstrap_local import _ADDED_COLUMNS
    inspector = sa_inspect(db.engine)
    missing = []
    for table, cols in _ADDED_COLUMNS.items():
        if not inspector.has_table(table):
            continue
        present = {c["name"] for c in inspector.get_columns(table)}
        for name, _type in cols:
            if name not in present:
                missing.append(f"{table}.{name}")
    return missing


if __name__ == "__main__":
    main()
