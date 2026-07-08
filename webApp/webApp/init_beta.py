from flask import Flask, render_template, redirect, request, flash, send_from_directory, url_for, send_file, session, abort, jsonify, Response, Blueprint
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate
from flask_cors import CORS
from sqlalchemy import select, insert, update, delete, and_, or_, distinct, case
from sqlalchemy.orm import aliased
from sqlalchemy.exc import SQLAlchemyError
from Schema import *
from functions import *
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
# from . import check_maintenance, role_required, permission_required
import json
import csv
import numpy as np
import smtplib
import time
import babel.numbers
import decimal
import itertools
import random
import subprocess
import base64
import os

# from config import MEDIA_FOLDER

 
beta = Blueprint('beta', __name__, static_folder='www/webApp/webApp/static')

# initialize scheduler
scheduler = APScheduler()

def check_maintenance(maintenance=False):
    # if maintenance and current_user.id != 142 and current_user.id != 2 and current_user.id != 468:            
    if maintenance and not permission_required(current_user.id, 'allow_maintenance') and current_user.id != 142:
        abort(503, "")

def role_required(requiredRole, message):          
    if isAllowed(current_user.role, requiredRole):
        return True
    else: 
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): tried to access " + message + " but was denied", date=datetime.utcnow()))
        db.session.commit()
        abort(403, "")

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


@beta.errorhandler(403)
def error403(error):
    return render_template('403.html'), 403

@beta.errorhandler(404)
def error404(error):
    return render_template('404.html'), 404

@beta.errorhandler(503)
def error503(error):
    return render_template('maintenance.html'), 503

@beta.errorhandler(400)
def error400(error):
    return render_template("400.html"), 400

# @beta.errorhandler(300)
# def error400(error):
#     #filename error
#     return render_template("300.html"), 400


MEDIA_FOLDER = 'var/www/webApp/webApp/'
@beta.route('/beta/CS310/images/<filename>')
def download_file(filename):
    return send_from_directory(MEDIA_FOLDER, filename, as_attachment=True)


# @beta.before_request
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


@beta.route('/beta/', methods=['POST', 'GET'])
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

            if check_password_hash(generate_password_hash('password'), password):
                session.pop('_flashes', None)
                return redirect(url_for('change_password'))
            
            if current_user.is_admin(): 
                return redirect(url_for('admin_dashboard'))
            if current_user.is_tutor(): 
                return redirect(url_for('tutor_dashboard'))
            if current_user.is_student():
                return redirect(url_for('student_dashboard'))
            if current_user.is_parent():
                return redirect(url_for('student_dashboard'))
            if current_user.is_receptionist() or current_user.is_exams_officer():
                return redirect(url_for('receptionist_dashboard'))
            else:
                return redirect(url_for('allTimetable', offset=0))

        return redirect(url_for('begin'))
    
    return render_template('login.html')

@beta.route('/beta/admin_dashboard', methods = ['POST', 'GET'])
@login_required
def admin_dashboard(): 
    check_maintenance()
    #role_required("admin", "admin dashboard")
    
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
    lessonCompletionPercentage = round((completedLessons / allLessons) * 100)
    
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

@beta.route('/beta/tutor_dashboard', methods = ['POST', 'GET'])
@login_required
def tutor_dashboard():
    check_maintenance()
    # #role_required("tutor", "Tutor Home")

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
    lessonCompletionPercentage = round((completedLessons / allLessons) * 100) if allLessons != 0 else 0
    
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
            func.avg(Grades.mark / Tests.total * 100).label('averagePercentageScore')
        )
        .join(Tests, Lesson.lessonID == Tests.lessonID)
        .join(Grades, Tests.testID == Grades.testID)
        .filter(Grades.mark > 0)  # Filter out marks above 0
        .filter(Tests.name.like("%February%"))
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

    return render_template("tutor_dashboard.html", lessonCompletionPercentage=lessonCompletionPercentage, percentageAttendance=percentageAttendance, ranking=ranking, totalTutors = totalTutors, total_hours = total_hours, year_group_counts = year_group_counts,year_group_categories = year_group_categories, colours = colours, site_usage_hour_slots = site_usage_hour_slots, tutor_totals = tutor_totals)

@beta.route('/beta/student_dashboard', methods=['POST', 'GET'])
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

@beta.route('/beta/receptionist_dashboard', methods = ['POST', 'GET'])
@login_required
def receptionist_dashboard():

    centreIDList = UserCentre.query.filter_by(userID = current_user.id).all()
    centreIDs = [user.centreID for user in centreIDList ]

    #lesson completion percentage
    allLessons = len(Lesson.query.filter(or_(Lesson.weekNo == gen_week_no(0), Lesson.weekNo == -1)).filter(Lesson.centreID in centreIDs).all())
    completedLessons = len(LessonInfo.query.filter_by(weekNo = gen_week_no(0)).all())

    if allLessons == 0 or completedLessons == 0:
        lessonCompletionPercentage = 0
    else:
        lessonCompletionPercentage = round((completedLessons / allLessons) * 100)    

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

@beta.route("/beta/parent_dashboard")
def parent_dashboard():
    parent_email = current_user.email

    # Get students associated with the parent email
    students = Students.query.filter_by(parent_email=parent_email).all()

    student_data = []
    current_week_no = gen_week_no(0)  # Function to get current week number

    for student in students:
        # Get grades for the student
        grades = Grades.query.filter_by(studentID=student.id).all()

        # Get the next lesson for the student
        next_lesson = (
            db.session.query(Lesson)
            .join(StudentLesson, StudentLesson.lessonID == Lesson.lessonID)
            .filter(
                StudentLesson.studentID == student.id,
                Lesson.active == True,
                Lesson.weekNo >= current_week_no  # Adjust week filtering as needed
            )
            .order_by(Lesson.startTime)
            .first()
        )

        # Collect student info, grades, and the next lesson data
        student_data.append({
            "student": student,
            "grades": grades,
            "next_lesson": next_lesson
        })

    return render_template('parent_dashboard.html', student_data=student_data)

@beta.route("/beta/tutor_performance")
@login_required
def tutor_performance():
    check_maintenance()
    #role_required("admin", "Tutor Performance")
    #Tutor Lesson Count
    results = (
        db.session.query(Lesson.tutorID, func.count().label('lessonCount'))
        .filter(Lesson.active == True, Lesson.weekNo == -1)
        .group_by(Lesson.tutorID)
        # .order_by(func.count().desc())
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
        .filter(Tests.name.like("%February%"))
        .group_by(Lesson.tutorID)
        .all()
    )


    tutorsPerformance = [getTutor(tutor_id) for tutor_id, _ in result]
    average_scores = [round(average_score) for _, average_score in result]
    
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

