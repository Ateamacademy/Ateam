"""
Local dev entrypoint for webApp.

Run from the OUTER webApp directory (the one that CONTAINS the `webApp` package),
e.g. /var/www/webApp:

    PYTHONPATH=/var/www/webApp python3 run_local.py

This mirrors how production's webapp.wsgi imports the app
(`from webApp import app`). Running it any other way breaks the
top-level `from Schema import *` / `from functions import *` imports.
"""
from webApp import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
