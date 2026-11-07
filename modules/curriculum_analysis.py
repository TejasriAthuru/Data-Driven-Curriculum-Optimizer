
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def load_curriculum_data():
    """Load curriculum effectiveness data."""
    path = PROCESSED_DATA_DIR / "curriculum_effectiveness.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"Curriculum effectiveness dataset not found: {path}"
        )

    return pd.read_csv(path)


def get_curriculum_summary(df=None):
    """Calculate summary metrics for curriculum effectiveness."""
    if df is None:
        df = load_curriculum_data()

    if df.empty:
        return {
            "total_courses": 0,
            "average_effectiveness_score": 0.0,
            "average_assessment_score": 0.0,
            "average_attendance": 0.0,
            "courses_needing_review": 0,
        }

    def numeric_mean(column):
        if column not in df.columns:
            return 0.0

        values = pd.to_numeric(df[column], errors="coerce")
        return round(float(values.mean()), 2) if values.notna().any() else 0.0

    if "effectiveness_status" in df.columns:
        status = df["effectiveness_status"].astype(str).str.strip().str.lower()
        needs_review = int(
            status.str.contains(
                "low|poor|review|ineffective|needs improvement",
                regex=True,
                na=False,
            ).sum()
        )
    else:
        needs_review = 0

    return {
        "total_courses": int(
            df["course_id"].nunique()
            if "course_id" in df.columns
            else len(df)
        ),
        "average_effectiveness_score": numeric_mean("effectiveness_score"),
        "average_assessment_score": numeric_mean("average_assessment_score"),
        "average_attendance": numeric_mean("average_attendance"),
        "courses_needing_review": needs_review,
    }


def get_course_effectiveness(df=None):
    """Return courses sorted by effectiveness score."""
    if df is None:
        df = load_curriculum_data()

    if "effectiveness_score" not in df.columns:
        return df.copy()

    return df.sort_values(
        "effectiveness_score",
        ascending=True,
        na_position="last",
    ).reset_index(drop=True)


def get_courses_needing_review(df=None):
    """Return courses whose effectiveness status suggests review."""
    if df is None:
        df = load_curriculum_data()

    if "effectiveness_status" not in df.columns:
        return df.iloc[0:0].copy()

    status = df["effectiveness_status"].astype(str).str.strip().str.lower()
    mask = status.str.contains(
        "low|poor|review|ineffective|needs improvement",
        regex=True,
        na=False,
    )

    return df[mask].copy()


def filter_courses(
    df=None,
    department_id=None,
    minimum_attendance=None,
    maximum_attendance=None,
    minimum_assessment_score=None,
    maximum_assessment_score=None,
):
    """Filter curriculum results by department and performance metrics."""
    if df is None:
        df = load_curriculum_data()

    result = df.copy()

    if department_id is not None and "department_id" in result.columns:
        result = result[
            result["department_id"].astype(str)
            == str(department_id)
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

    if "average_assessment_score" in result.columns:
        scores = pd.to_numeric(
            result["average_assessment_score"], errors="coerce"
        )

        if minimum_assessment_score is not None:
            result = result[scores >= minimum_assessment_score]
            scores = pd.to_numeric(
                result["average_assessment_score"], errors="coerce"
            )

        if maximum_assessment_score is not None:
            result = result[scores <= maximum_assessment_score]

    return result.reset_index(drop=True)


def main():
    """Print a curriculum effectiveness report."""
    df = load_curriculum_data()
    summary = get_curriculum_summary(df)

    print("CURRICULUM EFFECTIVENESS ANALYSIS")
    print("=" * 45)

    for metric, value in summary.items():
        print(f"{metric.replace('_', ' ').title()}: {value}")

    print("\nCourses ordered by effectiveness:")
    print(get_course_effectiveness(df).to_string(index=False))

    review_df = get_courses_needing_review(df)
    print(f"\nCourses flagged for review: {len(review_df)}")

    if not review_df.empty:
        print(review_df.to_string(index=False))


if __name__ == "__main__":
    main()
