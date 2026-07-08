from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Time, Date, ForeignKey, DateTime, Float
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.sql import func
from sqlalchemy import select, insert, update, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import Boolean 
from werkzeug.security import generate_password_hash
from flask_login import UserMixin, AnonymousUserMixin
import datetime 
from collections import defaultdict


db = SQLAlchemy()
''' 
log_on                                  ✓
view_all_lessons                        ✓ -implement timetable viewing
view_lessons_at_centre
change_lesson_time                      ✓
change_lesson_day                       ✓
change_lesson_tutor                     ✓
change_lesson_subject                   ✓
change_lesson_centre                    ✓
change_lesson_students                  ✓
add_a_new_lesson                        ✓
delete_a_lesson                         ✓
make_individual_test                    ✓
make_a_test_for_a_subject                   (will require changes to the base page)
add_a_new_subject                           (will require changes to the base page)    
upload_work_to_lesson                   ✓
upload_to_subject_resources             ✓
upload_to_subject                       ✓
change_lesson_plan                      ✓
view_all_tutor_information              ✓  (code done just needs change to base page)
view_below_payslips                     ✓
upload_paysClips                         ✓
edit_tutor_information                  ✓    
create_below_roles                      ✓
view_all_student_information            ✓
view_student_payment_information
edit_student_information                ✓
delete_a_student                        ✓
view_all_logs                           
view_centre_logs
approve_hours                           
send_emails_to_parents                  
send_emails_to_students                 ✓     
delete_messages
create_alerts                           ✓
dismiss_alerts                          ✓

'''

class Anonymous(AnonymousUserMixin):
  def __init__(self):
    self.username = 'Guest (Not Logged in)'
    self.id = None
    self.role = "Guest"

def get_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    return user


class User(db.Model):
    __tablename__= 'user'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String(20), ForeignKey('roles.name'))
    otherID = Column(Integer)
    email = Column(String)
    password = Column(String)
    points = Column(Integer, default = 0)
    log_on = Column(Boolean)    
    view_all_lessons = Column(Boolean, default = False)
    view_lessons_at_centre = Column(Boolean, default = False)     #still need to implement an ownership over the centres. Can have multiple
    change_lesson_time = Column(Boolean, default = False)
    change_lesson_day = Column(Boolean, default = False)
    change_lesson_tutor = Column(Boolean, default = False)
    change_lesson_subject = Column(Boolean, default = False)
    change_lesson_centre = Column(Boolean, default = False)
    change_lesson_students = Column(Boolean, default = False)
    add_a_new_lesson = Column(Boolean, default = False)
    delete_a_lesson = Column(Boolean, default = False)
    make_individual_test = Column(Boolean, default = False)
    make_a_test_for_a_subject = Column(Boolean, default = False)
    add_a_new_subject = Column(Boolean, default = False)
    upload_work_to_lesson = Column(Boolean, default = False)
    upload_to_subject_resources = Column(Boolean, default = False)
    upload_to_subject = Column(Boolean, default = False)
    change_lesson_plan = Column(Boolean, default = False)
    view_all_tutor_information = Column(Boolean, default = False)
    view_below_payslips = Column(Boolean, default = False)
    upload_payslips = Column(Boolean, default = False)
    edit_tutor_information = Column(Boolean, default = False)
    create_below_roles = Column(Boolean, default = False)
    view_all_student_information = Column(Boolean, default = False)
    view_student_payment_information = Column(Boolean, default = False)
    edit_student_information = Column(Boolean, default = False)
    delete_a_student = Column(Boolean, default = False)
    view_all_logs = Column(Boolean, default = False)
    view_centre_logs = Column(Boolean, default = False)
    approve_hours = Column(Boolean, default = False)
    send_emails_to_parents = Column(Boolean, default = False)
    send_emails_to_students = Column(Boolean, default = False)
    delete_messages = Column(Boolean, default = False)
    create_alerts = Column(Boolean, default = False)
    dismiss_alerts = Column(Boolean, default = False)
    create_marketplace_products = Column(Boolean, default = False)
    create_events = Column(Boolean, default = False)
    allow_maintenance = Column(Boolean, default = False)
    view_staff = Column(Boolean, default = False)
    view_staff_info = Column(Boolean, default = False)
    allow_maintenance = Column(Boolean, default = False)
    view_enquiries = Column(Boolean, default = False)
    reset_below_password = Column(Boolean, default = False)
    theme = Column(String, default = "default")

    
    def __init__(self, role, otherID, email, password):
        self.role = role
        self.otherID = otherID
        self.email = email
        self.password = password
        self.log_on = True
        self.view_all_lessons = False
        self.view_lessons_at_centre = False
        self.change_lesson_time = False
        self.change_lesson_day = False
        self.change_lesson_tutor = False
        self.change_lesson_subject = False
        self.add_a_new_lesson = False
        self.delete_a_lesson = False
        self.make_individual_test = False
        self.make_a_test_for_a_subject = False
        self.add_a_new_subject = False
        self.upload_work_to_lesson = False
        self.upload_to_subject_resources = False
        self.upload_to_subject = False
        self.change_lesson_plan = False
        self.view_all_tutor_information = False
        self.view_tutor_payslips = False
        self.edit_tutor_information = False
        self.add_a_new_tutor = False
        self.view_all_student_information = False
        self.view_student_payment_information = False
        self.edit_student_information = False
        self.delete_a_student = False
        self.view_all_logs = False
        self.view_centre_logs = False
        self.approve_hours = False
        self.send_emails_to_parents = False
        self.send_emails_to_students = False
        self.delete_messages = False
        
        
    def is_authenticated(self):
        return self.authenticated

    def is_active(self):   
        return True           

    def is_anonymous(self):
        return False          

    def get_id(self):         
        return str(self.id)
    
    def is_admin(self):
        if(self.role == "admin"):
            return True
        else: 
            return False
    
    def is_student(self):
        if(self.role == "student"):
            return True
        else:
            return False
        
    def is_tutor(self):
        if(self.role == "tutor"):
            return True
        else: 
            return False
    
    def is_parent(self):
        return self.role == "parent"
    
    def is_receptionist(self):
        return self.role == 'receptionist'
    
    def is_exams_officer(self):
        return self.role == "exams officer"

def getUserID(role, otherID):
    user = User.query.filter_by(role=role).filter_by(otherID=otherID).first()
    
    if user:
        return user.id

def getOtherID(role, id):
    user = User.query.filter_by(role=role).filter_by(id=id).first()
    
    if user: 
        return user.otherID
    else:
        return -1

def getOtherIDWithoutRole(id):
    user = User.query.filter_by(id=id).first()
    
    if user: 
        return user.otherID
    else:
        return -1

def getUserName(id):
    if id is None: 
        return "Guest Not Logged in"

    try: 
        user = get_user(id)
    except: 
        return "Guest Not Logged in"
    
    if user.role == "student":
        return getStudent(user.otherID)
    else: 
        return getStaff(user.otherID)

def getUserPassword(id):
    user = get_user(id)
    
    if user:
        return user.password

def getUserRole(id):
    user = User.query.filter_by(id = id).first()
    
    if user:
        return user.role
    else:
        return "anonymous"

def updatePoints(id, amount):
    user = User.query.get(id)
    if not user:
        return "user not found"
    
    stmt = update(User).values({'points' : user.points + amount }).where(User.id == id)
    db.session.execute(stmt)
    db.session.commit()
    
    db.session.add(log(role='admin', 
                    message=f"updated points for {getUserName(id)} by {str(amount)}", 
                    date=datetime.datetime.utcnow()))
    db.session.commit()

def getUserPoints(id):
    userEntry = User.query.filter_by(id = id).first()

    if userEntry: 
        return userEntry.points
    else:
        return 0 

def isParentFor(parentUserID, childStudentID): 
    parentEmail = User.query.filter_by(id = parentUserID).first()
    parentEmail = parentEmail.email
        
    return parentEmail == getStudentParentEmail(childStudentID)
    
    
    
    
    
# def getAll(role, log_on = False):
#     if log_on:
#         return User.query.filter_by(role = role).filter_by(log_on = True).all()
#     else: 
#         return User.query.filter_by(role = role).all()


'''
returns the user object
Returns the Names of the users in that role depending on whether they can log in or not
'''
def getAll(role, log_on=False):
    if role == "staff": 
        excluded_roles = ['student', 'parent', 'tutor']
        users = db.session.query(User).filter(User.role.notin_(excluded_roles)).all()
    elif role == "all":
        users = User.query.all()
    else:
        users = User.query.filter_by(role=role).all()


    
    result = []

    for user in users:
        if not (log_on and not user.log_on):
            user_data = user.__dict__.copy()
            user_data.pop('_sa_instance_state', None)  # Remove the SQLAlchemy instance state

            user_data['name'] = getUserName(user.id)

            result.append(user_data)
    
    return result

'''
returns the actual user objects of those in that role that are able to log in
'''
def getAllCurrent(role):
    #This function returns all of the users that can log in

    if role == "all":
        users = User.query.filter_by(log_on = True).all()
    else:
        users = User.query.filter_by(role = role).filter_by(log_on = True).all()

    # if role == "tutor": 
    #     query_result = db.session.query(User).join(Tutors, User.otherID == Tutors.id).filter(User.role == 'tutor', Tutors.log_on == True).all()
    # elif role == "student":
    #     query_result = db.session.query(User).join(Students, User.otherID == Students.id).filter(User.role == 'student', Students.log_on == True).all()
    # else: 
    #     return getAll(role)

    return users

def getUserEmail(id):
    if id:
        user = User.query.filter_by(id = id).first()

        if user:
            return user.email
        
            # if user.role == "tutor":
            #     return getTutorEmail(user.otherID)
            # elif user.role == "student":
            #     return getStudentEmail(user.otherID)
            # elif user.role == "admin":
            #     return getAdmin(user.otherID)
        else: 
            return "user does not exist"
    else: 
        return ""

def getUserPermission(id, action, role = None):
    if role:
        user = User.query.filter_by(role = role).filter_by(otherID = id).first()
    else:
        user = User.query.filter_by(id = id).first()

    if user:
        return user.__dict__[action]
    else: 
        return False

def getUserTheme(id):
    user = User.query.filter_by(id = id).first()
    
    if user:
        return user.theme
    else:
        return "default"


class Roles(db.Model):
    name = Column(String, primary_key = True)
    level = Column(Integer)
    view_all_lessons = Column(Boolean, default = False)
    view_lessons_at_centre = Column(Boolean, default = False)
    change_lesson_time = Column(Boolean, default = False)
    change_lesson_day = Column(Boolean, default = False)
    change_lesson_tutor = Column(Boolean, default = False)
    change_lesson_subject = Column(Boolean, default = False)
    change_lesson_centre = Column(Boolean, default = False)
    change_lesson_students = Column(Boolean, default = False)
    add_a_new_lesson = Column(Boolean, default = False)
    delete_a_lesson = Column(Boolean, default = False)
    make_individual_test = Column(Boolean, default = False)
    make_a_test_for_a_subject = Column(Boolean, default = False)
    add_a_new_subject = Column(Boolean, default = False)
    upload_work_to_lesson = Column(Boolean, default = False)
    upload_to_subject_resources = Column(Boolean, default = False)
    upload_to_subject = Column(Boolean, default = False)
    change_lesson_plan = Column(Boolean, default = False)
    view_all_tutor_information = Column(Boolean, default = False)
    view_below_payslips = Column(Boolean, default = False)
    upload_payslips = Column(Boolean, default = False)
    edit_tutor_information = Column(Boolean, default = False)
    create_below_roles = Column(Boolean, default = False)
    view_all_student_information = Column(Boolean, default = False)
    view_student_payment_information = Column(Boolean, default = False)
    edit_student_information = Column(Boolean, default = False)
    delete_a_student = Column(Boolean, default = False)
    view_all_logs = Column(Boolean, default = False)
    view_centre_logs = Column(Boolean, default = False)
    approve_hours = Column(Boolean, default = False)
    send_emails_to_parents = Column(Boolean, default = False)
    send_emails_to_students = Column(Boolean, default = False)
    delete_messages = Column(Boolean, default = False)
    create_alerts = Column(Boolean, default = False )
    dismiss_alerts = Column(Boolean, default = False )
    create_marketplace_products = Column(Boolean, default = False)
    create_events = Column(Boolean, default = False)
    allow_maintenance = Column(Boolean, default = False)
    view_staff = Column(Boolean, default = False)
    view_staff_info = Column(Boolean, default = False)
    allow_maintenance = Column(Boolean, default = False)
    view_enquiries = Column(Boolean, default = False)
    reset_below_password = Column(Boolean, default = False)


    def __init__(self, name, level):
        self.name = name
        self.level = level
        self.view_all_lessons = False
        self.view_lessons_at_centre = False
        self.change_lesson_time = False
        self.change_lesson_day = False
        self.change_lesson_tutor = False
        self.change_lesson_subject = False
        self.add_a_new_lesson = False
        self.delete_a_lesson = False
        self.make_individual_test = False
        self.make_a_test_for_a_subject = False
        self.add_a_new_subject = False
        self.upload_work_to_lesson = False
        self.upload_to_subject_resources = False
        self.upload_to_subject = False
        self.change_lesson_plan = False
        self.view_all_tutor_information = False
        self.view_tutor_payslips = False
        self.edit_tutor_information = False
        self.add_a_new_tutor = False
        self.view_all_student_information = False
        self.view_student_payment_information = False
        self.edit_student_information = False
        self.delete_a_student = False
        self.view_all_logs = False
        self.view_centre_logs = False
        self.approve_hours = False
        self.send_emails_to_parents = False
        self.send_emails_to_students = False
        self.delete_messages = False

