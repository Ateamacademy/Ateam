from datetime import date, timedelta
from flask import Flask, render_template, render_template_string
from EmailSender import * 
from Schema import *
import PyPDF2
import time
import re
import os
import random 
import string
import smtplib
from flask import render_template_string
from jinja2 import Template
import calendar
from io import BytesIO

# PDF / chart generation libraries. These load native system libraries (pango,
# cairo, poppler, ...) that can be missing in some deployments; keep the app
# booting even if they're unavailable — the affected PDF/report features then
# fail only when actually used, instead of taking down the whole app.
try:
    from weasyprint import HTML
except Exception:
    HTML = None
try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.utils import ImageReader
except Exception:
    canvas = landscape = A4 = ImageReader = None
try:
    from pdf2image import convert_from_path
except Exception:
    convert_from_path = None

os.environ['MPLCONFIGDIR'] = os.getcwd() + "/configs/"
try:
    import matplotlib
    matplotlib.use("Agg")  # headless backend
    import matplotlib.pyplot as plt
except Exception:
    plt = None




def day_to_num(day):
    if day == "MON":
        return 0
    elif day == "TUE":
        return 1
    elif day == "WED":
        return 2
    elif day == "THU":
        return 3
    elif day == "FRI":
        return 4
    elif day == "SAT":
        return 5
    elif day == "SUN":
        return 6
    else:
        return 0
    
def num_to_day(num):
    if num == 0:
        return "MON"
    elif num==1:
        return "TUE"
    elif num==2:
        return "WED"
    elif num==3:
        return "THU"
    elif num==4:
        return "FRI"
    elif num==5:
        return "SAT"
    elif num==6:
        return "SUN"
 
def num_to_month(num):
    if num == 1: 
        return "January"
    elif num == 2: 
        return "February"
    elif num == 3: 
        return "March"
    elif num == 4: 
        return "April"
    elif num == 5: 
        return "May"
    elif num == 6: 
        return "June"
    elif num == 7: 
        return "July"
    elif num == 8: 
        return "August"
    elif num == 9: 
        return "September"
    elif num == 10: 
        return "October"
    elif num == 11: 
        return "November"
    elif num == 12:
        return "December"
 
def gen_academic_year():
    today = date.today()
    month = today.month
    
    if month>=9 and month<=12:
        academicYear = str(today.year) + "-" + str(today.year+1)
    else:
        academicYear = str(today.year-1) + "-" + str(today.year)
    
    return academicYear

def gen_relative_academic_year(difference):
    today = date.today()
    month = today.month
    
    if month>=9 and month<=12:
        academicYear = str(today.year+difference) + "-" + str(today.year+difference+1)
    else:
        academicYear = str(today.year+difference-1) + "-" + str(today.year+difference)
    
    return academicYear

def gen_offset_academic_year(difference):
    today = date.today() + timedelta(days=difference)
    month = today.month

    if month>=9 and month<=12:
        academicYear = str(today.year) + "-" + str(today.year+1)
    else:
        academicYear = str(today.year-1) + "-" + str(today.year)
    
    return academicYear

def add_hour(time):
    num = int(time[:2])
    num = num + 1
    
    newTime = str(num) + time[2:]
    
    if len(newTime) < 8:
        newTime = "0" + newTime
    
    return newTime

def next_weekday(d, weekday):
    '''
    0-MON, 1-TUE, 2-WED...
    '''
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
        
    return d + timedelta(days_ahead)

#offset is in days
def gen_week_no(offset):
    today = date.today() + timedelta(days=offset)
        
    # Find the first Monday in the most recent September
    year = today.year if today.month >= 9 else today.year - 1
    september_first = date(year, 9, 1)
    while september_first.weekday() != 0:  # Monday is 0
        september_first += timedelta(days=1)
    
    # Calculate the difference in weeks from that Monday to today
    difference = (today - september_first).days // 7
    
    # Week number starts from 1
    week_number = difference + 1
    
    return str(week_number)

#NOT BROKEN - Works because gen_week_no is offset from current day
def dateToWeekNo(targetDate):
    difference = targetDate - date.today()
    
    return gen_week_no(difference.days)

def weekNoToDate(weekNo):
    today = date.today()
    year = today.year if today.month >= 9 else today.year - 1
    september_first = date(year, 9, 1)
    
    while september_first.weekday() != 0:  # Monday is 0
        september_first += timedelta(days=1)
        
    begin = september_first + timedelta(days=(weekNo - 2) * 7)
    end = begin + timedelta(days=6)

    return begin.strftime("%d/%m/%Y") + " - " + end.strftime("%d/%m/%Y")

def dateToDay(targetDate):
    '''  '''
    given_date = datetime.datetime.strptime(targetDate, '%d/%m/%Y')
    day = given_date.weekday()
    
    return num_to_day(day)

def isWeek(day):
    if(day == "MON" or day == "TUE" or day == "WED" or day == "THU" or day == "FRI"):
        return True
    else:
        return False

def getDaysSinceLesson(lessonID, weekNo):
    currentWeekNo = int(gen_week_no(0))
    currentDay = dateToDay(datetime.date.today().strftime('%d/%m/%Y'))
    
    if (currentWeekNo < int(weekNo)) or (currentWeekNo == weekNo and day_to_num(currentDay) < day_to_num(getLessonDay(lessonID))):
        return "lesson is in future"
    
    initial = (currentWeekNo - int(weekNo))*7
    result = int(initial) + (day_to_num(currentDay) - day_to_num(getLessonDay(lessonID)))
    
    if result <= 5: 
        return result
    else:
        return "X"

                                  
def append_to_html(original_html, html_to_append):
    return original_html[:-6] + html_to_append + original_html[-6:]

def generate_timetable(lessons):
    html = []
    for i in range(91):        
        html.append("<div class=\"col\" style=\" padding-top: 1px; padding-bottom: 1px;\"> </div>")
            
    # html.append("</div>")
        
    
    for lesson in lessons:
        start_time = lesson[3][:2]
        odd_number = 2 * (int(start_time) - 8) + 1
        # html[((int(start_time) - 8)*7) + day_to_num(lesson[2])] = "<div> <form action=\"/Classroom_View?lessonid=" + str(lesson[0]) + "&year=" + gen_academic_year() + "&" + "weekNo=" + gen_week_no() + "\" " +  "method = \"POST\"> <button class=\"accent-green-gradient\">" + lesson[6] + "</button> </form> </div>"
        html[((int(start_time) - 8)*7) + day_to_num(lesson[2])] = append_to_html(html[((int(start_time) - 8)*7) + day_to_num(lesson[2])], "<div class=\"row lessonButton\"> <div class=\"col\" style=\"padding-right:1px; padding-left:1px;\"> <a href=\"/Classroom_View_Home?lessonid=" + str(lesson[0]) + "&year=" + gen_academic_year() + "&" + "weekNo=" + gen_week_no() + "\" " +  "> <button class=\"accent-green-gradient\" style=\"padding-left:2px; padding-right:2px;\"> <p class=\"mb-0\"> " + lesson[6] + " - " + lesson[7] + "</p> </button> </a> </div> </div>")

    '''
    13*7
    7 X 8ams 
    7 X 9ams...
    
    MON-8
    TUE-8
    WED-8
    '''    
    return html

def generate_admin_day_timetable(lessons):
    html = []
    for i in range(91):        
        html.append("<div class=\"col\" style=\" padding-top: 1px; padding-bottom: 1px;\"> </div>")
            
    for lesson in lessons:
        start_time = lesson[3][:2]
        odd_number = 2 * (int(start_time) - 8) + 1
        # html[((int(start_time) - 8)*7) + day_to_num(lesson[2])] = "<div> <form action=\"/Classroom_View?lessonid=" + str(lesson[0]) + "&year=" + gen_academic_year() + "&" + "weekNo=" + gen_week_no() + "\" " +  "method = \"POST\"> <button class=\"accent-green-gradient\">" + lesson[6] + "</button> </form> </div>"
        html[((int(start_time) - 8)) + day_to_num(lesson[2])] = append_to_html(html[((int(start_time) - 8)*7) + day_to_num(lesson[2])], "<div class=\"row lessonButton\"> <div class=\"col\" style=\"padding-right:1px; padding-left:1px;\"> <a href=\"/Classroom_View_Home?lessonid=" + str(lesson[0]) + "&year=" + gen_academic_year() + "&" + "weekNo=" + gen_week_no() + "\" " +  "> <button class=\"accent-green-gradient\" style=\"padding-left:2px; padding-right:2px;\"> <p class=\"mb-0\"> " + lesson[6] + " - " + lesson[7] + "</p> </button> </a> </div> </div>")

    return html      
        
def generate_filename_to_upload(topic):
    day = date.today()
    day = day.strftime("%d%m%Y")

    t = time.localtime()
    current_time = time.strftime("%H%M%S", t)
    
    topic = re.sub(r'[^\w\s]', '', topic)             #filter all the alphanumeric characters out
    topic = topic.replace(" ", "_") 

    return topic + "__" + day + "_" + current_time + ".pdf"

def make_topic_folder(topic):
    os.makedirs("/var/www/webApp/webApp/files/" + topic.replace(" ", "-").upper())  

#only run once
def make_all_topics():
    #standard subjects
    for level in ['KS1', 'KS2', 'KS3', 'GCSE', 'ALEVEL']:
        for subject in ['MATHS', 'ENGLISH']:
            make_topic_folder(level + "-" + subject)
    
    #other Subjects
    for level in ['GCSE', 'ALEVEL']:
        for subject in ['COMPUTER-SCIENCE', 'BIOLOGY', 'CHEMISTRY', 'PHYSICS', 'FURTHER-MATHS', 'BUSINESS', 'HISTORY', 'GEOGRAPHY', 'ECONOMICS']:
            make_topic_folder(level + "-" + subject)
            
    make_topic_folder("11_PLUS")    
    
def studentListToString(studentList):
    string = ""
    
    for student in studentList:
        if "undefined" not in student:
            if "temp" in student:
                string = string + student + ", "
            else:
                string = string + getStudent(student) + ", "
    
    return string
    
def gen_username(first, second):
    return first[:3] + second[:3] + str(date.today().year)[-2:]

def gen_date():
    day = date.today()
    
    if int(day.day) < 10:
        dayString = "0"+ str(day.day)
    else: 
        dayString = str(day.day)
        
    if int(day.month) < 10:
        monthString = "0" + str(day.month)
    else: 
        monthString = str(day.month)
        
    return str(day.year) + "-" + monthString + "-" + dayString

def getSignature():
    signature = """
    
    <table border="0" width="450" cellspacing="0" cellpadding="0">
    <tbody>
    <tr>
    <td valign="top">
    <table border="0" width="100%" cellspacing="0" cellpadding="0">
    <tbody>
    <tr>
    <td style="padding-right: 10px; border-right: 1px solid #0f6aa4;" width="33%">
    <table border="0" width="100%" cellspacing="0" cellpadding="0">
    <tbody>
    <tr>
    <td align="center"><a> <img src="https://i.imgur.com/Xhd6PqP.png" width="161" height="75" /></a></td>
    </tr>
    </tbody>
    </table>
    </td>
    <td>
    <table border="0" width="100%" cellspacing="0" cellpadding="0">
    <tbody>
    <tr>
    <td style="padding-left: 10px;" valign="bottom">
    <table border="0" width="100%" cellspacing="0" cellpadding="0">
    <tbody>
    <tr>
    <td style="font-family: 'Roboto', sans-serif; font-size: 16px; line-height: 18px; font-weight: 600; color: #637e78; padding-top: 6px;" width="250"><span style="font-family: 'Roboto', sans-serif; font-size: 14px; line-height: 18px; font-weight: bold; color: #000;"> A-Team Academy </span> <br /><span style="font-family: 'Roboto', sans-serif; font-size: 12px; line-height: 18px; font-weight: bold; color: #a6a6a6;"> Exams Officer </span></td>
    </tr>
    <tr>
    <td width="100%">
    <table border="0" cellspacing="0" cellpadding="0">
    <tbody>
    <tr>
    <td width="100%">
    <table border="0" cellspacing="0" cellpadding="2">
    <tbody>
    <tr>
    <td style="font-family: 'Roboto', sans-serif; font-size: 13px; line-height: 14px; font-weight: 500; color: #a6a6a6;"><a style="font-family: 'Roboto', sans-serif; color: #fff !important; text-decoration: none !important;"><span style="font-family: 'Roboto', sans-serif; color: #a6a6a6; text-decoration: none;"> 0121 517 0110 </span></a></td>
    </tr>
    <tr>
    <td style="font-family: 'Roboto', sans-serif; font-size: 13px; line-height: 14px; font-weight: 500; color: #a6a6a6;"><a style="font-family: 'Roboto', sans-serif; color: #fff !important; text-decoration: none !important;" href="mailto:info@ateamacademy.co.uk"><span style="font-family: 'Roboto', sans-serif; color: #a6a6a6; text-decoration: none;">examsofficer@ateamacademy.co.uk </span></a></td>
    </tr>
    <tr>
    <td style="font-family: 'Roboto', sans-serif; font-size: 13px; line-height: 14px; font-weight: 500; color: #000;"><a style="font-family: 'Roboto', sans-serif; color: #0f6aa4 !important; text-decoration: none !important; font-weight: bold;" href="https://ateamacademy.co.uk/">ateamacademy.co.uk</a></td>
    </tr>
    <tr>
    <td style="font-family: 'Roboto', sans-serif; font-size: 13px; line-height: 14px; font-weight: 500; color: #000;"><a style="font-family: 'Roboto', sans-serif; color: #0f6aa4 !important; text-decoration: none !important; font-weight: bold;" href="https://ateamacad.co.uk/">ateamacad.co.uk</a></td>
    </tr>
    </tbody>
    </table>
    </td>
    </tr>
    </tbody>
    </table>
    </td>
    </tr>
    <tr>
    <td align="center">
    <table border="0" width="100%" cellspacing="5" cellpadding="0">
    <tbody>
    <tr>
    <td style="line-height: 14px; font-weight: bold; color: #647875;"><a href="https://www.instagram.com/ateamacad/?hl=en-gb"><img src="https://i.imgur.com/jJYDurj.png" alt="" width="20" height="20" /></a>  <a href="https://www.youtube.com/@ateamacad"><img src="https://i.imgur.com/0hNKzSu.png" alt="" width="20" height="20" /></a>  <a href="https://www.tiktok.com/@ateamacad"><img src="https://i.imgur.com/54lRT4V.png" alt="" width="20" height="20" /></a>  <a href="https://www.linkedin.com/company/98067317"><img src="https://i.imgur.com/0ITebQX.png" alt="" width="20" height="20" /></a></td>
    </tr>
    </tbody>
    </table>
    </td>
    </tr>
    </tbody>
    </table>
    </td>
    </tr>
    </tbody>
    </table>
    </td>
    </tr>
    </tbody>
    </table>
    </td>
    </tr>
    </tbody>
    </table>

    """
    
    return signature

