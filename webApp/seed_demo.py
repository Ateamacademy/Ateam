"""
Demo-data seeder for the Ateam legacy Flask + SQLAlchemy app.

Fills the database with a RICH, REALISTIC, ENTIRELY FAKE dataset (no real
people) so every page of the app looks populated. Safe to run on every boot:
it is idempotent (skips if students already exist) and resilient (each logical
section is wrapped in try/except and rolls back only the failing section).

Usage (the caller provides the Flask app context):

    with app.app_context():
        db.create_all()
        from seed_demo import seed_demo
        seed_demo()

Notes on the schema (learned from Schema.py / db_init):
  * A "tutor" in this app is a Staff row with role="tutor".  Lessons,
    LessonInfo, TutorSubject all FK their tutorID -> staff.id.  A separate
    Tutors table holds extra HR detail; we create matching rows there too.
  * Login accounts live in the User table (role -> roles.name, otherID ->
    the id of the matching Staff/Students row).
  * Students() accepts every field as a keyword argument (see gen_Student).
  * Lesson() needs positional (tutorID, subjectID, day, startTime, endTime,
    centreID, lessonName, AcademicYear, weekNo, active); weekNo == -1 marks a
    permanent timetable lesson.
"""

import datetime

from werkzeug.security import generate_password_hash

from Schema import (
    db,
    Roles,
    User,
    Admins,
    Tutors,
    Staff,
    Students,
    Subject,
    Centre,
    Lesson,
    LessonInfo,
    StudentLesson,
    StudentAttendance,
    Tests,
    Grades,
    TutorSubject,
    Alerts,
    UserAlerts,
    Messages,
    Events,
    RoleEvent,
    gen_schema_week_no,
)

# Models used only by seed_extras(). Imported separately so the core seeder's
# import list stays exactly as it was.
from Schema import (
    lessonPlan,
    Files,
    Feedback,
    Document,
    individualDocument,
    Exams,
    ExamPapers,
    studentExam,
    exam_student,
    UserEvents,
    BookableEvent,
    Booking,
    staffHours,
    UCASReference,
    Product,
    gameQuestions,
    GameScores,
    ExamRoom,
    RoomArrangements,
    SeatingArrangement,
    SeedFlag,
    Enquiry,
    MailingList,
    PointSystem,
    StaffReviews,
    StaffStrikes,
    LittleAlerts,
)


# --------------------------------------------------------------------------- #
# Static demo content (all fake)                                              #
# --------------------------------------------------------------------------- #

DEMO_PASSWORD = "Demo1234"  # plain-text; hashed before storage

# Roles that grant broad *view* permissions so demo pages aren't blank.
VIEW_PERMISSIONS = [
    "view_all_lessons",
    "view_lessons_at_centre",
    "view_all_tutor_information",
    "view_all_student_information",
    "view_all_logs",
    "view_centre_logs",
    "view_staff",
    "view_staff_info",
    "view_enquiries",
]

FIRST_NAMES = [
    "Olivia", "Amelia", "Isla", "Ava", "Freya", "Grace", "Sophie", "Mia",
    "Ella", "Charlotte", "Poppy", "Evie", "Ruby", "Chloe", "Daisy", "Maryam",
    "Oliver", "George", "Harry", "Noah", "Jack", "Leo", "Arthur", "Muhammad",
    "Oscar", "Archie", "Henry", "Theo", "Freddie", "Finlay", "Ethan", "Jacob",
    "Reuben", "Zain", "Ayaan", "Dylan", "Callum", "Nathan",
]

LAST_NAMES = [
    "Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson",
    "Davies", "Patel", "Robinson", "Wright", "Thompson", "Evans", "Walker",
    "White", "Roberts", "Green", "Hall", "Wood", "Khan", "Clarke", "Jackson",
    "Wood", "Harris", "Cooper", "Ward", "Morris", "Begum", "Hussain", "Ahmed",
    "Baker", "Turner", "Hill", "Cole", "Shah", "Owusu",
]

ETHNIC_ORIGINS = [
    "White British", "Asian British", "Black British", "Mixed Heritage",
    "Other",
]

TUTORS = [
    # (firstName, secondName, subject titles they teach, gender)
    ("Rebecca", "Fielding", ["Maths"], "Female"),
    ("Daniel", "Okafor", ["Physics"], "Male"),
    ("Priya", "Nair", ["Chemistry", "Biology"], "Female"),
    ("James", "Whitfield", ["English"], "Male"),
    ("Aisha", "Rahman", ["Economics"], "Female"),
    ("Thomas", "Bright", ["Geography", "History"], "Male"),
    ("Sofia", "Marchetti", ["Computer Science"], "Female"),
    ("Nathaniel", "Osei", ["Maths", "Physics"], "Male"),
]

# (tier, title, examBoard)
SUBJECTS = [
    ("GCSE", "Maths", "Edexcel"),
    ("GCSE", "English", "AQA"),
    ("GCSE", "Biology", "AQA"),
    ("GCSE", "Chemistry", "AQA"),
    ("GCSE", "Physics", "AQA"),
    ("GCSE", "Geography", "OCR"),
    ("A-Level", "Maths", "Edexcel"),
    ("A-Level", "Biology", "AQA"),
    ("A-Level", "Economics", "Edexcel"),
    ("A-Level", "Computer Science", "OCR"),
]

CENTRES = [
    ("Soho Centre", 40, "12 Frith Street, London W1D 4RQ"),
    ("Ilford Centre", 30, "88 High Road, Ilford IG1 1DE"),
]

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]

# grade bands used to derive a letter grade from a percentage
def _letter_grade(pct, is_alevel):
    if is_alevel:
        for cutoff, letter in [(80, "A*"), (70, "A"), (60, "B"),
                               (50, "C"), (40, "D"), (0, "E")]:
            if pct >= cutoff:
                return letter
        return "U"
    # GCSE 9-1
    for cutoff, letter in [(90, "9"), (80, "8"), (70, "7"), (60, "6"),
                           (50, "5"), (40, "4"), (30, "3"), (20, "2"), (0, "1")]:
        if pct >= cutoff:
            return letter
    return "U"


def _academic_year():
    """Return the current UK academic year as 'YYYY-YYYY'."""
    today = datetime.date.today()
    start = today.year if today.month >= 9 else today.year - 1
    return f"{start}-{start + 1}"


def _det(seed, modulo):
    """Small deterministic pseudo-random helper (no `random` import needed)."""
    return (seed * 2654435761) % modulo