@beta.route("/beta/tutorAccessRights", methods = ['POST', 'GET'])
@login_required
def tutorAccessRights():
    check_maintenance()
    tutorList = getAll("tutor")
        
    # print(tutors)
    return render_template("tutor_access_rights.html", tutors = sorted(sorted(tutorList, key=lambda x:x['name']), key=lambda x:x['log_on'], reverse=True), role=False, student = False)

@beta.route("/beta/roleAccessRights", methods = ['POST', 'GET'])
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

@beta.route("/beta/studentAccessRights", methods = ['POST', 'GET'])
@login_required
def studentAccessRights():
    check_maintenance()
    studentList = getAll("student")
    
    # print(tutors)
    return render_template("tutor_access_rights.html", tutors = sorted(sorted(studentList, key=lambda x:x['name']), key=lambda x:x['log_on'], reverse=True), student = True)

@beta.route("/beta/staffAccessRights", methods = ['POST', 'GET'])
@login_required
def staffAccessRights():
    check_maintenance()
    tutorList = getAll("staff")
        
    # print(tutors)
    return render_template("tutor_access_rights.html", tutors = sorted(sorted(tutorList, key=lambda x:x['name']), key=lambda x:x['log_on'], reverse=True), role=False, student = False)

@beta.route("/beta/tutorHours", methods = ['POST', 'GET'])
@login_required
def tutorHours():
    check_maintenance()
    tutorList = getAllUsers("tutor", log_on= True)
    day = date.today()
    
    tutors = [[getTutor(tutor.id), getTutorHours(tutor.id, gen_week_no(-21)), getTutorHours(tutor.id, gen_week_no(-14)), getTutorHours(tutor.id, gen_week_no(-7)), getTutorHours(tutor.id, gen_week_no(0)), getTutorAccess(tutor.id, "log_on")] for tutor in tutorList]
    weeks = [gen_week_no(-21), gen_week_no(-14), gen_week_no(-7), gen_week_no(0)]
    
    tutors2 = [[getTutor(tutor.id), getTutorMonthHours(tutor.id, int(day.month)-2), getTutorMonthHours(tutor.id, int(day.month)-1), getTutorMonthHours(tutor.id, int(day.month)), getTutorAccess(tutor.id, "log_on")] for tutor in tutorList]
    months = [num_to_month(int(day.month) - 2), num_to_month(int(day.month) - 1), num_to_month(int(day.month))]
    
    return render_template("tutor_hours.html", tutors = sorted(sorted(tutors, key=lambda x:x[0]), key=lambda x:x[5], reverse=True), weeks = weeks, tutors2 = sorted(sorted(tutors2, key=lambda x:x[0]), key=lambda x:x[4], reverse=True), months = months)

@beta.route("/beta/student_performance")
@login_required
def student_performance():
    check_maintenance()
    #role_required("admin", "Student Performance")

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

@beta.route('/beta/allTimetable')
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

                if (lesson.weekNo == -1 and lesson.created_week <= int(gen_week_no(int(offset)))) or str(lesson.weekNo) == str(weekNo):
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
                elif current_user.is_admin(): 
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
    
    elif current_user.is_student() or (studentID != -1 and permission_required(current_user.id, 'view_all_lessons')): 
        
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
                if lessonEntry.active == True:
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

@beta.route('/beta/allTimetableForApp')
def allTimetableForApp():
    check_maintenance()
    # db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): showing beta timetable", date=datetime.utcnow()))
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

@beta.route('/beta/generate_Timetable')
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