def gen_html(message): 
    head = """ 
        <!DOCTYPE html>
        <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>A-Team Academy</title>
        </head>
        <body>
        """
        
    signature = """
    
    <table border="0" width="450" cellspacing="0" cellpadding="0">
    <tbody>
    <tr>
    <td valign="top">
    <table border="0" width="100%" cellspacing="0" cellpadding="0">
    <tbody>
    <tr>
    <td style="padding-right: 10px; border-right: 1px solid #0f6aa4;" width="33%">
    <table border="0" width="100%" cellspacing="0" cellpadding="0">
    <tbody>
    <tr>
    <td align="center"><a> <img src="https://i.imgur.com/Xhd6PqP.png" width="161" height="75" /></a></td>
    </tr>
    </tbody>
    </table>
    </td>
    <td>
    <table border="0" width="100%" cellspacing="0" cellpadding="0">
    <tbody>
    <tr>
    <td style="padding-left: 10px;" valign="bottom">
    <table border="0" width="100%" cellspacing="0" cellpadding="0">
    <tbody>
    <tr>
    <td style="font-family: 'Roboto', sans-serif; font-size: 16px; line-height: 18px; font-weight: 600; color: #637e78; padding-top: 6px;" width="250"><span style="font-family: 'Roboto', sans-serif; font-size: 14px; line-height: 18px; font-weight: bold; color: #000;"> A-Team Academy </span> <br /><span style="font-family: 'Roboto', sans-serif; font-size: 12px; line-height: 18px; font-weight: bold; color: #a6a6a6;"> Exams Officer </span></td>
    </tr>
    <tr>
    <td width="100%">
    <table border="0" cellspacing="0" cellpadding="0">
    <tbody>
    <tr>
    <td width="100%">
    <table border="0" cellspacing="0" cellpadding="2">
    <tbody>
    <tr>
    <td style="font-family: 'Roboto', sans-serif; font-size: 13px; line-height: 14px; font-weight: 500; color: #a6a6a6;"><a style="font-family: 'Roboto', sans-serif; color: #fff !important; text-decoration: none !important;"><span style="font-family: 'Roboto', sans-serif; color: #a6a6a6; text-decoration: none;"> 0121 517 0110 </span></a></td>
    </tr>
    <tr>
    <td style="font-family: 'Roboto', sans-serif; font-size: 13px; line-height: 14px; font-weight: 500; color: #a6a6a6;"><a style="font-family: 'Roboto', sans-serif; color: #fff !important; text-decoration: none !important;" href="mailto:info@ateamacademy.co.uk"><span style="font-family: 'Roboto', sans-serif; color: #a6a6a6; text-decoration: none;">examsofficer@ateamacademy.co.uk </span></a></td>
    </tr>
    <tr>
    <td style="font-family: 'Roboto', sans-serif; font-size: 13px; line-height: 14px; font-weight: 500; color: #000;"><a style="font-family: 'Roboto', sans-serif; color: #0f6aa4 !important; text-decoration: none !important; font-weight: bold;" href="https://ateamacademy.co.uk/">ateamacademy.co.uk</a></td>
    </tr>
    </tbody>
    </table>
    </td>
    </tr>
    </tbody>
    </table>
    </td>
    </tr>
    <tr>
    <td align="center">
    <table border="0" width="100%" cellspacing="5" cellpadding="0">
    <tbody>
    <tr>
    <td style="line-height: 14px; font-weight: bold; color: #647875;"><a href="https://www.instagram.com/ateamacad/?hl=en-gb"><img src="https://i.imgur.com/jJYDurj.png" alt="" width="20" height="20" /></a>  <a href="https://www.youtube.com/@ateamacad"><img src="https://i.imgur.com/0hNKzSu.png" alt="" width="20" height="20" /></a>  <a href="https://www.tiktok.com/@ateamacad"><img src="https://i.imgur.com/54lRT4V.png" alt="" width="20" height="20" /></a>  <a href="https://www.linkedin.com/company/98067317"><img src="https://i.imgur.com/0ITebQX.png" alt="" width="20" height="20" /></a></td>
    </tr>
    </tbody>
    </table>
    </td>
    </tr>
    </tbody>
    </table>
    </td>
    </tr>
    </tbody>
    </table>
    </td>
    </tr>
    </tbody>
    </table>
    </td>
    </tr>
    </tbody>
    </table>

    """

    end = "</body>"
    
    return head + message + signature + end
    
