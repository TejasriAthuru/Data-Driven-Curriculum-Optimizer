import random
from datetime import date, timedelta

import mysql.connector
from dotenv import load_dotenv
import os
from pathlib import Path


# ---------------------------------------------------------
# 1. LOAD DATABASE SETTINGS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


# ---------------------------------------------------------
# 2. FIXED VALUES FOR REPRODUCIBLE DATA
# ---------------------------------------------------------

random.seed(42)


# ---------------------------------------------------------
# 3. MASTER DATA
# ---------------------------------------------------------

departments = [
    ("D01", "Computer Science and Engineering"),
    ("D02", "Artificial Intelligence and Data Science"),
    ("D03", "Electronics and Communication Engineering"),
]

faculty = [
    ("F001", "Anil Kumar", "anil.kumar@college.edu", "D01", "Assistant Professor"),
    ("F002", "Priya Sharma", "priya.sharma@college.edu", "D01", "Assistant Professor"),

    ("F003", "Rahul Reddy", "rahul.reddy@college.edu", "D02", "Assistant Professor"),
    ("F004", "Sneha Rao", "sneha.rao@college.edu", "D02", "Associate Professor"),

    ("F005", "Kiran Kumar", "kiran.kumar@college.edu", "D03", "Assistant Professor"),
    ("F006", "Meena Devi", "meena.devi@college.edu", "D03", "Associate Professor"),
]

courses = [
    ("CSE101", "Data Structures", 4.0, "D01", "F001", 5),
    ("CSE102", "Database Management Systems", 4.0, "D01", "F002", 5),
    ("CSE103", "Computer Networks", 3.0, "D01", "F001", 5),

    ("AID101", "Machine Learning", 4.0, "D02", "F003", 5),
    ("AID102", "Data Analytics", 4.0, "D02", "F004", 5),
    ("AID103", "Artificial Intelligence", 3.0, "D02", "F003", 5),

    ("ECE101", "Digital Electronics", 4.0, "D03", "F005", 5),
    ("ECE102", "Communication Systems", 4.0, "D03", "F006", 5),
    ("ECE103", "Microprocessors", 3.0, "D03", "F005", 5),
]


# ---------------------------------------------------------
# 4. STUDENTS
# ---------------------------------------------------------

students = []

student_ability = {}

for dept_code in ["D01", "D02", "D03"]:

    prefix = {
        "D01": "CSE",
        "D02": "AID",
        "D03": "ECE"
    }[dept_code]

    for i in range(1, 21):

        student_id = f"{prefix}{i:03d}"

        # Different students have different academic tendencies.
        ability = random.uniform(0.55, 0.95)

        student_ability[student_id] = ability

        gender = random.choice(["Female", "Male"])

        students.append(
            (
                student_id,
                f"Student {prefix}{i:03d}",
                gender,
                dept_code,
                5
            )
        )


# ---------------------------------------------------------
# 5. LEARNING OUTCOMES
# ---------------------------------------------------------

learning_outcomes = []

for course_id, course_name, credits, dept_id, faculty_id, semester in courses:

    lo1 = f"{course_id}_LO1"
    lo2 = f"{course_id}_LO2"

    learning_outcomes.append(
        (
            lo1,
            "LO1",
            f"Understand the fundamental concepts of {course_name}.",
            70.00
        )
    )

    learning_outcomes.append(
        (
            lo2,
            "LO2",
            f"Apply the concepts of {course_name} to solve academic problems.",
            70.00
        )
    )


# ---------------------------------------------------------
# 6. DATABASE CONNECTION
# ---------------------------------------------------------

connection = get_connection()
cursor = connection.cursor()