@beta.route('/beta/Classroom_View_Home', methods= ['POST', 'GET'])
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
    
    subjectID = Lesson.query.filter_by(lessonID=lessonID).first().subjectID
    topic = lessonPlan.query.filter_by(subjectID=subjectID, weekNo=weekNo).first().topic
    
    lessonInfo = Lesson.query.filter_by(lessonID = lessonID).first()
    startTime = lessonInfo.startTime
    endTime = lessonInfo.endTime
    centre = Centre.query.filter_by(centreID = lessonInfo.centreID).first().name
    subject = Subject.query.filter_by(subjectID = subjectID).first()
    tutor = Staff.query.filter_by(id=lessonInfo.tutorID).first()
    days = ['MON', 'TUES', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    
    info = {"startTime" : startTime, "endTime" : endTime, "centre" : centre, "centreid": lessonInfo.centreID, "subject" : subject.tier + " " + subject.title, "tutor" : tutor.firstName + " " + tutor.secondName, "tutorID" : tutor.id, "weekNo" : lessonInfo.weekNo, "day" : lessonInfo.day}
    
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
                           subjects = subjects, 
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

@beta.route('/beta/Classroom_View_Register', methods = ['POST', 'GET'])
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

@beta.route('/beta/Classroom_View_Files', methods = ['POST', 'GET'])
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
                starterList.append([file.filename, file.associatedTopic])
            
            if file.type == "main":
                mainList.append([file.filename, file.associatedTopic])

            if file.type == "homework":
                homeworkList.append([file.filename, file.associatedTopic])

            if file.type == "notes":
                notesList.append([file.filename, file.associatedTopic])
    


    #Get all the files at the lesson level
    uniqueFiles = Files.query.filter_by(lessonID = lessonid).filter_by(weekNo=weekNo).all()
    
    for file in uniqueFiles:
        if current_user.is_student() and file.studentview == False:
            continue
        
        if file.type == "starter":
            starterList.append([file.filename, file.associatedTopic, 'unique'])
        
        if file.type == "main":
            mainList.append([file.filename, file.associatedTopic, 'unique'])

        if file.type == "homework":
            homeworkList.append([file.filename, file.associatedTopic, 'unique'])

        if file.type == "notes":
            notesList.append([file.filename, file.associatedTopic, 'unique'])

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

@beta.route('/beta/Classroom_View_Forum', methods=['POST', 'GET'])
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

@beta.route('/beta/Classroom_View_Subject_Resources')
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

@beta.route('/beta/temp_student_reg', methods=['POST', 'GET'])
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

@beta.route('/beta/view_lessons')
@login_required
def view_lessons():
    check_maintenance()
    # #role_required("tutor", "View Lessons")
    
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


#This is a really bad function please fix it at some point
#worse than I though definitely fix
#repair the really long list and make it a dict 
#also implement the fileNumber stuff
@beta.route('/beta/lesson_plan', methods = ['POST', 'GET'])
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

@beta.route('/beta/tutor_overview', methods=['POST', 'GET'])
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

@beta.route('/beta/admin_overview', methods=['POST', 'GET'])
@login_required
def admin_overview():
    check_maintenance()
    #role_required("admin", "Admin Overview")
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

@beta.route("/beta/student_reg")
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

@beta.route("/beta/admin_tutor_view", methods=['POST', 'GET'])
@login_required
def admin_view_tutors():
    check_maintenance()
    #role_required("admin", "Admin Tutor View")
    tutorList = getAllUsers("tutor")
    tutors = []
    for tutor in tutorList:           
        tutors.append({"id" : getUserID("tutor", tutor.id), "firstName" : tutor.firstName, "secondName" : tutor.secondName, "gender" : tutor.gender, "email" : tutor.email, "phone" : tutor.phone, "logOn" : getUserPermission(id = tutor.id, action = "log_on", role = "tutor")})
    
    return render_template("admin_tutor_view.html", tutors= sorted(sorted(tutors, key = lambda x : x['firstName']), key=lambda x: x['logOn'], reverse = True))
    # return render_template("admin_tutor_view.html", tutors= tutors)


#id provided in the URL is the userID
@beta.route("/beta/admin_tutor_info", methods=['POST', 'GET'])
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
@beta.route("/beta/tutor_info", methods = ['POST', 'GET'])
@login_required
def tutor_info():
    check_maintenance()
    #role_required("tutor", "Tutor Tutor Info")
        
    tutorid = getOtherID("tutor", current_user.id)
    
    return view_tutor_info(tutorid, True)

#id provided in the URL is the userID
@beta.route("/beta/staff_info")
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


@beta.route("/beta/tutor_reg", methods=['POST', 'GET'])
@login_required
def add_tutor():
    check_maintenance()
    #role_required("admin", "Tutor Registration")
    lessons = []
    
    lessonList = Subject.query.all()
    for item in lessonList:
        lessons.append({"id": str(item.subjectID), "name": item.tier + " " + item.title})
    
    return render_template("tutor_reg.html", lessons=lessons )

@beta.route("/beta/admin_student_view", methods=["POST", "GET"])
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

@beta.route("/beta/admin_student_info", methods=['POST', 'GET'])
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

@beta.route("/beta/student_profile", methods = ['POST', 'GET'])
@login_required
def student_profile():
    check_maintenance()
    #role_required("student", "Student profile")
    studentID = getOtherID("student", current_user.id)
    
    return student_info(studentID, True)

@beta.route("/beta/subjects", methods=['POST', 'GET'])
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

@beta.route("/beta/weekly_report", methods =['POST', 'GET'])
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

@beta.route('/beta/Classroom_View_Grades', methods=['POST', 'GET'])
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

@beta.route('/beta/change_password', methods = ['POST', 'GET'])
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

@beta.route('/beta/student_overview', methods = ['POST', 'GET'])
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
        lessons.append({ "lesson" : getLessonString(lesson.lessonID), "week" : lesson.weekNo })
        
    return render_template("student_overview.html", lessons = sorted(lessons, key = lambda x: x['week'], reverse=True), name = name)

@beta.route('/beta/unregisteredStudents', methods = ['POST', 'GET'])
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

@beta.route('/beta/unregisteredGrades', methods = ['POST', 'GET'])
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
        unregistered.append({"studentName" : student.studentName, "test" : getGrade(student.gradeID), "testID" : student.testID, "mark" : student.mark, "gradeID" : student.gradeID})
        
        
    return render_template('unregisteredGrades.html', unregistered = sorted(unregistered, key=lambda x:x['studentName']), registered = sorted(registered, key=lambda x:x['name']))

@beta.route('/beta/importantDocs', methods = ['POST', 'GET'])
@login_required
def importantDocs(): 
    check_maintenance()
    #role_required("tutor", "Important Documents")

    path = '/var/www/webApp/webApp/files/IMPORTANT_DOCS'
    documentList = [{"displayName" : f.replace("_", " "), "name" : f, "type" : getFileType(f)[1:]} for f in listdir(path) if isfile(join(path, f))]
    # print(documentList)
    
    return render_template("importantDocs.html", documentList = sorted(documentList, key=lambda x:x['name']))

@beta.route('/beta/maintenance')
@login_required
def maintenance():
    check_maintenance()
    return render_template('maintenance.html')

@beta.route('/beta/lesson_files')
@login_required
def lesson_files():
    check_maintenance()
    #role_required("tutor", "Lesson Files")
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
                
            files[file.subjectID].append({"filename" : file.filename, "weekNo" : file.weekNo, "classtype" : file.classtype, "id" : file.fileid, "studentView" : file.studentview, "hide_from_all" : file.hide_from_all, "filenameView" : file.filename.replace("_", " "), 'subjectName' : getFileFolder(file.subjectID)})
    
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

@beta.route('/beta/studentGrades', methods = ['POST', 'GET'])
@login_required
def studentGrades():
    check_maintenance()
    #role_required("student", "Student Grades")
    if(current_user.is_student()):
        studentID = getOtherID("student", current_user.id)
    elif(current_user.is_admin()):
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

@beta.route('/beta/fix_files', methods = ['POST', 'GET'])
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

@beta.route('/beta/release_notes')
@login_required
def release_notes(): 
    check_maintenance()
    return render_template("release_notes.html")

@beta.route('/beta/make_all_tests')
@login_required
def make_all_tests():
    check_maintenance()
    #role_required("admin", "make all tests")

    subjectList = Subject.query.all()

    subjects = [{"id" : subject.subjectID, "name" : subject.tier + " " + subject.title} for subject in subjectList]
    scopes = ["all", "week", "weekend"]

    return render_template("make_all_tests.html", subjects = sorted(subjects, key = lambda x : x['name']), scopes = scopes)

@beta.route('/beta/make_exams')
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

@beta.route('/beta/make_new_exam_student')
@login_required
def make_new_exam_student(): 
    check_maintenance()
    nonExamStudents = Students.query.filter_by(exam_student = False).all()
    
    return render_template("make_new_exam_student.html", nonExamStudents = nonExamStudents)

@beta.route('/beta/exam_students')
@login_required
def exam_students(): 
    check_maintenance()
    permission_required(current_user.id, "view_all_student_information", fatal=True)
    examStudents = get_exam_students()
    
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
        examStudents=examStudents,
        exams=sorted(sorted(sorted(sorted(exams_dict, key = lambda x :x['code']), key = lambda x :x['title']), key = lambda x :x['tier']), key = lambda x :x['examSeries']),
        ucasReferences=ucasReferences,
        student_exam_map=student_exam_map,
        user_files_map=user_files_map, 
        user_id_map = user_id_map

    )
    
