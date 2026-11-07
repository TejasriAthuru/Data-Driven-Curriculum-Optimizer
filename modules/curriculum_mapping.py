
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def load_learning_outcomes(final=True):
    """Load the available learning-outcome analysis dataset."""
    file_name = (
        "learning_outcome_analysis_final.csv"
        if final
        else "learning_outcome_analysis.csv"
    )
    file_path = PROCESSED_DATA_DIR / file_name

    if not file_path.exists():
        raise FileNotFoundError(
            f"Learning-outcome dataset not found: {file_path}"
        )

    return pd.read_csv(file_path)


def calculate_attainment_gap(df):
    """Calculate target minus observed attainment where possible."""
    result = df.copy()

    if "target_attainment" not in result.columns:
        raise ValueError("Missing required column: target_attainment")

    observed_column = next(
        (
            column
            for column in [
                "calculated_attainment",
                "observed_course_performance",
                "attainment_percentage",
            ]
            if column in result.columns
        ),
        None,
    )

    if observed_column is None:
        raise ValueError(
            "No observed attainment column was found."
        )

    target = pd.to_numeric(result["target_attainment"], errors="coerce")
    observed = pd.to_numeric(result[observed_column], errors="coerce")

    # Positive values mean the observed result is below the target.
    result["calculated_gap"] = target - observed
    result["observed_attainment_used"] = observed_column

    return result


def get_mapping_summary(df=None):
    """Summarize course-to-learning-outcome mapping and attainment."""
    if df is None:
        df = load_learning_outcomes()

    if df.empty:
        return {
            "total_mappings": 0,
            "unique_courses": 0,
            "unique_learning_outcomes": 0,
            "average_attainment": 0.0,
            "average_target_attainment": 0.0,
            "outcomes_below_target": 0,
        }

    def numeric_mean(column):
        if column not in df.columns:
            return 0.0

        values = pd.to_numeric(df[column], errors="coerce")
        return round(float(values.mean()), 2) if values.notna().any() else 0.0

    observed_column = next(
        (
            column
            for column in [
                "calculated_attainment",
                "attainment_percentage",
                "observed_course_performance",
            ]
            if column in df.columns
        ),
        None,
    )

    if observed_column and "target_attainment" in df.columns:
        observed = pd.to_numeric(df[observed_column], errors="coerce")
        target = pd.to_numeric(df["target_attainment"], errors="coerce")
        below_target = int((observed < target).fillna(False).sum())
        average_attainment = numeric_mean(observed_column)
    else:
        below_target = 0
        average_attainment = 0.0

    return {
        "total_mappings": int(len(df)),
        "unique_courses": int(
            df["course_id"].nunique() if "course_id" in df.columns else 0
        ),
        "unique_learning_outcomes": int(
            df["lo_id"].nunique() if "lo_id" in df.columns else 0
        ),
        "average_attainment": average_attainment,
        "average_target_attainment": numeric_mean("target_attainment"),
        "outcomes_below_target": below_target,
    }


def get_outcomes_below_target(df=None):
    """Return outcome mappings where observed attainment is below target."""
    if df is None:
        df = load_learning_outcomes()

    if "target_attainment" not in df.columns:
        return df.iloc[0:0].copy()

    observed_column = next(
        (
            column
            for column in [
                "calculated_attainment",
                "attainment_percentage",
                "observed_course_performance",
            ]
            if column in df.columns
        ),
        None,
    )

    if observed_column is None:
        return df.iloc[0:0].copy()

    observed = pd.to_numeric(df[observed_column], errors="coerce")
    target = pd.to_numeric(df["target_attainment"], errors="coerce")

    return df[(observed < target).fillna(False)].copy()


def filter_learning_outcomes(
    df=None,
    course_id=None,
    attainment_status=None,
    maximum_attainment=None,
):
    """Filter learning-outcome records by course and attainment."""
    if df is None:
        df = load_learning_outcomes()

    result = df.copy()

    if course_id is not None and "course_id" in result.columns:
        result = result[
            result["course_id"].astype(str) == str(course_id)
        ]

    if (
        attainment_status is not None
        and "attainment_status" in result.columns
    ):
        result = result[
            result["attainment_status"].astype(str).str.casefold()
            == str(attainment_status).casefold()
        ]

    attainment_column = next(
        (
            column
            for column in [
                "calculated_attainment",
                "attainment_percentage",
                "observed_course_performance",
            ]
            if column in result.columns
        ),
        None,
    )

    if maximum_attainment is not None and attainment_column:
        values = pd.to_numeric(
            result[attainment_column], errors="coerce"
        )
        result = result[values <= maximum_attainment]

    return result.reset_index(drop=True)


def main():
    """Print the learning-outcome mapping report."""
    df = load_learning_outcomes()
    summary = get_mapping_summary(df)

    print("CURRICULUM AND LEARNING-OUTCOME MAPPING")
    print("=" * 50)

    for metric, value in summary.items():
        print(f"{metric.replace('_', ' ').title()}: {value}")

    print("\nLearning-outcome records:")
    print(df.to_string(index=False))

    below_target = get_outcomes_below_target(df)
    print(f"\nOutcomes below target: {len(below_target)}")

    if not below_target.empty:
        print(below_target.to_string(index=False))


if __name__ == "__main__":
    main()