def getRolePermission(role, permission):
    role = Roles.query.filter_by(name = role).first()
    
    if role:    
        return role.__dict__[permission]
    else: 
        return False

def getRoleLevel(role):
    level = Roles.query.filter_by(name = role).first()
    
    if level: 
        return level.level
    else:
        return -1

def getAllRoles():
    roleList = Roles.query.all()
    
    return [role.name for role in roleList]

class Admins(db.Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(10))
    password = Column(String(1000)) 
    associatedUser = Column(String)
    associatedEmail = Column(String)
    
    def __init__(self, username, password, associatedUser, associatedEmail):
        self.username = username
        self.password = password
        self.associatedUser = associatedUser
        self.associatedEmail = associatedEmail

class Tutors(db.Model):
    id = Column(Integer, primary_key=True)
    firstName = Column(String(50))
    middleName = Column (String)
    secondName = Column(String(50))
    known_as = Column(String(50))
    username = Column(String(50))
    password = Column(String(1000))
    email = Column(String(50))
    work_email = Column(String(50))
    date_of_birth = Column(Date)
    gender = Column(String) 
    country_of_birth = Column(String)
    nationality = Column(String)
    ethnic_origin = Column(String)
    mother_tongue = Column(String)
    post_code = Column(String)
    house_number = Column(String)
    street_name = Column(String)
    city_or_county = Column(String)
    borough_of_residence = Column(String)
    mode_of_travelling = Column(String)
    phone = Column(String(13)) 
    
    create_lessons = Column(Boolean)
    delete_lessons = Column(Boolean)
    update_lesson_plans = Column(Boolean)
    send_messages = Column(Boolean)
    update_lesson_info = Column(Boolean) 
    upload_files = Column(Boolean)
    log_on = Column(Boolean)
    #DBS number
    # National Insurance Number
    # Account Number
    
    def __init__(self, firstName, middleName, secondName, known_as, email, 
                 work_email, date_of_birth, gender, country_of_birth, nationality, ethnic_origin, 
                 mother_tongue, post_code, house_number, street_name, 
                 city_or_county, borough_of_residence, mode_of_travelling, phone, password):
        self.firstName = firstName
        self.middleName = middleName
        self.secondName = secondName
        self.known_as = known_as
        if work_email == "":
            self.username = email
        else: 
            self.username = work_email
        self.password = password
        self.email = email
        self.work_email = work_email
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.country_of_birth = country_of_birth
        self.nationality = nationality
        self.ethnic_origin = ethnic_origin
        self.mother_tongue = mother_tongue
        self.post_code = post_code
        self.house_number = house_number
        self.street_name = street_name
        self.city_or_county = city_or_county
        self.borough_of_residence = borough_of_residence
        self.mode_of_travelling = mode_of_travelling
        self.phone = phone
        
        self.create_lessons = False
        self.delete_lessons = False
        self.update_lesson_plans = False
        self.send_messages = False
        self.update_lesson_info = False
        self.upload_files = False
        self.log_on = True

def getTutorEmail(id):
    return Staff.query.filter_by(id=id).first().email

def getTutorAccess(id, action):
    tutor = User.query.filter_by(id = getUserID("tutor", id)).first()
    if tutor:
        return tutor.__dict__[action]
    else: 
        return False


class Staff(db.Model):
    id = Column(Integer, primary_key=True)
    role = Column(String)
    firstName = Column(String(50))
    middleName = Column (String)
    secondName = Column(String(50))
    known_as = Column(String(50))
    email = Column(String(50))
    work_email = Column(String(50))
    date_of_birth = Column(Date)
    gender = Column(String) 
    country_of_birth = Column(String)
    nationality = Column(String)
    ethnic_origin = Column(String)
    mother_tongue = Column(String)
    post_code = Column(String)
    house_number = Column(String)
    street_name = Column(String)
    city_or_county = Column(String)
    borough_of_residence = Column(String)
    mode_of_travelling = Column(String)
    phone = Column(String(13))
    points = Column(Integer, default = 0)

    def __init__(self, role, firstName, middleName,  secondName,  known_as,  email,  date_of_birth,  gender,
                 work_email = "",  country_of_birth = "",  nationality = "",  ethnic_origin = "",  mother_tongue = "",  post_code = "",  
                 house_number = "",  street_name = "",  city_or_county = "",  borough_of_residence = "",  mode_of_travelling = "",  phone = ""):
        
        self.role = role
        self.firstName = firstName
        self.middleName = middleName
        self.secondName = secondName
        self.known_as = known_as
        self.email = email
        self.work_email = work_email
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.country_of_birth = country_of_birth
        self.nationality = nationality
        self.ethnic_origin = ethnic_origin
        self.mother_tongue = mother_tongue
        self.post_code = post_code
        self.house_number = house_number
        self.street_name = street_name
        self.city_or_county = city_or_county
        self.borough_of_residence = borough_of_residence
        self.mode_of_travelling = mode_of_travelling
        self.phone = phone

#Returns the Student or Staff Objects
# staff = everyone except parents, students, tutors
# all_staff = everyone except parents and students
def getAllUsers(role, log_on = False):
    if role != 'all_staff':
        if log_on:
            users = User.query.filter_by(role = role).filter_by(log_on = True).all()
        else: 
            users = User.query.filter_by(role = role).all()
    else: 
        excluded_roles = ['student', 'parent']
        if log_on:
            users = db.session.query(User).filter(User.role.notin_(excluded_roles)).filter(User.log_on == True).all()
        else: 
            users = db.session.query(User).filter(User.role.notin_(excluded_roles)).all()        

    result = []
    if role == "student":
        for user in users:
            if user:
                student = Students.query.filter_by(id=user.otherID).first()
                if student: 
                    result.append(student)
    else: 
        for user in users: 
            if user:
                staff = Staff.query.filter_by(id=user.otherID).first()
                if staff:
                    result.append(staff)
                    
    
    
    return result

def getStaff(id):
    user = Staff.query.filter_by(id=id).first()

    if user:
        return user.firstName + " " + user.secondName
    else:
        return f"No Name for {id}"
    
def getStaffFirstName(id):
    user = Staff.query.filter_by(id=id).first()

    if user:
        return user.firstName.replace(" ", "")
    else:
        return f"No Name for {id}"

def getStaffRole(id):
    user = Staff.query.filter_by(id=id).first()

    if user:
        return user.role
    else:
        return f"No Role for {id}"

def getAdmin(id):
    return Staff.query.filter_by(id=id).filter_by(role="admin").first().firstName

def getAdminName(id):
    return Admins.query.filter_by(id=id).first().username

def getTutor(id):
    tutor = Staff.query.filter_by(id = id).filter_by(role="tutor").first()
    
    if tutor:
        return tutor.firstName + " " + tutor.secondName
    else: 
        return "No Tutor With ID: " + str(id)

def convertTutorToStaffID(tutorID):
    tutor = Tutors.query.filter_by(id=tutorID).first()

    if tutor:
        return Staff.query.filter_by(email=tutor.email).filter_by(role="tutor").first().id
    else:
        return -1 

def addPoints(staffID):
    original_points = Staff.query.filter_by(id = staffID).first().points
    
    if original_points: 
        stmt = update(Staff).where()

class StaffReviews(db.Model):
    staffID = Column(Integer, ForeignKey('staff.id'), primary_key = True)
    date = Column(Date, primary_key = True, default = datetime.date.today)
    PunctualityScore = Column(Integer)
    PunctualityComments = Column(String)
    LessonQualityScore = Column(Integer)
    LessonQualityComments = Column(String)
    LessonPreparednessScore = Column(Integer)
    LessonPreparednessComments = Column(String)
    ProfessionalismScore = Column(Integer)
    ProfessionalismComments = Column(String)
    TestScoresAverage = Column(Float)
    TestScoresComments = Column(String)
    extraComments = Column(String)
            
class StaffStrikes(db.Model):
    staffID = Column(Integer, ForeignKey('staff.id'), primary_key = True)
    date = Column(Date, primary_key = True, default = datetime.date.today)
    description = Column(String)


def gen_date_schema():
    # Every caller assigns this to a Date column (declaration_date), so return a
    # real date object — SQLAlchemy requires it on SQLite and it is equivalent on
    # Postgres (which previously just coerced the "YYYY-MM-DD" string this built).
    return datetime.date.today()



