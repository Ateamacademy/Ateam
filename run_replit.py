#!/usr/bin/env python3
"""Replit entrypoint for the A-Team webApp (Flask).

Replit's PostgreSQL add-on provides DATABASE_URL automatically. Set SECRET_KEY
(and MAIL_NOREPLY_PASSWORD / MAIL_EXAMS_PASSWORD if outbound email is needed)
in the Secrets pane. On the first run, bootstrap the database:

    python3 webApp/bootstrap_local.py

then log in with admin@local / AdminLocal1. See README-REPLIT.md for details.
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(BASE, "webApp")

sys.path.insert(0, APP_DIR)
os.chdir(APP_DIR)  # the app resolves file paths relative to this directory

from webApp import app  # noqa: E402

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")),
            debug=False, use_reloader=False)
