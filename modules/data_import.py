
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

# Expected columns for known project datasets.
EXPECTED_COLUMNS = {
    "student_course_performance.csv": [
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
        "risk_indicator",
    ],
    "student_performance_analysis.csv": [
        "student_id",
        "student_name",
        "average_assessment_score",
        "average_attendance",
        "average_feedback_rating",
        "courses_taken",
        "courses_at_risk",
        "performance_category",
        "risk_status",
    ],
    "course_summary.csv": [
        "course_id",
        "course_name",
        "credits",
        "department_id",
        "faculty_id",
        "semester",
        "average_attendance",
        "average_assessment_score",
        "average_feedback_rating",
        "students_enrolled",
        "students_at_risk",
    ],
    "learning_outcome_analysis_final.csv": [
        "course_id",
        "lo_id",
        "lo_code",
        "lo_description",
        "target_attainment",
        "observed_course_performance",
        "course_name",
        "department_id",
        "calculated_attainment",
        "attainment_gap",
        "attainment_status",
        "priority",
    ],
}


def validate_dataframe(df, expected_columns=None):
    """Validate the structure and basic quality of an imported DataFrame."""
    issues = []

    if df is None:
        return False, ["No dataset was provided."]

    if df.empty:
        issues.append("The uploaded dataset contains no data rows.")

    if len(df.columns) == 0:
        issues.append("The dataset has no columns.")

    if df.columns.duplicated().any():
        issues.append("Duplicate column names were found.")

    blank_columns = [
        str(column)
        for column in df.columns
        if not str(column).strip()
    ]
    if blank_columns:
        issues.append("One or more column names are blank.")

    if expected_columns:
        missing = [
            column for column in expected_columns
            if column not in df.columns
        ]
        if missing:
            issues.append(
                "Missing required columns: " + ", ".join(missing)
            )

    if df.isna().all(axis=1).any():
        issues.append("One or more rows are completely empty.")

    return len(issues) == 0, issues


def read_csv_file(file_path):
    """Read a CSV file and return its DataFrame."""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return pd.read_csv(file_path)


def preview_csv(file_path, rows=10):
    """Return the first few rows of a CSV file."""
    df = read_csv_file(file_path)
    return df.head(rows)


def get_expected_columns(file_name):
    """Return expected columns for a known dataset, if defined."""
    return EXPECTED_COLUMNS.get(Path(file_name).name)


def validate_csv_file(file_path):
    """Validate a CSV file against its known schema, when available."""
    file_path = Path(file_path)

    try:
        df = read_csv_file(file_path)
    except Exception as exc:
        return {
            "valid": False,
            "file_name": file_path.name,
            "issues": [f"Unable to read CSV: {exc}"],
            "rows": 0,
            "columns": 0,
        }

    valid, issues = validate_dataframe(
        df,
        expected_columns=get_expected_columns(file_path.name),
    )

    return {
        "valid": valid,
        "file_name": file_path.name,
        "issues": issues,
        "rows": len(df),
        "columns": len(df.columns),
    }


def save_uploaded_dataframe(
    df,
    file_name,
    destination_dir=None,
    overwrite=False,
):
    """
    Save an imported DataFrame as CSV.

    By default, files are saved to data/raw.
    Existing files are not overwritten unless overwrite=True.
    """
    if df is None:
        raise ValueError("No dataset was provided.")

    file_name = Path(file_name).name

    if not file_name.lower().endswith(".csv"):
        raise ValueError("Only CSV files are supported.")

    valid, issues = validate_dataframe(
        df,
        expected_columns=get_expected_columns(file_name),
    )

    if not valid:
        raise ValueError("Dataset validation failed: " + "; ".join(issues))

    destination_dir = (
        Path(destination_dir)
        if destination_dir is not None
        else RAW_DATA_DIR
    )
    destination_dir.mkdir(parents=True, exist_ok=True)

    output_path = destination_dir / file_name

    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"{output_path.name} already exists. "
            "Choose another filename or explicitly allow overwrite."
        )

    df.to_csv(output_path, index=False)
    return output_path


def import_csv_file(
    source_path,
    destination_dir=None,
    overwrite=False,
):
    """Read, validate, and import an existing CSV file."""
    source_path = Path(source_path)
    df = read_csv_file(source_path)

    return save_uploaded_dataframe(
        df=df,
        file_name=source_path.name,
        destination_dir=destination_dir,
        overwrite=overwrite,
    )


def list_csv_files(directory=None):
    """List CSV files in the selected directory."""
    directory = Path(directory) if directory else RAW_DATA_DIR

    if not directory.exists():
        return []

    return sorted(
        path.name for path in directory.glob("*.csv")
        if path.is_file()
    )


if __name__ == "__main__":
    print("Data Import Module")
    print("=" * 40)
    print(f"Raw data directory: {RAW_DATA_DIR}")
    print(f"Processed data directory: {PROCESSED_DATA_DIR}")

    files = list_csv_files()

    if files:
        print("\nCSV files available in data/raw:")
        for file_name in files:
            print(f"- {file_name}")
    else:
        print("\nNo CSV files currently exist in data/raw.")
        print("You can import CSV files using import_csv_file().")
