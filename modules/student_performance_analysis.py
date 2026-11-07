
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def load_student_performance():
    """Load student-level performance analysis."""
    path = PROCESSED_DATA_DIR / "student_performance_analysis.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"Student performance dataset not found: {path}"
        )

    return pd.read_csv(path)


def get_performance_summary(df=None):
    """Return overall student performance statistics."""
    if df is None:
        df = load_student_performance()

    if df.empty:
        return {
            "total_students": 0,
            "average_assessment_score": 0.0,
            "average_attendance": 0.0,
            "average_feedback_rating": 0.0,
            "students_at_risk": 0,
        }

    def numeric_mean(column):
        if column not in df.columns:
            return 0.0

        values = pd.to_numeric(df[column], errors="coerce")
        return round(float(values.mean()), 2) if values.notna().any() else 0.0

    if "risk_status" in df.columns:
        risk = df["risk_status"].astype(str).str.strip().str.lower()
        at_risk = int(risk.isin(["at risk", "at-risk", "high risk", "high-risk"]).sum())
    elif "courses_at_risk" in df.columns:
        risk_counts = pd.to_numeric(df["courses_at_risk"], errors="coerce").fillna(0)
        at_risk = int((risk_counts > 0).sum())
    else:
        at_risk = 0

    return {
        "total_students": int(
            df["student_id"].nunique()
            if "student_id" in df.columns
            else len(df)
        ),
        "average_assessment_score": numeric_mean("average_assessment_score"),
        "average_attendance": numeric_mean("average_attendance"),
        "average_feedback_rating": numeric_mean("average_feedback_rating"),
        "students_at_risk": at_risk,
    }


def get_performance_distribution(df=None):
    """Count students in each performance category."""
    if df is None:
        df = load_student_performance()

    if "performance_category" not in df.columns:
        return pd.DataFrame(columns=["performance_category", "student_count"])

    return (
        df["performance_category"]
        .fillna("Unknown")
        .value_counts()
        .rename_axis("performance_category")
        .reset_index(name="student_count")
    )


def get_risk_distribution(df=None):
    """Count students in each risk category."""
    if df is None:
        df = load_student_performance()

    if "risk_status" not in df.columns:
        return pd.DataFrame(columns=["risk_status", "student_count"])

    return (
        df["risk_status"]
        .fillna("Unknown")
        .value_counts()
        .rename_axis("risk_status")
        .reset_index(name="student_count")
    )


def get_students_at_risk(df=None):
    """Return students whose risk status indicates risk."""
    if df is None:
        df = load_student_performance()

    if "risk_status" in df.columns:
        risk = df["risk_status"].astype(str).str.strip().str.lower()
        return df[
            risk.isin(["at risk", "at-risk", "high risk", "high-risk"])
        ].copy()

    if "courses_at_risk" in df.columns:
        counts = pd.to_numeric(df["courses_at_risk"], errors="coerce").fillna(0)
        return df[counts > 0].copy()

    return df.iloc[0:0].copy()


def filter_students(
    df=None,
    performance_category=None,
    risk_status=None,
    minimum_attendance=None,
    maximum_attendance=None,
):
    """Filter students using performance, risk, and attendance criteria."""
    if df is None:
        df = load_student_performance()

    result = df.copy()

    if performance_category and "performance_category" in result.columns:
        result = result[
            result["performance_category"].astype(str).str.casefold()
            == str(performance_category).casefold()
        ]

    if risk_status and "risk_status" in result.columns:
        result = result[
            result["risk_status"].astype(str).str.casefold()
            == str(risk_status).casefold()
        ]

    if "average_attendance" in result.columns:
        attendance = pd.to_numeric(
            result["average_attendance"], errors="coerce"
        )

        if minimum_attendance is not None:
            result = result[attendance >= minimum_attendance]
            attendance = pd.to_numeric(
                result["average_attendance"], errors="coerce"
            )

        if maximum_attendance is not None:
            result = result[attendance <= maximum_attendance]

    return result.copy()


def main():
    """Run a command-line student performance summary."""
    df = load_student_performance()
    summary = get_performance_summary(df)

    print("STUDENT PERFORMANCE ANALYSIS")
    print("=" * 45)

    for metric, value in summary.items():
        print(f"{metric.replace('_', ' ').title()}: {value}")

    print("\nPerformance distribution:")
    print(get_performance_distribution(df).to_string(index=False))

    print("\nRisk distribution:")
    print(get_risk_distribution(df).to_string(index=False))


if __name__ == "__main__":
    main()
