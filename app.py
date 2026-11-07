
from pathlib import Path
import json
import io
from datetime import datetime

import pandas as pd
import streamlit as st

from modules.authentication import authenticate_user, create_user
from modules.database_connection import get_connection


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
IMPORTED_DIR = DATA_DIR / "imported"
SETTINGS_FILE = DATA_DIR / "system_settings.json"

IMPORTED_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(
    page_title="Data-Driven Curriculum Optimizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROLES = [
    "Data Admin",
    "Student",
    "Faculty",
    "Curriculum Committee",
    "Academic Administrator",
]

DEMO_USERS = {
    "Data Admin (admin_demo)": "admin_demo",
    "Student (student_demo)": "student_demo",
    "Faculty (faculty_demo)": "faculty_demo",
    "Curriculum Committee (committee_demo)": "committee_demo",
    "Academic Administrator (academic_admin_demo)": "academic_admin_demo",
}

ROLE_PAGES = {
    "Data Admin": [
        "Dashboard",
        "Upload and Manage Data",
        "Validate Data",
        "Data Summary",
    ],
    "Student": [
        "My Performance",
        "My Course Records",
        "My Learning Outcomes",
    ],
    "Faculty": [
        "Dashboard",
        "Marks and Assessment Analysis",
        "Attendance Analysis",
        "Course Analysis",
        "Student Risk Analysis",
        "Predictive Analysis",
        "Early Warnings",
        "Learning Outcomes",
        "Recommendations",
        "Reports",
    ],
    "Curriculum Committee": [
        "Dashboard",
        "Course Analysis",
        "CO PO Mapping",
        "Learning Outcome Attainment",
        "Weak Courses and Gaps",
        "Curriculum Effectiveness",
        "Recommendations",
        "Reports",
    ],
    "Academic Administrator": [
        "Dashboard",
        "Student Performance",
        "Course Analysis",
        "Risk Analysis",
        "Learning Outcomes",
        "Curriculum Effectiveness",
        "Recommendations",
        "Reports",
        "User Management",
        "System Settings",
        "Access Overview",
    ],
}

DATASETS = {
    "Student Performance": "student_performance_analysis.csv",
    "Student Course Performance": "student_course_performance.csv",
    "Course Summary": "course_summary.csv",
    "Course Performance": "course_performance_analysis.csv",
    "Course Risk": "course_risk_analysis.csv",
    "Attendance Analysis": "attendance_analysis.csv",
    "Attendance Performance": "attendance_performance_analysis.csv",
    "Learning Outcomes": "learning_outcome_analysis_final.csv",
    "Learning Outcome Mapping": "learning_outcome_analysis.csv",
    "Curriculum Effectiveness": "curriculum_effectiveness.csv",
    "Department Analysis": "department_analysis.csv",
    "Recommendations": "final_recommendations.csv",
    "Recommendation Summary": "recommendation_summary.csv",
    "Performance Distribution": "performance_distribution.csv",
    "Risk Distribution": "risk_distribution.csv",
}

DEFAULT_SETTINGS = {
    "attendance_threshold": 75,
    "performance_threshold": 50,
    "risk_threshold": 40,
}


# ============================================================
# DATABASE AND DATA HELPERS
# ============================================================

def query_database(sql, params=None):
    """Run a database query and return a DataFrame."""
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()

        columns = (
            [item[0] for item in cursor.description]
            if cursor.description else []
        )
        return pd.DataFrame(rows, columns=columns)

    except Exception as exc:
        st.error(f"Database operation failed: {exc}")
        return pd.DataFrame()

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


def load_dataset(label_or_filename):
    """Load a processed CSV by label or filename."""
    filename = DATASETS.get(label_or_filename, label_or_filename)
    path = PROCESSED_DIR / Path(filename).name

    if not path.is_file():
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception as exc:
        st.error(f"Could not read {path.name}: {exc}")
        return pd.DataFrame()


def available_datasets():
    return {
        label: filename
        for label, filename in DATASETS.items()
        if (PROCESSED_DIR / filename).is_file()
    }


