
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

FINAL_RECOMMENDATIONS_FILE = (
    PROCESSED_DATA_DIR / "final_recommendations.csv"
)
RECOMMENDATIONS_FILE = PROCESSED_DATA_DIR / "recommendations.csv"


def load_recommendations(final=True):
    """Load the project's existing recommendations."""
    file_path = (
        FINAL_RECOMMENDATIONS_FILE
        if final
        else RECOMMENDATIONS_FILE
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Recommendations file not found: {file_path}"
        )

    return pd.read_csv(file_path)


def get_recommendation_summary(df=None):
    """Summarize recommendations by priority."""
    if df is None:
        df = load_recommendations()

    if df.empty:
        return {
            "total_recommendations": 0,
            "courses_covered": 0,
            "high_priority": 0,
            "medium_priority": 0,
            "low_priority": 0,
        }

    priority = (
        df["priority"].astype(str).str.strip().str.lower()
        if "priority" in df.columns
        else pd.Series("", index=df.index)
    )

    return {
        "total_recommendations": int(len(df)),
        "courses_covered": int(
            df["course_id"].nunique()
            if "course_id" in df.columns
            else 0
        ),
        "high_priority": int(priority.isin(["high", "critical", "urgent"]).sum()),
        "medium_priority": int(priority.isin(["medium", "moderate"]).sum()),
        "low_priority": int(priority.isin(["low", "normal"]).sum()),
    }


def filter_recommendations(
    df=None,
    course_id=None,
    priority=None,
    source=None,
):
    """Filter recommendations by course, priority, or source."""
    if df is None:
        df = load_recommendations()

    result = df.copy()

    if course_id is not None and "course_id" in result.columns:
        result = result[
            result["course_id"].astype(str) == str(course_id)
        ]

    if priority is not None and "priority" in result.columns:
        result = result[
            result["priority"].astype(str).str.casefold()
            == str(priority).casefold()
        ]

    if source is not None and "source" in result.columns:
        result = result[
            result["source"].astype(str).str.casefold()
            == str(source).casefold()
        ]

    return result.reset_index(drop=True)


def get_recommendations_for_course(course_id, df=None):
    """Get all recommendations associated with one course."""
    if df is None:
        df = load_recommendations()

    if "course_id" not in df.columns:
        return df.iloc[0:0].copy()

    return df[df["course_id"].astype(str) == str(course_id)].copy()


def search_recommendations(search_text, df=None):
    """Search recommendation text across available columns."""
    if df is None:
        df = load_recommendations()

    if not search_text or not str(search_text).strip():
        return df.copy()

    search_text = str(search_text).strip()

    matches = df.astype(str).apply(
        lambda column: column.str.contains(
            search_text,
            case=False,
            regex=False,
            na=False,
        )
    )

    return df[matches.any(axis=1)].copy()


def main():
    """Print a recommendation summary and recommendation table."""
    df = load_recommendations()
    summary = get_recommendation_summary(df)

    print("RECOMMENDATION ENGINE")
    print("=" * 45)

    for metric, value in summary.items():
        print(f"{metric.replace('_', ' ').title()}: {value}")

    print("\nExisting recommendations:")
    print(df.to_string(index=False))

    print("\nPriority distribution:")
    if "priority" in df.columns:
        print(df["priority"].value_counts(dropna=False).to_string())
    else:
        print("No priority column is available.")


if __name__ == "__main__":
    main()
