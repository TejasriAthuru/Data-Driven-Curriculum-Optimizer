import os
from pathlib import Path

import pandas as pd

from modules.database_connection import get_connection


# ---------------------------------------------------------
# 1. PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PROCESSED_FOLDER = PROJECT_ROOT / "data" / "processed"
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# 2. READ DATA FROM MYSQL
# ---------------------------------------------------------

def read_table(connection, table_name):
    """Read a complete MySQL table into a Pandas DataFrame."""

    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM {table_name}")

    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description]

    cursor.close()

    return pd.DataFrame(rows, columns=columns)


# ---------------------------------------------------------
# 3. BASIC CLEANING
# ---------------------------------------------------------

def clean_dataframe(df):
    """Perform basic cleaning without changing valid values."""

    df = df.copy()

    # Remove completely duplicated rows
    df = df.drop_duplicates()

    # Remove unwanted spaces from text columns
    for column in df.select_dtypes(include=["str"]).columns:
        df[column] = df[column].apply(
            lambda value: value.strip() if isinstance(value, str) else value
        )

    return df


# ---------------------------------------------------------
# 4. PREPARE STUDENT-COURSE PERFORMANCE DATA
# ---------------------------------------------------------

def prepare_student_course_performance(
    enrollment,
    attendance,
    assessment,
    assessment_result,
    feedback
):
    """
    Combine enrollment, attendance, assessment and feedback
    information into one analysis-ready dataset.
    """

    # -----------------------------------------------------
    # Assessment performance
    # -----------------------------------------------------

    assessment_data = assessment_result.merge(
        assessment[
            [
                "assessment_id",
                "course_id",
                "assessment_type",
                "max_marks"
            ]
        ],
        on="assessment_id",
        how="left"
    )

    assessment_summary = (
        assessment_data
        .groupby(["student_id", "course_id"], as_index=False)
        .agg(
            total_marks_obtained=("marks_obtained", "sum"),
            total_max_marks=("max_marks", "sum"),
            average_assessment_percentage=("percentage", "mean")
        )
    )

    assessment_summary["overall_assessment_percentage"] = (
        assessment_summary["total_marks_obtained"]
        / assessment_summary["total_max_marks"]
        * 100
    ).round(2)

    assessment_summary["average_assessment_percentage"] = (
        assessment_summary["average_assessment_percentage"]
        .round(2)
    )

    # -----------------------------------------------------
    # Attendance
    # -----------------------------------------------------

    attendance_data = attendance[
        [
            "student_id",
            "course_id",
            "classes_conducted",
            "classes_attended",
            "attendance_percentage"
        ]
    ].copy()

    # -----------------------------------------------------
    # Feedback
    # -----------------------------------------------------

    feedback_summary = (
        feedback
        .groupby(["student_id", "course_id"], as_index=False)
        .agg(
            feedback_rating=("rating", "mean")
        )
    )

    feedback_summary["feedback_rating"] = (
        feedback_summary["feedback_rating"].round(2)
    )

    # -----------------------------------------------------
    # Start with enrollment
    # -----------------------------------------------------

    performance = enrollment[
        [
            "student_id",
            "course_id",
            "academic_year",
            "semester",
            "enrollment_status"
        ]
    ].copy()

    # Add attendance
    performance = performance.merge(
        attendance_data,
        on=["student_id", "course_id"],
        how="left"
    )

    # Add assessment performance
    performance = performance.merge(
        assessment_summary,
        on=["student_id", "course_id"],
        how="left"
    )

    # Add feedback
    performance = performance.merge(
        feedback_summary,
        on=["student_id", "course_id"],
        how="left"
    )

    # -----------------------------------------------------
    # At-risk indicator
    # -----------------------------------------------------

    performance["risk_indicator"] = "Low Risk"

    risk_condition = (
        (performance["attendance_percentage"] < 75)
        |
        (performance["overall_assessment_percentage"] < 50)
    )

    performance.loc[risk_condition, "risk_indicator"] = "At Risk"

    # -----------------------------------------------------
    # Final column order
    # -----------------------------------------------------

    performance = performance[
        [
            "student_id",
            "course_id",
            "academic_year",
            "semester",
            "enrollment_status",
            "classes_conducted",
            "classes_attended",
            "attendance_percentage",
            "total_marks_obtained",
            "total_max_marks",
            "average_assessment_percentage",
            "overall_assessment_percentage",
            "feedback_rating",
            "risk_indicator"
        ]
    ]

    return performance


# ---------------------------------------------------------
# 5. PREPARE COURSE-LEVEL DATA
# ---------------------------------------------------------