class Students(db.Model):
    id = Column(Integer, primary_key=True)
    firstName = Column(String(50))
    middleName = Column(String(50))
    secondName = Column(String(50))
    username = Column(String(10))
    password = Column(String(1000))
    email = Column(String(50))  #student-email
    parent_email = Column(String(50))  
    
    gender = Column(String) 
    date_of_birth = Column(Date)
    country_of_birth = Column(String)
    known_as = Column(String)
    nationality = Column(String)
    year_group = Column(String)
    ethnic_origin = Column(String)
    mother_tongue = Column(String)
    date_of_entry_uk = Column(Date)

    # Pupil Address
    post_code = Column(String)
    house_number = Column(String)
    street_name = Column(String)
    city_or_county = Column(String)
    borough_of_residence = Column(String)
    mode_of_travelling = Column(String)

    # Current School/s Child Attends (leave blank if not applicable)
    current_school_1 = Column(String)
    current_school_1_date_from = Column(Date)
    school_2 = Column(String)
    school_2_date_from = Column(Date)
    school_2_date_until = Column(Date)
    school_3 = Column(String)
    school_3_date_from = Column(Date)
    school_3_date_until = Column(Date)
    school_4 = Column(String)
    school_4_date_from = Column(Date)
    school_4_date_until = Column(Date)

    # Siblings / Additional Children
    sibling_1_forename = Column(String)
    sibling_1_surname = Column(String)
    sibling_1_date_of_birth = Column(Date)
    sibling_1_gender = Column(String)
    sibling_1_year_group = Column(String)
    sibling_1_id = Column(Integer, ForeignKey('user.id'))
    
    sibling_2_forename = Column(String)
    sibling_2_surname = Column(String)
    sibling_2_date_of_birth = Column(Date)
    sibling_2_gender = Column(String)
    sibling_2_year_group = Column(String)
    sibling_2_id = Column(Integer, ForeignKey('user.id'))
    
    sibling_3_forename = Column(String)
    sibling_3_surname = Column(String)
    sibling_3_date_of_birth = Column(Date)
    sibling_3_gender = Column(String)
    sibling_3_year_group = Column(String)
    sibling_3_id = Column(Integer, ForeignKey('user.id'))
    
    sibling_4_forename = Column(String)
    sibling_4_surname = Column(String)
    sibling_4_date_of_birth = Column(Date)
    sibling_4_gender = Column(String)
    sibling_4_year_group = Column(String)
    sibling_4_id = Column(Integer, ForeignKey('user.id'))

    # Looked After Children or Children on Child Protection Register
    previous_name = Column(String)
    legal_name = Column(String)
    child_protection_register = Column(Boolean)
    home_local_authority = Column(String)
    look_after_child_contact_info = Column(String)
    look_after_child_register = Column(Boolean)
    carer_name = Column(String)
    personal_education_plan = Column(Boolean)
    pep_contact_number = Column(String)

    # HM Armed Service Personnel Children - Leave blank if not applicable.
    armed_service_parent_name = Column(String)
    armed_service_parent_service = Column(String)
    armed_service_parent_rank = Column(String)
    armed_service_parent_additional_info = Column(String)

    # Medical Contact Information
    gp_name = Column(String)
    gp_post_code = Column(String)
    gp_telephone = Column(String)
    gp_practice_address = Column(String)
    child_normally_healthy = Column(Boolean)
    serious_illness_or_accidents = Column(String)
    condition_affecting_school_life = Column(String)
    allergies = Column(Boolean)
    allergyInfo = Column(String)
    asthma = Column(Boolean)
    epilepsy_or_fits = Column(Boolean)
    heart_problems = Column(Boolean)
    nose_bleeds = Column(Boolean)
    speech_or_hearing_difficulties = Column(Boolean)
    mobility_difficulties = Column(Boolean)
    other_difficulties = Column(String)
    known_medical_conditions = Column(String)
    medical_treatment_or_medicines = Column(String)
    extra_medical_info = Column(String)
    emergency_information = Column(String)

    # First Aid
    first_aid_permission = Column(Boolean)

    # Hospital or Emergency Services Referral
    hospital_referral_permission = Column(Boolean)

    # Special Educational Needs (SEN)
    special_educational_needs = Column(Boolean)
    sen_information = Column(String)

    # Behaviour Needs
    behavior_support_needed = Column(Boolean)
    behavior_support_info = Column(String)

    # Emergency Contact Details
    priority_contact_1_title = Column(String)
    priority_contact_1_relationship = Column(String)
    priority_contact_1_parental_responsibility = Column(Boolean)
    priority_contact_1_forename = Column(String)
    priority_contact_1_surname = Column(String)
    priority_contact_1_post_code = Column(String)
    priority_contact_1_home_telephone = Column(String)
    priority_contact_1_email = Column(String)
    priority_contact_1_mobile_telephone = Column(String)
    priority_contact_1_employer = Column(String)
    priority_contact_1_work_number = Column(String)
    priority_contact_1_other_info_numbers = Column(String)

    priority_contact_2_title = Column(String)
    priority_contact_2_relationship = Column(String)
    priority_contact_2_parental_responsibility = Column(Boolean)
    priority_contact_2_forename = Column(String)
    priority_contact_2_surname = Column(String)
    priority_contact_2_post_code = Column(String)
    priority_contact_2_home_telephone = Column(String)
    priority_contact_2_email = Column(String)
    priority_contact_2_mobile_telephone = Column(String)
    priority_contact_2_employer = Column(String)
    priority_contact_2_work_number = Column(String)
    priority_contact_2_other_info_numbers = Column(String)

    # Local Visits - Statement of Consent
    local_visits_permission = Column(Boolean)

    # Use of Photography and Digital Media
    digital_media_consent = Column(Boolean)

    # Pupil Ethnic Origin
    pupil_ethnic_origin = Column(String)

    # English as an Additional Language (EAL)
    eal = Column(Boolean)
    pupil_first_language = Column(String)
    pupil_first_language_spoken = Column(Boolean)
    pupil_first_language_read = Column(Boolean)
    pupil_first_language_written = Column(Boolean)
    
    pupil_other_language = Column(String)
    pupil_other_language_spoken = Column(Boolean)
    pupil_other_language_read = Column(Boolean)
    pupil_other_language_written = Column(Boolean)
    
    home_main_language = Column(String)
    home_main_language_spoken = Column(Boolean)
    home_main_language_read = Column(Boolean)
    home_main_language_written = Column(Boolean)
    
    home_other_language = Column(String)
    home_other_language_spoken = Column(Boolean)
    home_other_language_read = Column(Boolean)
    home_other_language_written = Column(Boolean)

    # Declaration
    declaration_signed = Column(Boolean)
    declaration_name = Column(String)
    declaration_date = Column(Date)

    # Additional Comments or Information about your Child/ Children
    additional_comments = Column(String)
    
    exam_student = Column(Boolean, default = False)
    log_on = Column(Boolean)
    see_all_work = Column(Boolean)
    
    payment_method = Column(String)
    payment_reference = Column(String)
    description = Column(String)
    monthly_amount = Column(Integer)
    
    def __init__(self,
        firstName,
        middleName,
        secondName,
        username,
        password,
        email,
        parent_email,
        gender ,
        date_of_birth ,
        country_of_birth ,
        known_as ,
        nationality ,
        year_group ,
        ethnic_origin ,
        mother_tongue ,
        date_of_entry_uk ,
        post_code,
        house_number,
        street_name,
        city_or_county,
        borough_of_residence,
        mode_of_travelling,
        current_school_1,
        current_school_1_date_from ,

        school_2,
        school_2_date_from ,
        school_2_date_until ,
        school_3,
        school_3_date_from ,
        school_3_date_until ,
        school_4,
        school_4_date_from ,
        school_4_date_until ,
        sibling_1_forename,

        sibling_1_surname,
        sibling_1_date_of_birth ,
        sibling_1_gender,
        sibling_1_year_group,
        sibling_1_id,
        sibling_2_forename,
        sibling_2_surname,

        sibling_2_date_of_birth ,
        sibling_2_gender,
        sibling_2_year_group,
        sibling_2_id,
        sibling_3_forename,
        sibling_3_surname,
        sibling_3_date_of_birth ,
        sibling_3_gender,
        sibling_3_year_group,
        sibling_3_id,
        sibling_4_forename,
        sibling_4_surname,
        sibling_4_date_of_birth ,
        sibling_4_gender,
        sibling_4_year_group,
        sibling_4_id,
        previous_name,
        legal_name,
        child_protection_register,
        home_local_authority,
        look_after_child_contact_info,
        look_after_child_register,
        carer_name,
        personal_education_plan,
        pep_contact_number,
        armed_service_parent_name,
        armed_service_parent_service,

        armed_service_parent_rank,
        armed_service_parent_additional_info,
        gp_name,
        gp_post_code,
        gp_telephone,
        gp_practice_address,
        child_normally_healthy,
        serious_illness_or_accidents,
        condition_affecting_school_life,
        allergies,
        allergyInfo,
        asthma,
        epilepsy_or_fits,
        heart_problems,
        nose_bleeds,
        speech_or_hearing_difficulties,
        mobility_difficulties,
        other_difficulties,
        known_medical_conditions,
        medical_treatment_or_medicines,
        extra_medical_info,
        emergency_information,
        first_aid_permission,
        hospital_referral_permission,
        special_educational_needs,
        sen_information,
        behavior_support_needed,
        behavior_support_info,
        priority_contact_1_title,
        priority_contact_1_relationship,
        priority_contact_1_parental_responsibility,
        priority_contact_1_forename,
        priority_contact_1_surname,
        priority_contact_1_post_code,
        priority_contact_1_home_telephone,
        priority_contact_1_email,
        priority_contact_1_mobile_telephone,
        priority_contact_1_employer,
        priority_contact_1_work_number,
        priority_contact_1_other_info_numbers,
        priority_contact_2_title,
        priority_contact_2_relationship,
        priority_contact_2_parental_responsibility,
        priority_contact_2_forename,
        priority_contact_2_surname,
        priority_contact_2_post_code,
        priority_contact_2_home_telephone,
        priority_contact_2_email,
        priority_contact_2_mobile_telephone,
        priority_contact_2_employer,
        priority_contact_2_work_number,
        priority_contact_2_other_info_numbers,
        local_visits_permission,
        digital_media_consent,
        declaration_signed,
        eal,
        pupil_first_language,
        pupil_first_language_spoken,
        pupil_first_language_read,
        pupil_first_language_written,
        pupil_other_language,
        pupil_other_language_spoken,
        pupil_other_language_read,
        pupil_other_language_written,
        home_main_language,
        home_main_language_spoken,
        home_main_language_read,
        home_main_language_written,
        home_other_language,
        home_other_language_spoken,
        home_other_language_read,
        home_other_language_written,
        declaration_name,
        declaration_date,
        additional_comments, 
        exam_student = False,
        log_on = True,
        see_all_work = False):
        
        self.firstName = firstName
        self.middleName = middleName
        self.secondName = secondName
        self.username = username
        self.password = password
        self.email = email
        self.parent_email = parent_email
        self.gender = gender
        try: 
            self.date_of_birth = date_of_birth 
        except: 
            self.date_of_birth = None
            
        self.country_of_birth = country_of_birth
        self.known_as = known_as
        self.nationality = nationality
        self.year_group = year_group
        self.ethnic_origin = ethnic_origin
        self.mother_tongue = mother_tongue
        try: 
            self.date_of_entry_uk = date_of_entry_uk
        except: 
            self.date_of_entry_uk = None
            
        self.post_code = post_code
        self.house_number = house_number
        self.street_name = street_name
        self.city_or_county = city_or_county
        self.borough_of_residence = borough_of_residence
        self.mode_of_travelling = mode_of_travelling
        
        self.current_school_1 = current_school_1
        try:
            self.current_school_1_date_from = current_school_1_date_from
        except: 
            self.current_school_1_date_from = None
            
        self.school_2 = school_2
        try:
            self.school_2_date_from = school_2_date_from
        except: 
            self.school_2_date_from = None
        try:
            self.school_2_date_until = school_2_date_until
        except: 
            self.school_2_date_until = None
            
        self.school_3 = school_3
        try:
            self.school_3_date_from = school_3_date_from
        except: 
            self.school_3_date_from = None
        try:
            self.school_3_date_until = school_3_date_until
        except: 
            self.school_3_date_until = None
            
        self.school_4 = school_4
        try:
            self.school_4_date_from = school_4_date_from
        except: 
            self.school_4_date_from = None
        try:
            self.school_4_date_until = school_4_date_until
        except: 
            self.school_4_date_until = None
        
        self.sibling_1_forename = sibling_1_forename
        self.sibling_1_surname = sibling_1_surname
        try:
            self.sibling_1_date_of_birth = sibling_1_date_of_birth
        except:
            self.sibling_1_date_of_birth = None
        self.sibling_1_gender = sibling_1_gender
        self.sibling_1_year_group = sibling_1_year_group
        self.sibling_1_id = sibling_1_id
        
        self.sibling_2_forename = sibling_2_forename
        self.sibling_2_surname = sibling_2_surname
        try:
            self.sibling_2_date_of_birth = sibling_2_date_of_birth
        except:
            self.sibling_2_date_of_birth = None
        self.sibling_2_gender = sibling_2_gender
        self.sibling_2_year_group = sibling_2_year_group
        self.sibling_2_id = sibling_2_id
        
        self.sibling_3_forename = sibling_3_forename
        self.sibling_3_surname = sibling_3_surname
        try:
            self.sibling_3_date_of_birth = sibling_3_date_of_birth
        except:
            self.sibling_3_date_of_birth = None
        self.sibling_3_gender = sibling_3_gender
        self.sibling_3_year_group = sibling_3_year_group
        self.sibling_3_id = sibling_3_id
        
        self.sibling_4_forename = sibling_4_forename
        self.sibling_4_surname = sibling_4_surname
        try:
            self.sibling_4_date_of_birth = sibling_4_date_of_birth
        except:
            self.sibling_4_date_of_birth = None
        self.sibling_4_gender = sibling_4_gender
        self.sibling_4_year_group = sibling_4_year_group
        self.sibling_4_id = sibling_4_id
        
        self.previous_name = previous_name
        self.legal_name = legal_name
        self.child_protection_register = child_protection_register if child_protection_register == True else False
        self.home_local_authority = home_local_authority
        self.look_after_child_contact_info = look_after_child_contact_info
        self.look_after_child_register = look_after_child_register if look_after_child_register == True else False
        self.carer_name = carer_name
        self.personal_education_plan = personal_education_plan if personal_education_plan == True else False
        self.pep_contact_number = pep_contact_number
        self.armed_service_parent_name = armed_service_parent_name
        self.armed_service_parent_service = armed_service_parent_service
        self.armed_service_parent_rank = armed_service_parent_rank
        self.armed_service_parent_additional_info = armed_service_parent_additional_info
        self.gp_name = gp_name
        self.gp_post_code = gp_post_code
        self.gp_telephone = gp_telephone
        self.gp_practice_address = gp_practice_address
        self.child_normally_healthy = child_normally_healthy if child_normally_healthy == True else False
        self.serious_illness_or_accidents = serious_illness_or_accidents if serious_illness_or_accidents == True else False
        self.condition_affecting_school_life = condition_affecting_school_life if condition_affecting_school_life == True else False
        self.allergies = allergies if allergies == True else False
        self.allergyInfo = allergyInfo
        self.asthma = asthma if asthma == True else False
        self.epilepsy_or_fits = epilepsy_or_fits if epilepsy_or_fits == True else False
        self.heart_problems = heart_problems if heart_problems == True else False
        self.nose_bleeds = nose_bleeds if nose_bleeds == True else False
        self.speech_or_hearing_difficulties = speech_or_hearing_difficulties if speech_or_hearing_difficulties == True else False
        self.mobility_difficulties = mobility_difficulties if mobility_difficulties == True else False
        self.other_difficulties = other_difficulties
        self.known_medical_conditions = known_medical_conditions
        self.medical_treatment_or_medicines = medical_treatment_or_medicines
        self.emergency_information = emergency_information
        self.extra_medical_info = extra_medical_info
        self.first_aid_permission = first_aid_permission if first_aid_permission == True else False
        self.hospital_referral_permission = hospital_referral_permission if hospital_referral_permission == True else False
        self.special_educational_needs = special_educational_needs if special_educational_needs == True else False
        self.sen_information = sen_information
        self.behavior_support_needed = behavior_support_needed if behavior_support_needed == True else False
        self.behavior_support_info = behavior_support_info
        self.priority_contact_1_title = priority_contact_1_title
        self.priority_contact_1_relationship = priority_contact_1_relationship
        self.priority_contact_1_parental_responsibility = priority_contact_1_parental_responsibility if priority_contact_1_parental_responsibility == True else False
        self.priority_contact_1_forename = priority_contact_1_forename
        self.priority_contact_1_surname = priority_contact_1_surname
        self.priority_contact_1_post_code = priority_contact_1_post_code
        self.priority_contact_1_home_telephone = priority_contact_1_home_telephone
        self.priority_contact_1_email = priority_contact_1_email
        self.priority_contact_1_mobile_telephone = priority_contact_1_mobile_telephone
        self.priority_contact_1_employer = priority_contact_1_employer
        self.priority_contact_1_work_number = priority_contact_1_work_number
        self.priority_contact_1_other_info_numbers = priority_contact_1_other_info_numbers
        self.priority_contact_2_title = priority_contact_2_title
        self.priority_contact_2_relationship = priority_contact_2_relationship
        self.priority_contact_2_parental_responsibility = priority_contact_2_parental_responsibility if priority_contact_2_parental_responsibility == True else False
        self.priority_contact_2_forename = priority_contact_2_forename
        self.priority_contact_2_surname = priority_contact_2_surname
        self.priority_contact_2_post_code = priority_contact_2_post_code
        self.priority_contact_2_home_telephone = priority_contact_2_home_telephone
        self.priority_contact_2_email = priority_contact_2_email
        self.priority_contact_2_mobile_telephone = priority_contact_2_mobile_telephone
        self.priority_contact_2_employer = priority_contact_2_employer
        self.priority_contact_2_work_number = priority_contact_2_work_number
        self.priority_contact_2_other_info_numbers = priority_contact_2_other_info_numbers
        self.local_visits_permission = local_visits_permission if local_visits_permission == True else False
        self.digital_media_consent = digital_media_consent if digital_media_consent == True else False
        self.eal = eal if eal == True else False
        self.pupil_first_language =pupil_first_language
        self.pupil_first_language_spoken = pupil_first_language_spoken  if pupil_first_language_spoken  == True else False
        self.pupil_first_language_read = pupil_first_language_read  if pupil_first_language_read  == True else False
        self.pupil_first_language_written = pupil_first_language_written  if pupil_first_language_written  == True else False
        self.pupil_other_language =pupil_other_language
        self.pupil_other_language_spoken = pupil_other_language_spoken  if pupil_other_language_spoken  == True else False
        self.pupil_other_language_read = pupil_other_language_read  if pupil_other_language_read  == True else False
        self.pupil_other_language_written = pupil_other_language_written  if pupil_other_language_written  == True else False
        self.home_main_language =home_main_language
        self.home_main_language_spoken = home_main_language_spoken  if home_main_language_spoken  == True else False
        self.home_main_language_read = home_main_language_read  if home_main_language_read  == True else False
        self.home_main_language_written = home_main_language_written  if home_main_language_written  == True else False
        self.home_other_language =home_other_language
        self.home_other_language_spoken = home_other_language_spoken if home_other_language_spoken == True else False 
        self.home_other_language_read = home_other_language_read  if home_other_language_read  == True else False
        self.home_other_language_written = home_other_language_written  if home_other_language_written  == True else False
        self.declaration_signed = declaration_signed if declaration_signed == True else False
        self.declaration_name = declaration_name
        try:
            self.declaration_date = declaration_date
        except:
            self.declaration_date = gen_date_schema()
        self.additional_comments = additional_comments 
        
        self.exam_student = exam_student
        self.log_on = log_on
        self.see_all_work = see_all_work