@beta.route('/beta/admin_create_alerts')
@login_required
def admin_create_alerts():
    check_maintenance()
    create_alerts = permission_required(current_user.id, 'create_alerts', fatal=True)
    
    return render_template("admin_create_alerts.html")

@beta.route('/beta/alert_status')
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

@beta.route('/beta/admin_send_email')
@login_required
def admin_send_emails():
    check_maintenance()
    return render_template("admin_send_emails.html")

@beta.route('/beta/payslips')
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
    payslips = [{"type" : getFileType(f)[1:], "name" : f} for f in listdir(path) if isfile(join(path, f))]

    return render_template("payslips.html", payslips = payslips, id=userID, upload=upload)

@beta.route("/beta/send_report_cards")
@login_required
def send_report_cards():
    check_maintenance()
    return ""

@beta.route("/beta/automatic_maths_marker")
@login_required
def mathsMarker(): 
    check_maintenance()
    return render_template("maths_marker.html")

@beta.route("/beta/view_feedback")
@login_required
def view_feedback(): 
    check_maintenance()
    feedback_list = Feedback.query.all()
    feedback = [{"file" : response.filename.replace("/var/www/webApp/webApp/", ""), "student" : getStudent(response.studentID), "feedback" : response.feedback, "student_good" : response.student_good, "tutor_good" : response.tutor_good, "correct" : "Correct" if response.correct else "Incorrect" } for response in feedback_list]

    return render_template("view_feedback.html", feedback = sorted(feedback, key = lambda x:x['file'] ,reverse=True))

@beta.route("/beta/view_exams")
@login_required
def view_exams():
    check_maintenance()
    return render_template("view_exams.html")

@beta.route("/beta/centre_overview")
@login_required
def centre_overview():
    check_maintenance()
    #role_required("admin", "Centre Overview")
    
    centreList = Centre.query.all()
    centres = []
    for centre in centreList:
        centres.append({"admin" : getStaff(centre.admin_id), "name" : centre.name, "room_number" : centre.room_number, "address" : centre.address, "centreID" : centre.centreID})
        
    return render_template("centre_overview.html", centres = sorted(centres, key=lambda x:x['name']), staffs=getAll('staff'))

@beta.route("/beta/exam_room_allocation")
@login_required
def exam_room_allocation(): 
    check_maintenance()
    students = [
        {'student_id': '001', 'surname': 'Smith', 'exam_code': 'MATH101'},
        {'student_id': '002', 'surname': 'Johnson', 'exam_code': 'MATH101'},
        {'student_id': '003', 'surname': 'Williams', 'exam_code': 'PHYS101'},
        {'student_id': '004', 'surname': 'Brown', 'exam_code': 'PHYS101'},
        {'student_id': '002', 'surname': 'Johnson', 'exam_code': 'PHYS101'},
        {'student_id': '005', 'surname': 'Jones', 'exam_code': 'CHEM101'},
        {'student_id': '006', 'surname': 'Garcia', 'exam_code': 'CHEM101'},
        {'student_id': '007', 'surname': 'Martinez', 'exam_code': 'BIO101'},
        {'student_id': '008', 'surname': 'Davis', 'exam_code': 'BIO101'},
    ]

    return render_template('exam_room_allocation.html', students = students)