def prepare_course_summary(
    course,
    student_course_performance
):
    """Create course-level analysis data."""

    course_summary = (
        student_course_performance
        .groupby("course_id", as_index=False)
        .agg(
            average_attendance=(
                "attendance_percentage",
                "mean"
            ),
            average_assessment_score=(
                "overall_assessment_percentage",
                "mean"
            ),
            average_feedback_rating=(
                "feedback_rating",
                "mean"
            ),
            students_enrolled=(
                "student_id",
                "nunique"
            ),
            students_at_risk=(
                "risk_indicator",
                lambda x: (x == "At Risk").sum()
            )
        )
    )

    course_summary["average_attendance"] = (
        course_summary["average_attendance"].round(2)
    )

    course_summary["average_assessment_score"] = (
        course_summary["average_assessment_score"].round(2)
    )

    course_summary["average_feedback_rating"] = (
        course_summary["average_feedback_rating"].round(2)
    )

    # Add course names and department information
    course_info = course[
        [
            "course_id",
            "course_name",
            "credits",
            "department_id",
            "faculty_id",
            "semester"
        ]
    ]

    course_summary = course_info.merge(
        course_summary,
        on="course_id",
        how="left"
    )

    return course_summary


# ---------------------------------------------------------
# 6. PREPARE LEARNING OUTCOME DATA
# ---------------------------------------------------------

def prepare_learning_outcome_data(
    learning_outcome,
    course_lo_mapping,
    course
):
    """Create analysis-ready learning outcome data."""

    lo_data = course_lo_mapping.merge(
        learning_outcome[
            [
                "lo_id",
                "lo_code",
                "lo_description",
                "target_attainment"
            ]
        ],
        on="lo_id",
        how="left"
    )

    lo_data = lo_data.merge(
        course[
            [
                "course_id",
                "course_name",
                "department_id"
            ]
        ],
        on="course_id",
        how="left"
    )

    lo_data["attainment_gap"] = (
        lo_data["target_attainment"]
        - lo_data["attainment_percentage"]
    ).round(2)

    lo_data["attainment_status"] = "Target Achieved"

    lo_data.loc[
        lo_data["attainment_gap"] > 0,
        "attainment_status"
    ] = "Below Target"

    return lo_data


# ---------------------------------------------------------
# 7. MAIN PREPROCESSING FUNCTION
# ---------------------------------------------------------

def main():

    print("\n==============================================")
    print("   MODULE 1 - DATA PREPROCESSING")
    print("==============================================")

    connection = get_connection()

    try:

        print("\nReading data from MySQL...")

        department = clean_dataframe(
            read_table(connection, "department")
        )

        faculty = clean_dataframe(
            read_table(connection, "faculty")
        )

        student = clean_dataframe(
            read_table(connection, "student")
        )

        course = clean_dataframe(
            read_table(connection, "course")
        )

        enrollment = clean_dataframe(
            read_table(connection, "enrollment")
        )

        attendance = clean_dataframe(
            read_table(connection, "attendance")
        )

        assessment = clean_dataframe(
            read_table(connection, "assessment")
        )

        assessment_result = clean_dataframe(
            read_table(connection, "assessment_result")
        )

        feedback = clean_dataframe(
            read_table(connection, "feedback")
        )

        learning_outcome = clean_dataframe(
            read_table(connection, "learning_outcome")
        )

        course_lo_mapping = clean_dataframe(
            read_table(connection, "course_lo_mapping")
        )

        print("Data loaded successfully.")

        # -------------------------------------------------
        # Create analysis-ready datasets
        # -------------------------------------------------

        student_course_performance = (
            prepare_student_course_performance(
                enrollment,
                attendance,
                assessment,
                assessment_result,
                feedback
            )
        )

        course_summary = prepare_course_summary(
            course,
            student_course_performance
        )

        learning_outcome_data = prepare_learning_outcome_data(
            learning_outcome,
            course_lo_mapping,
            course
        )

        # -------------------------------------------------
        # Save processed datasets
        # -------------------------------------------------

        student_course_performance.to_csv(
            PROCESSED_FOLDER / "student_course_performance.csv",
            index=False
        )

        course_summary.to_csv(
            PROCESSED_FOLDER / "course_summary.csv",
            index=False
        )

        learning_outcome_data.to_csv(
            PROCESSED_FOLDER / "learning_outcome_analysis.csv",
            index=False
        )

        # -------------------------------------------------
        # Display results
        # -------------------------------------------------

        print("\n========== PREPROCESSING SUMMARY ==========")

        print(
            f"Student-Course Performance : "
            f"{len(student_course_performance)} records"
        )

        print(
            f"Course Summary              : "
            f"{len(course_summary)} records"
        )

        print(
            f"Learning Outcome Data       : "
            f"{len(learning_outcome_data)} records"
        )

        print("\n========== OUTPUT FILES ==========")

        print(
            "1. data/processed/"
            "student_course_performance.csv"
        )

        print(
            "2. data/processed/"
            "course_summary.csv"
        )

        print(
            "3. data/processed/"
            "learning_outcome_analysis.csv"
        )

        print("\n==============================================")
        print("DATA PREPROCESSING COMPLETED SUCCESSFULLY")
        print("==============================================")


    except Exception as error:

        print("\nERROR DURING DATA PREPROCESSING")
        print(error)


    finally:

        connection.close()

        print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()