def getStudent(id):
    student = Students.query.filter_by(id = id).first()
    
    if student: 
        return student.firstName + " " + student.secondName
    else: 
        return "student not found"

def getStudentEmail(id):
    student = Students.query.filter_by(id = id).first()
    
    if student is not None and student.email is not None: 
        return student.email 
    else: 
        return ""
    
def getStudentParentEmail(id):
    student = Students.query.filter_by(id = id).first()
    
    if student is not None and student.parent_email is not None: 
        return student.parent_email
    else: 
        return ""
    
def getStudentPriorityEmail(id):
    student = Students.query.filter_by(id = id).first()
    
    if student is not None and student.parent_email is not None: 
        return student.priority_contact_1_email
    else: 
        return ""

def getStudentAccess(id, action):
    student = Students.query.filter_by(id = id).first()
    if student:
        return student.__dict__[action]
    else: 
        return False  

def getStudentDOB(id):
    student = Students.query.filter_by(id = id).first()
    
    if student is not None and student.date_of_birth is not None: 
        return student.date_of_birth.strftime("%d/%m/%Y")
    else: 
        return "--/--/--"
    
class exam_student(db.Model):
    studentID = Column(Integer, ForeignKey('students.id'), primary_key=True,)
    uci = Column(String)
    uln = Column(String)
    candidate_number = Column(String)
    access_arrangements = Column(String)
    message = Column(String, default = "")
    paid = Column(Boolean, default = False)
    paid_amount = Column(Integer)
    reference_required = Column(Boolean, default = False)
    reference_id = Column(Integer, ForeignKey('ucas_references.id'))
    approved = Column(Boolean, default = True)
    active = Column(Boolean, default = True)
    notes = Column(String, default = "")
    # The exam centre where this candidate sits their exams. Used by the seating
    # planner to only seat a centre's own candidates (Birmingham vs London/Manchester).
    centreID = Column(Integer, ForeignKey('centres.centreID'))
    # JSON list of the exams picked on the registration form
    # ([{"examID": 3, "label": "GCSE Mathematics Edexcel..."}]) so approval can
    # register the actual exams instead of an officer re-parsing free text.
    requested_exams = Column(String)
    # Auto-calculated fee (GBP) quoted at registration from the picked exams'
    # prices. paid/paid_amount keep recording what was actually received.
    quoted_total = Column(Float)
    # Exact amount (GBP, 2dp) collected via Stripe — the legacy paid_amount
    # column is Integer and cannot hold pence.
    paid_total = Column(Float)

def get_exam_students():
    # Join Students and ExamStudent, but only for those students where exam_student is True
    exam_students = db.session.query(Students, exam_student)\
        .join(exam_student, Students.id == exam_student.studentID)\
        .filter(Students.exam_student == True)\
        .all()
        
    exam_students_dict = []
    
    # Iterate over the results and build the dictionary
    for student, exam_stud in exam_students:
        date_of_birth_str = student.date_of_birth.strftime('%d/%m/%Y') if student.date_of_birth else None

        # Convert the Student object to a dictionary
        student_dict = {
            'id': student.id,
            'firstName': student.firstName,
            'middleName': student.middleName,
            'secondName': student.secondName,
            'username': student.username,
            'email': student.email,
            'parent_email': student.parent_email,
            'priority_contact_1_mobile_telephone' : student.priority_contact_1_mobile_telephone,
            'gender': student.gender,
            'date_of_birth': date_of_birth_str,  # Convert date to string
            'country_of_birth': student.country_of_birth,
            'known_as': student.known_as,
            'nationality': student.nationality,
            'year_group': student.year_group,
            'ethnic_origin': student.ethnic_origin,
            'mother_tongue': student.mother_tongue,
            'declaration_date' : student.declaration_date
            # Add more student fields as necessary
        }

        # Convert the studentExam object to a dictionary
        exam_student_dict = {
            'studentID': exam_stud.studentID,
            'uci': exam_stud.uci,
            'uln': exam_stud.uln,
            'access_arrangements': exam_stud.access_arrangements,
            'message': exam_stud.message,
            'paid': exam_stud.paid,
            'paid_amount': exam_stud.paid_amount,
            'reference_required': exam_stud.reference_required,
            'reference_id': exam_stud.reference_id,
            'approved': exam_stud.approved,
            'candidate_number': exam_stud.candidate_number,
            'notes' : exam_stud.notes,
            'message' : exam_stud.message,
            'centreID' : exam_stud.centreID,
            'quoted_total' : exam_stud.quoted_total,
            'paid_total' : exam_stud.paid_total

            # Add more examStudent fields as necessary
        }

        # Append the [student_dict, exam_student_dict] pair to the list
        exam_students_dict.append([student_dict, exam_student_dict])

    return sorted(exam_students_dict, key=lambda x : x[0]['firstName'] )
    

def getCandidateNumber(id):
    student = exam_student.query.filter_by(studentID = id).first()
    
    if student is not None and student.candidate_number is not None: 
        return student.candidate_number
    else: 
        return "NULL"
    
class TempStudent(db.Model):
    __tablename__ = 'tempstudent'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    firstName = Column(String(20))
    secondName = Column(String(20))
    emergencyNumber = Column(String(12))
    
    def __init__(self, firstName, secondName, emergencyNumber):
        self.firstName = firstName
        self.secondName = secondName
        self.emergencyNumber = emergencyNumber

class Subject(db.Model):
    __tablename__ = 'subjects'

    subjectID = Column(Integer, primary_key=True, autoincrement=True)
    tier = Column(String(15))
    title = Column(String(50))
    examBoard = Column(String(20))
    
    
    def __init__(self, tier, title, examBoard):
        self.tier = tier
        self.title = title
        self.examBoard = examBoard

def getSubjectID1(subject):
    tier = subject.split(" ", 1)[0]
    title = subject.split(" ", 1)[1]
    return getSubjectID2(tier, title)

def getSubjectID2(tier, title):
    subject = Subject.query.filter(and_(Subject.tier==tier, Subject.title==title)).first()
    if subject is not None: 
        return subject.subjectID
    else:
        return 0

def getSubjectName(id):
    if isinstance(id, int):
        subject = Subject.query.filter_by(subjectID=id).first()
        if subject is not None: 
            return subject.tier + " " + subject.title
        else: 
            return "Subject does not exist"
    else: 
        return "Subject doesnt exist"

def getSubjectFolder(id):
    subject = Subject.query.filter_by(subjectID = id).first()
    
    return subject.tier.replace(" ", "-").upper() +  "-" + subject.title.replace(" ", "-").upper()

def getTier(subjectID):
    subject = Subject.query.filter_by(subjectID = subjectID).first()

    if subject: 
        return subject.tier
    else: 
        return "No tier"
    
def getTitle(subjectID):
    subject = Subject.query.filter_by(subjectID = subjectID).first()

    if subject: 
        return subject.title
    else: 
        return "No title"

class unregisteredStudentLessons(db.Model):
    id = Column(Integer, primary_key=True)
    studentName = Column(String)
    lessonID = Column(Integer)
    
    def __init__(self, studentName, lessonID):
        self.studentName = studentName
        self.lessonID = lessonID   


class StudentLesson(db.Model):
    __tablename__ = 'students_lessons'

    studentID = Column(Integer, ForeignKey('students.id'), primary_key=True)
    lessonID = Column(Integer, primary_key=True)
    
    def __init__(self, studentID, lessonID):
        self.studentID = studentID
        self.lessonID = lessonID

def getStudents(lessonID):
    return StudentLesson.query.filter_by(lessonID = lessonID).all()


class Centre(db.Model):
    __tablename__ = 'centres'

    centreID = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30))
    capacity = Column(Integer)
    room_number = Column(Integer)
    address = Column(String(100))
    admin_id = Column(Integer, ForeignKey("user.id"))
    alias = Column(String)
    email = Column(String)
    # When this centre's morning/afternoon exam sessions start. Used by the
    # timetable email: papers display the centre's session time when set
    # (centres genuinely start at different times), else the paper's own time.
    am_start = Column(Time)
    pm_start = Column(Time)
    
    def __init__(self, name, capacity, room_number=0, address="", admin_id=1, alias = "", email = ""):
        self.name = name
        self.capacity = capacity
        self.room_number = room_number
        self.address = address
        self.admin_id = admin_id
        self.alias = alias
        self.email = email

def getCentre(id):
    return Centre.query.filter_by(centreID = id).first().name

def getAllCentres():
    return [centre.name for centre in Centre.query.all()]


class UserCentre(db.Model):
    centreID = Column(Integer, ForeignKey('centres.centreID'), primary_key = True)
    userID = Column(Integer, ForeignKey('user.id'), primary_key = True)

class Lesson(db.Model):
    __tablename__ = 'lessons'

    lessonID = Column(Integer, primary_key=True, autoincrement=True)
    tutorID = Column(Integer, ForeignKey('staff.id'))
    subjectID = Column(Integer, ForeignKey('subjects.subjectID'))
    day = Column(String(3))
    startTime = Column(Time)
    endTime = Column(Time)
    centreID = Column(Integer, ForeignKey('centres.centreID'))
    lessonName = Column(String(200))
    AcademicYear = Column(String(9))
    weekNo = Column(Integer)
    active = Column(Boolean, default=True)
    created_week = Column(Integer, default=1)
    joinable = Column(Boolean, default = True)


    tutors = relationship('Staff')
    subject = relationship('Subject')
    centre = relationship('Centre')
    
    def __init__(self, tutorID, subjectID, day, startTime, endTime, centreID, lessonName, AcademicYear, weekNo, active):
        self.tutorID = tutorID
        self.subjectID = subjectID
        self.day = day
        self.startTime = startTime
        self.endTime = endTime
        self.centreID = centreID
        self.lessonName = lessonName
        self.AcademicYear = AcademicYear
        self.weekNo = weekNo
        self.active = active
        self.created_week = gen_schema_week_no(0)
        self.joinable = True
        
def getLessonObject(lessonID):
    lesson = Lesson.query.filter_by(lessonID = lessonID).first()
    if lesson:
        return lesson
    else: 
        return None

def getLesson(id):
    lesson = Lesson.query.filter_by(lessonID = id).first()
    if lesson:
        tutorName = getTutor(lesson.tutorID)
        subject = getSubjectName(lesson.subjectID)
        centre = getCentre(lesson.centreID)
        return [str(lesson.startTime), str(lesson.endTime), lesson.day, subject, tutorName, centre, lesson.weekNo, lesson.active, lesson.AcademicYear]
    else: 
        return None

def getLessonString(id):
    lesson = getLesson(id)
    if lesson:
        start  = lesson[0]
        end = lesson[1]
        day  = lesson[2]
        subject  = lesson[3]
        tutor = lesson[4]
        centre = lesson[5]
        weekNo = lesson[6]
        active = lesson[7]
        year = lesson[8]
        
        result = subject + " at " + centre + " from " + start + " to " + end + " " + day + " taught by " + tutor + " in " + str(year)
        
        if weekNo != -1:
            result = result + " (Temporary for week " + str(weekNo) + ") "
        
        if not active:
            result = result + " ( Deleted ) "
        
        return result
    else: 
        return "Lesson does not Exist"

def getReducedLessonString(id):
    lesson = getLesson(id)
    if lesson:
        start  = lesson[0]
        end = lesson[1]
        day  = lesson[2]
        subject  = lesson[3]
        tutor = lesson[4]
        centre = lesson[5]
        weekNo = lesson[6]
        active = lesson[7]
        
        result = subject + " from " + start + " to " + end + " " + day 
        
        if weekNo != -1:
            result = result + " (Temporary for week " + str(weekNo) + ") "
        
        if not active:
            result = result + " ( Deleted ) "
        
        return result
    else: 
        return "Lesson does not Exist"