def gen_html_report_card(studentID, grades, period=""):
    html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Ace Your Report Card, {{ name }}!</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; color: #333;">

            <h1 style="text-align: center; color: #0066cc;">🌟 Your {{ period }} Report Card, {{ name }}! 🌟</h1>

            <table style="width: 100%; border-collapse: collapse; margin-top: 20px; background-color: #fff; border: 1px solid #ddd;">
                <thead>
                    <tr>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #0066cc; color: #fff;">Test Name</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #0066cc; color: #fff;">Score</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #0066cc; color: #fff;">Grade</th>
                    </tr>
                </thead>
                <tbody>
                {% for test in tests %}
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: left;"> 📚 {{ test.name }} </td>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: left;"> {{ test.mark }} / {{ test.total }} </td>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: left;"> {{ test.grade }} </td>
                    </tr>
                {% endfor %}
                
                </tbody>
            </table>
            <p style="text-align: center; margin-top: 20px; color: #0066cc;"> Questions or concerns? Don't hesitate to reach out at <a href="mailto:safwaan@ateamacademy.co.uk" style="color: #0066cc; text-decoration: none;">safwaan@ateamacademy.co.uk</a>! </p>

        </body>
        </html>


        """ + getSignature()
        
        
    tests = []
    for grade in grades:
        gradeEntry = Grades.query.filter_by(gradeID = grade).first()
        testID = gradeEntry.testID 
        testEntry = Tests.query.filter_by(testID = testID).first()
        
        mark = gradeEntry.mark
        grade = gradeEntry.grade
        total = testEntry.total
        name = testEntry.name
        
        tests.append({"name" : name, "mark" : mark, "grade" : grade, "total" : total})
            
    html_content = render_template_string(html_template, name = getStudent(studentID), tests = tests, period=period)

    return html_content
    
#creates email for a student registration
def confirmRegistration(name):
    html = """

    <div class="container" style = " width: 80%;
        margin: 0 auto;
        padding: 50px;
        background-color: #fff;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        margin-top: 50px;" >
      <h1 style = "color: #3498db;" >Registration Confirmation for """ + name + """ </h1>
      <p class="confirmation-text" style = "color: #3498db; font-weight: bold; font-size: 1.2em; >Thank you for registering on our website!</p>
      <p style = " font-size: 1.2em; " >Your registration is complete and you will soon be able to access all the features of our website. Your password will arrive shortly in a second email. </p>
      <p style = " font-size: 1.2em; " >If you have any questions or need further assistance, feel free to contact us.</p>
    </div>

    """

    return gen_html(html)

def confirmRegistrationSiblings():
    html = """

    <style>
      body {
        font-family: Arial, sans-serif;
        background-color: #f0f0f0;
        color: #000;
      }

      .container {
        width: 80%;
        margin: 0 auto;
        padding: 50px;
        background-color: #fff;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        margin-top: 50px;
      }

      h1 {
        color: #3498db;
      }

      p {
        font-size: 1.2em;
      }

      .confirmation-text {
        color: #3498db;
        font-weight: bold;
      }

    </style>

    <div class="container">
      <h1>Registration Confirmation </h1>
      <p class="confirmation-text">Thank you for registering on our website!</p>
      <p>Your registration is complete and you will soon be able to access all the features of our website.</p>
      <p>If you have any questions or need further assistance, feel free to contact us.</p>
    </div>

    """

    return gen_html(html)
    
def gen_html_password_reset(name, newPassword):
    html = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html dir="ltr" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office"><head><meta charset="UTF-8"><meta content="width=device-width, initial-scale=1" name="viewport"><meta name="x-apple-disable-message-reformatting"><meta http-equiv="X-UA-Compatible" content="IE=edge"><meta content="telephone=no" name="format-detection"><title></title><!--[if (mso 16)]>
    <style type="text/css">
    a {text-decoration: none;}
    </style>
    <![endif]--><!--[if gte mso 9]><style>sup { font-size: 100% !important; }</style><![endif]--><!--[if gte mso 9]>
        <xml>
            <o:OfficeDocumentSettings>
            <o:AllowPNG></o:AllowPNG>
            <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
        <![endif]--><!--[if mso]>
        <style type="text/css">
            ul {
        margin: 0 !important;
        }
        ol {
        margin: 0 !important;
        }
        li {
        margin-left: 47px !important;
        }

        </style><![endif]
    --></head><body class="body"><div dir="ltr" class="es-wrapper-color"><!--[if gte mso 9]>
			<v:background xmlns:v="urn:schemas-microsoft-com:vml" fill="t">
				<v:fill type="tile" color="#fafafa"></v:fill>
			</v:background>
		<![endif]--><table class="es-wrapper" width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-email-paddings" valign="top"><table cellpadding="0" cellspacing="0" class="es-content esd-header-popover" align="center"><tbody><tr><td class="es-adaptive esd-stripe" align="center"><table class="es-content-body" style="background-color: transparent;" width="600" cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center"><tbody><tr><td class="esd-structure es-p10" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="580" valign="top" align="center"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td align="center" class="es-infoblock esd-block-text"></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table><table class="es-content" cellspacing="0" cellpadding="0" align="center"><tbody><tr><td class="esd-stripe" style="background-color: #fafafa;" bgcolor="#fafafa" align="center"><table class="es-content-body" style="background-color: #ffffff;" esd-img-prev-src="" width="600" cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center"><tbody><tr><td class="esd-structure es-p40t es-p20r es-p20l" style="background-color: transparent; background-position: left top;" esd-img-prev-src="https://fkus.stripocdn.email/content/guids/CABINET_8a8240f4650bd716d3cd69675fe184ca/images/1041555765740937.png" esd-img-prev-position="left top" esd-img-prev-repeat="no-repeat" bgcolor="transparent" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="560" valign="top" align="center"><table esd-img-prev-src="" esd-img-prev-position="left top" style="background-position: left top;" width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-block-image es-p5t es-p5b" align="center" style="font-size:0"><a target="_blank"><img src="https://ecrugam.stripocdn.email/content/guids/CABINET_dd354a98a803b60e2f0411e893c82f56/images/23891556799905703.png" alt="" style="display: block;" width="175"></a></td></tr><tr><td class="esd-block-text es-p15t es-p15b" align="center"><h1 style="color: #333333; font-size: 20px;">

        <strong>FORGOT YOUR </strong></h1><h1 style="color: #333333; font-size: 20px;"><strong>&nbsp;PASSWORD?</strong></h1></td></tr><tr><td class="esd-block-text es-p40r es-p40l" align="left"> 
    
    <p style="text-align: center;">HI ''' + name + '''</p></td></tr><tr><td class="esd-block-text es-p35r es-p40l" align="left"> 
        
        <p style="text-align: center;">There was a request to change your password!</p></td></tr><tr><td class="esd-block-text es-p25t es-p40r es-p40l" align="center"> 
            
            <p>If did not make this request please let someone know otherwise your new password is below:&nbsp;</p>
            
            <p>
            ''' + newPassword + '''
            <br>
            </p> 
            
           </td></tr></tbody></table></td></tr></tbody></table></td></tr><tr><td class="esd-structure es-p5t es-p20b es-p20r es-p20l" esd-img-prev-src="" esd-img-prev-position="left top" style="background-position: left top;" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="560" valign="top" align="center"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td align="center" class="esd-empty-container" style="display: none;"></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table><table class="es-footer" cellspacing="0" cellpadding="0" align="center"><tbody><tr><td class="esd-stripe" style="background-color: #fafafa;" bgcolor="#fafafa" align="center"><table class="es-footer-body" esd-img-prev-src="" width="600" cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center"><tbody><tr><td class="esd-structure es-p10t es-p30b es-p20r es-p20l" style=" background-color: #0b5394; background-position: left top;" esd-img-prev-src="" esd-img-prev-position="left top" bgcolor="#0b5394" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="560" valign="top" align="center"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-block-text es-p5t es-p5b" align="left"><h2 style="font-size: 16px; color: #ffffff;"><strong>Have questions?</strong></h2></td></tr><tr><td esd-links-underline="none" esd-links-color="#ffffff" class="esd-block-text es-p5b" align="left"><p style="font-size: 14px; color: #ffffff;">Please contact Safwaan at safwaan@ateamacademy.co.uk<a target="_blank" style="font-size: 14px; text-decoration: none; color: #ffffff;"></a></p></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table><table class="es-content esd-footer-popover" cellspacing="0" cellpadding="0" align="center"><tbody><tr><td class="esd-stripe" style="background-color: #fafafa;" bgcolor="#fafafa" align="center"><table class="es-content-body" style="background-color: transparent;" esd-img-prev-src="" width="600" cellspacing="0" cellpadding="0" bgcolor="transparent" align="center"><tbody><tr><td class="esd-structure es-p15t" esd-img-prev-src="" esd-img-prev-position="left top" style="background-position: left top;" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="600" valign="top" align="center"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-block-spacer es-p20b es-p20r es-p20l" align="center" style="font-size:0"><table width="100%" height="100%" cellspacing="0" cellpadding="0" border="0"><tbody><tr><td style="border-bottom: 1px solid #fafafa; background: none; height: 1px; width: 100%; margin: 0px;"></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></div></body></html>'''
            
    return html

def gen_html_password_creation(name, newPassword):
    html = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html dir="ltr" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office"><head><meta charset="UTF-8"><meta content="width=device-width, initial-scale=1" name="viewport"><meta name="x-apple-disable-message-reformatting"><meta http-equiv="X-UA-Compatible" content="IE=edge"><meta content="telephone=no" name="format-detection"><title></title><!--[if (mso 16)]>
    <style type="text/css">
    a {text-decoration: none;}
    </style>
    <![endif]--><!--[if gte mso 9]><style>sup { font-size: 100% !important; }</style><![endif]--><!--[if gte mso 9]>
        <xml>
            <o:OfficeDocumentSettings>
            <o:AllowPNG></o:AllowPNG>
            <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
        <![endif]--><!--[if mso]>
        <style type="text/css">
            ul {
        margin: 0 !important;
        }
        ol {
        margin: 0 !important;
        }
        li {
        margin-left: 47px !important;
        }

        </style><![endif]
    --></head><body class="body"><div dir="ltr" class="es-wrapper-color"><!--[if gte mso 9]>
			<v:background xmlns:v="urn:schemas-microsoft-com:vml" fill="t">
				<v:fill type="tile" color="#fafafa"></v:fill>
			</v:background>
		<![endif]--><table class="es-wrapper" width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-email-paddings" valign="top"><table cellpadding="0" cellspacing="0" class="es-content esd-header-popover" align="center"><tbody><tr><td class="es-adaptive esd-stripe" align="center"><table class="es-content-body" style="background-color: transparent;" width="600" cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center"><tbody><tr><td class="esd-structure es-p10" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="580" valign="top" align="center"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td align="center" class="es-infoblock esd-block-text"></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table><table class="es-content" cellspacing="0" cellpadding="0" align="center"><tbody><tr><td class="esd-stripe" style="background-color: #fafafa;" bgcolor="#fafafa" align="center"><table class="es-content-body" style="background-color: #ffffff;" esd-img-prev-src="" width="600" cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center"><tbody><tr><td class="esd-structure es-p40t es-p20r es-p20l" style="background-color: transparent; background-position: left top;" esd-img-prev-src="https://fkus.stripocdn.email/content/guids/CABINET_8a8240f4650bd716d3cd69675fe184ca/images/1041555765740937.png" esd-img-prev-position="left top" esd-img-prev-repeat="no-repeat" bgcolor="transparent" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="560" valign="top" align="center"><table esd-img-prev-src="" esd-img-prev-position="left top" style="background-position: left top;" width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-block-image es-p5t es-p5b" align="center" style="font-size:0"><a target="_blank"><img src="https://ecrugam.stripocdn.email/content/guids/CABINET_dd354a98a803b60e2f0411e893c82f56/images/23891556799905703.png" alt="" style="display: block;" width="175"></a></td></tr><tr><td class="esd-block-text es-p15t es-p15b" align="center"><h1 style="color: #333333; font-size: 20px;">

        <strong>    Here is your password </strong></h1><h1 style="color: #333333; font-size: 20px;"></h1></td></tr><tr><td class="esd-block-text es-p40r es-p40l" align="left"> 
    
    <p style="text-align: center;">HI ''' + name + '''</p></td></tr><tr><td class="esd-block-text es-p35r es-p40l" align="left"> 
        
        <p style="text-align: center;">This is your password to log on to <a href="https://ateamacad.co.uk"> ateamacad.co.uk </a> where you can find your grades, classwork, homework and more!</p></td></tr><tr><td class="esd-block-text es-p25t es-p40r es-p40l" align="center"> 
            
            <p>Your new password is below:&nbsp;</p>
            
            <p>
            ''' + newPassword + '''
            <br>
            </p> 
            
            <p>Please change your password once you have logged on</p></td></tr></tbody></table></td></tr></tbody></table></td></tr><tr><td class="esd-structure es-p5t es-p20b es-p20r es-p20l" esd-img-prev-src="" esd-img-prev-position="left top" style="background-position: left top;" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="560" valign="top" align="center"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td align="center" class="esd-empty-container" style="display: none;"></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table><table class="es-footer" cellspacing="0" cellpadding="0" align="center"><tbody><tr><td class="esd-stripe" style="background-color: #fafafa;" bgcolor="#fafafa" align="center"><table class="es-footer-body" esd-img-prev-src="" width="600" cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center"><tbody><tr><td class="esd-structure es-p10t es-p30b es-p20r es-p20l" style=" background-color: #0b5394; background-position: left top;" esd-img-prev-src="" esd-img-prev-position="left top" bgcolor="#0b5394" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="560" valign="top" align="center"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-block-text es-p5t es-p5b" align="left"><h2 style="font-size: 16px; color: #ffffff;"><strong>Have questions?</strong></h2></td></tr><tr><td esd-links-underline="none" esd-links-color="#ffffff" class="esd-block-text es-p5b" align="left"><p style="font-size: 14px; color: #ffffff;">Please contact Safwaan at safwaan@ateamacademy.co.uk <a target="_blank" style="font-size: 14px; text-decoration: none; color: #ffffff;"> </a></p></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table><table class="es-content esd-footer-popover" cellspacing="0" cellpadding="0" align="center"><tbody><tr><td class="esd-stripe" style="background-color: #fafafa;" bgcolor="#fafafa" align="center"><table class="es-content-body" style="background-color: transparent;" esd-img-prev-src="" width="600" cellspacing="0" cellpadding="0" bgcolor="transparent" align="center"><tbody><tr><td class="esd-structure es-p15t" esd-img-prev-src="" esd-img-prev-position="left top" style="background-position: left top;" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="600" valign="top" align="center"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-block-spacer es-p20b es-p20r es-p20l" align="center" style="font-size:0"><table width="100%" height="100%" cellspacing="0" cellpadding="0" border="0"><tbody><tr><td style="border-bottom: 1px solid #fafafa; background: none; height: 1px; width: 100%; margin: 0px;"></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></div></body></html>'''
            
    return html
     
def gen_html_tutor_registration(name, password):
    html = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"><html dir="ltr" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office"><head><meta charset="UTF-8"><meta content="width=device-width, initial-scale=1" name="viewport"><meta name="x-apple-disable-message-reformatting"><meta http-equiv="X-UA-Compatible" content="IE=edge"><meta content="telephone=no" name="format-detection"><title></title><!--[if (mso 16)]>
    <style type="text/css">
    a {text-decoration: none;}
    </style>
    <![endif]--><!--[if gte mso 9]><style>sup { font-size: 100% !important; }</style><![endif]--><!--[if gte mso 9]>
        <xml>
            <o:OfficeDocumentSettings>
            <o:AllowPNG></o:AllowPNG>
            <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
        <![endif]--><!--[if mso]>
        <style type="text/css">
            ul {
        margin: 0 !important;
        }
        ol {
        margin: 0 !important;
        }
        li {
        margin-left: 47px !important;
        }

        </style><![endif]
    --></head><body class="body"><div dir="ltr" class="es-wrapper-color"><!--[if gte mso 9]>
			<v:background xmlns:v="urn:schemas-microsoft-com:vml" fill="t">
				<v:fill type="tile" color="#fafafa"></v:fill>
			</v:background>
		<![endif]--><table class="es-wrapper" width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-email-paddings" valign="top"><table cellpadding="0" cellspacing="0" class="es-content esd-header-popover" align="center"><tbody><tr><td class="es-adaptive esd-stripe" align="center"><table class="es-content-body" style="background-color: transparent;" width="600" cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center"><tbody><tr><td class="esd-structure es-p10" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="580" valign="top" align="center"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td align="center" class="es-infoblock esd-block-text"></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table><table class="es-content" cellspacing="0" cellpadding="0" align="center"><tbody><tr><td class="esd-stripe" style="background-color: #fafafa;" bgcolor="#fafafa" align="center"><table class="es-content-body" style="background-color: #ffffff;" esd-img-prev-src="" width="600" cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center"><tbody><tr><td class="esd-structure es-p40t es-p20r es-p20l" style="background-color: transparent; background-position: left top;" esd-img-prev-src="https://fkus.stripocdn.email/content/guids/CABINET_8a8240f4650bd716d3cd69675fe184ca/images/1041555765740937.png" esd-img-prev-position="left top" esd-img-prev-repeat="no-repeat" bgcolor="transparent" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="560" valign="top" align="center"><table esd-img-prev-src="" esd-img-prev-position="left top" style="background-position: left top;" width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-block-image es-p5t es-p5b" align="center" style="font-size:0"><a target="_blank"><img src="https://ecrugam.stripocdn.email/content/guids/CABINET_dd354a98a803b60e2f0411e893c82f56/images/23891556799905703.png" alt="" style="display: block;" width="175"></a></td></tr><tr><td class="esd-block-text es-p15t es-p15b" align="center"><h1 style="color: #333333; font-size: 20px;">

        <strong>    Here is your password </strong></h1><h1 style="color: #333333; font-size: 20px;"></h1></td></tr><tr><td class="esd-block-text es-p40r es-p40l" align="left"> 
    
    <p style="text-align: center;">Hi ''' + name + '''</p></td></tr><tr><td class="esd-block-text es-p35r es-p40l" align="left"> 
        
        <p style="text-align: center;">Welcome to A-Team Academy! We are so glad to have you tutoring for us! This is your password to log on to ateamacad.co.uk where you can find your lessons, access the classwork and markschemes, submit grades, view your hours and more! Simply log in with this email to access all the features</p></td></tr><tr><td class="esd-block-text es-p25t es-p40r es-p40l" align="center"> 
            
            <p>Your password is below:&nbsp;</p>
            
            <p>
            ''' + password + '''
            <br>
            </p> 
            
            <p>Please change your password once you have logged on. Other important information can be found in the important files section. In particular it is advised that you have a look at the following documents: https://ateamacad.co.uk/files/IMPORTANT_DOCS/Conducting_in_person_Lessons.pdf, https://ateamacad.co.uk/files/IMPORTANT_DOCS/Conducting_Online_Lessons.pdf, https://ateamacad.co.uk/files/IMPORTANT_DOCS/How_to_register_laptop.mp4. Any issues or questions regarding the site please contact safwaan@ateamacademy.co.uk </p></td></tr></tbody></table></td></tr></tbody></table></td></tr><tr><td class="esd-structure es-p5t es-p20b es-p20r es-p20l" esd-img-prev-src="" esd-img-prev-position="left top" style="background-position: left top;" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="560" valign="top" align="center"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td align="center" class="esd-empty-container" style="display: none;"></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table><table class="es-footer" cellspacing="0" cellpadding="0" align="center"><tbody><tr><td class="esd-stripe" style="background-color: #fafafa;" bgcolor="#fafafa" align="center"><table class="es-footer-body" esd-img-prev-src="" width="600" cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center"><tbody><tr><td class="esd-structure es-p10t es-p30b es-p20r es-p20l" style=" background-color: #0b5394; background-position: left top;" esd-img-prev-src="" esd-img-prev-position="left top" bgcolor="#0b5394" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="560" valign="top" align="center"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-block-text es-p5t es-p5b" align="left"><h2 style="font-size: 16px; color: #ffffff;"><strong>Have questions?</strong></h2></td></tr><tr><td esd-links-underline="none" esd-links-color="#ffffff" class="esd-block-text es-p5b" align="left"><p style="font-size: 14px; color: #ffffff;">Please contact Safwaan at safwaan@ateamacademy.co.uk<a target="_blank" style="font-size: 14px; text-decoration: none; color: #ffffff;"></a></p></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table><table class="es-content esd-footer-popover" cellspacing="0" cellpadding="0" align="center"><tbody><tr><td class="esd-stripe" style="background-color: #fafafa;" bgcolor="#fafafa" align="center"><table class="es-content-body" style="background-color: transparent;" esd-img-prev-src="" width="600" cellspacing="0" cellpadding="0" bgcolor="transparent" align="center"><tbody><tr><td class="esd-structure es-p15t" esd-img-prev-src="" esd-img-prev-position="left top" style="background-position: left top;" align="left"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-container-frame" width="600" valign="top" align="center"><table width="100%" cellspacing="0" cellpadding="0"><tbody><tr><td class="esd-block-spacer es-p20b es-p20r es-p20l" align="center" style="font-size:0"><table width="100%" height="100%" cellspacing="0" cellpadding="0" border="0"><tbody><tr><td style="border-bottom: 1px solid #fafafa; background: none; height: 1px; width: 100%; margin: 0px;"></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></div>
            
            ''' + getSignature() + '''</body></html>'''
            
    return html
  
def gen_html_new_message(message, lessonID, sender):
    html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #ffffff; color: #333; margin: 0; padding: 0;">

            <div style="max-width: 600px; margin: 0 auto; background-color: #007bff; color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">
                <h1 style = "color: white; "> {sender} said: </h1>
                <p style="margin-bottom: 15px; line-height: 1.6;"> {message} </p>
                <p style="line-height: 1.6; color:white;"> visit https://ateamacad.co.uk/Classroom_View_Forum?lessonid={lessonID}&year={gen_academic_year()}&weekNo={str(gen_week_no(0))} to respond</p>
            </div>
        </body>
        </html>
    """

    return html_content
         
def gen_html_tomorrow_timetable(name, lessons):
    # Get the number of lessons
    num_of_lessons = len(lessons)

    # Base email template with darker inline styles for red and blue colors
    email_template = f"""

        <p>You have {num_of_lessons} lesson(s) scheduled for tomorrow. Check it is accurate according to your knowledge and let Safwaan (safwaan@ateamacademy.co.uk) know if anything seems incorrect. If you havent already please send lessons plans to Safwaan or upload them to the website as notes ensuring that they are hidden from students. Please see the timetable below:</p>
        
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center; background-color: #1F3A65; color: white;">Day</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center; background-color: #1F3A65; color: white;">Lesson Name</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center; background-color: #1F3A65; color: white;">Start Time</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center; background-color: #1F3A65; color: white;">End Time</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center; background-color: #8B2F3C; color: white;">Centre</th>
                </tr>
            </thead>
            <tbody>
    """

    # Loop through the lessons and add rows to the timetable with alternating faint background colors
    for index, lesson in enumerate(lessons):
        start_time = lesson.startTime.strftime('%H:%M') if lesson.startTime else '--:--'
        end_time = lesson.endTime.strftime('%H:%M')

        # Apply faint background colors: light blue for even rows, light red for odd rows
        row_color = "#F0F4F8" if index % 2 == 0 else "#F8E5E5"

        # Add lesson information as rows with inline styles
        email_template += f"""
        <tr style="background-color: {row_color};">
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{lesson.day}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{getSubjectName(lesson.subjectID)}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{start_time}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{end_time}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{getCentre(lesson.centreID)}</td>
        </tr>
        """

    # Close the table and add a signature
    email_template += f"""
            </tbody>
        </table>

    """
        # {getSignature()}
    return email_template

def gen_html_grades_report(student_name, grades):
    # Get the number of tests in the grade report
    num_of_tests = len(grades)

    # Base email template with darker inline styles for red and blue colors
    email_template = f"""
        <p>Dear {student_name},</p>
        <p>Here is a summary of your grades for the recent assessments. There are {num_of_tests} test(s) included in this report. If you have any questions, please contact your tutor.</p>
        
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center; background-color: #1F3A65; color: white;">Test Name</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center; background-color: #1F3A65; color: white;">Date</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center; background-color: #8B2F3C; color: white;">Your Marks</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center; background-color: #8B2F3C; color: white;">Grade</th>
                </tr>
            </thead>
            <tbody>
    """

    # Loop through the grades and add rows to the table with alternating background colors
    for index, grade in enumerate(grades):
        date = grade['date'].strftime('%d-%m-%Y')
        test_name = grade['name']
        total_marks = grade['total']
        marks = grade['mark']
        grade_letter = grade['grade']

        # Apply faint background colors: light blue for even rows, light red for odd rows
        row_color = "#F0F4F8" if index % 2 == 0 else "#F8E5E5"

        # Add each test's grade information as rows with inline styles
        email_template += f"""
        <tr style="background-color: {row_color};">
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{test_name}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{date}</td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{marks} / {total_marks} </td>
            <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{grade_letter}</td>
        </tr>
        """

    # Close the table and add a signature
    email_template += f"""
            </tbody>
        </table>

    """
    # {getSignature()}
    return email_template



             