def load_settings():
    settings = DEFAULT_SETTINGS.copy()

    if SETTINGS_FILE.exists():
        try:
            saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            settings.update({
                key: saved[key]
                for key in DEFAULT_SETTINGS
                if key in saved
            })
        except (OSError, ValueError, TypeError):
            pass

    return settings


def save_settings(settings):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(settings, indent=4),
        encoding="utf-8",
    )


def user_role(user):
    return user.get("role", "")


def user_linked_id(user):
    return user.get("linked_id")


def show_table(df, title=None, filename="report.csv"):
    if title:
        st.subheader(title)

    if df.empty:
        st.info("No data is available for this section.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=f"download_{title}_{filename}" if title else filename,
    )


def show_metrics(df):
    if df.empty:
        return

    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        st.metric("Records", len(df))
        return

    columns = st.columns(min(4, len(numeric.columns)))
    for i, name in enumerate(numeric.columns[:4]):
        mean_value = numeric[name].mean()
        if pd.notna(mean_value):
            columns[i].metric(
                name.replace("_", " ").title(),
                f"{mean_value:.2f}",
            )


def filtered_by_linked_id(df, user, column="student_id"):
    """Return rows belonging to the authenticated linked ID."""
    linked_id = user_linked_id(user)

    if linked_id is None or column not in df.columns:
        return pd.DataFrame()

    return df[df[column].astype(str) == str(linked_id)].copy()


def assigned_course_ids(user):
    """Resolve courses assigned to a faculty linked ID."""
    linked_id = user_linked_id(user)
    if linked_id is None:
        return []

    df = query_database(
        "SELECT course_id FROM course WHERE faculty_id = %s",
        (linked_id,),
    )

    if df.empty or "course_id" not in df.columns:
        return []

    return df["course_id"].dropna().tolist()


def faculty_filter(df, user):
    """Limit course-level data to the faculty member's assigned courses."""
    if df.empty or "course_id" not in df.columns:
        return pd.DataFrame()

    ids = assigned_course_ids(user)
    if not ids:
        return pd.DataFrame()

    return df[df["course_id"].astype(str).isin(
        [str(value) for value in ids]
    )].copy()


def logout():
    st.session_state.pop("authenticated_user", None)
    st.session_state.pop("current_page", None)
    st.rerun()


# ============================================================
# LOGIN
# ============================================================

def login_page():
    st.title("📊 Data-Driven Curriculum Optimizer")
    st.markdown("### Secure Login")
    st.write("Choose your account and enter its password.")

    with st.form("login_form"):
        selected = st.selectbox(
            "Choose account",
            list(DEMO_USERS.keys()),
        )
        username = DEMO_USERS[selected]

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your account password",
        )

        submitted = st.form_submit_button(
            "Login",
            use_container_width=True,
        )

    if submitted:
        if not password:
            st.error("Please enter your password.")
            return

        try:
            user = authenticate_user(username, password)
        except Exception as exc:
            st.error(f"Login failed: {exc}")
            return

        if not user:
            st.error(
                "Invalid credentials, inactive account, "
                "or unsupported role."
            )
            return

        role = user_role(user)
        if role not in ROLE_PAGES:
            st.error("This account has an unsupported role.")
            return

        st.session_state["authenticated_user"] = user
        st.session_state["current_page"] = ROLE_PAGES[role][0]
        st.rerun()

    st.caption(
        "The account dropdown selects a username only. "
        "A valid password is still required."
    )


# ============================================================
# SHARED DASHBOARD
# ============================================================