@beta.route("/beta/approveHours")
@login_required
def approve_hours():
    check_maintenance()
    permission_required(current_user.id, 'approve_hours', fatal=True)
    
    lessons = getLessonsToApprove()
    shifts = []
    for lesson in lessons:
        shifts.append({"tutor" : getTutor(lesson.tutorID), 
                       "day" : lesson.day, 
                       "startTime": lesson.startTime, 
                       "weekNo" : lesson.weekNo, 
                       "duration" : lesson.duration, 
                       "register" : lesson.register, 
                       "homework" : lesson.homework, 
                       "description" : lesson.description, 
                       "id" : lesson.lessonID                       
                       })    
        
    otherHours = staffHours.query.filter_by(approved = False).all()
    
    for log in otherHours: 
        shifts.append({"tutor" : getTutor(log.staffID), 
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

@beta.route("/beta/calendar")
@login_required
def calendar():
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

@beta.route("/beta/staff_members_view")
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

@beta.route("/beta/begin_game")
def begin_game():
    questions = gameQuestions.query.all()
    questions = [{"question" : question.question, "correctAnswer" : question.correctAnswer, "answer2" : question.answer2, "answer3" : question.answer3, "answer4" : question.answer4} for question in questions]
    random.shuffle(questions)  # Randomize the order of questions
    return render_template("begin_game.html", questions = questions)

@beta.route("/beta/leaderboard")
def leaderboard():
    return render_template("leaderboard.html")

@beta.route("/beta/game_questions", methods = ['POST', 'GET'])
def game_questions():
    return render_template('game_questions.html')

@beta.route('/beta/myProfile')
@login_required
def myProfile(): 
    if current_user.is_student():
        return redirect('/student_profile')
    elif current_user.is_tutor(): 
        return redirect('/tutor_info')
    else:
        return redirect('staff_info')

@beta.route('/beta/contract/<tutorID>')
@login_required
def show_contract(tutorID):
    pdf_path = "/var/www/webApp/webApp/contracts/2_contract.pdf"
    
    if not os.path.exists(pdf_path):
        return f'Contract for tutor ID {tutorID} not found.', 404

    contract = extract_text(pdf_path)
    return render_template('tutor_contract.html', contract=contract)

@beta.route('/beta/document')
@login_required
def document():
    return render_template('document.html')

@beta.route('/beta/marketplace', methods=['GET', 'POST'])
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

@beta.route('/beta/marketplaceFiles/<int:product_id>/<filename>')
@login_required
def uploaded_file(product_id, filename):
    return send_from_directory(os.path.join('/var/www/webApp/webApp/marketPlaceFiles', str(product_id)), filename)

@beta.route('/beta/create_booking_event', methods=['GET', 'POST'])
@login_required
def create_booking_event():
    # permission_required("")
    if current_user.is_admin() == False: 
        abort(404, )
        
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
    
    return render_template('create_booking_event.html')

@beta.route('/beta/book_event', methods=['GET', 'POST'])
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
    
    events = BookableEvent.query.all()
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


@beta.route('/beta/get_available_times/<int:event_id>', methods=['GET'])
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

@beta.route('/beta/register_exam_interest')
def iframe():
    # The rewritten form template needs exam/centre context that only the main
    # route builds — send beta traffic there instead of rendering without it.
    return redirect('/register_exam_interest')

@beta.route('/beta/enquiry', methods=['GET', 'POST'])
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

@beta.route('/beta/enquiries', methods=['GET', 'POST'])
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

@beta.route('/beta/log_hours', methods=['GET', 'POST'])
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

@beta.route('/beta/trial_registration', methods=['GET', 'POST'])
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

@beta.route('/beta/ucas_reference', methods = ['POST', 'GET'])
def ucas_reference():
    return render_template('ucas_reference.html')

@beta.route('/beta/user_points', methods = ['POST', 'GET'])
@login_required
def user_points():
    users = getAllCurrent("all")

    return render_template('user_points.html', users=users)

@beta.route('/beta/tutor_application', methods = ['POST', 'GET'])
def tutor_application():
    return render_template('tutor_application.html')

'           _____ _______ _____ ____  _   _  _____  '
'     /\   / ____|__   __|_   _/ __ \| \ | |/ ____| '
'    /  \ | |       | |    | || |  | |  \| | (___   '
'   / /\ \| |       | |    | || |  | | . ` |\___ \  '
'  / ____ \ |____   | |   _| || |__| | |\  |____) | '
' /_/    \_\_____|  |_|  |_____\____/|_| \_|_____/  '
'                                                   '

@beta.route('/beta/update_enquiry/<int:enquiry_id>', methods=['POST'])
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

CORS(beta, resources={r"/add_external_enquiry": {"origins": "https://ateamacademy.co.uk"}})
@beta.route('/beta/add_external_enquiry', methods=['POST'])
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

@beta.route('/beta/get_little_alerts')
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

@beta.route("/beta/addGameScore", methods=['POST', 'GET'])
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

@beta.route('/beta/getLeaderboard', methods=['POST', 'GET'])
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

@beta.route('/beta/get_questions', methods=['GET'])
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

@beta.route('/beta/add_question', methods=['POST'])
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

@beta.route('/beta/claim_product/<int:product_id>', methods=['POST'])
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

@beta.route('/beta/delete_product/<int:product_id>', methods=['POST'])
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

@beta.route('/beta/fetch-events')
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

@beta.route('/beta/create-event', methods=['POST'])
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

@beta.route('/beta/update-event', methods=['POST'])
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
    return jsonify({'status': 'error', 'message': 'Event not found'}), 404

@beta.route('/beta/delete-event/<int:event_id>', methods=['DELETE'])
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
        
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Event not found'}), 404

@beta.route("/beta/addUserToEvent/<eventID>", methods=['POST'])
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

    db.session.commit()

    return jsonify({'status': 'success'})

@beta.route("/beta/deleteRole", methods = ['POST', 'GET'])
@login_required
def deleteRole():
    data = request.get_json()
    role = data['role']
    eventID = data['eventID']
    
    stmt = delete(RoleEvent).where(and_(RoleEvent.role == role, RoleEvent.eventID == eventID))
    db.session.execute(stmt)
    db.session.commit()
    
    return jsonify({"status" : "success"}), 200

@beta.route("/beta/good_response", methods=['POST', 'GET'])
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

@beta.route('/beta/logout', methods=['POST', 'GET'])
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

@beta.route('/beta/recordAttendance', methods = ['POST'])
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

    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): Register for " + getLessonString(lessonID) + " has just been updated for week " + weekNo, date=datetime.utcnow()))
    db.session.commit()
    return ""

@beta.route('/beta/removeTempStudentAttendance', methods = ['POST', 'GET'])
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

@beta.route('/beta/removeUnregistered', methods=['POST', 'GET'])
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
    
@beta.route('/beta/removeTemps')
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

@beta.route('/beta/download/<fileFolder>/<fileName>')
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

@beta.route('/beta/upload', methods=['POST','GET'])
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

@beta.route('/beta/uploadForAll', methods=['POST', 'GET'])
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
                    db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): " + filename + " Was just uploaded for " + getSubjectName(subjectID) + " for week " + weekNo  + " and studentView has been set to " + str(studentView), date=datetime.utcnow()))
                else: 
                    db.session.add(log(role = getUserRole(current_user.id), message= "(" + getUserName(current_user.id) + "): " + filename + " Was just uploaded for " + getSubjectName(subjectID) + " as a subject resource and studentView has been set to " + str(studentView), date=datetime.utcnow()))

                db.session.commit()
                
                continue
            else:
                continue
                
        
    return jsonify(fileID=fileEntry.fileid, filename=filename)

@beta.route('/beta/uploadPayslip/<tutorid>', methods = ['POST'])
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

@beta.route('/beta/deleteUniqueFile', methods=['POST', 'GET'])
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
    
@beta.route('/beta/files/<fileFolder>/<fileName>', methods=['POST', 'GET'])
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
            #role_required("tutor", "Viewing a test: " + fileName)
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

@beta.route('/beta/userFiles/<userID>/<filename>', methods = ['POST', 'GET'])
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
   
    

@beta.route('/beta/create_lesson', methods=['POST', 'GET'])
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

@beta.route('/beta/add_students', methods=['POST', 'GET'])                #Not sure why this is here but havent removed in case its used somewhere
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

@beta.route('/beta/remove_lesson', methods=['POST', 'GET'])
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

@beta.route('/beta/updateLessonPlan/<id>', methods=['POST', 'GET'])
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

@beta.route("/beta/register_student", methods=['POST', 'GET'])
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
    return ""


@beta.route("/beta/register_potential_exam_student", methods=['POST'])
def register_potential_exam_student():
    try:
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
        
        user_files_path = '/var/www/webApp/webApp/userFiles/' + str(user.id)
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
        
        db.session.add(exam_student(studentID = studentEntry.id, uci = uci, uln = uln, access_arrangements = accessArrangements, message=subjects, approved = False))
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
        print(e)
        return jsonify({'error': str(e)}), 400


@beta.route("/beta/register_exam_student", methods=['POST', 'GET'])
@login_required
def register_exam_student():
    check_maintenance()

    data = request.get_json()

    firstName = data['firstName']
    secondName = data['secondName']
    gender = data['gender']
    dob = data['dob']
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

@beta.route("/beta/dismissLesson", methods=['POST', 'GET'])
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

@beta.route("/beta/addNewTutor", methods=['POST', 'GET'])
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

    db.session.add(User(role="tutor", otherID=id, email=data['email'].lower().strip(), password = generate_password_hash(password)))
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