def createSibling(studentInfo, siblingNumber, password):
    if siblingNumber == 1: 
        return Students(
        firstName = studentInfo['sibling_1_forename'].capitalize(),
        middleName = "",
        secondName = studentInfo['sibling_1_surname'].capitalize(),
        known_as = "",
        email = studentInfo['sibling_1_email'],
        parent_email = studentInfo['parent_email'],
        year_group = studentInfo['sibling_1_year_group'],
        date_of_birth = studentInfo['sibling_1_date_of_birth'],
        gender = studentInfo['sibling_1_gender'],
        country_of_birth = "",
        nationality = "",
        ethnic_origin = "",
        mother_tongue = "",
        date_of_entry_uk = studentInfo['sibling_1_date_of_birth'],
        post_code = studentInfo['post_code'],
        house_number = studentInfo['house_number'],
        street_name = studentInfo['street_name'],
        city_or_county = studentInfo['city_or_county'],
        borough_of_residence = studentInfo['borough_of_residence'],
        mode_of_travelling = studentInfo['mode_of_travelling'],
        current_school_1 = "",
        current_school_1_date_from = None,
        school_2 = "",
        school_2_date_from = None,
        school_2_date_until = None,
        school_3 = "",
        school_3_date_from = None,
        school_3_date_until = None,
        school_4 = "",
        school_4_date_from = None,
        school_4_date_until = None,
        sibling_1_forename = studentInfo['firstName'],
        sibling_1_surname = studentInfo['secondName'],
        sibling_1_date_of_birth = studentInfo['date_of_birth'],
        sibling_1_gender = studentInfo['gender'],
        sibling_1_year_group = studentInfo['student_year_group'],
        sibling_2_forename = studentInfo['sibling_2_forename'],
        sibling_2_surname = studentInfo['sibling_2_surname'],
        sibling_2_date_of_birth = studentInfo['sibling_2_date_of_birth'],
        sibling_2_gender = studentInfo['sibling_2_gender'],
        sibling_2_year_group = studentInfo['sibling_2_year_group'],
        sibling_3_forename = studentInfo['sibling_3_forename'],
        sibling_3_surname = studentInfo['sibling_3_surname'],
        sibling_3_date_of_birth = studentInfo['sibling_3_date_of_birth'],
        sibling_3_gender = studentInfo['sibling_3_gender'],
        sibling_3_year_group = studentInfo['sibling_3_year_group'],
        sibling_4_forename = studentInfo['sibling_4_forename'],
        sibling_4_surname = studentInfo['sibling_4_surname'],
        sibling_4_date_of_birth = studentInfo['sibling_4_date_of_birth'],
        sibling_4_gender = studentInfo['sibling_4_gender'],
        sibling_4_year_group = studentInfo['sibling_4_year_group'],
        
        sibling_1_id = None, 
        sibling_2_id = None, 
        sibling_3_id = None,
        sibling_4_id = None,        
        
        previous_name = "",
        legal_name = "",
        home_local_authority = "",
        carer_name = "",
        look_after_child_contact_info = "",
        child_protection_register = "",
        look_after_child_register = "",
        personal_education_plan = "",
        pep_contact_number = "",
        armed_service_parent_name = "",
        armed_service_parent_service = "",
        armed_service_parent_rank = "",
        armed_service_parent_additional_info = "",
        gp_name = studentInfo['gp_name'],
        gp_post_code = studentInfo['gp_post_code'],
        gp_telephone = studentInfo['gp_telephone'],
        gp_practice_address = studentInfo['gp_practice_address'],
        child_normally_healthy = False,
        asthma = False,
        epilepsy_or_fits = False,
        heart_problems = False,
        allergies = False,
        allergyInfo = "",
        nose_bleeds = False,
        speech_or_hearing_difficulties = False,
        mobility_difficulties = False,
        other_difficulties = False,
        serious_illness_or_accidents = False,
        condition_affecting_school_life = False,
        extra_medical_info = "",
        known_medical_conditions = "",
        medical_treatment_or_medicines = "",
        emergency_information = "",
        first_aid_permission = False,
        hospital_referral_permission = False,
        special_educational_needs = False,
        sen_information = "",
        behavior_support_needed = False,
        behavior_support_info = "",
        priority_contact_1_title = studentInfo['priority_contact_1_title'],
        priority_contact_1_relationship = studentInfo['priority_contact_1_relationship'],
        priority_contact_1_forename = studentInfo['priority_contact_1_forename'],
        priority_contact_1_surname = studentInfo['priority_contact_1_surname'],
        priority_contact_1_post_code = studentInfo['priority_contact_1_post_code'],
        priority_contact_1_home_telephone = studentInfo['priority_contact_1_home_telephone'],
        priority_contact_1_mobile_telephone = studentInfo['priority_contact_1_mobile_telephone'],
        priority_contact_1_email = studentInfo['priority_contact_1_email'],
        priority_contact_1_employer = studentInfo['priority_contact_1_employer'],
        priority_contact_1_work_number = studentInfo['priority_contact_1_work_number'],
        priority_contact_1_other_info_numbers = studentInfo['priority_contact_1_other_info_numbers'],
        priority_contact_1_parental_responsibility = studentInfo['priority_contact_1_parental_responsibility'],
        priority_contact_2_title = studentInfo['priority_contact_2_title'],
        priority_contact_2_relationship = studentInfo['priority_contact_2_relationship'],
        priority_contact_2_forename = studentInfo['priority_contact_2_forename'],
        priority_contact_2_surname = studentInfo['priority_contact_2_surname'],
        priority_contact_2_post_code = studentInfo['priority_contact_2_post_code'],
        priority_contact_2_home_telephone = studentInfo['priority_contact_2_home_telephone'],
        priority_contact_2_mobile_telephone = studentInfo['priority_contact_2_mobile_telephone'],
        priority_contact_2_email = studentInfo['priority_contact_2_email'],
        priority_contact_2_employer = studentInfo['priority_contact_2_employer'],
        priority_contact_2_work_number = studentInfo['priority_contact_2_work_number'],
        priority_contact_2_other_info_numbers = studentInfo['priority_contact_2_other_info_numbers'],
        priority_contact_2_parental_responsibility = studentInfo['priority_contact_2_parental_responsibility'],

        pupil_first_language = "",
        pupil_first_language_spoken = False,
        pupil_first_language_read = False,
        pupil_first_language_written = False,
        pupil_other_language = "",
        pupil_other_language_spoken = False,
        pupil_other_language_read = False,
        pupil_other_language_written = False,
        eal = False,
        home_main_language = "",
        home_main_language_spoken = False,
        home_main_language_read = False,
        home_main_language_written = False,
        home_other_language = "",
        home_other_language_spoken = False,
        home_other_language_read = False,
        home_other_language_written = False,
        local_visits_permission = studentInfo['local_visits_permission'],
        digital_media_consent = studentInfo['digital_media_consent'],
        declaration_name = studentInfo['declaration_name'],
        declaration_signed = True,
        # declaration_date = datetime.strptime(date.today().strftime('%F') , "%Y-%M-%d"),
        # declaration_date= str(date.today().strftime('%F')),
        declaration_date=gen_date(),

        additional_comments = studentInfo['additional_comment'], 
        
        username = gen_username(studentInfo['sibling_1_forename'], studentInfo['sibling_1_surname']), 
        password = generate_password_hash(password)
    )
        
    elif siblingNumber == 2: 
        return Students(
        firstName = studentInfo['sibling_2_forename'].capitalize(),
        middleName = "",
        secondName = studentInfo['sibling_2_surname'].capitalize(),
        known_as = "",
        email = studentInfo['sibling_2_email'],
        parent_email = studentInfo['parent_email'],
        year_group = studentInfo['sibling_2_year_group'],
        date_of_birth = studentInfo['sibling_2_date_of_birth'],
        gender = studentInfo['sibling_2_gender'],
        country_of_birth = "",
        nationality = "",
        ethnic_origin = "",
        mother_tongue = "",
        date_of_entry_uk = studentInfo['sibling_2_date_of_birth'],
        post_code = studentInfo['post_code'],
        house_number = studentInfo['house_number'],
        street_name = studentInfo['street_name'],
        city_or_county = studentInfo['city_or_county'],
        borough_of_residence = studentInfo['borough_of_residence'],
        mode_of_travelling = studentInfo['mode_of_travelling'],
        current_school_1 = "",
        current_school_1_date_from = None,
        school_2 = "",
        school_2_date_from = None,
        school_2_date_until = None,
        school_3 = "",
        school_3_date_from = None,
        school_3_date_until = None,
        school_4 = "",
        school_4_date_from = None,
        school_4_date_until = None,
        sibling_1_forename = studentInfo['sibling_1_forename'],
        sibling_1_surname = studentInfo['sibling_1_surname'],
        sibling_1_date_of_birth = studentInfo['sibling_1_date_of_birth'],
        sibling_1_gender = studentInfo['sibling_1_gender'],
        sibling_1_year_group = studentInfo['sibling_1_year_group'],
        sibling_2_forename = studentInfo['firstName'],
        sibling_2_surname = studentInfo['secondName'],
        sibling_2_date_of_birth = studentInfo['date_of_birth'],
        sibling_2_gender = studentInfo['gender'],
        sibling_2_year_group = studentInfo['student_year_group'],
        sibling_3_forename = studentInfo['sibling_3_forename'],
        sibling_3_surname = studentInfo['sibling_3_surname'],
        sibling_3_date_of_birth = studentInfo['sibling_3_date_of_birth'],
        sibling_3_gender = studentInfo['sibling_3_gender'],
        sibling_3_year_group = studentInfo['sibling_3_year_group'],
        sibling_4_forename = studentInfo['sibling_4_forename'],
        sibling_4_surname = studentInfo['sibling_4_surname'],
        sibling_4_date_of_birth = studentInfo['sibling_4_date_of_birth'],
        sibling_4_gender = studentInfo['sibling_4_gender'],
        sibling_4_year_group = studentInfo['sibling_4_year_group'],
        
        sibling_1_id = None, 
        sibling_2_id = None, 
        sibling_3_id = None,
        sibling_4_id = None,        
        
        previous_name = "",
        legal_name = "",
        home_local_authority = "",
        carer_name = "",
        look_after_child_contact_info = "",
        child_protection_register = "",
        look_after_child_register = "",
        personal_education_plan = "",
        pep_contact_number = "",
        armed_service_parent_name = "",
        armed_service_parent_service = "",
        armed_service_parent_rank = "",
        armed_service_parent_additional_info = "",
        gp_name = studentInfo['gp_name'],
        gp_post_code = studentInfo['gp_post_code'],
        gp_telephone = studentInfo['gp_telephone'],
        gp_practice_address = studentInfo['gp_practice_address'],
        child_normally_healthy = False,
        asthma = False,
        epilepsy_or_fits = False,
        heart_problems = False,
        allergies = False,
        allergyInfo = "",
        nose_bleeds = False,
        speech_or_hearing_difficulties = False,
        mobility_difficulties = False,
        other_difficulties = False,
        serious_illness_or_accidents = False,
        condition_affecting_school_life = False,
        extra_medical_info = "",
        known_medical_conditions = "",
        medical_treatment_or_medicines = "",
        emergency_information = "",
        first_aid_permission = False,
        hospital_referral_permission = False,
        special_educational_needs = False,
        sen_information = "",
        behavior_support_needed = False,
        behavior_support_info = "",
        priority_contact_1_title = studentInfo['priority_contact_1_title'],
        priority_contact_1_relationship = studentInfo['priority_contact_1_relationship'],
        priority_contact_1_forename = studentInfo['priority_contact_1_forename'],
        priority_contact_1_surname = studentInfo['priority_contact_1_surname'],
        priority_contact_1_post_code = studentInfo['priority_contact_1_post_code'],
        priority_contact_1_home_telephone = studentInfo['priority_contact_1_home_telephone'],
        priority_contact_1_mobile_telephone = studentInfo['priority_contact_1_mobile_telephone'],
        priority_contact_1_email = studentInfo['priority_contact_1_email'],
        priority_contact_1_employer = studentInfo['priority_contact_1_employer'],
        priority_contact_1_work_number = studentInfo['priority_contact_1_work_number'],
        priority_contact_1_other_info_numbers = studentInfo['priority_contact_1_other_info_numbers'],
        priority_contact_1_parental_responsibility = studentInfo['priority_contact_1_parental_responsibility'],
        priority_contact_2_title = studentInfo['priority_contact_2_title'],
        priority_contact_2_relationship = studentInfo['priority_contact_2_relationship'],
        priority_contact_2_forename = studentInfo['priority_contact_2_forename'],
        priority_contact_2_surname = studentInfo['priority_contact_2_surname'],
        priority_contact_2_post_code = studentInfo['priority_contact_2_post_code'],
        priority_contact_2_home_telephone = studentInfo['priority_contact_2_home_telephone'],
        priority_contact_2_mobile_telephone = studentInfo['priority_contact_2_mobile_telephone'],
        priority_contact_2_email = studentInfo['priority_contact_2_email'],
        priority_contact_2_employer = studentInfo['priority_contact_2_employer'],
        priority_contact_2_work_number = studentInfo['priority_contact_2_work_number'],
        priority_contact_2_other_info_numbers = studentInfo['priority_contact_2_other_info_numbers'],
        priority_contact_2_parental_responsibility = studentInfo['priority_contact_2_parental_responsibility'],

        pupil_first_language = "",
        pupil_first_language_spoken = False,
        pupil_first_language_read = False,
        pupil_first_language_written = False,
        pupil_other_language = "",
        pupil_other_language_spoken = False,
        pupil_other_language_read = False,
        pupil_other_language_written = False,
        eal = False,
        home_main_language = "",
        home_main_language_spoken = False,
        home_main_language_read = False,
        home_main_language_written = False,
        home_other_language = "",
        home_other_language_spoken = False,
        home_other_language_read = False,
        home_other_language_written = False,
        local_visits_permission = studentInfo['local_visits_permission'],
        digital_media_consent = studentInfo['digital_media_consent'],
        declaration_name = studentInfo['declaration_name'],
        declaration_signed = True,
        # declaration_date = datetime.strptime(date.today().strftime('%F') , "%Y-%M-%d"),
        # declaration_date= str(date.today().strftime('%F')),
        declaration_date=gen_date(),

        additional_comments = studentInfo['additional_comment'], 
        
        username = gen_username(studentInfo['sibling_2_forename'], studentInfo['sibling_2_surname']), 
        password = generate_password_hash(password)
    )
    
    elif siblingNumber == 3:
        return Students(
        firstName = studentInfo['sibling_3_forename'].capitalize(),
        middleName = "",
        secondName = studentInfo['sibling_3_surname'].capitalize(),
        known_as = "",
        email = studentInfo['sibling_3_email'],
        parent_email = studentInfo['parent_email'],
        year_group = studentInfo['sibling_3_year_group'],
        date_of_birth = studentInfo['sibling_3_date_of_birth'],
        gender = studentInfo['sibling_3_gender'],
        country_of_birth = "",
        nationality = "",
        ethnic_origin = "",
        mother_tongue = "",
        date_of_entry_uk = studentInfo['sibling_3_date_of_birth'],
        post_code = studentInfo['post_code'],
        house_number = studentInfo['house_number'],
        street_name = studentInfo['street_name'],
        city_or_county = studentInfo['city_or_county'],
        borough_of_residence = studentInfo['borough_of_residence'],
        mode_of_travelling = studentInfo['mode_of_travelling'],
        current_school_1 = "",
        current_school_1_date_from = None,
        school_2 = "",
        school_2_date_from = None,
        school_2_date_until = None,
        school_3 = "",
        school_3_date_from = None,
        school_3_date_until = None,
        school_4 = "",
        school_4_date_from = None,
        school_4_date_until = None,
        sibling_1_forename = studentInfo['sibling_1_forename'],
        sibling_1_surname = studentInfo['sibling_1_surname'],
        sibling_1_date_of_birth = studentInfo['sibling_1_date_of_birth'],
        sibling_1_gender = studentInfo['sibling_1_gender'],
        sibling_1_year_group = studentInfo['sibling_1_year_group'],
        sibling_2_forename = studentInfo['sibling_2_forename'],
        sibling_2_surname = studentInfo['sibling_2_surname'],
        sibling_2_date_of_birth = studentInfo['sibling_2_date_of_birth'],
        sibling_2_gender = studentInfo['sibling_2_gender'],
        sibling_2_year_group = studentInfo['sibling_2_year_group'],
        sibling_3_forename = studentInfo['firstName'],
        sibling_3_surname = studentInfo['secondName'],
        sibling_3_date_of_birth = studentInfo['date_of_birth'],
        sibling_3_gender = studentInfo['gender'],
        sibling_3_year_group = studentInfo['student_year_group'],
        sibling_4_forename = studentInfo['sibling_4_forename'],
        sibling_4_surname = studentInfo['sibling_4_surname'],
        sibling_4_date_of_birth = studentInfo['sibling_4_date_of_birth'],
        sibling_4_gender = studentInfo['sibling_4_gender'],
        sibling_4_year_group = studentInfo['sibling_4_year_group'],
        
        sibling_1_id = None, 
        sibling_2_id = None, 
        sibling_3_id = None,
        sibling_4_id = None,        
        
        previous_name = "",
        legal_name = "",
        home_local_authority = "",
        carer_name = "",
        look_after_child_contact_info = "",
        child_protection_register = "",
        look_after_child_register = "",
        personal_education_plan = "",
        pep_contact_number = "",
        armed_service_parent_name = "",
        armed_service_parent_service = "",
        armed_service_parent_rank = "",
        armed_service_parent_additional_info = "",
        gp_name = studentInfo['gp_name'],
        gp_post_code = studentInfo['gp_post_code'],
        gp_telephone = studentInfo['gp_telephone'],
        gp_practice_address = studentInfo['gp_practice_address'],
        child_normally_healthy = False,
        asthma = False,
        epilepsy_or_fits = False,
        heart_problems = False,
        allergies = False,
        allergyInfo = "",
        nose_bleeds = False,
        speech_or_hearing_difficulties = False,
        mobility_difficulties = False,
        other_difficulties = False,
        serious_illness_or_accidents = False,
        condition_affecting_school_life = False,
        extra_medical_info = "",
        known_medical_conditions = "",
        medical_treatment_or_medicines = "",
        emergency_information = "",
        first_aid_permission = False,
        hospital_referral_permission = False,
        special_educational_needs = False,
        sen_information = "",
        behavior_support_needed = False,
        behavior_support_info = "",
        priority_contact_1_title = studentInfo['priority_contact_1_title'],
        priority_contact_1_relationship = studentInfo['priority_contact_1_relationship'],
        priority_contact_1_forename = studentInfo['priority_contact_1_forename'],
        priority_contact_1_surname = studentInfo['priority_contact_1_surname'],
        priority_contact_1_post_code = studentInfo['priority_contact_1_post_code'],
        priority_contact_1_home_telephone = studentInfo['priority_contact_1_home_telephone'],
        priority_contact_1_mobile_telephone = studentInfo['priority_contact_1_mobile_telephone'],
        priority_contact_1_email = studentInfo['priority_contact_1_email'],
        priority_contact_1_employer = studentInfo['priority_contact_1_employer'],
        priority_contact_1_work_number = studentInfo['priority_contact_1_work_number'],
        priority_contact_1_other_info_numbers = studentInfo['priority_contact_1_other_info_numbers'],
        priority_contact_1_parental_responsibility = studentInfo['priority_contact_1_parental_responsibility'],
        priority_contact_2_title = studentInfo['priority_contact_2_title'],
        priority_contact_2_relationship = studentInfo['priority_contact_2_relationship'],
        priority_contact_2_forename = studentInfo['priority_contact_2_forename'],
        priority_contact_2_surname = studentInfo['priority_contact_2_surname'],
        priority_contact_2_post_code = studentInfo['priority_contact_2_post_code'],
        priority_contact_2_home_telephone = studentInfo['priority_contact_2_home_telephone'],
        priority_contact_2_mobile_telephone = studentInfo['priority_contact_2_mobile_telephone'],
        priority_contact_2_email = studentInfo['priority_contact_2_email'],
        priority_contact_2_employer = studentInfo['priority_contact_2_employer'],
        priority_contact_2_work_number = studentInfo['priority_contact_2_work_number'],
        priority_contact_2_other_info_numbers = studentInfo['priority_contact_2_other_info_numbers'],
        priority_contact_2_parental_responsibility = studentInfo['priority_contact_2_parental_responsibility'],

        pupil_first_language = "",
        pupil_first_language_spoken = False,
        pupil_first_language_read = False,
        pupil_first_language_written = False,
        pupil_other_language = "",
        pupil_other_language_spoken = False,
        pupil_other_language_read = False,
        pupil_other_language_written = False,
        eal = False,
        home_main_language = "",
        home_main_language_spoken = False,
        home_main_language_read = False,
        home_main_language_written = False,
        home_other_language = "",
        home_other_language_spoken = False,
        home_other_language_read = False,
        home_other_language_written = False,
        local_visits_permission = studentInfo['local_visits_permission'],
        digital_media_consent = studentInfo['digital_media_consent'],
        declaration_name = studentInfo['declaration_name'],
        declaration_signed = True,
        # declaration_date = datetime.strptime(date.today().strftime('%F') , "%Y-%M-%d"),
        # declaration_date= str(date.today().strftime('%F')),
        declaration_date=gen_date(),

        additional_comments = studentInfo['additional_comment'], 
        
        username = gen_username(studentInfo['sibling_3_forename'], studentInfo['sibling_3_surname']), 
        password = generate_password_hash(password)
    )
    
    else: 
        return Students(
        firstName = studentInfo['sibling_4_forename'].capitalize(),
        middleName = "",
        secondName = studentInfo['sibling_4_surname'].capitalize(),
        known_as = "",
        email = studentInfo['sibling_4_email'],
        parent_email = studentInfo['parent_email'],
        year_group = studentInfo['sibling_4_year_group'],
        date_of_birth = studentInfo['sibling_4_date_of_birth'],
        gender = studentInfo['sibling_4_gender'],
        country_of_birth = "",
        nationality = "",
        ethnic_origin = "",
        mother_tongue = "",
        date_of_entry_uk = studentInfo['sibling_4_date_of_birth'],
        post_code = studentInfo['post_code'],
        house_number = studentInfo['house_number'],
        street_name = studentInfo['street_name'],
        city_or_county = studentInfo['city_or_county'],
        borough_of_residence = studentInfo['borough_of_residence'],
        mode_of_travelling = studentInfo['mode_of_travelling'],
        current_school_1 = "",
        current_school_1_date_from = None,
        school_2 = "",
        school_2_date_from = None,
        school_2_date_until = None,
        school_3 = "",
        school_3_date_from = None,
        school_3_date_until = None,
        school_4 = "",
        school_4_date_from = None,
        school_4_date_until = None,
        sibling_1_forename = studentInfo['sibling_1_forename'],
        sibling_1_surname = studentInfo['sibling_1_surname'],
        sibling_1_date_of_birth = studentInfo['sibling_1_date_of_birth'],
        sibling_1_gender = studentInfo['sibling_1_gender'],
        sibling_1_year_group = studentInfo['sibling_1_year_group'],
        sibling_2_forename = studentInfo['sibling_2_forename'],
        sibling_2_surname = studentInfo['sibling_2_surname'],
        sibling_2_date_of_birth = studentInfo['sibling_2_date_of_birth'],
        sibling_2_gender = studentInfo['sibling_2_gender'],
        sibling_2_year_group = studentInfo['sibling_2_year_group'],
        sibling_3_forename = studentInfo['sibling_3_forename'],
        sibling_3_surname = studentInfo['sibling_3_surname'],
        sibling_3_date_of_birth = studentInfo['sibling_3_date_of_birth'],
        sibling_3_gender = studentInfo['sibling_3_gender'],
        sibling_3_year_group = studentInfo['sibling_3_year_group'],
        sibling_4_forename = studentInfo['firstName'],
        sibling_4_surname = studentInfo['secondName'],
        sibling_4_date_of_birth = studentInfo['date_of_birth'],
        sibling_4_gender = studentInfo['gender'],
        sibling_4_year_group = studentInfo['student_year_group'],
        
        sibling_1_id = None, 
        sibling_2_id = None, 
        sibling_3_id = None,
        sibling_4_id = None,        
        
        previous_name = "",
        legal_name = "",
        home_local_authority = "",
        carer_name = "",
        look_after_child_contact_info = "",
        child_protection_register = "",
        look_after_child_register = "",
        personal_education_plan = "",
        pep_contact_number = "",
        armed_service_parent_name = "",
        armed_service_parent_service = "",
        armed_service_parent_rank = "",
        armed_service_parent_additional_info = "",
        gp_name = studentInfo['gp_name'],
        gp_post_code = studentInfo['gp_post_code'],
        gp_telephone = studentInfo['gp_telephone'],
        gp_practice_address = studentInfo['gp_practice_address'],
        child_normally_healthy = False,
        asthma = False,
        epilepsy_or_fits = False,
        heart_problems = False,
        allergies = False,
        allergyInfo = "",
        nose_bleeds = False,
        speech_or_hearing_difficulties = False,
        mobility_difficulties = False,
        other_difficulties = False,
        serious_illness_or_accidents = False,
        condition_affecting_school_life = False,
        extra_medical_info = "",
        known_medical_conditions = "",
        medical_treatment_or_medicines = "",
        emergency_information = "",
        first_aid_permission = False,
        hospital_referral_permission = False,
        special_educational_needs = False,
        sen_information = "",
        behavior_support_needed = False,
        behavior_support_info = "",
        priority_contact_1_title = studentInfo['priority_contact_1_title'],
        priority_contact_1_relationship = studentInfo['priority_contact_1_relationship'],
        priority_contact_1_forename = studentInfo['priority_contact_1_forename'],
        priority_contact_1_surname = studentInfo['priority_contact_1_surname'],
        priority_contact_1_post_code = studentInfo['priority_contact_1_post_code'],
        priority_contact_1_home_telephone = studentInfo['priority_contact_1_home_telephone'],
        priority_contact_1_mobile_telephone = studentInfo['priority_contact_1_mobile_telephone'],
        priority_contact_1_email = studentInfo['priority_contact_1_email'],
        priority_contact_1_employer = studentInfo['priority_contact_1_employer'],
        priority_contact_1_work_number = studentInfo['priority_contact_1_work_number'],
        priority_contact_1_other_info_numbers = studentInfo['priority_contact_1_other_info_numbers'],
        priority_contact_1_parental_responsibility = studentInfo['priority_contact_1_parental_responsibility'],
        priority_contact_2_title = studentInfo['priority_contact_2_title'],
        priority_contact_2_relationship = studentInfo['priority_contact_2_relationship'],
        priority_contact_2_forename = studentInfo['priority_contact_2_forename'],
        priority_contact_2_surname = studentInfo['priority_contact_2_surname'],
        priority_contact_2_post_code = studentInfo['priority_contact_2_post_code'],
        priority_contact_2_home_telephone = studentInfo['priority_contact_2_home_telephone'],
        priority_contact_2_mobile_telephone = studentInfo['priority_contact_2_mobile_telephone'],
        priority_contact_2_email = studentInfo['priority_contact_2_email'],
        priority_contact_2_employer = studentInfo['priority_contact_2_employer'],
        priority_contact_2_work_number = studentInfo['priority_contact_2_work_number'],
        priority_contact_2_other_info_numbers = studentInfo['priority_contact_2_other_info_numbers'],
        priority_contact_2_parental_responsibility = studentInfo['priority_contact_2_parental_responsibility'],

        pupil_first_language = "",
        pupil_first_language_spoken = False,
        pupil_first_language_read = False,
        pupil_first_language_written = False,
        pupil_other_language = "",
        pupil_other_language_spoken = False,
        pupil_other_language_read = False,
        pupil_other_language_written = False,
        eal = False,
        home_main_language = "",
        home_main_language_spoken = False,
        home_main_language_read = False,
        home_main_language_written = False,
        home_other_language = "",
        home_other_language_spoken = False,
        home_other_language_read = False,
        home_other_language_written = False,
        local_visits_permission = studentInfo['local_visits_permission'],
        digital_media_consent = studentInfo['digital_media_consent'],
        declaration_name = studentInfo['declaration_name'],
        declaration_signed = True,
        # declaration_date = datetime.strptime(date.today().strftime('%F') , "%Y-%M-%d"),
        # declaration_date= str(date.today().strftime('%F')),
        declaration_date=gen_date(),

        additional_comments = studentInfo['additional_comment'], 
        
        username = gen_username(studentInfo['sibling_4_forename'], studentInfo['sibling_4_surname']), 
        password = generate_password_hash(password)
    )