def seed_demo():
    """Populate the DB with fake demo data. Idempotent + resilient."""

    # ---------------------------------------------------------------- idempotency
    if Students.query.count() > 0:
        print("demo data already present, skipping")
        return

    academic_year = _academic_year()
    # pbkdf2:sha256 is portable across werkzeug/Python builds (some builds lack
    # hashlib.scrypt, which newer werkzeug defaults to).
    pw_hash = generate_password_hash(DEMO_PASSWORD, method="pbkdf2:sha256")
    logins_created = []  # (email, password, role)
    counts = {}

    # ------------------------------------------------------------------- roles
    try:
        role_defs = [("admin", 100), ("tutor", 50), ("student", 10),
                     ("parent", 5)]
        for name, level in role_defs:
            role = Roles.query.filter_by(name=name).first()
            if not role:
                role = Roles(name=name, level=level)
                db.session.add(role)
            # grant permissions
            if name == "admin":
                for col in role.__table__.columns:
                    if str(col.type) == "BOOLEAN":
                        setattr(role, col.name, True)
            else:
                for perm in VIEW_PERMISSIONS:
                    if hasattr(role, perm):
                        setattr(role, perm, True)
        db.session.commit()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[roles] section failed (continuing): {e}")

    # ------------------------------------------------------------ demo admin user
    # Some pages FK centres.admin_id -> user.id, so make sure a demo admin
    # exists to own the centres. bootstrap_local also makes admin@local; we add
    # a demo one only if there is no admin user at all.
    admin_user_id = 1
    try:
        existing_admin = User.query.filter_by(role="admin").first()
        if existing_admin:
            admin_user_id = existing_admin.id
        else:
            admin_staff = Staff(role="admin", firstName="Demo", middleName="",
                                secondName="Administrator", known_as="Demo Admin",
                                email="admin@demo.ateam", date_of_birth=None,
                                gender="Other")
            db.session.add(admin_staff)
            db.session.commit()
            admin_user = User(role="admin", otherID=admin_staff.id,
                              email="admin@demo.ateam", password=pw_hash)
            for col in admin_user.__table__.columns:
                if str(col.type) == "BOOLEAN":
                    setattr(admin_user, col.name, True)
            db.session.add(admin_user)
            db.session.commit()
            admin_user_id = admin_user.id
            logins_created.append(("admin@demo.ateam", DEMO_PASSWORD, "admin"))
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[admin user] section failed (continuing): {e}")

    # ----------------------------------------------------------------- centres
    centre_ids = []
    try:
        for name, capacity, address in CENTRES:
            centre = Centre(name=name, capacity=capacity, room_number=1,
                            address=address, admin_id=admin_user_id,
                            alias=name.split()[0],
                            email=f"{name.split()[0].lower()}@demo.ateam")
            db.session.add(centre)
            db.session.flush()
            centre_ids.append(centre.centreID)
        db.session.commit()
        counts["centres"] = Centre.query.count()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[centres] section failed (continuing): {e}")
        centre_ids = [c.centreID for c in Centre.query.all()]

    # ---------------------------------------------------------------- subjects
    subject_by_title = {}  # title -> subjectID (first match, any tier)
    subject_rows = []      # (subjectID, tier, title)
    try:
        for tier, title, board in SUBJECTS:
            subj = Subject(tier=tier, title=title, examBoard=board)
            db.session.add(subj)
            db.session.flush()
            subject_rows.append((subj.subjectID, tier, title))
            subject_by_title.setdefault(title, subj.subjectID)
        db.session.commit()
        counts["subjects"] = Subject.query.count()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[subjects] section failed (continuing): {e}")
        for s in Subject.query.all():
            subject_rows.append((s.subjectID, s.tier, s.title))
            subject_by_title.setdefault(s.title, s.subjectID)

    # ------------------------------------------------------------------ tutors
    # A tutor == a Staff row (role="tutor"). We also create a Tutors detail row
    # (matched by email, as convertTutorToStaffID expects) and one User login.
    tutor_staff_ids = []  # list of staff.id for lesson assignment
    tutor_login_email = None
    try:
        for i, (fn, sn, subj_titles, gender) in enumerate(TUTORS):
            email = f"{fn.lower()}.{sn.lower()}@demo.ateam"
            dob = datetime.date(1988 + (i % 8), 1 + (i % 12), 1 + (i % 27))

            staff = Staff(role="tutor", firstName=fn, middleName="",
                          secondName=sn, known_as=fn, email=email,
                          date_of_birth=dob, gender=gender,
                          work_email=email, nationality="British",
                          city_or_county="London",
                          phone=f"07700 9000{i:02d}")
            db.session.add(staff)
            db.session.flush()

            tutor_detail = Tutors(
                firstName=fn, middleName="", secondName=sn, known_as=fn,
                email=email, work_email=email, date_of_birth=dob,
                gender=gender, country_of_birth="United Kingdom",
                nationality="British", ethnic_origin="", mother_tongue="English",
                post_code="", house_number="", street_name="",
                city_or_county="London", borough_of_residence="",
                mode_of_travelling="", phone=f"07700 9000{i:02d}",
                password=pw_hash)
            db.session.add(tutor_detail)

            tutor_staff_ids.append(staff.id)

            # link tutor to the subjects they teach
            for t in subj_titles:
                sid = subject_by_title.get(t)
                if sid:
                    db.session.add(TutorSubject(staff.id, sid))

            # give the first tutor a login
            if i == 0:
                tutor_user = User(role="tutor", otherID=staff.id,
                                  email=email, password=pw_hash)
                for perm in VIEW_PERMISSIONS + ["upload_work_to_lesson",
                                                "change_lesson_plan"]:
                    if hasattr(tutor_user, perm):
                        setattr(tutor_user, perm, True)
                db.session.add(tutor_user)
                tutor_login_email = email
        db.session.commit()
        counts["tutors (staff)"] = Staff.query.filter_by(role="tutor").count()
        if tutor_login_email:
            logins_created.append((tutor_login_email, DEMO_PASSWORD, "tutor"))
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[tutors] section failed (continuing): {e}")
        tutor_staff_ids = [s.id for s in
                           Staff.query.filter_by(role="tutor").all()]

    # ---------------------------------------------------------------- students
    student_ids = []
    student_year_group = {}  # studentID -> int year group
    first_student_email = None
    first_parent_email = None
    try:
        for i in range(35):
            fn = FIRST_NAMES[i % len(FIRST_NAMES)]
            sn = LAST_NAMES[(i * 7 + 3) % len(LAST_NAMES)]
            year = 7 + (i % 7)  # Year 7..13
            # plausible DOB for that year group (school year age)
            birth_year = datetime.date.today().year - (year + 4)
            dob = datetime.date(birth_year, 1 + (i % 12), 1 + (i % 27))
            email = f"{fn.lower()}.{sn.lower()}{i}@demo-student.ateam"
            parent_email = f"parent.{sn.lower()}{i}@demo-parent.ateam"
            gender = "Female" if i % 2 == 0 else "Male"

            student = Students(
                firstName=fn, middleName="", secondName=sn,
                username=f"{fn.lower()}{i}"[:10], password=pw_hash,
                email=email, parent_email=parent_email, gender=gender,
                date_of_birth=dob, country_of_birth="United Kingdom",
                known_as=fn, nationality="British",
                year_group=str(year), ethnic_origin=ETHNIC_ORIGINS[i % 5],
                mother_tongue="English", date_of_entry_uk=None,
                post_code="E1 6AN", house_number=str(1 + i),
                street_name="Sample Road", city_or_county="London",
                borough_of_residence="Tower Hamlets", mode_of_travelling="Bus",
                current_school_1="Demo Secondary School",
                current_school_1_date_from=None,
                school_2="", school_2_date_from=None, school_2_date_until=None,
                school_3="", school_3_date_from=None, school_3_date_until=None,
                school_4="", school_4_date_from=None, school_4_date_until=None,
                sibling_1_forename="", sibling_1_surname="",
                sibling_1_date_of_birth=None, sibling_1_gender="",
                sibling_1_year_group="", sibling_1_id=None,
                sibling_2_forename="", sibling_2_surname="",
                sibling_2_date_of_birth=None, sibling_2_gender="",
                sibling_2_year_group="", sibling_2_id=None,
                sibling_3_forename="", sibling_3_surname="",
                sibling_3_date_of_birth=None, sibling_3_gender="",
                sibling_3_year_group="", sibling_3_id=None,
                sibling_4_forename="", sibling_4_surname="",
                sibling_4_date_of_birth=None, sibling_4_gender="",
                sibling_4_year_group="", sibling_4_id=None,
                previous_name="", legal_name=f"{fn} {sn}",
                child_protection_register=False, home_local_authority="",
                look_after_child_contact_info="",
                look_after_child_register=False, carer_name="",
                personal_education_plan=False, pep_contact_number="",
                armed_service_parent_name="", armed_service_parent_service="",
                armed_service_parent_rank="",
                armed_service_parent_additional_info="",
                gp_name="Demo Medical Practice", gp_post_code="E1 6AN",
                gp_telephone="020 7000 0000",
                gp_practice_address="1 Health Street, London",
                child_normally_healthy=True, serious_illness_or_accidents="None",
                condition_affecting_school_life="None", allergies=False,
                allergyInfo="None", asthma=False, epilepsy_or_fits=False,
                heart_problems=False, nose_bleeds=False,
                speech_or_hearing_difficulties=False,
                mobility_difficulties=False, other_difficulties="None",
                known_medical_conditions="None",
                medical_treatment_or_medicines="None", extra_medical_info="None",
                emergency_information="Contact parent/guardian",
                first_aid_permission=True, hospital_referral_permission=True,
                special_educational_needs=False, sen_information="None",
                behavior_support_needed=False, behavior_support_info="None",
                priority_contact_1_title="Mrs" if gender == "Female" else "Mr",
                priority_contact_1_relationship="Parent",
                priority_contact_1_parental_responsibility=True,
                priority_contact_1_forename="Sam", priority_contact_1_surname=sn,
                priority_contact_1_post_code="E1 6AN",
                priority_contact_1_home_telephone="020 7000 0001",
                priority_contact_1_email=parent_email,
                priority_contact_1_mobile_telephone=f"07800 100{i:03d}",
                priority_contact_1_employer="", priority_contact_1_work_number="",
                priority_contact_1_other_info_numbers="",
                priority_contact_2_title="", priority_contact_2_relationship="",
                priority_contact_2_parental_responsibility=False,
                priority_contact_2_forename="", priority_contact_2_surname="",
                priority_contact_2_post_code="",
                priority_contact_2_home_telephone="",
                priority_contact_2_email="",
                priority_contact_2_mobile_telephone="",
                priority_contact_2_employer="",
                priority_contact_2_work_number="",
                priority_contact_2_other_info_numbers="",
                local_visits_permission=True, digital_media_consent=True,
                declaration_signed=True, eal=False,
                pupil_first_language="English",
                pupil_first_language_spoken=True, pupil_first_language_read=True,
                pupil_first_language_written=True, pupil_other_language="",
                pupil_other_language_spoken=False,
                pupil_other_language_read=False,
                pupil_other_language_written=False,
                home_main_language="English", home_main_language_spoken=True,
                home_main_language_read=True, home_main_language_written=True,
                home_other_language="", home_other_language_spoken=False,
                home_other_language_read=False,
                home_other_language_written=False,
                declaration_name=f"Parent of {fn} {sn}",
                declaration_date=datetime.date.today(),
                additional_comments="Demo student record.",
                exam_student=False, log_on=(i == 0), see_all_work=False)
            db.session.add(student)
            db.session.flush()
            student_ids.append(student.id)
            student_year_group[student.id] = year

            if i == 0:
                first_student_email = email
                first_parent_email = parent_email
        db.session.commit()
        counts["students"] = Students.query.count()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[students] section failed (continuing): {e}")
        student_ids = [s.id for s in Students.query.all()]
        for s in Students.query.all():
            try:
                student_year_group[s.id] = int(s.year_group)
            except (TypeError, ValueError):
                student_year_group[s.id] = 10

    # -------------------------------------------------- student & parent logins
    try:
        if first_student_email:
            first_student = Students.query.filter_by(
                email=first_student_email).first()
            if first_student and not User.query.filter_by(
                    email=first_student_email).first():
                su = User(role="student", otherID=first_student.id,
                          email=first_student_email, password=pw_hash)
                db.session.add(su)
                logins_created.append(
                    (first_student_email, DEMO_PASSWORD, "student"))
            # parent login points at the same student (otherID = student id)
            if first_parent_email and not User.query.filter_by(
                    email=first_parent_email).first():
                pu = User(role="parent", otherID=first_student.id,
                          email=first_parent_email, password=pw_hash)
                for perm in VIEW_PERMISSIONS:
                    if hasattr(pu, perm):
                        setattr(pu, perm, True)
                db.session.add(pu)
                logins_created.append(
                    (first_parent_email, DEMO_PASSWORD, "parent"))
        db.session.commit()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[student/parent logins] section failed (continuing): {e}")

    # ------------------------------------------------------------------ lessons
    # Weekly permanent timetable (weekNo = -1 == permanent). Spread across days.
    lesson_records = []  # (lessonID, subjectID, tutor_staff_id, year_group)
    try:
        if not tutor_staff_ids:
            raise RuntimeError("no tutors available for lessons")
        times = [("09:00", "10:30"), ("10:45", "12:15"), ("13:00", "14:30"),
                 ("15:00", "16:30"), ("17:00", "18:30")]
        n_lessons = 18
        for i in range(n_lessons):
            sid, tier, title = subject_rows[i % len(subject_rows)]
            tutor_id = tutor_staff_ids[i % len(tutor_staff_ids)]
            day = DAYS[i % len(DAYS)]
            start_s, end_s = times[i % len(times)]
            centre_id = centre_ids[i % len(centre_ids)] if centre_ids else 1
            # year group: A-Level -> 12/13, GCSE -> 9/10/11
            if tier.upper().startswith("A"):
                year = 12 + (i % 2)
            else:
                year = 9 + (i % 3)
            lesson_name = f"{tier} {title} (Year {year})"
            start_t = datetime.datetime.strptime(start_s, "%H:%M").time()
            end_t = datetime.datetime.strptime(end_s, "%H:%M").time()
            lesson = Lesson(tutor_id, sid, day, start_t, end_t, centre_id,
                            lesson_name, academic_year, -1, True)
            db.session.add(lesson)
            db.session.flush()
            lesson_records.append((lesson.lessonID, sid, tutor_id, year))
        db.session.commit()
        counts["lessons"] = Lesson.query.count()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[lessons] section failed (continuing): {e}")
        for l in Lesson.query.all():
            lesson_records.append((l.lessonID, l.subjectID, l.tutorID, 10))

    # ---------------------------------------------------------- lesson info rows
    # A couple of weekly registers per lesson for recent weeks so approval /
    # register pages have content.
    current_week = int(gen_schema_week_no(0))
    recent_weeks = [w for w in (current_week - 2, current_week - 1,
                                current_week) if w >= 1]
    try:
        for lesson_id, sid, tutor_id, year in lesson_records:
            for wk in recent_weeks:
                info = LessonInfo(lessonID=lesson_id, weekNo=wk,
                                  tutorID=tutor_id, register=True,
                                  homework=(wk % 2 == 0), dismissed=False,
                                  description="Weekly session covered the "
                                              "planned topics.")
                info.approved = True
                db.session.add(info)
        db.session.commit()
        counts["lesson_info"] = LessonInfo.query.count()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[lesson_info] section failed (continuing): {e}")

    # -------------------------------------------------------- student enrolments
    # Each student joins 2-4 lessons, preferring lessons near their year group.
    enrolments = {}  # studentID -> [lessonID, ...]
    try:
        if not lesson_records:
            raise RuntimeError("no lessons available for enrolment")
        for idx, sid_student in enumerate(student_ids):
            yr = student_year_group.get(sid_student, 10)
            # candidate lessons: same-ish year group first
            candidates = [lr for lr in lesson_records if abs(lr[3] - yr) <= 1]
            if len(candidates) < 4:
                candidates = lesson_records
            n = 2 + _det(idx + 1, 3)  # 2..4 lessons
            chosen = []
            for k in range(n):
                lr = candidates[(idx + k * 3 + 1) % len(candidates)]
                if lr[0] not in chosen:
                    chosen.append(lr[0])
            for lesson_id in chosen:
                db.session.add(StudentLesson(studentID=sid_student,
                                             lessonID=lesson_id))
            enrolments[sid_student] = chosen
        db.session.commit()
        counts["student_lessons"] = StudentLesson.query.count()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[enrolments] section failed (continuing): {e}")
        enrolments = {}
        for sl in StudentLesson.query.all():
            enrolments.setdefault(sl.studentID, []).append(sl.lessonID)

    # ---------------------------------------------------------------- attendance
    # Attendance rows for the recent weeks, mostly present, some late/absent.
    try:
        n_rows = 0
        for sid_student, lesson_ids in enrolments.items():
            for lesson_id in lesson_ids:
                for w_i, wk in enumerate(recent_weeks):
                    r = _det(sid_student * 31 + lesson_id * 7 + wk, 10)
                    if r == 0:
                        present, notes = False, "Absent - notified by parent"
                    elif r == 1:
                        present, notes = True, "Arrived 10 minutes late"
                    else:
                        present, notes = True, ""
                    db.session.add(StudentAttendance(
                        lessonID=lesson_id, weekNo=wk,
                        AcademicYear=academic_year, studentID=sid_student,
                        present=present, extra_notes=notes))
                    n_rows += 1
        db.session.commit()
        counts["attendance"] = StudentAttendance.query.count()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[attendance] section failed (continuing): {e}")

    # ------------------------------------------------------------ tests + grades
    # One test per lesson for a recent week; a grade per enrolled student.
    try:
        # map lessonID -> subject tier for grade letters
        lesson_tier = {}
        for lesson_id, sid, tutor_id, year in lesson_records:
            subj = Subject.query.filter_by(subjectID=sid).first()
            lesson_tier[lesson_id] = (subj.tier if subj else "GCSE",
                                      subj.title if subj else "")
        test_week = recent_weeks[-1] if recent_weeks else current_week
        test_date = datetime.date.today() - datetime.timedelta(days=5)
        n_tests = 0
        n_grades = 0
        for lesson_id, sid, tutor_id, year in lesson_records:
            tier, title = lesson_tier.get(lesson_id, ("GCSE", ""))
            total = 50
            test = Tests(lessonID=lesson_id, weekNo=test_week, date=test_date,
                         total=total, filename="",
                         name=f"{title} Progress Test")
            db.session.add(test)
            db.session.flush()
            n_tests += 1
            is_al = tier.upper().startswith("A")
            # grade every enrolled student in this lesson
            enrolled = [s for s, lids in enrolments.items()
                        if lesson_id in lids]
            for s_id in enrolled:
                mark = 22 + _det(s_id * 13 + lesson_id, 27)  # 22..48 / 50
                pct = round(mark / total * 100)
                grade = _letter_grade(pct, is_al)
                student = Students.query.filter_by(id=s_id).first()
                name = (f"{student.firstName} {student.secondName}"
                        if student else "")
                db.session.add(Grades(testID=test.testID, studentID=s_id,
                                      studentName=name, mark=mark, grade=grade))
                n_grades += 1
        db.session.commit()
        counts["tests"] = Tests.query.count()
        counts["grades"] = Grades.query.count()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[tests/grades] section failed (continuing): {e}")

    # ----------------------------------------------------- alerts (optional)
    try:
        alerts = [
            ("student", "Welcome to the new term!",
             "Timetables are now live. Check your lessons page."),
            ("tutor", "Register reminder",
             "Please submit weekly registers by Friday evening."),
            ("parent", "Parents' evening",
             "Bookings for parents' evening open next week."),
        ]
        for role, title, message in alerts:
            alert = Alerts(message=message, role=role, title=title)
            db.session.add(alert)
            db.session.flush()
            for u in User.query.filter_by(role=role).all():
                db.session.add(UserAlerts(alertID=alert.alertID, userID=u.id))
        db.session.commit()
        counts["alerts"] = Alerts.query.count()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[alerts] section failed (continuing): {e}")

    # -------------------------------------------------- messages (optional)
    try:
        n_msgs = 0
        tutor_user = User.query.filter_by(role="tutor").first()
        student_user = User.query.filter_by(role="student").first()
        if lesson_records and tutor_user:
            lesson_id = lesson_records[0][0]
            now = datetime.datetime.utcnow()
            m1 = Messages(lessonID=lesson_id, userID=tutor_user.id,
                          time=now - datetime.timedelta(hours=2),
                          message="Reminder: homework is due next lesson.",
                          replyTo=-1, deleted=False)
            db.session.add(m1)
            db.session.flush()
            n_msgs += 1
            if student_user:
                m2 = Messages(lessonID=lesson_id, userID=student_user.id,
                              time=now - datetime.timedelta(hours=1),
                              message="Thanks, I'll have it ready!",
                              replyTo=m1.messageID, deleted=False)
                db.session.add(m2)
                n_msgs += 1
        db.session.commit()
        counts["messages"] = Messages.query.count()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[messages] section failed (continuing): {e}")

    # -------------------------------------------------- events (optional)
    try:
        today = datetime.date.today()
        events = [
            (today + datetime.timedelta(days=7), "Mock Exams Week",
             "GCSE and A-Level mock exams across both centres.", "student"),
            (today + datetime.timedelta(days=14), "Parents' Evening",
             "Meet the tutors at the Soho Centre.", "parent"),
            (today + datetime.timedelta(days=21), "Staff Training Day",
             "Whole-team CPD session. No lessons.", "tutor"),
        ]
        for date, title, desc, role in events:
            ev = Events(date=date, title=title, description=desc)
            db.session.add(ev)
            db.session.flush()
            db.session.add(RoleEvent(role, ev.id))
        db.session.commit()
        counts["events"] = Events.query.count()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[events] section failed (continuing): {e}")

    # -------------------------------------------------------------------- summary
    print("\n=== demo data seeded ===")
    for key in ["centres", "subjects", "tutors (staff)", "students",
                "lessons", "lesson_info", "student_lessons", "attendance",
                "tests", "grades", "alerts", "messages", "events"]:
        if key in counts:
            print(f"  {key:16}: {counts[key]}")

    print("\n=== demo logins ===")
    if logins_created:
        for email, pw, role in logins_created:
            print(f"  [{role:7}] {email}  /  {pw}")
    else:
        print("  (no new logins created)")
    print()


