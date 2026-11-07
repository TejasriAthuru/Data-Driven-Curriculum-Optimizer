
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

REQUIRED_COLUMNS = {
    "student_course_performance.csv": [
        "student_id",
        "course_id",
        "attendance_percentage",
        "overall_assessment_percentage",
        "risk_indicator",
    ],
    "student_performance_analysis.csv": [
        "student_id",
        "student_name",
        "average_assessment_score",
        "average_attendance",
        "performance_category",
        "risk_status",
    ],
    "course_summary.csv": [
        "course_id",
        "course_name",
        "average_attendance",
        "average_assessment_score",
    ],
    "learning_outcome_analysis_final.csv": [
        "course_id",
        "lo_id",
        "target_attainment",
        "calculated_attainment",
        "attainment_status",
    ],
    "final_recommendations.csv": [
        "recommendation_id",
        "source",
        "issue",
        "recommendation",
        "priority",
    ],
}


def inspect_csv(file_path):
    """Check one CSV for readability, missing values and duplicates."""
    result = {
        "file": file_path.name,
        "status": "PASS",
        "rows": 0,
        "columns": 0,
        "missing_cells": 0,
        "duplicate_rows": 0,
        "issues": [],
    }

    try:
        df = pd.read_csv(file_path)
    except Exception as exc:
        result["status"] = "FAIL"
        result["issues"].append(f"Unable to read CSV: {exc}")
        return result

    result["rows"] = len(df)
    result["columns"] = len(df.columns)
    result["missing_cells"] = int(df.isna().sum().sum())
    result["duplicate_rows"] = int(df.duplicated().sum())

    if df.empty:
        result["issues"].append("Dataset contains no data rows.")

    if len(df.columns) == 0:
        result["issues"].append("Dataset contains no columns.")

    required = REQUIRED_COLUMNS.get(file_path.name, [])
    missing_columns = [
        column for column in required if column not in df.columns
    ]

    if missing_columns:
        result["issues"].append(
            "Missing required columns: " + ", ".join(missing_columns)
        )

    if result["missing_cells"] > 0:
        result["issues"].append(
            f"{result['missing_cells']} missing cell(s) detected."
        )

    if result["duplicate_rows"] > 0:
        result["issues"].append(
            f"{result['duplicate_rows']} duplicate row(s) detected."
        )

    if result["issues"]:
        result["status"] = "WARNING"

    return result


def run_quality_checks(directory=PROCESSED_DATA_DIR):
    """Inspect all CSV files in the selected directory."""
    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(
            f"Dataset directory does not exist: {directory}"
        )

    files = sorted(directory.glob("*.csv"))
    results = [inspect_csv(file_path) for file_path in files]

    return results


def print_quality_report(results, directory=PROCESSED_DATA_DIR):
    """Print a readable quality-check report."""
    print("DATA QUALITY CHECK")
    print("=" * 55)
    print(f"Directory: {directory}")

    if not results:
        print("No CSV files found.")
        return

    for result in results:
        print(f"\nDataset: {result['file']}")
        print(f"Status: {result['status']}")
        print(f"Rows: {result['rows']}")
        print(f"Columns: {result['columns']}")
        print(f"Missing cells: {result['missing_cells']}")
        print(f"Duplicate rows: {result['duplicate_rows']}")

        for issue in result["issues"]:
            print(f"  - {issue}")

    passed = sum(result["status"] == "PASS" for result in results)
    warnings = sum(result["status"] == "WARNING" for result in results)
    failed = sum(result["status"] == "FAIL" for result in results)

    print("\n" + "=" * 55)
    print(f"Files checked: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Warnings: {warnings}")
    print(f"Failed: {failed}")


def export_quality_report(results, output_path=None):
    """Save the quality-check results to a CSV report."""
    if output_path is None:
        output_path = PROJECT_ROOT / "reports" / "data_quality_report.csv"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    flattened = []

    for result in results:
        flattened.append({
            "file": result["file"],
            "status": result["status"],
            "rows": result["rows"],
            "columns": result["columns"],
            "missing_cells": result["missing_cells"],
            "duplicate_rows": result["duplicate_rows"],
            "issues": "; ".join(result["issues"]),
        })

    pd.DataFrame(flattened).to_csv(output_path, index=False)
    return output_path


def main():
    results = run_quality_checks()
    print_quality_report(results)

    if results:
        output_path = export_quality_report(results)
        print(f"\nQuality report saved to: {output_path}")


if __name__ == "__main__":
    main()