def dashboard_page(role, user):
    st.header(f"{role} Dashboard")
    st.caption("Academic performance, curriculum quality and learning outcomes")

    if role == "Student":
        student_performance_page(user)
        return

    course_df = load_dataset("Course Summary")
    risk_df = load_dataset("Course Risk")
    student_df = load_dataset("Student Performance")
    lo_df = load_dataset("Learning Outcomes")

    if role == "Faculty":
        course_df = faculty_filter(course_df, user)
        risk_df = faculty_filter(risk_df, user)

    if role == "Curriculum Committee":
        st.info("Review course performance and learning-outcome attainment.")

    metrics = st.columns(4)
    metrics[0].metric("Courses", len(course_df))
    metrics[1].metric("Student records", len(student_df))
    metrics[2].metric("Risk records", len(risk_df))
    metrics[3].metric("Learning outcomes", len(lo_df))

    if not course_df.empty:
        show_table(course_df, "Course Summary", "course_summary.csv")

        if "average_assessment_score" in course_df.columns:
            chart_cols = [
                col for col in [
                    "course_name", "average_assessment_score"
                ] if col in course_df.columns
            ]
            if len(chart_cols) == 2:
                chart = course_df[chart_cols].dropna()
                if not chart.empty:
                    st.subheader("Average Course Assessment")
                    st.bar_chart(chart.set_index("course_name"))

    if not risk_df.empty:
        show_table(risk_df, "Course Risk Overview", "course_risk.csv")


# ============================================================
# DATA ADMIN — MODULE 1
# ============================================================

def data_summary_page():
    st.header("Data Summary")
    datasets = available_datasets()

    if not datasets:
        st.warning("No processed CSVs found in data/processed.")
        return

    rows = []
    for label, filename in datasets.items():
        df = load_dataset(filename)
        rows.append({
            "Dataset": label,
            "Filename": filename,
            "Rows": len(df),
            "Columns": len(df.columns),
            "Missing Values": int(df.isna().sum().sum()),
            "Duplicate Rows": int(df.duplicated().sum()),
        })

    show_table(pd.DataFrame(rows), "Processed Dataset Inventory")


def data_quality_page():
    st.header("Data Validation and Quality")
    datasets = available_datasets()

    if not datasets:
        st.warning("No processed datasets found.")
        return

    selected = st.selectbox("Dataset to validate", list(datasets.keys()))
    df = load_dataset(datasets[selected])

    if df.empty:
        st.warning("The selected dataset is empty or unavailable.")
        return

    a, b, c = st.columns(3)
    a.metric("Rows", len(df))
    b.metric("Columns", len(df.columns))
    c.metric("Duplicate rows", int(df.duplicated().sum()))

    report = pd.DataFrame({
        "Column": df.columns,
        "Data Type": [str(df[col].dtype) for col in df.columns],
        "Missing Values": [int(df[col].isna().sum()) for col in df.columns],
        "Missing (%)": [
            round(float(df[col].isna().mean() * 100), 2)
            for col in df.columns
        ],
        "Unique Values": [int(df[col].nunique(dropna=True)) for col in df.columns],
    })

    show_table(report, "Column Quality Report", "data_quality_report.csv")

    if df.duplicated().any():
        st.warning("Duplicate rows were detected. Review them before cleaning.")
        if st.checkbox("Preview duplicate rows"):
            st.dataframe(
                df[df.duplicated(keep=False)],
                use_container_width=True,
            )

    missing = df.isna().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        st.warning("Missing values were found in these columns.")
        st.bar_chart(missing)


def data_management_page():
    st.header("Upload and Manage Data")
    st.write(
        "Upload academic CSV files, preview their contents, validate them, "
        "and save them to the staging folder. Uploading does not automatically "
        "modify your database or processed datasets."
    )

    uploads = st.file_uploader(
        "Upload CSV files",
        type=["csv"],
        accept_multiple_files=True,
    )

    if uploads:
        for uploaded in uploads:
            with st.expander(uploaded.name, expanded=True):
                try:
                    df = pd.read_csv(uploaded)
                    st.write(f"{len(df)} rows · {len(df.columns)} columns")
                    st.dataframe(df.head(20), use_container_width=True)

                    st.write("Missing values:", int(df.isna().sum().sum()))
                    st.write("Duplicate rows:", int(df.duplicated().sum()))

                    safe_name = Path(uploaded.name).name
                    if st.button(
                        f"Save {safe_name} to staging",
                        key=f"save_{safe_name}",
                    ):
                        destination = IMPORTED_DIR / safe_name
                        destination.write_bytes(uploaded.getvalue())
                        st.success(f"Saved staging file: {safe_name}")

                except Exception as exc:
                    st.error(f"Could not read CSV: {exc}")

    st.divider()
    st.subheader("Staged Files")

    staged = sorted(
        path for path in IMPORTED_DIR.iterdir()
        if path.is_file() and path.suffix.lower() == ".csv"
    )

    if not staged:
        st.info("No staged CSV files.")
        return

    for path in staged:
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(path.name)
        col2.write(f"{path.stat().st_size:,} bytes")
        col3.download_button(
            "Download",
            data=path.read_bytes(),
            file_name=path.name,
            mime="text/csv",
            key=f"download_staged_{path.name}",
        )