@beta.route('/beta/deleteTutor/<id>', methods=['POST', 'GET'])
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

@beta.route("/beta/updateLessons", methods=["POST", "GET"])
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
    
@beta.route("/beta/addSubject", methods=['POST', 'GET'])
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

@beta.route("/beta/addStudents", methods=['POST', 'GET'])
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

@beta.route("/beta/removeStudent", methods=['POST', 'GET'])
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
@beta.route("/beta/convert_exam_student", methods=['POST', 'GET'])
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

@beta.route("/beta/removeSubject", methods=['POST', 'GET'])
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

@beta.route("/beta/deleteStudent/<id>", methods=['POST', 'GET'])
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
    
    stmt = delete(Students).where(Students.id == id)
    db.session.execute(stmt)
    db.session.commit()

    stmt = delete(User).where(and_(User.otherID == id, User.role == 'student' ))
    db.session.execute(stmt)
    db.session.commit()
    
    
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + name + " was just deleted", date=datetime.utcnow()))
    db.session.commit()
    
    return redirect("/admin_student_view")

@beta.route("/beta/deleteExamStudent")
@login_required
def deleteExamStudent(id):
    return ""

@beta.route("/beta/updateTutors", methods=['POST', 'GET'])
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

@beta.route("/beta/updateLessonInfo", methods=['POST', 'GET'])
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

@beta.route("/beta/updateTestInfo", methods = ['POST', 'GET'])
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

@beta.route("/beta/updateStudentInfo", methods = ['POST', 'GET'])
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

@beta.route("/beta/makeLessonPermanent", methods=['POST', 'GET'])
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

@beta.route('/beta/makeTest', methods = ['POST', 'GET'])
@login_required
def makeTest(): 
    check_maintenance()
    # #role_required("Tutor", "ACTION: making a test")
    permission_required(current_user.id, 'make_individual_test', fatal = True)
    data = request.get_json()
    
    lessonID = data['lessonID']
    weekNo = data['weekNo']
    date = data['date']
    total = data['total']
    name = data['name']
    
    createTestWithStudents(lessonID, weekNo, date, total, name)
        
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + "A test for " + getLessonString(lessonID) + " called " + name + "was just created", date=datetime.utcnow()))
    db.session.commit()
       
    
    return ""

@beta.route('/beta/makeAllTests', methods = ['POST', 'GET'])
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

@beta.route("/beta/updateTestMarks", methods = ['POST', 'GET'])
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

@beta.route("/beta/updateGrade", methods = ['POST', 'GET'])
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

@beta.route('/beta/deleteTest/<id>', methods = ['POST', 'GET'])
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

@beta.route('/beta/resetPassword', methods = ['POST', 'GET'])
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

@beta.route('/beta/makePerm', methods = ['POST', 'GET'])
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

@beta.route('/beta/makeGradePerm', methods = ['POST', 'GET'])
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

@beta.route("/beta/deleteGrade/<gradeID>", methods = ['POST', 'GET'])
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
    
@beta.route('/beta/fixFiles', methods = ['POST', 'GET'])
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

@beta.route('/beta/moveFiles', methods = ['POST', 'GET'])
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
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): " + getFileName(fileID) + " was just moved to " + getSubjectName(newSubjectID) + " for week " + newWeekNo, date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@beta.route("/beta/sendMessage", methods = ['POST', 'GET'])
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
        e1.send([getTutorEmail(getLessonTutor(int(lessonID))), getUserEmail(getMessageSender(replyTo)), getUserEmail(getThreadStarter(replyTo))], "New Message from" + getUserName(current_user.id), gen_html_new_message(message, lessonID, getUserName(current_user.id)))
    else: 
        e1 = EmailSender()
        e1.send([getUserEmail(getMessageSender(replyTo)), getUserEmail(getThreadStarter(replyTo))], "New Message from" + getUserName(current_user.id), gen_html_new_message(message, lessonID, getUserName(current_user.id)))
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "): has just sent a message to " + getLessonString(lessonID) ,  date=datetime.utcnow()))
    db.session.commit()
    
    return ""

@beta.route("/beta/deleteMessage", methods=['POST', 'GET'])
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

@beta.route("/beta/updateTutorAccessRights", methods=['POST', 'GET'])
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

@beta.route("/beta/updateRoleAccessRights", methods=['POST', 'GET'])
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

@beta.route("/beta/updateStudentAccessRights", methods=['POST', 'GET'])
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

@beta.route("/beta/getTutorHours", methods=['POST', 'GET'])
@login_required
def sendTutorHours():
    check_maintenance()
    try: 
        offset = int(request.args['offset'])
    except: 
        offset = 0
    return str(getTutorHours(getOtherID("tutor", current_user.id), gen_week_no(offset)))

@beta.route("/beta/getTutorMonthHours", methods=['POST', 'GET'])
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

@beta.route('/beta/getPermission', methods = ['GET'])
@login_required
def getPermission():
    check_maintenance()
    try: 
        permission = str(request.args['permission'])
    except:
        return jsonify({'permission' : False })

    return jsonify({'permission' : permission_required(current_user.id, permission) })

@beta.route('/beta/getRoleLevel', methods = ['GET'])
@login_required
def getRoleLevelFlask(): 
    try: 
        return jsonify({'roleLevel' : getRoleLevel(str(request.args['role'])) })
    except:
        return jsonify({'roleLevel' : getRoleLevel(getUserRole(current_user.id)) })

@beta.route('/beta/getRelativeRoleLevel', methods = ['GET'])
@login_required
def getRelativeRoleLevel():
    try:
        if request.args['inc'] == 'true':
            return jsonify({'roleLevel' : int(getRoleLevel(getUserRole(current_user.id))) >= int(getRoleLevel(str(request.args['role']))) })
        else: 
            return jsonify({'roleLevel' : int(getRoleLevel(getUserRole(current_user.id))) > int(getRoleLevel(str(request.args['role']))) })

    except: 
        return jsonify({'roleLevel' : False })

@beta.route("/beta/updateHours", methods = ['POST', 'GET'])
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

@beta.route("/beta/createAlert", methods = ['POST', 'GET'])
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

