
from pathlib import Path

import pandas as pd

try:
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
STUDENT_COURSE_FILE = PROCESSED_DATA_DIR / "student_course_performance.csv"


def load_student_course_data():
    """Load student-course performance data."""
    if not STUDENT_COURSE_FILE.exists():
        raise FileNotFoundError(
            f"Student-course dataset not found: {STUDENT_COURSE_FILE}"
        )

    return pd.read_csv(STUDENT_COURSE_FILE)


def summarize_risk_indicators(df=None):
    """Summarize the risk_indicator values already present in the dataset."""
    if df is None:
        df = load_student_course_data()

    if "risk_indicator" not in df.columns:
        raise ValueError("Required column 'risk_indicator' is missing.")

    summary = (
        df["risk_indicator"]
        .fillna("Unknown")
        .astype(str)
        .value_counts()
        .rename_axis("risk_indicator")
        .reset_index(name="record_count")
    )

    summary["percentage"] = (
        summary["record_count"] / max(len(df), 1) * 100
    ).round(2)

    return summary


def prepare_training_data(df=None):
    """
    Prepare features and labels for a risk-classification model.

    The existing risk_indicator column is used as the target label.
    This means the model learns to reproduce that existing label;
    it does not independently prove future student risk.
    """
    if df is None:
        df = load_student_course_data()

    required = [
        "risk_indicator",
        "attendance_percentage",
        "overall_assessment_percentage",
    ]
    missing = [column for column in required if column not in df.columns]

    if missing:
        raise ValueError(
            "Missing required training columns: " + ", ".join(missing)
        )

    data = df.dropna(subset=["risk_indicator"]).copy()

    feature_columns = [
        column
        for column in [
            "attendance_percentage",
            "overall_assessment_percentage",
            "average_assessment_percentage",
            "feedback_rating",
            "classes_conducted",
            "classes_attended",
            "academic_year",
            "semester",
            "enrollment_status",
        ]
        if column in data.columns
    ]

    if not feature_columns:
        raise ValueError("No usable feature columns are available.")

    X = data[feature_columns].copy()
    y = data["risk_indicator"].astype(str)

    numeric_columns = X.select_dtypes(
        include=["number", "bool"]
    ).columns.tolist()
    categorical_columns = [
        column for column in feature_columns
        if column not in numeric_columns
    ]

    return X, y, numeric_columns, categorical_columns


def train_risk_model(df=None, test_size=0.25, random_state=42):
    """Train and evaluate a risk-classification model."""
    if not SKLEARN_AVAILABLE:
        raise ImportError(
            "scikit-learn is required. Install it with: "
            "python -m pip install scikit-learn"
        )

    X, y, numeric_columns, categorical_columns = prepare_training_data(df)

    if len(y) < 8:
        raise ValueError(
            "Not enough records to train and evaluate a meaningful model."
        )

    class_counts = y.value_counts()
    if len(class_counts) < 2:
        raise ValueError(
            "Training requires at least two different risk_indicator classes."
        )

    # Stratification preserves class proportions when possible.
    stratify = y if class_counts.min() >= 2 else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )

    transformers = []

    if numeric_columns:
        numeric_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        transformers.append(
            ("numeric", numeric_pipeline, numeric_columns)
        )

    if categorical_columns:
        categorical_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(handle_unknown="ignore")),
            ]
        )
        transformers.append(
            ("categorical", categorical_pipeline, categorical_columns)
        )

    preprocessing = ColumnTransformer(transformers=transformers)

    model = Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    )

    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    results = {
        "model": model,
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "classification_report": classification_report(
            y_test,
            predictions,
            zero_division=0,
        ),
        "training_records": len(X_train),
        "testing_records": len(X_test),
        "class_distribution": y.value_counts().to_dict(),
        "features": X.columns.tolist(),
        "target": "risk_indicator",
    }

    return results


def main():
    """Print risk summary and optionally evaluate a model."""
    df = load_student_course_data()

    print("PREDICTIVE ANALYSIS")
    print("=" * 50)
    print(f"Student-course records: {len(df)}")

    print("\nExisting risk-indicator distribution:")
    print(summarize_risk_indicators(df).to_string(index=False))

    if not SKLEARN_AVAILABLE:
        print(
            "\nModel training skipped: scikit-learn is not installed."
        )
        print("Install it using: python -m pip install scikit-learn")
        return

    try:
        results = train_risk_model(df)

        print("\nModel evaluation")
        print("-" * 30)
        print(f"Training records: {results['training_records']}")
        print(f"Testing records: {results['testing_records']}")
        print(f"Accuracy: {results['accuracy']:.2%}")
        print("\nClassification report:")
        print(results["classification_report"])
        print(
            "\nNote: evaluation predicts the existing risk_indicator "
            "label. It is not proof of future risk prediction."
        )

    except (ValueError, ImportError) as exc:
        print(f"\nModel training skipped: {exc}")


if __name__ == "__main__":
    main()