# ============================================================
# STUDENT — PERSONAL RECORDS ONLY
# ============================================================

def student_performance_page(user):
    st.header("My Performance")

    df = load_dataset("Student Performance")
    if df.empty:
        st.info("Student performance data is not available.")
        return

    own = filtered_by_linked_id(df, user)
    if own.empty:
        st.warning(
            "No linked student record was found. "
            "Ask the administrator to link your account to your student ID."
        )
        return

    show_metrics(own)
    show_table(own, "Your Performance", "my_performance.csv")

    if "performance_category" in own.columns:
        st.subheader("Performance Category")
        st.bar_chart(own["performance_category"].value_counts())


def student_course_records_page(user):
    st.header("My Course Records")

    df = load_dataset("Student Course Performance")
    if df.empty:
        st.info("Student course records are not available.")
        return

    own = filtered_by_linked_id(df, user)
    if own.empty:
        st.warning("No course records are linked to this account.")
        return

    show_table(own, "Your Course Records", "my_course_records.csv")


def student_learning_outcomes_page(user):
    st.header("My Learning Outcomes")
    st.info(
        "The current learning-outcome CSVs are course-level data. "
        "They do not identify an individual student's attainment. "
        "Your course records are shown below where available."
    )
    student_course_records_page(user)


# ============================================================
# FACULTY — PERFORMANCE AND PREDICTIVE ANALYSIS
# ============================================================

def faculty_course_analysis_page(user):
    st.header("Course Analysis")

    df = load_dataset("Course Performance")
    if df.empty:
        df = load_dataset("Course Summary")

    df = faculty_filter(df, user)
    if df.empty:
        st.warning(
            "No assigned courses were found for this account. "
            "Verify the faculty linked_id and course.faculty_id mapping."
        )
        return

    show_metrics(df)
    show_table(df, "Assigned Course Performance", "assigned_courses.csv")

    if {"course_name", "average_assessment_score"}.issubset(df.columns):
        chart = df[["course_name", "average_assessment_score"]].dropna()
        if not chart.empty:
            st.bar_chart(chart.set_index("course_name"))


def faculty_student_analysis_page(user):
    st.header("Student Performance")

    course_ids = assigned_course_ids(user)
    if not course_ids:
        st.warning("No courses are assigned to this faculty account.")
        return

    df = load_dataset("Student Course Performance")
    if df.empty or "course_id" not in df.columns:
        st.info("Student course performance data is not available.")
        return

    df = df[df["course_id"].astype(str).isin(
        [str(x) for x in course_ids]
    )].copy()

    if df.empty:
        st.info("No student records exist for your assigned courses.")
        return

    show_table(df, "Students in Assigned Courses", "assigned_students.csv")

    if "overall_assessment_percentage" in df.columns:
        st.subheader("Assessment Score Distribution")
        st.bar_chart(df["overall_assessment_percentage"].dropna())