def getLessonLength(id):
    lesson = Lesson.query.filter_by(lessonID = id).first()
    
    if lesson.startTime and lesson.endTime:
            start_time = datetime.datetime.combine(datetime.datetime.today(), lesson.startTime)
            end_time = datetime.datetime.combine(datetime.datetime.today(), lesson.endTime)
            duration = end_time - start_time
            return duration.total_seconds() // 3600
    else:
        return 0

def getLessonTutor(id):
    lesson = Lesson.query.filter_by(lessonID = id).first()
    
    if lesson: 
        return lesson.tutorID
    else: 
        return "Lesson does not exist"

def getLessonSubject(id):
    lesson = Lesson.query.filter_by(lessonID = id).first()
    
    if lesson: 
        return lesson.subjectID
    else: 
        return "Lesson does not exist"

def getLessonsByScope(subjectID, scope):
    if scope == "all":
        lessonList = Lesson.query.filter_by(subjectID = subjectID).filter_by(active = True).filter_by(weekNo = -1).all()
        lessons = [lesson.lessonID for lesson in lessonList]
        return lessons

    elif scope == "week":
        lessonList = Lesson.query.filter_by(subjectID = subjectID).filter_by(active = True).filter_by(weekNo = -1).all()
        lessons = []

        for lesson in lessonList:
            if lesson.day == "MON" or lesson.day == "TUE" or lesson.day == "WED" or lesson.day == "THU" or lesson.day == "FRI":
                lessons.append(lesson.lessonID)
        
        return lessons

    elif scope == "weekend":
        lessonList = Lesson.query.filter_by(subjectID = subjectID).filter_by(active = True).filter_by(weekNo = -1).all()
        lessons = []

        for lesson in lessonList:
            if lesson.day == "SAT" or lesson.day == "SUN":
                lessons.append(lesson.lessonID)
        
        return lessons

    else:
        return []

def getLessonCentre(id):
    lesson = Lesson.query.filter_by(lessonID = id).first()
    
    if lesson: 
        return getCentre(lesson.centreID)
    else: 
        return "Lesson does not exist"
    
def getLessonDay(id):
    lesson = Lesson.query.filter_by(lessonID = id).first()
    
    if lesson: 
        return lesson.day
    else: 
        return "Lesson does not exist"
    
def getLessonStartTime(id):
    lesson = Lesson.query.filter_by(lessonID = id).first()
    
    if lesson: 
        return lesson.startTime
    else: 
        return "Lesson does not exist"

def getStudentsInLesson(id):
    '''
    {"registered": [], "unregistered" : []}
    '''
    lesson = Lesson.query.filter_by(lessonID = id).first()
    if lesson:
        regStudents = StudentLesson.query.filter_by(lessonID = id).all()
        
        registered = [student.studentID for student in regStudents]
        
        unregStudents = unregisteredStudentLessons.query.filter_by(lessonID = id).all()
        unregistered = [student.studentName for student in unregStudents]
        
    else:
        registered = [] 
        unregistered = []
        
    return {"registered" : registered, "unregistered" : unregistered}

def getNumberOfStudentsInLesson(id):
    students = getStudentsInLesson(id)

    return len(students["registered"]) + len(students["unregistered"])
    
def getLessonYear(id):
    lesson = Lesson.query.filter_by(lessonID=id).first()
    
    if lesson: 
        return lesson.AcademicYear
    else: 
        return f"No Lesson with ID {id}"
    
def checkLessonPermanence(id):
    lesson = Lesson.query.filter_by(lessonID = id).first()
    
    if lesson:
        weekNo = lesson.weekNo
          
class LessonInfo(db.Model):
    lessonID = Column(Integer, ForeignKey('lessons.lessonID'), primary_key=True)
    weekNo = Column(Integer, primary_key=True)
    tutorID = Column(Integer, ForeignKey('staff.id'))
    register = Column(Boolean)
    homework = Column(Boolean)
    dismissed = Column(Boolean)
    duration = Column(Float)
    day = Column(String)
    startTime = Column(Time) 
    description = Column(String)
    approved = Column(Boolean)
    rejected = Column(Boolean)
    
    
    def __init__(self, lessonID, weekNo, tutorID, register, homework, dismissed, description=""):
        self.lessonID = lessonID
        self.weekNo = weekNo
        self.tutorID = tutorID
        self.register = register
        self.homework = homework
        self.dismissed = dismissed
        self.duration = getLessonLength(lessonID)
        self.day = getLessonDay(lessonID)
        self.startTime = getLessonStartTime(lessonID)
        self.description = description
        self.approved = False
        self.rejected = False

def getLessonInfoString(id, weekNo):
    lesson = LessonInfo.query.filter_by(lessonID=id).filter_by(weekNo=weekNo).first()
    if lesson is not None:
        tutor = getTutor(lesson.tutorID)
    
        return getLessonString(id) + " taught THAT WEEK by " + tutor + " on week " + str(weekNo) + " for " + str(lesson.duration) + " hours "
    else:
        return "Lesson Not Found"

def getLessonsToApprove():
    return LessonInfo.query.filter_by(approved = False).filter_by(rejected = False).all()


class TutorSubject(db.Model):
    __tablename__ = 'tutor_subject'

    tutorID = Column(Integer, ForeignKey('staff.id'), primary_key=True)
    subjectID = Column(Integer, ForeignKey('subjects.subjectID'), primary_key=True)

    def __init__(self, tutorID, subjectID):
        self.tutorID = tutorID
        self.subjectID = subjectID
               
class StudentAttendance(db.Model):
    __tablename__ = 'student_attendance'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lessonID = Column(Integer, ForeignKey('lessons.lessonID'))
    weekNo = Column(Integer)
    AcademicYear = Column(String(9))
    studentID = Column(Integer, ForeignKey('students.id'))
    present = Column(Boolean)
    extra_notes = Column(String)
    
    def __init__(self, lessonID, weekNo, AcademicYear, studentID, present, extra_notes):
        self.lessonID = lessonID
        self.weekNo = weekNo
        self.AcademicYear = AcademicYear
        self.studentID = studentID
        self.present = present
        self.extra_notes = extra_notes

class TempAttendance(db.Model):
    __tablename__ = 'temp_attendance'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    lessonID = Column(Integer, ForeignKey('lessons.lessonID'))
    weekNo = Column(Integer)
    AcademicYear = Column(String(9))
    
    def __init__(self, name, lessonID, weekNo, AcademicYear):
        self.name = name
        self.lessonID = lessonID
        self.weekNo = weekNo
        self.AcademicYear = AcademicYear

class UnregisteredAttendance(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    lessonID = Column(Integer, ForeignKey('lessons.lessonID'))
    weekNo = Column(Integer)
    AcademicYear = Column(String(9))
    studentName = Column(String)
    present = Column(Boolean)
    extra_notes = Column(String)
    
    def __init__(self, lessonID, weekNo, AcademicYear, studentName, present, extra_notes):
        self.lessonID = lessonID
        self.weekNo = weekNo
        self.AcademicYear = AcademicYear
        self.studentName = studentName
        self.present = present
        self.extra_notes = extra_notes    


def getAttendance(lessonID, weekNo):
    student_attendance = StudentAttendance.query.filter_by(weekNo=int(weekNo), present=True, lessonID = lessonID).all()
    unregistered_attendance = UnregisteredAttendance.query.filter_by(weekNo=int(weekNo), present=True, lessonID = lessonID).all()
    temp_attendance = TempAttendance.query.filter_by(weekNo=int(weekNo), lessonID = lessonID).all()

    return student_attendance, unregistered_attendance, temp_attendance
        
        
#files can either have an associated lessonID OR (subjectID AND classtype). **
class Files(db.Model):
    fileid = Column(Integer, primary_key=True)
    lessonID = Column(Integer, ForeignKey('lessons.lessonID'))
    weekNo = Column(Integer)
    filename = db.Column(db.String(100))
    type = db.Column(db.String(20))          #type can be 'starter', 'main', 'homework' 
    associatedTopic = Column(String)
    subjectID = Column(Integer, ForeignKey('subjects.subjectID'))
    studentview = Column(Boolean) #default is true
    classtype = Column(String)
    hide_from_all = Column(Boolean)
    auto_print = Column(Boolean, default = False)
        
    def __init__(self, lessonID, weekNo, filename, type, associatedTopic, subjectID, studentview, classtype):
        self.lessonID = lessonID
        self.weekNo = weekNo
        self.filename = filename
        self.type = type
        self.associatedTopic = associatedTopic
        self.subjectID = subjectID 
        self.studentview = studentview
        self.classtype = classtype
        self.hide_from_all = False

def getFileName(fileID):
    file = Files.query.filter_by(fileid = fileID).first()
    
    if file is not None:
        return file.filename
    else: 
        return "No File Exists"

class lessonPlan(db.Model):
    subjectID = Column(Integer, ForeignKey('subjects.subjectID'), primary_key=True)
    weekNo = Column(Integer, primary_key=True)
    topic = Column(String)
    
    def __init__(self, subjectID, weekNo, topic):
        self.subjectID = subjectID
        self.weekNo = weekNo
        self.topic = topic

def getTopic(subjectID, weekNo):
    topicEntry = lessonPlan.query.filter_by(subjectID=subjectID).filter_by(weekNo = weekNo).first()
    
    if topicEntry: 
        return topicEntry.topic
    else: 
        return "no topic"


class log(db.Model):
    # Pass the callable, not its result: calling utcnow() here would freeze the
    # default at import time, giving every row the same timestamp.
    date = Column(DateTime, primary_key= True, default=datetime.datetime.utcnow)
    message = Column(String)
    role = Column(String)
    
    def __init__(self, date, message, role):
        self.date = date + datetime.timedelta(hours=1)
        self.message = message
        self.role = role
        
class Tests(db.Model):
    __tablename__ = 'tests'
    testID = Column(Integer, primary_key=True, autoincrement=True)
    lessonID = Column(Integer, ForeignKey('lessons.lessonID'))
    weekNo = Column(Integer)
    date = Column(Date)
    total = Column(Integer)
    filename = db.Column(db.String(100))
    name = db.Column(db.String(100))
    
    def __init__(self, lessonID, weekNo, date, total, filename, name):
        self.lessonID = lessonID
        self.weekNo = weekNo
        self.date = date
        self.total = total
        self.filename = filename
        self.name = name

def getTest(testID):
    test = Tests.query.filter_by(testID = testID).first()
    
    if test is not None: 
        return test.name + " for lesson " + getLessonString(test.lessonID)

    return "TEST DOESNT EXIST"

def createTestWithStudents(lessonID, weekNo, date, total, name, filename=""):
    if total == "":
        db.session.add(Tests(lessonID = lessonID, weekNo = weekNo, date = date, total = 0, name=name, filename = filename))
    else:
        db.session.add(Tests(lessonID = lessonID, weekNo = weekNo, date = date, total = total, name=name, filename = filename))
        
    
    db.session.commit()
    
    studentList = StudentLesson.query.filter_by(lessonID = lessonID).all()
    testID = Tests.query.all()[-1].testID
    
    for student in studentList:
        db.session.add(Grades(testID = testID, studentID = student.studentID, studentName = "", mark = -1, grade = ""))
        db.session.commit()
        
    return ""

def get_tests_in_date_range_and_lesson(start_date, end_date, lesson_id):
    """
    Fetch all tests within a specified date range and for a specific lesson.

    :param session: SQLAlchemy session object
    :param start_date: Start of the date range (inclusive)
    :param end_date: End of the date range (inclusive)
    :param lesson_id: ID of the lesson to filter by
    :return: List of tests within the date range and matching the lesson ID
    """
    test = db.session.query(Tests).filter(
        and_(
            Tests.date >= start_date,
            Tests.date <= end_date,
            Tests.lessonID == lesson_id
        )
    ).first()
    
    if test:
        return test.testID
    else:
        return None



class Grades(db.Model):
    __tablename__ = 'grades'
    gradeID = Column(Integer, primary_key=True, autoincrement=True)
    testID = Column(Integer, ForeignKey('tests.testID'))
    studentID = Column(Integer, ForeignKey('students.id'))
    studentName = Column(String)
    mark = Column(Integer)
    grade = Column(String)
    
    def __init__(self, testID, studentID, studentName, mark, grade):
        self.testID = testID
        self.studentID = studentID
        self.studentName = studentName
        self.mark = mark
        self.grade = grade

def getGrade(gradeID):
    grade = Grades.query.filter_by(gradeID = gradeID).first()
    
    if grade is None:
        return "grade not found"
    
    testTotal = Tests.query.filter_by(testID = grade.testID).first()
    
    if testTotal: 
        testTotal = testTotal.total
    else: 
        testTotal = 0
        
    if grade.studentID:
        return getStudent(grade.studentID) + "'s mark of " + str(grade.mark) + "/" + str(testTotal)  + ", grade: " + grade.grade + " for " + getTest(grade.testID)
    else: 
        return grade.studentName + "'s mark of " + str(grade.mark)  + "/" + str(testTotal) + ", grade: " + grade.grade + " for " + getTest(grade.testID)
    
def getGrades(gradeIDs):
    grades = []
    for grade in gradeIDs: 
        grades.append(getGrade(grade))
    
    return grades

def getAverageGrade(testID):
    result = (
        db.session.query(Grades.testID, Grades.mark)
        .filter(Grades.testID == testID, Grades.mark != -1)
        .all()
    )

    grades = [int(row.mark) for row in result]
    if grades:
        average_grade = sum(grades) / len(grades)
        return average_grade
    else:
        return 0

def getAllGrades(testID):
    grades = Grades.query.filter_by(testID = testID).filter(Grades.mark > -1).all()
    
    if grades:
        return grades
    else: 
        return []
        
def getGradeSubject(gradeID):
    grade = Grades.query.filter_by(gradeID=gradeID).first()
    
    if grade: 
        test = Tests.query.filter_by(testID = grade.testID).first()
        
        if test: 
            lesson = Lesson.query.filter_by(lessonID = test.lessonID).first()
            
            if lesson: 
                return lesson.subjectID
            
    return "subject could not be found"

def getGradeYear(gradeID):
    grade = Grades.query.filter_by(gradeID=gradeID).first()
    
    if grade: 
        test = Tests.query.filter_by(testID = grade.testID).first()
        
        if test: 
            lesson = getLessonYear(test.lessonID)
            
            if lesson: 
                return lesson
            
    return "subject could not be found"



class Messages(db.Model) :
    __tablename__ = "messages"
    messageID = Column(Integer, primary_key=True, autoincrement=True)
    lessonID = Column(Integer, ForeignKey('lessons.lessonID'))
    userID = Column(Integer, ForeignKey('user.id'))
    time = Column(DateTime)
    message = Column(String)
    replyTo = Column(Integer)
    deleted = Column(Boolean)
    
    def __init__(self, lessonID, userID, time, message, replyTo, deleted):
        self.lessonID = lessonID
        self.userID = userID
        self.time = time
        self.message = message
        self.replyTo = replyTo
        self.deleted = deleted
        
def getMessage(id):

    message = Messages.query.filter_by(messageID = id).first()

    if message:
        return getUserName(message.userID) + " wrote " + message.message + " for " + getLessonString(message.lessonID)
    else: 
        return "message does not exist"

def getMessageSender(id):
    message = Messages.query.filter_by(messageID = id).first()

    if message:
        return message.userID
    else:
        return None

def getThreadStarter(id):
    message = Messages.query.filter_by(messageID = id).first()

    if message:
        while message.replyTo != -1:
            message = Messages.query.filter_by(messageID = message.replyTo).first()
        
        return message.userID
    
    return None


class Alerts(db.Model): 
    alertID = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String)
    title = Column(String)
    message = Column(String)
    dismissed = Column(Boolean)
    
    def __init__(self, message, role, title):
        self.message = message
        self.role = role
        self.title = title
        self.dismissed = False