def gen_random_password(length):
    # With combination of lower and upper case
    result_str = ''.join(random.choice(string.ascii_letters) for i in range(length))
    # print random string
    return result_str

def getFileType(filepath): 
    return os.path.splitext(filepath)[1]

def isAllowed(currentRole, requiredRole): 
    if currentRole == "student":
        if requiredRole == "admin" or requiredRole == "tutor":
            return False
        else:
            return True
    
    elif currentRole == "tutor":
        if requiredRole == "admin":
            return False
        else:
            return True    
        
    elif currentRole == "admin": 
        return True
    
    else: 
        return False

def sendMultiple(emails):
    for email in emails: 
        e1 = EmailSender()
        e1.send(email['email'], email['subject'], email['message'])
        
def getDOB(DOB):
    if DOB is not None: 
        return DOB.strftime("%d / %m / %Y")
    else :
        return "01 / 01 / 2000"
        
def studentWasJustCreated(studentInfo):
    
    existingStudent = Students.query.filter_by(firstName = studentInfo['firstName'].capitalize()).filter_by(secondName = studentInfo['secondName'].capitalize()).filter_by(email = studentInfo['email']).first()
        
    if existingStudent is not None:
        try:
            # Append (not read-mode) to the data file next to the package;
            # the old code opened read-only and wrote a dict, so it always failed.
            tempStudentsPath = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "webApp", "tempStudents.txt")
            with open(tempStudentsPath, "a") as f:
                f.write(str(studentInfo) + "\n")
        except OSError:
            pass
        return True
    else:   
        return False
    