def faculty_attendance_page(user):
    st.header("Attendance Analysis")

    course_ids = assigned_course_ids(user)
    if not course_ids:
        st.warning("No assigned courses were found.")
        return

    df = load_dataset("Attendance Performance")
    if df.empty or "course_id" not in df.columns:
        df = load_dataset("Student Course Performance")

    if df.empty or "course_id" not in df.columns:
        st.info("Attendance data is not available.")
        return

    df = df[df["course_id"].astype(str).isin(
        [str(x) for x in course_ids]
    )].copy()

    show_table(df, "Attendance for Assigned Courses", "attendance.csv")

    if "attendance_percentage" in df.columns:
        settings = load_settings()
        threshold = settings["attendance_threshold"]
        df["attendance_status"] = df["attendance_percentage"].apply(
            lambda x: "Below threshold"
            if pd.notna(x) and x < threshold else "Meets threshold"
        )
        show_table(df, "Attendance Threshold Check", "attendance_check.csv")


def faculty_risk_page(user):
    st.header("Student Risk Analysis")

    course_ids = assigned_course_ids(user)
    if not course_ids:
        st.warning("No assigned courses were found.")
        return

    df = load_dataset("Course Risk")
    if not df.empty and "course_id" in df.columns:
        df = df[df["course_id"].astype(str).isin(
            [str(x) for x in course_ids]
        )].copy()
        show_table(df, "Risk by Assigned Course", "assigned_risk.csv")

    students = load_dataset("Student Course Performance")
    if not students.empty and "course_id" in students.columns:
        students = students[students["course_id"].astype(str).isin(
            [str(x) for x in course_ids]
        )].copy()

        if "risk_indicator" in students.columns:
            show_table(
                students[students["risk_indicator"].notna()],
                "Risk Indicators",
                "risk_indicators.csv",
            )

    if df.empty and students.empty:
        st.info("Risk analysis data is not available.")


def predictive_analysis_page(user):
    st.header("Predictive Analysis")
    st.write(
        "This page uses the project's existing processed performance and risk "
        "data. It does not claim to train a new model unless the predictive "
        "analysis module is explicitly connected."
    )

    course_ids = assigned_course_ids(user)
    df = load_dataset("Student Course Performance")

    if df.empty or "course_id" not in df.columns:
        st.info("Student course performance data is not available.")
        return

    df = df[df["course_id"].astype(str).isin(
        [str(x) for x in course_ids]
    )].copy()

    if df.empty:
        st.warning("No records are available for assigned courses.")
        return

    if "overall_assessment_percentage" in df.columns:
        threshold = load_settings()["performance_threshold"]
        score = pd.to_numeric(
            df["overall_assessment_percentage"], errors="coerce"
        )
        df["screening_flag"] = score.apply(
            lambda x: "Review recommended"
            if pd.notna(x) and x < threshold else "No score-based flag"
        )
        show_table(df, "Performance Screening", "performance_screening.csv")

    st.caption(
        "Screening flags are indicators for review, not guaranteed predictions "
        "of future academic outcomes."
    )


def faculty_early_warnings_page(user):
    st.header("Early Warning Indicators")

    course_ids = assigned_course_ids(user)
    df = load_dataset("Student Course Performance")

    if df.empty or "course_id" not in df.columns:
        st.info("Student course performance data is not available.")
        return

    df = df[df["course_id"].astype(str).isin(
        [str(x) for x in course_ids]
    )].copy()

    settings = load_settings()
    if "attendance_percentage" in df.columns:
        attendance = pd.to_numeric(df["attendance_percentage"], errors="coerce")
        df["attendance_warning"] = attendance < settings["attendance_threshold"]

    if "overall_assessment_percentage" in df.columns:
        score = pd.to_numeric(
            df["overall_assessment_percentage"], errors="coerce"
        )
        df["performance_warning"] = score < settings["performance_threshold"]

    warning_columns = [
        col for col in ["attendance_warning", "performance_warning"]
        if col in df.columns
    ]

    if warning_columns:
        mask = df[warning_columns].fillna(False).any(axis=1)
        show_table(df[mask], "Records to Review", "early_warnings.csv")
    else:
        st.info("Required attendance and assessment columns are unavailable.")


# ============================================================
# CURRICULUM COMMITTEE — MODULE 2
# ============================================================