try:

    # -----------------------------------------------------
    # 7. INSERT DEPARTMENTS
    # -----------------------------------------------------

    cursor.executemany(
        """
        INSERT INTO department
        (department_id, department_name)
        VALUES (%s, %s)
        """,
        departments
    )


    # -----------------------------------------------------
    # 8. INSERT FACULTY
    # -----------------------------------------------------

    cursor.executemany(
        """
        INSERT INTO faculty
        (faculty_id, faculty_name, email, department_id, designation)
        VALUES (%s, %s, %s, %s, %s)
        """,
        faculty
    )


    # -----------------------------------------------------
    # 9. INSERT STUDENTS
    # -----------------------------------------------------

    cursor.executemany(
        """
        INSERT INTO student
        (student_id, student_name, gender, department_id, semester)
        VALUES (%s, %s, %s, %s, %s)
        """,
        students
    )


    # -----------------------------------------------------
    # 10. INSERT COURSES
    # -----------------------------------------------------

    cursor.executemany(
        """
        INSERT INTO course
        (course_id, course_name, credits, department_id, faculty_id, semester)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        courses
    )


    # -----------------------------------------------------
    # 11. INSERT LEARNING OUTCOMES
    # -----------------------------------------------------

    cursor.executemany(
        """
        INSERT INTO learning_outcome
        (lo_id, lo_code, lo_description, target_attainment)
        VALUES (%s, %s, %s, %s)
        """,
        learning_outcomes
    )


    # -----------------------------------------------------
    # 12. COURSE - LEARNING OUTCOME MAPPING
    # -----------------------------------------------------

    course_lo_mapping = []

    # Different courses get slightly different attainment
    # so that our analysis can identify variations.

    course_attainment = {
        "CSE101": (82, 78),
        "CSE102": (76, 72),
        "CSE103": (70, 68),

        "AID101": (84, 80),
        "AID102": (88, 84),
        "AID103": (75, 71),

        "ECE101": (79, 74),
        "ECE102": (73, 70),
        "ECE103": (68, 65),
    }

    for course_id, course_name, credits, dept_id, faculty_id, semester in courses:

        lo1_attainment, lo2_attainment = course_attainment[course_id]

        course_lo_mapping.append(
            (
                course_id,
                f"{course_id}_LO1",
                lo1_attainment
            )
        )

        course_lo_mapping.append(
            (
                course_id,
                f"{course_id}_LO2",
                lo2_attainment
            )
        )

    cursor.executemany(
        """
        INSERT INTO course_lo_mapping
        (course_id, lo_id, attainment_percentage)
        VALUES (%s, %s, %s)
        """,
        course_lo_mapping
    )


    # -----------------------------------------------------
    # 13. ENROLLMENT
    # -----------------------------------------------------

    enrollments = []

    department_students = {
        "D01": [s[0] for s in students if s[3] == "D01"],
        "D02": [s[0] for s in students if s[3] == "D02"],
        "D03": [s[0] for s in students if s[3] == "D03"],
    }

    department_courses = {
        "D01": ["CSE101", "CSE102", "CSE103"],
        "D02": ["AID101", "AID102", "AID103"],
        "D03": ["ECE101", "ECE102", "ECE103"],
    }

    for dept_id in department_students:

        for student_id in department_students[dept_id]:

            for course_id in department_courses[dept_id]:

                enrollments.append(
                    (
                        student_id,
                        course_id,
                        "2026-27",
                        5,
                        "Active"
                    )
                )

    cursor.executemany(
        """
        INSERT INTO enrollment
        (student_id, course_id, academic_year, semester, enrollment_status)
        VALUES (%s, %s, %s, %s, %s)
        """,
        enrollments
    )


    # -----------------------------------------------------
    # 14. ATTENDANCE
    # -----------------------------------------------------

    attendance_records = []

    for student_id, course_id, academic_year, semester, status in enrollments:

        ability = student_ability[student_id]

        # Attendance roughly follows student tendency.
        attendance_percentage = (
            55 + (ability * 40) + random.uniform(-5, 5)
        )

        attendance_percentage = max(
            50,
            min(98, attendance_percentage)
        )

        classes_conducted = 40

        classes_attended = round(
            classes_conducted * attendance_percentage / 100
        )

        actual_percentage = (
            classes_attended / classes_conducted
        ) * 100

        attendance_records.append(
            (
                student_id,
                course_id,
                classes_conducted,
                classes_attended,
                round(actual_percentage, 2)
            )
        )

    cursor.executemany(
        """
        INSERT INTO attendance
        (student_id, course_id, classes_conducted,
         classes_attended, attendance_percentage)
        VALUES (%s, %s, %s, %s, %s)
        """,
        attendance_records
    )


    # -----------------------------------------------------
    # 15. ASSESSMENTS
    # -----------------------------------------------------

    assessments = []

    assessment_types = [
        ("MID", "Midterm", 30),
        ("ASSIGN", "Assignment", 20),
        ("QUIZ", "Quiz", 10),
    ]

    for course_id, course_name, credits, dept_id, faculty_id, semester in courses:

        for code, assessment_name, max_marks in assessment_types:

            assessment_id = f"{course_id}_{code}"

            assessments.append(
                (
                    assessment_id,
                    course_id,
                    assessment_name,
                    assessment_name,
                    max_marks,
                    date(2026, 9, 1)
                )
            )

    cursor.executemany(
        """
        INSERT INTO assessment
        (assessment_id, course_id, assessment_type,
         assessment_name, max_marks, assessment_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        assessments
    )


    # -----------------------------------------------------
    # 16. ASSESSMENT RESULTS
    # -----------------------------------------------------

    assessment_results = []

    course_difficulty = {
        "CSE101": 0.00,
        "CSE102": -0.05,
        "CSE103": -0.08,

        "AID101": -0.03,
        "AID102": 0.04,
        "AID103": -0.04,

        "ECE101": -0.01,
        "ECE102": -0.06,
        "ECE103": -0.10,
    }

    assessment_effect = {
        "MID": -0.02,
        "ASSIGN": 0.04,
        "QUIZ": 0.01,
    }

    for assessment_id, course_id, assessment_type, assessment_name, max_marks, assessment_date in assessments:

        dept_id = next(
            c[3] for c in courses if c[0] == course_id
        )

        course_students = department_students[dept_id]

        for student_id in course_students:

            ability = student_ability[student_id]

            performance = (
                ability
                + course_difficulty[course_id]
                + assessment_effect[
                    next(
                        code
                        for code, name, marks in assessment_types
                        if name == assessment_name
                    )
                ]
                + random.uniform(-0.08, 0.08)
            )

            performance = max(0.35, min(0.98, performance))

            marks_obtained = round(
                max_marks * performance,
                2
            )

            percentage = round(
                (marks_obtained / max_marks) * 100,
                2
            )

            if percentage >= 85:
                grade = "A"
            elif percentage >= 70:
                grade = "B"
            elif percentage >= 55:
                grade = "C"
            elif percentage >= 40:
                grade = "D"
            else:
                grade = "F"

            assessment_results.append(
                (
                    assessment_id,
                    student_id,
                    marks_obtained,
                    percentage,
                    grade
                )
            )

    cursor.executemany(
        """
        INSERT INTO assessment_result
        (assessment_id, student_id, marks_obtained,
         percentage, grade)
        VALUES (%s, %s, %s, %s, %s)
        """,
        assessment_results
    )


    # -----------------------------------------------------
    # 17. FEEDBACK
    # -----------------------------------------------------

    feedback_records = []

    comments = [
        "Good course content",
        "Course was easy to understand",
        "More practical examples would help",
        "Useful for academic learning",
        "Assignments were helpful",
        "Some topics were difficult",
        "Good teaching and course structure",
    ]

    for student_id, course_id, academic_year, semester, status in enrollments:

        ability = student_ability[student_id]

        rating = 2.5 + (ability * 2.0) + random.uniform(-0.5, 0.5)

        rating = max(1.0, min(5.0, rating))

        feedback_records.append(
            (
                student_id,
                course_id,
                round(rating, 1),
                random.choice(comments),
                date(2026, 10, 1)
            )
        )

    cursor.executemany(
        """
        INSERT INTO feedback
        (student_id, course_id, rating, comments, feedback_date)
        VALUES (%s, %s, %s, %s, %s)
        """,
        feedback_records
    )


    # -----------------------------------------------------
    # 18. SAVE EVERYTHING
    # -----------------------------------------------------

    connection.commit()

    print("\n======================================")
    print("DATASET GENERATED SUCCESSFULLY")
    print("======================================")

    print(f"Departments       : {len(departments)}")
    print(f"Faculty           : {len(faculty)}")
    print(f"Students          : {len(students)}")
    print(f"Courses           : {len(courses)}")
    print(f"Learning Outcomes : {len(learning_outcomes)}")
    print(f"LO Mappings       : {len(course_lo_mapping)}")
    print(f"Enrollments       : {len(enrollments)}")
    print(f"Attendance        : {len(attendance_records)}")
    print(f"Assessments       : {len(assessments)}")
    print(f"Assessment Results: {len(assessment_results)}")
    print(f"Feedback          : {len(feedback_records)}")

    print("\nAll data inserted into MySQL successfully.")


except Exception as error:

    connection.rollback()

    print("\nERROR OCCURRED")
    print(error)

    print("\nNo partial changes were saved.")


finally:

    cursor.close()
    connection.close()

    print("\nDatabase connection closed.")