def createAlert(role, title, message):
    db.session.add(Alerts(role=role, title=title, message=message))
    alertID = Alerts.query.order_by(Alerts.alertID).all()[-1].alertID

    users = getAllCurrent(role)
    
    for user in users: 
        db.session.add(UserAlerts(alertID = alertID, userID = user.id))   

    db.session.commit()

def getAlertTitle(id):
    alert = Alerts.query.filter_by(alertID = id).first()
    
    if alert:
        return alert.title
    else: 
        return "Alert not Found"
    
class UserAlerts(db.Model):
    __tablename__ = "user_alerts"
    alertID = Column(Integer, ForeignKey('alerts.alertID'), primary_key=True)
    userID = Column(Integer, ForeignKey('user.id'), primary_key=True)
    viewed = Column(Boolean)
    
    def __init__(self, alertID, userID): 
        self.alertID = alertID
        self.userID = userID
        self.viewed = False
     
class gameQuestions(db.Model):
    question = Column(String, primary_key=True)
    correctAnswer = Column(String)
    answer2 = Column(String)
    answer3 = Column(String)
    answer4 = Column(String)

class GameScores(db.Model):
    email = Column(String, primary_key = True)
    name = Column(String)
    score = Column(Integer)
    image = Column(BYTEA)  # Store the image as a text blob

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    individual = db.Column(Boolean, default = False)
    sign = db.Column(Boolean, default = False)

def getDoc(id):
    doc = Document.query.filter_by(id = id).first()

    if doc: 
        return doc.title
    else:
        return f"no document with id {id}"
    
class individualDocument(db.Model):
    userID = Column(Integer, ForeignKey('user.id'), primary_key=True)
    docID = Column(Integer, ForeignKey('document.id'), primary_key=True)
    signature_destination = Column(String, nullable = True)
    
    def __init__(self, userID, docID):
        self.userID = userID
        self.docID = docID
        
        
class Product(db.Model):
    __tablename__ = 'product'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    reward = Column(Integer, nullable=False)
    description = Column(String(500), nullable=True)
    sold = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    completed = Column(Boolean, default=False)
    approved = Column(Boolean, default=False)

    user = relationship("User")    
        
def getProduct(id):
    product = Product.query.filter_by(id=id).first()

    if product: 
        return f"{product.name} for £{product.reward}"
    else:
        return f"no product found for id: {id}"

class Events(db.Model):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date)
    title = Column(String)
    description = Column(String)
    
    def __init__(self, date=datetime.datetime.today(), title="", description=""): 
        self.date = date
        self.title = title
        self.description = description

def getEvents(userID=-1):
    if userID == -1:
        events = Events.query.all()
        event_data = []
        for event in events:
            # Add associated users
            associated_users = User.query.join(UserEvents).filter(UserEvents.eventID == event.id).all()
            users_list = [{'id': user.id, 'name': getUserName(user.id), 'role' : getUserRole(user.id)} for user in associated_users]
            event_data.append({
                'id': event.id,
                'date': event.date.isoformat(),
                'title': event.title,
                'description': event.description,
                'users': users_list, 
                'type' : 'event'
            })
    else:
        user_role = getUserRole(userID)
        user_events = UserEvents.query.filter_by(userID=userID).all()
        role_events = getEventByRole(user_role)
        event_ids = set()

        for user_event in user_events:
            event_ids.add(user_event.eventID)

        for role_event in role_events:
            event_ids.add(role_event.eventID)

        event_data = []
        for event_id in event_ids:
            event = Events.query.get(event_id)
            associated_users = User.query.join(UserEvents).filter(UserEvents.eventID == event.id).all()
            users_list = [{'id': user.id, 'name': getUserName(user.id), 'role': getUserRole(user.id)} for user in associated_users]
            
            associated_roles = RoleEvent.query.filter_by(eventID=event.id).all()
            roles_list = [role_event.role for role_event in associated_roles]
            
            event_data.append({
                'id': event.id,
                'date': event.date.isoformat(),
                'title': event.title,
                'description': event.description,
                'users': users_list,
                'roles': roles_list, 
                'type' : 'event'
            })

    return event_data

def getEvent(eventID):
    event = Events.query.filter_by(id=eventID).first()

    if event:
        return f"{event.title} on {str(event.date)}"
    else: 
        return "no event found"

class RoleEvent(db.Model): 
    __tablename__ = 'roleevent'
    
    role = Column(String, primary_key=True)
    eventID = Column(Integer, ForeignKey('events.id'), primary_key=True)
    
    def __init__(self, role, eventID):
        self.role = role
        self.eventID = eventID 
        
def getEventByRole(role):
    return RoleEvent.query.filter_by(role = role).all()
    
class UserEvents(db.Model):
    __tablename__ = 'userevents'
    
    userID = Column(Integer, ForeignKey('user.id'), primary_key=True)
    eventID = Column(Integer, ForeignKey('events.id'), primary_key=True)
    
    def __init__(self, userID, eventID):
        self.userID = userID
        self.eventID = eventID
            
class Exams(db.Model): 
    __tablename__ = 'exams'
    examID = Column(Integer, primary_key=True, autoincrement=True)
    tier = Column(String(50))
    title = Column(String(50))
    examBoard = Column(String(20))
    code = Column(String(20))
    Option = Column(String(20))
    examSeries = Column(String(20))     #either Summer or November or Mock
    AcademicYear = Column(String(9))
    active = Column(Boolean, default = True)
    # Entry fee in GBP; drives the automatic quote (and prepayment) on the
    # public registration form. None = price on enquiry.
    price = Column(Float)


    def __init__(self, tier, title, examBoard, code, Option, examSeries, AcademicYear):
        self.tier = tier
        self.title = title
        self.examBoard = examBoard
        self.code = code
        self.Option = Option
        self.examSeries = examSeries.strip().capitalize()
        self.AcademicYear = AcademicYear
        
    def to_dict(self):
        return {
            'examID' : self.examID,
            'tier' : self.tier, 
            'title' : self.title, 
            'examBoard' : self.examBoard, 
            'code' : self.code, 
            'Option' : self.Option, 
            'examSeries' : self.examSeries, 
            'AcademicYear' : self.AcademicYear
        }

def getExams(AcademicYear):
    exams = Exams.query.filter_by(AcademicYear = AcademicYear).filter_by(active=True).all()
    
    return exams

def getExam(examID):
    exam = Exams.query.filter_by(examID = examID).first()
    
    if exam:
        return f"{exam.examBoard} {exam.tier} {exam.title} {exam.Option} for {exam.examSeries} {exam.AcademicYear}"
    
def getExamDetails(exam_id):
    # Fetch the exam details and papers for a specific exam
    exam = Exams.query.filter_by(examID=exam_id).first()
    papers = ExamPapers.query.filter_by(examID=exam_id).order_by(ExamPapers.date).all()
    return exam, papers

def getLatestExamDate(examID):
    exam, papers = getExamDetails(examID)
    if papers:
        return papers[-1].date
    else: 
        return datetime.strptime("2100-12-30", "%Y-%m-%d")
    
def getFirstExamDate(examID):
    exam, papers = getExamDetails(examID)
    if papers:
        return papers[0].date
    else: 
        return datetime.strptime("2100-12-30", "%Y-%m-%d")
    
    

class ExamPapers(db.Model):
    __tablename__ = 'exampapers'
    examID = Column(Integer, ForeignKey('exams.examID'), primary_key = True)
    paperNo = Column(Integer, primary_key = True)
    paperCode = Column(String(10))
    startTime = Column(Time)
    duration = Column(Integer)
    total = Column(Integer)
    date = Column(Date)
    extra_info = Column(String)
    
    def __init__(self, examID, paperNo, paperCode, duration, total, date, extra_info, startTime):
        self.examID = examID
        self.paperNo = paperNo
        self.paperCode = paperCode
        self.duration = duration
        self.total = total
        self.date = date
        self.extra_info = extra_info
        self.startTime = startTime
        
def getExamPapers(examID):
    papers = ExamPapers.query.filter_by(examID = examID).all()
    
    if papers: 
        return papers
    else: 
        return []
    
    

    
class studentExam(db.Model):
    __tablename__ = "studentExams"
    studentID = Column(Integer, ForeignKey('students.id'), primary_key = True)
    examID = Column(Integer, ForeignKey('exams.examID'), primary_key = True)

def getExamsForStudent(studentID, start_date=datetime.datetime.strptime("1900-12-30", "%Y-%m-%d"), end_date=datetime.datetime.strptime("3100-12-30", "%Y-%m-%d")):
    exams = studentExam.query.filter_by(studentID = studentID)
    
    if exams: 
        result = [
            exam.examID for exam in exams 
            if start_date <= datetime.datetime.strptime(datetime.datetime.strftime(getFirstExamDate(exam.examID), "%Y-%m-%d"), "%Y-%m-%d") <= end_date
        ]    
    else: 
        result = []
        
    return result 

def getStudentsForExam(examID):
    students = studentExam.query.filter_by(examID = examID)
    
    if students: 
        result = [student.examID for student in students]
    else: 
        result = []
        
    return result

class Feedback(db.Model):
    filename = Column(String, primary_key = True)
    studentID = Column(Integer, ForeignKey("students.id"))
    feedback = Column(String)
    student_good = Column(Boolean)
    tutor_good = Column(Boolean)
    correct = Column(Boolean)

    def __init__(self, filename, studentID, feedback, correct):
        self.filename = filename
        self.studentID = studentID
        self.feedback = feedback
        self.student_good = None
        self.tutor_good = None
        self.correct = correct

class LittleAlerts(db.Model):
    __tablename__ = 'little_alerts'

    alertID = Column(Integer, primary_key = True, autoincrement=True)
    date_time = Column(DateTime, default=datetime.datetime.utcnow)
    userID = Column(Integer, ForeignKey('user.id') )
    message = Column(String)
    viewed = Column(Boolean, default=False)
    
def createLittleAlertForRole(role, message):
    userList = getAllCurrent(role)
    
    for user in userList: 
        db.session.add(LittleAlerts(userID = user.id, message = message ))
        
    db.session.commit()
    
    return True   


class Enquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    callerName = db.Column(db.String(150), nullable=False)
    studentName = db.Column(db.String(150), nullable=False)
    year_group = db.Column(db.String(50), nullable=False)
    location = db.Column(db.Integer, db.ForeignKey("centres.centreID"), nullable=False)
    parent_email = db.Column(db.String(150), nullable=False)
    contact_number = db.Column(db.String(50), nullable=False)
    enquiry_info = db.Column(db.Text, nullable=False)
    result = db.Column(db.Text, nullable=False)
    userID = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    escalated = db.Column(db.Boolean, default=False)
    escalated_user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    date = Column(DateTime, default=datetime.datetime.utcnow)

class BookableEvent(db.Model):
    __tablename__ = 'bookable_events'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration = Column(Integer, nullable=False)  # Duration in minutes
    location = Column(String, nullable=False)
    description = Column(String, nullable=True)    
    bookable = Column(Boolean, default = True)
    

