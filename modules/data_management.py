
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"


def get_data_directories():
    """Return the configured data directories."""
    return {
        "project": PROJECT_ROOT,
        "data": DATA_DIR,
        "raw": RAW_DATA_DIR,
        "processed": PROCESSED_DATA_DIR,
    }


def list_datasets(directory=None):
    """List CSV datasets available in a directory."""
    directory = Path(directory) if directory else PROCESSED_DATA_DIR

    if not directory.exists():
        return []

    return sorted(
        path.name
        for path in directory.glob("*.csv")
        if path.is_file()
    )


def load_dataset(file_name, directory=None):
    """Load a CSV dataset by filename."""
    directory = Path(directory) if directory else PROCESSED_DATA_DIR

    # Only allow a filename, not an arbitrary path.
    safe_name = Path(file_name).name
    if safe_name != file_name or not safe_name.lower().endswith(".csv"):
        raise ValueError("Provide a valid CSV filename only.")

    file_path = directory / safe_name

    if not file_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    return pd.read_csv(file_path)


def get_dataset_summary(file_name, directory=None):
    """Return basic information about a dataset."""
    df = load_dataset(file_name, directory)

    return {
        "file_name": file_name,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": df.columns.tolist(),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_usage_bytes": int(df.memory_usage(deep=True).sum()),
    }


def search_dataset(file_name, search_text, directory=None):
    """Find rows containing text in any column."""
    df = load_dataset(file_name, directory)

    if search_text is None or not str(search_text).strip():
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


def filter_dataset(file_name, column, value, directory=None):
    """Filter a dataset by an exact column value."""
    df = load_dataset(file_name, directory)

    if column not in df.columns:
        raise ValueError(
            f"Column '{column}' not found. "
            f"Available columns: {', '.join(map(str, df.columns))}"
        )

    return df[
        df[column].astype(str).str.casefold()
        == str(value).casefold()
    ].copy()


def export_dataset(
    file_name,
    output_path,
    directory=None,
    overwrite=False,
):
    """Export a dataset to another CSV file."""
    df = load_dataset(file_name, directory)
    output_path = Path(output_path)

    if output_path.suffix.lower() != ".csv":
        raise ValueError("Export destination must have a .csv extension.")

    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"{output_path} already exists. "
            "Set overwrite=True to replace it."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    return output_path


def main():
    """Display an inventory of the project's datasets."""
    print("DATA MANAGEMENT")
    print("=" * 60)

    for label, directory in [
        ("Raw datasets", RAW_DATA_DIR),
        ("Processed datasets", PROCESSED_DATA_DIR),
    ]:
        print(f"\n{label}: {directory}")

        files = list_datasets(directory)

        if not files:
            print("  No CSV files found.")
            continue

        for file_name in files:
            try:
                summary = get_dataset_summary(file_name, directory)
                print(
                    f"  {file_name}: "
                    f"{summary['rows']} rows, "
                    f"{summary['columns']} columns, "
                    f"{summary['missing_cells']} missing cells"
                )
            except Exception as exc:
                print(f"  {file_name}: Could not inspect ({exc})")


if __name__ == "__main__":
    main()
