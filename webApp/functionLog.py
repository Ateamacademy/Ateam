from datetime import date, timedelta
from EmailSender import * 
from Schema import *
import time
import re
import os
import random 
import string
import smtplib
from flask import render_template_string


def addToLog(role, message):
    db.session.add(log(role = role, message=message, date=datetime.datetime.utcnow()))
    db.session.commit()