def curriculum_course_analysis_page():
    st.header("Course-wise Curriculum Analysis")

    df = load_dataset("Course Performance")
    if df.empty:
        df = load_dataset("Course Summary")

    show_metrics(df)
    show_table(df, "Course Analysis", "curriculum_course_analysis.csv")


def learning_outcomes_page():
    st.header("Learning Outcome Attainment")

    df = load_dataset("Learning Outcomes")
    if df.empty:
        df = load_dataset("Learning Outcome Mapping")

    if df.empty:
        st.warning("Learning outcome data is not available.")
        return

    show_table(df, "Learning Outcome Analysis", "learning_outcomes.csv")

    for column in ["calculated_attainment", "attainment_percentage"]:
        if column in df.columns:
            group_column = "lo_code" if "lo_code" in df.columns else None
            if group_column:
                chart = df.groupby(group_column)[column].mean().dropna()
                if not chart.empty:
                    st.subheader("Average Attainment by Learning Outcome")
                    st.bar_chart(chart)
            break


def co_po_mapping_page():
    st.header("CO/PO Mapping")

    df = load_dataset("Learning Outcome Mapping")
    if df.empty:
        df = load_dataset("Learning Outcomes")

    if df.empty:
        st.info(
            "No mapping data is available. Check that your mapping dataset "
            "contains course_id, lo_id, and the appropriate mapping fields."
        )
        return

    show_table(df, "Available Mapping Records", "mapping_records.csv")

    if {"course_id", "lo_id"}.issubset(df.columns):
        st.subheader("Mapping Completeness")
        summary = (
            df.groupby("course_id")
            .agg(mapped_outcomes=("lo_id", "nunique"),
                 mapping_records=("lo_id", "count"))
            .reset_index()
        )
        show_table(summary, "Mappings by Course", "mapping_completeness.csv")

    st.caption(
        "A complete CO-to-PO alignment score requires the project's actual "
        "CO/PO mapping weights and mapping table. This page does not invent "
        "alignment scores when those inputs are absent."
    )


def weak_courses_page():
    st.header("Weak Courses and Attainment Gaps")

    df = load_dataset("Learning Outcomes")
    if df.empty:
        df = load_dataset("Learning Outcome Mapping")

    if df.empty:
        st.info("Learning outcome data is not available.")
        return

    if "attainment_status" in df.columns:
        weak = df[
            df["attainment_status"].astype(str).str.contains(
                "below|low|weak|gap|under", case=False, na=False
            )
        ]
        show_table(weak, "Outcomes Flagged for Review", "weak_outcomes.csv")

    if "attainment_gap" in df.columns:
        gaps = df.copy()
        gaps["attainment_gap"] = pd.to_numeric(
            gaps["attainment_gap"], errors="coerce"
        )
        gaps = gaps.sort_values("attainment_gap", ascending=False)
        show_table(gaps, "Attainment Gap Review", "attainment_gaps.csv")


def curriculum_effectiveness_page():
    st.header("Curriculum Effectiveness")

    df = load_dataset("Curriculum Effectiveness")
    if df.empty:
        st.warning("Curriculum effectiveness data is not available.")
        return

    show_metrics(df)
    show_table(df, "Curriculum Effectiveness", "curriculum_effectiveness.csv")

    if {"course_name", "effectiveness_score"}.issubset(df.columns):
        chart = df[["course_name", "effectiveness_score"]].dropna()
        if not chart.empty:
            st.bar_chart(chart.set_index("course_name"))


# ============================================================
# RECOMMENDATIONS AND REPORTS — MODULE 4
# ============================================================

def recommendations_page():
    st.header("Evidence-based Recommendations")

    df = load_dataset("Recommendations")
    if df.empty:
        df = load_dataset("Course Performance")

    if df.empty:
        st.info("No recommendation or course analysis data is available.")
        return

    show_table(df, "Recommendations and Evidence", "recommendations.csv")

    if "priority" in df.columns:
        st.subheader("Recommendations by Priority")
        st.bar_chart(df["priority"].fillna("Unspecified").value_counts())


