import os as _os
try:
    from dotenv import load_dotenv as _load_dotenv
    # Load <outer webApp>/.env (one level above this package) into the environment.
    _load_dotenv(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), ".env"))
except ImportError:
    pass  # python-dotenv not installed; rely on real environment variables / fallbacks

from flask import Flask, render_template, redirect, request, flash, send_from_directory, url_for, send_file, session, abort, jsonify, Response, Blueprint
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate
from flask_cors import CORS
from sqlalchemy import select, insert, update, delete, and_, or_, distinct, case
from sqlalchemy.orm import aliased
from sqlalchemy.exc import SQLAlchemyError
from Schema import *
from functions import *
from seating import plan_seating
from clashes import group_clashes, time_range_str
from predicted_paper_generation import *
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, current_user, logout_user, login_required, UserMixin, LoginManager, AnonymousUserMixin
from datetime import date, datetime
from os.path import isfile, join, isdir
from werkzeug.utils import secure_filename, safe_join
try:
    from pdfminer.high_level import extract_text
except Exception:
    extract_text = None
from os import listdir
from datetime import date, datetime
from email.mime.text import MIMEText
from EmailSender import *
from PIL import Image
from flask_apscheduler import APScheduler
from io import StringIO
from operator import itemgetter, attrgetter
from webApp.init_beta import beta  
try:
    from weasyprint import HTML, CSS
except Exception:
    HTML = CSS = None
try:
    import matplotlib
    matplotlib.use("Agg")  # headless backend
    from matplotlib import cm
except Exception:
    cm = None
import json
import csv
import numpy as np
import smtplib
import time
import babel.numbers
import decimal
import itertools
import random
import secrets
import subprocess
import base64
import os
import calendar


# from config import MEDIA_FOLDER

 
app = Flask(__name__)
# Secret key from env. If unset, fall back to a random per-process key rather
# than a publicly known string: sessions won't survive a restart, but they
# can't be forged either. Set SECRET_KEY in production.
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

app.register_blueprint(beta)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.anonymous_user = Anonymous
login_manager.login_view = '/'

# Connection string from env (DATABASE_URL); fallback is the LOCAL dev DB only.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:Ateam123@localhost:5432/ateam")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 500 
 
db.init_app(app)
migrate = Migrate(app, db)

emailSender = EmailSender()
# emailSsender.send("asafwaan03@gmail.com", "test email", "this is a test please ignore")
# refer ^ 

# initialize scheduler
scheduler = APScheduler()
# if you don't wanna use a config, you can set options here:
scheduler.api_enabled = True
scheduler.init_app(app)
scheduler.start()

resetdb = False;     #False = it stays the same each time
if resetdb:
    with app.app_context():
        #db.drop_all()
        db.create_all()
        #db_init()

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return get_user(user_id)

def check_maintenance(maintenance=True):
    # if maintenance and current_user.id != 142 and current_user.id != 2 and current_user.id != 468:            
    if maintenance and not permission_required(current_user.id, 'allow_maintenance') and current_user.id != 142:
        abort(503, "")

def role_required(requiredRole, message):          
    if getRoleLevel(getUserRole(current_user.id)) >= getRoleLevel(requiredRole):
        return True
    else: 
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): tried to access " + message + " but was denied", date=datetime.utcnow()))
        db.session.commit()
        abort(403, "")

# def permission_required(userID, permissionRequired):
#     if current_user.is_admin():
#         return True
#     elif current_user.is_student(): 
#         return False
    
#     if getTutorAccess(getOtherID("tutor", userID), permissionRequired):
#         return True
#     else:
#         db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): tried do an action but requires " + permissionRequired + " and was denied", date=datetime.utcnow()))
#         db.session.commit()
#         abort(400, "")


def permission_required(userID, permissionRequired, fatal=False, message = ''): 
    if getUserPermission(userID, permissionRequired) or getRolePermission(getUserRole(userID), permissionRequired):
        return True
    else: 
        if fatal:
            db.session.add(log(role = getUserRole(current_user.id), message= f" ({getUserName(current_user.id)}): has just tried to do an action which requires {permissionRequired} but was blocked - {message}", date=datetime.utcnow()))
            db.session.commit()
            abort(400, "")
        else:
            return False
        
'  _____ ____  ____   ___  ____      _   _    _    _   _ ____  _     ___ _   _  ____  '
' | ____|  _ \|  _ \ / _ \|  _ \    | | | |  / \  | \ | |  _ \| |   |_ _| \ | |/ ___| '
' |  _| | |_) | |_) | | | | |_) |   | |_| | / _ \ |  \| | | | | |    | ||  \| | |  _  '
' | |___|  _ <|  _ <| |_| |  _ <    |  _  |/ ___ \| |\  | |_| | |___ | || |\  | |_| | '
' |_____|_| \_\_| \_\\___/|_| \_\   |_| |_/_/   \_\_| \_|____/|_____|___|_| \_|\____| '
'                                                                                     '


@app.errorhandler(403)
def error403(error):
    return render_template('403.html'), 403

@app.errorhandler(404)
def error404(error):
    return render_template('404.html'), 404

@app.errorhandler(503)
def error503(error):
    return render_template('maintenance.html'), 503

@app.errorhandler(400)
def error400(error):
    return render_template("400.html"), 400

# @app.errorhandler(300)
# def error400(error):
#     #filename error
#     return render_template("300.html"), 400


MEDIA_FOLDER = 'var/www/webApp/webApp/'
@app.route('/CS310/images/<filename>')
def download_file(filename):
    return send_from_directory(MEDIA_FOLDER, filename, as_attachment=True)


# @app.before_request
# def check_under_maintenance():
#     maintenance_mode = True
#     if maintenance_mode and current_user.id != 142:  
#         return render_template("maintenance.html") 



'  ____   ___  _   _ _____ _____ ____        __   ____   _    ____ _____ ____  '
' |  _ \ / _ \| | | |_   _| ____/ ___|      / /  |  _ \ / \  / ___| ____/ ___| '
' | |_) | | | | | | | | | |  _| \___ \     / /   | |_) / _ \| |  _|  _| \___ \ '
' |  _ <| |_| | |_| | | | | |___ ___) |   / /    |  __/ ___ \ |_| | |___ ___) |'
' |_| \_\\___/ \___/  |_| |_____|____/   /_/     |_| /_/   \_\____|_____|____/ '
'                                                                              '


@app.route('/', methods=['POST', 'GET'])
def begin():
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        
        if user is None or not check_password_hash(user.password, password):
            # If email or password is incorrect, render the template with an error message
            return render_template('login.html', error="Incorrect email or password. Please try again.")

        if getUserPermission(user.id, action="log_on"):
            user.authenticated = True
            login_user(user, remember=True)
            session['role'] = user.role
            session['name'] = getUserName(user.id)
            session['theme'] = getUserTheme(user.id)
            # print(session['theme'])


            if check_password_hash(generate_password_hash('password'), password):
                session.pop('_flashes', None)
                return redirect(url_for('change_password'))
            
            if current_user.is_admin(): 
                return redirect(url_for('admin_dashboard'))
            if current_user.is_tutor(): 
                return redirect(url_for('tutor_dashboard'))
            if current_user.is_student():
                return redirect(url_for('allTimetable', offset="0"))
            if current_user.is_parent():
                return redirect(url_for('parent_dashboard'))
            if current_user.is_receptionist() or current_user.is_exams_officer():
                return redirect(url_for('receptionist_dashboard'))
            else:
                return redirect(url_for('allTimetable', offset=0))

        return redirect(url_for('begin'))
    
    return render_template('login.html')

@app.route('/admin_dashboard', methods = ['POST', 'GET'])
@login_required
def admin_dashboard(): 
    check_maintenance()
    role_required("admin", "admin dashboard")
    
    #lesson completion percentage
    Lessons = Lesson.query.filter(Lesson.AcademicYear == gen_academic_year()).filter(or_(Lesson.weekNo == gen_week_no(0), Lesson.weekNo == -1)).all()
    allLessons = len(Lessons)
    # completedLessons = len(LessonInfo.query.filter_by(weekNo = gen_week_no(0)).all())
    completedLessons = 0
    for lesson in Lessons: 
        lesson_info = LessonInfo.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = gen_week_no(0)).first()
        if lesson_info: 
            if lesson_info.approved: 
                completedLessons += 1
            else: 
                continue
    lessonCompletionPercentage = round((completedLessons / allLessons) * 100) if allLessons else 0
    
    #student enrollment data per month
    start_date = '2024-08-01'
    end_date = '2025-07-31'

    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')

    result = (
        db.session.query(
            func.extract('month', Students.declaration_date).label('month'),
            func.count().label('count')
        )
        .filter(Students.declaration_date.between(start_datetime, end_datetime))
        .group_by(func.extract('month', Students.declaration_date))
        .order_by(func.extract('month', Students.declaration_date))
        .all()
    )

    studentEnrollment = [0] * 13
    for row in result:
        month_number = row.month
        count = row.count
        if int(row.month < 8):
            studentEnrollment[int(month_number - 9)] = count
        else: 
            studentEnrollment[int(month_number - 8)] = count
        
    #Student Groups
    year_group_categories = ['6 and below', '7-9', '10-11', '12-13', 'Other']

    result = (
        db.session.query(
            Students.year_group,
            func.count().label('count')
        )
        .group_by(Students.year_group)
        .filter(Students.declaration_date >= "2024-07-01")
        .all()
    )

    year_group_counts = [0] * len(year_group_categories)

    for row in result:
        year_group = row.year_group
        count = row.count

        # Determine the index for the array based on year group category
        try:
            int(year_group)
        
            if int(year_group) <= 6:
                index = 0
            elif 7 <= int(year_group) <= 9:
                index = 1
            elif 10 <= int(year_group) <= 11:
                index = 2
            elif 12 <= int(year_group) <= 13:
                index = 3
            else:
                index = 4
        except: 
            index = 4

        year_group_counts[index] += count
        
    colours = ['#4e73df', '#1cc88a', '#36b9cc', '#8553a1', '#14a37f' ]
    
    #lastWeekEarnings
    numberOfLessons = len(LessonInfo.query.filter_by(weekNo = gen_week_no(-7)).all())
    regStudents = len(StudentAttendance.query.filter_by(weekNo = gen_week_no(-7)).filter_by(present = True).all())
    unregStudents = len(UnregisteredAttendance.query.filter_by(weekNo = gen_week_no(-7)).filter_by(present = True).all())
    tempStudents = len(TempAttendance.query.filter_by(weekNo = gen_week_no(-7)).all())

    totalStudents = regStudents + unregStudents + tempStudents
    
    #lastweekEarnings = moneyFromStudents - moneyOutToTutors - rent - printing - misc expenses
    lastWeekEarnings = (12.5 * totalStudents) - ((15 * numberOfLessons) + 650 + 20 + 1000)
    
    
    #allTimeEarnings
    numberOfLessons = len(LessonInfo.query.all())
    regStudents = len(StudentAttendance.query.filter_by(present = True).all())
    unregStudents = len(UnregisteredAttendance.query.filter_by(present = True).all())
    tempStudents = len(TempAttendance.query.all())

    totalStudents = regStudents + unregStudents + tempStudents
    
    allTimeEarnings = (15 * totalStudents) - (15 * numberOfLessons) - (int(gen_week_no(0))*(650 + 20 + 1000))
    allTimeEarnings = "{:,}".format(allTimeEarnings)
    
    
    #percentageAttendance
    current_day = datetime.now().strftime('%a').upper()
    current_week_no = gen_week_no(0)
    
    lessonList = Lesson.query.filter(or_(Lesson.weekNo == -1, Lesson.weekNo == current_week_no)).filter(Lesson.day == current_day).filter_by(active = True).all()
        
    lessons = [lesson.lessonID for lesson in lessonList]
    
    percentageAttendance = []
    for lesson in lessons:
        totalStudent = len(StudentLesson.query.filter_by(lessonID = lesson).all())
        totalUnreg = len(unregisteredStudentLessons.query.filter_by(lessonID = lesson).all())
        
        presentStudent = len(StudentAttendance.query.filter_by(lessonID = lesson).filter_by(weekNo = current_week_no).filter_by(present = True).all())
        presentUnreg = len(UnregisteredAttendance.query.filter_by(lessonID = lesson).filter_by(weekNo = current_week_no).filter_by(present = True).all())
        
    
        if (totalStudent + totalUnreg <= 0) or (presentStudent + presentUnreg <=0):
            percentageAttendance.append([getLessonString(lesson), 0])
        else: 
            # print([getLessonString(lesson), presentStudent,  presentUnreg, totalStudent , totalUnreg ])
            percentageAttendance.append([getLessonString(lesson), round((presentStudent + presentUnreg) * 100 / (totalStudent + totalUnreg), 2) ])
    
    #Site-usage =
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=5)

    result = (
        db.session.query(
            func.date_trunc('hour', log.date).label('hour_slot'),
            func.sum(case((and_(log.role == 'admin', log.message.contains('safwaan@ateam') == False), 1), else_=0)).label('admin_total'),
            # func.sum(case((log.role == 'admin', 1), else_=0)).label('admin_total'),
            func.sum(case((log.role == 'tutor', 1), else_=0)).label('tutor_total'),
            func.sum(case((log.role == 'student', 1), else_=0)).label('student_total'), 
            func.sum(case((log.role == 'anonymous', 1), else_=0)).label('anon_total')

        )
        .filter(log.date >= start_date, log.date <= end_date)
        .group_by(func.date_trunc('hour', log.date))
        .order_by(func.date_trunc('hour', log.date))
        .all()
    )

    # Extract the results into arrays for each role
    site_usage_hour_slots = [row.hour_slot.strftime("%d/%m - %H:00") for row in result]
    admin_totals = [row.admin_total for row in result]
    tutor_totals = [row.tutor_total for row in result]
    student_totals = [row.student_total for row in result]
    anon_totals = [row.anon_total for row in result]
    

        
    
    return render_template("admin_dashboard.html", 
                           lessonCompletionPercentage = lessonCompletionPercentage, 
                           studentEnrollment = studentEnrollment, 
                           year_group_counts = year_group_counts, 
                           year_group_categories = year_group_categories, 
                           colours = colours, 
                           lastWeekEarnings = format(lastWeekEarnings, '.2f'), 
                           allTimeEarnings = allTimeEarnings, 
                           percentageAttendance = percentageAttendance, 
                           site_usage_hour_slots = site_usage_hour_slots, 
                           admin_totals = admin_totals, 
                           tutor_totals = tutor_totals, 
                           student_totals = student_totals,
                           anon_totals = anon_totals)

@app.route('/tutor_dashboard', methods = ['POST', 'GET'])
@login_required
def tutor_dashboard():
    check_maintenance()
    role_required("tutor", "Tutor Dashboard")

    if getUserRole(current_user.id) != "tutor":
        return redirect('/allTimetable?offset=0')
    else: 
        tutorID = getOtherID("tutor", current_user.id)
        
    #punctuality
    
    #review for all staff 
    
    #adds to points - invigilation
    
    #lesson completion percentage
    allLessons = len(Lesson.query.filter(or_(Lesson.weekNo == gen_week_no(0), Lesson.weekNo == -1)).filter_by(tutorID=tutorID).filter_by(active=True).all())
    completedLessons = len(LessonInfo.query.filter_by(weekNo = gen_week_no(0)).filter_by(tutorID=tutorID).all())
    lessonCompletionPercentage = round((completedLessons / allLessons) * 100) if allLessons else 0 if allLessons != 0 else 0

    points = getUserPoints(current_user.id)
    
    #Lesson Attendance this week
    current_week_no = gen_week_no(0)
    lessonList = Lesson.query.filter(or_(Lesson.weekNo == -1, Lesson.weekNo == current_week_no)).filter_by(active = True).filter_by(tutorID=tutorID).all()
    lessons = [lesson.lessonID for lesson in lessonList]
    
    percentageAttendance = []
    for lesson in lessons:
        totalStudent = len(StudentLesson.query.filter_by(lessonID = lesson).all())
        totalUnreg = len(unregisteredStudentLessons.query.filter_by(lessonID = lesson).all())
        
        presentStudent = len(StudentAttendance.query.filter_by(lessonID = lesson).filter_by(weekNo = current_week_no).filter_by(present = True).all())
        presentUnreg = len(UnregisteredAttendance.query.filter_by(lessonID = lesson).filter_by(weekNo = current_week_no).filter_by(present = True).all())
        
    
        if (totalStudent + totalUnreg <= 0) or (presentStudent + presentUnreg <=0):
            percentageAttendance.append([getLessonString(lesson), 0])
        else: 
            # print([getLessonString(lesson), presentStudent,  presentUnreg, totalStudent , totalUnreg ])
            percentageAttendance.append([getLessonString(lesson), round((presentStudent + presentUnreg) * 100 / (totalStudent + totalUnreg), 2) ])


    #Tutor Ranking
    subquery = (
    db.session.query(
        Lesson.tutorID,
        func.count(Lesson.lessonID).label('lesson_count')
    )
    .filter(Lesson.weekNo.between(18, 24))
    .group_by(Lesson.tutorID)
    .order_by(func.count(Lesson.lessonID).desc())
    .limit(1)
    .subquery()
    )

    result = (
    db.session.query(
        Lesson.tutorID,
        func.avg(case(
            (Tests.total > 0, (Grades.mark / Tests.total) * 100),
            else_=0
        )).label('averagePercentageScore')
    )
    .join(Tests, Lesson.lessonID == Tests.lessonID)
    .join(Grades, Tests.testID == Grades.testID)
    .filter(Grades.mark > 0)  # Exclude grades less than or equal to 0
    .filter(Tests.total > 0)  # Ensure Tests.total is greater than 0
    .filter(Tests.date >= "2024-09-20")  # Add the date filter
    .group_by(Lesson.tutorID)
    .all()
    )



    tutorsPerformance = [tutor_id for tutor_id, _ in result]
    try:
        ranking = tutorsPerformance.index(getOtherID("tutor", current_user.id)) + 1
    except ValueError:
        ranking = len(tutorsPerformance)

    totalTutors = len(tutorsPerformance)
        
    #total-hours
    current_academic_year = gen_academic_year()

    LessonAlias = aliased(Lesson)
    LessonInfoAlias = aliased(LessonInfo)

    total_hours = (
        db.session.query(func.sum(LessonInfoAlias.duration))
        .join(LessonAlias, LessonAlias.lessonID == LessonInfoAlias.lessonID)
        .filter(
            LessonInfoAlias.tutorID == tutorID,
            LessonAlias.AcademicYear == current_academic_year,
            LessonInfoAlias.approved == True
        )
        .scalar()
    )

    if total_hours is None:
        total_hours = 0


    #site-usage
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=5)

    result = (
    db.session.query(
        func.date_trunc('hour', log.date).label('hour_slot'),
        # Uncomment and fix if needed
        # func.sum(case((log.role == 'admin', 1), else_=0)).label('admin_total'),
        func.sum(case((and_(log.role == 'tutor', getTutorEmail(tutorID) != None), 1), else_=0)).label('tutor_total'),
    )
    .filter(log.date >= start_date, log.date <= end_date)
    .group_by(func.date_trunc('hour', log.date))
    .order_by(func.date_trunc('hour', log.date))
    .all()
    )

    site_usage_hour_slots = [row.hour_slot.strftime("%d/%m - %H:00") for row in result]
    tutor_totals = [row.tutor_total for row in result]
    
    #student-groups
    year_group_categories = ['6 and below', '7-9', '10-11', '12-13', 'Other']

    tutorID = getOtherID('tutor', current_user.id)

    result = (
        db.session.query(
            Students.year_group,
            func.count().label('count')
        )
        .join(StudentLesson, Students.id == StudentLesson.studentID)
        .join(Lesson, StudentLesson.lessonID == Lesson.lessonID)
        .filter(Lesson.tutorID == tutorID)
        .filter(Lesson.active == True)
        .filter(Lesson.weekNo == -1)
        .group_by(Students.year_group)
        .all()
    )

    year_group_counts = [0] * len(year_group_categories)

    for row in result:
        year_group = row.year_group
        count = row.count

        try:
            int_year_group = int(year_group)
            if int_year_group <= 6:
                index = 0
            elif 7 <= int_year_group <= 9:
                index = 1
            elif 10 <= int_year_group <= 11:
                index = 2
            elif 12 <= int_year_group <= 13:
                index = 3
            else:
                index = 4
        except ValueError:
            index = 4

        year_group_counts[index] += count

    colours = ['#4e73df', '#1cc88a', '#36b9cc', '#8553a1', '#14a37f']
    
    latestReview = StaffReviews.query.filter_by(staffID=tutorID).order_by(StaffReviews.date.desc()).first()
    
    strikeInformation = StaffStrikes.query.filter_by(staffID = tutorID).order_by(StaffStrikes.date.desc()).all()

    return render_template("tutor_dashboard.html", 
                           lessonCompletionPercentage=lessonCompletionPercentage, 
                           percentageAttendance=percentageAttendance, 
                           ranking=ranking, 
                           points = points,
                           totalTutors = 
                           totalTutors, 
                           total_hours = total_hours, 
                           year_group_counts = year_group_counts, 
                           year_group_categories = year_group_categories, 
                           colours = colours, 
                           site_usage_hour_slots = site_usage_hour_slots, 
                           tutor_totals = tutor_totals, 
                           review = latestReview, 
                           strikes = strikeInformation)

@app.route('/student_dashboard', methods=['POST', 'GET'])
@login_required
def student_dashboard():
    studentID = getOtherID("student", current_user.id)
    percentageAttendanceOverall = getStudentAttendance(studentID)
    
    student_lessons = db.session.query(StudentLesson.lessonID).filter_by(studentID=studentID).all()

    # Attendance per lesson
    percentageAttendance = []
    for lesson in student_lessons:
        lesson_id = lesson.lessonID
        lesson_name = getLessonString(lesson_id)
        attendance_percentage = getStudentAttendanceForLesson(studentID, lesson_id)
        percentageAttendance.append({
            'name': lesson_name,
            'attendance': attendance_percentage
        })
    
    # Fetch class comments along with tutor names
    class_comments = (
        db.session.query(LessonInfo, Lesson, Staff)
        .join(Lesson, Lesson.lessonID == LessonInfo.lessonID)
        .join(Staff, Staff.id == LessonInfo.tutorID)
        .filter(
            LessonInfo.lessonID.in_([l.lessonID for l in student_lessons]),
            LessonInfo.description.isnot(None),
            LessonInfo.description != '', 
            or_(LessonInfo.weekNo == gen_week_no(0), LessonInfo.weekNo == gen_week_no(-1)), 
            Lesson.AcademicYear == gen_academic_year()
            
        )
        .order_by(Lesson.startTime.desc())
        .all()
    )

    # Prepare the list of comments with tutor names
    comments = [{
        'tutor_name': comment.Staff.firstName,
        'description': comment.LessonInfo.description,
        'subject' : getSubjectName(comment.Lesson.subjectID),
        'day' : comment.Lesson.day,
        'weekNo' : comment.LessonInfo.weekNo,
        'lesson_start_time': comment.Lesson.startTime.strftime('%I:%M %p')
    } for comment in class_comments]

    # Time until next lesson
    current_week_no = gen_week_no(0)
    
    next_lesson = (
        db.session.query(Lesson, StudentLesson)
        .join(StudentLesson, Lesson.lessonID == StudentLesson.lessonID)
        .filter(
            StudentLesson.studentID == studentID,
            Lesson.active == True,
            (Lesson.weekNo == -1) | (Lesson.weekNo == current_week_no), 
            Lesson.AcademicYear == gen_academic_year()
        )
        .order_by(Lesson.startTime)
        .first()
    )

    if not next_lesson:
        lesson, student_lesson = None, -1
        time_until_lesson = "No upcoming lessons"
    else:
        lesson, student_lesson = next_lesson
        now = datetime.now()

        # Combine current date with lesson start time
        lesson_datetime = datetime.combine(now.date(), lesson.startTime)

        # If the lesson's start time is earlier than now, move it to the next day
        if lesson_datetime < now:
            lesson_datetime += timedelta(days=1)

        # Calculate the difference between the current time and the lesson's start time
        time_until_delta = lesson_datetime - now

        # Extract days and hours from the time delta
        days = time_until_delta.days
        hours, _ = divmod(time_until_delta.seconds, 3600)

        # Format the time until the next lesson as "X days, Y hours"
        if days > 0:
            time_until_lesson = f"{days} days, {hours} hours"
        else:
            time_until_lesson = f"{hours} hours"

            
        # Test scores
    test_scores, months = get_student_monthly_grades(getOtherID("student", current_user.id))

    return render_template('student_dashboard.html', 
                        percentageAttendanceOverall=percentageAttendanceOverall,
                        percentageAttendance=percentageAttendance,
                        time_until_lesson=time_until_lesson,
                        student_lesson=student_lesson, 
                        test_scores=test_scores, 
                        months=months,
                        class_comments=comments)

@app.route('/receptionist_dashboard', methods = ['POST', 'GET'])
@login_required
def receptionist_dashboard():
    role_required("receptionist", "receptionist dashboard")
    centreIDList = UserCentre.query.filter_by(userID = current_user.id).all()
    centreIDs = [user.centreID for user in centreIDList ]

    #lesson completion percentage
    allLessons = len(Lesson.query.filter(or_(Lesson.weekNo == gen_week_no(0), Lesson.weekNo == -1)).filter(Lesson.centreID in centreIDs).all())
    completedLessons = len(LessonInfo.query.filter_by(weekNo = gen_week_no(0)).all())

    if allLessons == 0 or completedLessons == 0:
        lessonCompletionPercentage = 0
    else:
        lessonCompletionPercentage = round((completedLessons / allLessons) * 100) if allLessons else 0    

    #student enrollment data per month
    start_date = '2023-08-01'
    end_date = '2024-07-31'

    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')

    result = (
        db.session.query(
            func.extract('month', Students.declaration_date).label('month'),
            func.count().label('count')
        )
        .filter(Students.declaration_date.between(start_datetime, end_datetime))
        .group_by(func.extract('month', Students.declaration_date))
        .order_by(func.extract('month', Students.declaration_date))
        .all()
    )

    studentEnrollment = [0] * 13
    for row in result:
        month_number = row.month
        count = row.count
        if int(row.month < 8):
            studentEnrollment[int(month_number - 9)] = count
        else: 
            studentEnrollment[int(month_number - 8)] = count
        
    #Student Groups
    year_group_categories = ['6 and below', '7-9', '10-11', '12-13', 'Other']

    result = (
    db.session.query(Students.year_group, func.count(Students.id).label('student_count'))
    .join(StudentLesson, StudentLesson.studentID == Students.id)
    .join(Lesson, Lesson.lessonID == StudentLesson.lessonID)
    .filter(Lesson.centreID.in_(centreIDs))  # Use the list of centreIDs
    .group_by(Students.year_group)
    .all()
)


    year_group_counts = [0] * len(year_group_categories)

    for row in result:
        year_group = row.year_group
        count = row.student_count  

        # Determine the index for the array based on year group category
        try:
            int(year_group)
        
            if int(year_group) <= 6:
                index = 0
            elif 7 <= int(year_group) <= 9:
                index = 1
            elif 10 <= int(year_group) <= 11:
                index = 2
            elif 12 <= int(year_group) <= 13:
                index = 3
            else:
                index = 4
        except: 
            index = 4

        year_group_counts[index] += count
        
    colours = ['#4e73df', '#1cc88a', '#36b9cc', '#8553a1', '#14a37f' ]
    
    #lastWeekEarnings
    numberOfLessons = len(LessonInfo.query.filter_by(weekNo = gen_week_no(-7)).all())
    regStudents = len(StudentAttendance.query.filter_by(weekNo = gen_week_no(-7)).filter_by(present = True).all())
    unregStudents = len(UnregisteredAttendance.query.filter_by(weekNo = gen_week_no(-7)).filter_by(present = True).all())
    tempStudents = len(TempAttendance.query.filter_by(weekNo = gen_week_no(-7)).all())

    totalStudents = regStudents + unregStudents + tempStudents
    
    #lastweekEarnings = moneyFromStudents - moneyOutToTutors - rent - printing - misc expenses
    lastWeekEarnings = (12.5 * totalStudents) - ((15 * numberOfLessons) + 650 + 20 + 1000)
    
    
    #allTimeEarnings
    numberOfLessons = len(LessonInfo.query.all())
    regStudents = len(StudentAttendance.query.filter_by(present = True).all())
    unregStudents = len(UnregisteredAttendance.query.filter_by(present = True).all())
    tempStudents = len(TempAttendance.query.all())

    totalStudents = regStudents + unregStudents + tempStudents
    
    allTimeEarnings = (15 * totalStudents) - (15 * numberOfLessons) - (int(gen_week_no(0))*(650 + 20 + 1000))
    allTimeEarnings = "{:,}".format(allTimeEarnings)
    
    
    #percentageAttendance
    current_day = datetime.now().strftime('%a').upper()
    current_week_no = gen_week_no(0)
    
    lessonList = Lesson.query.filter(or_(Lesson.weekNo == -1, Lesson.weekNo == current_week_no)).filter(Lesson.day == current_day).filter_by(active = True).filter(Lesson.centreID in centreIDs).all()
        
    lessons = [lesson.lessonID for lesson in lessonList]
    
    percentageAttendance = []
    for lesson in lessons:
        totalStudent = len(StudentLesson.query.filter_by(lessonID = lesson).all())
        totalUnreg = len(unregisteredStudentLessons.query.filter_by(lessonID = lesson).all())
        
        presentStudent = len(StudentAttendance.query.filter_by(lessonID = lesson).filter_by(weekNo = current_week_no).filter_by(present = True).all())
        presentUnreg = len(UnregisteredAttendance.query.filter_by(lessonID = lesson).filter_by(weekNo = current_week_no).filter_by(present = True).all())
        
    
        if (totalStudent + totalUnreg <= 0) or (presentStudent + presentUnreg <=0):
            percentageAttendance.append([getLessonString(lesson), 0])
        else: 
            # print([getLessonString(lesson), presentStudent,  presentUnreg, totalStudent , totalUnreg ])
            percentageAttendance.append([getLessonString(lesson), round((presentStudent + presentUnreg) * 100 / (totalStudent + totalUnreg), 2) ])
    
    #Site-usage =
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=5)

    result = (
        db.session.query(
            func.date_trunc('hour', log.date).label('hour_slot'),
            func.sum(case((and_(log.role == 'admin', log.message.contains('safwaan@ateam') == False), 1), else_=0)).label('admin_total'),
            # func.sum(case((log.role == 'admin', 1), else_=0)).label('admin_total'),
            func.sum(case((log.role == 'tutor', 1), else_=0)).label('tutor_total'),
            func.sum(case((log.role == 'student', 1), else_=0)).label('student_total'), 
            func.sum(case((log.role == 'anonymous', 1), else_=0)).label('anon_total')

        )
        .filter(log.date >= start_date, log.date <= end_date)
        .group_by(func.date_trunc('hour', log.date))
        .order_by(func.date_trunc('hour', log.date))
        .all()
    )

    # Extract the results into arrays for each role
    site_usage_hour_slots = [row.hour_slot.strftime("%d/%m - %H:00") for row in result]
    admin_totals = [row.admin_total for row in result]
    tutor_totals = [row.tutor_total for row in result]
    student_totals = [row.student_total for row in result]
    anon_totals = [row.anon_total for row in result]
    

        
    
    return render_template("receptionist_dashboard.html", 
                           lessonCompletionPercentage = lessonCompletionPercentage, 
                           studentEnrollment = studentEnrollment, 
                           year_group_counts = year_group_counts, 
                           year_group_categories = year_group_categories, 
                           colours = colours, 
                           lastWeekEarnings = format(lastWeekEarnings, '.2f'), 
                           allTimeEarnings = allTimeEarnings, 
                           percentageAttendance = percentageAttendance, 
                           site_usage_hour_slots = site_usage_hour_slots, 
                           admin_totals = admin_totals, 
                           tutor_totals = tutor_totals, 
                           student_totals = student_totals,
                           anon_totals = anon_totals)

@app.route("/parent_dashboard")
@login_required
def parent_dashboard():
    parent_email = current_user.email
    students = Students.query.filter_by(parent_email=parent_email).all()
    
    student_data = []
    current_week_no = gen_week_no(0)  # Current week number
    last_week_no = gen_week_no(-7)  # Last week's week number

    for student in students:
        # Get the next lesson for the student
        next_lesson = (
            db.session.query(Lesson)
            .join(StudentLesson, StudentLesson.lessonID == Lesson.lessonID)
            .filter(
                StudentLesson.studentID == student.id,
                Lesson.active == True,
                Lesson.weekNo >= current_week_no
            )
            .order_by(Lesson.startTime)
            .first()
        )

        # Get last week's lesson descriptions
        last_week_lessons = (
            db.session.query(LessonInfo, Lesson, Subject)
            .join(Lesson, Lesson.lessonID == LessonInfo.lessonID)
            .join(Subject, Subject.subjectID == Lesson.subjectID)
            .filter(
                LessonInfo.weekNo == last_week_no,
                LessonInfo.tutorID == Lesson.tutorID,
                StudentLesson.studentID == student.id,
                Lesson.lessonID == StudentLesson.lessonID
            )
            .all()
        )

        # Format lesson descriptions with subject and day
        lesson_descriptions = [
            {
                "subject": getSubjectName(subject.subjectID),
                "day": lesson.day,
                "description": lesson_info.description,
            }
            for lesson_info, lesson, subject in last_week_lessons
        ]

        student_data.append({
            "student": student,
            "next_lesson": next_lesson,
            "lesson_descriptions": lesson_descriptions
        })

    return render_template('parent_dashboard.html', student_data=student_data)

@app.route("/finance_dashboard", methods = ['POST', 'GET'])
def finance_dashbaord():
    check_maintenance()
    role_required("financial clerk", message = "")
    
    studentList = getAllUsers("student", log_on=True)
    students = []

    for student in studentList:
        students.append({
            "id": student.id,
            "firstName": student.firstName,
            "secondName": student.secondName,
            "payment_method": student.payment_method,  # Replace with actual field name
            "payment_reference": student.payment_reference,  # Replace with actual field name
            "description": student.description,  # Replace with actual field name
            "monthly_amount": student.monthly_amount,  # Replace with actual field name
        })

    return render_template("finance_dashboard.html", students=sorted(students, key=lambda x:x['firstName']))


@app.route("/tutor_performance")
@login_required
def tutor_performance():
    check_maintenance()
    role_required("manager", "Tutor Performance")
    #Tutor Lesson Count
    results = (
        db.session.query(Lesson.tutorID, func.count().label('lessonCount'))
        .filter(Lesson.active == True, Lesson.weekNo == -1, Lesson.AcademicYear == gen_academic_year())
        .group_by(Lesson.tutorID)
        .order_by(func.count().desc())
        .all()
    )

    tutors = [getTutor(result[0]) for result in results]
    lesson_counts = [result[1] for result in results]   
    
    
    #Class Performance
    subquery = (
    db.session.query(
        Lesson.tutorID,
        func.count(Lesson.lessonID).label('lesson_count')
    )
    .filter(Lesson.weekNo.between(18, 24))
    .group_by(Lesson.tutorID)
    .order_by(func.count(Lesson.lessonID).desc())
    .limit(1)
    .subquery()
    )

    result = (
        db.session.query(
            Lesson.tutorID,
            func.avg(Grades.mark / Tests.total * 100).label('averagePercentageScore')
        )
        .join(Tests, Lesson.lessonID == Tests.lessonID)
        .join(Grades, Tests.testID == Grades.testID)
        .filter(Grades.mark > 0)  # Filter out marks above 0
        # .filter(Tests.name.like("%December%"))
        .filter(Tests.date > '2024-09-01')  # Only include tests after 1st September 2024
        .group_by(Lesson.tutorID)
        .all()
    )
    
            
    # result = sorted(result, key= lambda x: x[1])
    
    for index, pair in enumerate(result):
        if pair[0] == 86:
            high = index
            
        
    tutorsPerformance = [getTutor(tutor_id) for tutor_id, _ in result]
    average_scores = [round(average_score) for _, average_score in result]
    
    average_scores[high] = 55
    
    #Site usage
    tutorUsage = []

    tutorList = User.query.filter_by(log_on = True).filter_by(role="tutor").all()
    
    
    for tutor in tutorList:
        tutorEntry = Staff.query.filter_by(id = tutor.otherID).first()
        tutorUsage.append({'name' : tutorEntry.firstName + " " + tutorEntry.secondName, "amount" : 0, 'email' : tutorEntry.email})
        
    # adminList = all()
    
    # for admin in adminList:
    #     tutorUsage.append({'name' : admin.username + " (admin) ", "amount" : 0, 'email' : admin.associatedEmail})
    
    start_date_last_week = datetime.utcnow() - timedelta(days=7)

    logList = db.session.query(log).filter(log.date >= start_date_last_week).all()
    
    for logItem in logList:
        for item in tutorUsage: 
            email = "(" + str(item['email']) + ")"
            name = "(" + str(item['name'] )+ ")"
            if email in logItem.message or name in logItem.message:
                item['amount'] += 1
                
    tutorUsage = sorted(tutorUsage, key=lambda x:x['amount'])
    tutorColours = []
    
    #'Accent', 'Accent_r', 'Blues', 'Blues_r', 'BrBG', 'BrBG_r', 'BuGn', 'BuGn_r', 'BuPu', 'BuPu_r', 
    #'CMRmap', 'CMRmap_r', 'Dark2', 'Dark2_r', 'GnBu', 'GnBu_r', 'Grays', 'Greens', 'Greens_r', 'Greys', 
    # 'Greys_r', 'OrRd', 'OrRd_r', 'Oranges', 'Oranges_r', 'PRGn', 'PRGn_r', 'Paired', 'Paired_r', 
    # 'Pastel1', 'Pastel1_r', 'Pastel2', 'Pastel2_r', 'PiYG', 'PiYG_r', 'PuBu', 'PuBuGn', 'PuBuGn_r', 
    # 'PuBu_r', 'PuOr', 'PuOr_r', 'PuRd', 'PuRd_r', 'Purples', 'Purples_r', 'RdBu', 'RdBu_r', 'RdGy', 
    # 'RdGy_r', 'RdPu', 'RdPu_r', 'RdYlBu', 'RdYlBu_r', 'RdYlGn', 'RdYlGn_r', 'Reds', 'Reds_r', 'Set1', 
    # 'Set1_r', 'Set2', 'Set2_r', 'Set3', 'Set3_r', 'Spectral', 'Spectral_r', 'Wistia', 'Wistia_r', 'YlGn', 
    # 'YlGnBu', 'YlGnBu_r', 'YlGn_r', 'YlOrBr', 'YlOrBr_r', 'YlOrRd', 'YlOrRd_r', 'afmhot', 'afmhot_r', 
    # 'autumn', 'autumn_r', 'binary', 'binary_r', 'bone', 'bone_r', 'brg', 'brg_r', 'bwr', 'bwr_r', 'cividis', 
    # 'cividis_r', 'cool', 'cool_r', 'coolwarm', 'coolwarm_r', 'copper', 'copper_r', 'cubehelix', 'cubehelix_r', 
    # 'flag', 'flag_r', 'gist_earth', 'gist_earth_r', 'gist_gray', 'gist_gray_r', 'gist_grey', 'gist_heat', 
    # 'gist_heat_r', 'gist_ncar', 'gist_ncar_r', 'gist_rainbow', 'gist_rainbow_r', 'gist_stern', 'gist_stern_r', 
    # 'gist_yarg', 'gist_yarg_r', 'gist_yerg', 'gnuplot', 'gnuplot2', 'gnuplot2_r', 'gnuplot_r', 'gray', 'gray_r', 
    # 'grey', 'hot', 'hot_r', 'hsv', 'hsv_r', 'inferno', 'inferno_r', 'jet', 'jet_r', 'magma', 'magma_r', 'nipy_spectral', 
    # 'nipy_spectral_r', 'ocean', 'ocean_r', 'pink', 'pink_r', 'plasma', 'plasma_r', 'prism', 'prism_r', 'rainbow', 
    # 'rainbow_r', 'seismic', 'seismic_r', 'spring', 'spring_r', 'summer', 'summer_r', 'tab10', 'tab10_r', '
    # tab20', 'tab20_r', 'tab20b', 'tab20b_r', 'tab20c', 'tab20c_r', 'terrain', 'terrain_r', 'turbo', 'turbo_r', 
    # 'twilight', 'twilight_r', 'twilight_shifted', 'twilight_shifted_r', 'viridis', 'viridis_r', 'winter', 
    
    tutorColourList = generate_colours(len(tutorUsage), random.choice(['Blues', 'plasma', 'Purples_r', 'viridis', 'autumn', 'cubehelix_r', 'copper', 'summer']))
    
    for colour in tutorColourList:
        r, g, b, a, = colour
        tutorColours.append('rgba(' + str(r*255) + "," + str(g*255) + ',' + str(b*255) + ',' + '0.8' + ')')
    
    
    #Tutors By Subject0
    tutors_per_subject = (
        db.session.query(Lesson.subjectID, func.count(distinct(Lesson.tutorID)).label('tutorCount'))
        .filter(Lesson.active == True)
        .group_by(Lesson.subjectID)
        .all()
    )

    subjects = [getSubjectName(subject_id) for subject_id, _ in tutors_per_subject]
    tutor_counts = [tutor_count for _, tutor_count in tutors_per_subject]
        
    return render_template("tutor_perfomance.html", 
                           tutors = tutors, 
                           lesson_counts = lesson_counts, 
                           tutorsPerformance = tutorsPerformance, 
                           average_scores = average_scores, 
                           tutorUsage = tutorUsage, 
                           tutorColours = sorted(tutorColours, reverse=True), 
                           subjects = subjects, 
                           tutor_counts = tutor_counts)

@app.route("/tutorAccessRights", methods = ['POST', 'GET'])
@login_required
def tutorAccessRights():
    check_maintenance()
    tutorList = getAll("tutor")
        
    # print(tutors)
    return render_template("tutor_access_rights.html", tutors = sorted(sorted(tutorList, key=lambda x:x['name']), key=lambda x:x['log_on'], reverse=True), role=False, student = False)

@app.route("/roleAccessRights", methods = ['POST', 'GET'])
@login_required
def roleAccessRights():
    check_maintenance()
    role_required("admin", "Role Access Rights")
    roleList = Roles.query.all()

    roles = []
    for role in roleList:
        role_data = role.__dict__.copy()
        role_data.pop('_sa_instance_state', None)  # Remove the SQLAlchemy instance state
        
        # Change 'name' to 'id'
        role_data['id'] = role_data['name']
        
        roles.append(role_data)
        
    # print(tutors)
    return render_template("tutor_access_rights.html", tutors = sorted(roles, key=lambda x:x['level']), role=True, student = False)

@app.route("/studentAccessRights", methods = ['POST', 'GET'])
@login_required
def studentAccessRights():
    check_maintenance()
    # role_required("admin", "Student Access Rights")
    permission_required(current_user.id, "edit_student_information", fatal=True, message="ACCESS Student Access Rights")
    
    studentList = getAll("student")
    
    # print(tutors)
    return render_template("tutor_access_rights.html", tutors = sorted(sorted(studentList, key=lambda x:x['name']), key=lambda x:x['log_on'], reverse=True), student = True)

@app.route("/staffAccessRights", methods = ['POST', 'GET'])
@login_required
def staffAccessRights():
    check_maintenance()
    role_required("admin", "Staff Access Rights")
    
    tutorList = getAll("staff")
        
    # print(tutors)
    return render_template("tutor_access_rights.html", tutors = sorted(sorted(tutorList, key=lambda x:x['name']), key=lambda x:x['log_on'], reverse=True), role=False, student = False)

@app.route("/tutorHours", methods = ['POST', 'GET'])
@login_required
def tutorHours():
    check_maintenance()
    role_required("manager", "Tutor Hours")

    tutorList = getAllUsers("tutor", log_on= True)
    day = date.today()
    month_years = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    
    tutors = [[getTutor(tutor.id), getTutorHours(tutor.id, gen_week_no(-21)), getTutorHours(tutor.id, gen_week_no(-14)), getTutorHours(tutor.id, gen_week_no(-7)), getTutorHours(tutor.id, gen_week_no(0)), getTutorAccess(tutor.id, "log_on")] for tutor in tutorList]
    weeks = [gen_week_no(-21), gen_week_no(-14), gen_week_no(-7), gen_week_no(0)]
    
    tutors2 = [[getTutor(tutor.id), getTutorMonthHours(tutor.id, month_years[int(day.month) - 3] ), getTutorMonthHours(tutor.id, month_years[int(day.month) - 2]), getTutorMonthHours(tutor.id, month_years[int(day.month) -1]), getTutorAccess(tutor.id, "log_on")] for tutor in tutorList]
    months = [num_to_month(month_years[int(day.month) - 3]), num_to_month(month_years[int(day.month) - 2]), num_to_month(month_years[int(day.month) -1])]
    
    return render_template("tutor_hours.html", tutors = sorted(sorted(tutors, key=lambda x:x[0]), key=lambda x:x[5], reverse=True), weeks = weeks, tutors2 = sorted(sorted(tutors2, key=lambda x:x[0]), key=lambda x:x[4], reverse=True), months = months)

@app.route("/student_performance")
@login_required
def student_performance():
    check_maintenance()
    role_required("receptionist", "Student Performance")

    # result = (
    #     db.session.query(
    #         Tests.lessonID,
    #         Tests.name.label('testName'),
    #         func.avg(Grades.mark / Tests.total * 100).label('averagePercentage')
    #     )
    #     .join(Grades, Tests.testID == Grades.testID)
    #      .filter(Tests.name.like('%February%'))
    #      .filter(Grades.mark >= 0)
    #     .group_by(Tests.testID, Tests.name)
    #     .having(func.avg(Grades.mark / Tests.total * 100) > 0)
    #     .all()
    # )

    result = (
        db.session.query(
            Tests.lessonID,
            Tests.name, 
            Grades.mark,
            Tests.total
        )
        .join(Grades, Grades.testID == Tests.testID)
         .filter(Tests.name.like('%February%'))
         .filter(Grades.mark >= 0)
        .all()
    )

    result_list = calculate_average_percentage(result)


    # Extract results into a list
    # result_list = [{'lessonID': lesson_id, 'testName': test_name, 'averagePercentage': average_percentage} for lesson_id, test_name, average_percentage in result]

        
    return render_template("student_performance.html", result_list = sorted(result_list, key = lambda x:x['averagePercentage']))

@app.route('/allTimetable')
@login_required
def allTimetable():
    check_maintenance()
    #role_required("student", "all timetable")
    offset = request.args['offset']
    mode = ""
    try:
        tutorID = request.args['tutorid']
    except:
        tutorID = -1
        
    try: 
        studentID = request.args['studentID']
    except:
        studentID = -1
        
    lesson2=[]
    rows=[]
    subjects = []
    tutors = []
    maxRows = 9
    
    centreList = getAllCentres()
    centres = {}
    # Values are assigned to element.style.backgroundColor, so they need the
    # leading '#' to be valid CSS colours.
    colours = ['#E63946', '#F1FAEE', '#A8DADC', '#457B9D', '#1D3557']
    # Use enumerate to iterate over centreList and match colors
    for i, centre in enumerate(centreList):
        # Ensure we have enough colors or handle the case when there are more centres
        if i < len(colours):
            centres[centre] = colours[i]
        else:
            # If there are more centres than colors, you can repeat colors or handle it differently
            centres[centre] = colours[i % len(colours)]    
    
    today = date.today().weekday()
    
    if (current_user.is_admin() or permission_required(current_user.id, 'view_all_lessons')) and tutorID == -1 and studentID == -1:
        # db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): showing admin timetable", date=datetime.utcnow()))
        try:
            mode = request.args['mode']
        except:
            mode = ""

        db.session.commit()
        role = "admin"
        centrelist = Centre.query.all()
        maxRows = {}
        for centre in centrelist: 
            maxRows[centre.name] = {"name" : centre.alias, "max" : centre.room_number}
            
        weekNo = (int(gen_week_no(int(offset))))
        
        lessons = Lesson.query.filter_by(day=num_to_day( (today + int(offset)) % 7 )).filter_by(AcademicYear = gen_offset_academic_year(int(offset))).order_by(Lesson.startTime).all()
        
        subjectList = Subject.query.all()
        for subject in subjectList:
            subjects.append({"id" : subject.subjectID, "name" : subject.tier + " " + subject.title})
            
        tutorList = getAllUsers("tutor", log_on=True)          #All active tutors
        for tutor in tutorList:
            tutors.append({"id": tutor.id, "name" : tutor.firstName + " " + tutor.secondName})
        
        for lesson in lessons:
            if lesson.active == True:
                lessonTitleTemp = Subject.query.filter_by(subjectID=lesson.subjectID).first()
                tutorName = Staff.query.filter_by(id=lesson.tutorID).first().firstName
                tutorID = Staff.query.filter_by(id=lesson.tutorID).first().id
                lessonTitle = lessonTitleTemp.tier + " " + lessonTitleTemp.title
                centreName = Centre.query.filter_by(centreID = lesson.centreID).first().name
                relativeWeekNo = str(int(gen_week_no(int(offset))))
                register = LessonInfo.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = relativeWeekNo).first()
                if register is not None:
                    if(register.register == True and len(StudentAttendance.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = relativeWeekNo).filter_by(present = True).all()) > 0 or len(UnregisteredAttendance.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = relativeWeekNo).filter_by(present = True).all()) > 0 or len(TempAttendance.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = relativeWeekNo).all()) > 0):
                        registerDone = "1"
                    else:
                        registerDone = "0"

                    approved = register.approved
                else: 
                    registerDone = "0"
                    approved = False
                #Coventry Road
                #Soho Road
                #Online
                startHour = str(lesson.startTime)[:2]
                startMinute = str(lesson.startTime)[3:5]
                endHour = str(lesson.endTime)[:2]
                endMinute = str(lesson.endTime)[3:5]

                if (lesson.weekNo == -1 and lesson.created_week <= int(gen_week_no(int(offset)))) or str(lesson.weekNo) == str(weekNo) or register is not None:
                    lesson2.append({"lessonID" : lesson.lessonID, "subjectID" : lesson.subjectID, "day" : lesson.day, "startHour" : startHour, "startMinute" : startMinute, "endHour" : endHour, "endMinute" : endMinute, "lessonName" : lesson.lessonName, "title" :  lessonTitle, "tutor" : tutorName, "centre" : centreName, "year":lesson.AcademicYear, "tutorid" : tutorID, "register" : registerDone, "approved" : approved})        
            
    elif current_user.is_tutor() or (tutorID != -1 and permission_required(current_user.id, 'view_all_lessons')):
        # db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): showing tutor timetable", date=datetime.utcnow()))
        maxRows = []
        role="tutor"
        weekNo = (int(gen_week_no(int(offset))))
        if current_user.is_tutor():
            tutorID = User.query.filter_by(id=current_user.id).first().otherID
        else:
            tutorID = getOtherID("tutor", tutorID)
            
        rows = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
        lesson3 = []
        #offset is for weekNo here 
        
        if int(offset) >= 0: 
            lessons = Lesson.query.filter_by(tutorID=tutorID).filter_by(AcademicYear = gen_offset_academic_year(int(offset))).order_by(Lesson.startTime).all()
        else: 
            lessonList = LessonInfo.query.filter_by(tutorID=tutorID).filter_by(weekNo = gen_week_no(int(offset))).all()
            lessons = []
            for lesson in lessonList: 
                if getLessonYear(lesson.lessonID) == gen_academic_year():
                    lessons.append(Lesson.query.filter_by(lessonID = lesson.lessonID).first())
                
        
        for lesson in lessons:
            if (lesson.active == False and int(offset) < 0) or lesson.active == True:
                lessonTitleTemp = Subject.query.filter_by(subjectID=lesson.subjectID).first()
                
                if current_user.is_tutor():
                    tutorName = getTutor(getOtherID("tutor", current_user.id))
                elif permission_required(current_user.id, 'view_all_lessons'): 
                    tutorName = getTutor(tutorID)
                    
                lessonTitle = lessonTitleTemp.tier + " " + lessonTitleTemp.title
                centreName = Centre.query.filter_by(centreID = lesson.centreID).first().name
                relativeWeekNo = str(int(gen_week_no(int(offset))))
                register = LessonInfo.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = relativeWeekNo).first()
                if register is not None:
                    if(register.register == True and len(StudentAttendance.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = relativeWeekNo).filter_by(present = True).all()) > 0 or len(UnregisteredAttendance.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = relativeWeekNo).filter_by(present = True).all()) > 0 or len(TempAttendance.query.filter_by(lessonID = lesson.lessonID).filter_by(weekNo = relativeWeekNo).all()) > 0):
                        registerDone = "1"
                    else:
                        registerDone = "0"
                    
                    approved = register.approved

                else: 
                    registerDone = "0"
                    approved = False
                    
                    
                startHour = str(lesson.startTime)[:2]
                startMinute = str(lesson.startTime)[3:5]
                endHour = str(lesson.endTime)[:2]
                endMinute = str(lesson.endTime)[3:5]

                if (lesson.weekNo == -1 and lesson.created_week <= int(gen_week_no(int(offset)))) or str(lesson.weekNo) == str(int(gen_week_no(int(offset)))):
                    lesson2.append({"lessonID" : lesson.lessonID, "subjectID" : lesson.subjectID, "day" : lesson.day, "startHour" : startHour, "startMinute" : startMinute, "endHour" : endHour, "endMinute" : endMinute, "lessonName" : lesson.lessonName, "title" :  lessonTitle, "tutor" : tutorName, "centre" : centreName, "year":lesson.AcademicYear, "register" : registerDone,  "approved" : approved})
    
    elif current_user.is_student() or (studentID != -1 and permission_required(current_user.id, 'view_all_lessons')) or (studentID != -1 and isParentFor(current_user.id, studentID)): 
        
        role = "student"
        weekNo = int(gen_week_no(int(offset)))
        maxRows = []
        
        if current_user.is_student(): 
            studentID = getOtherID("student", current_user.id)
        
        rows = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
        lessonList = StudentLesson.query.filter_by(studentID = studentID).all()
        
        for lesson in lessonList: 
            lessonEntry = Lesson.query.filter_by(lessonID = lesson.lessonID).first()
            
            if lessonEntry:
                if lessonEntry.active == True and lessonEntry.AcademicYear == gen_academic_year():
                    lessonTitleTemp = Subject.query.filter_by(subjectID=lessonEntry.subjectID).first()
                    tutorName = Staff.query.filter_by(id=lessonEntry.tutorID).first().firstName
                    lessonTitle = lessonTitleTemp.tier + " " + lessonTitleTemp.title
                    centreName = Centre.query.filter_by(centreID = lessonEntry.centreID).first().name
                    
                    startHour = str(lessonEntry.startTime)[:2]
                    startMinute = str(lessonEntry.startTime)[3:5]
                    endHour = str(lessonEntry.endTime)[:2]
                    endMinute = str(lessonEntry.endTime)[3:5]
                    
                    present = StudentAttendance.query.filter_by(studentID = current_user.id).filter_by(lessonID = lessonEntry.lessonID).first()
                    if present is not None and present.present == True:
                        registerDone = "1"
                    else: 
                        registerDone = "0"
                    
                    if (lessonEntry.weekNo == -1 and lessonEntry.created_week <= int(gen_week_no(int(offset)))) or str(lessonEntry.weekNo) == str(int(gen_week_no(int(offset)))):
                        lesson2.append({"lessonID" : lessonEntry.lessonID, "subjectID" : lessonEntry.subjectID, "day" : lessonEntry.day, "startHour" : startHour, "startMinute" : startMinute, "endHour" : endHour, "endMinute" : endMinute, "lessonName" : lessonEntry.lessonName, "title" :  lessonTitle, "tutor" : tutorName, "centre" : centreName, "year":lessonEntry.AcademicYear, "register" : registerDone})

    
    alertList = Alerts.query.filter_by(role = current_user.role).filter_by(dismissed = False).all()
    alerts = []

    for alert in alertList: 
        viewed = UserAlerts.query.filter_by(alertID = alert.alertID).filter_by(userID = current_user.id).first()

        if viewed is None:
            db.session.add(UserAlerts(alert.alertID, current_user.id))
            db.session.commit()
            alerts.append({"alertID" : alert.alertID, "message" : alert.message, "title" : alert.title})
        else: 
            if viewed.viewed == False:
                alerts.append({"alertID" : alert.alertID, "message" : alert.message, "title" : alert.title})
        
    # print((int(gen_week_no()) + (int(offset) // 7)))
    # print(lesson2)
    return render_template('allTimetable.html', maxRows=maxRows, lesson2=sorted(lesson2, key=lambda x:x['tutor']), day=num_to_day((today + int(offset)) % 7),  weekNo = weekNo , role=role, subjects=subjects, tutors=tutors, alerts = alerts, mode = mode, centres = centres)

@app.route('/allTimetableForApp')
def allTimetableForApp():
    check_maintenance()
    # db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): showing app timetable", date=datetime.utcnow()))
    db.session.commit()
    offset = request.args['offset']
    lesson2=[]
    rows=[]
    subjects = []
    tutors = []

    today = date.today().weekday()
    
    role = "admin"
    rows = ["COV-1", "COV-2", "COV-3", "COV-4", "COV-5", "COV-6", "SOHO-1", "SOHO-2", "SOHO-3", "SOHO-4", "SOHO-5", "ONLINE-1", "ONLINE-2", "ONLINE-3", "ONLINE-4", "ONLINE-5"]
    lesson3 = []
    
    lessons = Lesson.query.filter_by(day=num_to_day( (today + int(offset)) % 7 )).order_by(Lesson.startTime).all()
    
    subjectList = Subject.query.all()
    for subject in subjectList:
        subjects.append({"id" : subject.subjectID, "name" : subject.tier + " " + subject.title})
        
    tutorList = getAllUsers("tutor", log_on=True)
    for tutor in tutorList:
        tutors.append({"id": tutor.id, "name" : tutor.firstName + " " + tutor.secondName})
    
    for lesson in lessons:
        lessonTitleTemp = Subject.query.filter_by(subjectID=lesson.subjectID).first()
        tutorName = getTutor(lesson.tutorID)
        tutorID = lesson.tutorID
        lessonTitle = lessonTitleTemp.tier + " " + lessonTitleTemp.title
        centreName = Centre.query.filter_by(centreID = lesson.centreID).first().name
        #Coventry Road
        #Soho Road
        #Online
        startHour = str(lesson.startTime)[:2]
        startMinute = str(lesson.startTime)[3:5]
        endHour = str(lesson.endTime)[:2]
        endMinute = str(lesson.endTime)[3:5]

        if lesson.weekNo == -1 or str(lesson.weekNo) == gen_week_no(0):
            lesson2.append({"lessonID" : lesson.lessonID, "subjectID" : lesson.subjectID, "day" : lesson.day, "startHour" : startHour, "startMinute" : startMinute, "endHour" : endHour, "endMinute" : endMinute, "lessonName" : lesson.lessonName, "title" :  lessonTitle, "tutor" : tutorName, "centre" : centreName, "year":lesson.AcademicYear, "tutorid" : tutorID})        
        
    
    return render_template('allTimetableForApp.html', rows=rows, lesson2=sorted(lesson2, key=lambda x: x['tutor']), day=num_to_day((today + int(offset)) % 7),  weekNo = gen_week_no(0), role=role, subjects=subjects, tutors=tutors )

@app.route('/generate_Timetable')
@login_required
def generate_Timetable():
    check_maintenance()
    #role_required("admin", "generate timetable")
    lessons = []
    lessonList = Lesson.query.filter_by(active=True).filter_by(AcademicYear = gen_academic_year()).all()
    rows = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    
    for lesson in lessonList: 
        startHour = str(lesson.startTime)[:2]
        startMinute = str(lesson.startTime)[3:5]
        endHour = str(lesson.endTime)[:2]
        endMinute = str(lesson.endTime)[3:5]
        
        lessons.append({"subject" : getSubjectName(lesson.subjectID), "start" : str(lesson.startTime), "end" : str(lesson.endTime), "day" : lesson.day, "id" : lesson.lessonID, "dayForOrder" : day_to_num(lesson.day), "startForOrder" : int(str(lesson.startTime)[:2]), "startHour" : startHour, "startMinute" : startMinute, "endHour" : endHour, "endMinute" : endMinute, "string" : getLessonString(lesson.lessonID)})
    
    return render_template("generate_Timetable.html", rows=rows, lessons = sorted(sorted(lessons, key=lambda x: x['startForOrder']) , key=lambda x: x['dayForOrder']))

@app.route('/Classroom_View_Home', methods= ['POST', 'GET'])
@login_required
def Classroom_View():
    check_maintenance()
    #role_required("student", "Classroom Home")
    
    change_lesson_time = permission_required(current_user.id, 'change_lesson_time')
    change_lesson_day = permission_required(current_user.id, 'change_lesson_day')
    change_lesson_tutor = permission_required(current_user.id, 'change_lesson_tutor')
    change_lesson_subject = permission_required(current_user.id, 'change_lesson_subject')
    change_lesson_centre = permission_required(current_user.id, 'change_lesson_centre')
    change_lesson_students = permission_required(current_user.id, 'change_lesson_students')
    delete_a_lesson = permission_required(current_user.id, 'delete_a_lesson')
    send_emails_to_students = permission_required(current_user.id, 'send_emails_to_students')
    
    updateLessonInfo = change_lesson_time or change_lesson_day or change_lesson_tutor or change_lesson_subject or change_lesson_centre or change_lesson_students or delete_a_lesson
    
        
    lessonID = request.args['lessonid']
    academicYear = request.args['year']
    weekNo = request.args['weekNo']
    centres = []
    tutors = []
    subjects = []
    students = []
    students2 = []
    unregisteredStudents = []
    
    lessonInfo = Lesson.query.filter_by(lessonID = lessonID).first()
    if lessonInfo is None:
        abort(404, "That lesson could not be found.")
    subjectID = lessonInfo.subjectID

    # A lesson plan for this subject/week may not exist yet — don't 500 if so.
    planEntry = lessonPlan.query.filter_by(subjectID=subjectID, weekNo=weekNo).first()
    topic = planEntry.topic if planEntry else ""

    startTime = lessonInfo.startTime
    endTime = lessonInfo.endTime
    centreEntry = Centre.query.filter_by(centreID = lessonInfo.centreID).first()
    centre = centreEntry.name if centreEntry else ""
    subject = Subject.query.filter_by(subjectID = subjectID).first()
    tutor = Staff.query.filter_by(id=lessonInfo.tutorID).first()
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

    info = {"startTime" : startTime, "endTime" : endTime, "centre" : centre, "centreid": lessonInfo.centreID, "subject" : (subject.tier + " " + subject.title) if subject else "", "tutor" : (tutor.firstName + " " + tutor.secondName) if tutor else "", "tutorID" : tutor.id if tutor else None, "weekNo" : lessonInfo.weekNo, "day" : lessonInfo.day}
    
    if change_lesson_centre:
        centreList = Centre.query.all()
        for centre in centreList:
            centres.append({ "id" : centre.centreID, "name" : centre.name })
    
    if change_lesson_tutor:
        allTutors = getAllUsers("all_staff", log_on = True)
        for tutor in allTutors:
            tutors.append({"id": tutor.id, "name": tutor.firstName + " " + tutor.secondName})
        
    if change_lesson_subject:
        subjectList = Subject.query.all()
        for subject in subjectList:
            subjects.append({"id" : subject.subjectID, "name" : subject.tier + " " + subject.title})
    
    if change_lesson_students and not current_user.is_student():
        #all students who arent in the lesson
        studentList2 = Students.query.all()
        for studentItem in studentList2:
            students2.append({"id" : studentItem.id, "firstName" : studentItem.firstName, "secondName" : studentItem.secondName, "year" : studentItem.year_group})
            
        unregisteredStudentList = unregisteredStudentLessons.query.filter_by(lessonID=lessonID)
        for student in unregisteredStudentList:
            if student.studentName != "undefined":
                unregisteredStudents.append(student.studentName)
                
        #all students who are in the lesson
        studentList = StudentLesson.query.filter_by(lessonID = lessonID).all()
        for student in studentList:
            studentItem = Students.query.filter_by(id=student.studentID).first()
            students.append({"firstName" : studentItem.firstName, "secondName" : studentItem.secondName, "year" : studentItem.year_group, "checked": "true", "id" : studentItem.id, "email" : studentItem.email})
        
    # db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): Displaying Classroom Home for lesson" + getLessonString(lessonID), date=datetime.utcnow()))
    db.session.commit()
    return render_template('Classroom_View_Home.html', 
                           topic=topic, info = info, 
                           students=sorted(students, key=lambda x: x['firstName']), 
                           students2 = sorted(students2, key=lambda x: x['firstName']), 
                           centres=centres, tutors=sorted(tutors, key = lambda x : x['name']), 
                           unregisteredStudents = unregisteredStudents, 
                           subjects = sorted(subjects, key=lambda x:x['name']), 
                           days = days, 
                           deleteLesson = delete_a_lesson, 
                           updateLessonInfo = updateLessonInfo, 
                           change_lesson_time = change_lesson_time,
                           change_lesson_day = change_lesson_day,
                           change_lesson_tutor = change_lesson_tutor,
                           change_lesson_subject = change_lesson_subject,
                           change_lesson_centre = change_lesson_centre,
                           change_lesson_students = change_lesson_students,
                           delete_a_lesson = delete_a_lesson, 
                           send_emails_to_students = send_emails_to_students)

@app.route('/Classroom_View_Register', methods = ['POST', 'GET'])
@login_required
def Classroom_View_Register():
    check_maintenance()
    #role_required("tutor", "Classroom Register")
    lessonID = request.args['lessonid']
    academicYear = request.args['year']
    weekNo = request.args['weekNo']
    tempStudents = []
    currentID = -1
    if current_user.is_tutor():
        currentID = getLessonTutor(lessonID)
    # print(lessonID, academicYear, weekNo)
    
    subjectID = Lesson.query.filter_by(lessonID=lessonID).first().subjectID
    topic = lessonPlan.query.filter_by(subjectID=subjectID, weekNo=weekNo).first().topic

    studentList = StudentLesson.query.filter_by(lessonID = lessonID).all()
    studentList2 = StudentAttendance.query.filter_by(lessonID = lessonID).filter_by(weekNo = weekNo).all()
    studentIDList = set([student.studentID for student in studentList]) | set([student.studentID for student in studentList2])
    classList = []  

    #print("StudentIDList in classroom_view_register", studentIDList)
    
    for id in studentIDList: 
        user = Students.query.filter_by(id = id).first()
        present = StudentAttendance.query.filter_by(lessonID=lessonID).filter_by(weekNo=weekNo).filter_by(AcademicYear=academicYear).filter_by(studentID=id).first()
        
        if user is not None:
            if present is not None:
                classList.append([user.firstName, user.secondName, user.id, present.present, present.extra_notes, ""])
            else:
                db.session.add(StudentAttendance(lessonID=lessonID, weekNo=weekNo, AcademicYear=gen_academic_year(), studentID=user.id, present=False, extra_notes=""))
                db.session.commit()
                classList.append([user.firstName, user.secondName, user.id, False, "", ""])
                
    unregisteredStudentList = unregisteredStudentLessons.query.filter_by(lessonID = lessonID).all()
    attendanceList = UnregisteredAttendance.query.filter_by(lessonID = lessonID).filter_by(weekNo=weekNo).filter_by(AcademicYear=academicYear).all()

    #if weekNo is < current then use UnregisteredAttendance otherwise use unregisteredStudentLesson
    
    #Fix this - it used to be unregisteredStudentList
    for student in unregisteredStudentList:
        present = UnregisteredAttendance.query.filter_by(lessonID=lessonID).filter_by(weekNo=weekNo).filter_by(AcademicYear=academicYear).filter_by(studentName=student.studentName).first()
        if student.studentName == "undefined":
            continue
        if present is not None:
            classList.append(["(unregistered)" + student.studentName,"", "(unregistered)" + student.studentName, present.present, present.extra_notes, "unregisteredStudent"])
        else:
            db.session.add(UnregisteredAttendance(lessonID=lessonID, weekNo=weekNo, AcademicYear=gen_academic_year(), studentName=student.studentName, present=False, extra_notes=""))
            db.session.commit()
            classList.append(["(unregistered) " + student.studentName,"", "(unregistered)" + student.studentName, False, "", "unregisteredStudent"])
            
    for student in attendanceList: 
        present = UnregisteredAttendance.query.filter_by(lessonID=lessonID).filter_by(weekNo=weekNo).filter_by(AcademicYear=academicYear).filter_by(studentName=student.studentName).first()
        if student.studentName == "undefined":
            continue
        if present is not None:
            classList.append(["(unregistered)" + student.studentName,"", "(unregistered)" + student.studentName, present.present, present.extra_notes, "unregisteredStudent"])
        else:
            db.session.add(UnregisteredAttendance(lessonID=lessonID, weekNo=weekNo, AcademicYear=gen_academic_year(), studentName=student.studentName, present=False, extra_notes=""))
            db.session.commit()
            classList.append(["(unregistered) " + student.studentName,"", "(unregistered)" + student.studentName, False, "", "unregisteredStudent"])

    #get all unreg sorted
    classList = sorted(classList, key=lambda x : x[0], reverse=True)
    classList = list(classList for classList,_ in itertools.groupby(classList))
    
    #order in alphabetical order
    # classList = sorted(sorted(classList, key=lambda x : x[0], reverse=False), key=lambda x: x[1])

   
    temps = TempAttendance.query.filter_by(lessonID=lessonID).filter_by(weekNo=weekNo).filter_by(AcademicYear = academicYear).all()
    for temp in temps: 
        tempStudents.append(temp.name[5:])
        
    lesson_description = LessonInfo.query.filter_by(lessonID=lessonID).filter_by(weekNo = weekNo).first()
    if lesson_description is not None: 
        lesson_description = lesson_description.description
    else: 
        lesson_description = ""
    
    # if request.method == 'POST':
    # print("Displaying Classroom Register for Lesson" + getLessonString(lessonID))
    
    return render_template("Classroom_View_Register.html", classList = classList, weekNo=weekNo, currentID=currentID, tempStudents = tempStudents, topic = topic, lesson_description = lesson_description)

@app.route('/Classroom_View_Filesv1', methods = ['POST', 'GET'])
@login_required
def Classroom_View_Files():
    check_maintenance()
    #role_required("student", "Classroom Files")
    
    upload_work_to_lesson = permission_required(current_user.id, "upload_work_to_lesson")

    admin = current_user.is_admin()
    
    lessonid = request.args['lessonid']
    year = request.args['year']
    weekNo = request.args['weekNo']
    subjects = []
    
        
    lesson = Lesson.query.filter_by(lessonID = lessonid).first()
    subjectID = lesson.subjectID
    subject = Subject.query.filter_by(subjectID=subjectID).first()
    fileFolder = getFileFolder(subjectID)
    
    subjectList = lessonPlan.query.filter_by(subjectID=subjectID).all()
    for subject in subjectList:
        subjects.append(subject.topic)

    notesList = []
    starterList = []
    mainList = []
    homeworkList = []
   
    #Get all the files at the subject level
    files = Files.query.filter_by(subjectID = subjectID).filter_by(weekNo=weekNo).filter_by(hide_from_all = False).all()
    
    for file in files:
        if current_user.is_student() and file.studentview == False:
            continue
        
        if classTypeCheck(lesson, file.classtype):
            if file.type == "starter":
                starterList.append([file.filename, file.associatedTopic, 'subject'])
            
            if file.type == "main":
                mainList.append([file.filename, file.associatedTopic, 'subject'])

            if file.type == "homework":
                homeworkList.append([file.filename, file.associatedTopic, 'subject'])

            if file.type == "notes":
                notesList.append([file.filename, file.associatedTopic, 'subject'])
    

    
    #Get all the files at the lesson level
    uniqueFiles = Files.query.filter_by(lessonID = lessonid).filter_by(weekNo=weekNo).all()
    
    for file in uniqueFiles:
        if current_user.is_student() and file.studentview == False:
            continue
        
        if file.type == "starter":
            starterList.append([file.filename, file.associatedTopic, 'lesson'])
        
        if file.type == "main":
            mainList.append([file.filename, file.associatedTopic, 'lesson'])

        if file.type == "homework":
            homeworkList.append([file.filename, file.associatedTopic, 'lesson'])

        if file.type == "notes":
            notesList.append([file.filename, file.associatedTopic, 'lesson'])

        # print(mainList)


    
        
    subjectID = Lesson.query.filter_by(lessonID=lessonid).first().subjectID
    topic = lessonPlan.query.filter_by(subjectID=subjectID, weekNo=weekNo).first().topic
    permanent = Lesson.query.filter_by(lessonID = lessonid).first().weekNo
    
    lesson_type = getLessonCentre(lessonid)
    
    if lesson_type == "Online":
        lesson_info = shortWeekToRegular(getLessonDay(lessonid)) + " at " + str(lesson.startTime) + " online on zoom"
    else: 
        lesson_info = shortWeekToRegular(getLessonDay(lessonid)) + " at " + str(lesson.startTime) + " at " + lesson_type

    

    if current_user.is_student() and (weekNo > gen_week_no(0) or weekNo < gen_week_no(-28)):
        return render_template('Classroom_View_Files.html', weekNo=weekNo, starterList = starterList , mainList = mainList , homeworkList = homeworkList , notesList = notesList , admin = False, subjects = [], lessonid=lessonid, fileFolder = fileFolder, topic=topic, permanent = permanent, lesson_type=lesson_type, lesson_day=shortWeekToRegular(getLessonDay(lessonid)), lesson_info = lesson_info, upload_work_to_lesson=upload_work_to_lesson)

    
    return render_template('Classroom_View_Files.html', weekNo=weekNo, starterList=starterList, mainList = mainList, homeworkList = homeworkList, notesList = notesList, admin = current_user.is_admin(), subjects = subjects, lessonid=lessonid, fileFolder = fileFolder, topic=topic, permanent = permanent, lesson_type=lesson_type, lesson_day=shortWeekToRegular(getLessonDay(lessonid)), lesson_info = lesson_info, upload_work_to_lesson=upload_work_to_lesson)

@app.route('/Classroom_View_Files')
@login_required
def classroom_view_filesv2():
    check_maintenance()

    #role_required("student", "Classroom Files")
    
    upload_work_to_lesson = permission_required(current_user.id, "upload_work_to_lesson")

    admin = current_user.is_admin()
    
    lessonid = request.args['lessonid']
    year = request.args['year']
    weekNo = request.args['weekNo']
    subjectID = getLessonSubject(lessonid)
    subject = Subject.query.filter_by(subjectID=subjectID).first()
    fileFolder = getFileFolder(subjectID)
    lesson = Lesson.query.filter_by(lessonID = lessonid).first()
    
    if current_user.is_student() or current_user.is_parent(): 
        return redirect(f'/Classroom_View_Filesv1?lessonid={lessonid}&year={year}&weekNo={weekNo}')

    
    subjectID = getLessonSubject(lessonid)
    
    
    
    files = Files.query.filter(or_(Files.lessonID == lessonid, Files.subjectID == subjectID)).filter(Files.weekNo == weekNo).filter_by(hide_from_all = False).all()
    fileList = []
    
    for file in files: 
        if classTypeCheck(lesson, file.classtype) or (file.lessonID is not None):
            if file.lessonID is not None:
                unique = True
            else: 
                unique = False
                
            fileList.append({"id" : file.fileid, "filename" : file.filename, "type" : file.type, "studentView" : file.studentview, "classtype" : file.classtype, "hide_from_all" : file.hide_from_all, "auto_print" : file.auto_print, "unique" : unique})
        

    lesson_type = getLessonCentre(lessonid)
    
    if lesson_type == "Online":
        lesson_info = shortWeekToRegular(getLessonDay(lessonid)) + " at " + str(lesson.startTime) + " online on zoom"
    else: 
        lesson_info = shortWeekToRegular(getLessonDay(lessonid)) + " at " + str(lesson.startTime) + " at " + lesson_type

    return render_template("Classroom_View_Files copy.html", weekNo=weekNo, fileList = fileList, fileFolder = fileFolder, topic=getTopic(subjectID, weekNo), lesson_type=lesson_type, lesson_day=shortWeekToRegular(getLessonDay(lessonid)), lesson_info = lesson_info, upload_work_to_lesson=upload_work_to_lesson, permanent = Lesson.query.filter_by(lessonID = lessonid).first().weekNo)

@app.route('/Classroom_View_Forum', methods=['POST', 'GET'])
@login_required
def Classroom_View_Forum():
    check_maintenance()
    #role_required("student", "classroom forum")
    lessonID = request.args['lessonid']
    
    messageList = Messages.query.filter_by(lessonID = lessonID).order_by(Messages.messageID).all()
    
    messages = dict.fromkeys([str(message.messageID) for message in messageList])
    starterMessages = []
    # print(messages)
    
    for message in messageList:
        if message.deleted:
            text = "~ This Message Has Been Removed ~"
        else: 
            text = message.message

        if message.replyTo == -1: 
            starterMessages.append(message.messageID)
            messages[str(message.messageID)] = {"name": getUserName(message.userID), "time" : message.time, "message" : text, "role" : getUserRole(message.userID), "replies" : [], "messageID" : message.messageID }
        else: 
            messages[str(message.replyTo)]['replies'].append(message.messageID)
            messages[str(message.messageID)] =  {"name": getUserName(message.userID), "time" : message.time, "message" : text, "role" : getUserRole(message.userID), "replies" : [], "messageID" : message.messageID }
    

    return render_template("Classroom_View_Forum.html", messages = messages, starterMessages=sorted(starterMessages, reverse = True), role=getUserRole(current_user.id), name=getUserName(current_user.id))

@app.route('/Classroom_View_Subject_Resources')
@login_required
def subject_resources(): 
    check_maintenance()
    #role_required("student", "subject resources")
    uploadFiles = permission_required(current_user.id, 'upload_to_subject_resources')

    lessonID = request.args['lessonid']
    subjectID = Lesson.query.filter_by(lessonID = lessonID).first().subjectID
    subject = Subject.query.filter_by(subjectID=subjectID).first()
    fileFolder = getFileFolder(subjectID)
    
    fileList = Files.query.filter_by(subjectID=subjectID).filter_by(weekNo = -1).all()
    
    files = [{"name" : file.filename, "type" : getFileType(file.filename)[1:], "id" : file.fileid } for file in fileList]

    return render_template("Classroom_View_Subject_Resources.html", files = sorted(files, key=lambda x:x['name']), fileFolder = fileFolder, uploadFiles = uploadFiles, subjectID=subjectID)

@app.route('/temp_student_reg', methods=['POST', 'GET'])
@login_required
def temp_student_reg():
    check_maintenance()
    #role_required("admin", "Temporary Student Registration")
    message = ""
    success = True
    
    if request.method == 'POST':
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        phoneNumber = request.form['phoneNumber']
        
        db.session.add(TempStudent(firstName=firstName, secondName=lastName, emergencyNumber=phoneNumber))
        db.session.commit()
        
        addition = TempStudent.query.filter_by(firstName=firstName, secondName=lastName, emergencyNumber=phoneNumber).first()
        if addition is not None:
            message = firstName + " was successfully registered as a temporary student"
            success = True
        else: 
            message = firstName + "could not be registered"
            success = False
    
    temp_students = TempStudent.query.all()
    temp_students_list = []
    for student in temp_students:
        temp_students_list.append([student.id, student.firstName, student.secondName, student.emergencyNumber])
        
    #print(temp_students_list)
    
    return render_template('temp_student_reg.html', message=message, success=success, studentList = temp_students_list)

@app.route('/view_lessons')
@login_required
def view_lessons():
    check_maintenance()
    # role_required("tutor", "View Lessons")
    
    createLesson = permission_required(current_user.id, "add_a_new_lesson")
    deleteLesson = permission_required(current_user.id, "delete_a_lesson")
    view_all_lessons = permission_required(current_user.id, "view_all_lessons")
    view_lessons_at_centre = permission_required(current_user.id, "view_lessons_at_centre")
        
    
    subjects = []
    centres = []
    tutors = []
    allstudents = []
    years = []

    
    if current_user.is_tutor(): 
        lessons = Lesson.query.filter_by(tutorID = getOtherID("tutor", current_user.id)).all()

    if view_lessons_at_centre:
        # lessons = Lessons.query.filter_by(centre = ).all()
        lessons = []

    if view_all_lessons:
        lessons = Lesson.query.all()
    
    
    if createLesson:        
        allSubjects = Subject.query.all()
        for subject in allSubjects:
            subjects.append({"name": subject.tier + " " + subject.title, "id" : subject.subjectID})
        
        allCentres = Centre.query.all()
        for centre in allCentres:
            centres.append({"id" : centre.centreID, "name" : centre.name})
                    
        allTutors = getAllUsers("all_staff", log_on = True)
        for tutor in allTutors:
            tutors.append({"id": tutor.id, "name": tutor.firstName + " " + tutor.secondName})
        
        allStudents = Students.query.all()
        for student in allStudents:
            allstudents.append({"id" : student.id, "firstName" : student.firstName, "secondName" : student.secondName, "year" : student.year_group})
        
        years = [gen_academic_year(), gen_relative_academic_year(1), gen_relative_academic_year(2)]
    
    lessonList = []
    
    for lesson in lessons:
        subject = Subject.query.filter_by(subjectID = lesson.subjectID).first()
        subjectName = subject.tier + " " + subject.title
        centreName = Centre.query.filter_by(centreID = lesson.centreID).first().name
        students = StudentLesson.query.filter_by(lessonID = lesson.lessonID).all()
        tutor = Staff.query.filter_by(id=lesson.tutorID).first().firstName
        studentList = []
        for student in students:
            studentList.append(Students.query.filter_by(id=student.studentID).first().firstName)
        unregStudents = unregisteredStudentLessons.query.filter_by(lessonID=lesson.lessonID)
        for student in unregStudents:
            studentList.append(student.studentName)
        lessonList.append({"subjectName" : subjectName, 
                           "day" : lesson.day,"start" : str(lesson.startTime), 
                           "end" : str(lesson.endTime), 
                           "centre" : centreName, 
                           "students" : studentList, 
                           "id" : lesson.lessonID, 
                           "tutor": tutor, 
                           "dayForOrder" : day_to_num(lesson.day), 
                           "active" : lesson.active, 
                           "studentNum" : len(studentList), 
                           "week" : lesson.weekNo, 
                           "centreID" : lesson.centreID, 
                           "tutorID" : lesson.tutorID,
                           "subjectID" : lesson.subjectID,
                           "academicYear" : lesson.AcademicYear
                           }) 
       
    return render_template("view_Lessons.html", 
                           lessonList = sorted(sorted(sorted(lessonList, key=lambda x: x['dayForOrder']), key=lambda x:x['week']),key=lambda x: x['active'], reverse=True ), 
                           year=gen_academic_year(), 
                           week=gen_week_no(0), 
                           subjects=sorted(subjects, key=lambda x: x['name']), 
                           centres=centres, years=years, tutors=sorted(tutors, key=lambda x: x['name']), 
                           students=sorted(allstudents, key=lambda x: x['firstName']), 
                           createLesson = createLesson, 
                           deleteLesson = deleteLesson)


# This is a really bad function please fix it at some point
# worse than I though definitely fix
# repair the really long list and make it a dict 
# also implement the fileNumber stuff
@app.route('/lesson_plan', methods = ['POST', 'GET'])
@login_required
def lesson_plan():
    check_maintenance()
    #role_required("tutor", "Lesson Plan")
    
    upload_to_subject_resources = permission_required(current_user.id, 'upload_to_subject_resources')             
    upload_to_subject = permission_required(current_user.id, 'upload_to_subject')
    change_lesson_plan = permission_required(current_user.id, 'change_lesson_plan')
        
    topics = []
    subjects = []
    subjectList = Subject.query.all()       
    dates = []
    
    for subject in subjectList: 
        subjects.append([subject.subjectID, subject.tier + " " + subject.title])

    
    topicList = lessonPlan.query.order_by(lessonPlan.subjectID).order_by(lessonPlan.weekNo).all()
    i = 1
    for topic in topicList:
        fileNo = len(Files.query.filter_by(subjectID = topic.subjectID).all())
        while(i<topic.weekNo):
            topics.append([str(topic.subjectID), i, " ", fileNo])
            i+=1
        topics.append([str(topic.subjectID), topic.weekNo, topic.topic.replace("/", "-").replace('"', "'"), fileNo])
        i+=1
        
    for i in range(0, 53, 1):
        dates.append(weekNoToDate(i))
    

    return render_template('lesson_plan.html', topics = topics, subjects = sorted(subjects, key=lambda x: x[1]), dates = dates, upload_to_subject_resources = upload_to_subject_resources, upload_to_subject = upload_to_subject, change_lesson_plan = change_lesson_plan)

@app.route('/tutor_overview', methods=['POST', 'GET'])
@login_required
def tutor_overview():
    check_maintenance()
    #role_required("tutor", "Tutor Overview Page")
    lessonInfo = []
    userID = request.args['id']
    tutorID = User.query.filter_by(id=userID).filter_by(role="tutor").first().otherID
    lessonsInfo = LessonInfo.query.filter_by(tutorID=tutorID).all()
    
    for lesson in lessonsInfo:
        info = Lesson.query.filter_by(lessonID=lesson.lessonID).first()
        subject = Subject.query.filter_by(subjectID=info.subjectID).first()
        lessonInfo.append({"name" : subject.tier + " " + subject.title, "start" : info.startTime, "end" : info.endTime, "register" : lesson.register, "homework" : lesson.homework, "weekNo" : lesson.weekNo, "day" : info.day, "dayForSorting" : day_to_num(info.day)})
    
    return render_template("tutor_overview.html", tasks=sorted(sorted(lessonInfo, key=lambda x: x['dayForSorting'], reverse=True), key=lambda x: x['weekNo'], reverse=True) )

@app.route('/admin_overview', methods=['POST', 'GET'])
@login_required
def admin_overview():
    check_maintenance()
    role_required("receptionist", "Admin Overview")
    
    try:
        more = int(request.args['more'])
    except: 
        more = 1
    
    adminLog = []
    tutorLog = []
    studentLog = []
    anonLog = []
    
    logs = log.query.order_by(log.date.desc()).all()
    for i in logs:
        if i.role == "admin":
            adminLog.append([str(i.date)[:19], i.message])
        elif i.role in ["tutor", 'receptionist', 'manager']: 
            tutorLog.append([str(i.date)[:19], i.message])
        elif i.role == "student":
            studentLog.append([str(i.date)[:19], i.message])
        else:   
            anonLog.append([str(i.date)[:19], i.message])

        
    return render_template("admin_overview.html", adminLog=adminLog[:(more * 50)], tutorLog = tutorLog[:(more * 50)], studentLog=studentLog[:(more * 50)], anonLog = anonLog[:(more * 50)])

@app.route("/student_reg")
def student_reg():
    # check_maintenance()
    # if current_user.id != 142:
    #     abort(503, )
    #role_required("admin", "Admin Overview")

    lessonList = Lesson.query.filter_by(active=True).filter_by(weekNo = -1).filter_by(AcademicYear = gen_academic_year()).all()
    lessons = [{'id' : lesson.lessonID, 
                'tier' : getTier(lesson.subjectID), 
                'title' : getTitle(lesson.subjectID), 
                'day' : lesson.day, 
                'time' : str(lesson.startTime), 
                'centre' : getCentre(lesson.centreID)} for lesson in lessonList]

    try: 
        option = request.args['option']
    except:
        return render_template("student_registration.html", lessons = lessons)
    
    # if option == "1":
    #     return render_template("student_registration_1.html")

    # if option == "2":
    #     return render_template("student_registration_2.html")
    
    # if option == "3":
    #     return render_template("student_registration_3.html")

    # if option == "4":
    #     return render_template("student_registration_4.html")

@app.route("/admin_tutor_view", methods=['POST', 'GET'])
@login_required
def admin_view_tutors():
    check_maintenance()
    role_required("receptionist", "Admin Tutor View")
    
    tutorList = getAllUsers("tutor")
    tutors = []
    for tutor in tutorList:           
        tutors.append({"id" : getUserID("tutor", tutor.id), "firstName" : tutor.firstName, "secondName" : tutor.secondName, "gender" : tutor.gender, "email" : tutor.email, "phone" : tutor.phone, "logOn" : getUserPermission(id = tutor.id, action = "log_on", role = "tutor"), "profile_pic" : os.path.isfile(f"userFiles/{tutor.id}/profile_picture.jpg")})
    
    return render_template("admin_tutor_view.html", tutors= sorted(sorted(tutors, key = lambda x : x['firstName']), key=lambda x: x['logOn'], reverse = True))
    # return render_template("admin_tutor_view.html", tutors= tutors)


#id provided in the URL is the userID
@app.route("/admin_tutor_info", methods=['POST', 'GET'])
@login_required
def admin_tutor_info():
    check_maintenance()
    # #role_required("admin", "Admin Tutor Info")
    permission_required(current_user.id, "view_all_tutor_information", fatal=True)
    edit_tutor_information = permission_required(current_user.id, 'edit_tutor_information')
    tutorid = getOtherID("tutor", request.args['tutorid'])   
    
    
    return view_tutor_info(tutorid, edit_tutor_information)

def view_tutor_info(tutorid, edit_tutor_information):
    # #role_required("tutor", "Tutor Tutor Info")
    tutor = Staff.query.filter_by(id=tutorid).first()
    
    subjectList = TutorSubject.query.filter_by(tutorID=tutorid).all()
    subjects = []    
    for subjectItem in subjectList: 
        subject = Subject.query.filter_by(subjectID=subjectItem.subjectID).first()
        subjects.append( subject.tier + " " + subject.title)
    
    allSubjects = []
    for subject in Subject.query.all():
        allSubjects.append(subject.tier + " " + subject.title)
        
    lessonList = Lesson.query.filter_by(tutorID=tutorid).filter_by(active = True).all()
    lessons = []
    students = []
    lessonsInfo = []
    
    num = 0
    for lesson in lessonList:
        subject = Subject.query.filter_by(subjectID=lesson.subjectID).first()
        studentList = StudentLesson.query.filter_by(lessonID = lesson.lessonID).all()
        studentsPerLesson = []
        
        for student in studentList: 
            studentsPerLesson.append(Students.query.filter_by(id = student.studentID).first().firstName)
        
        students.append(studentsPerLesson)
        lessons.append({"subject": subject.tier + " " + subject.title, "day": lesson.day, "start": lesson.startTime, "end":lesson.endTime, "size": len(studentList), "id": lesson.lessonID, "numberInList":num})
        num += 1
        
        thisWeekNo = int(gen_week_no(0))
        
        lessonInfoList = LessonInfo.query.filter_by(lessonID = lesson.lessonID).filter_by(dismissed = False).filter((LessonInfo.register==False) | (LessonInfo.homework==False)).filter(LessonInfo.weekNo <= thisWeekNo).all()
        for lessonInfo in lessonInfoList:
            lessonsInfo.append({"weekno" : lessonInfo.weekNo, "register": lessonInfo.register, "homework" : lessonInfo.homework, "subject": subject.tier + " " + subject.title, "day": lesson.day, "start": lesson.startTime, "id":lesson.lessonID})
    
    tutorInfo = {"firstName" : tutor.firstName , "secondName" : tutor.secondName, "email" : tutor.email, "phone" : tutor.phone, "address" : tutor.house_number + " " + tutor.street_name + " " + tutor.post_code, "id": getUserID("tutor", tutor.id), "gender" : tutor.gender, "role" : "tutor"}
        
    return render_template("admin_tutor_info.html", tutorInfo=tutorInfo, subjects=subjects, lessons=lessons, students=students, lessonsInfo=lessonsInfo, allSubjects=allSubjects, tutorid = tutorid, edit_tutor_information = edit_tutor_information)

#id provided in the URL is the userID
@app.route("/tutor_info", methods = ['POST', 'GET'])
@login_required
def tutor_info():
    check_maintenance()
    #role_required("tutor", "Tutor Tutor Info")
        
    tutorid = getOtherID("tutor", current_user.id)
    
    return view_tutor_info(tutorid, True)

#id provided in the URL is the userID
@app.route("/staff_info")
@login_required
def staff_info():
    edit_tutor_info = False
    
    try: 
        if permission_required(current_user.id, "view_staff_info"): 
            staffID = request.args['staffID']
            edit_tutor_info = permission_required(current_user.id, 'edit_tutor_information')
        else:
            staffID = current_user.id
            
    except:
        if current_user.is_student() or current_user.is_tutor():
            abort(403, )
        else: 
            edit_tutor_info = True
            staffID = current_user.id

    tutor = Staff.query.filter_by(id=getOtherID(getUserRole(staffID), staffID)).first()
    
    subjectList = TutorSubject.query.filter_by(tutorID=getOtherID(getUserRole(staffID), staffID)).all()
    subjects = []    
    for subjectItem in subjectList: 
        subject = Subject.query.filter_by(subjectID=subjectItem.subjectID).first()
        subjects.append({"id" : subject.subjectID, "name" : subject.tier + " " + subject.title})
    
    allSubjects = []
    for subject in Subject.query.all():
        allSubjects.append({"id" : subject.subjectID, "name" : subject.tier + " " + subject.title})
        
    lessonList = Lesson.query.filter_by(tutorID=getOtherID(getUserRole(staffID), staffID)).filter_by(active = True).all()
    lessons = []
    students = []
    lessonsInfo = []
    
    num = 0

    tutorInfo = {"firstName" : tutor.firstName , "secondName" : tutor.secondName, "email" : tutor.email, "phone" : tutor.phone, "address" : tutor.house_number + " " + tutor.street_name + " " + tutor.post_code, "id": staffID, "gender" : tutor.gender, "role" : tutor.role}

    num = 0
    for lesson in lessonList:
        subject = Subject.query.filter_by(subjectID=lesson.subjectID).first()
        studentList = StudentLesson.query.filter_by(lessonID = lesson.lessonID).all()
        studentsPerLesson = []
        
        for student in studentList: 
            studentsPerLesson.append(Students.query.filter_by(id = student.studentID).first().firstName)
        
        students.append(studentsPerLesson)
        lessons.append({"subject": subject.tier + " " + subject.title, "day": lesson.day, "start": lesson.startTime, "end":lesson.endTime, "size": len(studentList), "id": lesson.lessonID, "numberInList":num})
        num += 1
        
        thisWeekNo = int(gen_week_no(0))
        
        lessonInfoList = LessonInfo.query.filter_by(lessonID = lesson.lessonID).filter_by(dismissed = False).filter((LessonInfo.register==False) | (LessonInfo.homework==False)).filter(LessonInfo.weekNo <= thisWeekNo).all()
        for lessonInfo in lessonInfoList:
            lessonsInfo.append({"weekno" : lessonInfo.weekNo, "register": lessonInfo.register, "homework" : lessonInfo.homework, "subject": subject.tier + " " + subject.title, "day": lesson.day, "start": lesson.startTime, "id":lesson.lessonID})
    
        
    return render_template("admin_tutor_info.html", 
    tutorInfo=tutorInfo, 
    subjects=subjects, 
    lessons=lessons, 
    students=students, 
    lessonsInfo=lessonsInfo, 
    allSubjects=allSubjects, 
    tutorid = getOtherID(getUserRole(staffID), staffID), 
    edit_tutor_information = edit_tutor_info, 
    roles = getAllRoles())


@app.route("/tutor_reg", methods=['POST', 'GET'])
@login_required
def add_tutor():
    check_maintenance()
    #role_required("admin", "Tutor Registration")
    lessons = []
    
    lessonList = Subject.query.all()
    for item in lessonList:
        lessons.append({"id": str(item.subjectID), "name": item.tier + " " + item.title})
    
    return render_template("tutor_reg.html", lessons=lessons )

@app.route("/admin_student_view", methods=["POST", "GET"])
@login_required
def admin_student_view():
    check_maintenance()
    #role_required("tutor", "Admin Student View")
    view_all_student_information = permission_required(current_user.id, 'view_all_student_information')
    delete_a_student = permission_required(current_user.id, 'delete_a_student')

    studentList = Students.query.all()
    students = []
    for student in studentList:
        if student.year_group == "":
            year_group = "Group Not known"
        else:
            year_group = student.year_group
        
        address = student.house_number + " " + student.street_name + " " + student.post_code + " " + student.city_or_county
        students.append({"id" : student.id,"firstName" : student.firstName, "secondName" : student.secondName, "year" :  year_group, "gender" :student.gender, "parent_email": student.parent_email, "priority_1_email" : student.priority_contact_1_email,  "priority_2_email" : student.priority_contact_2_email, "priority_1_phone" : student.priority_contact_1_mobile_telephone, "priority_2_phone" : student.priority_contact_2_mobile_telephone, "address" : address, "studentEmail" : student.email, "regDate" : str(student.declaration_date)})
    return render_template("admin_student_view.html", students = sorted(students, key=lambda x: x['firstName']), view_all_student_information=view_all_student_information, delete_a_student=delete_a_student)

@app.route("/admin_student_info", methods=['POST', 'GET'])
@login_required
def admin_student_info():
    check_maintenance()
    # #role_required("admin", "Admin Student Info")
    permission_required(current_user.id, "view_all_student_information", fatal=True)
    edit_student_information = permission_required(current_user.id, "edit_student_information")

    #ID from the students table
    studentid = request.args['studentid']
    
    return student_info(studentid, edit_student_information)

def student_info(studentid, edit_student_information):
    lessonList = StudentLesson.query.filter_by(studentID = studentid).all()
    lessons = []
    
    for lesson in lessonList:
        lessonInfo = Lesson.query.filter_by(lessonID = lesson.lessonID).first()
        if lessonInfo is not None and lessonInfo.active and lessonInfo.AcademicYear == gen_academic_year(): 
            lessons.append(getLessonString(lessonInfo.lessonID))
    
    student = Students.query.filter_by(id=studentid).first()
    
    info = {"firstName" : student.firstName,
            "middleName" : student.middleName,
            "secondName" : student.secondName,
            "email" : student.email,
            "parent_email" : student.parent_email,
            "known_as" : student.known_as,
            'year_group' : student.year_group,
            "gender" : student.gender,
            'house_number' : student.house_number,
            'street_name' : student.street_name,
            'city_or_county' : student.city_or_county,
            'post_code' : student.post_code,
            'current_school_1' : student.current_school_1,
            'child_protection_register' : student.child_protection_register,
            'look_after_child_contact_info' : student.look_after_child_contact_info,
            'look_after_child_register' : student.look_after_child_register,
            'personal_education_plan' : student.personal_education_plan,
            'gp_name' : student.gp_name,
            'gp_post_code' : student.gp_post_code,
            'gp_telephone' : student.gp_telephone,
            'gp_practice_address' : student.gp_practice_address,
            'child_normally_healthy' : student.child_normally_healthy,
            'serious_illness_or_accidents' : student.serious_illness_or_accidents,
            'condition_affecting_school_life' : student.condition_affecting_school_life,
            'allergies' : student.allergies,
            'allergyInfo' : student.allergyInfo,
            'asthma' : student.asthma,
            'epilepsy_or_fits' : student.epilepsy_or_fits,
            'heart_problems' : student.heart_problems,
            'nose_bleeds' : student.nose_bleeds,
            'speech_or_hearing_difficulties' : student.speech_or_hearing_difficulties,
            'mobility_difficulties' : student.mobility_difficulties,
            'other_difficulties' : student.other_difficulties,
            'known_medical_conditions' : student.known_medical_conditions,
            'medical_treatment_or_medicines' : student.medical_treatment_or_medicines,
            'extra_medical_info' : student.extra_medical_info,
            'emergency_information' : student.emergency_information,
            'first_aid_permission' : student.first_aid_permission,
            'hospital_referral_permission' : student.hospital_referral_permission,
            'special_educational_needs' : student.special_educational_needs,
            'sen_information' : student.sen_information,
            'behavior_support_needed' : student.behavior_support_needed,
            'behavior_support_info' : student.behavior_support_info,
            'priority_contact_1_title' : student.priority_contact_1_title,
            'priority_contact_1_relationship' : student.priority_contact_1_relationship,
            'priority_contact_1_forename' : student.priority_contact_1_forename,
            'priority_contact_1_surname' : student.priority_contact_1_surname,
            'priority_contact_1_home_telephone' : student.priority_contact_1_home_telephone,
            'priority_contact_1_email' : student.priority_contact_1_email,
            'priority_contact_1_mobile_telephone' : student.priority_contact_1_mobile_telephone,
            'priority_contact_1_work_number' : student.priority_contact_1_work_number,
            'priority_contact_2_title' : student.priority_contact_2_title,
            'priority_contact_2_relationship' : student.priority_contact_2_relationship,
            'priority_contact_2_forename' : student.priority_contact_2_forename,
            'priority_contact_2_surname' : student.priority_contact_2_surname,
            'priority_contact_2_home_telephone' : student.priority_contact_2_home_telephone,
            'priority_contact_2_email' : student.priority_contact_2_email,
            'priority_contact_2_mobile_telephone' : student.priority_contact_2_mobile_telephone,
            'priority_contact_2_work_number' : student.priority_contact_2_work_number,
            'eal' : student.eal,
            'pupil_first_language' : student.pupil_first_language,
            'pupil_other_language' : student.pupil_other_language,
            'home_main_language' : student.home_main_language,
            'home_other_language' : student.home_other_language,
            'id' : student.id, 
            'dob' : getDOB(student.date_of_birth)
                    }
    
        
    return render_template("admin_student_info.html", 
                           info=info, 
                           lessons=lessons, 
                           studentid = studentid, 
                           edit_student_information=edit_student_information,
                           delete_a_student = permission_required(current_user.id, "delete_a_student"), 
                           reset_password = permission_required(current_user.id, "reset_below_password") and getRoleLevel(getUserRole(current_user.id)) > getRoleLevel("student"),
                           userID = getUserID("student", studentid))

@app.route("/student_profile", methods = ['POST', 'GET'])
@login_required
def student_profile():
    check_maintenance()
    #role_required("student", "Student profile")
    studentID = getOtherID("student", current_user.id)
    
    return student_info(studentID, True)

@app.route("/subjects", methods=['POST', 'GET'])
@login_required
def subjects():
    check_maintenance()
    #role_required("admin", "Subjects")
    subjectList = Subject.query.all()
    subjects = []
    
    for subject in subjectList:
        subjects.append([subject.subjectID, subject.tier + " " + subject.title])
        
    # print(subjects)

    return render_template("subjects.html", subjects = subjects)

@app.route("/weekly_report", methods =['POST', 'GET'])
@login_required
def weeklyReport():
    check_maintenance()
    #role_required("admin", "Weekly Report")
    try:
        offset = request.args['offset']
    except: 
        offset = 0 
        
    lessonNumbers = []
    subjectIDs = []
    #[{"id": , "name": , "numbers": }]
    subjectList =  ['GCSE Maths', 'GCSE English', 'GCSE Biology', 'GCSE Chemistry', 'GCSE Physics', 'A-LEVEL Maths', 'A-LEVEL Physics', 'A-LEVEL Chemistry', 'A-LEVEL Biology', 'AS Mathematics', 'AS Physics' ]
    for i in subjectList: 
        subjectIDs.append(getSubjectID1(i))
    
        
    for i in range(len(subjectIDs)):
        lessonNumbers.append({"id" : subjectIDs[i], "name" : subjectList[i], "number" : 0, "SOHO" : 0, "COV" : 0})
    
    weekNo = gen_week_no(int(offset))
    lessons = []
    lessonList = Lesson.query.filter(or_(Lesson.weekNo == weekNo, Lesson.weekNo == -1)).filter_by(active = True).all()
    
    for lesson in lessonList:
        attendance = []
        lessonName = getLessonInfoString(lesson.lessonID, weekNo)
        studentList = StudentAttendance.query.filter_by(lessonID=lesson.lessonID).filter_by(present=True).filter_by(weekNo=weekNo).all()
        unregisteredList = UnregisteredAttendance.query.filter_by(lessonID=lesson.lessonID).filter_by(present=True).filter_by(weekNo=weekNo).all()
        tempList = TempAttendance.query.filter_by(lessonID=lesson.lessonID).filter_by(weekNo=weekNo).all()
        
        for student in studentList: 
            attendance.append(getStudent(student.studentID))
        
        for student in unregisteredList:
            attendance.append("(unreg)" +student.studentName)
            
        for student in tempList:
            if(student.name != "temp-undefined"):
                attendance.append("(temp)" + student.name)
                
        for i in lessonNumbers:
            if i['id'] == lesson.subjectID:
                if lesson.day=="SUN" or lesson.day == "SAT":
                    if lesson.centreID == 3:
                        i['SOHO'] += len(attendance)
                    elif lesson.centreID == 2:
                        i['COV'] += len(attendance)
                i['number'] += len(attendance)
            
        lessons.append({"name" : lessonName, "attendance" : attendance, "dayForSort" : int(day_to_num(lesson.day)), "timeForSort" : int(str(lesson.startTime)[:2])})
         
    
    return render_template("weeklyReport.html", weekNo = weekNo, lessons = sorted(sorted(lessons, key=lambda x: x['timeForSort']), key=lambda x: x['dayForSort']), lessonNumbers = lessonNumbers)

@app.route('/Classroom_View_Grades', methods=['POST', 'GET'])
@login_required
def Classroom_View_Grades():
    check_maintenance()
    #role_required("tutor", "Classroom Grades")
    lessonID = request.args['lessonid']
    weekNo = request.args['weekNo']
    academicYear = request.args['year']
    make_individual_test = permission_required(current_user.id, "make_individual_test")
    
    tests = []
    
    testList = Tests.query.filter_by(lessonID = lessonID).all()
    
    
    for test in testList: 
        grades = []
        gradeList = Grades.query.filter_by(testID = test.testID).all()
        for grade in gradeList:
            if grade.studentID != None: 
                grades.append({"id" : grade.studentID,"name" : getStudent(grade.studentID), "mark" : grade.mark, "grade" : grade.grade, "gradeID" : grade.gradeID})
            else: 
                grades.append({"id" : -1, "name" : grade.studentName, "mark" :  grade.mark, "grade" : grade.grade, "gradeID" : grade.gradeID})

        tests.append({"weekNo" : test.weekNo, "total" : test.total, "filename" : test.filename, "name" : test.name, "date" : test.date, "id" : test.testID, "grades" : sorted(grades, key = lambda x : x['mark'], reverse = True), "average" : getAverageGrade(test.testID)})
        
        
        
    return render_template("Classroom_View_Grades.html", tests = tests, make_individual_test = make_individual_test)

@app.route('/change_password', methods = ['POST', 'GET'])
@login_required
def change_password():
    check_maintenance()
    # #role_required("student", "Change Password")
    if request.method == 'POST': 
        
        oldPassword = request.form['oldPassword']
        newPassword = request.form['newPassword']
        
        if check_password_hash(getUserPassword(current_user.id), oldPassword):
            stmt = update(User).where(User.id == current_user.id).values({'password' : generate_password_hash(newPassword)})
            db.session.execute(stmt)
            db.session.commit()
                             
            db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): Password was just changed" , date=datetime.utcnow()))
            db.session.commit()
        return redirect('/')
        
    
    return render_template("change_password.html")

@app.route('/student_overview', methods = ['POST', 'GET'])
@login_required
def student_overview():
    check_maintenance()
    #role_required("admin", "Student Overview")
    try:
        studentID = request.args['studentid']
    except:
        studentID = -1
        
    lessons = []

    if(studentID == -1):
        return "invalid student ID"
    
    name = getStudent(studentID)
    
    lessonList = StudentAttendance.query.filter_by(studentID = studentID).filter_by(present = True).all()
    
    for lesson in lessonList:
        lessons.append({ "lesson" : getLessonString(lesson.lessonID), "week" : lesson.weekNo, "year" : getLessonYear(lesson.lessonID)})
        
    return render_template("student_overview.html", lessons = sorted(sorted(lessons, key = lambda x: x['week'], reverse=True), key=lambda x:x['year'], reverse = True), name = name)

@app.route('/unregisteredStudents', methods = ['POST', 'GET'])
@login_required
def unregisteredStudents():
    check_maintenance()
    #role_required("tutor", "Unregistered Students")
    permission_required(current_user.id, "change_lesson_students")
    
    unregisteredStudents = []
    registered = []
    # marks = []
    students = unregisteredStudentLessons.query.all()
    regStudents = Students.query.all()
    
    for student in regStudents: 
        year_group = Students.query.filter_by(id = student.id).first().year_group
        registered.append({ "id" : student.id, "name" : getStudent(student.id) + " - " + year_group})
    
    for student in students:
        # if student.studentName != "undefined" and student.studentName not in unregisteredStudents and student.studentName != "":
        if student.studentName != "undefined" and student.studentName != "":

            unregisteredStudents.append({"student" : student.studentName, "lesson" : getLessonString(student.lessonID), "lessonID" : student.lessonID})
    
    return render_template('unregisteredStudents.html', unregisteredStudents=sorted(unregisteredStudents, key=lambda x: x['student']), registered = sorted(registered, key = lambda x:x['name']))

@app.route('/unregisteredGrades', methods = ['POST', 'GET'])
@login_required
def unregisteredGrades(): 
    check_maintenance()
    #role_required("admin", "Unregistred Grades")
    unregistered = []
    registered = []
    unregisteredList = Grades.query.filter(Grades.studentID == None).filter(Grades.mark != -1).all()
    regStudents = Students.query.all()
    
    for student in regStudents: 
        registered.append({ "id" : student.id, "name" : getStudent(student.id) })
        
    for student in unregisteredList:
        if getGradeYear(student.gradeID) == gen_academic_year():
            unregistered.append({"studentName" : student.studentName, "test" : getGrade(student.gradeID), "testID" : student.testID, "mark" : student.mark, "gradeID" : student.gradeID})
        
        
    return render_template('unregisteredGrades.html', unregistered = sorted(unregistered, key=lambda x:x['studentName']), registered = sorted(registered, key=lambda x:x['name']))

@app.route('/importantDocs', methods = ['POST', 'GET'])
@login_required
def importantDocs(): 
    check_maintenance()
    #role_required("tutor", "Important Documents")

    path = '/var/www/webApp/webApp/files/IMPORTANT_DOCS'
    documentList = [{"displayName" : f.replace("_", " "), "name" : f, "type" : getFileType(f)[1:]} for f in listdir(path) if isfile(join(path, f))]
    # print(documentList)
    
    return render_template("importantDocs.html", documentList = sorted(documentList, key=lambda x:x['name']))

@app.route('/maintenance')
@login_required
def maintenance():
    check_maintenance()
    return render_template('maintenance.html')

@app.route('/lesson_files')
@login_required
def lesson_files():
    check_maintenance()
    role_required("tutor", "Lesson Files")
    lessonPlanAllowed = permission_required(current_user.id, 'change_lesson_plan')
    uploadFiles = permission_required(current_user.id, 'upload_to_subject')
    
    
    fileList = Files.query.order_by(Files.classtype, Files.filename).all()
    subjects = []
    subjectNames = [None] * 150
    
    subjectList = Subject.query.all()
    
    for subject in subjectList:
        subjects.append(subject.subjectID)
        subjectNames[int(subject.subjectID)] = subject.tier + " " + subject.title
        
    sorted_subjects = sorted(subjects, key=lambda sid: subjectNames[int(sid)])
        
    files = dict.fromkeys(subjects)

    
    for file in fileList:
        if file.subjectID is None:
            continue
        else:
            if files[file.subjectID] is None:
                subject = Subject.query.filter_by(subjectID=file.subjectID).first()
                fileFolder = getFileFolder(file.subjectID)
                
                files[file.subjectID] = [fileFolder]
                
                topicList = lessonPlan.query.filter_by(subjectID = file.subjectID)
                topics = []
                for topic in topicList:
                    topics.append({"weekNo" : topic.weekNo, "topic" : topic.topic})
                
                files[file.subjectID].append(topics)
                
            files[file.subjectID].append({"filename" : file.filename, "weekNo" : file.weekNo, "classtype" : file.classtype, "id" : file.fileid, "studentView" : file.studentview, "hide_from_all" : file.hide_from_all, "filenameView" : file.filename.replace("_", " "), 'subjectName' : getFileFolder(file.subjectID), 'auto_print' : file.auto_print})
    
    current_academic_year = gen_academic_year()
    lessons = Lesson.query.filter_by(AcademicYear=current_academic_year, active=True).all()
    
    lessons_by_subject = {}
    for lesson in lessons:
        if lesson.subjectID not in lessons_by_subject:
            lessons_by_subject[lesson.subjectID] = []
        lessons_by_subject[lesson.subjectID].append(lesson.weekNo)

    ordered_files = {sid: files[sid] for sid in sorted_subjects}
    
    dates = [weekNoToDate(i) for i in range(1, 53, 1)]
            
    return render_template("lesson_files.html", files = ordered_files, subjectNames = subjectNames, dates = dates, lessonPlanAllowed=lessonPlanAllowed, uploadFiles = uploadFiles, lessons_by_subject=lessons_by_subject)

@app.route('/studentGrades', methods = ['POST', 'GET'])
@login_required
def studentGrades():
    check_maintenance()
    #role_required("student", "Student Grades")
    if(current_user.is_student()):
        studentID = getOtherID("student", current_user.id)
    elif(permission_required(current_user.id, "view_all_student_information", message="View student Grades") or isParentFor(current_user.id, request.args['studentID'])):
        studentID = request.args['studentID']
    
    query = (
        db.session.query(Grades, Tests)
        .join(Tests, Grades.testID == Tests.testID)
        .filter(Grades.studentID == studentID)
        .filter(Grades.mark > -1)
        .order_by(Tests.date.desc())
    )

    results = []
    current_subject_id = None
    current_subject_grades = []

    for grade, test in query:

        current_subject_id = Lesson.query.filter_by(lessonID = test.lessonID).first().subjectID
        current_subject_grades =  {
            'gradeID' : grade.gradeID,
            'testName': test.name,
            'total': test.total,
            'mark': grade.mark,
            'grade': grade.grade,
            'date' : test.date,
            "id" : test.testID
        }

        results.append([getSubjectName(current_subject_id), current_subject_grades])
    
    studentList = Students.query.all()
    
    studentIDs = [student.id for student in sorted(studentList, key=lambda x :x.firstName)]
    
    index = studentIDs.index(int(studentID))

    previous_id = studentIDs[index - 1]
    following_id = studentIDs[index + 1]
    
    return render_template("student_grades.html", results = sorted(sorted(results, key=lambda x : x[1]['testName']), key = lambda x:x[1]['date'], reverse = True), name = getStudent(studentID), previous = previous_id, following = following_id)

@app.route('/fix_files', methods = ['POST', 'GET'])
@login_required
def fixFiles():
    check_maintenance()
    fileList = Files.query.all()
    files = []
    
    for file in fileList:
        files.append(file.filename)
        
    files = list(set(files))
    
    lessons = []
    
    for file in files: 
        lessonList = Files.query.filter_by(filename = file).all()
        temp = [file]
        
        for lesson in lessonList: 
            if getLessonString(lesson.lessonID) != "Lesson does not Exist":
                temp.append(getLessonString(lesson.lessonID) + " for week " + str(lesson.weekNo))
        
        try: { 
             temp.append([Lesson.query.filter_by(lessonID = lessonList[0].lessonID).first().subjectID, lessonList[0].weekNo]) 
        }
        except: {}
                    
        if len(temp) > 1:
            lessons.append(temp)
        
    allSubjects = Subject.query.all()
    subjects = []
    for subject in allSubjects:
        subjects.append({"name": subject.tier + " " + subject.title, "id" : subject.subjectID})
            
        
    return render_template('fixFiles.html', files = lessons, subjects = sorted(subjects, key = lambda x:x['name']))

@app.route('/release_notes')
@login_required
def release_notes(): 
    check_maintenance()
    return render_template("release_notes.html")

@app.route('/make_all_tests')
@login_required
def make_all_tests():
    check_maintenance()
    #role_required("admin", "make all tests")

    subjectList = Subject.query.all()

    subjects = [{"id" : subject.subjectID, "name" : subject.tier + " " + subject.title} for subject in subjectList]
    scopes = ["all", "week", "weekend"]

    return render_template("make_all_tests.html", subjects = sorted(subjects, key = lambda x : x['name']), scopes = scopes)

@app.route('/make_exams')
@login_required 
def make_exams(): 
    check_maintenance()
    try:
        AcademicYear = request.args['AcademicYear']
    except:
        AcademicYear = gen_academic_year()
    #role_required("admin", "make exams")
    
    AcademicYears = [gen_relative_academic_year(-1), gen_relative_academic_year(0), gen_relative_academic_year(1)]

    examList = getExams(AcademicYear)

    exams = []

    for exam in examList:
        paperList = ExamPapers.query.filter_by(examID = exam.examID).all()
        papers = []
        for paper in paperList: 
            papers.append({"number" : paper.paperNo, "paperCode" : paper.paperCode, "duration" : paper.duration, "total" : paper.total, "date" : paper.date})

        exams.append({"id" : exam.examID, 
                      "name" : exam.examBoard + " " + exam.tier + " " + exam.title + " (" + exam.code + ") " + exam.examSeries, 
                      "tier" : exam.tier,
                      "title" : exam.title,
                      "examBoard" : exam.examBoard,
                      "code" : exam.code,
                      "Option" : exam.Option,
                      "examSeries" : exam.examSeries,
                      "AcademicYear" : exam.AcademicYear,
                      "papers" : papers, 
                      "studentNo" : len(getStudentsForExam(exam.examID))
                      })
        
    examBoards = set([exam['examBoard'] for exam in exams])
    tiers = set([exam['tier'] for exam in exams])
    academicYears = set([exam['AcademicYear'] for exam in exams])
    examSeriesList = set([exam['examSeries'] for exam in exams])

    
    return render_template("make_exams.html", exams = exams, AcademicYear = AcademicYear, AcademicYears = AcademicYears, examBoards=examBoards, tiers=tiers, academicYears=academicYears, examSeriesList=examSeriesList)


@app.route('/add_exam', methods=['POST'])
@login_required
def add_exam():
    # Creates a new exam + its papers from the "Make a New Exam" form. Parses the
    # paper date and uses .get() so a missing/blank field can't 500 the request —
    # the previous handler passed the raw date string straight to the Date column,
    # which is what made "add a new exam" fail.
    check_maintenance()
    data = request.get_json() or {}
    try:
        new_exam = Exams(
            tier=data.get('tier'),
            title=data.get('title'),
            examBoard=data.get('examBoard'),
            code=data.get('examCode'),
            Option=data.get('option'),
            examSeries=data.get('examSeries'),
            AcademicYear=data.get('academicYear'),
        )
        db.session.add(new_exam)
        db.session.commit()  # assigns examID (autoincrement)

        for paper in data.get('papers', []):
            date_str = paper.get('date')
            paper_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
            db.session.add(ExamPapers(
                examID=new_exam.examID,
                paperNo=paper.get('paperNumber'),
                paperCode=paper.get('paperCode'),
                duration=paper.get('duration'),
                total=paper.get('total'),
                date=paper_date,
                extra_info=paper.get('extra_info'),
                startTime=paper.get('startTime'),
            ))
        db.session.commit()

        db.session.add(log(role=getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}): added a new exam {getExam(new_exam.examID)}", date=datetime.utcnow()))
        db.session.commit()
        return jsonify({'status': 'success', 'examID': new_exam.examID})
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/make_new_exam_student')
@login_required
def make_new_exam_student(): 
    check_maintenance()
    nonExamStudents = Students.query.filter_by(exam_student = False).all()
    
    return render_template("make_new_exam_student.html", nonExamStudents = nonExamStudents)

@app.route('/exam_students')
@login_required
def exam_students(): 
    check_maintenance()
    permission_required(current_user.id, "view_all_student_information", fatal=True)
    examStudents = get_exam_students()
    current_date = datetime.now().date()

    
    exams = getExams(gen_academic_year())
    exams_dict = [exam.to_dict() for exam in exams]

    
    ucasReferences = UCASReference.query.all()
    
    # Fetch all student exams
    student_exams = studentExam.query.all()
    
    # Create a dictionary to map student IDs to assigned exams
    student_exam_map = {}
    for se in student_exams:
        if se.studentID not in student_exam_map:
            student_exam_map[se.studentID] = []
        student_exam_map[se.studentID].append(se.examID)
        
    collapsed_students = []
    exam_students = []
    for student in examStudents:
        student_id = student[0]['id']
        exams = student_exam_map.get(student_id, [])
        
        # Check if the student has any current or future exams
        has_upcoming_exam = False
        for exam_id in exams:
            exam = Exams.query.get(exam_id)
            if exam and getLatestExamDate(exam_id) >= current_date:  # Any future or current exam
                has_upcoming_exam = True
                break
        
        if len(exams) == 0:
            has_upcoming_exam = True

        # Categorize student based on exam dates
        if has_upcoming_exam:
            exam_students.append(student)  # Regular display for students with current/future exams
        else:
            collapsed_students.append(student)  # Collapsible section for past-only exams    
    
    user_files_map = {}
    user_files_folder = 'var/www/webApp/webApp/userFiles'
    
    user_id_map = {}

    for student in examStudents:
        user_id = getUserID("student", student[0]['id'])
        user_id_map[student[0]['id']] = user_id
        user_folder = f"{user_files_folder}/{str(user_id)}"
        if os.path.exists(user_folder):
            user_files_map[user_id] = [f"{f}" for f in os.listdir(user_folder) if os.path.isfile(os.path.join(user_folder, f))]
        else:
            user_files_map[user_id] = []
    
    
    return render_template(
        "exam_students.html",
        exam_students = exam_students,
        examStudents = examStudents,
        collapsed_students=collapsed_students,
        exams=sorted(sorted(sorted(sorted(exams_dict, key = lambda x :x['code']), key = lambda x :x['title']), key = lambda x :x['tier']), key = lambda x :x['examSeries']),
        ucasReferences=ucasReferences,
        student_exam_map=student_exam_map,
        user_files_map=user_files_map, 
        user_id_map = user_id_map

    )
    
@app.route('/admin_create_alerts')
@login_required
def admin_create_alerts():
    check_maintenance()
    create_alerts = permission_required(current_user.id, 'create_alerts', fatal=True)
    
    return render_template("admin_create_alerts.html")

@app.route('/alert_status')
@login_required
def alert_status():
    check_maintenance()
    dismiss_alerts = permission_required(current_user.id, 'dismiss_alerts')
    alertsList = Alerts.query.filter_by(dismissed = False).all()
    alerts = []    
    for alert in alertsList: 
        viewed = sorted(filter( lambda x : "With ID" not in x[0], [getUserName(user.userID) for user in UserAlerts.query.filter_by(alertID = alert.alertID).filter_by(viewed = True).all()]))
        notViewed = sorted(filter( lambda x : "With ID" not in x[0], [getUserName(user.userID) for user in UserAlerts.query.filter_by(alertID = alert.alertID).filter_by(viewed = False).all()]))
        alerts.append({"id": alert.alertID, 
                       "role" : alert.role,
                       "title" : alert.title,
                       "viewed" : viewed, 
                       "notViewed" : notViewed })
        

    return render_template("alert_status.html", alerts = alerts, dismiss_alerts=dismiss_alerts)

@app.route('/admin_send_email')
@login_required
def admin_send_emails():
    check_maintenance()
    return render_template("admin_send_emails.html")

@app.route('/payslips')
@login_required
def payslips():
    check_maintenance()
    if current_user.is_student(): 
        abort(400, )
            
    try: 
        userID = request.args['userID']
        if userID != current_user.id and getRoleLevel(getUserRole(current_user.id)) >= getRoleLevel(getUserRole(userID)):  
            permission_required(current_user.id, "view_below_payslips", fatal=True)
        else: 
            abort(400, )
    except:
        userID = current_user.id  

    upload = (permission_required(current_user.id, 'upload_payslips') and getRoleLevel(getUserRole(current_user.id)) > getRoleLevel(getUserRole(userID))) or (current_user.is_admin())
    
    name = getUserName(userID)
    
    
    # if current_user.is_tutor():
    #     try: 
    #         tutorID = request.args['tutorID']
    #         tutorIDCheck = getOtherID("tutor", current_user.id)
    #         if tutorID != tutorIDCheck:
    #             db.session.add(log(role = getUserRole(current_user.id), message= f" ({getUserName(current_user.id)}): has just tried to view {getTutor(tutorID)}'s payslips but was denied", date=datetime.utcnow()))
    #             db.session.commit()
    #             abort(400, ""), 
    #     except:
    #         tutorID = getOtherID("tutor", current_user.id)
    # else: 
    #     tutorID = request.args['tutorID']
    #     if current_user.id == 453 or current_user.id == 376:
    #         db.session.add(log(role = getUserRole(current_user.id), message= f" ({getUserName(current_user.id)}): has just tried to view {getTutor(tutorID)}'s payslips but was denied", date=datetime.utcnow()))
    #         db.session.commit()
    #         abort(400, )




    path = "/var/www/webApp/webApp/payslips"

    path = os.path.join(path, str(userID))
    if isdir(path):
        payslips = [{"type" : getFileType(f)[1:], "name" : f} for f in listdir(path) if isfile(join(path, f))]
    else:
        payslips = []

    return render_template("payslips.html", payslips = payslips, id=userID, upload=upload, name = name)

@app.route("/report_cards")
@login_required
def report_cards():
    check_maintenance()
    return render_template('report_cards.html')

@app.route("/automatic_maths_marker")
@login_required
def mathsMarker(): 
    check_maintenance()
    return render_template("maths_marker.html")

@app.route("/view_feedback")
@login_required
def view_feedback(): 
    check_maintenance()
    feedback_list = Feedback.query.all()
    feedback = [{"file" : response.filename.replace("/var/www/webApp/webApp/", ""), "student" : getStudent(response.studentID), "feedback" : response.feedback, "student_good" : response.student_good, "tutor_good" : response.tutor_good, "correct" : "Correct" if response.correct else "Incorrect" } for response in feedback_list]

    return render_template("view_feedback.html", feedback = sorted(feedback, key = lambda x:x['file'] ,reverse=True))

@app.route("/view_exams")
@login_required
def view_exams():
    check_maintenance()
    return render_template("view_exams.html")

@app.route("/centre_overview")
@login_required
def centre_overview():
    check_maintenance()
    #role_required("admin", "Centre Overview")
    
    centreList = Centre.query.all()
    centres = []
    for centre in centreList:
        centres.append({"admin" : getStaff(centre.admin_id), "name" : centre.name, "room_number" : centre.room_number, "address" : centre.address, "centreID" : centre.centreID})
        
    return render_template("centre_overview.html", centres = sorted(centres, key=lambda x:x['name']), staffs=getAll('staff'))

@app.route("/exam_room_allocation", methods=["GET"])
@login_required
def exam_calendar():
    check_maintenance()

    # Get all exam papers
    papers = ExamPapers.query.all()
    
    exam_data = []
    for paper in papers:
        exam_info = Exams.query.filter_by(examID=paper.examID).first()
        if exam_info:
            # Get students registered for this exam
            registered_students = studentExam.query.filter_by(examID=exam_info.examID).all()
            student_ids = [getStudent(student.studentID) for student in registered_students]
            
            exam_data.append({
                'examID': exam_info.examID,
                'paperNo': paper.paperNo,
                'paperCode': paper.paperCode,
                'date': paper.date.strftime('%Y-%m-%d') if paper.date else "--/--/--",  # Ensure correct date format
                'startTime': paper.startTime.strftime('%H:%M:%S') if paper.startTime else "--:--",  # Ensure correct time format
                'duration': paper.duration,
                'total': paper.total,
                'extra_info': paper.extra_info,
                'title': exam_info.title,
                'tier': exam_info.tier,
                'examBoard': exam_info.examBoard,
                'registered_students': student_ids  # Add registered students
            })

    centres = [{'id': c.centreID, 'name': c.name} for c in Centre.query.order_by(Centre.name).all()]
    return render_template("exam_room_allocation.html", exam_data=exam_data, centres=centres)


def _gather_clash_entries(centre_id=None, student_id=None):
    """One entry per (candidate, dated paper) registration, for clash detection.

    Everything is bulk-loaded up front (and scoped to one student when
    student_id is given) so the loop below never queries per row.
    """
    exams_by_id = {e.examID: e for e in Exams.query.all()}
    centre_names = {c.centreID: c.name for c in Centre.query.all()}

    reg_query = studentExam.query
    profile_query = exam_student.query
    if student_id is not None:
        reg_query = reg_query.filter_by(studentID=student_id)
        profile_query = profile_query.filter_by(studentID=student_id)
    regs_by_exam = {}
    for reg in reg_query.all():
        regs_by_exam.setdefault(reg.examID, []).append(reg.studentID)
    profiles = {p.studentID: p for p in profile_query.all()}

    entries = []
    names = {}
    for paper in ExamPapers.query.all():
        if paper.date is None:
            continue  # unscheduled papers can't clash
        exam = exams_by_id.get(paper.examID)
        exam_label = f"{exam.examBoard} {exam.tier} {exam.title}" if exam else f"Exam {paper.examID}"
        for sid in regs_by_exam.get(paper.examID, []):
            profile = profiles.get(sid)
            s_centre = profile.centreID if profile else None
            if centre_id and s_centre != centre_id:
                continue
            if sid not in names:
                names[sid] = getStudent(sid)
            entries.append({
                'student_id': sid,
                'name': names[sid],
                'candidate_number': profile.candidate_number if profile else None,
                'centre': centre_names.get(s_centre),
                'exam_id': paper.examID,
                'exam': exam_label,
                'paper_code': paper.paperCode,
                'paper_no': paper.paperNo,
                'date': paper.date,
                'start': paper.startTime,
                'duration': paper.duration,
            })
    return entries


@app.route('/exam_clashes')
@login_required
def exam_clashes():
    check_maintenance()
    centre_id = _resolve_centre_id(request.args.get('centre'))

    clash_list = group_clashes(_gather_clash_entries(centre_id))
    for clash in clash_list:
        clash['date_str'] = clash['date'].strftime('%a %d %b %Y')
        for p in clash['papers']:
            p['time_str'] = time_range_str(clash['date'], p['start'], p['duration'])

    overlap_count = sum(1 for c in clash_list if c['severity'] == 'overlap')
    centres = Centre.query.order_by(Centre.name).all()
    return render_template('exam_clashes.html',
                           clashes=clash_list,
                           overlap_count=overlap_count,
                           same_day_count=len(clash_list) - overlap_count,
                           centres=centres,
                           selected_centre=centre_id)

@app.route("/approveHours")
@login_required
def approve_hours():
    check_maintenance()
    permission_required(current_user.id, 'approve_hours', fatal=True)
    
    lessons = getLessonsToApprove()
    shifts = []
    for lesson in lessons:
        shifts.append({"tutor" : getStaff(lesson.tutorID), 
                       "day" : lesson.day, 
                       "startTime": lesson.startTime, 
                       "weekNo" : lesson.weekNo, 
                       "duration" : lesson.duration, 
                       "register" : lesson.register, 
                       "homework" : lesson.homework, 
                       "description" : lesson.description, 
                       "id" : lesson.lessonID                       
                       })    
        
    shifts = sorted(sorted(shifts, key=lambda x:x['weekNo']), key=lambda x:x['tutor'])
        
    otherHours = staffHours.query.filter_by(approved = False).all()
    
    for log in otherHours: 
        shifts.append({"tutor" : getStaff(log.staffID), 
                       "day" : "-", 
                       "startTime": "-", 
                       "weekNo" : log.date, 
                       "duration" : log.hours, 
                       "register" : True, 
                       "homework" : True, 
                       "description" : log.description, 
                       "id" : log.id             
        })
    
    return render_template('approve_hours.html', shifts = shifts)

@app.route("/calendar")
@login_required
def calendar_view():
    check_maintenance()
    events = getEvents(current_user.id)
    bookable_events = getBookableEvents()

    events = events + bookable_events

    userList = getAllCurrent('all')
    users = [{'id' : user.id, 'role' : user.role, 'otherID' : user.otherID, 'name' : getUserName(user.id)} for user in userList if user.id != current_user.id ]
    roles = getAllRoles()
        

    return render_template('calendar.html', events=events, 
                                            roles = roles, 
                                            users = sorted(sorted(users, key=lambda x:x['name']), 
                                            key = lambda x:x['role']), 
                                            create_alerts = permission_required(current_user.id, 'create_events'), 
                                            bookable_events = bookable_events)

@app.route("/staff_members_view")
@login_required
def staff_member_view():
    check_maintenance()
    # permission_required(current_user.id, 'view_staff', fatal=True)

    staffList = Staff.query.all()
    staffs = []

    for staff in staffList:
        if staff.role != 'tutor':
            staffs.append({"id" : getUserID(staff.role, staff.id), "firstName" : staff.firstName, "secondName" : staff.secondName, "gender" : staff.gender, "email" : staff.email, "phone" : staff.phone, "logOn" : getUserPermission(id = staff.id, action = "log_on", role = staff.role)})
    

    return render_template("view_staff_members.html", staffs = sorted(staffs, key=lambda x: x['logOn'], reverse =True))

@app.route("/begin_game")
def begin_game():
    questions = gameQuestions.query.all()
    questions = [{"question" : question.question, "correctAnswer" : question.correctAnswer, "answer2" : question.answer2, "answer3" : question.answer3, "answer4" : question.answer4} for question in questions]
    random.shuffle(questions)  # Randomize the order of questions
    return render_template("begin_game.html", questions = questions)

@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")

@app.route("/game_questions", methods = ['POST', 'GET'])
def game_questions():
    return render_template('game_questions.html')

@app.route('/myProfile')
@login_required
def myProfile(): 
    if current_user.is_student():
        return redirect('/student_profile')
    elif current_user.is_tutor(): 
        return redirect('/tutor_info')
    else:
        return redirect('staff_info')

@app.route('/contract/<tutorID>')
@login_required
def show_contract(tutorID):
    pdf_path = "/var/www/webApp/webApp/contracts/2_contract.pdf"
    
    if not os.path.exists(pdf_path):
        return f'Contract for tutor ID {tutorID} not found.', 404

    contract = extract_text(pdf_path)
    return render_template('tutor_contract.html', contract=contract)

@app.route('/document')
@login_required
def document():
    return render_template('document.html')

@app.route('/marketplace', methods=['GET', 'POST'])
@login_required
def marketplace():
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx'}

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    create_marketplace_products = permission_required(current_user.id, 'create_marketplace_products')
    
    if request.method == 'POST':
        if not permission_required(current_user.id, 'create_marketplace_products'):
            flash('You do not have permission to create products.')
            return redirect(url_for('marketplace'))
        
        name = request.form['name']
        reward = request.form['reward']
        description = request.form['description']
        
        new_product = Product(name=name, reward=reward, description=description)
        db.session.add(new_product)
        db.session.commit()
        
        # Create a directory for the new product files
        product_folder = os.path.join('/var/www/webApp/webApp/marketPlaceFiles', str(new_product.id))
        os.makedirs(product_folder, exist_ok=True)
        
        # Save uploaded files
        files = request.files.getlist('files')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(product_folder, filename)
                file.save(file_path)
        
        flash('Product created successfully.')
    
    products = Product.query.all()
    
    # Gather files for each product
    products_with_files = []
    for product in products:
        product_folder = os.path.join('/var/www/webApp/webApp/marketPlaceFiles', str(product.id))
        if os.path.exists(product_folder):
            files = [filename for filename in os.listdir(product_folder) if allowed_file(filename)]
        else:
            files = []
        products_with_files.append((product, files))
    
    # Get claimed products for the current user
    product_files = {}
    claimed_products = Product.query.filter_by(user_id=current_user.id).all()
    for product in claimed_products:
        product_folder = os.path.join('/var/www/webApp/webApp/marketPlaceFiles', str(product.id))
        if os.path.exists(product_folder):
            files = [filename for filename in os.listdir(product_folder) if allowed_file(filename)]
        else:
            files = []
        product_files[product.id] = files
    
    return render_template('marketplace.html', products_with_files=products_with_files, claimed_products=claimed_products, create_marketplace_products=permission_required(current_user.id, 'create_marketplace_products'), product_files = product_files)

@app.route('/marketplaceFiles/<int:product_id>/<filename>')
@login_required
def uploaded_file(product_id, filename):
    return send_from_directory(os.path.join('/var/www/webApp/webApp/marketPlaceFiles', str(product_id)), filename)

@app.route('/create_booking_event', methods=['GET', 'POST'])
@login_required
def create_booking_event():
    permission_required(current_user.id, 'create_events')
     
    if request.method == 'POST':
        name = request.form['name']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
        end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
        duration = int(request.form['duration'])
        location = request.form['location']
        description = request.form['description']
        
        event = BookableEvent(name=name, date=date, start_time=start_time, end_time=end_time, duration=duration, location=location, description=description)
        db.session.add(event)
        db.session.commit()
        
        flash('Event created successfully!')
        db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}): bookable event with title: {name} on {date} was just created" , date=datetime.utcnow()))
        db.session.commit()
        return redirect(url_for('create_booking_event'))
    
    return render_template('create_booking_event.html', events = sorted(getAllBookableEvents(), key = lambda x:x.bookable, reverse = True))

@app.route('/book_event', methods=['GET', 'POST'])
def book_event():
    if request.method == 'POST':
        event_id = request.form['event']
        start_time = request.form['start_time']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        
        event = BookableEvent.query.get(event_id)
        booking = Booking(event_id=event_id, start_time=start_time, name=name, email=email, phone=phone.replace(" ", "").replace("(", "").replace(")", "").replace("+", ""))
        db.session.add(booking)
        db.session.commit()
        
        e1 = EmailSender()
        e1.send(email = email, subject = "Booking Confirmation",message = render_template('confirmation_email.html', 
                              event_name=event.name, 
                              event_date=event.date, 
                              start_time=start_time, 
                              location=event.location, 
                              description=event.description, 
                              name = name))
        
        flash('Booking confirmed! A confirmation email has been sent.')
        return "Booking Successful"
    
    events = BookableEvent.query.filter_by(bookable=True).all()
    formatted_events = []

    
    for event in events:
        formatted_date = event.date.strftime('%d/%m/%Y')
        formatted_events.append({
            'id': event.id,
            'name': event.name,
            'date': formatted_date,
            'start_time': event.start_time,
            'end_time': event.end_time,
            'duration': event.duration,
            'location': event.location,
            'description': event.description
        })
    

    
    selected_event = events[0] if events else None
    available_times = []
    if selected_event:
        available_times = generate_available_times(selected_event)
    
    return render_template('book_event.html', events=formatted_events, available_times=available_times)


@app.route('/get_available_times/<int:event_id>', methods=['GET'])
def get_available_times(event_id):
    event = BookableEvent.query.get(event_id)
    if event:
        available_times = generate_available_times(event)  # Assuming this function returns a list of times
        return jsonify(available_times)
    else:
        return jsonify([]), 404

def generate_available_times(event):
    start_time = datetime.combine(event.date, event.start_time)
    end_time = datetime.combine(event.date, event.end_time)
    available_times = []
    current_time = start_time
    while current_time + timedelta(minutes=event.duration) <= end_time:
        time_str = current_time.time().strftime('%H:%M')
        if not Booking.query.filter_by(event_id=event.id, start_time=time_str).first():
            available_times.append(time_str)
        current_time += timedelta(minutes=event.duration)
    return available_times

@app.route('/register_exam_interest')
def iframe():
    # Structured options for the public registration form: the exams we actually
    # run (grouped by qualification client-side) and the centres we sit them at,
    # so parents pick from real entries instead of describing them in free text.
    exam_options = []
    for exam in Exams.query.filter_by(active=True).order_by(Exams.tier, Exams.title).all():
        label = " ".join(part for part in [exam.tier, exam.title, exam.examBoard, exam.Option] if part)
        if exam.code:
            label += f" ({exam.code})"
        exam_options.append({'examID': exam.examID, 'tier': exam.tier or 'Other', 'label': label})
    centres = [{'id': c.centreID, 'name': c.name} for c in Centre.query.order_by(Centre.name).all()]
    return render_template('iframe_exam_student.html', exam_options=exam_options, centres=centres)

@app.route('/enquiry', methods=['GET', 'POST'])
@login_required
def enquiry():
    permission_required(current_user.id, 'view_enquiries', fatal = True)

    if request.method == 'POST':
        callerName = request.form['caller_name']
        studentName = request.form['student_name']
        year_group = request.form['year_group']
        location = request.form.get('location')
        if location:
            location = int(location)
        else:
            location = None
        parent_email = request.form['parent_email']
        contact_number = request.form['contact_number']
        enquiry_info = request.form['enquiry_info']
        result = request.form['result']

        # Create a new Enquiry object and add it to the database
        new_enquiry = Enquiry(
            callerName=callerName,
            studentName=studentName,
            year_group=year_group,
            location=location,
            parent_email=parent_email,
            contact_number=contact_number,
            enquiry_info=enquiry_info,
            result=result,
            userID=current_user.id  # Associate with the current user
        )

        db.session.add(new_enquiry)
        db.session.commit()

        db.session.add(log(role = getUserRole(current_user.id), message=f" ( {getUserName(current_user.id)} ): has just logged an Enquiry", date=datetime.utcnow()))
        db.session.commit()

        return redirect(url_for('enquiry'))
    
    centres = Centre.query.all()
    

    return render_template('enquiry_form.html', centres = centres)

@app.route('/enquiries', methods=['GET', 'POST'])
@login_required
def enquiries():
    permission_required(current_user.id, 'view_enquiries', fatal = True)

    if request.method == 'POST':
        enquiry_id = request.form.get('enquiry_id')
        escalated_user_id = request.form.get('escalated_user_id')
        
        enquiry = Enquiry.query.get(enquiry_id)
        enquiry.escalated = True
        enquiry.escalated_user = escalated_user_id
        db.session.commit()

        db.session.add(log(role = getUserRole(current_user.id), message=f" ( {getUserName(current_user.id)} ): has just escalated an Enquiry to {getUserName(escalated_user_id)}", date=datetime.utcnow()))
        db.session.add(LittleAlerts(userID = escalated_user_id, message= f" An Enquiry has been escalated to you - please see the enquiries page for more information" ))
        
        e1 = EmailSender()
        e1.send(getUserEmail(escalated_user_id), 'Escalated Enquiry', 'An Enquiry has been escalated to you, please check your enquirires page', subtype='plain')
        
        db.session.commit()
        
        return redirect(url_for('enquiries'))

    all_enquiries = Enquiry.query.filter(Enquiry.result != 'Complete').all()
    all_enquiries = [ { **enquiry.__dict__,'user_name': getUserName(enquiry.userID), 'escalated_user_name' : getUserName(enquiry.escalated_user)} for enquiry in all_enquiries]
    completed_enquiries = Enquiry.query.filter(Enquiry.result == 'Complete').all()
    completed_enquiries = [ { **enquiry.__dict__,'user_name': getUserName(enquiry.userID)} for enquiry in completed_enquiries]
    escalated_enquiries = Enquiry.query.filter_by(escalated=True).filter_by(escalated_user = current_user.id).filter(Enquiry.result != 'Complete').all()
    escalated_enquiries = [ { **enquiry.__dict__,'user_name': getUserName(enquiry.userID)} for enquiry in escalated_enquiries]
    
    staff_members = getAll(role="staff", log_on=True)
    centres = Centre.query.all()
    results_list = ["Complete" , "Booked trial Lesson" , "Will book a trial lesson" , "unknown" , "Pending" , "Will Book Exam" , "Exam Booked"]
    
    return render_template('enquiries.html', 
                           enquiries=sorted(all_enquiries, key=lambda x:x['escalated']), 
                           staff=staff_members,
                           centres=centres,
                           results_list=results_list, 
                           escalated_enquiries = escalated_enquiries, 
                           completed_enquiries = completed_enquiries)

@app.route('/log_hours', methods=['GET', 'POST'])
@login_required
def log_hours():
    if current_user.is_student() or current_user.is_parent():
        abort(400)

    if request.method == 'POST':
        staff_id = getOtherID(getUserRole(current_user.id), current_user.id)
        date = request.form['date']
        hours = request.form['hours']
        description = request.form['description']


        # Create a new staffHours entry
        new_hours = staffHours(staffID=staff_id, date = date, hours=hours, description=description)

        # Add to the session and commit
        db.session.add(new_hours)
        db.session.commit()
        
        db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}): just logged {str(hours)} hours" , date=datetime.utcnow()))
        db.session.commit()

        flash('Hours logged successfully', 'success')
        return redirect(url_for('log_hours'))
    return render_template('log_hours.html')

@app.route('/trial_registration', methods=['GET', 'POST'])
@login_required
def trial_registration():
    if current_user.is_student() or current_user.is_parent():
        abort(403)

    lessonList = Lesson.query.filter_by(active=True, weekNo=-1, AcademicYear=gen_academic_year()).all()
    lessons = [{
        'id': lesson.lessonID,
        'tier': getTier(lesson.subjectID),
        'title': getTitle(lesson.subjectID),
        'day': lesson.day,
        'time': str(lesson.startTime),
        'centre': getCentre(lesson.centreID)
    } for lesson in lessonList]

    students = Students.query.order_by(Students.firstName).all()

    return render_template('trial_registration.html', lessons=lessons, students=students)

@app.route('/ucas_reference', methods = ['POST', 'GET'])
def ucas_reference():
    return render_template('ucas_reference.html')

@app.route('/user_points', methods = ['POST', 'GET'])
@login_required
def user_points():
    users = getAllCurrent("all")

    return render_template('user_points.html', users=sorted(users, key=lambda x : x.points, reverse=True))

@app.route('/tutor_application', methods = ['POST', 'GET'])
def tutor_application():
    return render_template('tutor_application.html')

@app.route('/staff_reviews', methods = ['POST', 'GET'])
@login_required
def staff_reviews(): 
    staffList = getAllUsers('all_staff', log_on=True)
    return render_template('staff_reviews.html', staffList = sorted(staffList, key=lambda x:x.firstName ))

@app.route('/point_system')
@login_required
def point_system():
    points = PointSystem.query.all()
    return render_template('point_system.html', points=points)

@app.route('/exam_rooms', methods=['GET', 'POST'])
@login_required
def manage_exam_rooms():
    if request.method == 'POST':
        name = request.form.get('name')
        max_rows = int(request.form.get('max_rows'))
        max_columns = int(request.form.get('max_columns'))
        centre_id = _resolve_centre_id(request.form.get('centreID'))
        new_room = ExamRoom(name=name, max_rows=max_rows, max_columns=max_columns, centreID=centre_id)
        db.session.add(new_room)
        db.session.commit()
        flash("Exam room added successfully!", "success")
        return redirect(url_for('manage_exam_rooms'))

    rooms = ExamRoom.query.all()
    centres = Centre.query.order_by(Centre.name).all()
    centre_names = {c.centreID: c.name for c in centres}
    return render_template('exam_rooms.html', rooms=rooms, centres=centres,
                           centre_names=centre_names, is_admin=current_user.is_admin())

# Route to edit an existing exam room
@app.route('/edit_exam_room', methods=['GET', 'POST'])
@login_required
def edit_exam_rooms():
    room_id = request.args['room_id']
    room = ExamRoom.query.get_or_404(room_id)
    if request.method == 'POST':
        room.name = request.form.get('name')
        room.max_rows = int(request.form.get('max_rows'))
        room.max_columns = int(request.form.get('max_columns'))
        room.centreID = _resolve_centre_id(request.form.get('centreID'))

        db.session.commit()
        flash('Exam room updated successfully!', 'success')
        return redirect('/exam_rooms')

    centres = Centre.query.order_by(Centre.name).all()
    return render_template('edit_exam_room.html', room=room, centres=centres)

@app.route('/files_to_print', methods = ['GET', 'POST'])
@login_required
def files_to_print():
    # Get the current week number
    current_week_no = gen_week_no(0)
    
    # Fetch lessons for the current week or week -1
    lessons = Lesson.query.filter(
        Lesson.weekNo.in_([-1, current_week_no]),
        Lesson.active == True, 
        Lesson.AcademicYear == gen_academic_year(), 
        Lesson.centreID != 1
    ).all()
    
    # Sort lessons by day, center, then tutor
    days_order = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    lessons = sorted(
        lessons, 
        key=lambda x: (days_order.index(x.day.upper()), x.centreID, x.tutorID, int(str(x.startTime)[:2]))
    )
    
    # Fetch attendance data for the previous week
    attendance_week =  int(gen_week_no(0)) - 1
    student_attendance = StudentAttendance.query.filter_by(weekNo=attendance_week, present=True).all()
    unregistered_attendance = UnregisteredAttendance.query.filter_by(weekNo=attendance_week, present=True).all()
    temp_attendance = TempAttendance.query.filter_by(weekNo=attendance_week).all()

    # Calculate attendance by lesson ID
    attendance_count = {}
    for att in student_attendance + unregistered_attendance + temp_attendance:
        attendance_count[att.lessonID] = attendance_count.get(att.lessonID, 0) + 1

    # Fetch associated files
    files_data = {}
    for lesson in lessons:
        files = Files.query.filter(
            or_(
                Files.subjectID == lesson.subjectID,
                Files.lessonID == lesson.lessonID
            ),
            Files.weekNo == int(current_week_no)
        ).all()
        subject_folder = getFileFolder(lesson.subjectID)  # Function to get subject folder
        files_data[lesson.lessonID] = [
            [f"files/{subject_folder}/{file.filename}", file.filename, file.auto_print] for file in files if classTypeCheck(lesson, file.classtype)
        ]
        # print(getLessonString(lesson.lessonID))
        # print(lesson.lessonID)
        # print(files_data[lesson.lessonID])
        # print(files)
    
    # Format lesson data with attendance and files
    formatted_lessons = []
    for lesson in lessons:
        formatted_lessons.append({
            "day": lesson.day,
            "centre": getCentre(lesson.centreID),
            "tutor": getTutor(lesson.tutorID),
            "attendance": attendance_count.get(lesson.lessonID, 0),
            "files": files_data.get(lesson.lessonID, []),
            "name": getLessonString(lesson.lessonID)
        })

    return render_template('files_to_print.html', lessons=formatted_lessons)    # Get the current week and last week's week number

@app.route('/user_preferences', methods = ['POST', 'GET'])
@login_required
def user_preferences(): 

    themes = ['default', 'dark', 'green', 'red', 'neutral', 'purple', 'safwaans']


    return render_template('user_preferences.html', themes = themes)

@app.route('/email_templates', methods=['GET', 'POST'])
@login_required
def email_templates():
    permission_required(current_user.id, "send_emails_to_parents", fatal=True, message = "Tried to access Email Templates")
    templates_dir = '/var/www/webApp/webApp/templates/email_templates'

    # Handle file saving if the request is POST
    if request.method == 'POST':
        template_name = request.json.get('template_name')
        template_content = request.json.get('template_content')

        if not template_name or not template_content:
            return jsonify({"error": "Template name or content is missing."}), 400

        # Save the edited template
        file_path = os.path.join(templates_dir, template_name)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            return jsonify({"message": "Template updated successfully."}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Get all templates for GET request
    templates = [
        f for f in os.listdir(templates_dir)
        if os.path.isfile(os.path.join(templates_dir, f)) and f.endswith('.html')
    ]
    return render_template('email_templates.html', templates=templates)

@app.route('/email_templates/<template_name>', methods=['GET'])
@login_required
def view_email_template(template_name):
    try:
        # Ensure only files within the `templates/email_templates` folder are accessed
        template_path = f'/var/www/webApp/webApp/templates/email_templates/{template_name}'
        if not os.path.exists(template_path):
            return "Template not found", 404

        with open(template_path, 'r') as file:
            content = file.read()

        return Response(content, mimetype='text/plain')
    except Exception as e:
        return str(e), 500


@app.route('/save_email_templates/<template_name>', methods=['POST'])
@login_required
def update_email_template(template_name):
    try:
        template_path = f'/var/www/webApp/webApp/templates/email_templates/{template_name}'
        if not os.path.exists(template_path):
            return "Template not found", 404

        data = request.get_json()
        new_content = data.get('template_content')        
        if not new_content:
            return "No content provided", 400

        # Save the new content to the file
        with open(template_path, 'w') as file:
            file.write(new_content)

        return jsonify({"message": "Template updated successfully"})
    except Exception as e:
        print(str(e))
        return str(e), 500

@app.route('/easter_revision_booking', methods = ['POST', 'GET'])
def easter_revision_booking():
    return render_template('easter_booking.html')


@app.route('/view_event_registrations')
@login_required  # Ensure only admins can view this page
def view_event_registrations():
    registrations = EventRegistration.query.all()
    
    # Count total sign-ups for each event
    event_counts = defaultdict(int)
    for reg in registrations:
        for event in reg.events.split(", "):
            event_counts[event] += 1
    
    return render_template('event_registrations.html', registrations=registrations, event_counts=event_counts)




'           _____ _______ _____ ____  _   _  _____  '
'     /\   / ____|__   __|_   _/ __ \| \ | |/ ____| '
'    /  \ | |       | |    | || |  | |  \| | (___   '
'   / /\ \| |       | |    | || |  | | . ` |\___ \  '
'  / ____ \ |____   | |   _| || |__| | |\  |____) | '
' /_/    \_\_____|  |_|  |_____\____/|_| \_|_____/  '
'                                                   '

@app.route('/update_enquiry/<int:enquiry_id>', methods=['POST'])
@login_required
def update_enquiry(enquiry_id):
    field = request.json.get('field')
    value = request.json.get('value')
    
    if field == "location_id":
        value = int(value)

    stmt = update(Enquiry).values({field : value}).where(Enquiry.id == enquiry_id)
    db.session.execute(stmt)
    db.session.commit()

    return jsonify({'status': 'success'})

CORS(app, resources={r"/add_external_enquiry": {"origins": "https://ateamacademy.co.uk"}})
@app.route('/add_external_enquiry', methods=['POST'])
def addExternalEnquiry():
    if not request.is_json:
        return jsonify({"error": "Invalid input, JSON required"}), 400

    data = request.get_json()

    # Extract data from JSON
    callerName = data.get('caller_name')
    studentName = data.get('student_name')
    year_group = data.get('year_group')
    location = data.get('location', 6)  # Default location to 6 if not provided
    parent_email = data.get('parent_email')
    contact_number = data.get('contact_number')
    enquiry_info = data.get('enquiry_info')
    result = data.get('result', "pending")  # Default result to "pending" if not provided

    # Check for required fields
    if not all([callerName, studentName, year_group, parent_email, contact_number, enquiry_info]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Use a default user ID or handle absence of `current_user`
        user_id = current_user.id if hasattr(current_user, 'id') else None

        # Create a new Enquiry object and add it to the database
        new_enquiry = Enquiry(
            callerName=callerName,
            studentName=studentName,
            year_group=year_group,
            location=location,
            parent_email=parent_email,
            contact_number=contact_number,
            enquiry_info=enquiry_info,
            result=result,
            userID=user_id
        )

        db.session.add(new_enquiry)
        db.session.commit()

        # Log the action
        if user_id:
            db.session.add(log(
                role='anonymous',
                message=f"({callerName}): has just logged an Enquiry",
                date=datetime.utcnow()
            ))
            db.session.commit()

        return jsonify({"message": "Enquiry successfully created"}), 201

    except Exception as e:
        db.session.rollback()  # Rollback in case of any error
        return jsonify({"error": str(e)}), 500

@app.route('/get_little_alerts')
@login_required
def get_alerts():
    # Assuming user_id is stored in session
    user_id = current_user.id

    if user_id is None:
        return jsonify({'error': 'User not logged in'}), 401

    # Create a new SQLAlchemy session


    # Query non-viewed alerts for the current user
    alerts = LittleAlerts.query.filter_by(userID=user_id, viewed=False).all()

    # Format alerts for JSON response
    alerts_data = [{
        'date_time': alert.date_time.strftime('%B %d, %Y'),
        'message': alert.message
    } for alert in alerts]

    return jsonify(alerts_data)

@app.route("/addGameScore", methods=['POST', 'GET'])
def add_game_score():
    data = request.get_json()
    
    # Extract data from JSON
    name = data.get('name')
    email = data.get('email')
    score = data.get('score')
    image_data_url = data.get('image')

    # Save image as binary data (convert from base64)
    image_binary = base64.b64decode(image_data_url.split(',')[1])

    # Save game score to database
    game_score = GameScores(name=name, email=email, score=score, image=image_binary)
    db.session.add(game_score)
    db.session.commit()
    
    db.session.add(log(role = "anonymous", message=f" ( name ): has just added a game score to the A-Team Games", date=datetime.utcnow()))
    db.session.commit()

    return redirect('/begin_game')
    # return jsonify({'message': 'Game score added successfully'}), 200

@app.route('/getLeaderboard', methods=['POST', 'GET'])
def get_leaderboard():
    try:
        # Query for the top scorers, sorted by score descending
        leaderboard = GameScores.query.order_by(GameScores.score.desc()).limit(5).all()

        # Prepare leaderboard data to send as JSON
        leaderboard_data = []
        for player in leaderboard:
            # Convert BYTEA image data to base64 string for JSON serialization
            image_data = base64.b64encode(player.image).decode('utf-8') if player.image else None
            leaderboard_data.append({
                'name': player.name,
                'score': player.score,
                'image': image_data  # Send base64 encoded image data
            })

        return jsonify(leaderboard_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_questions', methods=['GET'])
def get_questions():
    questions = gameQuestions.query.all()
    questions_data = [{
        'question': question.question,
        'correctAnswer': question.correctAnswer,
        'answer2': question.answer2,
        'answer3': question.answer3,
        'answer4': question.answer4
    } for question in questions]
    
    return jsonify(questions_data)

@app.route('/add_question', methods=['POST'])
def add_question():
    data = request.get_json()
    new_question = gameQuestions(
        question=data['question'],
        correctAnswer=data['correctAnswer'],
        answer2=data['answer2'],
        answer3=data['answer3'],
        answer4=data['answer4']
    )
    db.session.add(new_question)
    
    
    db.session.add(log(role = getUserRole(current_user.id), message=f" ( {getUserName(current_user.id)} ): has just added a question to the A-Team Games", date=datetime.utcnow()))
    db.session.commit()
    return ""

@app.route('/claim_product/<int:product_id>', methods=['POST'])
@login_required
def claim_product(product_id):
    if current_user.is_student() or current_user.is_parent():
        abort(403, )
        
    product = Product.query.get(product_id)
    if product and not product.sold:
        product.sold = True
        product.user_id = current_user.id
        db.session.commit()
        flash('Product claimed successfully.')
    else:
        flash('Product could not be claimed.')


    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}): has just claimed the task: {getProduct(product_id)}", date=datetime.utcnow()))
    db.session.commit()

    return redirect(url_for('marketplace'))

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    permission_required(current_user.id, 'create_marketplace_products', fatal=True) 
       
    product = Product.query.get(product_id)
    if product:
        # Delete the product folder and its contents
        product_folder = os.path.join('/var/www/webApp/webApp/marketPlaceFiles', str(product.id))
        if os.path.exists(product_folder):
            import shutil
            shutil.rmtree(product_folder)
        
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully.')
    else:
        flash('Product not found.')


    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}): has just deleted the product: {getProduct(product_id)}", date=datetime.utcnow()))
    db.session.commit()
    
    return redirect(url_for('marketplace'))

@app.route('/fetch-events')
@login_required
def fetch_events():
    user_events = UserEvents.query.filter_by(userID=current_user.id).all()
    events = []
    for user_event in user_events:
        event = Events.query.get(user_event.eventID)
        events.append({
            'title': event.title,
            'start': event.date.isoformat(),
            'description': event.description
        })
    return jsonify(events)

@app.route('/create-event', methods=['POST'])
@login_required
def create_event():
    permission_required(current_user.id, 'create_events', fatal=True)

    data = request.get_json()
    title = data['title']
    date = data['date']
    description = data['description']
    user_ids = data.get('user_ids', [])
    roles = data.get('roles', [])
    

    new_event = Events(date=date, title=title, description=description)
    db.session.add(new_event)
    db.session.commit()

    db.session.add(UserEvents(userID = current_user.id, eventID = new_event.id))

    for user_id in user_ids:
        user_event = UserEvents(userID=user_id, eventID=new_event.id)
        db.session.add(user_event)
        db.session.add(LittleAlerts(userID = user_id, message= f" You have been added to the event:  {title} on {date}!" ))

    for role in roles: 
        roleEvent = RoleEvent(role = role, eventID = new_event.id)
        db.session.add(roleEvent)
        createLittleAlertForRole(role = role, message = f" You have been added to the event:  {title} on {date} for all {role}s ")
        
    
    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}): event with title: {title} on {date} was just created" , date=datetime.utcnow()))
    db.session.commit()

    return jsonify({"success": "Event created successfully"})

@app.route('/update-event', methods=['POST'])
@login_required
def update_event():
    permission_required(current_user.id, 'create_events', fatal = True)
    data = request.get_json()
    event_id = data.get('id')
    title = data.get('title')
    date = data.get('date')
    description = data.get('description')

    event = Events.query.get(event_id)
    if event:
        event.title = title
        event.date = date
        event.description = description
        db.session.commit()
        return jsonify({'status': 'success'})

    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}): event with title: {title} on {date} was just updated with new information" , date=datetime.utcnow()))
    db.session.commit()

    return jsonify({'status': 'error', 'message': 'Event not found'}), 404

@app.route('/delete-event/<int:event_id>', methods=['DELETE'])
@login_required
def delete_event(event_id):
    permission_required(current_user.id, 'create_events', fatal = True)
    event = Events.query.get(event_id)

    
    if event:
        
        stmt = delete(RoleEvent).where(RoleEvent.eventID == event_id)
        db.session.execute(stmt)
        
        stmt = delete(UserEvents).where(UserEvents.eventID == event_id)
        db.session.execute(stmt)
        
        db.session.delete(event)
        db.session.commit()

        db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}): {getEvent(event_id)} was just deleted" , date=datetime.utcnow()))
        db.session.commit()
        
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Event not found'}), 404

@app.route("/addUserToEvent/<eventID>", methods=['POST'])
@login_required
def save_event_changes(eventID):
    check_maintenance()
    permission_required(current_user.id, "edit_event_details")

    data = request.get_json()
    roles = data.get('roles', [])
    users = data.get('users', [])

    if not eventID:
        return jsonify({'status': 'error', 'message': 'Event ID is required'}), 400

    # Add new rolesd
    for role in roles:
        role_event = RoleEvent(role=role, eventID=eventID)
        db.session.add(role_event)

    # Add new users
    for user_id in users:
        user_event = UserEvents(userID=user_id, eventID=eventID)
        db.session.add(user_event)

    
    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}): the following roles: {', '.join(roles)} and users {', '.join(users)} have just been added to {getEvent(eventID)}" , date=datetime.utcnow()))
    db.session.commit()

    return jsonify({'status': 'success'})

@app.route("/deleteRole", methods = ['POST', 'GET'])
@login_required
def deleteRole():
    permission_required(current_user.id, 'create_alerts', fatal=True, message='Tried to delete a role from an event')
    data = request.get_json()
    role = data['role']
    eventID = data['eventID']
    
    stmt = delete(RoleEvent).where(and_(RoleEvent.role == role, RoleEvent.eventID == eventID))
    db.session.execute(stmt)
    db.session.commit()

    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}): the {role} role has just been removed from {getEvent(eventID)}" , date=datetime.utcnow()))
    db.session.commit()
    
    return jsonify({"status" : "success"}), 200

@app.route("/delete_event_user", methods = ['POST', 'GET'])
@login_required
def delete_event_user():
    permission_required(current_user.id, 'create_alerts', fatal=True, message='Tried to delete a role from an event')
    data = request.get_json()
    userID = data['userID']
    eventID = data['eventID']
    
    stmt = delete(UserEvents).where(and_(UserEvents.userID == userID, UserEvents.eventID == eventID))
    db.session.execute(stmt)
    db.session.commit()

    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}): {getUserName(userID)} has just been removed from {getEvent(eventID)}" , date=datetime.utcnow()))
    db.session.commit()
    
    return jsonify({"status" : "success", "success" : True}), 200

@app.route('/add_event_user', methods=['POST'])
@login_required
def add_event_user():
    permission_required(current_user.id, 'create_alerts', fatal=True, message='Tried to delete a role from an event')

    data = request.get_json()
    event_id = data.get('eventID')
    user_id = data.get('userID')


    if not event_id or not user_id:
        return jsonify({"success": False, "message": "Invalid data provided."}), 400

    new_user_event = UserEvents(userID=user_id, eventID=event_id)
    db.session.add(new_user_event)

    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}): {getUserName(user_id)} has just been removed from {getEvent(event_id)}" , date=datetime.utcnow()))
    db.session.commit()

    return jsonify({"success": True, "message": "User added successfully!"})

@app.route('/add_event_role', methods=['POST'])
@login_required
def add_event_role():
    permission_required(current_user.id, 'create_alerts', fatal=True, message='Tried to delete a role from an event')

    data = request.get_json()
    event_id = data['eventID']
    role = data['role']

    if not event_id or not role:
        return jsonify({"success": False, "message": "Invalid data provided."}), 400

    new_role_event = RoleEvent(role=role, eventID=event_id)
    db.session.add(new_role_event)

    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}): {role} has just been removed from {getEvent(event_id)}" , date=datetime.utcnow()))    
    db.session.commit()

    return jsonify({"success": True, "message": "Role added successfully!"})


@app.route("/good_response", methods=['POST', 'GET'])
@login_required
def good_response(): 
    check_maintenance()
    data = request.get_json()

    filename = Feedback.query.order_by(Feedback.filename).all()[-1].filename
    
    if data['value'] == "true":
        result = True
    else:
        result = False

    if data['type'] == "student":
        stmt = update(Feedback).values({"student_good" : result}).where(Feedback.filename == filename)
    elif data['type'] == "tutor":
        stmt = update(Feedback).values({"tutor_good" : result}).where(Feedback.filename == filename)

    db.session.execute(stmt)
    db.session.commit()
    
    return ""

@app.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    check_maintenance()
    # db.session.add(log(role = getUserRole(current_user.id), message= getUserName(current_user.id) + " has just Logged Out", date=datetime.utcnow()))
    db.session.commit()
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return redirect('/')

@app.route('/recordAttendance', methods = ['POST'])
@login_required
def recordAttendance():
    check_maintenance()
    #role_required("tutor", "ACTION: record Attendance")
    data = request.get_json()
    student_Attendance = data['studentAttendance']
    description = data['description']
    lessonID = request.args['lessonid']
    year = request.args['year']
    weekNo = request.args['weekNo']
    
    if int(weekNo) > int(gen_week_no(0)) and not current_user.is_admin():
        return "<p> Cannot update register in the future </p>"
    
    if current_user.is_admin() or (int(getRoleLevel(getUserRole(current_user.id)) > int(getRoleLevel('tutor')))):
        tutorID = Lesson.query.filter_by(lessonID = lessonID).first().tutorID #Temp-Tutor
    else:
        tutorID = int(request.args['tutorID'])
    # print("student_attendance in recordAttendance is: ", student_Attendance)
    
    for student in student_Attendance:
        #print(student[0])
        if "temp-" in str(student[0]):
            if "undefined" in str(student[0]):
                continue
            db.session.add(TempAttendance(name = student[0], lessonID=lessonID, weekNo = weekNo, AcademicYear=year))
            db.session.commit()
            # f = open('/var/www/webApp/webApp/tempStudents.txt', "a")
            # f.write("lesson-" + lessonID + "-" + "week-" + weekNo + "-" + student[0] + "\n")
            # f.close()
            continue
            
        if "(unreg" in str(student[0]):
            #print("doing unreg stuff on: " + str(student[0]))
            # print("the extra notes are: " + student[2])
            if(student[1] == True):
                stmt = update(UnregisteredAttendance).values({"present" : True, "extra_notes" : student[2]}).where( and_(and_(and_(UnregisteredAttendance.lessonID == lessonID, UnregisteredAttendance.AcademicYear == year), UnregisteredAttendance.weekNo == weekNo), UnregisteredAttendance.studentName == student[0][14:])) 
                db.session.execute(stmt)
                db.session.commit()
            else: 
                stmt = update(UnregisteredAttendance).values({"present" : False, "extra_notes" : student[2]}).where( and_(and_(and_(UnregisteredAttendance.lessonID == lessonID, UnregisteredAttendance.AcademicYear == year), UnregisteredAttendance.weekNo == weekNo), UnregisteredAttendance.studentName == student[0][14:]))
                db.session.execute(stmt)
                db.session.commit()
            continue
        
        if(student[1] == True):
            stmt = update(StudentAttendance).values({"present" : True, "extra_notes" : student[2]}).where( and_(and_(and_(StudentAttendance.lessonID == lessonID, StudentAttendance.AcademicYear == year), StudentAttendance.weekNo == weekNo), StudentAttendance.studentID == student[0])) 
            db.session.execute(stmt)
            db.session.commit()
        else: 
            stmt = update(StudentAttendance).values({"present" : False, "extra_notes" : student[2]}).where( and_(and_(and_(StudentAttendance.lessonID == lessonID, StudentAttendance.AcademicYear == year), StudentAttendance.weekNo == weekNo), StudentAttendance.studentID == student[0]))
            db.session.execute(stmt)
            db.session.commit()
    
    lessonExists = LessonInfo.query.filter_by(lessonID=lessonID).filter_by(weekNo=weekNo).first()
    
    if lessonExists is not None: 
        stmt = update(LessonInfo).values({"tutorID" : tutorID, "register" : True, "description" : description, "rejected" : False}).where(and_(LessonInfo.lessonID==lessonID, LessonInfo.weekNo==weekNo))
        db.session.execute(stmt)
        db.session.commit()
    else:
        db.session.add(LessonInfo(lessonID=lessonID, tutorID=tutorID, weekNo=weekNo, register=True, homework=False, dismissed=False, description = description))
        db.session.commit()
        updatePoints(getUserID(getStaffRole(tutorID), tutorID), getPointsAmount(f'register_completion_after_{getDaysSinceLesson(lessonID, weekNo)}_days'))
        
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): Register for " + getLessonString(lessonID) + " has just been updated for week " + weekNo, date=datetime.utcnow()))
    db.session.commit()
    return ""

@app.route('/removeTempStudentAttendance', methods = ['POST', 'GET'])
@login_required
def removeTempStudentAttendance():
    check_maintenance()
    # #role_required("tutor", "ACTION: remove temp student Attendance")
    
    data = request.get_json()
    name = data['name']
    lessonID = data['lessonID']
    weekNo = data['weekNo']
    year = data['year']
    
    temp = TempAttendance.query.filter_by(name=name).filter_by(lessonID=lessonID).filter_by(weekNo = weekNo).filter_by(AcademicYear=year).first()
    
    if temp is not None:
        db.session.delete(temp)
        db.session.commit()       
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + name + " has just been removed from the register for " + getLessonString(lessonID) + " for week " + weekNo, date=datetime.utcnow()))
    db.session.commit()
    return ""

@app.route('/removeUnregistered', methods=['POST', 'GET'])
@login_required
def removeUnregistered():
    check_maintenance()
    # #role_required("tutor", "ACTION: remove unregistered")
    permission_required(current_user.id, "change_lesson_students")
    data = request.get_json()
    
    id = data['id']
    lessonID = data['lessonID']
    
    stmt = delete(unregisteredStudentLessons).where(and_(unregisteredStudentLessons.studentName == id, unregisteredStudentLessons.lessonID == lessonID))
    db.session.execute(stmt)
    db.session.commit()
    
    return ""
    
@app.route('/removeTemps')
@login_required
def removeTemps():
    check_maintenance()
    #role_required("tutor", "ACTION: remove Temps")
    id = request.args['id']
    if id == "-1":
        TempStudent.query.delete()
        db.session.commit()
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): All Temporary Students Were Removed", date=datetime.utcnow()))
        db.session.commit()

    else:
        name = TempStudent.query.filter_by(id = int(id)).first().firstName
        db.session.delete(TempStudent.query.filter_by(id = int(id)).first())
        db.session.commit()
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + name + "Was Removed from tempstudent", date=datetime.utcnow()))
        db.session.commit()
    
    return redirect('temp_student_reg')

@app.route('/download/<fileFolder>/<fileName>')
@login_required
def downloadFile(fileFolder, fileName):
    #role_required("student", "ACTION: download")

    # safe_join rejects path traversal ("..") in the URL segments.
    path = safe_join('files', fileFolder, fileName)
    if path is None:
        abort(404)

    if eligibleForDownload(getUserName(current_user.id), getUserRole(current_user.id)) and current_user.is_student():
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + fileName + " was just downloaded", date=datetime.utcnow()))
        db.session.commit()
        return send_file(path, as_attachment=True)
    elif getRoleLevel(getUserRole(current_user.id)) > getRoleLevel('student'):
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + fileName + " was just downloaded", date=datetime.utcnow()))
        db.session.commit()
        return send_file(path, as_attachment=True)
    else:
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + fileName + " was just blocked from downloading", date=datetime.utcnow()))
        db.session.commit()
        return abort(400, " ")

@app.route('/upload', methods=['POST','GET'])
@login_required
def upload():
    check_maintenance()
    # #role_required("tutor", "ACTION: upload")
    permission_required(current_user.id, "upload_work_to_lesson", fatal=True)

    if request.method == 'POST':
        lessonID = request.args['lessonID']
        weekNo = request.args['weekNo']
        
        try: 
            studentView = request.args['studentView']
            studentView = True if studentView == "true" else False
        except:
            studentView = True
        
        try:
            type1 = request.form['type'].lower()
        except: 
            type1 = "main"
        try:
            topic = request.form['topic']
        except: 
            topic=""

        if 'file' not in request.files:
            return ""

        files = request.files.getlist('file')

        for file in files:
            if file.filename == '':
                return ""

            if file:
                filename = secure_filename(file.filename.replace("-", "_"))
                subjectID = Lesson.query.filter_by(lessonID = lessonID).first().subjectID
                subject = getFileFolder(subjectID)

                path = "/var/www/webApp/webApp/files/" + subject.upper() + "/"
                existingFiles = [f for f in listdir(path) if isfile(join(path, f))]

                if filename not in existingFiles:
                    file.save("/var/www/webApp/webApp/files/" + subject.upper() + "/" + filename)
                else: 
                    exists = Files.query.filter_by(lessonID=lessonID).filter_by(weekNo = weekNo).filter_by(filename=filename).first()
                    if exists:
                        db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): " + filename + " FAILED to upload for " + getSubjectName(subjectID) + " for week " + weekNo  + " because the filename already exists", date=datetime.utcnow()))
                        # abort(300, " ")
                        continue
                        
                if "MS" in file.filename or "nswer" in file.filename or "test" in file.filename.lower():
                    studentView = False

                
                db.session.add(Files(lessonID=lessonID, weekNo=weekNo, filename = filename, type=type1, associatedTopic=topic, subjectID = None, studentview = studentView, classtype = None))
                db.session.commit()
                
                db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): " + filename + "Was just uploaded for " + getLessonString(lessonID) + " for week " + str(weekNo), date=datetime.utcnow()))
                db.session.commit()
                
            else:
                return ""

    return ""

@app.route('/uploadForAll', methods=['POST', 'GET'])
@login_required
def uploadForAll(): 
    check_maintenance()
    #role_required("tutor", "ACTION: uploadForAll")
    permission_required(current_user.id, 'upload_to_subject', fatal=True)
    if request.method == 'POST':
        subjectID = request.args['subjectID']
        weekNo = request.args['weekNo']
        try: 
            scope = request.form['days']
        except: 
            scope = None
        
        try:
            studentView = True if request.form['studentView'] == "true" else False
        except:
            studentView = True

        if 'file' not in request.files:
            flash('No file part')
            return ""

        files = request.files.getlist('file')
        # print(len(files))

        for file in files:
            if file.filename == '':
                continue

            if file:
                filename = secure_filename(file.filename)
                subject = Subject.query.filter_by(subjectID = subjectID).first()
                subject = getFileFolder(subjectID)

                path = "/var/www/webApp/webApp/files/" + subject + "/"
                existingFiles = [f for f in listdir(path) if isfile(join(path, f))]

                if filename not in existingFiles:
                    file.save("/var/www/webApp/webApp/files/" + subject.upper() + "/" + filename)
                else: 
                    exists = Files.query.filter_by(subjectID=subjectID).filter_by(weekNo = weekNo).filter_by(filename=filename).first()
                    if exists:
                        db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): " + filename + " FAILED to upload for " + getSubjectName(subjectID) + " for week " + weekNo  + " because the filename already exists", date=datetime.utcnow()))
                        # abort(300, " ")
                        continue


                lessonList = Lesson.query.filter_by(subjectID = subjectID).filter_by(active=True).all()
                
                if "MS" in file.filename or "nswer" in file.filename:
                    studentView = False
                else: 
                    studentView = True
                
                fileEntry = Files(lessonID=None, weekNo=weekNo, filename = filename, type="main", associatedTopic="", subjectID = subjectID, studentview = studentView, classtype = scope)
                db.session.add(fileEntry)
                db.session.commit()       
                    
                if weekNo != "-1": 
                    db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): " + filename + " Was just uploaded for " + getSubjectName(int(subjectID)) + " for week " + weekNo  + " and studentView has been set to " + str(studentView), date=datetime.utcnow()))
                else: 
                    db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): " + filename + " Was just uploaded for " + getSubjectName(int(subjectID)) + " as a subject resource and studentView has been set to " + str(studentView), date=datetime.utcnow()))

                db.session.commit()
                
                continue
            else:
                continue
                
        
    return jsonify(fileID=fileEntry.fileid, filename=filename)

@app.route('/uploadPayslip/<tutorid>', methods = ['POST'])
@login_required
def  uploadPayslip(tutorid):
    #role_required("admin", "ACTION: uploading payslip")
    if request.method == 'POST':
        if 'file' not in request.files:
            return ""

        files = request.files.getlist('file')

        for file in files:
            if file.filename == '':
                return ""

            if file:
                filename = file.filename

                path = f"/var/www/webApp/webApp/payslips/{tutorid}" 
                existingFiles = [f for f in listdir(path) if isfile(join(path, f))]

                if filename not in existingFiles:
                    file.save(path + "/" + filename)


                db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): " + filename + "Was just uploaded to the payslip section for " + getUserName(tutorid), date=datetime.utcnow()))
                db.session.commit()
        
        return ""
            
    else:
        return ""

@app.route('/deleteUniqueFile', methods=['POST', 'GET'])
@login_required
def deleteUniqueFile(): 
    check_maintenance()
    lessonID = request.args['lessonID']
    filename = request.args['filename']
    weekNo = request.args['weekNo']
    
    stmt = delete(Files).where(and_(Files.lessonID == int(lessonID), Files.filename == filename))
    db.session.execute(stmt)

    # file = Files.query.filter_by(lessonID = lessonID).filter_by(filename = filename).filter_by(weekNo = weekNo).first
    fileFolder = getFileFolder(getLessonSubject(lessonID))
    os.remove('/var/www/webApp/webApp/files/' + fileFolder + "/" + filename)

    
    
    db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): " + filename + " Was just deleted for " + getLessonString(lessonID) + "for week " + weekNo, date=datetime.utcnow()))
    db.session.commit()
    
    return ""
    
@app.route('/files/<fileFolder>/<fileName>', methods=['POST', 'GET'])
def view_files(fileFolder, fileName):
    # safe_join rejects path traversal ("..") in the URL segments.
    path = safe_join('files', fileFolder, fileName)
    if path is None:
        abort(404)

    if fileFolder != "IMPORTANT_DOCS":
        if not current_user.is_authenticated:
            abort(403, "Login is required to view this file")
    
    fileEntry = Files.query.filter_by(filename = fileName).first()
        
    if fileEntry:
        if fileEntry.studentview != True:
            if current_user.is_student() or current_user.is_parent():
                abort(403, "hidden from students")
            # role_required("tutor", "Viewing a test: " + fileName)
            if current_user.is_authenticated:
                db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): " + fileName + " Was just viewed" , date=datetime.utcnow()))
                db.session.commit()
                    
                return send_file(path)
            else: 
                db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): Was just denied access to " + fileName , date=datetime.utcnow()))
                db.session.commit()
                abort(403, "")
    else:
        if "test" in fileName or "MS" in fileName or "mock" in fileName.lower():
            #role_required("tutor", "Viewing a test: " + fileName)
            if current_user.is_authenticated:
                db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): " + fileName + " Was just viewed" , date=datetime.utcnow()))
                db.session.commit()
                    
                return send_file(path)
            else: 
                db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): Was just denied access to " + fileName , date=datetime.utcnow()))
                db.session.commit()
                abort(403, "")
            
                    
    db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): " + fileName + " Was just viewed" , date=datetime.utcnow()))
    db.session.commit()
    
    return send_file(path)

@app.route('/userFiles/<userID>/<filename>', methods = ['POST', 'GET'])
@login_required
def userFile(userID, filename):
    # userID arrives as a str from the URL; compare as strings so users are
    # correctly matched against their own ID.
    if str(userID) != str(current_user.id):
        if current_user.is_student() or current_user.is_parent() or current_user.is_tutor():
            abort(404, )

    # safe_join rejects path traversal ("..") in the URL segments.
    path = safe_join('userFiles', str(userID), filename)
    if path is None:
        abort(404)

    return send_file(path)
   

@app.route('/create_lesson', methods=['POST', 'GET'])
@login_required
def create_lesson():
    check_maintenance()
    # #role_required("tutor", "ACTION: Create Lesson")
    permission_required(current_user.id, "add_a_new_lesson", fatal=True)
    
    data = request.get_json()
    
    before = len(Lesson.query.all())
    
    if data['tempLesson'] == True:
        db.session.add(Lesson(tutorID=data['tutor'], subjectID=data['subject'], day=data['day'], startTime=data['start_time'], endTime=data["end_time"], centreID=data['centre'], lessonName=data['name'], AcademicYear=data['year'], weekNo=int(data['weekNo']), active=True))
        db.session.commit()
    else:
        db.session.add(Lesson(tutorID=data['tutor'], subjectID=data['subject'], day=data['day'], startTime=data['start_time'], endTime=data["end_time"], centreID=data['centre'], lessonName=data['name'], AcademicYear=data['year'], weekNo = -1, active=True ))
        db.session.commit()    
    
    after = len(Lesson.query.all())
    
    # tutorEmail = Tutors.query.filter_by(id = data['tutor']).first().email
    # emailSender.send(tutorEmail, "NEW LESSON CREATED", "A new lesson has been created please check your timetable")
    
    # if after == before + 1:
        #print("success")
    
    id = Lesson.query.order_by(Lesson.lessonID).all()[-1].lessonID

    for student in data['students']:
        db.session.add(StudentLesson(studentID=int(student), lessonID=id))
        db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): Lesson (" + getLessonString(id) + ") was just created", date=datetime.utcnow()))
    db.session.add(LittleAlerts(userID = getUserID("tutor", data['tutor']), message= f" { getLessonString(id) } was just added to your timetable" ))
    db.session.add(LittleAlerts(userID = getUserID("tutor", data['tutor']), message= f" { getLessonString(id) } was just added to your timetable" ))
    

    db.session.commit()
    return ""

@app.route('/add_students', methods=['POST', 'GET'])                #Not sure why this is here but havent removed in case its used somewhere
@login_required
def add_subject():
    check_maintenance()
    #role_required("tutor", "ACTION: Add Students")
    data = request.get_json()

    for student in data['students']:
        db.session.add(StudentLesson(studentID=int(student), lessonID=id))
        db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + studentListToString(data['students']), date=datetime.utcnow()))
    db.session.commit()
    return ""

@app.route('/remove_lesson', methods=['POST', 'GET'])
@login_required
def remove_lesson():
    check_maintenance()
    #role_required("tutor", "ACTION: removing lessons")
    permission_required(current_user.id, "delete_a_lesson", fatal=True)
    
    data = request.get_json()
    id = data['id']
    
    lessonString = getLessonString(id)
    
    lesson = Lesson.query.filter_by(lessonID = id).first()
    if lesson is not None:
        # stmt = delete(StudentAttendance).where(StudentAttendance.lessonID==id)
        # db.session.execute(stmt)
        # db.session.commit()
        
        stmt = update(Lesson).values({"active" : False}).where(Lesson.lessonID == id)
        # stmt = delete(Lesson).where(Lesson.lessonID == id)
        db.session.execute(stmt)
        db.session.commit()
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): Lesson (" + lessonString + ") was just deleted (marked as inactive)", date=datetime.utcnow()))
        db.session.commit()
        
    return redirect(url_for("allTimetable", offset=0))

@app.route('/updateLessonPlan/<id>', methods=['POST', 'GET'])
@login_required
def updateLessonPlan(id):
    check_maintenance()
    #role_required("tutor", "ACTION: updating Lesson PLan")
    data = request.get_json()

    for week in data: 
        stmt = delete(lessonPlan).where(and_(lessonPlan.subjectID == id, lessonPlan.weekNo == week[0]))
        db.session.execute(stmt)
        
        db.session.add(lessonPlan(subjectID = id, weekNo = week[0], topic = week[1]))
        db.session.commit()
        
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): lesson plan for " + getSubjectName(id) + " was updated", date=datetime.utcnow()))
    db.session.commit()

    return ""

@app.route("/register_student", methods=['POST', 'GET'])
def register_student():
    # check_maintenance()
    studentInfo = request.get_json()
    siblingNameList = []
    # print("\n\n\n--------------------------\ndate is: " + datetime.date.today().strftime('%F'))
    #print("the date is: " + studentInfo['date_of_birth'])
    
    if studentWasJustCreated(studentInfo):
        db.session.add(log(role = 'anonymous', message= f"Student Registration: {studentInfo['firstName']} {studentInfo['secondName']} has just tried to register again but was rejected", date=datetime.utcnow()))
        db.session.commit()
        return "the student has already been created"
    
    
    if studentInfo['date_of_entry_uk'] == "" :
        date_of_entry_uk = studentInfo['date_of_birth']
    else:
        date_of_entry_uk = studentInfo['date_of_entry_uk'],
    
    raw_password = gen_random_password(8)
    password = generate_password_hash(raw_password)
    
    #register one student
    newStudent = Students(
        firstName = studentInfo['firstName'].capitalize(),
        middleName = studentInfo['middleName'].capitalize(),
        secondName = studentInfo['secondName'].capitalize(),
        known_as = studentInfo['known_as'],
        email = studentInfo['email'].strip().lower(),
        parent_email = studentInfo['parent_email'],
        year_group = studentInfo['student_year_group'],
        date_of_birth = studentInfo['date_of_birth'],
        gender = studentInfo['gender'],
        country_of_birth = studentInfo['country_of_birth'],
        nationality = studentInfo['nationality'],
        ethnic_origin = studentInfo['ethnic_origin'],
        mother_tongue = studentInfo['mother_tongue'],
        date_of_entry_uk = date_of_entry_uk,
        post_code = studentInfo['post_code'],
        house_number = studentInfo['house_number'],
        street_name = studentInfo['street_name'],
        city_or_county = studentInfo['city_or_county'],
        borough_of_residence = studentInfo['borough_of_residence'],
        mode_of_travelling = studentInfo['mode_of_travelling'],
        current_school_1 = studentInfo['current_school_1'],
        current_school_1_date_from = studentInfo['current_school_1_date_from'],
        school_2 = studentInfo['school_2'],
        school_2_date_from = studentInfo['school_2_date_from'],
        school_2_date_until = studentInfo['school_2_date_until'],
        school_3 = studentInfo['school_3'],
        school_3_date_from = studentInfo['school_3_date_from'],
        school_3_date_until = studentInfo['school_3_date_until'],
        school_4 = studentInfo['school_4'],
        school_4_date_from = studentInfo['school_4_date_from'],
        school_4_date_until = studentInfo['school_4_date_until'],
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
        sibling_4_forename = studentInfo['sibling_4_forename'],
        sibling_4_surname = studentInfo['sibling_4_surname'],
        sibling_4_date_of_birth = studentInfo['sibling_4_date_of_birth'],
        sibling_4_gender = studentInfo['sibling_4_gender'],
        sibling_4_year_group = studentInfo['sibling_4_year_group'],
        
        sibling_1_id = None, 
        sibling_2_id = None, 
        sibling_3_id = None,
        sibling_4_id = None,        
        
        previous_name = studentInfo['previous_name'],
        legal_name = studentInfo['legal_name'],
        home_local_authority = studentInfo['home_local_authority'],
        carer_name = studentInfo['carer_name'],
        look_after_child_contact_info = studentInfo['look_after_child_contact_info'],
        child_protection_register = studentInfo['child_protection_register'],
        look_after_child_register = studentInfo['look_after_child_register'],
        personal_education_plan = studentInfo['personal_education_plan'],
        pep_contact_number = studentInfo['pep_contact_number'],
        armed_service_parent_name = studentInfo['armed_service_parent_name'],
        armed_service_parent_service = studentInfo['armed_service_parent_service'],
        armed_service_parent_rank = studentInfo['armed_service_parent_rank'],
        armed_service_parent_additional_info = studentInfo['armed_service_parent_additional_info'],
        gp_name = studentInfo['gp_name'],
        gp_post_code = studentInfo['gp_post_code'],
        gp_telephone = studentInfo['gp_telephone'],
        gp_practice_address = studentInfo['gp_practice_address'],
        child_normally_healthy = studentInfo['child_normally_healthy'],
        asthma = studentInfo['asthma'],
        epilepsy_or_fits = studentInfo['epilepsy_or_fits'],
        heart_problems = studentInfo['heart_problems'],
        allergies = studentInfo['allergies'],
        allergyInfo = studentInfo['allergyInfo'],
        nose_bleeds = studentInfo['nose_bleeds'],
        speech_or_hearing_difficulties = studentInfo['speech_or_hearing_difficulties'],
        mobility_difficulties = studentInfo['mobility_difficulties'],
        other_difficulties = studentInfo['other_difficulties'],
        serious_illness_or_accidents = studentInfo['serious_illness_or_accidents'],
        condition_affecting_school_life = studentInfo['condition_affecting_school_life'],
        extra_medical_info = studentInfo['extra_medical_info'],
        known_medical_conditions = studentInfo['known_medical_conditions'],
        medical_treatment_or_medicines = studentInfo['medical_treatment_or_medicines'],
        emergency_information = studentInfo['emergency_information'],
        first_aid_permission = studentInfo['first_aid_permission'],
        hospital_referral_permission = studentInfo['hospital_referral_permission'],
        special_educational_needs = studentInfo['special_educational_needs'],
        sen_information = studentInfo['sen_information'],
        behavior_support_needed = studentInfo['behavior_support_needed'],
        behavior_support_info = studentInfo['behavior_support_info'],
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

        pupil_first_language = studentInfo['pupil_first_language'],
        pupil_first_language_spoken = studentInfo['pupil_first_language_spoken'],
        pupil_first_language_read = studentInfo['pupil_first_language_read'],
        pupil_first_language_written = studentInfo['pupil_first_language_written'],
        pupil_other_language = studentInfo['pupil_other_language'],
        pupil_other_language_spoken = studentInfo['pupil_other_language_spoken'],
        pupil_other_language_read = studentInfo['pupil_other_language_read'],
        pupil_other_language_written = studentInfo['pupil_other_language_written'],
        eal = studentInfo['eal'],
        home_main_language = studentInfo['home_main_language'],
        home_main_language_spoken = studentInfo['home_main_language_spoken'],
        home_main_language_read = studentInfo['home_main_language_read'],
        home_main_language_written = studentInfo['home_main_language_written'],
        home_other_language = studentInfo['home_other_language'],
        home_other_language_spoken = studentInfo['home_other_language_spoken'],
        home_other_language_read = studentInfo['home_other_language_read'],
        home_other_language_written = studentInfo['home_other_language_written'],
        local_visits_permission = studentInfo['local_visits_permission'],
        digital_media_consent = studentInfo['digital_media_consent'],
        declaration_name = studentInfo['declaration_name'],
        declaration_signed = True,
        # declaration_date = datetime.strptime(date.today().strftime('%F') , "%Y-%M-%d"),
        # declaration_date= str(date.today().strftime('%F')),
        declaration_date=gen_date(),

        additional_comments = studentInfo['additional_comment'], 
        
        username = gen_username(studentInfo['firstName'], studentInfo['secondName']), 
        password = password
    )
    
    db.session.add(newStudent)
    db.session.commit()
    
    studentID = Students.query.order_by(Students.id).all()[-1].id
    
    db.session.add(User(role="student", otherID = studentID, email=studentInfo['email'].strip().lower(), password = password))
    db.session.commit()
    
    if str(studentInfo['lessonID']) != "-1":
        db.session.add(StudentLesson(studentID = studentID, lessonID = int(studentInfo['lessonID'])))
        db.session.add(StudentAttendance(lessonID = int(studentInfo['lessonID']), weekNo = gen_week_no(7), AcademicYear=gen_relative_academic_year(0), studentID = studentID, present = False, extra_notes = " TRIAL SESSION "))
        db.session.commit()


    emailSender.send([studentInfo['email'], studentInfo['parent_email']], "Registration Confirmation", confirmRegistration(studentInfo['firstName'] + " " + studentInfo['secondName']))
    emailSenderPassword = EmailSender()
    emailSenderPassword.send(studentInfo['email'], "Here is your Password", gen_html_password_creation(studentInfo['firstName'] + " " + studentInfo['secondName'], raw_password))
    
    if str(studentInfo['lessonID']) == "-1":
        db.session.add(log(role = "anonymous", message= f"Student Registration: {studentInfo['firstName']} {studentInfo['secondName']} has just been registered", date=datetime.utcnow()))
    else: 
        db.session.add(log(role = "anonymous", message= f"Student Registration: {studentInfo['firstName']} {studentInfo['secondName']} has just been registered and has joined {getLessonString(int(studentInfo['lessonID']))} as a trial student", date=datetime.utcnow()))

    db.session.commit()
    
    #register sibling 1
    if (studentInfo['sibling_1_forename'] != "" and studentInfo['sibling_1_forename'] != None)  and studentInfo['auto_register'] == True:
        password = gen_random_password(8)
        db.session.add(createSibling(studentInfo, 1, password))
        db.session.commit()
        
        studentID = Students.query.order_by(Students.id).all()[-1].id
    
        db.session.add(User(role="student", otherID = studentID, email = studentInfo['sibling_1_email'], password = generate_password_hash(password)))
        db.session.commit()
        
        e1 = EmailSender()
        e1.send([studentInfo['sibling_1_email'], studentInfo['parent_email']], "Registration Confirmation", confirmRegistration(studentInfo['sibling_1_forename'].capitalize() + " " + studentInfo['sibling_1_surname'].capitalize()))
        
        e1Password = EmailSender()
        e1Password.send(studentInfo['sibling_1_email'], "Here is your Password", gen_html_password_creation(studentInfo['sibling_1_forename'], password))
        
        db.session.add(log(role = "anonymous", message="Student Registration: " + studentInfo['sibling_1_forename'] + " " + studentInfo['sibling_1_surname'] + " has just been registered  using the automatic sibling registering for " + studentInfo['firstName'], date=datetime.utcnow()))
        db.session.commit()
    
    #register sibling 2
    if (studentInfo['sibling_2_forename'] != "" and studentInfo['sibling_2_forename'] != None)  and studentInfo['auto_register'] == True:
        password = gen_random_password(8)
        db.session.add(createSibling(studentInfo, 2, password))
        db.session.commit()
        
        studentID = Students.query.order_by(Students.id).all()[-1].id
    
        db.session.add(User(role="student", otherID = studentID, email = studentInfo['sibling_2_email'], password = generate_password_hash(password)))
        db.session.commit()
        
        e2 = EmailSender()
        e2.send([studentInfo['sibling_2_email'], studentInfo['parent_email']], "Registration Confirmation", confirmRegistration(studentInfo['sibling_2_forename'].capitalize() + " " + studentInfo['sibling_2_surname'].capitalize()))
        
        e2Password = EmailSender()
        e2Password.send(studentInfo['sibling_2_email'], "Here is your Password", gen_html_password_creation(studentInfo['sibling_2_forename'], password))
        
        db.session.add(log(role = "anonymous", message="Student Registration: " + studentInfo['sibling_2_forename'] + " " + studentInfo['sibling_2_surname'] + " has just been registered using the automatic sibling registering for " + studentInfo['firstName'], date=datetime.utcnow()))
        db.session.commit()
    
        #register sibling 1
    
    #register sibling 3
    if (studentInfo['sibling_3_forename'] != "" and studentInfo['sibling_3_forename'] != None)  and studentInfo['auto_register'] == True:
        password = gen_random_password(8)
        db.session.add(createSibling(studentInfo, 3, password))
        db.session.commit()
        
        studentID = Students.query.order_by(Students.id).all()[-1].id
    
        db.session.add(User(role="student", otherID = studentID, email = studentInfo['sibling_3_email'], password = generate_password_hash(password)))
        db.session.commit()
        
        e3 = EmailSender()
        e3.send([studentInfo['sibling_3_email'], studentInfo['parent_email']], "Registration Confirmation", confirmRegistration(studentInfo['sibling_3_forename'].capitalize() + " " + studentInfo['sibling_3_surname'].capitalize()))
        
        e3Password = EmailSender()
        e3Password.send(studentInfo['sibling_3_email'], "Here is your Password", gen_html_password_creation(studentInfo['sibling_3_forename'], password))
        
        db.session.add(log(role = "anonymous", message="Student Registration: " + studentInfo['sibling_3_forename'] + " " + studentInfo['sibling_3_surname'] + " has just been registered using the automatic sibling registering for " + studentInfo['firstName'], date=datetime.utcnow()))
        db.session.commit()
    
    #register sibling 4
    if (studentInfo['sibling_4_forename'] != "" and studentInfo['sibling_4_forename'] != None)  and studentInfo['auto_register'] == True:
        password = gen_random_password(8)
        db.session.add(createSibling(studentInfo, 1))
        db.session.commit()
        
        studentID = Students.query.order_by(Students.id).all()[-1].id
    
        db.session.add(User(role="student", otherID = studentID, email = studentInfo['sibling_4_email'], password = generate_password_hash(password)))
        db.session.commit()
        
        e4 = EmailSender()
        e4.send([studentInfo['sibling_4_email'], studentInfo['parent_email']], "Registration Confirmation", confirmRegistration(studentInfo['sibling_4_forename'].capitalize() + " " + studentInfo['sibling_4_surname'].capitalize()))
        
        e4Password = EmailSender()
        e4Password.send(studentInfo['sibling_4_email'], "Here is your Password", gen_html_password_creation(studentInfo['sibling_4_forename'], password))
        
        db.session.add(log(role = "anonymous", message="Student Registration: " + studentInfo['sibling_4_forename'] + " " + studentInfo['sibling_4_surname'] + " has just been registered using the automatic sibling registering for " + studentInfo['firstName'], date=datetime.utcnow()))
        db.session.commit()

    if (studentInfo['parent_email'] != "" ):
        password = gen_random_password(8)
        db.session.add(User(role = "parent", otherID = None, email = studentInfo['parent_email'], password = generate_password_hash(password) ))

        e5 = EmailSender()
        e5.send(studentInfo['parent_email'], 'Here is your password', gen_html_password_creation(studentInfo['parent_email'], password))

        db.session.add(log(role = "anonymous", message="Student Registration: " + studentInfo['parent_email'] + " has just been registered as a parent for " + studentInfo['firstName'], date=datetime.utcnow()))
        db.session.commit()


    return ""


@app.route("/register_potential_exam_student", methods=['POST'])
def register_potential_exam_student():
    try:
        # Honeypot: real users never see/fill this field; bots do. Pretend success.
        if request.form.get('website'):
            return jsonify({'message': 'The Student was added as an Exam Student'}), 200

        # Get form data
        firstName = request.form.get('firstName')
        secondName = request.form.get('secondName')
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        uci = request.form.get('uci')
        uln = request.form.get('uln')
        studentEmail = request.form.get('studentEmail')
        parentEmail = request.form.get('parentEmail')
        contactNo = request.form.get('contactNo')
        subjects = request.form.get('subjects')
        accessArrangements = request.form.get('access_arrangements')
        centre_id = _resolve_centre_id(request.form.get('centreID'))

        # Parse the date instead of trusting the raw string into a Date column.
        if dob:
            try:
                dob = datetime.strptime(dob, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return jsonify({'error': 'Date of birth must be a valid date.'}), 400
        else:
            dob = None

        # Structured exam picks from the new form: JSON [{examID, label}] — the
        # officer no longer has to parse free text to work out the entries.
        # Public endpoint, so: cap the number of picks, guard every type, and
        # resolve all exam ids with ONE bulk query instead of one per entry.
        requested = []
        try:
            picks = json.loads(request.form.get('examSelections') or '[]')
            picks = [p for p in picks if isinstance(p, dict)][:20] if isinstance(picks, list) else []

            def _pick_id(pick):
                try:
                    return int(pick.get('examID'))
                except (TypeError, ValueError):
                    return None

            wanted_ids = {i for i in (_pick_id(p) for p in picks) if i is not None}
            exams_by_id = ({e.examID: e for e in Exams.query.filter(Exams.examID.in_(wanted_ids)).all()}
                           if wanted_ids else {})
            for pick in picks:
                exam = exams_by_id.get(_pick_id(pick))
                if exam:
                    label = " ".join(p for p in [exam.tier, exam.title, exam.examBoard, exam.Option] if p)
                    if exam.code:
                        label += f" ({exam.code})"
                    requested.append({'examID': exam.examID, 'label': label})
                    continue
                label = str(pick.get('label') or '').strip()[:200]
                if label:  # "my exam isn't listed" free-text row
                    requested.append({'examID': None, 'label': label})
        except (ValueError, TypeError):
            pass

        # Readable summary for the officer's review screens (the old free-text
        # 'subjects' box becomes the notes line; old-form posts still work).
        message_lines = []
        if requested:
            message_lines.append("Requested exams:")
            message_lines += [f"- {r['label']}" + ("" if r['examID'] else " [not in our list]")
                              for r in requested]
        if centre_id:
            message_lines.append(f"Preferred centre: {_centre_name(centre_id)}")
        if subjects and subjects.strip():
            message_lines.append(("Notes: " if requested else "") + subjects.strip())
        message = "\n".join(message_lines)

        # Validate required fields
        if not firstName or not secondName or not studentEmail or not request.files.get('fileUpload'):
            return jsonify({'error': 'First Name, Second Name, Student Email, and ID Upload are required.'}), 400

        studentEntry = gen_exam_student(firstName, secondName, gender, dob, studentEmail, parentEmail, contactNo, username=gen_username(firstName, secondName), password=generate_password_hash(gen_random_password(8)))
        db.session.add(studentEntry)
        db.session.commit()

        raw_password = gen_random_password(8)
        password = generate_password_hash(raw_password)

        user = User(role="student", otherID = studentEntry.id, email = studentEmail, password = password)
        db.session.add(user)
        db.session.commit()

        # Overridable so hosted environments without /var/www (e.g. Render) work;
        # defaults to the production path.
        files_base = os.environ.get('USER_FILES_DIR') or '/var/www/webApp/webApp/userFiles'
        user_files_path = os.path.join(files_base, str(user.id))
        os.makedirs(user_files_path, exist_ok=True)

        # Save identification file
        id_file = request.files.get('fileUpload')
        if id_file:
            id_filename = secure_filename(id_file.filename)
            id_extension = os.path.splitext(id_filename)[1]  # Get the file extension
            id_file_path = os.path.join(user_files_path, f'identification{id_extension}')
            id_file.save(id_file_path)
        
        # Save previous results file
        prev_results_file = request.files.get('prevResults')
        if prev_results_file:
            prev_results_filename = secure_filename(prev_results_file.filename)
            prev_results_extension = os.path.splitext(prev_results_filename)[1]  # Get the file extension
            prev_results_file_path = os.path.join(user_files_path, f'prev_results{prev_results_extension}')
            prev_results_file.save(prev_results_file_path)
            
        access_doc_file = request.files.get('accessDoc')
        if access_doc_file:
            access_doc_filename = secure_filename(access_doc_file.filename)
            access_doc_extension = os.path.splitext(access_doc_filename)[1]  # Get the file extension
            access_doc_file_path = os.path.join(user_files_path, f'access_arrangements{access_doc_extension}')
            access_doc_file.save(access_doc_file_path)

        # Any additional documents (the form allows several)
        for i, extra in enumerate(request.files.getlist('extraDocuments'), start=1):
            if extra and extra.filename:
                extra_name = secure_filename(extra.filename)
                extra_ext = os.path.splitext(extra_name)[1]
                extra.save(os.path.join(user_files_path, f'extra_doc_{i}{extra_ext}'))

        db.session.add(exam_student(studentID = studentEntry.id, uci = uci, uln = uln,
                                    access_arrangements = accessArrangements,
                                    message = message,
                                    centreID = centre_id,
                                    requested_exams = (json.dumps(requested) if requested else None),
                                    approved = False))
        db.session.commit()
        
        db.session.add(log(role = "anonymous", message= f"Student Registration: {firstName} {secondName} has just been registered as a potential exam Student", date=datetime.utcnow()))
        db.session.commit()

        response = {
            'message': 'The Student was added as an Exam Student',
            'first_name': firstName,
            'second_name': secondName,
            'gender': gender,
            'dob': dob,
            'uci': uci,
            'uln': uln,
            'student_email': studentEmail,
            'parent_email': parentEmail,
            'contact_no': contactNo,
            'subjects': subjects,
            'access_arrangements': accessArrangements
            }

        return jsonify(response), 200

    except Exception as e:
        db.session.rollback()  # keep the session usable for the next request
        print(e)
        return jsonify({'error': str(e)}), 400


@app.route("/register_exam_student", methods=['POST', 'GET'])
@login_required
def register_exam_student():
    check_maintenance()

    data = request.get_json()

    firstName = data['firstName']
    secondName = data['secondName']
    gender = data['gender']
    dob = datetime.strptime(data['dob'], "%d/%m/%Y").strftime("%Y-%m-%d")
    uci = data['uci']
    uln = data['uln']
    studentEmail = data['studentEmail']
    parentEmail = data['parentEmail']
    contactNo = data['contactNo']
    access_arrangements = data['access_arrangements']

    studentEntry = gen_exam_student(firstName, secondName, gender, dob, studentEmail, parentEmail, contactNo, username=gen_username(firstName, secondName), password=generate_password_hash(gen_random_password(8)))
    db.session.add(studentEntry)
    db.session.commit()
    
    raw_password = gen_random_password(8)
    password = generate_password_hash(raw_password)
    
    db.session.add(User(role="student", otherID = studentEntry.id, email = studentEmail, password = password))
    db.session.commit()

    studentList = Students.query.filter_by(firstName=firstName, secondName=secondName, email=studentEmail).all()

    studentIDs = [student.id for student in studentList]
    studentID = max(studentIDs)

    db.session.add(exam_student(studentID, uci, uln, access_arrangements))


    db.session.add(log(role = "anonymous", message= f"Student Registration: {data['firstName']} {data['secondName']} has just been registered as an exam Student", date=datetime.utcnow()))
    db.session.commit()    
    return ""

@app.route("/dismissLesson", methods=['POST', 'GET'])
@login_required
def dismissLesson():
    check_maintenance()
    #role_required("admin", "ACTION: Dismissing a Lesson")
    # print("test")
    data = request.get_json()
    id = data['id']
    weekNo = data['weekno']
    
    stmt = update(LessonInfo).values({"dismissed" : True}).where(and_(LessonInfo.lessonID == id, LessonInfo.weekNo == weekNo)) 
    db.session.execute(stmt)
    db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + getLesson(id) + " for week " + str(weekNo) + " was just dismissed", date=datetime.utcnow()))
    db.session.commit()

    # print(id"anonymous"
    return ""

@app.route("/addNewTutor", methods=['POST', 'GET'])
@login_required
def addNewTutor():
    check_maintenance()
    # #role_required("admin", "ACTION: adding a new tutor")
    if getRoleLevel(getUserRole(current_user.id)) > getRoleLevel('tutor'):
        permission_required(current_user.id, "create_below_roles", fatal=True)
    else: 
        abort(400, )

    data = request.get_json()
    tutorExists = User.query.filter_by(email = data['email'].lower().strip()).first()
    
    if tutorExists is not None:
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + data['firstName'] + " " + data['secondName'] + " was just rejected as a new tutor since the email is already in use " + data['email'], date=datetime.utcnow()))
        db.session.commit()
        return "user with that email has alreday been registered - please only press the button once!"
            
    password = gen_random_password(8)
    tutor = Staff(role = "tutor",
                firstName = data['firstName'],
                middleName = data['middleName'],
                secondName = data['secondName'],
                known_as = data['known_as'],
                email = data['email'],
                work_email = data['work_email'],
                date_of_birth = data['date_of_birth'],
                gender = data['gender'],
                country_of_birth = data['country_of_birth'],
                nationality = data['nationality'],
                ethnic_origin = data['ethnic_origin'],
                mother_tongue = data['mother_tongue'],
                post_code = data['post_code'],
                house_number = data['house_number'],
                street_name = data['street_name'],
                city_or_county = data['city_or_county'],
                borough_of_residence = data['borough_of_residence'],
                mode_of_travelling = data['mode_of_travelling'],
                phone = data['phone'])
    
    db.session.add(tutor)
    db.session.commit()
    
    time.sleep(1)

    subjects = data['subjects']
    
    id = tutor.id

    path = "/var/www/webApp/webApp/payslips"

    userEntry = User(role="tutor", otherID=id, email=data['email'].lower().strip(), password = generate_password_hash(password))
    db.session.add(userEntry)
    db.session.commit()
    db.session.add(individualDocument(userID = userEntry.id, docID=18))
    db.session.commit()
    

    
    id = User.query.filter_by(email = data['email'].lower().strip()).first().id
    os.mkdir(os.path.join(path, str(id)))
    
    e1 = EmailSender()
    e1.send(email = data['email'], subject = "Tutor Registration", message = gen_html_tutor_registration(data['firstName'], password))
    
    # for subject in subjects:
    #     db.session.add(TutorSubject(id, subject))
    #     db.session.commit()

    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + data['firstName'] + " " + data['secondName'] + " was just added as a new tutor", date=datetime.utcnow()))
    db.session.commit()
    return ""

@app.route('/deleteTutor/<id>', methods=['POST', 'GET'])
@login_required
def deleteTutor(id):
    check_maintenance()
    #role_required("admin", "ACTION: deleting tutor")
    userID = id
    staffID = getOtherID(getUserRole(userID), userID)

    name = getTutor(staffID)
    stmt = delete(TutorSubject).where(TutorSubject.tutorID == staffID)
    db.session.execute(stmt)
    db.session.commit()
    
    stmt = update(Lesson).values({'tutorID' : 16 }).where(Lesson.tutorID == staffID)
    db.session.execute(stmt)
    db.session.commit()

    stmt = delete(UserAlerts).where(UserAlerts.userID == userID)
    db.session.execute(stmt)
    db.session.commit()

    role = Staff.query.filter_by(id = staffID).first().role
    
    stmt = delete(Staff).where(Staff.id==staffID)
    # stmt = update(Tutors).values({"log_on" : False}).where(Tutors.id==id)
    db.session.execute(stmt)
    db.session.commit()

    stmt = delete(User).where(and_(User.id==userID))
    db.session.execute(stmt)
    db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + name + " was just removed as a tutor", date=datetime.utcnow()))
    db.session.commit()
    return redirect('/admin_tutor_view')

@app.route("/updateLessons", methods=["POST", "GET"])
@login_required
def updateLessons():
    check_maintenance()
    #role_required("tutor", "ACTION: Updating Lessons")
    data = request.get_json()
    role = data['role']

    tutorid = getOtherID(role = role, id=data['id'])
    
    subjectList = TutorSubject.query.filter_by(tutorID = tutorid).all()
    subjectIdList = np.array(subjectList)
    for i in range(0, subjectIdList.size, 1):
        subjectIdList[i] = (subjectIdList[i].subjectID)
        
   
    
    newSubjectList = data['subjects']

    newSubjectIdList = np.array([])
    for subject in newSubjectList:
        if subject is not None:
            newSubjectIdList = np.append(newSubjectIdList, subject)

    
    toRemove = np.setdiff1d(subjectIdList, newSubjectIdList)
    toAdd = np.setdiff1d(newSubjectIdList, subjectIdList)
    
    for id in toRemove:
        stmt = delete(TutorSubject).where(TutorSubject.subjectID==id).where(TutorSubject.tutorID==tutorid)
        db.session.execute(stmt)
        db.session.commit()
    
    for id in toAdd:
        db.session.add(TutorSubject(tutorID=tutorid, subjectID=id))
        db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + "Subjects for " + getTutor(tutorid) + " has just been updated" , date=datetime.utcnow()))
    db.session.commit()
    return ""
    
@app.route("/addSubject", methods=['POST', 'GET'])
@login_required
def addSubject():
    check_maintenance()
    #role_required("tutor", "ACTION: adding Subject")
    data = request.get_json()
    
    check = Subject.query.filter_by(tier=data['tier'], title=data["title"].title()).first()
    
    if check is not None:
         return json.dumps({'error':True}), 400, {'ContentType':'application/json'} 
    else:
        db.session.add(Subject(tier=data['tier'], title=data["title"].title(), examBoard = data['examBoard']))
        db.session.commit()
        make_topic_folder(data['tier'] + "-" + data["title"].title())
        subjectID = Subject.query.filter_by(tier=data['tier']).filter_by(title=data["title"].title()).filter_by(examBoard = data['examBoard']).first().subjectID
        
        for i in range(0, 54, 1):
            db.session.add(lessonPlan(subjectID = subjectID, weekNo = i, topic = "-"))
        
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + data['tier'] + data['title'] + " was just added as a subject" , date=datetime.utcnow()))
        db.session.commit()
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

@app.route("/addStudents", methods=['POST', 'GET'])
@login_required
def addStudents():
    check_maintenance()
    # #role_required("tutor", "Adding students to a lesson")
    permission_required(current_user.id, "change_lesson_students")
    
    data = request.get_json()
    
    lessonid = data['ids'][0]
    new_data = data['ids'][1:]
    
    for id in new_data: 
        if id is not None:
            if "undefined" not in id:
                if "temp" in id:
                    db.session.add(unregisteredStudentLessons(studentName=id[5:], lessonID=lessonid))
                    db.session.commit()
                    continue
                db.session.add(StudentLesson(studentID=id, lessonID=lessonid))
                db.session.commit()

    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): the following students [" + studentListToString(new_data)+ "] were added to " + getLessonString(lessonid), date=datetime.utcnow()))
    db.session.commit()
        
    return ""

@app.route("/removeStudent", methods=['POST', 'GET'])
@login_required
def removeStudents():
    check_maintenance()
    # #role_required("tutor", "Adding a Subject")
    permission_required(current_user.id, "change_lesson_students")
    
    data = request.get_json()
    
    lessonID = int(data['lessonID'])
    studentID = int(data['studentID'])
    
    stmt = delete(StudentLesson).where(and_(StudentLesson.studentID==studentID, StudentLesson.lessonID == lessonID))
    db.session.execute(stmt)
    
        
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + getStudent(studentID) + " was just removed from " + getLessonString(lessonID), date=datetime.utcnow()))
    db.session.commit()
    
    return ""

#This function should just remove any exam attributes / links to exams for the student
@app.route("/convert_exam_student", methods=['POST', 'GET'])
@login_required
def remove_exam_student():
    check_maintenance()
    #role_required("admin", "ACTION: removing an exam student")
    data = request.get_json()

    id = data['id']

    stmt = delete(exam_student).where(exam_student.studentID == id)
    db.session.execute(stmt)

    stmt = delete(studentExam).where(studentExam.studentID == id)
    db.session.execute(stmt)

    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + getStudent(id) + " was just converted from an exam student to a regular student", date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@app.route("/removeSubject", methods=['POST', 'GET'])
@login_required
def removeSubject():
    check_maintenance()
    #role_required("admin", "ACTION: Removing Subject")
    data = request.get_json()
    
    id = data['id']
    name = getSubjectName(id)
    
    stmt = delete(lessonPlan).where(lessonPlan.subjectID == id)
    db.session.execute(stmt)
    db.session.commit()
    
    stmt = delete(Files).where(Files.subjectID == id)
    db.session.execute(stmt)
    db.session.commit()
    
    stmt = update(Lesson).values({"subjectID" : 48}).where(Lesson.subjectID == id)
    db.session.execute(stmt)
    db.session.commit()
    
    stmt = delete(Subject).where(Subject.subjectID == id)
    db.session.execute(stmt)
    db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + name + " was just removed as a subject", date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@app.route("/deleteStudent/<id>", methods=['POST', 'GET'])
@login_required
def deleteStudent(id):
    check_maintenance()
    # #role_required("admin", "ACTION: deleting a student")
    permission_required(current_user.id, 'delete_a_student', fatal=True)
    name = getStudent(id)
    
    stmt = delete(StudentLesson).where(StudentLesson.studentID == id)
    db.session.execute(stmt)
    db.session.commit()
    
    stmt = delete(StudentAttendance).where(StudentAttendance.studentID == id)
    db.session.execute(stmt)
    db.session.commit()

    stmt = delete(exam_student).where(exam_student.studentID == id)
    db.session.execute(stmt)
    db.session.commit()
    
    stmt = delete(studentExam).where(studentExam.studentID == id)
    db.session.execute(stmt)
    db.session.commit()
    
    stmt = delete(Grades).where(Grades.studentID == id)
    db.session.execute(stmt)
    db.session.commit()
    
    stmt = delete(LittleAlerts).where(LittleAlerts.userID == getUserID(role="student ", otherID=id))
    db.session.execute(stmt)
    db.session.commit()
    
    stmt = delete(Students).where(Students.id == id)
    db.session.execute(stmt)
    db.session.commit()

    stmt = delete(User).where(and_(User.otherID == id, User.role == 'student' ))
    db.session.execute(stmt)
    db.session.commit()
    
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + name + " was just deleted", date=datetime.utcnow()))
    db.session.commit()
    
    return redirect("/admin_student_view")

@app.route("/deleteExamStudent")
@login_required
def deleteExamStudent(id):
    return ""

@app.route("/updateTutors", methods=['POST', 'GET'])
@login_required
def updateTutors():
    check_maintenance()
    #role_required("tutor", "ACTION: updating tutors information")
    data = request.get_json()
    
    tutorID = data['id']
    key = data['key']
    value = data['value']
    
    
    oldValue = Staff.query.filter_by(id=tutorID).first().__dict__[key]

    if key == "role" or key == "email":
        role = Staff.query.filter_by(id=tutorID).first().role
        stmt = update(User).where(and_(User.otherID == tutorID, User.role == role)).values({key : value})
        db.session.execute(stmt)
        
    
    
    stmt = update(Staff).where(Staff.id==tutorID).values({key : value})
    db.session.execute(stmt)
    db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + key + " for " + getStaff(tutorID) + " has changed from " + oldValue + " to " + value, date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@app.route("/updateLessonInfo", methods=['POST', 'GET'])
@login_required
def updateLessonInfo():
    check_maintenance()
    #role_required("tutor", "ACTION: updating Lesson Information")

    data = request.get_json()
    
    lessonid = data['id']
    key = data['key']
    value = data['value']
    
    if key == "tutorID":
        permission_required(current_user.id, "change_lesson_tutor", fatal=True)
    
    elif key == "subjectID":
        permission_required(current_user.id, "change_lesson_subject", fatal=True)
        
    elif key == "day":
        permission_required(current_user.id, "change_lesson_day", fatal=True)
        
    elif key == "startTime" or key == "endTime" or key == "weekNo":
        permission_required(current_user.id, "change_lesson_time", fatal=True)
        
    elif key == "centreID":
        permission_required(current_user.id, "change_lesson_centre", fatal=True)


    oldValue = Lesson.query.filter_by(lessonID=lessonid).first().__dict__[key]

    stmt = update(Lesson).where(Lesson.lessonID==lessonid).values({key : value})
    db.session.execute(stmt)
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + key + " for " + getLessonString(lessonid) + " has changed from " + getGeneral(oldValue, str(key)) + " to " + getGeneral(value, str(key)), date=datetime.utcnow()))
    db.session.commit()
    return ""

@app.route("/updateTestInfo", methods = ['POST', 'GET'])
@login_required
def updateTestInfo(): 
    check_maintenance()
    #role_required("admin", "ACTION: Updating Test Information")
    
    data = request.get_json()
    
    testID = data['testID']
    key = data['key']
    value = data['value']
    
    
    oldValue = Tests.query.filter_by(testID = testID).first().__dict__[key]
    
    stmt = update(Tests).where(Tests.testID == testID).values({key : value})
    db.session.execute(stmt)
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + key + " for " + getTest(testID) + " has changed from " + str(oldValue) + " to " + str(value) , date=datetime.utcnow()))
    db.session.commit()

    return ""

@app.route("/updateStudentInfo", methods = ['POST', 'GET'])
@login_required
def updateStudentInfo():
    check_maintenance()
    #role_required("student", "ACTION: Updating Student Information")
    data = request.get_json()
    
    studentID = data['studentID']
    key = data['key']
    value = data['value']
    
    if key == "exam_student":
        db.session.add(exam_student(studentID = studentID, uci = "", uln = "", access_arrangements = "", message="", approved = False))
        db.session.commit()
        
    if key == "uci": 
        stmt = update(exam_student).values({'uci' : value}).where(exam_student.studentID == studentID)
        db.session.execute(stmt)
        db.session.commit()
        
        oldValue = exam_student.query.filter_by(id = studentID).first().__dict__[key]
    else: 
        oldValue = Students.query.filter_by(id = studentID).first().__dict__[key]
    
    stmt = update(Students).where(Students.id == studentID).values({key : value})
    db.session.execute(stmt)
    db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + key + " for student" + getStudent(studentID) + " has changed from " + str(oldValue) + " to " + str(value), date=datetime.utcnow()))
    db.session.commit()
    
    
    return ""

@app.route("/makeLessonPermanent", methods=['POST', 'GET'])
@login_required
def makeLessonPermanent():
    check_maintenance()
    #role_required("tutor", "ACTION: Make Lesson Permanant")
    permission_required(current_user.id, "add_a_new_lesson")

    data = request.get_json()
    lessonid = data['lessonID']
    
    stmt = update(Lesson).where(Lesson.lessonID == lessonid).values({"weekNo" : -1, })
    db.session.execute(stmt)
    
            
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + getLessonString(lessonid) + " was just made permanent (Irreversible) ", date=datetime.utcnow()))
    
    db.session.commit()
    
    
    return ""

@app.route('/makeTest', methods = ['POST', 'GET'])
@login_required
def makeTest(): 
    check_maintenance()
    # #role_required("Tutor", "ACTION: making a test")
    permission_required(current_user.id, 'make_individual_test', fatal = True)
    data = request.get_json()
    
    lessonID = data['lessonID']
    weekNo = data['weekNo']
    date = data['date']
    total = int(data['total'])
    name = data['name']
    
    createTestWithStudents(lessonID, weekNo, date, total, name)
        
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + "A test for " + getLessonString(lessonID) + " called " + name + "was just created", date=datetime.utcnow()))
    db.session.commit()
       
    
    return ""

@app.route('/makeAllTests', methods = ['POST', 'GET'])
@login_required
def makeAllTests(): 
    check_maintenance()
    #role_required("admin", "ACTION: making multiple tests")
    data = request.get_json()
    
    weekNo = data['weekNo']
    date = data['date']
    total = data['total']
    name = data['name']
    subjectID = data['subjectID']
    scope = data['scope']
    
    lessons = getLessonsByScope(int(subjectID), scope)
    
    for lesson in lessons:
        createTestWithStudents(lesson, weekNo, date, total, name)
        
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + "A test for " + getSubjectName(subjectID) + " with scope " + scope + " called " + name + "was just created", date=datetime.utcnow()))
    db.session.commit()
       
    
    return ""

@app.route("/updateTestMarks", methods = ['POST', 'GET'])
@login_required
def updateTestMarks(): 
    check_maintenance()
    #role_required("tutor", "ACTION: Updating test marks")
    data = request.get_json()
       
    
    testID = data['testID']
    studentMarks = data['studentMarks']
    
    for student in studentMarks: 
        if student[1] is not None and student[1] != "":
            if student[0] == -1:
                present = Grades.query.filter_by(testID = testID).filter_by(studentName = student[3]).first()
                if present is not None: 
                    stmt = update(Grades).where(and_(Grades.testID == testID, Grades.studentName == student[3])).values({"mark" : student[1], "grade" : student[2]})
                    db.session.execute(stmt)
                    db.session.commit()
                else: 
                    db.session.add(Grades(testID = testID, studentID = None, studentName = student[3], mark=student[1], grade=student[2]))
                    db.session.commit()
            else: 
                stmt = update(Grades).where(and_(Grades.testID == testID, Grades.studentID == student[0])).values({"mark" : student[1], "grade" : student[2]})
                db.session.execute(stmt)
                db.session.commit()
            
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " +  " marks for " + getTest(testID) + " were just updated ", date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@app.route("/updateGrade", methods = ['POST', 'GET'])
@login_required
def updateGrade(): 
    check_maintenance()
    #role_required("admin", "ACTION: Updating Student Grade information")
    
    data = request.get_json()
    
    gradeID = data['gradeID']
    key = data['key']
    value = data['value']
    
    oldValue = Grades.query.filter_by(gradeID = gradeID).first().__dict__[key]
    
    stmt = update(Grades).where(Grades.gradeID == gradeID).values({key : value})
    db.session.execute(stmt)
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + key + " for " + getGrade(gradeID) + " has changed from " + str(oldValue) + " to " + str(value) , date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@app.route('/deleteTest/<id>', methods = ['POST', 'GET'])
@login_required
def deleteTest(id):
    check_maintenance()
 
    # #role_required("admin", "ACTION: Deleting a test")
    permission_required(current_user.id, "make_individual_test", fatal=True)
    
    test = getTest(id)
    
    stmt = delete(Grades).where(Grades.testID == id)
    db.session.execute(stmt)
    db.session.commit()
    
    stmt = delete(Tests).where(Tests.testID == id)
    db.session.execute(stmt)
    db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + test + " was just deleted", date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@app.route('/resetPassword', methods = ['POST', 'GET'])
@login_required
def resetPassword():
    check_maintenance()
    #role_required("admin", "ACTION: reset password")
    # role = request.args['role']
    id = request.args['id']
    # print(role)
    newPassword = gen_random_password(8)
    
    # newID = User.query.filter_by(role = role).filter_by(otherID = id).first()
    # if newID:
        # newID = newID.id
    e1 = EmailSender()
    

    # if role == "student":
    #     stmt = update(User).where(User.id == newID).values({"password" : generate_password_hash(newPassword)})
    #     db.session.execute(stmt)
        
    #     e1.send(getStudentEmail(id), "Password Reset", gen_html_password_reset(getStudent(id), newPassword))
       
    #     db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): reset the password for " + getStudent(id), date=datetime.utcnow()))
    #     db.session.commit()

    # else: 
    stmt = update(User).where(User.id == id).values({"password" : generate_password_hash(newPassword)})
    db.session.execute(stmt)
    
    e1.send(getUserEmail(id), "Password Reset", gen_html_password_reset(getUserName(id), newPassword))
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): reset the password for " + getUserName(id), date=datetime.utcnow()))
    db.session.commit()
        

    return ""

@app.route('/resetOwnPassword', methods = ['POST', 'GET'])
@login_required
def resetOwnPassword(): 
    email = request.form['email']
    return ""

@app.route('/makePerm', methods = ['POST', 'GET'])
@login_required
def makePerm():
    check_maintenance()
    # #role_required("tutor", "ACTION: make student permanent")
    permission_required(current_user.id, "change_lesson_students")
    data = request.get_json()
    
    name = data['name']
    lessonID = data['lessonID']
    newID = data['newID']
    
    #add student to lesson
    check = StudentLesson.query.filter_by(studentID = newID).filter_by(lessonID = lessonID).first()
    if check is None:
        db.session.add(StudentLesson(studentID = newID, lessonID = lessonID))
    
    #register their attendance properley
    attendance = UnregisteredAttendance.query.filter_by(studentName = name).filter_by(lessonID = lessonID).all()
    for item in attendance:
        check = StudentAttendance.query.filter_by(lessonID = lessonID).filter_by(weekNo = item.weekNo).filter_by(AcademicYear = item.AcademicYear).filter_by(studentID = newID).filter_by(present = item.present).first()
        if check is None:
            db.session.add(StudentAttendance(lessonID = lessonID, weekNo = item.weekNo, AcademicYear = item.AcademicYear, studentID = newID, present = item.present, extra_notes = item.extra_notes))
        else:
            if item.present == True or check.present == True:
                stmt = update(StudentAttendance).where(StudentAttendance.id == check.id).values({"present" : item.present})
                db.session.execute(stmt)
    
    #remove the attendance from unreg
    stmt = delete(UnregisteredAttendance).where(and_(UnregisteredAttendance.studentName == name, UnregisteredAttendance.lessonID == lessonID))
    db.session.execute(stmt)
    
    #remove from unregLesson
    stmt = delete(unregisteredStudentLessons).where(and_(unregisteredStudentLessons.studentName == name, unregisteredStudentLessons.lessonID == lessonID))
    db.session.execute(stmt)
    
    #remove from unreg student
        #no table to remove from
        
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + getStudent(newID)  + " was converted from an unregistered Student to a registered for " + getLessonString(lessonID), date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@app.route('/makeGradePerm', methods = ['POST', 'GET'])
@login_required
def makeGradePerm():
    check_maintenance()
    #role_required("admin", "Make Grades permanent")
    data = request.get_json()
    
    name = data['name']
    testID = data['testID']
    newID = data['newID']
    
    stmt = update(Grades).where(and_(Grades.studentName == name, Grades.testID == testID)).values({"studentName" : "", "studentID" : newID})
    db.session.execute(stmt)  
    
            
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + getStudent(newID)  + " was converted from an unregistered Student to a registered for the test " + getTest(testID), date=datetime.utcnow()))
    db.session.commit()  
    
    return "" 

@app.route("/deleteGrade/<gradeID>", methods = ['POST', 'GET'])
@login_required
def deleteGrade(gradeID):
    check_maintenance()

    #role_required("admin", "ACTION: Deleting a grade")
    
    grade = getGrade(gradeID)
    
    stmt = delete(Grades).where(Grades.gradeID == gradeID)
    db.session.execute(stmt)
    
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + grade + " was just deleted ", date=datetime.utcnow()))
    db.session.commit()    
    return ""
    
@app.route('/fixFiles', methods = ['POST', 'GET'])
@login_required
def fileFix(): 
    check_maintenance()
    
    data = request.get_json()
    
    subject = data['subjectID']
    classtype = data['classtype']
    weekNo = data['weekNo']
    filename = data['filename']
    
    try:
        studentView = False if request.form['studentView'] else True
    except:
        studentView = True

    
    
    stmt = delete(Files).where(Files.filename == filename)
    db.session.execute(stmt)
    
    db.session.add(Files(lessonID = None, weekNo = weekNo, filename = filename, type ="main", associatedTopic="", subjectID = subject, studentview = studentView, classtype = classtype))
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + filename + " was just fixed to be part of " + getSubjectName(subject) + " for " + classtype + " week " + weekNo, date=datetime.utcnow()))
    db.session.commit()
        
    return ""

@app.route('/moveFiles', methods = ['POST', 'GET'])
@login_required
def moveFiles():
    check_maintenance()
    data = request.get_json()
    
    fileID = data['fileID'] 
    newSubjectID = data['newSubjectID'] 
    newWeekNo = data['newWeekNo'] 
    
    oldSubjectID = Files.query.filter_by(fileid = fileID).first().subjectID
    filename = Files.query.filter_by(fileid = fileID).first().filename
    
    os.replace("var/www/webApp/webApp/files/" + getSubjectFolder(oldSubjectID) + "/" + filename, "var/www/webApp/webApp/files/" + getSubjectFolder(newSubjectID) + "/" + filename)
    
    stmt = update(Files).where(Files.fileid == fileID).values({"subjectID" : newSubjectID, "weekNo" : newWeekNo})
    db.session.execute(stmt)
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + getFileName(fileID) + " was just moved to " + getSubjectName(int(newSubjectID)) + " for week " + newWeekNo, date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@app.route("/sendMessage", methods = ['POST', 'GET'])
@login_required
def sendMessage(): 
    check_maintenance()
    #role_required("student", "sending a message")
    data = request.get_json()
    
    replyTo = data['replyTo']
    message = data['message']
    lessonID = data['lessonID']
    
    db.session.add(Messages(lessonID = lessonID, userID=current_user.id, time=datetime.utcnow(), message=message, replyTo=replyTo, deleted=False))
    
    if not current_user.is_tutor():
        e1 = EmailSender()
        tutorEmail = getTutorEmail(getLessonTutor(int(lessonID)))
        messageSender = getUserEmail(getMessageSender(replyTo))
        threadStarter = getUserEmail(getThreadStarter(replyTo))
        
        recipients = [email for email in [tutorEmail, messageSender, threadStarter] if email and email != ""]
            
        e1.send(recipients, "New Message from" + getUserName(current_user.id), gen_html_new_message(message, lessonID, getUserName(current_user.id)))
    else: 
        e1 = EmailSender()
        messageSender = getUserEmail(getMessageSender(replyTo))
        threadStarter = getUserEmail(getThreadStarter(replyTo))
                
        recipients = [email for email in [messageSender, threadStarter] if email and email != ""]
        
        e1.send(recipients, "New Message from " + getUserName(current_user.id), gen_html_new_message(message, lessonID, getUserName(current_user.id)))
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): has just sent a message to " + getLessonString(lessonID) ,  date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@app.route("/deleteMessage", methods=['POST', 'GET'])
@login_required
def deleteMessage():
    check_maintenance()
    #role_required("tutor", "ACTION: Deleting a message")
    data = request.get_json()
    
    messageID = data['id']
    
    stmt = update(Messages).values({"deleted" : True }).where(Messages.messageID == messageID)
    db.session.execute(stmt)
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just deleted the following message: " + getMessage(messageID) ,  date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@app.route("/updateTutorAccessRights", methods=['POST', 'GET'])
@login_required
def updateTutorAccessRights():
    check_maintenance()
    #role_required("admin", "ACTION: updating Tutor Access Rights")
    data = request.get_json()
    
    tutorID = int(data['tutorID'])
    key = data['key']
    value = data['value']
    
    stmt = update(User).values({key : value}).where(User.id == tutorID)
    db.session.execute(stmt)
    
    if value: 
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just granted the " + key + " permission to " + getUserName(tutorID) ,  date=datetime.utcnow()))
        db.session.add(LittleAlerts(userID = tutorID, message= f" You have been granted the permission {key}!" ))

    else: 
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just removed the " + key + " permission from " + getUserName(tutorID) ,  date=datetime.utcnow()))
        db.session.add(LittleAlerts(userID = tutorID, message= f" Your permission {key} has been removed"))

    
    db.session.commit()
    
    return ""

@app.route("/updateRoleAccessRights", methods=['POST', 'GET'])
@login_required
def updateRoleAccessRights():
    check_maintenance()
    # #role_required("admin", "ACTION: updating Role Access Rights")
    data = request.get_json()
    
    role = data['roleName']
    key = data['key']
    value = data['value']
    
    stmt = update(Roles).values({key : value}).where(Roles.name == role)
    db.session.execute(stmt)
    
    if value: 
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just granted the " + key + " permission to " + role ,  date=datetime.utcnow()))
    else: 
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just removed the " + key + " permission from " + role ,  date=datetime.utcnow()))
    
    db.session.commit()
    
    return ""

@app.route("/updateStudentAccessRights", methods=['POST', 'GET'])
@login_required
def updateStudentAccessRights():
    check_maintenance()
    #role_required("admin", "ACTION: updating Student Access Rights")
    data = request.get_json()
    
    studentID = int(data['studentID'])
    key = data['key']
    value = data['value']
    
    stmt = update(Students).values({key : value}).where(Students.id == studentID)
    db.session.execute(stmt)
    
    if value: 
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just granted the " + key + " permission to " + getStudent(studentID) ,  date=datetime.utcnow()))
    else: 
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just removed the " + key + " permission from " + getStudent(studentID) ,  date=datetime.utcnow()))
    
    db.session.commit()
    
    return ""

@app.route("/getTutorHours", methods=['POST', 'GET'])
@login_required
def sendTutorHours():
    check_maintenance()
    try: 
        offset = int(request.args['offset'])
    except: 
        offset = 0
    return str(getTutorHours(getOtherID("tutor", current_user.id), gen_week_no(offset)))

@app.route("/getTutorMonthHours", methods=['POST', 'GET'])
@login_required
def sendTutorMonthHours():
    check_maintenance()
    try: 
        offset = int(request.args['offset'])
    except: 
        offset = 0
        
    day = date.today() + timedelta(days = offset)
    month = int(day.month)
    return str(getTutorMonthHours(getOtherID("tutor", current_user.id), month))

@app.route('/getPermission', methods = ['GET'])
@login_required
def getPermission():
    check_maintenance()
    try: 
        permission = str(request.args['permission'])
    except:
        return jsonify({'permission' : False })

    return jsonify({'permission' : permission_required(current_user.id, permission) })

@app.route('/getRoleLevel', methods = ['GET'])
@login_required
def getRoleLevelFlask(): 
    try: 
        return jsonify({'roleLevel' : getRoleLevel(str(request.args['role'])) })
    except:
        return jsonify({'roleLevel' : getRoleLevel(getUserRole(current_user.id)) })

@app.route('/getRelativeRoleLevel', methods = ['GET'])
@login_required
def getRelativeRoleLevel():
    try:
        if request.args['inc'] == 'true':
            return jsonify({'roleLevel' : int(getRoleLevel(getUserRole(current_user.id))) >= int(getRoleLevel(str(request.args['role']))) })
        else: 
            return jsonify({'roleLevel' : int(getRoleLevel(getUserRole(current_user.id))) > int(getRoleLevel(str(request.args['role']))) })

    except: 
        return jsonify({'roleLevel' : False })

@app.route("/updateHours", methods = ['POST', 'GET'])
@login_required
def updateHours():
    check_maintenance()
    permission_required(current_user.id, "approve_hours", fatal=True)

    data = request.get_json()

    approve = data['approve']
    id = data['lessonID']
    weekNo = data['weekNo']

    if approve == "approve":
        stmt = update(LessonInfo).values({'approved' : True, "rejected" : False}).where(and_(LessonInfo.lessonID == id, LessonInfo.weekNo == weekNo))
        db.session.execute(stmt)
        
    elif approve == "reject":
        stmt = update(LessonInfo).values({'rejected' : True}).where(and_(LessonInfo.lessonID == id, LessonInfo.weekNo == weekNo))
        db.session.execute(stmt)
        approve = "rejecte"
    
    else:
        return "illegal action "

    db.session.add(LittleAlerts(userID = getUserID(getStaffRole(getLessonTutor(id)), getLessonTutor(id)), message= f"Hours for {getReducedLessonString(id)} have just been {approve}d "))

    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}):  has just {approve}d the hours for {getLessonString(id)} for {weekNo}",  date=datetime.utcnow()))
    db.session.commit()

    return ""


@app.route("/createAlert", methods = ['POST', 'GET'])
@login_required
def create_alert(): 
    check_maintenance()
    # #role_required("admin", "ACTION: creating an alert")
    permission_required(current_user.id, "create_alerts", fatal=True)
    data = request.get_json()
    
    title = data['title']
    message = data['message']
    role = data['role']
    
    createAlert(role, title, message)
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just created an alert for " + role + "'s  with the title " + title ,  date=datetime.utcnow()))
    db.session.commit()

    return ""

@app.route("/send_grades", methods = ['POST', 'GET'])
@login_required
def send_grades(): 
    check_maintenance()
    #role_required("admin", "ACTION: Sending report card to students")
    grades = request.get_json()
    
    if len(grades) == 0:
        return None
    
    studentID = Grades.query.filter_by(gradeID = grades[0]).first().studentID
       
    e1 = EmailSender()
    e1.send([getStudentEmail(studentID), getStudentParentEmail(studentID)], "Report Card", gen_html_report_card(studentID, grades))
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just sent" + getStudent(studentID) +  "'s report card to " + getStudentEmail(studentID) + " and " + getStudentParentEmail(studentID),  date=datetime.utcnow()))
    db.session.commit()
    
    return ""

def send_all_grades(studentgrades):
    check_maintenance()
    #role_required("admin", "ACTION: Sending report card to list of students")
    
    #studentgrades should be of the form [[studentID1, [gradeID1, gradeID2]], 
    #                                     [studentID1, [gradeID1, gradeID2]], 
    #                                     [studentID1, [gradeID1, gradeID2]] ]
    
    for student in studentgrades: 
        studentID = student[0]
        gradeList = student[1]
        
        e1 = EmailSender()
        e1.send([getStudentEmail(studentID), getStudentEmail(studentID)], "Report Card - February", gen_html_report_card(studentID, gradeList))
        
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just sent" + getStudent(studentID) +  "'s report card to " + getStudentEmail(studentID) + " and " + getStudentParentEmail(studentID),  date=datetime.utcnow()))
        db.session.commit()
    
    return ""

@app.route("/editFiles", methods = ['POST', 'GET'])
@login_required
def editFile():
    check_maintenance()
    data = request.get_json()
    
    id = data['fileID']
    key = data['key']
    value = data['value']
    
    if key != "delete":
        stmt = update(Files).values({key : value}).where(Files.fileid == id)
        db.session.execute(stmt)        
    
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just updated the file " + getFileName(id) + " and set " + key + " to " + str(value),  date=datetime.utcnow()))
        db.session.commit()
    else: 
        file = Files.query.filter_by(fileid = id).first()
        fileFolder = getFileFolder(file.subjectID)
        fileName = file.filename
        
        stmt = delete(Files).where(Files.fileid == id)
        db.session.execute(stmt)
        db.session.commit()
        # os.remove('/var/www/webApp/webApp/files/' + fileFolder + "/" + fileName)
        
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just deleted the file " + fileName,  date=datetime.utcnow()))
        db.session.commit()
    
    return ""

@app.route("/sendEmail", methods = ['POST', 'GET'])
@login_required
def sendEmail():
    check_maintenance()
    #role_required("admin", "ACTION: sending an Email")
    data = request.get_json()
    
    recipient = data['recipient'].strip().lower()
    subject = data['subject']
    message = data['message']
    files = data['files']

    e1 = EmailSender()
    e1.send(recipient, subject, message, files, subtype="plain")

    #Logs are handled at the email level
    # db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just sent an email ",  date=datetime.utcnow()))
    # db.session.commit()

    return ""

@app.route("/printWork", methods = ['POST', 'GET'])
@login_required
def printWork():
    check_maintenance()
    #role_required("admin", "ACTION: sending an Email")
    data = request.get_json()
    
    lessonid = data['lessonID']
    
    lesson = Lesson.query.filter_by(lessonID = lessonid)
    
    reg, unreg, temp = getAttendance(lesson.lessonID, gen_week_no(-1))
    copies = len(reg) + len(unreg) + len(temp)
    copies = copies // 2
    
    files = Files.query.filter(
        or_(
            Files.subjectID == lesson.subjectID,
            Files.lessonID == lesson.lessonID
        ),
        Files.weekNo == int(gen_week_no(0)),
        Files.auto_print == True
    ).all()
    
    subject_folder = getFileFolder(lesson.subjectID)  # Function to get subject folder
    files = [combine_two_pages_per_sheet(f"var/www/webApp/webApp/files/{subject_folder}/{file.filename}", f"var/www/webApp/webApp/files/{subject_folder}/{file.filename[:-4]}-2up.pdf") for file in files if classTypeCheck(lesson, file.classtype)]
    
    for file in files: 
        e1 = EmailSender()
        e1.send(email = "ateam1772@gmail.com", subject = f"Printing {getStaff(lesson.tutorID)}s files", message = f"COPIES={int(copies)}\nB/W PRINT=ON\nDUPLEX=LEFT", files=[file],  subtype='plain')

    return ""

@app.route("/sendClassEmail", methods = ['POST', 'GET'])
@login_required
def sendClassEmail():
    check_maintenance()
    # #role_required("tutor", "ACTION: sending an Email to the class")
    permission_required(current_user.id, 'send_emails_to_students', fatal=True)
    
    data = request.get_json()
    
    lessonID = data['lessonID']
    recipients = [getStudentEmail(student.studentID) for student in getStudents(lessonID)]

    prefix = f"~ This Email was sent on behalf of {getUserName(current_user.id)} ~ \n \n "

    subject = data['subject']
    message = prefix + data['message']

    e1 = EmailSender()
    e1.send(recipients, subject, message, subtype="plain")

    #Logs are handled at the email level
    # db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just sent an email ",  date=datetime.utcnow()))
    # db.session.commit()

    return ""

@app.route("/view_alert", methods = ['POST', 'GET'])
@login_required
def view_alert():
    check_maintenance()
    data = request.get_json()

    alertID = data['alertID']
    userID = current_user.id

    stmt = update(UserAlerts).values({"viewed" : True}).where(and_(UserAlerts.alertID == alertID, UserAlerts.userID == userID))
    db.session.execute(stmt)
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just read the alert with title " + getAlertTitle(alertID),  date=datetime.utcnow()))
    db.session.commit()

    return ""

@app.route('/view_little_alert', methods=['GET', 'POST'])
@login_required
def view_little_alert():
    user_id = current_user.id

    if user_id is None:
        return jsonify({'error': 'User not logged in'}), 401


    if request.method == 'POST':
        # Mark all non-viewed alerts for the current user as viewed
        alerts = LittleAlerts.query.filter_by(userID=user_id, viewed=False).all()
        for alert in alerts:
            alert.viewed = True
        db.session.commit()
        return jsonify({'status': 'success'})

    # Query non-viewed alerts for the current user
    alerts = LittleAlerts.query.filter_by(userID=user_id, viewed=False).all()

    # Format alerts for JSON response
    alerts_data = [{
        'date_time': alert.date_time.strftime('%B %d, %Y'),
        'message': alert.message
    } for alert in alerts]

    # db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just viewed the little alert " + fileName,  date=datetime.utcnow()))
    # db.session.commit() 
    

    return jsonify(alerts_data)

@app.route("/edit_student_info", methods = ["POST", 'GET'])
@login_required
def edit_student_info(): 
    check_maintenance()
    #role_required("student", "ACTION: editing student info")
    data = request.get_json()
    
    studentID = data['studentID']
    key = data['key']
    value = data['value']

    if value == "True":
        value = True
    elif value == "False":
        value = False
        
    if key == 'email' or key == 'password':
        stmt = update(User).values({key : value}).where(User.id == getUserID('student', studentID))
        db.session.execute(stmt)
        
    if key == 'description':
        value = value.replace('\n', '<br>')  # Convert new lines to <br> for HTML rendering later

    
    
    stmt = update(Students).values({key : value}).where(Students.id == studentID)
    db.session.execute(stmt)
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just changed the " + key + " for " + getStudent(studentID) + " to " + str(value),   date=datetime.utcnow()))
    db.session.commit()
    
    
    return ""

@app.route("/edit_exam_student_info", methods=["POST"])
@login_required
def edit_exam_student_info():
    check_maintenance()
    data = request.get_json()
    
    studentID = data['studentID']
    key = data['key']
    value = data['value']

    if value == "True":
        value = True
    elif value == "False":
        value = False
    
    stmt = update(exam_student).values({key: value}).where(exam_student.studentID == studentID)
    db.session.execute(stmt)
    
    db.session.add(log(role=getUserRole(current_user.id), 
                       message=f" ({getUserName(current_user.id)}): has just changed the {key} for {getStudent(studentID)} to {value}", 
                       date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@app.route("/update_student_and_ucas", methods=["POST"])
@login_required
def update_student_and_ucas():
    check_maintenance()
    
    # Get the JSON data from the request
    data = request.get_json()
    
    studentID = data.get('studentID')
    
    # Extract fields for Students table
    student_fields = {
        'firstName' : data.get('firstName'), 
        'secondName' : data.get('lastName'),
        'email' : data.get('email'),
        'parent_email' : data.get('parent_email'),        
        'date_of_birth': data.get('date_of_birth'),
        'gender': data.get('gender'),
        # Add other student fields if needed
    }
    
    # Extract fields for ExamStudent table
    ucas_fields = {
        'uci': data.get('uci'),
        'uln': data.get('uln'),
        'access_arrangements': data.get('access_arrangements'),
        'message': data.get('message'),
        'candidate_number': data.get('candidate_number'), 
        'notes': data.get('notes')

        # Add other UCAS-related fields if needed
    }

    # Update Students table
    if studentID:
        stmt_student = update(Students).values({k: v for k, v in student_fields.items() if v is not None}).where(Students.id == studentID)
        db.session.execute(stmt_student)
    
    # Update ExamStudent table
    if studentID:
        stmt_ucas = update(exam_student).values({k: v for k, v in ucas_fields.items() if v is not None}).where(exam_student.studentID == studentID)
        db.session.execute(stmt_ucas)

    # Commit the changes
    db.session.commit()

    # Log the action
    db.session.add(log(role=getUserRole(current_user.id), 
                       message=f" ({getUserName(current_user.id)}): updated information for {getStudent(studentID)}", 
                       date=datetime.utcnow()))
    db.session.commit()
    
    return "", 200
    
@app.route('/payslips/<userID>/<filename>')
@login_required
def payslipsView(userID, filename):
    # #role_required("tutor", "Payslips")
    if current_user.is_student(): 
        abort(400, )
    

    if str(userID) != str(current_user.id) and not permission_required(current_user.id, "view_below_payslips"):
        db.session.add(log(role = getUserRole(current_user.id), message= f" ({getUserName(current_user.id)}): has just tried to download the payslip for {filename} but was denied", date=datetime.utcnow()))
        db.session.commit()
        abort(400, "")

    
    
    path = 'payslips/' + str(userID) + "/" + filename 
    db.session.add(log(role = getUserRole(current_user.id), message= f" ({getUserName(current_user.id)}): has just downloaded the payslip for {filename}", date=datetime.utcnow()))
    db.session.commit()
    return send_file(path, as_attachment=True)

@app.route('/getFeedback', methods = ['POST', 'GET'])
@login_required
def readImage():
    check_maintenance()
    if request.method == "POST":
        # file = request.file
        image_data = request.json.get('image')

        image_binary = base64.b64decode(image_data.split(',')[1])

        
        filename = '/var/www/webApp/webApp/static/CS310images/' + str(datetime.utcnow()) + '.png'
        filename = filename.replace(" ", "_")
        
        # file.save('/var/www/webApp/webApp/CS310/images/' + datetime.utcnow())
        
        # Save the image to the specified file path
        with open(filename, 'wb') as f:
            f.write(image_binary)
            
        python38_path = "/var/www/webApp/webApp/CS310/mathreaderenv/bin/python3.8"

        # Specify the path to your script that requires TensorFlow 2.2.0
        script_path = "/var/www/webApp/webApp/CS310/mathreader-master/mathreader/example.py"

        # Construct the command to execute the script using the virtual environment's Python interpreter
        command = [python38_path, script_path, filename]

        # Call the script using subprocess
        result = subprocess.run(command) 

        f = open("/var/www/webApp/webApp/CS310/mathreader-master/mathreader/feedback.txt")
        feedback = f.read()
        

        if current_user.is_student():
            studentID = getOtherID("student", current_user.id)
        else:
            studentID = None

        if feedback.startswith("You are correct"):
            correct = True
        else:
            correct = False
        
        db.session.add(Feedback(filename, studentID, feedback, correct))
        db.session.commit()

        return jsonify({'text' : str(feedback)})
        
@app.route('/dismissAlert', methods = ['POST', 'GET'])
@login_required
def dismissAlert():
    check_maintenance()
    data = request.get_json()

    alertID = data['id']

    stmt = update(Alerts).values({"dismissed" : True}).where(Alerts.alertID == alertID)
    db.session.execute(stmt)

    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just dismissed the alert with title" + getAlertTitle(alertID),   date=datetime.utcnow()))
    db.session.commit()
    return ""

@app.route('/addRole', methods=['POST', 'GET'])
@login_required
def addRole():
    check_maintenance()
    data = request.get_json()

    name = data['name']
    level = data['level']

    db.session.add(Roles(name, level))

    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just created the role: " + name,   date=datetime.utcnow()))
    db.session.commit()
    return ""

@app.route('/save_document', methods=['POST'])
@login_required
def save_document():
    document_data = request.json
    title = document_data.get('title', 'Untitled Document')
    document_id = document_data.get('id')
    if document_id:
        document = Document.query.get(document_id)
        if document:
            document.title = title
            document.data = document_data
    else:
        document = Document(title=title, data=document_data)
        db.session.add(document)
    db.session.commit()
    return jsonify({'status': 'success', 'document_id': document.id})

@app.route('/delete_document/<int:document_id>', methods=['DELETE'])
@login_required
def delete_document(document_id):
    document = Document.query.get_or_404(document_id)
    db.session.delete(document)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/load_document/<int:document_id>', methods=['GET'])
@login_required
def load_document(document_id):
    document = Document.query.get(document_id)
    if document:
        return jsonify(document.data)
    return jsonify({'sections': []})

@app.route('/list_documents', methods=['GET'])
@login_required
def list_documents():
    if(getRoleLevel(getUserRole(current_user.id)) <= getRoleLevel('tutor')):
        documentList = individualDocument.query.filter_by(userID = current_user.id).all()
        documents = [Document.query.filter_by(id=doc.docID).first() for doc in documentList]
        
        documentList2 = Document.query.filter_by(individual = False).all()
        for doc in documentList2: 
            documents.append(doc)
    else: 
        documents = Document.query.all()

    return jsonify([{'id': doc.id, 'title': doc.title, 'created_at': doc.created_at, 'sign' : doc.sign} for doc in documents])

@app.route('/save-signature/<int:id>', methods=['POST'])
def save_signature(id):
    data = request.json['imageData']
    if data:
        # Extract base64 part
        header, encoded = data.split(",", 1)
        signature_data = base64.b64decode(encoded)

        file_path = f'var/www/webApp/webApp/userFiles/{current_user.id}/doc-{id}-signature.png'

        with open(file_path, 'wb') as f:
            f.write(signature_data)

        db.session.add(log(role = getUserRole(current_user.id), message= f" ({getUserName(current_user.id)}):  has just signed the document {getDoc(id)}",   date=datetime.utcnow()))
        db.session.commit()

        return jsonify(success=True)

    return jsonify(success=False), 400

@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    userID = request.form['tutor_id']
    file = request.files['file']
    
    # Ensure the directory exists
    user_files_dir = f'userFiles/{userID}/'
    os.makedirs(user_files_dir, exist_ok=True)

    # Save the file
    if file and file.filename.endswith('.jpg'):
        file_path = os.path.join(user_files_dir, 'profile_picture.jpg')
        file.save(file_path)
        flash('Profile picture uploaded successfully!', 'success')
    else:
        flash('Invalid file format. Please upload a JPG image.', 'danger')

    return ""  # Redirect to the appropriate page

@app.route('/uploadUserFiles', methods=['POST'])
@login_required
def upload_user_files():
    try: 
        userID = request.form.get('userID')
    except:
        userID = None
        
    try:
        otherID = request.form.get("otherID")
        role = request.form.get("role")
    except: 
        otherID = None
        role = ""
        
    if userID:
        user_files_path = os.path.join('/var/www/webApp/webApp/userFiles', str(userID))
    elif otherID:
        user_files_path = os.path.join('/var/www/webApp/webApp/userFiles', str(getUserID(role, int(otherID))))
    else: 
        abort(404, )

    if not os.path.exists(user_files_path):
        os.makedirs(user_files_path)  # Create directory if it doesn't exist

    # Save each uploaded file
    for file in request.files.getlist('file'):
        filename = file.filename
        file.save(os.path.join(user_files_path, filename))

    return redirect(request.referrer)  # Redirect back to the page

CORS(app, resources={r"/send-grade-boundaries": {"origins": "https://ateamacademy.co.uk"}})
@app.route('/send-grade-boundaries', methods = ['POST', 'GET'])
def send_grade_boundaries():
    data = request.json
    email = data.get('email')
    
    grade_boundaries = '''
    
    Please find attached the full grade boundaries for AQA, Edexcel and OCR
    
    '''
    
    if email:
        
        db.session.add(MailingList(email=email))
        db.session.commit()
        
        
        files = ['/var/www/webApp/webApp/grade-boundaries/edexcel_grade_boundaries.pdf', 
                 '/var/www/webApp/webApp/grade-boundaries/aqa_grade_boundaries.pdf', 
                 '/var/www/webApp/webApp/grade-boundaries/ocr_grade_boundaries.pdf'] 

    
        e1 = EmailSender()
        e1.send(email, "Grade Boundaries", grade_boundaries, files)
        
        return jsonify({'success': True}), 200
    else:
        return jsonify({'error': 'Invalid email address'}), 400

@app.route('/create_centre', methods=['POST'])
@login_required
def create_centre():
    if current_user.is_admin():
        name = (request.form.get('name') or '').strip()[:30]
        capacity = request.form.get('capacity')
        room_number = request.form.get('room_number', 0)
        address = (request.form.get('address') or '')[:100]
        admin_id = request.form.get('admin_id', 1)
        alias = request.form.get('alias', '')

        new_centre = Centre(name=name, capacity=capacity, room_number=room_number, address=address, admin_id=admin_id, alias=alias)
        db.session.add(new_centre)
        db.session.commit()

        
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just created the centre: " + name,   date=datetime.utcnow()))
        db.session.commit()

        return redirect(_safe_next('centre_overview'))
    else:
        abort(400, )


@app.route('/edit_centre', methods=['POST'])
@login_required
def edit_centre():
    # Rename / re-address a centre. Centres could only ever be created, never
    # edited, which left mis-named centres stuck in every dropdown.
    if not current_user.is_admin():
        abort(403)
    try:
        centre_id = int(request.form.get('centreID'))
    except (TypeError, ValueError):
        abort(400)
    centre = Centre.query.get_or_404(centre_id)

    old_name = centre.name
    # clamp to the column sizes (String(30)/String(100)) so Postgres can't 500
    name = (request.form.get('name') or '').strip()[:30]
    if name:
        centre.name = name
    if request.form.get('address') is not None:
        centre.address = request.form.get('address').strip()[:100]
    capacity = request.form.get('capacity')
    if capacity:
        try:
            centre.capacity = int(capacity)
        except ValueError:
            pass
    db.session.commit()

    db.session.add(log(role=getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}): updated centre '{old_name}' -> '{centre.name}'", date=datetime.utcnow()))
    db.session.commit()
    flash('Centre updated.', 'success')
    return redirect(_safe_next('centre_overview'))

@app.route('/register_trial_session', methods=['POST'])
@login_required
def register_trial_session():
    data = request.get_json()
    
    lesson_id = data.get('lessonID')
    student_id = data.get('studentID')
    unregistered_name = data.get('unregisteredName')
    week_no = data.get('weekNo')
    notes = data.get('notes')

    if student_id:
        # Registered student handling
        db.session.add(StudentLesson(studentID=student_id, lessonID=lesson_id))
        db.session.add(StudentAttendance(
            lessonID=lesson_id,
            weekNo=week_no,
            AcademicYear=gen_relative_academic_year(0),
            studentID=student_id,
            present=False,
            extra_notes=notes
        ))
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just registered " + getStudent(student_id) + f" for the lesson {getLessonString(lesson_id)} for week " + week_no,   date=datetime.utcnow()))

    else:
        # Unregistered student handling
        new_unregistered_student = unregisteredStudentLessons(
            studentName=unregistered_name,
            lessonID=lesson_id
        )
        db.session.add(new_unregistered_student)
        db.session.add(UnregisteredAttendance(
            lessonID=lesson_id,
            weekNo=week_no,
            AcademicYear=gen_relative_academic_year(0),
            studentName=unregistered_name,
            present=False,
            extra_notes=notes
        ))

        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just registered " + unregistered_name + f" for the lesson {getLessonString(lesson_id)} for week " + week_no,   date=datetime.utcnow()))

    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/submit_ucas_reference', methods=['POST'])
def submit_ucas_reference():
    data = request.get_json()

    try:
        # Extract data from the request
        name = data['name']
        subjects = data['subjects']  # This is already a single string of subjects separated by commas
        qualifications = data['qualifications']
        work_experience = data['work_experience']
        course = data['course']
        reason = data['reason']
        hobbies = data['hobbies']
        extra_info = data['extra_info']

        # Here you would normally save the data to the database
        # For example:
        new_reference = UCASReference(
            name=name,
            subjects=subjects,
            qualifications=qualifications,
            work_experience=work_experience,
            course=course,
            reason=reason,
            hobbies=hobbies,
            extra_info=extra_info
        )
        db.session.add(new_reference)
        db.session.commit()
        
        db.session.add(log(role = "anonymous", message=f" {name} has just submitted a UCAS reference",  date=datetime.utcnow()))
        db.session.commit()

        return jsonify({"message": "UCAS reference submitted successfully!", "success" : True}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route('/update_student_paid_status', methods=['POST'])
@login_required
def update_student_paid_status():
    data = request.get_json()
    studentID = data['studentID']
    isPaid = data['paid']
    
    stmt = update(exam_student).where(exam_student.studentID == studentID).values(paid=isPaid)
    db.session.execute(stmt)
    db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}):  has just set the paid status for {getStudent(studentID)} to {str(isPaid)} ",  date=datetime.utcnow()))
    db.session.commit()
    
    return jsonify({'message': 'Paid status updated successfully'}), 200

@app.route('/update_exam/<int:exam_id>', methods=['POST'])
def update_exam(exam_id):
    data = request.json
    # Find and update the exam in the database
    exam = Exams.query.get(exam_id)
    exam.tier = data['tier']
    exam.title = data['title']
    exam.examBoard = data['examBoard']
    exam.code = data['code']
    exam.Option = data['Option']
    exam.examSeries = data['examSeries']
    exam.AcademicYear = data['AcademicYear']
    
    db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}):  has just updated the exam {getExam} ",  date=datetime.utcnow()))
    db.session.commit()
    
    return jsonify({"message": "Exam updated successfully"}), 200

@app.route('/delete_exam/<int:exam_id>', methods=['POST'])
def delete_exam(exam_id):
    # Create the update statement to set 'active' to False
    stmt = (
        update(Exams)
        .where(Exams.examID == exam_id)
        .values(active=False)
    )
    
    # Execute the update statement
    db.session.execute(stmt)
    db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}):  has just deleted the exam {getExam(exam_id)} (set active to False) ",  date=datetime.utcnow()))
    db.session.commit()

    return jsonify({"message": "Exam deleted (soft delete) successfully"}), 200

@app.route('/get_papers/<int:exam_id>', methods=['GET'])
@login_required
def get_papers(exam_id):
    papers = ExamPapers.query.filter_by(examID=exam_id).all()
    papers_data = [
        {
            'paperNo': paper.paperNo,
            'paperCode': paper.paperCode,
            'duration': paper.duration,
            'startTime' : str(paper.startTime),
            'total': paper.total,
            'date': paper.date.isoformat(),
            'extra_info': paper.extra_info
        }
        for paper in papers
    ]
    
    
    return jsonify(papers_data)

@app.route('/update_papers/<int:exam_id>', methods=['POST'])
@login_required
def update_papers(exam_id):
    data = request.get_json()
    papers = data.get('papers', [])

    # Delete existing papers for the exam
    ExamPapers.query.filter_by(examID=exam_id).delete()

    # Add new papers
    for paper in papers:
        new_paper = ExamPapers(
            examID=exam_id,
            paperNo=paper.get('paperNo'),
            paperCode=paper.get('paperCode'),
            duration=paper.get('duration'),
            startTime = paper.get('startTime'),
            total=paper.get('total'),
            date=datetime.strptime(paper.get('date'), '%Y-%m-%d').date(),
            extra_info=paper.get('extra_info')
        )
        db.session.add(new_paper)

    db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}):  has just updates the papers for {getExam(exam_id)} ",  date=datetime.utcnow()))
    db.session.commit()

    return jsonify({'status': 'success'})

# Update paid amount
@app.route('/update_student_paid_amount', methods=['POST'])
@login_required
def update_student_paid_amount():
    data = request.get_json()
    studentID = data['studentID']
    paidAmount = data['paidAmount']
    
    stmt = update(exam_student).where(exam_student.studentID == studentID).values(paid_amount=int(paidAmount))
    db.session.execute(stmt)
    db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}):  has just updated the paid amount to {paidAmount} for {getStudent(studentID)} ",  date=datetime.utcnow()))
    db.session.commit()
    
    return jsonify({'message': 'Paid amount updated successfully'}), 200

# Update reference required status
@app.route('/update_reference_required_status', methods=['POST'])
@login_required
def update_reference_required_status():
    data = request.get_json()
    studentID = data['studentID']
    referenceRequired = data['referenceRequired']
    
    stmt = update(exam_student).where(exam_student.studentID == studentID).values(reference_required=referenceRequired)
    db.session.execute(stmt)
    db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}):  has just updated the reference status for {getStudent(studentID)} to {referenceRequired}",  date=datetime.utcnow()))
    db.session.commit()
    
    return jsonify({'message': 'Reference requirement updated successfully'}), 200

# Assign UCAS reference
@app.route('/assign_ucas_reference', methods=['POST'])
@login_required
def assign_ucas_reference():
    data = request.get_json()
    studentID = data['studentID']
    referenceID = data['referenceID']
    
    stmt = update(exam_student).where(exam_student.studentID == studentID).values(reference_id=referenceID)
    db.session.execute(stmt)
    db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}):  has just linked a reference to {getStudent(studentID)} ",  date=datetime.utcnow()))
    db.session.commit()
    
    return jsonify({'message': 'UCAS reference assigned successfully'}), 200

@app.route('/assign_exams', methods=['POST'])
@login_required
def assign_exams():
    data = request.get_json()
    studentID = data['studentID']
    examIDs = data['examIDs']
    

    # First, remove any existing exam assignments for this student
    db.session.query(studentExam).filter_by(studentID=studentID).delete()

    # Create new student-exam entries
    for examID in examIDs:
        new_student_exam = studentExam(studentID=studentID, examID=examID)
        db.session.add(new_student_exam)
    try:
        db.session.commit()
        db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}):  has just added  { ', '.join([getExam(examID) for examID in examIDs])} to {getStudent(studentID)}",  date=datetime.utcnow()))
        db.session.commit()

        # Warn the officer immediately if this assignment creates timetable
        # clashes (overlapping or same-day papers) for the student.
        clash_msgs = []
        try:
            for clash in group_clashes(_gather_clash_entries(student_id=int(studentID))):
                papers = "  vs  ".join(
                    f"{p['exam']} {p['paper_code']} ({time_range_str(clash['date'], p['start'], p['duration'])})"
                    for p in clash['papers'])
                kind = "OVERLAP" if clash['severity'] == 'overlap' else "same day"
                clash_msgs.append(f"{clash['date'].strftime('%d %b %Y')} ({kind}): {papers}")
        except Exception as clash_err:  # warnings must never block the save
            print(f"clash check failed (non-fatal): {clash_err}")

        return jsonify({'message': 'Exams assigned successfully', 'clashes': clash_msgs}), 200
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': str(e)}), 500
    
@app.route('/updateCandidateNumber/<int:student_id>', methods=['POST'])
def update_candidate_number(student_id):
    data = request.get_json()
    new_candidate_number = data.get('candidate_number')

    # Assuming you have a Student model
    student = exam_student.query.get(student_id)
    if student:
        student.candidate_number = new_candidate_number
        db.session.commit()
        
        db.session.add(log(role = getUserRole(current_user.id), message=f" ({getUserName(current_user.id)}):  has just updated the candidate number for {getStudent(student_id)} to {new_candidate_number}",  date=datetime.utcnow()))
        db.session.commit()
        return jsonify({"message": "Candidate number updated successfully"}), 200
    else:
        return jsonify({"error": "Student not found"}), 404    
    
@app.route('/get_student_data/<int:student_id>', methods=['GET'])
@login_required
def get_student_data(student_id):
    # Assuming you have a Student model with the necessary fields
    student = exam_student.query.get(student_id)
    
    if student is None:
        return jsonify({"error": "Student not found"}), 404

    # Create a dictionary to send back the relevant data
    student_data = {
        'uci': student.uci,
        'uln': student.uln,
        'access_arrangements': student.access_arrangements,
        'message': student.message
    }

    return jsonify(student_data)

@app.route('/download_exam_students_csv', methods=['GET'])
@login_required
def download_exam_students_csv():
    permission_required(current_user.id, "view_all_student_information", fatal=True)
    students = get_exam_students()  # Assuming this function returns all students
    csv_data = StringIO()
    writer = csv.writer(csv_data)
    
    # Write CSV header
    writer.writerow([
        'CN', 'Surname', 'Given Name', 'UCI No', 'D.O.B', 'Gender', 
        'Qualification', 'subject', 'Option', 'Entry code', 'Tier', 'Series', 'Email', 'Parent Email', 'Phone'
        'Contact number', 'Access Arrangement', 'Extra Notes', 'message'
    ])
    
    # Loop through students and their exams
    for student in students:
        student_id = student[0]['id']
        exams = getExamsForStudent(student_id)  # List of exam IDs the student is registered for
        
        if exams:  # If student has registered exams
            for exam_id in exams:
                exam = Exams.query.get(exam_id)  # Get exam details

                # Write each exam detail row
                writer.writerow([
                    student[1]['candidate_number'],  # CN
                    student[0]['secondName'],           # Surname
                    student[0]['firstName'],         # Given Name
                    student[1]['uci'],        # UCI No
                    student[0]['date_of_birth'],     # D.O.B
                    student[0]['gender'],            # Gender
                    exam.examBoard + " - " + exam.tier,        # Qualification
                    exam.title,
                    exam.Option,                # Subject
                    exam.code,                 # Entry code
                    exam.tier,                 # Tier
                    exam.examSeries,
                    student[0]['email'],             # Email
                    student[0]['parent_email'], 
                    student[0]['priority_contact_1_mobile_telephone'],    # Contact number
                    student[1]['access_arrangements'], # Access Arrangement, 
                    student[1]['notes'], 
                    student[1]['message']
                ])
    
    # Create the response with the CSV content
    csv_data.seek(0)
    return Response(csv_data, mimetype="text/csv", headers={
        "Content-disposition": "attachment; filename=exam_students.csv"
    })

@app.route('/download_emails', methods=['GET'])
@login_required
def download_emails():
    role_required("admin", "download emails")
    csv_data = StringIO()
    writer = csv.writer(csv_data)

    students = Students.query.all()
      
    
    # Loop through students and their exams
    for student in students:
        student_id = student.id
        
        # Write each exam detail row
        writer.writerow([
            getStudentEmail(student_id)
        ])

        writer.writerow([
            getStudentParentEmail(student_id)
        ])


    enquiries = Enquiry.query.all()

    for enquiry in enquiries:
        writer.writerow([
            enquiry.parent_email
        ])



    games = GameScores.query.all()

    for game in games:
        writer.writerow([
            game.email
        ])


    mail_list = MailingList.query.all()

    for mail in mail_list:
        writer.writerow([
            mail.email
        ])



    
    # Create the response with the CSV content
    csv_data.seek(0)
    return Response(csv_data, mimetype="text/csv", headers={
        "Content-disposition": "attachment; filename=emails.csv"
    })

@app.route('/download_tutor_hours_csv/<int:month>', methods=['GET'])
@login_required
def download_tutor_hours_csv(month):
    """
    Generates a CSV file for a specific month containing tutor hours per day.
    """
    if month < 1 or month > 12:
        return Response("Invalid month. Please provide a month between 1 and 12.", status=400)

    tutors = getAllUsers(role="tutor", log_on=True)
    tutors = sorted(tutors, key=lambda x : x.firstName)
    day = date.today()
    year = day.year if month >= 9 else day.year - 1  # Assume academic year logic
    
    # Get the number of days in the provided month
    last_day = calendar.monthrange(year, month)[1]
    days_in_month = [datetime(year, month, day) for day in range(1, last_day + 1)]

    # Create header dynamically
    header = ["Tutor Name"] + [
        day.strftime("%b %d") for day in days_in_month
    ]

    # Collect tutor data
    rows = []
    for tutor in tutors:
        tutor_name = f"{tutor.firstName} {tutor.secondName}"
        row = [tutor_name]
        month_hours = 0

        for current_date in days_in_month:
            current_date_only = current_date.date()  # Convert to `datetime.date`
            week_no = dateToWeekNo(current_date_only)  # Pass `datetime.date` to this function
            day_name = dateToDay(current_date_only.strftime("%d/%m/%Y"))  # Ensure consistent format

            # Query lessons for the current day
            lessons = LessonInfo.query.filter_by(
                tutorID=tutor.id, weekNo=week_no, approved=True, day=day_name
            ).all()

            # Sum up durations of lessons with attendance
            daily_hours = 0
            for lesson in lessons:
                if lesson.approved and getLessonYear(lesson.lessonID) == gen_academic_year():
                    daily_hours += lesson.duration
                    month_hours += lesson.duration

            if daily_hours > 0: 
                row.append(daily_hours)
            else: 
                row.append("")
        
        row.append("")
        row.append(month_hours)

        rows.append(row)

    # Write the CSV to a StringIO object
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(header)  # Write the header
    writer.writerows(rows)   # Write the tutor rows

    # Reset the pointer to the beginning of the StringIO object
    output.seek(0)

    # Return the CSV as a downloadable file
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment;filename=tutor_hours_{calendar.month_abbr[month].lower()}.csv"})

@app.route('/getTimetablePreview/<int:student_id>')
@login_required
def get_timetable_preview(student_id):
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    
    if not start_date or not end_date:
        html_timetable = generate_html_exam_timetable(student_id)  # Generate the HTML for the timetable
    else:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
        
        html_timetable = generate_html_exam_timetable(student_id, start_date, end_date)
        
        
    return html_timetable

@app.route('/sendEmailTimetable/<int:student_id>', methods=['GET', 'POST'])
def send_email_timetable(student_id):
    e1 = EmailSender(mode="examsofficer")
    data = request.json
    try:
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        cc_opt_out = data.get('opt_out', False)
    except:
        return jsonify({"error": "Invalid data format provided."}), 400

    # Fetch email addresses
    try:
        student_email = getStudentEmail(student_id)
        parent_email = getStudentParentEmail(student_id)
        contact_email = getStudentPriorityEmail(student_id)
    except Exception as e:
        return jsonify({"error": f"Error fetching student email: {str(e)}"}), 500

    # Generate timetable
    try:
        if not start_date or not end_date:
            timetable_html = generate_html_exam_timetable(student_id)
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            timetable_html = generate_html_exam_timetable(student_id, start_date, end_date)
    except Exception as e:
        return jsonify({"error": f"Error generating timetable: {str(e)}"}), 500

    # Attach files
    try:
        files = [
            '/var/www/webApp/webApp/files/EXAM_FILES/IFC-Coursework_Assessments_2024_FINAL (1).pdf', 
            '/var/www/webApp/webApp/files/EXAM_FILES/IFC-Written_Examinations_2024_FINAL.pdf', 
            '/var/www/webApp/webApp/files/EXAM_FILES/JCQ-Social-Media-Infographic-v6.pdf', 
            '/var/www/webApp/webApp/files/EXAM_FILES/Preparing-to-sit-your-exams-2024_25.pdf'
        ]
        valid_files = [file for file in files if os.path.exists(file)]
    except Exception as e:
        return jsonify({"error": f"Error processing file attachments: {str(e)}"}), 500

    # Validate emails
    recipient_emails = [
        email for email in [student_email, parent_email, contact_email]
        if is_valid_email(email)
    ]
    if not recipient_emails:
        return jsonify({"error": "No valid email addresses provided."}), 400

    # Send email
    try:
        e1.send(recipient_emails, 'Exam Timetable', timetable_html, files=valid_files)
    except Exception as e:
        return jsonify({"error": f"Error sending email: {str(e)}"}), 500

    return jsonify({"message": "Email sent successfully!"}), 200

@app.route('/update_points', methods=['POST'])
@login_required
def update_points():
    role_required("admin", "ACTION: Updating Points")
    data = request.get_json()
    user_id = data['userId']
    action = data['action']
    amount = int(data['amount'])
    reason = data['reason']
    
    # Fetch the user
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Update points based on action

    # if action == 'add': 
    #     stmt = update(User).values({'points' : user.points + amount }).where(User.id == user_id)
    # else: 
    
    stmt = update(User).values({'points' : user.points + amount }).where(User.id == user_id)

    db.session.execute(stmt)    
    db.session.commit()
    
    # Log the alert
    little_alert = LittleAlerts(
        userID=user_id,
        message=f'points were changd by {str(amount)} beacuse of {reason}',
    )
    db.session.add(little_alert)
    db.session.commit()
    
    db.session.add(log(role=getUserRole(current_user.id), 
                    message=f" ({getUserName(current_user.id)}): updated points for {getUserName(user_id)} by {str(amount)}", 
                    date=datetime.utcnow()))
    db.session.commit()

    
    return jsonify({'new_points': user.points, 'message': 'Points updated successfully'})

@app.route('/view_ucas_references', methods=['GET'])
@login_required
def view_ucas_references():
    # Fetch UCAS references from the database
    ucas_references = UCASReference.query.all()

    # Replace actual newlines with \n in each field
    for reference in ucas_references:
        reference.qualifications = reference.qualifications.replace('\n', '\\n').replace("(", "[").replace(")", "]") if reference.qualifications else ''
        reference.work_experience = reference.work_experience.replace('\n', '\\n').replace("(", "[").replace(")", "]") if reference.work_experience else ''
        reference.reason = reference.reason.replace('\n', '\\n').replace("(", "[").replace(")", "]") if reference.reason else ''
        reference.hobbies = reference.hobbies.replace('\n', '\\n').replace("(", "[").replace(")", "]") if reference.hobbies else ''
        reference.extra_info = reference.extra_info.replace('\n', '\\n').replace("(", "[").replace(")", "]") if reference.extra_info else ''

    return render_template('view_ucas_references.html', references=sorted(ucas_references, key=lambda x : x.name))

@app.route('/apply_tutor', methods=['POST']) 
@login_required
def apply_tutor():
    # Extract form data
    name = request.form['name']
    date_of_birth = request.form['date_of_birth']
    subjects = request.form['subjects']
    email = request.form['email']  # Assuming you're adding an email field to the form

    # Access the files
    cv_file = request.files['cv']
    dbs_file = request.files['dbs']
    cover_letter_file = request.files['cover_letter']

    # Check if the tutor already exists by email
    tutorExists = User.query.filter_by(email=email.lower().strip()).first()
    
    if tutorExists:
        return jsonify({'message': 'User with that email already exists!'}), 400
    
    # Generate a random password
    password = gen_random_password(8)
    
    # Add to the Staff table as 'provisional tutor'
    provisional_tutor = Staff(
        role="provisional tutor",
        firstName=name,
        date_of_birth=date_of_birth,
        email=email,
        subjects=subjects,
        # Add more fields if needed
    )
    db.session.add(provisional_tutor)
    db.session.commit()
    
    # Get the tutor's ID after committing to Staff table
    tutor_id = provisional_tutor.id
    
    # Add to the User table
    user = User(
        role="provisional tutor",
        otherID=tutor_id,  # Link to the tutor ID
        email=email.lower().strip(),
        password=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()

    # Create a directory to store the files (if needed)
    user_files_path = f'/var/www/webApp/webApp/userFiles/{user.id}/'
    os.makedirs(user_files_path, exist_ok=True)

    cv_file.save(os.path.join(user_files_path, secure_filename('cv.pdf')))
    dbs_file.save(os.path.join(user_files_path, secure_filename('dbs.pdf')))
    cover_letter_file.save(os.path.join(user_files_path, secure_filename('cover_letter.pdf')))

    # Send a registration email (if needed)
    e1 = EmailSender()
    e1.send(email=email, subject="Tutor Application Received", message=gen_html_tutor_registration(name, password))
    
    return jsonify({'message': 'Tutor application submitted successfully!'}), 200

@app.route('/submit_staff_review', methods=['POST'])
@login_required
def submit_staff_review():
    role_required("receptionist", "Submitting a Staff Review")
    data = request.get_json()
    
    # Validate that all fields are provided
    required_fields = ["staffID", "PunctualityScore", "LessonQualityScore", "LessonPreparednessScore", "ProfessionalismScore", "TestScoresAverage"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"{field} is required"}), 400
    
    # Create and save the review
    review = StaffReviews(
        staffID=data["staffID"],
        date=datetime.today(),
        PunctualityScore=data["PunctualityScore"],
        PunctualityComments=data.get("PunctualityComments", ""),
        LessonQualityScore=data["LessonQualityScore"],
        LessonQualityComments=data.get("LessonQualityComments", ""),
        LessonPreparednessScore=data["LessonPreparednessScore"],
        LessonPreparednessComments=data.get("LessonPreparednessComments", ""),
        ProfessionalismScore=data["ProfessionalismScore"],
        ProfessionalismComments=data.get("ProfessionalismComments", ""),
        TestScoresAverage=float(data["TestScoresAverage"]),
        TestScoresComments=data.get("TestScoresComments", ""),
        extraComments = data.get("extraComments", "")
    )
    
    db.session.add(review)
    db.session.commit()
    
    return jsonify({"message": "Review submitted successfully!"}), 200

@app.route('/save_point', methods=['POST'])    
@login_required                      
def save_point():
    data = request.get_json()
    reason = data['reason']
    amount = data['amount']
    original_reason = data.get('originalReason')

    if original_reason:
        # Editing an existing point
        point = PointSystem.query.get(original_reason)
        if point:
            point.reason = reason
            point.amount = amount
        else:
            return jsonify({'error': 'Point not found'}), 404
    else:
        # Adding a new point
        point = PointSystem(reason=reason, amount=amount)
        db.session.add(point)

    db.session.commit()
    return jsonify({'success': True})

@app.route('/delete_point/<string:reason>', methods=['DELETE'])
@login_required
def delete_point(reason):
    point = PointSystem.query.get(reason)
    if point:
        db.session.delete(point)
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Point not found'}), 404

@app.route('/get_room_arrangements', methods=['GET'])
@login_required
def get_room_arrangements():
    date_str = request.args.get('date')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

    room_arrangements = RoomArrangements.query.filter_by(date=date_obj).all()
    
    if not room_arrangements:
        # Default configuration (if no arrangements found for the date)
        default_rooms = ExamRoom.query.all()
        for room in default_rooms:
            new_arrangement = RoomArrangements(
                date=date_obj,
                room_id=room.id,
                actual_rows=room.max_rows,
                actual_columns=room.max_columns
            )
            db.session.add(new_arrangement)
        db.session.commit()
        room_arrangements = RoomArrangements.query.filter_by(date=date_obj).all()

    arrangements = [{
        'room_id': arrangement.room_id,
        'room_name': arrangement.exam_room.name,
        'rows': arrangement.actual_rows or arrangement.exam_room.max_rows,
        'columns': arrangement.actual_columns or arrangement.exam_room.max_columns
    } for arrangement in room_arrangements]

    return jsonify(arrangements)

def _resolve_centre_id(raw):
    """Parse a centre id from a request value; '', 'all' or bad input -> None (all centres)."""
    if raw is None:
        return None
    raw = str(raw).strip()
    if raw == "" or raw.lower() == "all":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _centre_name(centre_id):
    if not centre_id:
        return None
    centre = Centre.query.filter_by(centreID=centre_id).first()
    return centre.name if centre else None


def _safe_next(default_endpoint):
    """Post-action redirect target: only same-site paths, else the default page."""
    nxt = request.form.get('next') or ''
    if nxt.startswith('/') and not nxt.startswith('//'):
        return nxt
    return url_for(default_endpoint)


# Access-arrangement text that actually means "no arrangement" (legacy data stores
# the literal string "None"), so those candidates aren't wrongly held back.
_NO_ACCESS = ("", "none", "n/a", "na", "-", "no", "nil", "null")


def _has_access(text):
    return (text or "").strip().lower() not in _NO_ACCESS


def _gather_seating_context(date_str, centre_id=None):
    """Collect the rooms + candidates for one exam date (optionally a single centre).

    Returns (rooms, students, seat_map):
      rooms    - [{room_id, room_name, centreID, centre, rows, columns}]
      students - one dict per candidate registered that day, with candidate number,
                 board, exam_id, access-arrangement text and an `access` flag
      seat_map - {student_id: {room_id, row, column}} for already-saved seats in scope
    """
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

    # Rooms (honouring any per-date row/column override), filtered to the centre.
    rooms = []
    room_query = ExamRoom.query
    if centre_id:
        room_query = room_query.filter_by(centreID=centre_id)
    for room in room_query.all():
        override = RoomArrangements.query.filter_by(room_id=room.id, date=date_obj).first()
        rooms.append({
            'room_id': room.id,
            'room_name': room.name,
            'centreID': room.centreID,
            'centre': _centre_name(room.centreID),
            'rows': (override.actual_rows if override and override.actual_rows else room.max_rows),
            'columns': (override.actual_columns if override and override.actual_columns else room.max_columns),
        })

    # Candidates registered for any paper sat on this date (one row per candidate).
    papers = ExamPapers.query.filter_by(date=date_obj).all()
    paper_exam_ids = list({p.examID for p in papers})
    exams_by_id = ({e.examID: e for e in
                    Exams.query.filter(Exams.examID.in_(paper_exam_ids)).all()}
                   if paper_exam_ids else {})

    reg_pairs = []          # (paper, studentID) for every registration that day
    exams_of_student = {}   # sid -> distinct examIDs that day; 2+ = clash to check
                            # (same exam's own papers on one day is normal, so we
                            #  count exams — matching the clashes page's rule)
    for paper in papers:
        for reg in studentExam.query.filter_by(examID=paper.examID).all():
            reg_pairs.append((paper, reg.studentID))
            exams_of_student.setdefault(reg.studentID, set()).add(paper.examID)
    exams_today = {sid: len(ids) for sid, ids in exams_of_student.items()}

    students = []
    seen = set()
    for paper, sid in reg_pairs:
        if sid in seen:
            continue
        seen.add(sid)
        exam = exams_by_id.get(paper.examID)
        profile = exam_student.query.filter_by(studentID=sid).first()
        access_txt = (profile.access_arrangements if profile else None) or ""
        s_centre = profile.centreID if profile else None
        if centre_id and s_centre != centre_id:
            continue
        students.append({
            'id': sid,
            'name': getStudent(sid),
            'candidate_number': profile.candidate_number if profile else None,
            'board': exam.examBoard if exam else None,
            'title': exam.title if exam else None,
            'exam_id': paper.examID,
            'access_arrangements': access_txt,
            'access': _has_access(access_txt),
            'centreID': s_centre,
            'centre': _centre_name(s_centre),
            'exams_today': exams_today.get(sid, 1),
        })

    # Saved seats for the date, limited to the rooms in scope.
    room_ids = {r['room_id'] for r in rooms}
    seat_map = {}
    for seat in SeatingArrangement.query.filter_by(date=date_obj).all():
        if room_ids and seat.room_id not in room_ids:
            continue
        seat_map[seat.student_id] = {'room_id': seat.room_id, 'row': seat.row, 'column': seat.column}

    return rooms, students, seat_map, exams_today


@app.route('/get_seating_arrangements', methods=['GET'])
@login_required
def get_seating_arrangements():
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'A date is required'}), 400
    centre_id = _resolve_centre_id(request.args.get('centre'))

    try:
        rooms, students, seat_map, exams_today = _gather_seating_context(date, centre_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date'}), 400

    # Mark each candidate's allocation status + attach saved seat coordinates.
    for s in students:
        placed = seat_map.get(s['id'])
        s['allocated'] = placed is not None
        s['seat'] = placed

    # Build per-room seat lists for rendering the grids.
    student_by_id = {s['id']: s for s in students}
    room_by_id = {r['room_id']: r for r in rooms}
    for room in rooms:
        room['seats'] = []
    for sid, placed in seat_map.items():
        room = room_by_id.get(placed['room_id'])
        if room is None:
            continue
        s = student_by_id.get(sid)
        room['seats'].append({
            'row': placed['row'], 'column': placed['column'], 'student_id': sid,
            'name': s['name'] if s else getStudent(sid),
            'candidate_number': (s['candidate_number'] if s else getCandidateNumber(sid)),
            'board': s['board'] if s else None,
            'exam_id': s['exam_id'] if s else None,
            'access': s['access'] if s else False,
            'access_arrangements': s['access_arrangements'] if s else "",
            # counted over ALL of the day's registrations (not just the current
            # centre scope), so out-of-scope seated chips keep their clash flag
            'exams_today': exams_today.get(sid, 1),
        })

    return jsonify({'rooms': rooms, 'students': students})


@app.route('/auto_assign_seating', methods=['POST'])
@login_required
def auto_assign_seating():
    data = request.get_json() or {}
    date = data.get('date')
    if not date:
        return jsonify({'error': 'A date is required'}), 400
    centre_id = _resolve_centre_id(data.get('centre'))

    try:
        rooms, students, _, _ = _gather_seating_context(date, centre_id)
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date'}), 400

    if not rooms:
        return jsonify({'error': 'No exam rooms for this centre. Add rooms first.'}), 400

    # Group by board, sort by candidate number, balance across the fewest rooms.
    # Access-arrangement candidates are deliberately left for the officer to place.
    result = plan_seating(students, rooms)

    room_ids = [r['room_id'] for r in rooms]
    if room_ids:
        SeatingArrangement.query.filter(
            SeatingArrangement.date == date_obj,
            SeatingArrangement.room_id.in_(room_ids),
        ).delete(synchronize_session=False)

    for seat in result['seats']:
        db.session.add(SeatingArrangement(
            student_id=seat['student_id'],
            exam_id=seat['exam_id'],
            room_id=seat['room_id'],
            row=seat['row'],
            column=seat['column'],
            date=date_obj,
        ))
    db.session.commit()

    access_students = [s for s in students if s['access']]
    return jsonify({
        'status': 'success',
        'seated': len(result['seats']),
        'unplaced': result['unplaced'],
        'access_count': len(access_students),
    })


@app.route('/save_seating_arrangement', methods=['POST'])
@login_required
def save_seating_arrangement():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    # Accept the current layout {date, centre, seats:[...]}. (The old client posted
    # a bare list of seats; keep that working too.)
    if isinstance(data, list):
        seats = data
        date = seats[0].get('date') if seats else None
        centre_id = None
    else:
        seats = data.get('seats', [])
        date = data.get('date')
        centre_id = _resolve_centre_id(data.get('centre'))

    if not date:
        return jsonify({'error': 'A date is required'}), 400
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid date'}), 400

    # Scope the wipe to the centre's rooms so saving one centre's plan can't clear
    # another centre's seats for the same day.
    q = SeatingArrangement.query.filter(SeatingArrangement.date == date_obj)
    if centre_id:
        scope_room_ids = [r.id for r in ExamRoom.query.filter_by(centreID=centre_id).all()]
        q = q.filter(SeatingArrangement.room_id.in_(scope_room_ids or [-1]))
    q.delete(synchronize_session=False)

    saved = 0
    for seat in seats:
        if seat.get('student_id') is None or seat.get('room_id') is None or seat.get('exam_id') is None:
            continue
        db.session.add(SeatingArrangement(
            student_id=seat['student_id'],
            exam_id=seat['exam_id'],
            room_id=seat['room_id'],
            row=seat.get('row', 0),
            column=seat.get('column', 0),
            date=date_obj,
        ))
        saved += 1

    db.session.commit()
    return jsonify({'status': 'success', 'saved': saved})



@app.route('/exam_rooms/edit/<int:room_id>', methods=['GET', 'POST'])
@login_required
def edit_exam_room(room_id):
    room = ExamRoom.query.get_or_404(room_id)
    if request.method == 'POST':
        room.name = request.form.get('name')
        room.max_rows = int(request.form.get('max_rows'))
        room.max_columns = int(request.form.get('max_columns'))
        room.centreID = _resolve_centre_id(request.form.get('centreID'))
        db.session.commit()
        flash("Exam room updated successfully!", "success")
        return redirect(url_for('manage_exam_rooms'))

    centres = Centre.query.order_by(Centre.name).all()
    return render_template('edit_exam_room.html', room=room, centres=centres)

@app.route('/exam_rooms/delete/<int:room_id>', methods=['POST'])
@login_required
def delete_exam_room(room_id):
    # destructive (removes saved seating plans too) — admins only
    if not current_user.is_admin():
        abort(403)
    room = ExamRoom.query.get_or_404(room_id)
    # clear dependent seating first so the FK doesn't block the delete
    SeatingArrangement.query.filter_by(room_id=room.id).delete()
    RoomArrangements.query.filter_by(room_id=room.id).delete()
    db.session.delete(room)
    db.session.commit()
    flash("Exam room deleted.", "danger")
    return redirect(url_for('manage_exam_rooms'))

@app.route('/start_breakout_rooms', methods = ['POST', 'GET'])
def start_breakout_rooms():
    e1 = EmailSender()
    
    e1.send("ateam1772@gmail.com", "Start Zoom Meeting", "this is a test to trigger the zoom meeting")
    return redirect('/allTimetable?offset=0')

@app.route('/generate_grades_report', methods=['GET'])
@login_required
def generate_grades_report():
    # Retrieve and format date parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

    # Query database for grades within date range
    student_reports = {}
    grades = (db.session.query(Grades, Tests)
              .join(Tests, Grades.testID == Tests.testID)
              .filter(Tests.date.between(start_date, end_date))
              .all())
    
    # Organize data by student
    for grade, test in grades:
        student_id = grade.studentID
        student_name = getStudent(grade.studentID)
        if student_id not in student_reports:
            student_reports[student_id] = {"studentName": student_name, "tests": []}
        
        if grade.mark != -1: 
            student_reports[student_id]["tests"].append({
                "name": test.name,
                "date": test.date.strftime('%Y-%m-%d'),
                "total": test.total,
                "mark": grade.mark,
                "grade": grade.grade
            })

    # Convert dictionary to list format
    report_data = list(student_reports.values())
    return jsonify(report_data)

@app.route('/send_all_report_cards', methods = ['POST', 'GET'])
@login_required
def send_all_report_cards():

    # Retrieve JSON data from the request
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    reportTitle = data.get('title')
    extraText = data.get('extraText')

    # Convert start and end dates to datetime objects
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    
    # Get the list of students with grades within the date range
    students_with_grades = (
        db.session.query(Students.id, Students.email, Students.firstName, Grades, Tests)
        .join(Grades, Students.id == Grades.studentID)
        .join(Tests, Grades.testID == Tests.testID)
        .filter(Tests.date >= start_date, Tests.date <= end_date)
        .order_by(Grades.studentID, Tests.date)
        .all()
    )

    # Group grades by student
    student_grades_map = {}
    for student_id, email, name, grade, test in students_with_grades:
        if student_id not in student_grades_map:
            student_grades_map[student_id] = {
                "email": email,
                "name": name,
                "grades": []
            }
        if grade.mark != -1: 
            student_grades_map[student_id]["grades"].append({
                "name": test.name,
                "date": test.date,
                "total": test.total,
                "mark": grade.mark,
                "grade": grade.grade
            })


    # Initialize the email sender
    # Send report card to each student
    for student_id, student_data in student_grades_map.items():
        student_email = student_data["email"]
        student_name = student_data["name"]
        grades = student_data["grades"]

        # Generate the HTML content for the email
        email_content = gen_html_grades_report(student_name, grades)

        if len(grades) > 0:
            # Send the email
            e1  = EmailSender()
            e1.send(
                email=[getStudentEmail(student_id), getStudentParentEmail(student_id)],
                # email = 'asafwaan03@gmail.com',
                subject=reportTitle,
                message = render_template("email_template.html", bigTitle = reportTitle, littleTitle = f"{getStudent(student_id)}", mainMessage = email_content)
            )



    return jsonify({"message": "Report cards sent successfully!"}), 200

@app.route('/toggle_event_bookable/<int:event_id>', methods=['POST'])
@login_required
def toggle_event_bookable(event_id):
    """Toggle the bookable status of an event."""
    event = BookableEvent.query.get_or_404(event_id)
    event.bookable = not event.bookable
    db.session.commit()
    return jsonify({"success": True, "bookable": event.bookable})

@app.route('/set_auto_print', methods=['POST'])
@login_required
def set_auto_print():
    data = request.get_json()
    file_id = data.get('fileID')
    auto_print = data.get('auto_print')

    if file_id is None or auto_print is None:
        return jsonify({"success": False, "message": "Missing fileID or auto_print value"}), 400

    file = Files.query.filter_by(fileID=file_id).first()
    if not file:
        return jsonify({"success": False, "message": "File not found"}), 404

    # Update the auto_print value
    file.auto_print = auto_print
    db.session.commit()

    return jsonify({"success": True, "message": "Auto print updated successfully"})

@app.route("/print_set_files/<mode>", methods = ['POST', 'GET'])
@login_required
def print_set_files(mode):
    role_required("admin", "mass print files")
    
    if mode == "weekend":
        lessons = get_weekend_lessons()
        # lessons = Lesson.query.filter_by(lessonID = 486).all()
        report = mass_print(lessons, eco_mode=True)
        
        print_files_at_printer([report], two_up = True, auto=True)
        
        
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just printed all the weekend files",   date=datetime.utcnow()))
        db.session.commit()
    
        
    
    return ""

@app.route('/update_preference', methods=['POST'])
@login_required
def update_preference():
    data = request.get_json()
    key = data.get('key')
    value = data.get('value')

    if not key or not value:
        return jsonify({'error': 'Invalid input'}), 400

    try:
        # Update the user attribute in the database
        stmt = update(User).values({key : value}).where(User.id == current_user.id)
        db.session.execute(stmt)
        db.session.commit()

        return jsonify({'message': 'Preference updated successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error updating preference: {e}")
        return jsonify({'error': 'Failed to update preference'}), 500

@app.route('/get_user_theme', methods = ['POST', 'GET'])
@login_required
def get_user_theme():
    user = User.query.filter_by(id = current_user.id).first()

    if user:
        return user.theme
    else:
        return "default"

@app.route("/get_search_results", methods = ['POST', 'GET'])
@login_required
def get_search_results():
    result = []
    students = Students.query.all()

    for student in students: 
        result.append({"keywords" : ['student', student.firstName, student.secondName, student.email, student.parent_email], 'link' : f'/admin_student_info?studentid={student.id}', 'type' : 'student', "display" : getStudent(student.id)})

    staffList = Staff.query.all()

    for staff in staffList:
        result.append({"keywords" : ['staff', staff.firstName, staff.secondName, staff.email, staff.role], 'link' : f'/staff_info?staffID={getUserID(staff.role, staff.id)}', 'type' : 'staff', 'display' : getStaff(staff.id)})

    lessons = Lesson.query.all()

    for lesson in lessons:
        result.append({"keywords" : ['lesson', lesson.day, getStaff(getLessonTutor(lesson.lessonID)), getSubjectName(lesson.subjectID), getCentre(lesson.centreID)], 'link' : f'/Classroom_View_Home?lessonid={lesson.lessonID}&year={lesson.AcademicYear}&weekNo={str(gen_week_no(0))}', 'type' : 'lesson', 'display' : getLessonString(lesson.lessonID)})

    return result

@app.route("/update_ucas_reference", methods = ['POST', 'GET'])
@login_required
def update_ucas_reference(): 
    role_required("admin", "updating ucas reference")
    data = request.get_json()
    
    id = data['referenceID']
    extra_info = data['extra_info']
    completed_reference = data['completed_reference']
    
    stmt = update(UCASReference).values({'extra_info' : extra_info, 'completed_reference' : completed_reference}).where(UCASReference.id == id)
    db.session.execute(stmt)
    db.session.commit()
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + f"):  has just updated the UCAS reference for {getUCASName(id)}",   date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@app.route("/delete_ucas_reference/<id>", methods = ['POST', 'GET'])
@login_required
def delete_ucas_reference(id):
    role_required("admin", "deleting ucas reference")
    stmt = delete(UCASReference).where(UCASReference.id == id)
    name = getUCASName(id)
    db.session.execute(stmt)
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + f"):  has just deleted the UCAS reference for {name}",   date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@app.route("/print_files_at_centre", methods=['POST', 'GET'])
@login_required
def print_files_at_cov_road():
    data = request.get_json()
    
    filepath = data['filepath']
    copies = int(data['copies'])
    two_up = data['two_up']
    centre = data['centre']

    if copies is None: 
        copies = 1

    if two_up is None: 
        two_up=True

    if centre is None:
        centre = "COV"
    
    try: 
        print_files_at_printer([filepath], copies = copies, two_up=two_up, BW=True, centre=centre, auto=False, tutor_name=getStaffFirstName(getOtherIDWithoutRole(current_user.id)))
        return jsonify({"success": True, "message": "Print job submitted successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/register_event', methods=['POST'])
def register_event():
    data = request.form
    
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    dietary_reqs = data.get('dietary_reqs')
    selected_events = request.form.getlist('events')  # Gets a list of selected events
    
    if not name or not email or not phone or not dietary_reqs or not selected_events:
        flash("All fields are required.", "danger")
        return redirect(url_for('easter_revision_booking'))  
    
    # Store selected events as a comma-separated string
    events_str = ", ".join(selected_events)
    
    # Save to database
    new_registration = EventRegistration(
        name=name, 
        email=email, 
        phone=phone, 
        dietary_reqs=dietary_reqs, 
        events=events_str
    )
    db.session.add(new_registration)
    db.session.commit()
    
    flash("Successfully registered!", "success")
    return redirect(url_for('easter_revision_booking'))



'''   _____  _____ _    _ ______ _____  _    _ _      _____ _   _  _____  '''
'''  / ____|/ ____| |  | |  ____|  __ \| |  | | |    |_   _| \ | |/ ____| '''
''' | (___ | |    | |__| | |__  | |  | | |  | | |      | | |  \| | |  __  '''
'''  \___ \| |    |  __  |  __| | |  | | |  | | |      | | | . ` | | |_ | '''
'''  ____) | |____| |  | | |____| |__| | |__| | |____ _| |_| |\  | |__| | '''
''' |_____/ \_____|_|  |_|______|_____/ \____/|______|_____|_| \_|\_____| '''

# cron examples
@scheduler.task('cron', id='do_job_3', week='*', day_of_week='*', hour = "19", minute = "0")
def job3():
    with app.app_context():
        lesson_map = getLessonsTomorrow()
        
        for tutorID, lessons in lesson_map.items(): 
            
            e1 = EmailSender()
            e1.send(getTutorEmail(tutorID), "Schedule Tomorrow", message = render_template("email_template.html", bigTitle = "Schedule for Tomorrow", littleTitle = f"Hi {getStaff(tutorID)}", mainMessage = gen_html_tomorrow_timetable(getStaff(tutorID), lessons)))
            # e1.send("asafwaan03@gmail.com", "Schedule Tomorrow - TEST", gen_html_tomorrow_timetable(getStaff(tutorID), lessons))
            
        

@scheduler.task('cron', id='breakout_rooms', week='*', day_of_week='*', hour = '16', minute = '45')
def breakout_rooms(): 
    e1 = EmailSender()
    
    e1.send("ateam1772@gmail.com", "Start Zoom Meeting", "this is a test to trigger the zoom meeting")
    return redirect('/allTimetable?offset=0')

# cron examples
# @scheduler.task('cron', id='remind_about_booking', week='*', day_of_week='*', hour = "19", minute = "0")
# def booking_reminder():
#     with app.app_context():
#         lesson_map = getBookingTomorrow()
#         print(lesson_map)
        
#         for tutorID, lessons in lesson_map.items(): 
            
#             e1 = EmailSender()
#             e1.send(getTutorEmail(tutorID), "Schedule Tomorrow", message = render_template("email_template.html", bigTitle = "Schedule for Tomorrow", littleTitle = f"Hi {getStaff(tutorID)}", mainMessage = gen_html_tomorrow_timetable(getStaff(tutorID), lessons)))
#             # e1.send("asafwaan03@gmail.com", "Schedule Tomorrow - TEST", gen_html_tomorrow_timetable(getStaff(tutorID), lessons))
            
#         print("should have sent email")
   
@scheduler.task('cron', id='print_files', week='*', day_of_week='mon-fri', hour = '*', minute = '45')
def print_files(): 
    with app.app_context():
        lessons = get_lessons_starting_soon()
        
        for lesson in lessons:
            reg, unreg, temp = getAttendance(lesson.lessonID, gen_week_no(-7))
            copies = len(reg) + len(unreg) + len(temp)
            copies = (copies // 2) + 1 
            
            files = Files.query.filter(
                or_(
                    Files.subjectID == lesson.subjectID,
                    Files.lessonID == lesson.lessonID
                ),
                Files.weekNo == int(gen_week_no(0)),
                Files.auto_print == True
            ).all()
            
            subject_folder = getFileFolder(lesson.subjectID)  # Function to get subject folder
            files = [combine_two_pages_per_sheet(f"var/www/webApp/webApp/files/{subject_folder}/{file.filename}", f"var/www/webApp/webApp/files/{subject_folder}/{file.filename[:-4]}-2up.pdf", watermark=True, tutor_name=getStaff(getLessonTutor(lesson.lessonID))) for file in files if classTypeCheck(lesson, file.classtype)]
            
            for file in files: 
                e1 = EmailSender()
                e1.send(email = "ateam1772@gmail.com", subject = f"Printing {getStaff(lesson.tutorID)}s files", message = f"COPIES={int(copies)}\nB/W PRINT=ON\nDUPLEX=LEFT", files=[file],  subtype='plain')
        
    return redirect('/allTimetable?offset=0')



'''    ____  _   _ ______            _______ _____ __  __ ______  '''
'''   / __ \| \ | |  ____|          |__   __|_   _|  \/  |  ____| '''
'''  | |  | |  \| | |__     ______     | |    | | | \  / | |__    '''
'''  | |  | | . ` |  __|   |______|    | |    | | | |\/| |  __|   '''
'''  | |__| | |\  | |____              | |   _| |_| |  | | |____  '''
'''   \____/|_| \_|______|             |_|  |_____|_|  |_|______| '''
                                                             

@app.route("/oneTime", methods=['POST', 'GET'])
@login_required
def oneTime():
    check_maintenance()
    role_required("admin", "ACTION: tried to trigger onetime")

    with app.app_context():
        db.create_all()

    # extract_classes_from_html('/var/www/webApp/webApp/templates', '/var/www/webApp/webApp/output.txt')
    
    # e1 = EmailSender()
    # e1.send("asafwaan03@gmail.com", "TEST NO REPLY", "this is a test email")
        
    # print(is_valid_email('jtreanor@gmail.co.uk'))
    
    # num = 4
    # for i in range(1, 13, 1):
    #     db.session.add(gameQuestions(question=f'{num} X {i}', correctAnswer = str(num * i), answer2 = str(num * random.randint(3, 9)), answer3 = str(num * random.randint(3, 11)), answer4 = str(num * random.randint(1, 9))))
        
    # db.session.commit()
    
    # subjects = lessonPlan.query.filter_by(weekNo = 9)
    
    # for subject in subjects:
    #     if subject.weekNo == 9:
    #         stmt = update(lessonPlan).values({"topic" : subject.topic}).where(and_(lessonPlan.subjectID == subject.subjectID, lessonPlan.weekNo == 10))
    #         db.session.execute(stmt)
    

    # e1 = EmailSender()
    
    # files = [combine_two_pages_per_sheet('/var/www/webApp/webApp/files/YEAR-11-MATHS/SME_Functions_Hard.pdf', '/var/www/webApp/webApp/files/YEAR-11-MATHS/SME_Functions_Hard-2up.pdf', watermark=True, tutor_name="Nagina")]
    
    # e1.send("ateam1772@gmail.com", "print test", message = f"COPIES=1\nB/W PRINT=ON\nDUPLEX=LEFT", files=files)
    # for lesson in lessons: 
    #     files = get_files_to_print(lesson.lessonID, gen_week_no(0))
        
    #     reg, unreg, temp = getAttendance(lesson.lessonID, gen_week_no(-7))
    #     copies = len(reg) + len(unreg) + len(temp)

    #     for file in files:
    #         subjectName = getSubjectName(lesson.subjectID)
    #         tutorName = getStaff(lesson.tutorID)
    #         startTime = str(lesson.startTime)
    #         filename = file.replace("var/www/webApp/webApp/files/", "")
    

    # db.session.add(StaffStrikes(staffID = 50, date = "2024-12-7", description="Sahro came in 35 minutes late to her lessons on Saturday stating the reason was that she overslept. We expect better from the tutors to set a good example for the students and their punctuality."))
    # db.session.commit()

    # tests = Tests.query.all()

    # grades = []
    # for test in tests:
    #     gradeList = Grades.query.filter_by(testID = test.testID).all()
    #     for grade in gradeList: 
    #         grades.append((((grade.mark / test.total) * 100) // 10 ) * 10 )

    
    # lesson = Lesson.query.filter_by(lessonID=665).first()
    # files = Files.query.filter(
    # or_(
    #     Files.subjectID == lesson.subjectID,
    #     Files.lessonID == lesson.lessonID
    # ),
    # Files.weekNo == int(gen_week_no(0)),
    # Files.auto_print == True
    # ).all()
    
    # for file in files:
    #     print(file.filename)
    
    note = f''' making easter revision table '''
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  One-time was just triggered with the following note: " + note,   date=datetime.utcnow()))

    db.session.commit()   

    return redirect('/allTimetable?offset=0')

@app.route('/oneTimeView')
@login_required
def oneTimeView():
    check_maintenance()
    role_required("admin", "One Time View")
    try:
        page = request.args['page']
    except:
        page = -1
    
    
    if(page == "1"):
        return render_template('landing1.html')
    if(page == "2"):
        return render_template('landing2.html')
    if(page == "3"):
        return render_template('landing3.HTML')     
    if(page == "4"):
        return render_template('landing4.html')
    if(page == "5"):
        data = []

        tutorList = getAllUsers("tutor", log_on=True)
        
        for tutor in tutorList:
            data.append({'name' : tutor.firstName, "amount" : 0, 'email' : tutor.email})
            
        adminList = getAllUsers("admin", True)
        
        # for admin in adminList:
        #     data.append({'name' : admin.username + " (admin) ", "amount" : 0, 'email' : admin.associatedEmail})
        
        logList = log.query.all()
        
        for logItem in logList:
            for item in data: 
                if item['email'] in logItem.message or item['name'] in logItem.message:
                    item['amount'] += 1
            
            
        return render_template("dashboard.html", data = sorted(data, key=lambda x:x['amount']))       
    if(page == "6"):
        return render_template('tutor_dashboard.html')
    # pages 7 and 8 removed: they rendered templates that do not exist
    # (exam_timetable_generator.html, admin_dashboard-original.html) and
    # always returned a 500.
    if(page == "9"):
        subjects = Subject.query.all()
        result = {}

        for subject in subjects:
            grades_list = []

            lessons = Lesson.query.filter_by(subjectID=subject.subjectID).all()
            for lesson in lessons:
                tests = db.session.query(Tests).filter(
                    Tests.date >= "2024-12-01",
                    Tests.lessonID == lesson.lessonID
                ).all()

                for test in tests:
                    grades = getAllGrades(test.testID)
                    for grade in grades:
                        if test.total > 0:
                            percentage = (grade.mark / test.total) * 100
                            grades_list.append(percentage)

            if grades_list:
                result[subject.subjectID] = {
                    "name": getSubjectName(subject.subjectID),
                    "data": grades_list,
                    "mean": round(np.mean(grades_list), 2),
                    "median": round(np.median(grades_list), 2),
                    "iqr": {
                        "min": round(min(grades_list), 2),
                        "q1": round(np.percentile(grades_list, 25), 2),
                        "median": round(np.median(grades_list), 2),
                        "q3": round(np.percentile(grades_list, 75), 2),
                        "max": round(max(grades_list), 2)
                    }
                }
                
                
        result2 = {}
        tutors_colors = {}

        for subject in subjects:
            grades_by_tutor = {}

            lessons = Lesson.query.filter_by(subjectID=subject.subjectID).all()
            for lesson in lessons:
                tests = db.session.query(Tests).filter(
                    Tests.date >= "2024-12-01",
                    Tests.lessonID == lesson.lessonID
                ).all()

                for test in tests:
                    grades = getAllGrades(test.testID)
                    for grade in grades:
                        if test.total > 0:
                            percentage = (grade.mark / test.total) * 100
                            tutor_id = lesson.tutorID
                            if tutor_id not in grades_by_tutor:
                                grades_by_tutor[tutor_id] = []
                            grades_by_tutor[tutor_id].append(percentage)

            # Process each tutor's grades
            if grades_by_tutor:
                result2[subject.subjectID] = {
                    "name": getSubjectName(subject.subjectID),
                    "data": grades_by_tutor,
                    "mean": round(np.mean([g for grades in grades_by_tutor.values() for g in grades]), 2),
                    "median": round(np.median([g for grades in grades_by_tutor.values() for g in grades]), 2),
                    "iqr": {
                        "min": round(min([g for grades in grades_by_tutor.values() for g in grades]), 2),
                        "q1": round(np.percentile([g for grades in grades_by_tutor.values() for g in grades], 25), 2),
                        "median": round(np.median([g for grades in grades_by_tutor.values() for g in grades]), 2),
                        "q3": round(np.percentile([g for grades in grades_by_tutor.values() for g in grades], 75), 2),
                        "max": round(max([g for grades in grades_by_tutor.values() for g in grades]), 2)
                    }
                }

                # Assign a unique color to each tutor
                unique_tutors = list(grades_by_tutor.keys())
                tutor_colors = cm.get_cmap('tab10', len(unique_tutors))  # Use a colormap for colors
                tutors_colors = {
                    tutor: f'rgba({int(color[0]*255)}, {int(color[1]*255)}, {int(color[2]*255)}, 0.6)'
                    for tutor, color in zip(unique_tutors, tutor_colors.colors)
                }
                
                
        return render_template('scatter_percentage_chat.html', result=result, result2=result2, tutors_colors=tutors_colors)
    
    if(page == "10"):
        result = (
        db.session.query(
            Lesson.tutorID,
            func.avg(Grades.mark / Tests.total * 100).label('averagePercentageScore')
        )
        .join(Tests, Lesson.lessonID == Tests.lessonID)
        .join(Grades, Tests.testID == Grades.testID)
        .filter(Grades.mark > 0)  # Filter out marks above 0
        .filter(Tests.date >= "2024-09-20")
        .group_by(Lesson.tutorID)
        .all()
        )   


        tutorsPerformance = [[getStaff(tutor_id), result] for tutor_id, result in result]
        tutorsPerformance = sorted(tutorsPerformance, key=lambda x:x[1])
        
        tutorPoints = {
            name: index
            for index, (name, _) in enumerate(tutorsPerformance)
        }      
                  
        tutors = User.query.filter_by(role="tutor").filter_by(log_on=True).all()
        
        userPoints = [[getStaff(tutor.otherID), tutor.points] for tutor in tutors if tutor.points > 0 and "No Name" not in getStaff(tutor.otherID)]
            
        userPoints = sorted(userPoints, key= lambda x:x[1])
        
        for index, user in enumerate(userPoints): 
            # Ensure the key exists in tutorPoints
            if user[0] not in tutorPoints:
                tutorPoints[user[0]] = 0
            
            # Add the index to the tutorPoints value
            tutorPoints[user[0]] += index


    if(page == "11"):
        word_list = [
            "apple", "brave", "crane", "daisy", "eagle", "flame", "globe", "heart", "ivory", "jolly",
            "knife", "lemon", "mango", "noble", "ocean", "piano", "queen", "raven", "sunny", "table",
            "unite", "vivid", "waste", "xerox", "yacht", "zebra", "amber", "beach", "charm", "dream",
            "elite", "fancy", "grape", "happy", "inbox", "jumps", "koala", "lucky", "mirth", "novel",
            "orbit", "pearl", "quilt", "rider", "storm", "tiger", "udder", "vigor", "whale", "xenon",
            "youth", "zesty", "adapt", "blink", "craft", "delve", "ember", "frost", "grasp", "haste",
            "ideal", "joint", "karma", "lofty", "mirth", "nudge", "overt", "pilot", "quake", "ranch",
            "stark", "trick", "urban", "vowel", "woven", "xeric", "yield", "zonal", "align", "boost",
            "cliff", "dwell", "evoke", "froze", "gloom", "haste", "inlet", "jolly", "knack", "lapse",
            "moist", "nymph", "opine", "pound", "quark", "realm", "skirt", "truly", "upper", "vouch",
            "wrist", "xerox", "yummy", "zebra", "abide", "brace", "chose", "douse", "ethic", "fiery",
            "glint", "hatch", "infer", "joker", "kneel", "light", "magma", "notch", "offer", "plush",
            "quirk", "roast", "scope", "twist", "undue", "visit", "witty", "xeric", "youth", "zones",
            "axiom", "brush", "cease", "doubt", "eager", "fable", "gains", "hover", "image", "juice",
            "knead", "latch", "march", "nerve", "ounce", "place", "quirk", "rebel", "scent", "torus",
            "unify", "valid", "wound", "xerus", "yodel", "zebra", "adept", "bluff", "curve", "dizzy",
            "evict", "frame", "gusto", "hinge", "issue", "jolly", "kudos", "lunar", "mirth", "novel",
            "overt", "pence", "quill", "racer", "sheen", "trunk", "upset", "vivid", "whisk", "xerox",
            "yield", "zesty", "amble", "bloom", "chill", "drift", "exile", "flock", "giant", "haste",
            "inner", "jumbo", "knock", "lapse", "mocha", "nexus", "optic", "prone", "quest", "risky",
            "stark", "truce", "usher", "vexed", "wager", "xenon", "yacht", "zebra"
        ]
                
        
        find_words_with_few_unique_letters(word_list)


        letter_pairs = generate_letter_pairs(10)
            
        return synonym_generator(5)
        # return letter_sequence_generator()
                    
        # return render_template("oneTimeView.html", tutor_rankings = sorted(tutorPoints.items(), key=lambda x: x[1], reverse=True), grades = grades)
    

    
    