def isMarkScheme(file):
    bannedForStudents = ["test", 
                         "markscheme", 
                         "ms"]
    if any(item in file.filename for item in bannedForStudents):
        return True
        
    return False

def classTypeCheck(lesson, classtype):
    if classtype == "all" or classtype is None:
        return True
    
    elif classtype == "week" and lesson.day in ['MON', 'TUE', 'WED', 'THU', 'FRI']:
        return True
    
    elif classtype == "weekend" and lesson.day in ['SAT', 'SUN']:
        return True
    
    else: 
        return False        

def shiftTopicsBack(subjectID, startWeek=1, endWeek=51, step=1):
    '''
    shiftTopicsBack(subjectID, startWeek=1, endWeek=51, step=1)
    this will shift all topics back so the topic from week 2 will go to week 1
    week 52s topics will go to week 51
    
    startWeek should be the first week to change not the week its changing from
    endWeek should be the last week to change NOT the week its taking it from
    '''
    
    if step <= 0:
        raise Exception("step should be a positive number")
    elif not type(step) is int:
        raise TypeError("step should be an integer")
    elif endWeek < startWeek: 
        raise Exception("startWeek should be smaller than endWeek")
    
    for i in range(startWeek, endWeek+1, 1):
        newTopic = lessonPlan.query.filter_by(subjectID = subjectID).filter_by(weekNo = i + step).first().topic
        stmt = update(lessonPlan).values({"topic" : newTopic}).where(and_(lessonPlan.subjectID == subjectID, lessonPlan.weekNo == i ))
        db.session.execute(stmt)
        db.session.commit()
    
def shiftTopicsForward(subjectID, startWeek=2, endWeek=52, step=1):
    '''
    shiftTopicsForward(subjectID, startWeek=1, endWeek=52, step=1)
    this will shift all topics forward so the topic from week 1 will go to week 2
    week 51s topics will go to week 52
    
    startWeek should be the first week to change not the week its changing from
    endWeek should be the last week to change NOT the week its taking it from
    '''
    
    if step <= 0:
        raise Exception("step should be a positive number")
    elif not type(step) is int:
        raise TypeError("step should be an integer")
    elif endWeek < startWeek: 
        raise Exception("startWeek should be smaller than endWeek")
    
    for i in range(endWeek, startWeek-1, -1):
        newTopic = lessonPlan.query.filter_by(subjectID = subjectID).filter_by(weekNo = i-step).first().topic
        stmt = update(lessonPlan).values({"topic" : newTopic}).where(and_(lessonPlan.subjectID == subjectID, lessonPlan.weekNo == i ))
        db.session.execute(stmt)
        db.session.commit()

def getTutorHours(tutorID, weekNo):
    lessonList = LessonInfo.query.filter_by(tutorID=tutorID).filter_by(weekNo = weekNo).filter_by(approved = True).all()
    totalHours = 0 
    for lesson in lessonList:
        if getLessonYear(lesson.lessonID) == gen_academic_year():
            if len(StudentAttendance.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = weekNo).filter_by(present = True).all()) > 0 or len(UnregisteredAttendance.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = weekNo).filter_by(present = True).all()) > 0 or len(TempAttendance.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = weekNo).all()) > 0:
                totalHours += lesson.duration
    
    return totalHours

def getTutorMonthHours(tutorID, month):
    '''
    startDate, endDate should be in the form "DD/MM/YYY"
    month should be an integer, 1-12
    '''
    day = date.today()
    last_day = calendar.monthrange(day.year, month)[1]
    if month<1 or month>12: 
        return "month doesnt exist"
    else: 
        startDay = dateToDay(f"01/{str(month)}/{str(day.year)}")
        startWeek = dateToWeekNo(datetime.date(int(day.year), month, 1))
        
        endDay = dateToDay(f"{last_day}/{str(month)}/{str(day.year)}")
        endWeek = dateToWeekNo(datetime.date(int(day.year), month, last_day))
            
        
        totalHours = 0 
        for i in range(int(startWeek), int(endWeek)+1, 1):
            lessonList = LessonInfo.query.filter_by(tutorID=tutorID).filter_by(weekNo = i).filter_by(approved = True).all()
            if i == int(startWeek):
                lessonList = [lesson for lesson in lessonList if (day_to_num(lesson.day) >= day_to_num(startDay) and getLessonYear(lesson.lessonID) == gen_academic_year())]
                
            elif i == int(endWeek):
                lessonList = [lesson for lesson in lessonList if (day_to_num(lesson.day) <= day_to_num(endDay) and getLessonYear(lesson.lessonID) == gen_academic_year())]

            for lesson in lessonList:
                if getLessonYear(lesson.lessonID) == gen_academic_year():
                    if len(StudentAttendance.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = i).filter_by(present = True).all()) > 0 or len(UnregisteredAttendance.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = i).filter_by(present = True).all()) > 0 or len(TempAttendance.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = i).all()) > 0:
                        # print(getLessonInfoString(lesson.lessonID, lesson.weekNo))
                        totalHours += lesson.duration
                        
                        
                # else: 
                #     # print("not counted")
                        
            # print(getTutor(tutorID))
            # if lessonList != []: 
            #     print(lessonList)
    
    return totalHours


def getFileFolder(subjectID):
    subject = Subject.query.filter_by(subjectID = subjectID).first()
    if subject is not None: 
        return subject.tier.replace(" ", "-").upper() +  "-" + subject.title.replace(" ", "-").upper()
    else: 
        return ""

def shortWeekToRegular(day):

    if day == "MON": 
        return "Monday"
    elif day == "TUE": 
        return "Tuesday"
    elif day == "WED":
        return "Wednesday"
    elif day == "THU":
        return "Thursday"
    elif day == "FRI":
        return "Friday"
    elif day == "SAT": 
        return "Saturday"
    elif day == "SUN":
        return "Sunday"
    else:
        return "Day Not Found"

def eligibleForDownload(name, role):
    current_time = datetime.datetime.utcnow()
    one_hour_ago = current_time - timedelta(minutes=30)

    # Filter logs for a user who downloaded 5 or more files in the last hour
    downloaded_files_count = db.session.query(func.count().label("downloaded_count")) \
        .filter(and_(log.date >= one_hour_ago, log.role == role, log.message.like('%was just downloaded%'), log.message.like('%' + name +'%'))).scalar()

    if downloaded_files_count is not None and downloaded_files_count >= 5:
        return False
    else:
        return True

def gen_html_topic_list(subjects, weeks):
    html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>December Mock Results for </title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 20px;">

            <h1 style="text-align: center;"> Topic List for Weekday Tests<h1>

            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <thead>
                    <tr>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2; font-size:small;"> Test Name </th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2; font-size:small;"> Topic List </th>
                    </tr>
                </thead>
                <tbody>
                {% for test in tests %}
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: left; font-size:small;"> {{ test.name }} </td>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: left; font-size:small;"> {% for topic in test.topics %} {{ topic }} <br> {% endfor %} </td>
                    </tr>
                {% endfor %}
                
                </tbody>
            </table>
            <p style = "font-size: small;"> * Please note that all of the above may not apply to you. These tests will take place during your regularly scheduled lessons between the 12th and the 18th February so you will only have tests in the subjects that you usually participate in. Revision materal and resources can be found at ateamacad.co.uk</p>
            <p style = "font-size: small;"> If there are any issues or questions regarding the above results please feel free to email safwaan@ateamacademy.co.uk. </p>

        </body>
        </html>

        """ + getSignature()
        
    tests = []
    
    for subject in subjects:
        if subject == 7:
            topics = ["Paper 1 Content"]
        else:
            topics = []
            for week in weeks: 
                topic = lessonPlan.query.filter_by(subjectID = subject).filter_by(weekNo = week).first()
                if topic: 
                    topics.append(topic.topic)
            
        tests.append({"name" : getSubjectName(subject), "topics" : topics})
            
    html_content = render_template_string(html_template, tests = tests)

    return html_content

def gen_html_topic_list2(topicList):
    html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>December Mock Results for </title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 20px;">

            <h1 style="text-align: center;"> Topic List for Easter Mocks<h1>

            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <thead>
                    <tr>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2; font-size:small;"> Test Name </th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left; background-color: #f2f2f2; font-size:small;"> Time </th>
                    </tr>
                </thead>
                <tbody>
                {% for test in tests %}
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: left; font-size:small;"> {{ test.name }} </td>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: left; font-size:small;"> {% for topic in test.topics %} {{ topic }} <br> {% endfor %} </td>
                    </tr>
                {% endfor %}
                
                </tbody>
            </table>
            <p style = "font-size: small;"> * Please note that all of the above may not apply to you. These tests will take place in your regular lessons between the 1st April and the 7th April so you will only have tests in the subjects that you usually participate in. Please ensure that you arrive promptly. Revision materal and resources can be found at ateamacad.co.uk</p>
            <p style = "font-size: small;"> If there are any issues or questions regarding the above results please feel free to email safwaan@ateamacademy.co.uk. </p>

        </body>
        </html>

        """ + getSignature()
        
                
    html_content = render_template_string(html_template, tests = topicList)

    return html_content