def getBookableEvents():
    # Retrieve all bookable events and their booking information
    events = BookableEvent.query.filter_by(bookable = True).all()
    event_data = []
    for event in events:
        # Add associated bookings
        bookings = Booking.query.filter_by(event_id=event.id).order_by(Booking.start_time.asc()).all()
        bookings_list = [{'id': booking.id, 'name': booking.name, 'email': booking.email, 'phone': booking.phone, 'start': str(booking.start_time)} for booking in bookings]
        
        event_data.append({
            'id': event.id,
            'title': event.name,
            'date': event.date.isoformat(),
            'description': event.description,
            'bookings': bookings_list, 
            'type' : 'bookable'
        })

    return event_data

def getAllBookableEvents():
    events = BookableEvent.query.all()

    return events

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('bookable_events.id'), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

class MailingList(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String)
    
class staffHours(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    staffID = Column(Integer, ForeignKey('staff.id'))
    date = Column(Date)
    hours = Column(Float)
    description = Column(String)
    approved = Column(Boolean)
    rejected = Boolean(Boolean)
    
class UCASReference(db.Model):
    __tablename__ = 'ucas_references'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    subjects = db.Column(db.Text, nullable=False)
    course = db.Column(db.String(150), nullable=False)
    qualifications = db.Column(db.Text, nullable=True)
    work_experience = db.Column(db.Text, nullable=True)
    reason = db.Column(db.Text, nullable=False)
    hobbies = db.Column(db.Text, nullable=True)
    extra_info = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    completed_reference = db.Column(String)
    
def getUCASName(id):
    name = UCASReference.query.filter_by(id = id).first()
    
    if name:
        return name.name
    else:
        return "No UCAS reference Found"

class PointSystem(db.Model):
    reason = Column(String, primary_key=True)
    amount = Column(Integer)
    
def getPointsAmount(reason):
    entry = PointSystem.query.filter_by(reason = reason).first()
    
    if entry: 
        return entry.amount
    else:
        return 0

class ExamRoom(db.Model):
    __tablename__ = 'exam_rooms'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    max_rows = db.Column(db.Integer, nullable=False)
    max_columns = db.Column(db.Integer, nullable=False)
    # Which centre this room belongs to, so the planner can filter rooms per centre.
    centreID = db.Column(db.Integer, db.ForeignKey('centres.centreID'), nullable=True)

    def __init__(self, name, max_rows, max_columns, centreID=None):
        self.name = name
        self.max_rows = max_rows
        self.max_columns = max_columns
        self.centreID = centreID

class SeedFlag(db.Model):
    # One-shot markers for data migrations run by the seeder, so a backfill can
    # run exactly once and never fight later hand-edits (renames/deletes).
    __tablename__ = 'seed_flags'
    name = db.Column(db.String, primary_key=True)

    def __init__(self, name):
        self.name = name


class RoomArrangements(db.Model):
    __tablename__ = 'room_arrangements'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('exam_rooms.id'), nullable=False)
    actual_rows = db.Column(db.Integer, nullable=True)  # Override rows for a specific exam date
    actual_columns = db.Column(db.Integer, nullable=True)  # Override columns for a specific exam date

    exam_room = db.relationship("ExamRoom", backref="arrangements")

    def __init__(self, date, room_id, actual_rows=None, actual_columns=None):
        self.date = date
        self.room_id = room_id
        self.actual_rows = actual_rows
        self.actual_columns = actual_columns

class SeatingArrangement(db.Model):
    __tablename__ = "seating_arrangement"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.examID"), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey("exam_rooms.id"), nullable=False)
    row = db.Column(db.Integer, nullable=False)
    column = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)

class EventRegistration(db.Model):
    __tablename__ = "event_registrations"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    dietary_reqs = db.Column(db.Text, nullable=False)
    events = db.Column(db.Text, nullable=False)  # Stores event names as a comma-separated string
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)  # Auto-record when registered


def gen_schema_week_no(offset):
    today = datetime.date.today() + datetime.timedelta(days=offset)
        
    # Find the first Monday in the most recent September
    year = today.year if today.month >= 9 else today.year - 1
    september_first = datetime.date(year, 9, 1)
    while september_first.weekday() != 0:  # Monday is 0
        september_first += datetime.timedelta(days=1)
    
    # Calculate the difference in weeks from that Monday to today
    difference = (today - september_first).days // 7
    
    # Week number starts from 1
    week_number = difference + 1
    
    return str(week_number)

def getGeneral(id, field):
    if field in ["tutorid", "tutorID", "tutorId", "Tutorid", "TutorID", "TutorId", "TUTORID"]:
        return getTutor(id)
    elif field in ["studentid", "studentID", "studentId", "Studentid", "StudentID", "StudentId", "STUDENTID"]:
        return getStudent(id)
    elif field in ["centreid", "centreID", "centreId", "Centreid", "CentreID", "CentreId", "CENTREID"]:
        return getCentre(id)
    elif field in ["subjectid", "subjectID", "subjectId", "Subjectid", "SubjectID", "SubjectId", "SUBJECTID"]:
        return getSubjectName(id)
    else:
        return str(id)
    
def gen_Student(firstName, secondName, username, password, email):
    return Students(firstName=firstName, secondName=secondName, username=username, password=password, email=email,
        parent_email = " ",
        middleName = " ",
        gender = " " ,
        date_of_birth = datetime.date(2000, 1, 1) ,
        country_of_birth = " " ,
        known_as = " " ,
        nationality = " " ,
        year_group = " " ,
        ethnic_origin = " " ,
        mother_tongue = " " ,
        date_of_entry_uk = datetime.date(2000, 1, 1) ,
        post_code = " " ,
        house_number = " " ,
        street_name = " " ,
        city_or_county = " " ,
        borough_of_residence = " " ,
        mode_of_travelling = " " ,
        
        current_school_1 = " " ,
        current_school_1_date_from = datetime.date(2000, 1, 1) ,
        school_2 = " " ,
        school_2_date_from = datetime.date(2000, 1, 1) ,
        school_2_date_until = datetime.date(2000, 1, 1) ,
        school_3 = " " ,
        school_3_date_from = datetime.date(2000, 1, 1) ,
        school_3_date_until = datetime.date(2000, 1, 1) ,
        school_4 = " " ,
        school_4_date_from = datetime.date(2000, 1, 1) ,
        school_4_date_until = datetime.date(2000, 1, 1) ,
        
        sibling_1_forename = " " ,
        sibling_1_surname = " " ,
        sibling_1_date_of_birth = datetime.date(2000, 1, 1) ,
        sibling_1_gender = " " ,
        sibling_1_year_group = " " ,
        sibling_1_id = None,
        sibling_2_forename = " " ,
        sibling_2_surname = " " ,
        sibling_2_date_of_birth = datetime.date(2000, 1, 1) ,
        sibling_2_gender = " " ,
        sibling_2_year_group = " " ,
        sibling_2_id = None,
        sibling_3_forename = " " ,
        sibling_3_surname = " " ,
        sibling_3_date_of_birth = datetime.date(2000, 1, 1) ,
        sibling_3_gender = " " ,
        sibling_3_year_group = " " ,
        sibling_3_id = None,
        sibling_4_forename = " " ,
        sibling_4_surname = " " ,
        sibling_4_date_of_birth = datetime.date(2000, 1, 1) ,
        sibling_4_gender = " " ,
        sibling_4_year_group = " " ,
        sibling_4_id = None,
        previous_name = " " ,
        legal_name = " ",
        look_after_child_contact_info = " ",
        child_protection_register = False,
        home_local_authority = " " ,
        look_after_child_register = False,
        carer_name = " " ,
        personal_education_plan = False,
        pep_contact_number = " " ,
        armed_service_parent_name = " " ,
        armed_service_parent_service = " " ,
        armed_service_parent_rank = " " ,
        armed_service_parent_additional_info = " " ,
        gp_name = " " ,
        gp_post_code = " " ,
        gp_telephone = " " ,
        gp_practice_address = " " ,
        child_normally_healthy = False,
        serious_illness_or_accidents = " " ,
        condition_affecting_school_life = " " ,
        allergies = False ,
        allergyInfo= " ",
        asthma = False,
        epilepsy_or_fits = False,
        heart_problems = False ,
        nose_bleeds = False,
        speech_or_hearing_difficulties = False,
        mobility_difficulties = False,
        other_difficulties = "",
        known_medical_conditions = " " ,
        medical_treatment_or_medicines = " " ,
        emergency_information = " " ,
        extra_medical_info = " ", 
        first_aid_permission = False,
        hospital_referral_permission = False,
        special_educational_needs = False,
        sen_information = " " ,
        behavior_support_needed = False,
        behavior_support_info = " " ,
        priority_contact_1_title = " " ,
        priority_contact_1_relationship = " " ,
        priority_contact_1_parental_responsibility = False ,
        priority_contact_1_forename = " " ,
        priority_contact_1_surname = " " ,
        priority_contact_1_post_code = " " ,
        priority_contact_1_home_telephone = " " ,
        priority_contact_1_email = " " ,
        priority_contact_1_mobile_telephone = " " ,
        priority_contact_1_employer = " " ,
        priority_contact_1_work_number = " " ,
        priority_contact_1_other_info_numbers = " " ,
        priority_contact_2_title = " " ,
        priority_contact_2_relationship = " " ,
        priority_contact_2_parental_responsibility = False ,
        priority_contact_2_forename = " " ,
        priority_contact_2_surname = " " ,
        priority_contact_2_post_code = " " ,
        priority_contact_2_home_telephone = " " ,
        priority_contact_2_email = " " ,
        priority_contact_2_mobile_telephone = " " ,
        priority_contact_2_employer = " " ,
        priority_contact_2_work_number = " " ,
        priority_contact_2_other_info_numbers = " " ,
        local_visits_permission = False ,
        digital_media_consent = False ,
        eal = False, 
        pupil_first_language = " ", 
        pupil_first_language_spoken = False, 
        pupil_first_language_read = False, 
        pupil_first_language_written = False, 
        pupil_other_language = " ", 
        pupil_other_language_spoken = False, 
        pupil_other_language_read = False, 
        pupil_other_language_written = False, 
        home_main_language = " ", 
        home_main_language_spoken = False, 
        home_main_language_read = False, 
        home_main_language_written = False, 
        home_other_language = " ", 
        home_other_language_spoken = False, 
        home_other_language_read = False, 
        home_other_language_written = False, 
        declaration_signed = False ,
        declaration_name = " " ,
        declaration_date = gen_date_schema() ,
        additional_comments = " " )

def gen_exam_student(firstName, secondName, gender, dob, email, parent_email, contact_no, username, password):
    return Students(firstName=firstName, secondName=secondName, username=username, password=password, email=email, gender = gender, date_of_birth=dob,
        parent_email = parent_email,
        middleName = " ",
        country_of_birth = " " ,
        known_as = " " ,
        nationality = " " ,
        year_group = " " ,
        ethnic_origin = " " ,
        mother_tongue = " " ,
        date_of_entry_uk = datetime.date(2000, 1, 1) ,
        post_code = " " ,
        house_number = " " ,
        street_name = " " ,
        city_or_county = " " ,
        borough_of_residence = " " ,
        mode_of_travelling = " " ,
        
        current_school_1 = " " ,
        current_school_1_date_from = datetime.date(2000, 1, 1) ,
        school_2 = " " ,
        school_2_date_from = datetime.date(2000, 1, 1) ,
        school_2_date_until = datetime.date(2000, 1, 1) ,
        school_3 = " " ,
        school_3_date_from = datetime.date(2000, 1, 1) ,
        school_3_date_until = datetime.date(2000, 1, 1) ,
        school_4 = " " ,
        school_4_date_from = datetime.date(2000, 1, 1) ,
        school_4_date_until = datetime.date(2000, 1, 1) ,
        
        sibling_1_forename = " " ,
        sibling_1_surname = " " ,
        sibling_1_date_of_birth = datetime.date(2000, 1, 1) ,
        sibling_1_gender = " " ,
        sibling_1_year_group = " " ,
        sibling_1_id = None,
        sibling_2_forename = " " ,
        sibling_2_surname = " " ,
        sibling_2_date_of_birth = datetime.date(2000, 1, 1) ,
        sibling_2_gender = " " ,
        sibling_2_year_group = " " ,
        sibling_2_id = None,
        sibling_3_forename = " " ,
        sibling_3_surname = " " ,
        sibling_3_date_of_birth = datetime.date(2000, 1, 1) ,
        sibling_3_gender = " " ,
        sibling_3_year_group = " " ,
        sibling_3_id = None,
        sibling_4_forename = " " ,
        sibling_4_surname = " " ,
        sibling_4_date_of_birth = datetime.date(2000, 1, 1) ,
        sibling_4_gender = " " ,
        sibling_4_year_group = " " ,
        sibling_4_id = None,
        previous_name = " " ,
        legal_name = " ",
        look_after_child_contact_info = " ",
        child_protection_register = False,
        home_local_authority = " " ,
        look_after_child_register = False,
        carer_name = " " ,
        personal_education_plan = False,
        pep_contact_number = " " ,
        armed_service_parent_name = " " ,
        armed_service_parent_service = " " ,
        armed_service_parent_rank = " " ,
        armed_service_parent_additional_info = " " ,
        gp_name = " " ,
        gp_post_code = " " ,
        gp_telephone = " " ,
        gp_practice_address = " " ,
        child_normally_healthy = False,
        serious_illness_or_accidents = " " ,
        condition_affecting_school_life = " " ,
        allergies = False ,
        allergyInfo= " ",
        asthma = False,
        epilepsy_or_fits = False,
        heart_problems = False ,
        nose_bleeds = False,
        speech_or_hearing_difficulties = False,
        mobility_difficulties = False,
        other_difficulties = "",
        known_medical_conditions = " " ,
        medical_treatment_or_medicines = " " ,
        emergency_information = " " ,
        extra_medical_info = " ", 
        first_aid_permission = False,
        hospital_referral_permission = False,
        special_educational_needs = False,
        sen_information = " " ,
        behavior_support_needed = False,
        behavior_support_info = " " ,
        priority_contact_1_title = " " ,
        priority_contact_1_relationship = " " ,
        priority_contact_1_parental_responsibility = False ,
        priority_contact_1_forename = " " ,
        priority_contact_1_surname = " " ,
        priority_contact_1_post_code = " " ,
        priority_contact_1_home_telephone = contact_no ,
        priority_contact_1_email = parent_email ,
        priority_contact_1_mobile_telephone = contact_no ,
        priority_contact_1_employer = " " ,
        priority_contact_1_work_number = " " ,
        priority_contact_1_other_info_numbers = " " ,
        priority_contact_2_title = " " ,
        priority_contact_2_relationship = " " ,
        priority_contact_2_parental_responsibility = False ,
        priority_contact_2_forename = " " ,
        priority_contact_2_surname = " " ,
        priority_contact_2_post_code = " " ,
        priority_contact_2_home_telephone = " " ,
        priority_contact_2_email = " " ,
        priority_contact_2_mobile_telephone = " " ,
        priority_contact_2_employer = " " ,
        priority_contact_2_work_number = " " ,
        priority_contact_2_other_info_numbers = " " ,
        local_visits_permission = False ,
        digital_media_consent = False ,
        eal = False, 
        pupil_first_language = " ", 
        pupil_first_language_spoken = False, 
        pupil_first_language_read = False, 
        pupil_first_language_written = False, 
        pupil_other_language = " ", 
        pupil_other_language_spoken = False, 
        pupil_other_language_read = False, 
        pupil_other_language_written = False, 
        home_main_language = " ", 
        home_main_language_spoken = False, 
        home_main_language_read = False, 
        home_main_language_written = False, 
        home_other_language = " ", 
        home_other_language_spoken = False, 
        home_other_language_read = False, 
        home_other_language_written = False, 
        declaration_signed = False ,
        declaration_name = " " ,
        declaration_date = gen_date_schema() ,
        additional_comments = " ", 
        exam_student = True)