@beta.route("/beta/add_exam", methods = ['POST', 'GET'])
@login_required
def add_exam():
    check_maintenance()
    #role_required("admin", "ACTION: Adding an Exam")
    data = request.get_json()

    tier = data['tier']
    title = data['title']
    examBoard = data['examBoard']
    examCode= data['examCode']
    option = data['option']
    examSeries = data['examSeries']
    academicYear = data['academicYear']
    papers = data['papers']

    with db.session.no_autoflush:
        exam = Exams(tier = tier, title = title, examBoard = examBoard, code = examCode, Option = option, examSeries = examSeries, AcademicYear=academicYear)
        db.session.add(exam)
        db.session.commit()

        for paper in papers: 
            db.session.add(ExamPapers(examID = exam.examID, paperNo = paper['paperNumber'], paperCode = paper['paperCode'], duration = paper['duration'], total = paper['total'], date = paper['date'], extra_info = paper['extra_info'], startTime = paper['startTime']))
            db.session.commit()

        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just created an exam for " + examBoard + " " + tier + " " + title + " " + option + " with " + str(len(papers)) + " papers " ,  date=datetime.utcnow()))


    return ""

@beta.route("/beta/send_grades", methods = ['POST', 'GET'])
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

@beta.route("/beta/editFiles", methods = ['POST', 'GET'])
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

@beta.route("/beta/sendEmail", methods = ['POST', 'GET'])
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

@beta.route("/beta/sendClassEmail", methods = ['POST', 'GET'])
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

@beta.route("/beta/view_alert", methods = ['POST', 'GET'])
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

@beta.route('/beta/view_little_alert', methods=['GET', 'POST'])
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

@beta.route("/beta/edit_student_info", methods = ["POST", 'GET'])
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
    
    
    stmt = update(Students).values({key : value}).where(Students.id == studentID)
    db.session.execute(stmt)
    
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just changed the " + key + " for " + getStudent(studentID) + " to " + str(value),   date=datetime.utcnow()))
    db.session.commit()
    
    
    return ""

@beta.route("/beta/edit_exam_student_info", methods=["POST"])
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

@beta.route("/beta/update_student_and_ucas", methods=["POST"])
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
        'candidate_number': data.get('candidate_number')

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
    
@beta.route('/beta/payslips/<userID>/<filename>')
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

@beta.route('/beta/getFeedback', methods = ['POST', 'GET'])
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
        
@beta.route('/beta/dismissAlert', methods = ['POST', 'GET'])
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

@beta.route('/beta/addRole', methods=['POST', 'GET'])
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

@beta.route('/beta/save_document', methods=['POST'])
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

@beta.route('/beta/delete_document/<int:document_id>', methods=['DELETE'])
@login_required
def delete_document(document_id):
    document = Document.query.get_or_404(document_id)
    db.session.delete(document)
    db.session.commit()
    return jsonify({'status': 'success'})

@beta.route('/beta/load_document/<int:document_id>', methods=['GET'])
@login_required
def load_document(document_id):
    document = Document.query.get(document_id)
    if document:
        return jsonify(document.data)
    return jsonify({'sections': []})

@beta.route('/beta/list_documents', methods=['GET'])
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

@beta.route('/beta/save-signature/<int:id>', methods=['POST'])
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