# --------------------------------------------------------------------------- #
# seed_extras(): top up all the OTHER page-backing areas.                      #
#                                                                              #
# Unlike seed_demo() this is NOT globally guarded. Each area is its own        #
# try/except section that:                                                     #
#   * checks whether ITS OWN table already has rows and skips if so            #
#     (so it can top up a DB that has the core data but none of the extras);   #
#   * FETCHES its dependencies from the database (never assumes in-memory      #
#     objects, because on the live server seed_demo() will have been skipped   #
#     and only the DB rows exist);                                             #
#   * rolls back only itself on failure and keeps going.                       #
#                                                                              #
# The caller wires this into startup; seed_demo() is left untouched.           #
# --------------------------------------------------------------------------- #

def _weeks_in_play():
    """Weeks the classroom pages care about: the permanent marker (-1) and a
    small window around the current schema week."""
    try:
        current = int(gen_schema_week_no(0))
    except Exception:  # noqa: BLE001
        current = 1
    weeks = {-1, current}
    for w in (current - 2, current - 1, current + 1):
        if w >= 1:
            weeks.add(w)
    return sorted(weeks)


def seed_extras():
    """Top up every remaining page-backing area with fake demo data.

    Safe to run on every boot: each section is independently idempotent and
    self-contained. Returns nothing; prints per-section progress + a summary.
    """
    counts = {}          # area -> row count after seeding
    skipped = []         # areas skipped because already populated

    weeks = _weeks_in_play()
    try:
        current_week = int(gen_schema_week_no(0))
    except Exception:  # noqa: BLE001
        current_week = 1
    academic_year = _academic_year()

    # ----------------------------------------------------------- lesson plans
    # A topic per Subject for every week in play (incl. weekNo == -1 and the
    # current week) so classroom / lesson-plan pages show topics.
    try:
        if lessonPlan.query.count() == 0:
            subjects = Subject.query.all()
            if not subjects:
                raise RuntimeError("no subjects available for lesson plans")
            topic_bank = [
                "Introduction & Key Concepts", "Core Skills Practice",
                "Exam Technique Workshop", "Consolidation & Review",
                "Applied Problem Solving", "Past Paper Walkthrough",
                "Foundations & Recap", "Extension & Challenge",
            ]
            added = 0
            for subj in subjects:
                for wk in weeks:
                    if lessonPlan.query.filter_by(
                            subjectID=subj.subjectID, weekNo=wk).first():
                        continue
                    idx = (subj.subjectID + (wk if wk > 0 else 0))
                    topic = topic_bank[idx % len(topic_bank)]
                    label = "Permanent" if wk == -1 else f"Week {wk}"
                    db.session.add(lessonPlan(
                        subj.subjectID, wk,
                        f"{subj.title}: {topic} ({label})"))
                    added += 1
            db.session.commit()
            counts["lesson_plans"] = lessonPlan.query.count()
            print(f"[lesson_plans] seeded {added} topic rows")
        else:
            skipped.append("lesson_plans")
            print("[lesson_plans] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[lesson_plans] section failed (continuing): {e}")

    # ----------------------------------------------------------------- files
    # Lesson files (lessonID set, subjectID None) + subject resources
    # (subjectID set, lessonID None, classtype scope). type is one of
    # starter/main/homework/notes; studentview controls student visibility.
    try:
        if Files.query.count() == 0:
            lessons = Lesson.query.all()
            subjects = Subject.query.all()
            if not lessons or not subjects:
                raise RuntimeError("no lessons/subjects available for files")
            added = 0
            # --- lesson-specific files: a starter / main / homework per lesson
            #     for the current week.
            file_kinds = [
                ("starter", "Starter_Questions", True),
                ("main", "Main_Worksheet", True),
                ("homework", "Homework_Sheet", True),
                ("notes", "Tutor_Notes", False),  # hidden from students
            ]
            for lesson in lessons:
                for ftype, stem, studentview in file_kinds:
                    fname = (f"{stem}_L{lesson.lessonID}"
                             f"_W{current_week}.pdf")
                    f = Files(lessonID=lesson.lessonID, weekNo=current_week,
                              filename=fname, type=ftype,
                              associatedTopic="Weekly topic",
                              subjectID=None, studentview=studentview,
                              classtype=None)
                    db.session.add(f)
                    added += 1
            # --- subject resources: a couple per subject, scope "all" so they
            #     show on both weekday and weekend lessons. Cover current week
            #     and the permanent (-1) week.
            for subj in subjects:
                for wk in (current_week, -1):
                    for ftype, stem in (("main", "Revision_Pack"),
                                        ("notes", "Reference_Notes")):
                        folder = (subj.tier.replace(" ", "-").upper() + "-"
                                  + subj.title.replace(" ", "-").upper())
                        fname = f"{stem}_{folder}_W{wk}.pdf"
                        f = Files(lessonID=None, weekNo=wk, filename=fname,
                                  type=ftype, associatedTopic="",
                                  subjectID=subj.subjectID, studentview=True,
                                  classtype="all")
                        db.session.add(f)
                        added += 1
            db.session.commit()
            counts["files"] = Files.query.count()
            print(f"[files] seeded {added} file rows")
        else:
            skipped.append("files")
            print("[files] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[files] section failed (continuing): {e}")

    # --------------------------------------------------------------- feedback
    # view_feedback reads every row; correct/student_good/tutor_good drive the
    # display. Keep content benign.
    try:
        if Feedback.query.count() == 0:
            students = Students.query.limit(6).all()
            if not students:
                raise RuntimeError("no students available for feedback")
            samples = [
                ("Excellent working shown throughout. Keep it up!", True,
                 True, None),
                ("Good effort - remember to check your units next time.",
                 True, None, True),
                ("A few slips in the algebra; review the worked example.",
                 False, None, None),
                ("Clear, well-structured answers. Strong exam technique.",
                 True, True, True),
                ("Homework not fully attempted - please complete section B.",
                 False, False, None),
                ("Great improvement since last week's assessment.",
                 True, None, None),
            ]
            added = 0
            for i, stu in enumerate(students):
                text, correct, student_good, tutor_good = samples[
                    i % len(samples)]
                fname = f"feedback/demo/{stu.id}_response_{i + 1}.pdf"
                fb = Feedback(filename=fname, studentID=stu.id,
                              feedback=text, correct=correct)
                fb.student_good = student_good
                fb.tutor_good = tutor_good
                db.session.add(fb)
                added += 1
            db.session.commit()
            counts["feedback"] = Feedback.query.count()
            print(f"[feedback] seeded {added} rows")
        else:
            skipped.append("feedback")
            print("[feedback] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[feedback] section failed (continuing): {e}")

    # -------------------------------------------------------------- documents
    # A few shared (individual=False) docs plus one per-user doc linked through
    # individualDocument.
    try:
        if Document.query.count() == 0:
            added = 0
            shared_docs = [
                ("Safeguarding Policy", False, False),
                ("Student Code of Conduct", False, False),
                ("Fire Evacuation Procedure", False, False),
                ("Parental Consent Form", False, True),  # requires signature
            ]
            for title, individual, sign in shared_docs:
                doc = Document(title=title,
                               data={"sections": [
                                   {"heading": title,
                                    "body": "This is demo content for the "
                                            f"'{title}' document."}]},
                               individual=individual, sign=sign)
                db.session.add(doc)
                added += 1
            db.session.flush()

            # one per-user document for the first few users
            users = User.query.limit(3).all()
            if users:
                indiv = Document(title="Individual Learning Plan",
                                 data={"sections": [
                                     {"heading": "Targets",
                                      "body": "Personalised targets (demo)."}]},
                                 individual=True, sign=True)
                db.session.add(indiv)
                db.session.flush()
                for u in users:
                    if not individualDocument.query.filter_by(
                            userID=u.id, docID=indiv.id).first():
                        db.session.add(individualDocument(userID=u.id,
                                                          docID=indiv.id))
                added += 1
            db.session.commit()
            counts["documents"] = Document.query.count()
            counts["individual_documents"] = individualDocument.query.count()
            print(f"[documents] seeded {added} documents "
                  f"(+{counts['individual_documents']} user links)")
        else:
            skipped.append("documents")
            print("[documents] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[documents] section failed (continuing): {e}")

    # ------------------------------------------------------------------ exams
    # A couple of exams (active, current academic year) with papers and some
    # student registrations, plus exam_student metadata rows.
    exam_ids = []
    try:
        if Exams.query.count() == 0:
            exam_defs = [
                ("GCSE", "Maths", "Edexcel", "1MA1", "Higher", "Summer"),
                ("A-Level", "Biology", "AQA", "7402", "", "Summer"),
            ]
            for tier, title, board, code, option, series in exam_defs:
                exam = Exams(tier=tier, title=title, examBoard=board,
                             code=code, Option=option, examSeries=series,
                             AcademicYear=academic_year)
                exam.active = True
                db.session.add(exam)
                db.session.flush()
                exam_ids.append(exam.examID)
            db.session.commit()
            counts["exams"] = Exams.query.count()
            print(f"[exams] seeded {len(exam_ids)} exams")
        else:
            skipped.append("exams")
            exam_ids = [e.examID for e in Exams.query.all()]
            print("[exams] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[exams] section failed (continuing): {e}")
        exam_ids = [e.examID for e in Exams.query.all()]

    # exam papers
    try:
        if ExamPapers.query.count() == 0 and exam_ids:
            base_date = datetime.date.today() + datetime.timedelta(days=30)
            added = 0
            for i, ex_id in enumerate(exam_ids):
                for paper_no in (1, 2):
                    p_date = base_date + datetime.timedelta(
                        days=i * 3 + paper_no)
                    paper = ExamPapers(
                        examID=ex_id, paperNo=paper_no,
                        paperCode=f"{ex_id}P{paper_no}",
                        duration=90, total=80, date=p_date,
                        extra_info="Calculator allowed" if paper_no == 2
                        else "Non-calculator",
                        startTime=datetime.time(9, 0))
                    db.session.add(paper)
                    added += 1
            db.session.commit()
            counts["exam_papers"] = ExamPapers.query.count()
            print(f"[exam_papers] seeded {added} papers")
        elif ExamPapers.query.count() > 0:
            skipped.append("exam_papers")
            print("[exam_papers] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[exam_papers] section failed (continuing): {e}")

    # studentExam registrations + exam_student metadata
    try:
        if studentExam.query.count() == 0 and exam_ids:
            students = Students.query.limit(12).all()
            added_reg = 0
            for i, stu in enumerate(students):
                ex_id = exam_ids[i % len(exam_ids)]
                if not studentExam.query.filter_by(
                        studentID=stu.id, examID=ex_id).first():
                    se = studentExam()
                    se.studentID = stu.id
                    se.examID = ex_id
                    db.session.add(se)
                    added_reg += 1
            db.session.commit()
            counts["student_exams"] = studentExam.query.count()
            print(f"[student_exams] seeded {added_reg} registrations")
        elif studentExam.query.count() > 0:
            skipped.append("student_exams")
            print("[student_exams] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[student_exams] section failed (continuing): {e}")

    try:
        if exam_student.query.count() == 0:
            # mark students as exam candidates with metadata, spread across centres
            students = Students.query.limit(12).all()
            centre_ids = [c.centreID for c in Centre.query.order_by(Centre.centreID).all()]
            real_access = ["25% extra time", "Separate room", "Reader / scribe"]
            added = 0
            for i, stu in enumerate(students):
                if exam_student.query.filter_by(studentID=stu.id).first():
                    continue
                es = exam_student()
                es.studentID = stu.id
                es.uci = f"UCI{stu.id:07d}"
                es.uln = f"{1000000000 + stu.id}"
                es.candidate_number = f"{1001 + i}"
                # ~1 in 4 candidates has an access arrangement; the rest are blank
                es.access_arrangements = (real_access[(i // 4) % len(real_access)]
                                          if i % 4 == 0 else "")
                es.centreID = centre_ids[i % len(centre_ids)] if centre_ids else None
                es.message = ""
                es.paid = (i % 2 == 0)
                es.paid_amount = 45 if i % 2 == 0 else 0
                es.reference_required = False
                es.approved = True
                es.active = True
                es.notes = "Demo exam candidate."
                db.session.add(es)
                # flag the student record too so get_exam_students() finds them
                stu.exam_student = True
                added += 1
            db.session.commit()
            counts["exam_student_meta"] = exam_student.query.count()
            print(f"[exam_student_meta] seeded {added} candidate rows")
        else:
            skipped.append("exam_student_meta")
            print("[exam_student_meta] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[exam_student_meta] section failed (continuing): {e}")

    # ------------------------------------------------------- forum messages
    # A few threads (replyTo == -1) with replies, tied to lessons. Content is
    # deliberately safe/benign. seed_demo() may have added the first thread on
    # lesson[0]; we top up further lessons so more forums are populated.
    try:
        lessons = Lesson.query.limit(4).all()
        tutor_user = User.query.filter_by(role="tutor").first()
        student_user = User.query.filter_by(role="student").first()
        if lessons and tutor_user:
            now = datetime.datetime.utcnow()
            added = 0
            for lesson in lessons:
                # skip lessons that already have any forum activity
                if Messages.query.filter_by(lessonID=lesson.lessonID).first():
                    continue
                root = Messages(
                    lessonID=lesson.lessonID, userID=tutor_user.id,
                    time=now - datetime.timedelta(hours=3),
                    message="Welcome to the class forum. Post any questions "
                            "about this week's work here.",
                    replyTo=-1, deleted=False)
                db.session.add(root)
                db.session.flush()
                added += 1
                if student_user:
                    reply = Messages(
                        lessonID=lesson.lessonID, userID=student_user.id,
                        time=now - datetime.timedelta(hours=2),
                        message="Thanks! Could you re-share the worksheet "
                                "from last lesson?",
                        replyTo=root.messageID, deleted=False)
                    db.session.add(reply)
                    db.session.flush()
                    added += 1
                    reply2 = Messages(
                        lessonID=lesson.lessonID, userID=tutor_user.id,
                        time=now - datetime.timedelta(hours=1),
                        message="Of course - it's now in the Files section.",
                        replyTo=root.messageID, deleted=False)
                    db.session.add(reply2)
                    added += 1
            db.session.commit()
            if added:
                counts["forum_messages"] = Messages.query.count()
                print(f"[forum_messages] seeded {added} messages")
            else:
                skipped.append("forum_messages")
                print("[forum_messages] already present, skipping")
        else:
            print("[forum_messages] no lessons/tutor available, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[forum_messages] section failed (continuing): {e}")

    # ------------------------------------------------ user / bookable events
    # Link some events to individual users (UserEvents). seed_demo() created
    # Events + RoleEvent already, so we only add the user-specific links here.
    try:
        if UserEvents.query.count() == 0:
            events = Events.query.all()
            users = User.query.limit(4).all()
            added = 0
            if events and users:
                for i, u in enumerate(users):
                    ev = events[i % len(events)]
                    if not UserEvents.query.filter_by(
                            userID=u.id, eventID=ev.id).first():
                        db.session.add(UserEvents(u.id, ev.id))
                        added += 1
            db.session.commit()
            if added:
                counts["user_events"] = UserEvents.query.count()
                print(f"[user_events] seeded {added} links")
            else:
                print("[user_events] no events/users available, skipping")
        else:
            skipped.append("user_events")
            print("[user_events] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[user_events] section failed (continuing): {e}")

    # bookable event + bookings
    try:
        if BookableEvent.query.count() == 0:
            ev_date = datetime.date.today() + datetime.timedelta(days=10)
            event = BookableEvent(
                name="Parents' Evening Consultations",
                date=ev_date, start_time=datetime.time(16, 0),
                end_time=datetime.time(19, 0), duration=15,
                location="Soho Centre - Main Hall",
                description="Book a 15-minute slot with your child's tutor.",
                bookable=True)
            db.session.add(event)
            db.session.flush()
            slots = [
                (datetime.time(16, 0), "Sam Taylor", "sam.taylor@demo-parent.ateam"),
                (datetime.time(16, 15), "Alex Patel", "alex.patel@demo-parent.ateam"),
                (datetime.time(16, 30), "Jordan Khan", "jordan.khan@demo-parent.ateam"),
            ]
            for i, (t, name, email) in enumerate(slots):
                db.session.add(Booking(
                    event_id=event.id, start_time=t, name=name, email=email,
                    phone=f"07700 900{100 + i}"))
            db.session.commit()
            counts["bookable_events"] = BookableEvent.query.count()
            counts["bookings"] = Booking.query.count()
            print(f"[bookable_events] seeded 1 event + "
                  f"{counts['bookings']} bookings")
        else:
            skipped.append("bookable_events")
            print("[bookable_events] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[bookable_events] section failed (continuing): {e}")

    # ------------------------------------------------------------ staff hours
    # Manual "other hours" entries: a mix of approved and pending (approved is
    # False/None for pending -> shown on approve-hours page). NOTE: the schema
    # has no real `rejected` column (it is mis-declared), so we never set it.
    try:
        if staffHours.query.count() == 0:
            tutors = Staff.query.filter_by(role="tutor").all()
            if not tutors:
                raise RuntimeError("no tutors available for staff hours")
            descriptions = [
                "Marking mock exam papers", "Resource preparation",
                "Parent phone calls", "Department meeting",
                "1:1 catch-up session", "Report writing",
            ]
            added = 0
            for i, tutor in enumerate(tutors):
                for j in range(2):  # one approved, one pending per tutor
                    entry = staffHours(
                        staffID=tutor.id,
                        date=datetime.date.today()
                        - datetime.timedelta(days=(i + j + 1) * 2),
                        hours=1.5 + (j * 0.5),
                        description=descriptions[(i + j) % len(descriptions)],
                        approved=(j == 0))
                    db.session.add(entry)
                    added += 1
            db.session.commit()
            counts["staff_hours"] = staffHours.query.count()
            print(f"[staff_hours] seeded {added} entries "
                  "(half approved, half pending)")
        else:
            skipped.append("staff_hours")
            print("[staff_hours] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[staff_hours] section failed (continuing): {e}")

    # ------------------------------------------------------- UCAS references
    try:
        if UCASReference.query.count() == 0:
            refs = [
                ("Aisha Begum", "Biology, Chemistry, Maths", "Medicine",
                 "AAA predicted at A-Level",
                 "Two weeks shadowing at a local GP practice",
                 "A long-standing passion for the biological sciences and a "
                 "desire to help others.",
                 "Netball captain; volunteers at a care home."),
                ("Daniel Osei", "Maths, Physics, Computer Science",
                 "Computer Science",
                 "A*AA predicted at A-Level",
                 "Summer coding internship at a fintech startup",
                 "Fascinated by algorithms and building software that "
                 "solves real problems.",
                 "Runs the school coding club; competitive chess player."),
                ("Freya Wilson", "English, History, Geography", "Law",
                 "AAB predicted at A-Level",
                 "Work experience at a local solicitors' office",
                 "Enjoys constructing arguments and a strong sense of "
                 "justice drew me to law.",
                 "Debating society; Duke of Edinburgh Gold Award."),
            ]
            added = 0
            for name, subjects, course, quals, work, reason, hobbies in refs:
                ref = UCASReference(
                    name=name, subjects=subjects, course=course,
                    qualifications=quals, work_experience=work,
                    reason=reason, hobbies=hobbies,
                    extra_info="Reference drafted by tutor (demo).",
                    completed_reference="")
                db.session.add(ref)
                added += 1
            db.session.commit()
            counts["ucas_references"] = UCASReference.query.count()
            print(f"[ucas_references] seeded {added} references")
        else:
            skipped.append("ucas_references")
            print("[ucas_references] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[ucas_references] section failed (continuing): {e}")

    # ---------------------------------------------------------- marketplace
    try:
        if Product.query.count() == 0:
            products = [
                ("£10 Amazon Voucher", 500,
                 "Redeem your points for a gift voucher.", False),
                ("A-Team Hoodie", 800,
                 "Branded hoodie in your choice of size.", False),
                ("Revision Guide Bundle", 300,
                 "Set of subject revision guides.", True),
                ("Cinema Tickets (x2)", 650,
                 "Two tickets to a cinema of your choice.", False),
                ("Premium Stationery Set", 200,
                 "Notebooks, pens and highlighters.", False),
            ]
            added = 0
            for name, reward, desc, sold in products:
                p = Product(name=name, reward=reward, description=desc)
                p.sold = sold
                p.completed = False
                p.approved = True
                db.session.add(p)
                added += 1
            db.session.commit()
            counts["products"] = Product.query.count()
            print(f"[products] seeded {added} products")
        else:
            skipped.append("products")
            print("[products] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[products] section failed (continuing): {e}")

    # ----------------------------------------------- game questions + scores
    try:
        if gameQuestions.query.count() == 0:
            questions = [
                ("What is 7 x 8?", "56", "54", "48", "64"),
                ("What is the chemical symbol for water?",
                 "H2O", "CO2", "O2", "HO"),
                ("What is the capital of France?",
                 "Paris", "London", "Rome", "Madrid"),
                ("What is 15% of 200?", "30", "25", "35", "20"),
                ("Which planet is closest to the Sun?",
                 "Mercury", "Venus", "Earth", "Mars"),
            ]
            added = 0
            for q, correct, a2, a3, a4 in questions:
                gq = gameQuestions()
                gq.question = q
                gq.correctAnswer = correct
                gq.answer2 = a2
                gq.answer3 = a3
                gq.answer4 = a4
                db.session.add(gq)
                added += 1
            db.session.commit()
            counts["game_questions"] = gameQuestions.query.count()
            print(f"[game_questions] seeded {added} questions")
        else:
            skipped.append("game_questions")
            print("[game_questions] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[game_questions] section failed (continuing): {e}")

    try:
        if GameScores.query.count() == 0:
            scores = [
                ("olivia.demo@demo-student.ateam", "Olivia S.", 950),
                ("george.demo@demo-student.ateam", "George J.", 870),
                ("amelia.demo@demo-student.ateam", "Amelia T.", 810),
                ("noah.demo@demo-student.ateam", "Noah B.", 760),
                ("isla.demo@demo-student.ateam", "Isla W.", 720),
            ]
            added = 0
            for email, name, score in scores:
                gs = GameScores()
                gs.email = email
                gs.name = name
                gs.score = score
                gs.image = None
                db.session.add(gs)
                added += 1
            db.session.commit()
            counts["game_scores"] = GameScores.query.count()
            print(f"[game_scores] seeded {added} leaderboard scores")
        else:
            skipped.append("game_scores")
            print("[game_scores] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[game_scores] section failed (continuing): {e}")

    # ------------------------------------------------ exam rooms + seating
    # Room, a dated arrangement for it, and a seating plan for the students
    # registered to the first exam on that date.
    try:
        if ExamRoom.query.count() == 0:
            rooms = [
                ("Main Hall", 8, 6),
                ("Room 12", 5, 4),
            ]
            for name, rows, cols in rooms:
                if not ExamRoom.query.filter_by(name=name).first():
                    db.session.add(ExamRoom(name, rows, cols))
            db.session.commit()
            counts["exam_rooms"] = ExamRoom.query.count()
            print(f"[exam_rooms] seeded {counts['exam_rooms']} rooms")
        else:
            skipped.append("exam_rooms")
            print("[exam_rooms] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[exam_rooms] section failed (continuing): {e}")

    # ---- exam venue migration (runs ONCE, marked by a SeedFlag) --------------
    # Exams are sat at dedicated venues (Cov Rd, Church), not at the demo
    # teaching centres (Soho/Ilford). One time only: create the venue centres,
    # move exam rooms/candidates off the demo teaching centres onto them, and
    # give each venue two rooms to plan with. The flag makes this a one-shot so
    # later hand-edits (renaming a centre, deleting a room) are never fought or
    # resurrected by a redeploy.
    try:
        _VENUE_FLAG = "venue_migration_v1"
        if SeedFlag.query.get(_VENUE_FLAG):
            raise StopIteration  # already migrated; skip the whole section

        VENUES = [("Cov Rd", "Coventry Road, Birmingham"),
                  ("Church", "Church Road, Birmingham")]
        # demo teaching centre (exact seeded name) -> exam venue
        DEMO_REMAP = {"Soho Centre": "Cov Rd", "Ilford Centre": "Church"}

        venue_ids = {}
        for vname, vaddr in VENUES:
            c = Centre.query.filter_by(name=vname).first()
            if not c:
                c = Centre(name=vname, capacity=60, room_number=1, address=vaddr)
                db.session.add(c)
                db.session.flush()
            venue_ids[vname] = c.centreID
        db.session.commit()
        venue_id_list = [venue_ids[vname] for vname, _ in VENUES]

        # Move exam rooms + candidates from the demo teaching centres to venues.
        # Only rows tagged to the exact seeded demo names are touched, so real
        # (hand-entered) centres are never remapped.
        moved = 0
        for old_name, new_name in DEMO_REMAP.items():
            old = Centre.query.filter_by(name=old_name).first()
            if not old:
                continue
            new_id = venue_ids[new_name]
            for room in ExamRoom.query.filter_by(centreID=old.centreID).all():
                room.centreID = new_id
                # auto-generated names carried the old centre name; follow it
                if room.name.startswith(old_name + " Room"):
                    renamed = room.name.replace(old_name, new_name, 1)
                    if not ExamRoom.query.filter_by(name=renamed).first():
                        room.name = renamed
                moved += 1
            for es in exam_student.query.filter_by(centreID=old.centreID).all():
                es.centreID = new_id
                moved += 1
        if moved:
            db.session.commit()

        # Untagged rooms/candidates get spread across the venues.
        fixed_rooms = 0
        for i, room in enumerate(ExamRoom.query.order_by(ExamRoom.id).all()):
            if getattr(room, "centreID", None) is None:
                room.centreID = venue_id_list[i % len(venue_id_list)]
                fixed_rooms += 1
        if fixed_rooms:
            db.session.commit()

        fixed_cands = 0
        for i, es in enumerate(exam_student.query.order_by(exam_student.studentID).all()):
            if getattr(es, "centreID", None) is None:
                es.centreID = venue_id_list[i % len(venue_id_list)]
                fixed_cands += 1
        if fixed_cands:
            db.session.commit()

        # Guarantee rooms only where candidates actually sit exams, so teaching
        # centres don't get phantom exam rooms recreated for them.
        cand_centre_ids = sorted({es.centreID for es in exam_student.query.all()
                                  if getattr(es, "centreID", None)})
        made_rooms = 0
        for cid in cand_centre_ids:
            cobj = Centre.query.filter_by(centreID=cid).first()
            cname = cobj.name if cobj else f"Centre {cid}"
            have = ExamRoom.query.filter_by(centreID=cid).count()
            n = have + 1
            while have < 2:
                rname = f"{cname} Room {n}"
                if not ExamRoom.query.filter_by(name=rname).first():
                    db.session.add(ExamRoom(rname, 5, 5, cid))
                    made_rooms += 1
                    have += 1
                n += 1
        if made_rooms:
            db.session.commit()

        # Mark done so this never runs again (hand-edits stay untouched forever).
        db.session.add(SeedFlag(_VENUE_FLAG))
        db.session.commit()
        print(f"[venue_migration] done: moved:{moved} rooms_tagged:{fixed_rooms} "
              f"rooms_created:{made_rooms} candidates_tagged:{fixed_cands}")
    except StopIteration:
        pass  # venue migration already ran once; nothing to do
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[venue_migration] section failed (continuing): {e}")

    # ---- demo clash (runs ONCE, marked by a SeedFlag) -------------------------
    # Register one candidate for both demo exams and overlap their first papers,
    # so the Exam Clashes page has something real to show. One-shot: once the
    # officer resolves it (moves a paper / drops an entry), it never comes back.
    try:
        _CLASH_FLAG = "clash_demo_v1"
        if not SeedFlag.query.get(_CLASH_FLAG):
            exams = Exams.query.order_by(Exams.examID).limit(2).all()
            if len(exams) == 2:
                paper_a = ExamPapers.query.filter_by(examID=exams[0].examID, paperNo=1).first()
                paper_b = ExamPapers.query.filter_by(examID=exams[1].examID, paperNo=1).first()
                reg_a = studentExam.query.filter_by(examID=exams[0].examID).first()
                if paper_a and paper_b and paper_a.date and paper_a.startTime and reg_a:
                    # second exam's paper starts an hour into the first one
                    paper_b.date = paper_a.date
                    paper_b.startTime = (datetime.datetime.combine(paper_a.date, paper_a.startTime)
                                         + datetime.timedelta(minutes=60)).time()
                    if not studentExam.query.filter_by(studentID=reg_a.studentID,
                                                       examID=exams[1].examID).first():
                        db.session.add(studentExam(studentID=reg_a.studentID,
                                                   examID=exams[1].examID))
                    print(f"[clash_demo] candidate {reg_a.studentID} now sits both exams "
                          f"on {paper_a.date} (overlapping)")
            db.session.add(SeedFlag(_CLASH_FLAG))
            db.session.commit()
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[clash_demo] section failed (continuing): {e}")

    try:
        if SeatingArrangement.query.count() == 0:
            room = ExamRoom.query.first()
            paper = ExamPapers.query.order_by(ExamPapers.date).first()
            if room and paper:
                seat_date = paper.date
                # room arrangement for that date (if not present)
                if not RoomArrangements.query.filter_by(
                        date=seat_date, room_id=room.id).first():
                    db.session.add(RoomArrangements(
                        date=seat_date, room_id=room.id,
                        actual_rows=room.max_rows,
                        actual_columns=room.max_columns))
                # seat the students registered to that exam
                regs = studentExam.query.filter_by(
                    examID=paper.examID).all()
                added = 0
                cols = room.max_columns
                for idx, reg in enumerate(regs):
                    row = idx // cols + 1
                    col = idx % cols + 1
                    if row > room.max_rows:
                        break
                    db.session.add(SeatingArrangement(
                        student_id=reg.studentID, exam_id=paper.examID,
                        room_id=room.id, row=row, column=col, date=seat_date))
                    added += 1
                db.session.commit()
                counts["seating_arrangements"] = SeatingArrangement.query.count()
                counts["room_arrangements"] = RoomArrangements.query.count()
                print(f"[seating] seeded {added} seats "
                      f"(+{counts['room_arrangements']} room arrangements)")
            else:
                print("[seating] no room/exam paper available, skipping")
        else:
            skipped.append("seating_arrangements")
            print("[seating] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[seating] section failed (continuing): {e}")

    # ------------------------------------------------- enquiries + mailing
    try:
        if Enquiry.query.count() == 0:
            centres = Centre.query.all()
            admin_user = User.query.filter_by(role="admin").first()
            if not centres or not admin_user:
                raise RuntimeError("no centres/admin available for enquiries")
            enquiries = [
                ("Sam Taylor", "Ella Taylor", "9", "Booked trial Lesson",
                 "Interested in GCSE Maths support on Saturdays."),
                ("Alex Patel", "Zara Patel", "12", "Will book a trial lesson",
                 "Looking for A-Level Biology tuition."),
                ("Jordan Khan", "Yusuf Khan", "10", "Pending",
                 "Asked about pricing for two subjects."),
                ("Chris Owusu", "Ama Owusu", "11", "Complete",
                 "Enrolled after a successful trial lesson."),
            ]
            added = 0
            for i, (caller, student, yr, result, info) in enumerate(enquiries):
                centre = centres[i % len(centres)]
                enq = Enquiry(
                    callerName=caller, studentName=student, year_group=yr,
                    location=centre.centreID,
                    parent_email=f"{caller.split()[0].lower()}@demo-parent.ateam",
                    contact_number=f"07700 900{200 + i}",
                    enquiry_info=info, result=result,
                    userID=admin_user.id, escalated=False)
                db.session.add(enq)
                added += 1
            db.session.commit()
            counts["enquiries"] = Enquiry.query.count()
            print(f"[enquiries] seeded {added} enquiries")
        else:
            skipped.append("enquiries")
            print("[enquiries] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[enquiries] section failed (continuing): {e}")

    try:
        if MailingList.query.count() == 0:
            emails = [
                "newsletter1@demo-parent.ateam",
                "newsletter2@demo-parent.ateam",
                "newsletter3@demo-parent.ateam",
                "prospective.parent@demo.ateam",
            ]
            for em in emails:
                ml = MailingList()
                ml.email = em
                db.session.add(ml)
            db.session.commit()
            counts["mailing_list"] = MailingList.query.count()
            print(f"[mailing_list] seeded {counts['mailing_list']} entries")
        else:
            skipped.append("mailing_list")
            print("[mailing_list] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[mailing_list] section failed (continuing): {e}")

    # -------------------------------------------- point system (staff perf)
    try:
        if PointSystem.query.count() == 0:
            point_defs = [
                ("Perfect attendance", 50),
                ("Homework completed", 20),
                ("Top of the class", 100),
                ("Helping a peer", 30),
                ("Excellent effort", 25),
            ]
            for reason, amount in point_defs:
                ps = PointSystem()
                ps.reason = reason
                ps.amount = amount
                db.session.add(ps)
            db.session.commit()
            counts["point_system"] = PointSystem.query.count()
            print(f"[point_system] seeded {counts['point_system']} rules")
        else:
            skipped.append("point_system")
            print("[point_system] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[point_system] section failed (continuing): {e}")

    # staff reviews
    try:
        if StaffReviews.query.count() == 0:
            tutors = Staff.query.filter_by(role="tutor").all()
            added = 0
            for i, tutor in enumerate(tutors[:5]):
                rev = StaffReviews()
                rev.staffID = tutor.id
                rev.date = datetime.date.today() - datetime.timedelta(
                    days=14 + i)
                rev.PunctualityScore = 8 + (i % 3)
                rev.PunctualityComments = "Reliably on time."
                rev.LessonQualityScore = 7 + (i % 4)
                rev.LessonQualityComments = "Well-planned, engaging lessons."
                rev.LessonPreparednessScore = 8 + (i % 2)
                rev.LessonPreparednessComments = "Materials ready in advance."
                rev.ProfessionalismScore = 9
                rev.ProfessionalismComments = "Professional with students and "
                rev.TestScoresAverage = 68.5 + i
                rev.TestScoresComments = "Class results above target."
                rev.extraComments = "A valued member of the team."
                db.session.add(rev)
                added += 1
            db.session.commit()
            counts["staff_reviews"] = StaffReviews.query.count()
            print(f"[staff_reviews] seeded {added} reviews")
        else:
            skipped.append("staff_reviews")
            print("[staff_reviews] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[staff_reviews] section failed (continuing): {e}")

    # staff strikes (a couple, tastefully minor)
    try:
        if StaffStrikes.query.count() == 0:
            tutors = Staff.query.filter_by(role="tutor").all()
            added = 0
            for i, tutor in enumerate(tutors[:2]):
                st = StaffStrikes()
                st.staffID = tutor.id
                st.date = datetime.date.today() - datetime.timedelta(
                    days=30 + i)
                st.description = ("Late submission of weekly register "
                                  "(demo record).")
                db.session.add(st)
                added += 1
            db.session.commit()
            counts["staff_strikes"] = StaffStrikes.query.count()
            print(f"[staff_strikes] seeded {added} strikes")
        else:
            skipped.append("staff_strikes")
            print("[staff_strikes] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[staff_strikes] section failed (continuing): {e}")

    # ------------------------------------------------------- tutor-subjects
    # Link each tutor to 1-3 subjects. seed_demo() links tutors during core
    # seeding; we only top up if the table is empty (fresh core-only DBs where
    # the tutor section may have partially run still get covered because we
    # skip-per-row below).
    try:
        if TutorSubject.query.count() == 0:
            tutors = Staff.query.filter_by(role="tutor").all()
            subjects = Subject.query.all()
            if not tutors or not subjects:
                raise RuntimeError("no tutors/subjects for tutor-subject link")
            added = 0
            for i, tutor in enumerate(tutors):
                n = 1 + (i % 3)  # 1..3 subjects
                for k in range(n):
                    subj = subjects[(i + k) % len(subjects)]
                    if not TutorSubject.query.filter_by(
                            tutorID=tutor.id,
                            subjectID=subj.subjectID).first():
                        db.session.add(TutorSubject(tutor.id, subj.subjectID))
                        added += 1
            db.session.commit()
            counts["tutor_subjects"] = TutorSubject.query.count()
            print(f"[tutor_subjects] seeded {added} links")
        else:
            skipped.append("tutor_subjects")
            print("[tutor_subjects] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[tutor_subjects] section failed (continuing): {e}")

    # --------------------------------------------------------- little alerts
    try:
        if LittleAlerts.query.count() == 0:
            users = User.query.limit(6).all()
            messages = [
                "You have a new grade available.",
                "Your timetable was updated.",
                "A new document needs your signature.",
                "Homework is due tomorrow.",
                "You earned points this week!",
            ]
            added = 0
            for i, u in enumerate(users):
                la = LittleAlerts()
                la.userID = u.id
                la.message = messages[i % len(messages)]
                la.viewed = (i % 3 == 0)
                db.session.add(la)
                added += 1
            db.session.commit()
            counts["little_alerts"] = LittleAlerts.query.count()
            print(f"[little_alerts] seeded {added} alerts")
        else:
            skipped.append("little_alerts")
            print("[little_alerts] already present, skipping")
    except Exception as e:  # noqa: BLE001
        db.session.rollback()
        print(f"[little_alerts] section failed (continuing): {e}")

    # -------------------------------------------------------------- summary
    print("\n=== seed_extras summary ===")
    if counts:
        for key in sorted(counts):
            print(f"  {key:22}: {counts[key]}")
    else:
        print("  (nothing new seeded)")
    if skipped:
        print("  skipped (already populated): " + ", ".join(sorted(skipped)))
    print()
