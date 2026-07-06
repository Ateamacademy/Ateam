#!/usr/bin/env python3
"""Replit entrypoint for the A-Team webApp (Flask).

Just import this repo into Replit, add the PostgreSQL tool (Tools pane -> it
sets DATABASE_URL automatically), and press Run. On first start this creates the
database tables and an admin login so you can sign in immediately with:

    admin@local  /  AdminLocal1

Optional Secrets: SECRET_KEY (else a per-run key is used, so sessions reset on
restart), MAIL_NOREPLY_PASSWORD / MAIL_EXAMS_PASSWORD (only for outbound email).
See README-REPLIT.md for details.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE, "webApp")

sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)  # the app resolves file paths relative to this directory

# Some hosts (older Render, Heroku) hand out the deprecated "postgres://" URL
# scheme; SQLAlchemy needs "postgresql://". Normalise before the app reads it.
_db_url = os.environ.get("DATABASE_URL", "")
if _db_url.startswith("postgres://"):
    os.environ["DATABASE_URL"] = "postgresql://" + _db_url[len("postgres://"):]

from webApp import app  # noqa: E402


def _bootstrap_db() -> None:
    """Create tables + an admin login on first run. Idempotent; safe every start."""
    if not os.environ.get("DATABASE_URL"):
        print("[run_replit] DATABASE_URL not set — add the PostgreSQL tool in Replit.")
        return
    try:
        import bootstrap_local  # webApp/bootstrap_local.py
        bootstrap_local.main()
    except Exception as exc:  # non-fatal: the app can still serve static pages
        print(f"[run_replit] DB bootstrap skipped/failed (non-fatal): {exc}")

    # Optional realistic (fake) demo data, so the app looks populated. Enabled
    # via SEED_DEMO=1. Idempotent — seed_demo() skips if students already exist.
    if os.environ.get("SEED_DEMO") == "1":
        import seed_demo  # webApp/seed_demo.py
        with app.app_context():
            # Core data first, then the extras that top up every other area.
            # Both are idempotent and wrapped so one failure can't block the other.
            try:
                seed_demo.seed_demo()
            except Exception as exc:
                print(f"[run_replit] core demo seed failed (non-fatal): {exc}")
            try:
                seed_demo.seed_extras()
            except Exception as exc:
                print(f"[run_replit] extra demo seed failed (non-fatal): {exc}")


if __name__ == "__main__":
    _bootstrap_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")),
            debug=False, use_reloader=False)