def reports_page():
    st.header("Reports and Exports")

    datasets = available_datasets()
    if not datasets:
        st.info("No processed datasets are available for export.")
        return

    selected = st.selectbox("Choose report", list(datasets.keys()))
    df = load_dataset(datasets[selected])

    if df.empty:
        st.warning("The selected report is empty.")
        return

    show_metrics(df)
    show_table(df, selected, datasets[selected])

    st.caption(
        "CSV export is supported here. PDF export requires the project's "
        "report_generator module to be connected and configured."
    )


# ============================================================
# ACADEMIC ADMINISTRATOR
# ============================================================

def user_management_page():
    st.header("User Management")

    st.warning(
        "Only create accounts for authorized users. Never share passwords "
        "in exported reports or group chats."
    )

    with st.form("create_user_form"):
        username = st.text_input("New username")
        password = st.text_input("Temporary password", type="password")
        confirm = st.text_input("Confirm password", type="password")
        role = st.selectbox("Role", ROLES)
        linked_id = st.text_input("Linked student/faculty ID (optional)")
        submitted = st.form_submit_button("Create Account")

    if submitted:
        username = username.strip()

        if not username:
            st.error("Enter a username.")
        elif len(password) < 8:
            st.error("Password must contain at least 8 characters.")
        elif password != confirm:
            st.error("Passwords do not match.")
        else:
            try:
                result = create_user(
                    username=username,
                    password=password,
                    role=role,
                    linked_id=linked_id.strip() or None,
                )
                if result is False:
                    st.error("The user could not be created.")
                else:
                    st.success(
                        "Account creation completed. Verify the account "
                        "in the database before sharing login details."
                    )
            except Exception as exc:
                st.error(f"Could not create account: {exc}")

    st.subheader("Registered Accounts")
    users = query_database(
        "SELECT user_id, username, role, linked_id, is_active "
        "FROM users ORDER BY user_id"
    )
    show_table(users, "Accounts", "user_accounts.csv")


def system_settings_page():
    st.header("System Settings and Thresholds")
    settings = load_settings()

    with st.form("settings_form"):
        attendance = st.number_input(
            "Attendance threshold (%)",
            min_value=0, max_value=100,
            value=int(settings["attendance_threshold"]),
        )
        performance = st.number_input(
            "Performance threshold (%)",
            min_value=0, max_value=100,
            value=int(settings["performance_threshold"]),
        )
        risk = st.number_input(
            "Risk threshold (%)",
            min_value=0, max_value=100,
            value=int(settings["risk_threshold"]),
        )
        submitted = st.form_submit_button("Save Settings")

    if submitted:
        save_settings({
            "attendance_threshold": int(attendance),
            "performance_threshold": int(performance),
            "risk_threshold": int(risk),
        })
        st.success("Settings saved.")

    st.caption(
        "These settings are stored in data/system_settings.json. "
        "Analysis modules must read these values to apply them consistently."
    )


