
"""Role-based access control for the Data-Driven Curriculum Optimizer."""

from modules.database_connection import get_connection

ROLES = {
    "Data Admin",
    "Student",
    "Faculty",
    "Curriculum Committee",
    "Academic Administrator",
}

ROLE_PERMISSIONS = {
    "Data Admin": {
        "upload_import_data",
        "manage_datasets",
        "validate_data",
        "clean_preprocess_data",
        "integrate_datasets",
        "view_data_quality",
        "view_data_summary",
    },
    "Student": {
        "provide_own_data",
        "view_own_performance",
        "view_own_course_analysis",
        "view_own_learning_outcomes",
    },
    "Faculty": {
        "view_assigned_course_performance",
        "view_assigned_course_trends",
        "view_assigned_course_risks",
        "view_assigned_course_students",
        "analyze_assessment_results",
        "analyze_attendance",
        "analyze_marks_gpa_cgpa",
        "perform_statistical_analysis",
        "view_grade_distribution",
        "view_correlation_analysis",
        "view_item_level_analysis",
        "view_rubric_consistency",
        "view_cohort_comparison",
        "view_significant_patterns",
        "view_trend_analysis",
        "predict_future_performance",
        "run_predictive_analysis",
        "view_risk_classification",
        "view_early_warnings",
        "view_performance_reports",
        "view_recommendations",
        "export_assigned_course_reports",
    },
    "Curriculum Committee": {
        "view_course_analysis",
        "view_learning_outcomes",
        "view_mapping_completeness",
        "analyze_co_po_mapping",
        "compute_learning_outcome_attainment",
        "identify_weak_courses",
        "review_performance_findings",
        "view_curriculum_effectiveness",
        "view_curriculum_recommendations",
        "view_performance_reports",
        "export_curriculum_reports",
    },
    "Academic Administrator": {
        "view_overall_dashboard",
        "view_interactive_dashboard",
        "view_performance_visualizations",
        "view_learning_outcome_charts",
        "view_risk_indicators",
        "view_system_reports",
        "export_reports",
        "export_csv_reports",
        "export_pdf_reports",
        "manage_users",
        "manage_roles",
        "manage_system_settings",
        "configure_thresholds",
        "view_access_overview",
    },
}


def authorize_user_action(role, action):
    """Return True when the role is permitted to perform the action."""
    if role not in ROLE_PERMISSIONS:
        return False
    return action in ROLE_PERMISSIONS[role]


def require_permission(role, action):
    """Raise PermissionError when access is not allowed."""
    if not authorize_user_action(role, action):
        raise PermissionError(
            f"Role '{role}' is not authorized to perform '{action}'."
        )
    return True


def get_student_id_for_user(user):
    """Resolve a student's database ID from an authenticated user record."""
    if not user or user.get("role") != "Student":
        return None

    linked_id = user.get("linked_id")
    if linked_id is not None:
        return linked_id

    username = user.get("username")
    if not username:
        return None

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT student_id
            FROM student
            WHERE student_id = %s
            LIMIT 1
            """,
            (username,),
        )
        row = cursor.fetchone()
        return row["student_id"] if row else None
    except Exception:
        return None
    finally:
        cursor.close()
        conn.close()


def get_assigned_course_ids(user):
    """Return course IDs assigned to the authenticated faculty member."""
    if not user or user.get("role") != "Faculty":
        return []

    linked_id = user.get("linked_id")
    if linked_id is None:
        return []

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT course_id FROM course WHERE faculty_id = %s",
            (linked_id,),
        )
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        return []
    finally:
        cursor.close()
        conn.close()


def get_access_summary():
    """Return a readable overview of permissions for each role."""
    return {
        role: sorted(permissions)
        for role, permissions in ROLE_PERMISSIONS.items()
    }


if __name__ == "__main__":
    print("Role-based access control check")
    print("=" * 40)

    for role in sorted(ROLES):
        print(f"\n{role}")
        for permission in sorted(ROLE_PERMISSIONS[role]):
            print(f"  - {permission}")

    print("\nAccess control module loaded successfully.")
