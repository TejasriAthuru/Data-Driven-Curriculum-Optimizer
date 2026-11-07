
from pathlib import Path
from datetime import datetime

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"


def load_report_data(file_name):
    """Load a processed CSV dataset for reporting."""
    safe_name = Path(file_name).name

    if safe_name != file_name or not safe_name.lower().endswith(".csv"):
        raise ValueError("Provide a valid CSV filename.")

    file_path = PROCESSED_DATA_DIR / safe_name

    if not file_path.is_file():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    return pd.read_csv(file_path)


def export_csv_report(df, output_name):
    """Export a DataFrame as a CSV report."""
    output_name = Path(output_name).name

    if not output_name.lower().endswith(".csv"):
        raise ValueError("CSV report filename must end with .csv.")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / output_name

    df.to_csv(output_path, index=False)
    return output_path


def generate_student_performance_report():
    """Export the student performance analysis."""
    df = load_report_data("student_performance_analysis.csv")
    return export_csv_report(df, "student_performance_report.csv")


def generate_curriculum_report():
    """Export curriculum effectiveness data."""
    df = load_report_data("curriculum_effectiveness.csv")
    return export_csv_report(df, "curriculum_effectiveness_report.csv")


def generate_recommendations_report():
    """Export final recommendations."""
    df = load_report_data("final_recommendations.csv")
    return export_csv_report(df, "recommendations_report.csv")


def generate_learning_outcomes_report():
    """Export learning-outcome analysis."""
    df = load_report_data("learning_outcome_analysis_final.csv")
    return export_csv_report(df, "learning_outcomes_report.csv")


def generate_pdf_report():
    """Generate a PDF summary of available project analysis."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            PageBreak,
        )
    except ImportError as exc:
        raise ImportError(
            "PDF generation requires reportlab. "
            "Install it with: python -m pip install reportlab"
        ) from exc

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = REPORTS_DIR / f"academic_analysis_{timestamp}.pdf"

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=20,
            leading=26,
            spaceAfter=12,
        )
    )

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        rightMargin=0.45 * inch,
        leftMargin=0.45 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    story = [
        Paragraph("Data-Driven Curriculum Optimizer", styles["ReportTitle"]),
        Paragraph(
            f"Academic Analysis Report | Generated {datetime.now():%d %B %Y, %H:%M}",
            styles["Normal"],
        ),
        Spacer(1, 18),
    ]

    report_sections = [
        (
            "Student Performance",
            "student_performance_analysis.csv",
            [
                "student_id",
                "student_name",
                "average_assessment_score",
                "average_attendance",
                "performance_category",
                "risk_status",
            ],
        ),
        (
            "Curriculum Effectiveness",
            "curriculum_effectiveness.csv",
            [
                "course_id",
                "course_name",
                "average_assessment_score",
                "average_attendance",
                "effectiveness_score",
                "effectiveness_status",
            ],
        ),
        (
            "Learning Outcome Analysis",
            "learning_outcome_analysis_final.csv",
            [
                "course_id",
                "lo_code",
                "course_name",
                "target_attainment",
                "calculated_attainment",
                "attainment_status",
                "priority",
            ],
        ),
        (
            "Recommendations",
            "final_recommendations.csv",
            [
                "source",
                "course_id",
                "course_name",
                "issue",
                "priority",
                "recommendation",
            ],
        ),
    ]

    for index, (section_title, file_name, preferred_columns) in enumerate(
        report_sections
    ):
        try:
            df = load_report_data(file_name)
        except FileNotFoundError:
            story.append(Paragraph(section_title, styles["Heading2"]))
            story.append(
                Paragraph(f"Dataset unavailable: {file_name}", styles["Normal"])
            )
            story.append(Spacer(1, 12))
            continue

        story.append(Paragraph(section_title, styles["Heading2"]))

        columns = [column for column in preferred_columns if column in df.columns]
        if not columns:
            columns = df.columns.tolist()[:6]

        table_df = df[columns].copy()

        # Keep the PDF readable for larger datasets.
        max_rows = 25
        displayed_df = table_df.head(max_rows)

        table_data = [columns]
        for _, row in displayed_df.iterrows():
            table_data.append([
                "" if pd.isna(value) else str(value)
                for value in row.tolist()
            ])

        available_width = landscape(A4)[0] - 0.9 * inch
        column_width = available_width / max(len(columns), 1)

        table = Table(
            table_data,
            colWidths=[column_width] * len(columns),
            repeatRows=1,
        )
        table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#23415A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("LEADING", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#F1F5F9"),
                ]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )

        story.append(table)

        if len(table_df) > max_rows:
            story.append(
                Paragraph(
                    f"Showing {max_rows} of {len(table_df)} rows. "
                    "The full dataset is available in the CSV export.",
                    styles["Italic"],
                )
            )

        story.append(Spacer(1, 16))

        if index < len(report_sections) - 1:
            story.append(PageBreak())

    document.build(story)
    return output_path


def main():
    """Generate CSV and PDF reports."""
    print("REPORT GENERATOR")
    print("=" * 45)

    generators = [
        ("Student performance", generate_student_performance_report),
        ("Curriculum effectiveness", generate_curriculum_report),
        ("Recommendations", generate_recommendations_report),
        ("Learning outcomes", generate_learning_outcomes_report),
    ]

    for label, generator in generators:
        try:
            path = generator()
            print(f"{label}: {path}")
        except Exception as exc:
            print(f"{label} report failed: {exc}")

    try:
        pdf_path = generate_pdf_report()
        print(f"PDF report: {pdf_path}")
    except Exception as exc:
        print(f"PDF report failed: {exc}")


if __name__ == "__main__":
    main()