def db_init():
    # Insert data into the tables

    centres = [Centre(name="Online", capacity=30),
               Centre(name='Coventry Road', capacity=10),
               Centre(name='Soho Road', capacity=10) ]
    
    db.session.add_all(centres)
    db.session.commit()
    
    subjectList = [
    Subject(tier='GCSE', title='Maths', examBoard='Edexcel'),
    Subject(tier='GCSE', title='English', examBoard='AQA'),
    Subject(tier='GCSE', title='Chemistry', examBoard='AQA'),
    Subject(tier='GCSE', title='Biology', examBoard='AQA'),
    Subject(tier='A-LEVEL', title='Maths', examBoard='Edexcel'),
    Subject(tier='A-LEVEL', title='English', examBoard='Edexcel'),
    Subject(tier='A-LEVEL', title='Chemistry', examBoard='AQA'),
    Subject(tier='A-LEVEL', title='Biology', examBoard='AQA'),
    ]
    db.session.add_all(subjectList)
    db.session.commit()
    
    tutors = [
        Tutors(  firstName = "Safwaan",
                middleName = "",
                secondName = "Ali",
                known_as = "Safwaan",
                email = "asafwaan03@gmail.com",
                work_email = "safwaan@ateamacademy.co.uk",
                date_of_birth = "2003-06-23",
                gender = "Male",
                country_of_birth = "",
                nationality = "",
                ethnic_origin ="",
                mother_tongue ="",
                date_of_entry_uk ="2003-06-23",
                post_code ="",
                house_number ="",
                street_name ="",
                city_or_county ="",
                borough_of_residence ="",
                mode_of_travelling ="",
                phone = "07814 160991")
    ]
    db.session.add_all(tutors)
    db.session.commit() 
    
    
    tutor_subjects = [
        TutorSubject(1, 1),
        TutorSubject(1, 2),
        TutorSubject(1, 3),
        TutorSubject(1, 4),
        TutorSubject(1, 5),
        TutorSubject(1, 6)
    ]   
    db.session.add_all(tutor_subjects)
    db.session.commit()    

    students = [
    gen_Student(firstName ='Ahsan', secondName ='Younis', username ='Ahsan123', password='password', email = 'ahsanyounis@gmail.com'),
    gen_Student(firstName ='Peter', secondName ='Ezemba', username ='peter123', password='password', email = 'peterEzemba@gmail.com'),
    gen_Student(firstName ='Aasma', secondName ='Sunayr', username ='aasma123', password='password', email = 'aasmayounis@gmail.com'),
    gen_Student(firstName ='Samir', secondName ='Qureshi',username = 'samir123',password='password', email = 'samirqureshi@gmail.com')
    ]
    db.session.add_all(students)
    db.session.commit()
    
    db.session.add(Students(
    firstName="John",
    middleName="David",
    secondName="Smith",
    username="john123",
    password="securepassword",
    email="john.smith@example.com",
    parent_email="parent@example.com",
    gender="Male",
    date_of_birth="2005-05-10",
    country_of_birth="United Kingdom",
    known_as="Johnny",
    nationality="British",
    year_group="10",
    ethnic_origin="Caucasian",
    mother_tongue="English",
    date_of_entry_uk="2015-09-01",
    post_code="SW1A 1AA",
    house_number="123",
    street_name="Main Street",
    city_or_county="London",
    borough_of_residence="Westminster",
    mode_of_travelling="Bus",
    current_school_1="ABC Secondary School",
    current_school_1_date_from="2015-09-01",
    school_2="XYZ Elementary School",
    school_2_date_from="2010-09-01",
    school_2_date_until="2015-08-31",
    school_3="123 Primary School",
    school_3_date_from="2007-09-01",
    school_3_date_until="2010-08-31",
    school_4="456 Middle School",
    school_4_date_from="2015-09-01",
    school_4_date_until="2018-06-30",
    sibling_1_forename="Emma",
    sibling_1_surname="Smith",
    sibling_1_date_of_birth="2003-02-15",
    sibling_1_gender="Female",
    sibling_1_year_group="8",
    sibling_1_id="SIB123",
    sibling_2_forename="James",
    sibling_2_surname="Smith",
    sibling_2_date_of_birth="2010-10-03",
    sibling_2_gender="Male",
    sibling_2_year_group="3",
    sibling_2_id="SIB456",
    sibling_3_forename="Olivia",
    sibling_3_surname="Johnson",
    sibling_3_date_of_birth="2009-07-20",
    sibling_3_gender="Female",
    sibling_3_year_group="5",
    sibling_3_id="SIB789",
    sibling_4_forename="Sophia",
    sibling_4_surname="Brown",
    sibling_4_date_of_birth="2013-12-08",
    sibling_4_gender="Female",
    sibling_4_year_group="1",
    sibling_4_id="SIB101",
    previous_name="Johnny Johnson",
    legal_name="John David Smith",
    child_protection_register=False,
    home_local_authority="London Borough of Westminster",
    look_after_child_contact_info="CareProvider Inc.",
    look_after_child_register=True,
    carer_name="Mary Johnson",
    personal_education_plan=False,
    pep_contact_number="01234 567890",
    armed_service_parent_name="David Smith Sr.",
    armed_service_parent_service="Royal Army",
    armed_service_parent_rank="Sergeant",
    armed_service_parent_additional_info="Deployed overseas",
    gp_name="Dr. Jane Johnson",
    gp_post_code="SW1A 1AB",
    gp_telephone="020 1234 5678",
    gp_practice_address="123 Medical Avenue, London",
    child_normally_healthy=True,
    serious_illness_or_accidents="None",
    condition_affecting_school_life="None",
    allergies=False,
    allergyInfo="N/A",
    asthma=False,
    epilepsy_or_fits=False,
    heart_problems=False,
    nose_bleeds=False,
    speech_or_hearing_difficulties=False,
    mobility_difficulties=False,
    other_difficulties=False,
    known_medical_conditions="None",
    medical_treatment_or_medicines="None",
    extra_medical_info="N/A",
    emergency_information="Contact parent",
    first_aid_permission=True,
    hospital_referral_permission=True,
    special_educational_needs=False,
    sen_information="N/A",
    behavior_support_needed=False,
    behavior_support_info="N/A",
    priority_contact_1_title="Mr.",
    priority_contact_1_relationship="Father",
    priority_contact_1_parental_responsibility=True,
    priority_contact_1_forename="David",
    priority_contact_1_surname="Smith",
    priority_contact_1_post_code="SW1A 1AB",
    priority_contact_1_home_telephone="01234 567890",
    priority_contact_1_email="david.smith@example.com",
    priority_contact_1_mobile_telephone="07890 123456",
    priority_contact_1_employer="XYZ Corporation",
    priority_contact_1_work_number="020 1234 5678",
    priority_contact_1_other_info_numbers="N/A",
    priority_contact_2_title="Mrs.",
    priority_contact_2_relationship="Mother",
    priority_contact_2_parental_responsibility=True,
    priority_contact_2_forename="Emma",
    priority_contact_2_surname="Smith",
    priority_contact_2_post_code="SW1A 1AB",
    priority_contact_2_home_telephone="01234 567890",
    priority_contact_2_email="emma.smith@example.com",
    priority_contact_2_mobile_telephone="07890 123456",
    priority_contact_2_employer="ABC Corporation",
    priority_contact_2_work_number="020 1234 5678",
    priority_contact_2_other_info_numbers="N/A",
    local_visits_permission=True,
    digital_media_consent=True,
    declaration_signed=True,
    eal=True,
    pupil_first_language="Spanish",
    pupil_first_language_spoken=True,
    pupil_first_language_read=True,
    pupil_first_language_written=False,
    pupil_other_language="French",
    pupil_other_language_spoken=False,
    pupil_other_language_read=False,
    pupil_other_language_written=False,
    home_main_language="English",
    home_main_language_spoken=True,
    home_main_language_read=True,
    home_main_language_written=True,
    home_other_language="German",
    home_other_language_spoken=False,
    home_other_language_read=False,
    home_other_language_written=False,
    declaration_name="John Smith",
    declaration_date="2023-08-13",
    additional_comments="Additional comments go here."
)
)   
    
    admins = [
        Admins(username = "admin", password = "admin", associatedUser = 1, associatedEmail = "admin@admin.com")
    ]
    db.session.add_all(admins)
    db.session.commit()
    
    users = [
        User("admin", 1),
        User("tutor", 1),
        User("student", 1),
        User("student", 2),
        User("student", 3),
        User("student", 4),
        User("tutor", 2),
    ]
    db.session.add_all(users)
    db.session.commit()
    
    
    lessons = [
        # Lesson(tutorID=1, subjectID=1, day='MON', startTime='08:00:00', endTime='15:00:00', centreID=1, lessonName='GCSE maths', AcademicYear = '2022-2023'),
        # Lesson(tutorID=2, subjectID=2, day='MON', startTime='08:00:00', endTime='15:00:00', centreID=2, lessonName='GCSE english', AcademicYear = '2022-2023'),
        # Lesson(tutorID=1, subjectID=1, day='TUE', startTime='08:00:00', endTime='16:00:00', centreID=2, lessonName='GCSE english', AcademicYear = '2022-2023'),
        # Lesson(tutorID=1, subjectID=1, day='WED', startTime='10:00:00', endTime='11:00:00', centreID=2, lessonName='GCSE physics', AcademicYear = '2022-2023'),
        # Lesson(tutorID=1, subjectID=1, day='THU', startTime='12:00:00', endTime='15:00:00', centreID=3, lessonName='GCSE maths', AcademicYear = '2022-2023'),
        # Lesson(tutorID=1, subjectID=1, day='FRI', startTime='20:00:00', endTime='16:00:00', centreID=1, lessonName='GCSE english', AcademicYear = '2022-2023'),
        # Lesson(tutorID=2, subjectID=1, day='SAT', startTime='16:00:00', endTime='11:00:00', centreID=1, lessonName='GCSE physics', AcademicYear = '2022-2023'),
        # Lesson(tutorID=1, subjectID=1, day='SUN', startTime='15:00:00', endTime='15:00:00', centreID=3, lessonName='GCSE maths', AcademicYear = '2022-2023'),
        # Lesson(tutorID=1, subjectID=1, day='WED', startTime='14:00:00', endTime='16:00:00', centreID=1, lessonName='GCSE english', AcademicYear = '2022-2023'),
        Lesson(tutorID=1, subjectID=1, day='MON', startTime='9:00:00', endTime='10:00:00', centreID=1, lessonName='GCSE physics', AcademicYear = '2023-2024')
    ]
    db.session.add_all(lessons)
    db.session.commit()

    lessonsinfo = [
        LessonInfo(lessonID=1, weekNo=35, register=True, homework=False, dismissed=False),
        LessonInfo(lessonID=1, weekNo=36, register=True, homework=False, dismissed=False),
    ]
    db.session.add_all(lessonsinfo)
    db.session.commit()
    
    
    student_lessons = [
        StudentLesson(studentID=2, lessonID=1),
        StudentLesson(studentID=1, lessonID=1)
    ]
    db.session.add_all(student_lessons)
    
    
    # Commit the changes to the database
    db.session.commit()