@beta.route('/beta/upload_profile_picture/<userID>', methods=['POST'])
@login_required
def upload_profile_picture(userID):
    try:
        # Get the file from the request
        file = request.files.get('profilePicture')

        if file and file.filename.lower().endswith('.jpg'):
            # Secure the filename
            filename = 'profile_picture.jpg'
            file_path = os.path.join('www/webApp/webApp/userFiles', userID, filename)
            
            # Save the original file
            file.save(file_path)

            # Open and process the image
            with Image.open(file_path) as img:
                # Ensure the image is square
                img.thumbnail((512, 512), Image.ANTIALIAS)
                width, height = img.size
                if width != height:
                    new_size = max(width, height)
                    new_img = Image.new('RGB', (new_size, new_size), (255, 255, 255))
                    new_img.paste(img, (0, 0, width, height))
                    img = new_img
                img = img.resize((512, 512), Image.ANTIALIAS)
                img.save(file_path, format='JPEG')

            response = {
                'message': 'Profile picture uploaded and processed successfully'
            }
            return jsonify(response), 200

        else:
            return jsonify({'error': 'Invalid file format. Only JPG files are allowed.'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@beta.route('/beta/uploadUserFiles', methods=['POST'])
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

CORS(beta, resources={r"/send-grade-boundaries": {"origins": "https://ateamacademy.co.uk"}})
@beta.route('/beta/send-grade-boundaries', methods = ['POST', 'GET'])
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

@beta.route('/beta/create_centre', methods=['POST'])
@login_required
def create_centre():
    if current_user.is_admin():
        name = request.form.get('name')
        capacity = request.form.get('capacity')
        room_number = request.form.get('room_number', 0)
        address = request.form.get('address', '')
        admin_id = request.form.get('admin_id', 1)
        alias = request.form.get('alias', '')

        new_centre = Centre(name=name, capacity=capacity, room_number=room_number, address=address, admin_id=admin_id, alias=alias)
        db.session.add(new_centre)
        db.session.commit()

        
        db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  has just created the centre: " + name,   date=datetime.utcnow()))
        db.session.commit()

        return redirect(url_for('centre_overview'))
    else: 
        abort(400, )

@beta.route('/beta/register_trial_session', methods=['POST'])
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

@beta.route('/beta/submit_ucas_reference', methods=['POST'])
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

@beta.route('/beta/update_student_paid_status', methods=['POST'])
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

@beta.route('/beta/update_exam/<int:exam_id>', methods=['POST'])
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

@beta.route('/beta/delete_exam/<int:exam_id>', methods=['POST'])
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

@beta.route('/beta/get_papers/<int:exam_id>', methods=['GET'])
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

@beta.route('/beta/update_papers/<int:exam_id>', methods=['POST'])
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
@beta.route('/beta/update_student_paid_amount', methods=['POST'])
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
@beta.route('/beta/update_reference_required_status', methods=['POST'])
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
@beta.route('/beta/assign_ucas_reference', methods=['POST'])
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

@beta.route('/beta/assign_exams', methods=['POST'])
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
        return jsonify({'message': 'Exams assigned successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({'error': str(e)}), 500
    
@beta.route('/beta/updateCandidateNumber/<int:student_id>', methods=['POST'])
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
    
@beta.route('/beta/get_student_data/<int:student_id>', methods=['GET'])
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

@beta.route('/beta/download_exam_students_csv', methods=['GET'])
@login_required
def download_exam_students_csv():
    permission_required(current_user.id, "view_all_student_information", fatal=True)
    students = get_exam_students()  # Assuming this function returns all students
    csv_data = StringIO()
    writer = csv.writer(csv_data)
    
    # Write CSV header
    writer.writerow([
        'CN', 'Surname', 'Given Name', 'UCI No', 'D.O.B', 'Gender', 
        'Qualification', 'Option', 'Entry code', 'Tier', 'Series', 'Email', 
        'Contact number', 'Access Arrangement'
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
                    exam.Option,                # Subject
                    exam.code,                 # Entry code
                    exam.tier,                 # Tier
                    exam.examSeries,
                    student[0]['email'],             # Email
                    student[0]['priority_contact_1_mobile_telephone'],    # Contact number
                    student[1]['access_arrangements'] # Access Arrangement
                ])
    
    # Create the response with the CSV content
    csv_data.seek(0)
    return Response(csv_data, mimetype="text/csv", headers={
        "Content-disposition": "attachment; filename=exam_students.csv"
    })

@beta.route('/beta/getTimetablePreview/<int:student_id>')
@login_required
def get_timetable_preview(student_id):
    html_timetable = generate_html_exam_timetable(student_id)  # Generate the HTML for the timetable
    return html_timetable

@beta.route('/beta/sendEmailTimetable/<int:student_id>', methods=['POST'])
def send_email_timetable(student_id):
    e1 = EmailSender()
    
    # Fetch email addresses
    student_email = getStudentEmail(student_id)
    parent_email = getStudentParentEmail(student_id)
    contact_email = getStudentPriorityEmail(student_id)
    
    # Generate the timetable in HTML format
    timetable_html = generate_html_exam_timetable(student_id)
    
    # File attachments
    files = [
        '/var/www/webApp/webApp/files/EXAM_FILES/IFC-Coursework_Assessments_2024_FINAL (1).pdf', 
        '/var/www/webApp/webApp/files/EXAM_FILES/IFC-Written_Examinations_2024_FINAL.pdf', 
        '/var/www/webApp/webApp/files/EXAM_FILES/JCQ-Social-Media-Infographic-v6.pdf', 
        '/var/www/webApp/webApp/files/EXAM_FILES/Preparing-to-sit-your-exams-2024_25.pdf'
    ]
    
    # Ensure files exist
    valid_files = [file for file in files if os.path.exists(file)]
    
    # Filter valid emails only
    recipient_emails = [
        email for email in [student_email, parent_email, contact_email]
        if is_valid_email(email)
    ]
    
    if not recipient_emails:
        return jsonify({"error": "No valid email addresses provided."}), 400

    # Send email with valid recipients and files
    e1.send(recipient_emails, 'Exam Timetable', timetable_html, files=valid_files)
    
    return jsonify({"message": "Email sent successfully!"}), 200

@beta.route('/beta/update_points', methods=['POST'])
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
        message=f' {str(amount)} points were {action}d beacuse of {reason}',
    )
    db.session.add(little_alert)
    db.session.commit()
    
    return jsonify({'new_points': user.points, 'message': 'Points updated successfully'})

@beta.route('/beta/view_ucas_references', methods=['GET'])
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

    return render_template('view_ucas_references.html', references=ucas_references)

@beta.route('/beta/apply_tutor', methods=['POST'])
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
    e1.send(email=email, subject="Tutor application Received", message=gen_html_tutor_registration(name, password))
    
    return jsonify({'message': 'Tutor application submitted successfully!'}), 200


'''   _____  _____ _    _ ______ _____  _    _ _      _____ _   _  _____  '''
'''  / ____|/ ____| |  | |  ____|  __ \| |  | | |    |_   _| \ | |/ ____| '''
''' | (___ | |    | |__| | |__  | |  | | |  | | |      | | |  \| | |  __  '''
'''  \___ \| |    |  __  |  __| | |  | | |  | | |      | | | . ` | | |_ | '''
'''  ____) | |____| |  | | |____| |__| | |__| | |____ _| |_| |\  | |__| | '''
''' |_____/ \_____|_|  |_|______|_____/ \____/|______|_____|_| \_|\_____| '''

# # cron examples
# @scheduler.task('cron', id='do_job_3', week='*', day_of_week='*', hour = "19", minute = "0")
# def job3():
#     with app.app_context():
#         lesson_map = getLessonsTomorrow()
#         print(lesson_map)
        
#         for tutorID, lessons in lesson_map.items(): 
            
#             e1 = EmailSender()
#             e1.send(getTutorEmail(tutorID), "Schedule Tomorrow", message = render_template("email_template.html", bigTitle = "Schedule for Tomorrow", littleTitle = f"Hi {getStaff(tutorID)}", mainMessage = gen_html_tomorrow_timetable(getStaff(tutorID), lessons)))
#             # e1.send("asafwaan03@gmail.com", "Schedule Tomorrow - TEST", gen_html_tomorrow_timetable(getStaff(tutorID), lessons))
            
#         print("should have sent email")
        
            
            


'''    ____  _   _ ______            _______ _____ __  __ ______  '''
'''   / __ \| \ | |  ____|          |__   __|_   _|  \/  |  ____| '''
'''  | |  | |  \| | |__     ______     | |    | | | \  / | |__    '''
'''  | |  | | . ` |  __|   |______|    | |    | | | |\/| |  __|   '''
'''  | |__| | |\  | |____              | |   _| |_| |  | | |____  '''
'''   \____/|_| \_|______|             |_|  |_____|_|  |_|______| '''
                                                             

@beta.route("/beta/oneTime", methods=['POST', 'GET'])
@login_required
def oneTime():
    check_maintenance()
    role_required("admin", "ACTION: tried to trigger onetime")

    # with app.app_context():
    #     db.create_all()


    # extract_classes_from_html('/var/www/webApp/webApp/templates', '/var/www/webApp/webApp/output.txt')
    
    e1 = EmailSender()
    e1.send("asafwaan03@gmail.com", "TEST NO REPLY", "this is a test email")
        
    
    note = f''' getting class link '''
    db.session.add(log(role = getUserRole(current_user.id), message=" (" + getUserName(current_user.id) + "):  One-time was just triggered with the following note: " + note,   date=datetime.utcnow()))

    db.session.commit()   

    return redirect('/allTimetable?offset=0')

@beta.route('/beta/oneTimeView')
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
        return render_template('oneTimeView.html')
    if(page == "10"):
        lesson_map = getLessonsTomorrow()
        lesson = None
        
        for tutorID, lessons in lesson_map.items(): 
            if tutorID == 74:
                lesson = lessons

        return render_template("email_template.html", bigTitle = "Schedule for Tomorrow", littleTitle = f"Hi {getStaff}", mainMessage = gen_html_tomorrow_timetable(getStaff(74), lesson))

    
    
