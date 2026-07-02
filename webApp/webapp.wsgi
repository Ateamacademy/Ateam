#!/usr/bin/python
import sys
import os
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/webApp/")

from webApp import app as application
# Only override the key when SECRET_KEY is explicitly set; otherwise keep the
# random per-process key the app generated (never a publicly known constant).
if os.environ.get("SECRET_KEY"):
    application.secret_key = os.environ["SECRET_KEY"]