def generate_html_exam_timetable_original(student_id, start_date=datetime.datetime.strptime("1900-12-30", "%Y-%m-%d"), end_date=datetime.datetime.strptime("3100-12-30", "%Y-%m-%d")):
    # Get the list of exam IDs the student is registered for
    exam_ids = getExamsForStudent(student_id, start_date, end_date)
    
    if not exam_ids:
        return "<p>No exams registered for this student.</p>"
    
    # Start building the HTML
    html_content = """
    <html>
    <body>
        <h2>Exam Timetable for {}</h2>
        
        <p> Thank you for choosing A-Team Academy to sit your exams. We have now processed the entries and you can find attached the exam timetable. Please check with timetable accordingly (Name and date of birth) and any details that are not pointed out now could result in additional charges if changes are required later. </p> 
        
        <p> Please also read the Instruction to Candidate for exams documents as attached while preparing for your exams. </p>
        
        <p> Candidates are expected to arrive at least 15 minutes prior to each exam with ID that was presented at time of registration as well as the correct stationary. Mobile phones, AirPods, Bluetooth devices and smart watches are not allowed into the exam room (you can leave them with the exam's officer who will guide you on the day). 
 
            <br><br> All exams will take place at the Yardley Centre:
            
            <b> <br><br>1772 Coventry Road
            <br>Birmingham
            <br>B26 1PB </b>
            
            <br><br>Failure to turn up on time or to the exams altogether can impact your overall performance. If you have any further questions then please get in touch by emailing examsofficer@ateamacademy.co.uk.
            
            <br><br> Kind Regards, 
            
            <br><br> Hannah Tse </p>
            
        <p> STUDENT NAME: {} </p>
        <p> D.O.B: {} </p>
        <p> CANDIDATE NUMBER: {} </p>
        
        <table border="1" cellpadding="5" cellspacing="0">
            <thead>
                <tr>
                    <th>Exam Board</th>
                    <th>Exam Title</th>
                    <th>Paper Code</th>
                    <th>Paper Number</th>
                    <th>Date</th>
                    <th>Start Time</th>
                    <th>Duration (minutes)</th>
                    <th>Extra Information</th>
                </tr>
            </thead>
            <tbody>
    """.format(getStudent(student_id), getStudent(student_id), getStudentDOB(student_id), getCandidateNumber(student_id))

    # Iterate over each exam ID and get its details and associated exam papers
    for exam_id in exam_ids:
        exam, papers = getExamDetails(exam_id)
        
        # If the exam has papers, list them
        if papers:
            for paper in papers:
                html_content += """
                <tr>
                    <td>{exam_board}</td>
                    <td>{exam_title}</td>
                    <td>{paper_code}</td>
                    <td>{paper_no}</td>
                    <td>{date}</td>
                    <td>{start_time}</td>
                    <td>{duration}</td>
                    <td>{extra_info}</td>
                </tr>
                """.format(
                    exam_board = exam.examBoard,
                    exam_title=exam.title,
                    paper_code=paper.paperCode,
                    paper_no=paper.paperNo,
                    date=paper.date.strftime("%d-%m-%Y") if paper.date else '--/--/--',
                    start_time=paper.startTime.strftime("%H:%M") if paper.startTime else '--:--',
                    duration=paper.duration,
                    extra_info=paper.extra_info if paper.extra_info else 'N/A'
                )
        else:
            # If no papers are found, add a row indicating no papers for this exam
            html_content += """
            <tr>
                <td>{exam_title}</td>
                <td colspan="6">No papers available for this exam</td>
            </tr>
            """.format(exam_title=exam.title)

    # Close the table and HTML
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """

    return html_content


def generate_html_exam_timetable(student_id, start_date=datetime.datetime.strptime("1900-12-30", "%Y-%m-%d"), end_date=datetime.datetime.strptime("3100-12-30", "%Y-%m-%d")):
    # Get the list of exam IDs the student is registered for
    exam_ids = getExamsForStudent(student_id, start_date, end_date)

    if not exam_ids:
        return "<p>No exams registered for this student.</p>"

    # Get student details
    student_name = getStudent(student_id)
    student_dob = getStudentDOB(student_id)
    candidate_number = getCandidateNumber(student_id)

    # The candidate's exam centre drives the venue block (the address used to be
    # hardcoded to one site, wrong for anyone sitting elsewhere) and, when the
    # centre defines its own session start times, the displayed paper times.
    profile = exam_student.query.filter_by(studentID=student_id).first()
    centre = (Centre.query.filter_by(centreID=profile.centreID).first()
              if profile and profile.centreID else None)

    def _display_time(paper_start):
        if paper_start is None:
            return None
        if centre is not None:
            session_start = (centre.am_start if paper_start < datetime.time(12, 0)
                             else centre.pm_start)
            if session_start:
                return session_start.strftime("%H:%M")
        return paper_start.strftime("%H:%M")

    # Collect exams and their papers
    exams = []
    for exam_id in exam_ids:
        exam, papers = getExamDetails(exam_id)
        exam_data = {
            "exam_board": exam.examBoard,
            "title": exam.title,
            "papers": [
                {
                    "paper_code": paper.paperCode,
                    "paper_no": paper.paperNo,
                    "date": paper.date.strftime("%d-%m-%Y") if paper.date else None,
                    "start_time": _display_time(paper.startTime),
                    "duration": paper.duration,
                    "extra_info": paper.extra_info if paper.extra_info else None,
                }
                for paper in papers
            ]
        }
        exams.append(exam_data)

    # Render the HTML template with the data
    html_content = render_template(
        "email_templates/exam_timetable.html",
        student_name=student_name,
        student_dob=student_dob,
        candidate_number=candidate_number,
        exams=exams,
        centre_name=centre.name if centre else None,
        centre_address=(centre.address or "").strip() if centre else None,
        centre_am_start=centre.am_start.strftime("%H:%M") if centre and centre.am_start else None,
        centre_pm_start=centre.pm_start.strftime("%H:%M") if centre and centre.pm_start else None,
    )
    return html_content


def calculate_average_percentage(tests):
    test_totals = {}  # Dictionary to store total marks and total possible marks for each test name
    
    for test in tests:
        test_id, test_name, mark, total = test
        
        # Initialize totals for the test name if not already present
        if test_name not in test_totals:
            test_totals[test_name] = {'total_marks': mark, 'total_possible_marks': total}
        
        # Update totals for the test name
        test_totals[test_name]['total_marks'] += mark
        test_totals[test_name]['total_possible_marks'] += total
    
    average_percentages = []
    
    # Calculate average percentage for each test name
    for test_name, totals in test_totals.items():
        average_percentages.append({'averagePercentage' : round((totals['total_marks'] / totals['total_possible_marks']) * 100, 2), 'testName' : test_name})
    
    return average_percentages

def generate_colours(n, type):

    cmap = plt.cm.get_cmap(type, n)  # Choosing a colormap, you can choose any other colormap
    colors = [cmap(i) for i in range(n)]  # Generating n colors
    
    return colors

def grade_boundaries(test_name):
    result = (
        db.session.query(
            Grades.gradeID,
            Grades.mark,
            Tests.total
        )
        .join(Grades, Grades.testID == Tests.testID)
         .filter(Tests.name.like('%' + test_name + '%'))
         .filter(Grades.mark >= 0)
        .all()
    )
    
    for gradeID, mark, total in result:
        if getGradeSubject(gradeID) == getSubjectID2("A-LEVEL", "Maths"):
            percentage = (int(mark) / int(total)) * 100
            
            if percentage > 15.67:
                grade = 'E'
            if percentage > 28:
                grade = 'D'
            if percentage > 40.33:
                grade = 'C'
            if percentage > 52.67:
                grade = 'B'
            if percentage > 65.33:
                grade = 'A'
            if percentage > 81.33:
                grade = 'A*'

                
            stmt = update(Grades).where(Grades.gradeID == gradeID).values({"grade" : grade})
            db.session.execute(stmt)
            
            note = "giving " + getGrade(gradeID) + " a grade of " + grade
            # note = ''' lead up to submitting grades '''

            db.session.add( log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + "One-time was just triggered with the following note: " + note , date=datetime.utcnow() ))
            db.session.commit()   

def sendTopicLists():    
    # students_with_subjects = (
    # db.session.query(
    #     Students.id,
    #     Students.email,
    #     Subject.tier,
    #     Subject.title
    # )
    # .join(StudentLesson, StudentLesson.studentID == Students.id)
    # .join(Lesson, StudentLesson.lessonID == Lesson.lessonID)
    # .join(Subject, Lesson.subjectID == Subject.subjectID)
    # .filter(Subject.tier.in_(['A-LEVEL']))
    # .all()
    # )

    # topics = {  "GCSE Biology" : ['5. Homeostasis & Response', '6. Inheritance, Variation & Evolution', '7. Ecology'], 
    #             "GCSE Chemistry" : ['6. Chemical Change: Rate & Extent', '7. Organic Chemistry', '8. Chemical Analysis', '9. Chemistry of the Atmosphere', '10. Using Resources'], 
    #             "GCSE Physics" : ['5. Forces', '6. Waves', '7. Magnetism & Electromagnetism', '8. Space Physics'], 
    #             "GCSE Maths" : ['Calculator Topics (Paper 2)'], 
    #             "GCSE English" : ['Paper 2'], 
    #             "GCSE English Literature" : ['Paper 2'],
    #             "A-LEVEL Biology" : ['5 Energy transfers in and between organisms', '6 Organisms respond to changes in their internal and external environments', '7 Genetics, populations, evolution and ecosystems', '8 The control of gene expression'], 
    #             "A-LEVEL Chemistry" : ['3.1.2 Amount of substance','3.1.3 Bonding','3.1.4 Energetics','3.1.5 Kinetics','3.1.6 Chemical equilibria, Le Chateliers principle and Kc', '3.1.9  Carboxylic acids and derivatives', '3.3.1 Introduction to organic chemistry', '3.3.2 Alkanes', '3.3.3 Halogenoalkanes', '3.3.4 Alkenes', '3.3.5 Alcohols', '3.3.6 Organic analysis', '3.3.7 Optical isomerism', '3.3.8 Aldehydes and ketones', '3.3.9 Carboxylic acids and derivatives', '3.3.10 Aromatic chemistry', '3.3.11 Amines', '3.3.12 Polymers', '3.3.13 Amino acids, proteins and DNA', '3.3.14 Organic synthesis', '3.3.15 Nuclear magnetic resonance spectroscopy', '3.3.16 Chromatography'],
    #             "A-LEVEL Physics" : ['6.2 (Thermal Physics)', '7 Fields and their consequences', '8 Nuclear physics'], 
    #             "A-LEVEL Computer Science" : ['Component 02: Algorithms and programming'] }

    # Constructing the result in the desired format
    # result_dict = {}
    # emails = []
    # for student_id, email, subject_tier, subject_title in students_with_subjects:
    #     emails.append(email)


    # # Convert the dictionary to the desired list format
    # result_list = [{'email': email, 'subject_titles': subject_titles} for email, subject_titles in result_dict.items()]

    # # Printing the result
    # # for item in result_list:
    # print(emails)
    # for email in emails:
    #     topicList = []
    
    return ""

def getGradesByTestName(studentID, test_name=""):
    testIDs = Tests.query.filter(Tests.name.like(f'%{test_name}%')).all()
    testIDs = [testID.testID for testID in testIDs]

    grades = []
    for testID in testIDs:
        grade_list = Grades.query.filter_by(testID = testID).filter_by(studentID = studentID).filter(Grades.mark > -1).all()
        for grade in grade_list:
            grades.append(grade.gradeID)
    

    return grades

def getStudentAttendance(studentID):
    # Get the current academic year using the gen_academic_year function
    current_academic_year = gen_academic_year()

    # Subquery to get the first and last week of attendance for each lesson
    subquery = (
        db.session.query(
            StudentAttendance.lessonID,
            func.min(StudentAttendance.weekNo).label('first_week'),
            func.max(StudentAttendance.weekNo).label('last_week')
        )
        .filter(
            StudentAttendance.studentID == studentID,
            StudentAttendance.AcademicYear == current_academic_year,
            StudentAttendance.present == True
        )
        .group_by(StudentAttendance.lessonID)
        .subquery()
    )

    # Main query to calculate the total weeks attended
    total_weeks_attended = (
        db.session.query(func.count(StudentAttendance.id))
        .join(subquery, 
              (StudentAttendance.lessonID == subquery.c.lessonID) &
              (StudentAttendance.weekNo >= subquery.c.first_week) &
              (StudentAttendance.weekNo <= subquery.c.last_week))
        .filter(
            StudentAttendance.studentID == studentID,
            StudentAttendance.AcademicYear == current_academic_year,
            StudentAttendance.present == True
        )
        .scalar()
    )

    # Main query to calculate the total possible weeks
    total_weeks_possible = (
        db.session.query(func.count(StudentAttendance.id))
        .join(subquery, 
              (StudentAttendance.lessonID == subquery.c.lessonID) &
              (StudentAttendance.weekNo >= subquery.c.first_week) &
              (StudentAttendance.weekNo <= subquery.c.last_week))
        .filter(
            StudentAttendance.studentID == studentID,
            StudentAttendance.AcademicYear == current_academic_year
        )
        .scalar()
    )

    if total_weeks_possible == 0:
        return 0

    attendance_percentage = (total_weeks_attended / total_weeks_possible) * 100

    return attendance_percentage

def getStudentAttendanceForLesson(studentID, lessonID):
    # Get the current academic year using the gen_academic_year function
    current_academic_year = gen_academic_year()

    # Subquery to get the first and last week of attendance for the specific lesson
    subquery = (
        db.session.query(
            func.min(StudentAttendance.weekNo).label('first_week'),
            func.max(StudentAttendance.weekNo).label('last_week')
        )
        .filter(
            StudentAttendance.studentID == studentID,
            StudentAttendance.lessonID == lessonID,
            StudentAttendance.AcademicYear == current_academic_year,
            StudentAttendance.present == True
        )
        .subquery()
    )

    # Main query to calculate the total weeks attended for the specific lesson
    total_weeks_attended = (
        db.session.query(func.count(StudentAttendance.id))
        .filter(
            StudentAttendance.studentID == studentID,
            StudentAttendance.lessonID == lessonID,
            StudentAttendance.AcademicYear == current_academic_year,
            StudentAttendance.present == True,
            StudentAttendance.weekNo >= subquery.c.first_week,
            StudentAttendance.weekNo <= subquery.c.last_week
        )
        .scalar()
    )

    # Main query to calculate the total possible weeks for the specific lesson
    total_weeks_possible = (
        db.session.query(func.count(StudentAttendance.id))
        .filter(
            StudentAttendance.studentID == studentID,
            StudentAttendance.lessonID == lessonID,
            StudentAttendance.AcademicYear == current_academic_year,
            StudentAttendance.weekNo >= subquery.c.first_week,
            StudentAttendance.weekNo <= subquery.c.last_week
        )
        .scalar()
    )

    if total_weeks_possible == 0:
        return 0

    attendance_percentage = (total_weeks_attended / total_weeks_possible) * 100

    return attendance_percentage

def get_student_monthly_grades(student_id):
    # Query to get all tests, grades, and subjects for a specific student
    results = db.session.query(
        Lesson.subjectID,
        func.date_part('month', Tests.date).label('month'),
        Grades.mark
    ).join(
        Tests, Lesson.lessonID == Tests.lessonID
    ).join(
        Grades, Tests.testID == Grades.testID
    ).filter(
        Grades.studentID == student_id
    ).order_by(
        Lesson.subjectID,
        Tests.date
    ).all()
    
    # Process results to group by subjectID and month
    data_by_subject = defaultdict(list)
    months_set = set()
    for row in results:
        subject_id = row.subjectID
        month = int(row.month)
        mark = int(row.mark)
        data_by_subject[subject_id].append((month, mark))
        months_set.add(month)
    
    # Convert months set to a sorted list
    def month_sort_key(month):
        order = [9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8]
        return order.index(month)
    months = sorted(months_set, key=month_sort_key)
    
    # Prepare 2D array
    subjects = sorted(data_by_subject.keys())
    
    result = []
    for subject_id in subjects:
        row = [getSubjectName(subject_id)]  # Start with the subject name
        for month, mark in data_by_subject[subject_id]:
            row.append(f"{num_to_month(month)}: {mark}")
        result.append(row)
    
    months = [num_to_month(month) for month in months]
    return result, months

def getLessonsToJoin():
    result = []
    lessons = Lesson.query.filter(or_(or_(Lesson.weekNo == -1, Lesson.weekNo == gen_week_no(0)), Lesson.weekNo == gen_week_no(1))).filter(Lesson.active == True).filter(Lesson.AcademicYear == gen_academic_year()).all()
    
    for lesson in lessons:
        num = getNumberOfStudentsInLesson(lesson.lessonID)
        if 1 < num and num < 8: 
            result.append(lesson)
            
    return result

def getLessonsTomorrow():
    today = datetime.datetime.today()
    tomorrow = today + datetime.timedelta(days=1)
    
    tomorrow_day = tomorrow.strftime('%a').upper()
    
    if tomorrow_day == 'SUN':
        week_no = gen_week_no(1)
    else:
        week_no = gen_week_no(0)
        
    lessons = Lesson.query.filter(or_(Lesson.weekNo == int(week_no), Lesson.weekNo == -1))\
                          .filter_by(day = tomorrow_day)\
                          .filter_by(AcademicYear=gen_academic_year())\
                          .filter_by(active=True).all()
           
    lesson_map = {}
    
    for lesson in lessons:
        if lesson.tutorID not in lesson_map:
            lesson_map[lesson.tutorID] = [lesson]
        else: 
            lesson_map[lesson.tutorID].append(lesson)
                          
    return lesson_map 
    
def get_lessons_starting_soon():
    # Get the current time
    now = datetime.datetime.now()
    now_hour = int(now.strftime("%H"))
    now_minute = int(now.strftime("%M"))
    
    # Calculate the time 15 minutes from now
    future_time = now + timedelta(minutes = 30)
    future_hour = int(future_time.strftime("%H"))
    future_minute = int(future_time.strftime("%M"))
    
    # Query lessons
    lessons = Lesson.query.filter(
            Lesson.day == num_to_day(datetime.datetime.today().weekday()), 
            Lesson.weekNo == -1,
            Lesson.AcademicYear == gen_academic_year(), 
            Lesson.active == True, 
            Lesson.centreID == 2
        ).all()

    lessons_starting_soon = []
    for lesson in lessons:
        startHour = int(str(lesson.startTime).split(":")[0])
        startMinute = int(str(lesson.startTime).split(":")[1])
        
        if ((startHour > now_hour) or (startHour == now_hour and startMinute >= now_minute)) and ((startHour < future_hour) or (startHour == future_hour and startMinute <= future_minute)):
            lessons_starting_soon.append(lesson)
    
    return lessons_starting_soon


def get_weekend_lessons():
    lessons = Lesson.query.filter(
        or_(Lesson.day == "SAT", Lesson.day == "SUN"), 
        Lesson.weekNo == -1,
        Lesson.AcademicYear == gen_academic_year(), 
        Lesson.active == True, 
        Lesson.centreID != 1
    ).all()
    
    lessons = sorted(
        lessons, 
        key=lambda lesson: (lesson.day, lesson.centreID, lesson.tutorID, lesson.startTime)
    )    
    
    return lessons

def get_2up_filename(file_path):
    # Modify the filename to reflect the 2-up version
    return f"{file_path[:-4]}-2up.pdf"


def get_files_to_print(lessonID, weekNo, eco_mode=False): 
    reg, unreg, temp = getAttendance(lessonID, int(weekNo) - 1)
    copies = len(reg) + len(unreg) + len(temp)
    copies = (copies // 2) + 1 
    
    files = Files.query.filter(
        or_(
            Files.subjectID == getLessonSubject(lessonID),
            Files.lessonID == lessonID
        ),
        Files.weekNo == int(weekNo),
        Files.auto_print == True
    ).all()
    
    subject_folder = getFileFolder(getLessonSubject(lessonID))  # Function to get subject folder
    # files = [f"var/www/webApp/webApp/files/{ subject_folder }/{ file.filename}" for file in files]
    # code [lessonID]-[weekNo]-[copies]
    code = f"{lessonID}-{weekNo}-{str(copies)}"
    if 'nglish' in getSubjectName(getLessonSubject(lessonID)):
        files = [combine_two_pages_per_sheet(f"var/www/webApp/webApp/files/{subject_folder}/{file.filename}", f"var/www/webApp/webApp/files/{subject_folder}/{file.filename[:-4]}-2up.pdf", watermark=True, tutor_name=getStaffFirstName(getLessonTutor(lessonID)), code=code, eco_mode=False) for file in files if classTypeCheck(getLessonObject(lessonID), file.classtype)]
    else: 
        files = [combine_two_pages_per_sheet(f"var/www/webApp/webApp/files/{subject_folder}/{file.filename}", f"var/www/webApp/webApp/files/{subject_folder}/{file.filename[:-4]}-2up.pdf", watermark=True, tutor_name=getStaffFirstName(getLessonTutor(lessonID)), code=code, eco_mode=False, alternate_mode=True) for file in files if classTypeCheck(getLessonObject(lessonID), file.classtype)]
        
    

    return files


def get_file_page_count(file_path):
    # Open the PDF file
    with open(file_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        return len(reader.pages)
    
def mass_print(lessons, eco_mode=False):
    html_template = """
