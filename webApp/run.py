#!/usr/bin/env python3
"""
Start the A-Team webApp locally.

USAGE
-----
From a normal Windows terminal (PowerShell / cmd / Windows Terminal):

    wsl -d Ubuntu -u root -- python3 /var/www/webApp/run.py

  ...or, if you have Python installed on Windows, just:

    python run.py            (this file bridges itself into WSL automatically)

From inside the Ubuntu (WSL) shell:

    python3 /var/www/webApp/run.py

Then open http://localhost:5000  and log in with  admin@local / AdminLocal1
Press Ctrl+C to stop.

The script takes care of: starting PostgreSQL, using the correct virtualenv,
setting PYTHONPATH so `from webApp import app` resolves, and running the server.
"""
import os
import re
import sys
import time
import signal
import subprocess

VENV_DIR = "/root/ateam-venv"
VENV_PYTHON = VENV_DIR + "/bin/python"
APP_DIR = "/var/www/webApp"
HOST = "127.0.0.1"
PORT = 5000


def run_on_windows():
    """We're on Windows: re-launch this same script inside WSL Ubuntu."""
    cmd = ["wsl", "-d", "Ubuntu", "-u", "root", "--",
           "python3", "/var/www/webApp/run.py"]
    try:
        sys.exit(subprocess.call(cmd))
    except FileNotFoundError:
        sys.exit("ERROR: 'wsl' not found. Is WSL installed and on PATH?")


def free_port(port):
    """Stop any process already listening on `port` (a previous run of this app)."""
    try:
        out = subprocess.check_output(
            ["ss", "-H", "-ltnp", "sport = :%d" % port],
            text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return
    pids = {int(p) for p in re.findall(r"pid=(\d+)", out)} - {os.getpid()}
    if not pids:
        return
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    time.sleep(1.5)
    for pid in pids:                      # force-kill any survivors
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    print("  (stopped previous instance on port %d: pid %s)"
          % (port, ", ".join(map(str, sorted(pids)))))


def run_on_linux():
    """We're inside WSL/Linux: ensure venv + Postgres, then serve."""
    # 1) Make sure we're running under the project's virtualenv.
    #    (Compare sys.prefix, not the interpreter path: the venv's `python`
    #     is a symlink to the system interpreter, so realpath would match.)
    if os.path.exists(VENV_PYTHON) and os.path.abspath(sys.prefix) != VENV_DIR:
        os.execv(VENV_PYTHON, [VENV_PYTHON, os.path.abspath(__file__)])

    # 2) Start PostgreSQL (no-op if already running).
    subprocess.call(["service", "postgresql", "start"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 2b) Stop any previous instance still holding the port.
    free_port(PORT)

    # 3) Make the package importable exactly like production's wsgi does.
    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)
    os.chdir(APP_DIR)

    # 4) Import and run. (reloader off: APScheduler double-starts under it.)
    from webApp import app
    print(f"\n  A-Team webApp -> http://localhost:{PORT}")
    print("  login: admin@local / AdminLocal1   (Ctrl+C to stop)\n")
    # Werkzeug's interactive debugger allows remote code execution; only
    # enable it when explicitly requested via FLASK_DEBUG=1.
    debug = os.environ.get("FLASK_DEBUG", "") == "1"
    app.run(host=HOST, port=PORT, debug=debug, use_reloader=False)


if __name__ == "__main__":
    if os.name == "nt":
        run_on_windows()
    else:
        run_on_linux()