def access_overview_page():
    st.header("Role Access Overview")

    rows = []
    for role, pages in ROLE_PAGES.items():
        for page in pages:
            rows.append({"Role": role, "Page": page})

    show_table(pd.DataFrame(rows), "Configured Role Pages", "role_access.csv")

    st.warning(
        "Navigation separation is not sufficient security by itself. "
        "Backend modules must also validate role permissions before returning "
        "or changing sensitive data."
    )


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():
    if "authenticated_user" not in st.session_state:
        login_page()
        return

    user = st.session_state["authenticated_user"]
    role = user_role(user)

    if role not in ROLE_PAGES:
        st.error("Unsupported role. Please contact the administrator.")
        if st.button("Log out"):
            logout()
        return

    st.title("📊 Data-Driven Curriculum Optimizer")

    with st.sidebar:
        st.subheader("Account")
        st.write(f"**Username:** {user.get('username', 'Unknown')}")
        st.write(f"**Role:** {role}")
        st.divider()
        st.subheader("Navigation")

        pages = ROLE_PAGES[role]
        current = st.session_state.get("current_page", pages[0])
        if current not in pages:
            current = pages[0]

        selected = st.radio(
            "Select page",
            pages,
            index=pages.index(current),
            label_visibility="collapsed",
        )
        st.session_state["current_page"] = selected

        st.divider()
        if st.button("Log out", use_container_width=True):
            logout()

    page = st.session_state["current_page"]

    # Data Admin
    if role == "Data Admin":
        if page == "Dashboard":
            dashboard_page(role, user)
        elif page == "Upload and Manage Data":
            data_management_page()
        elif page == "Validate Data":
            data_quality_page()
        elif page == "Data Summary":
            data_summary_page()

    # Student
    elif role == "Student":
        if page == "My Performance":
            student_performance_page(user)
        elif page == "My Course Records":
            student_course_records_page(user)
        elif page == "My Learning Outcomes":
            student_learning_outcomes_page(user)

    # Faculty
    elif role == "Faculty":
        if page == "Dashboard":
            dashboard_page(role, user)
        elif page == "Marks and Assessment Analysis":
            faculty_student_analysis_page(user)
        elif page == "Attendance Analysis":
            faculty_attendance_page(user)
        elif page == "Course Analysis":
            faculty_course_analysis_page(user)
        elif page == "Student Performance":
            faculty_student_analysis_page(user)
        elif page == "Student Risk Analysis":
            faculty_risk_page(user)
        elif page == "Predictive Analysis":
            predictive_analysis_page(user)
        elif page == "Early Warnings":
            faculty_early_warnings_page(user)
        elif page == "Learning Outcomes":
            learning_outcomes_page()
        elif page == "Recommendations":
            recommendations_page()
        elif page == "Reports":
            reports_page()

    # Curriculum Committee
    elif role == "Curriculum Committee":
        if page == "Dashboard":
            dashboard_page(role, user)
        elif page == "Course Analysis":
            curriculum_course_analysis_page()
        elif page == "CO PO Mapping":
            co_po_mapping_page()
        elif page == "Learning Outcome Attainment":
            learning_outcomes_page()
        elif page == "Weak Courses and Gaps":
            weak_courses_page()
        elif page == "Curriculum Effectiveness":
            curriculum_effectiveness_page()
        elif page == "Recommendations":
            recommendations_page()
        elif page == "Reports":
            reports_page()

    # Academic Administrator
    elif role == "Academic Administrator":
        if page == "Dashboard":
            dashboard_page(role, user)
        elif page == "Student Performance":
            student_analysis_page()
        elif page == "Course Analysis":
            curriculum_course_analysis_page()
        elif page == "Risk Analysis":
            risk_analysis_page()
        elif page == "Learning Outcomes":
            learning_outcomes_page()
        elif page == "Curriculum Effectiveness":
            curriculum_effectiveness_page()
        elif page == "Recommendations":
            recommendations_page()
        elif page == "Reports":
            reports_page()
        elif page == "User Management":
            user_management_page()
        elif page == "System Settings":
            system_settings_page()
        elif page == "Access Overview":
            access_overview_page()

    st.divider()
    st.caption(
        "Data-Driven Curriculum Optimizer | Academic Analytics | "
        + datetime.now().strftime("%d %b %Y")
    )


def student_analysis_page():
    st.header("Student Performance Analysis")
    df = load_dataset("Student Performance")
    if df.empty:
        st.info("Student performance data is not available.")
        return

    show_metrics(df)
    show_table(df, "Student Performance", "student_performance.csv")

    if "performance_category" in df.columns:
        st.subheader("Performance Category Distribution")
        st.bar_chart(df["performance_category"].value_counts())


def risk_analysis_page():
    st.header("Risk Analysis")
    df = load_dataset("Course Risk")
    distribution = load_dataset("Risk Distribution")

    show_table(df, "Course Risk Analysis", "course_risk.csv")
    show_table(distribution, "Risk Distribution", "risk_distribution.csv")

    if {"risk_status", "student_count"}.issubset(distribution.columns):
        st.bar_chart(distribution.set_index("risk_status")["student_count"])


if __name__ == "__main__":
    main()