<div class="container mt-5">
    <h1 class="text-center">Weekend Files to Print</h1>
    <h2 class="text-center"> Eco Mode: {{ eco_mode }} </h2>

    {% for centre, centre_data in grouped_data.items() %}
        <h2>Centre: {{ centre }}</h2>
        <table class="table table-bordered" style="border: 1px solid #ddd; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #f8f9fa;">
                    <th style="border: 1px solid #ddd; padding: 8px;">Tutor</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Lesson</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Start Time</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">End Time</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">File Name</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Pages</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Copies</th>
                </tr>
            </thead>
            <tbody>
                {% for tutor, tutor_data in centre_data.items() %}
                    {% for lesson, lesson_data in tutor_data.items() %}
                        {% for file_info in lesson_data['files'] %}
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 8px;">{{ tutor }}</td>
                                <td style="border: 1px solid #ddd; padding: 8px;">{{ lesson_data['name'] }}</td>
                                <td style="border: 1px solid #ddd; padding: 8px;">{{ lesson_data['start_time'] }}</td>
                                <td style="border: 1px solid #ddd; padding: 8px;">{{ lesson_data['end_time'] }}</td>
                                <td style="border: 1px solid #ddd; padding: 8px;">{{ file_info[0] }}</td>  <!-- File Name -->
                                <td style="border: 1px solid #ddd; padding: 8px;">
                                    {% if file_info|length == 4 %}
                                        {{ file_info[2] }}  <!-- File Pages -->
                                    {% else %}
                                        --  <!-- Placeholder if pages data is not available -->
                                    {% endif %}
                                </td>
                                <td style="border: 1px solid #ddd; padding: 8px;">{{ file_info[1] }}</td>  <!-- Copies -->
                            </tr>
                        {% endfor %}
                    {% endfor %}
                {% endfor %}
            </tbody>
        </table>
        <p><strong>Total Sheets for {{ centre }}:</strong> {{ totals[centre] }}</p>
    {% endfor %}

    <h4 class="text-end">Overall Total Sheets: {{ overall_total }}</h4>
</div>

<style>
    @media print {
        @page {
            size: A4 landscape;
            margin: 20mm;
        }

        body {
            width: 100%;
            margin: 0;
            padding: 0;
        }

        table {
            width: 100%;
            page-break-before: always;
        }

        th, td {
            text-align: left;
            border: 1px solid #ddd;
            padding: 8px;
            word-wrap: break-word;
        }

        h2, h3, h4 {
            text-align: center;
        }
    }
</style>

    """

    grouped_data = {}
    totals = {}
    overall_total_pages = 0

    # Group lessons by center, tutor, and lesson
    for lesson in lessons:
        files = get_files_to_print(lesson.lessonID, gen_week_no(0), eco_mode=eco_mode)
        reg, unreg, temp = getAttendance(lesson.lessonID, gen_week_no(-7))
        
        copies = len(reg) + len(unreg) + len(temp)

        centre = getCentre(lesson.centreID)
        tutor = getStaff(lesson.tutorID)
        lesson_name = lesson.lessonID
        start_time = lesson.startTime.strftime("%H:%M")
        end_time = lesson.endTime.strftime("%H:%M")
        centre_total_pages = 0

        if centre not in grouped_data:
            grouped_data[centre] = {}
            totals[centre] = 0

        if tutor not in grouped_data[centre]:
            grouped_data[centre][tutor] = {}

        if lesson_name not in grouped_data[centre][tutor]:
            grouped_data[centre][tutor][lesson_name] = {
                "name": getSubjectName(lesson.subjectID),
                "start_time": start_time,
                "end_time": end_time,
                "files": [],  # Initialize files as a list
                "file_count": 0  # Initialize file count
            }

        if len(files) > 0:
            for file in files:
                filename = file.replace("var/www/webApp/webApp/files/", "").replace("_", " ")
                file_pages = get_file_page_count(file)  # Get page count for the file
                pages_printed = file_pages * copies  # Total pages for this file
                grouped_data[centre][tutor][lesson_name]["files"].append((filename, copies, file_pages, pages_printed))
                centre_total_pages += pages_printed
                
                e1 = EmailSender()
                e1.send(email = "ateam1772@gmail.com", subject = f"Printing {getStaff(lesson.tutorID)}s files - {str(pages_printed)}", message = f"COPIES={int(copies)}\nB/W PRINT=ON\nDUPLEX=LEFT", files=[file],  subtype='plain')        
        else: 
            grouped_data[centre][tutor][lesson_name]["files"].append(('NO FILES', 0, 0, 0))

            
            

        # Update file count for the lesson
        grouped_data[centre][tutor][lesson_name]["file_count"] = len(files)

        totals[centre] += centre_total_pages
        overall_total_pages += centre_total_pages


    # Render the HTML with Jinja2
    template = Template(html_template)
    rendered_html = template.render(
        grouped_data=grouped_data, totals=totals, overall_total=overall_total_pages, eco_mode=eco_mode
    )
    

    # Generate PDF using WeasyPrint
    current_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"/var/www/webApp/webApp/print_reports/Printing_report_{current_datetime}.pdf"

    # Generate PDF using WeasyPrint
    pdf = HTML(string=rendered_html).write_pdf()
    with open(pdf_filename, "wb") as f:
        f.write(pdf)

    return pdf_filename
    # return render_template_string(html_template, grouped_data=grouped_data, totals=totals, overall_total=0)

def is_valid_email(email):
    
    if email != '':
        return True
    else: 
        return False

    # """Check if the email is a valid format."""

    # # Regular expression for validating an Email

    # regex = r'^[a-zA-Z0-9]+[\._]?[a-zA-Z0-9]+[@]\w+([.]\w+)+$'
    
    # # If the string matches the regex, it is a valid email
    # return bool(re.match(regex, email))

    
def calculatePointsForLesson(lessonID, weekNo, userID):
    # Fetch lesson information
    lesson_info = db.session.query(LessonInfo).filter_by(lessonID=lessonID, weekNo=weekNo).first()

    if not lesson_info:
        return {"error": "Lesson not found"}

    # Fetch attendance data from all three tables
    student_attendance = db.session.query(StudentAttendance).filter_by(lessonID=lessonID, weekNo=weekNo).all()
    temp_attendance = db.session.query(TempAttendance).filter_by(lessonID=lessonID, weekNo=weekNo).all()
    unregistered_attendance = db.session.query(UnregisteredAttendance).filter_by(lessonID=lessonID, weekNo=weekNo).all()

    # Combine attendance data into one list
    total_attendance = student_attendance + temp_attendance + unregistered_attendance

    # 1. Calculate student retention (attendance)
    total_students = len(total_attendance)
    present_students = sum(1 for record in student_attendance if getattr(record, 'present', False)) + \
                       sum(1 for record in unregistered_attendance if getattr(record, 'present', False))

    # Calculate retention percentage for the current week
    if total_students == 0:
        retention_percentage = 0
    else:
        retention_percentage = (present_students / total_students) * 100

    # Fetch past 4 weeks' attendance to compare retention
    past_week_nos = [weekNo - i for i in range(1, 5)]  # Last 4 weeks
    past_attendance = db.session.query(StudentAttendance).filter(
        StudentAttendance.lessonID == lessonID,
        StudentAttendance.weekNo.in_(past_week_nos)
    ).all()

    past_total_students = len(past_attendance)
    past_present_students = sum(1 for record in past_attendance if getattr(record, 'present', False))

    # Compare with past retention percentage
    if past_total_students == 0:
        retention_change = retention_percentage
    else:
        past_retention_percentage = (past_present_students / past_total_students) * 100
        retention_change = retention_percentage - past_retention_percentage  # Retention increase or decrease

    retention_score = max(0, min(100, retention_change))  # Clamp the retention score between 0 and 100

    # 2. Add points for lesson description
    description_score = 10 if lesson_info.description and len(lesson_info.description) > 0 else 0

    # 3. Add points for punctuality (assuming `register` is used as a punctuality marker)
    punctuality_score = 10 if lesson_info.register else 0

    # 4. Add points for homework
    homework_score = 10 if lesson_info.homework else 0

    # Calculate the total score out of 100
    total_score = retention_score + description_score + punctuality_score + homework_score

    return {
        "retention_score": retention_score,
        "description_score": description_score,
        "punctuality_score": punctuality_score,
        "homework_score": homework_score,
        "total_score": total_score
    }

def extract_classes_from_html(folder_path, output_file):
    class_dict = {}

    # Regex to match classes in HTML tags
    class_pattern = re.compile(r'class="([^"]+)"')
    tag_pattern = re.compile(r'<(\w+)\s.*?class="([^"]+)".*?>')

    # Iterate through all files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".html"):
            filepath = os.path.join(folder_path, filename)

            # Read the HTML file
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()

                # Find all tags with class attributes
                matches = tag_pattern.findall(content)

                for tag, class_list in matches:
                    # Split multiple classes in one class attribute
                    classes = class_list.split()
                    for cls in classes:
                        if cls not in class_dict:
                            class_dict[cls] = set()  # Use a set to avoid duplicate tags
                        class_dict[cls].add(tag)

    # Write the extracted classes and their associated tags into the output file
    with open(output_file, 'w', encoding='utf-8') as css_file:
        for cls, tags in class_dict.items():
            # Write the comment with the associated tags
            css_file.write(f"/* Used in: {', '.join(tags)} */\n")
            css_file.write(f".{cls} {{\n    /* Add your styles here */\n}}\n\n")

def combine_two_pages_per_sheet(input_filename, output_filename, watermark=False, tutor_name="", code="None Supplied", eco_mode=False, auto=True, alternate_mode=False):
    # Read the input PDF
    reader = PdfReader(input_filename)
    num_pages = len(reader.pages)

    # Set up the canvas for the new PDF
    output_buffer = BytesIO()
    page_width, page_height = landscape(A4)
    c = canvas.Canvas(output_buffer, pagesize=(page_width, page_height))
    
    # Convert each page to an image
    images = convert_from_path(input_filename)
    
    if eco_mode:
        num_pages = 8 if num_pages > 8 else num_pages
        
        
    if alternate_mode: 
        for i in range(8, num_pages, 2):
            # Place the first page image on the left
            img1 = ImageReader(images[i])
            c.drawImage(img1, 0, 0, width=page_width / 2, height=page_height)

            # Add watermark to the front page
            if watermark and i == 0:
                if auto:
                    watermark_text = f"Printed automatically for {tutor_name}, Code: {code}"
                else: 
                    watermark_text = f"Printed by {tutor_name}"

                c.setFont("Helvetica-Bold", 9)
                c.setFillColorRGB(0, 0, 0)  # Light gray
                c.drawString(20, page_height - 20, watermark_text)

            # Place the second page image on the right (if exists)
            if i + 1 < num_pages:
                img2 = ImageReader(images[i + 1])
                c.drawImage(img2, page_width / 2, 0, width=page_width / 2, height=page_height)

            # Finish the page
            c.showPage()
    else:
        # Process the images in pairs for 2-up layout
        for i in range(0, num_pages, 2):
            # Place the first page image on the left
            img1 = ImageReader(images[i])
            c.drawImage(img1, 0, 0, width=page_width / 2, height=page_height)

            # Add watermark to the front page
            if watermark and i == 0:
                if auto:
                    watermark_text = f"Printed automatically for {tutor_name}, Code: {code}"
                else: 
                    watermark_text = f"Printed by {tutor_name}"

                c.setFont("Helvetica-Bold", 9)
                c.setFillColorRGB(0, 0, 0)  # Light gray
                c.drawString(20, page_height - 20, watermark_text)

            # Place the second page image on the right (if exists)
            if i + 1 < num_pages:
                img2 = ImageReader(images[i + 1])
                c.drawImage(img2, page_width / 2, 0, width=page_width / 2, height=page_height)

            # Finish the page
            c.showPage()
    
    # Save the final PDF
    c.save()
    
    # Write the PDF to the output path
    with open(output_filename, 'wb') as f:
        f.write(output_buffer.getvalue())

    return output_filename


# extract_classes_from_html('/var/www/webApp/webApp/templates', '/var/www/webApp/webApp/output.txt')

def print_files_at_printer(files, copies = 1, two_up=True, BW=True, centre="COV", auto=True, tutor_name=""):
    if centre == "COV":
        email = "ateam1772@gmail.com"
    elif centre == "SOHO":
        email = "ateam305soho@gmail.com"
    else:
        email = "ateam1772@gmail.com"
        
    if BW: 
        colourmode = "B/W PRINT=ON"
    else: 
        colourmode = "B/W PRINT=OFF"
        
    if two_up:
        files = [combine_two_pages_per_sheet(file, get_2up_filename(file), watermark=True, auto=auto, tutor_name=tutor_name ) for file in files]
    
    for file in files: 
        e1 = EmailSender()
        e1.send(email = email, subject = f"Printing {int(copies)} of {file} ", message = f"COPIES={int(copies)}\n{colourmode}\nDUPLEX=LEFT", files=[file],  subtype='plain')
