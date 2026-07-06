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
