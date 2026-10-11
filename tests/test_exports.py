"""Unit tests for Excel and Power BI export workflows."""

import pytest
import openpyxl
import pandas as pd
from pathlib import Path
from src.analytics import compute_kpis, get_department_kpis, get_course_kpis, get_monthly_completion_trends
from src.data_generator import generate_clean_dataset
from src.excel_export import generate_excel_workbook
from src.power_bi_export import export_power_bi_datasets


@pytest.fixture
def sample_dataset():
    """Generate a clean mini dataset for export tests."""
    return generate_clean_dataset(num_records=50, seed=42)


def test_excel_workbook_generation_and_sheets(sample_dataset, tmp_path):
    """Verify Excel workbook is created with all 6 required worksheets."""
    df = sample_dataset
    kpis = compute_kpis(df, as_of_date="2026-10-15")
    dept_df = get_department_kpis(df, as_of_date="2026-10-15")
    course_df = get_course_kpis(df, as_of_date="2026-10-15")
    dq_summary = {
        "total_records": 50, "valid_records": 50, "flagged_records": 0,
        "duplicates": 0, "missing_fields": 0, "date_errors": 0, "score_errors": 0
    }
    flagged_df = pd.DataFrame()

    out_file = generate_excel_workbook(
        clean_df=df,
        kpis=kpis,
        dept_df=dept_df,
        course_df=course_df,
        dq_summary=dq_summary,
        flagged_df=flagged_df,
        output_filename="test_report.xlsx"
    )

    assert out_file.exists()

    # Load with openpyxl and inspect sheets
    wb = openpyxl.load_workbook(out_file)
    expected_sheets = [
        "Executive Summary",
        "Training Records",
        "Department KPIs",
        "Course KPIs",
        "Data Quality Report",
        "Data Dictionary"
    ]
    for s in expected_sheets:
        assert s in wb.sheetnames, f"Missing sheet: {s}"

    # Verify Executive Summary title cell
    ws_exec = wb["Executive Summary"]
    assert "TrainOps" in str(ws_exec["A1"].value)


def test_power_bi_csv_export_package(sample_dataset, tmp_path):
    """Verify Power BI export creates all 5 clean CSVs with stable schemas."""
    df = sample_dataset
    dept_df = get_department_kpis(df, as_of_date="2026-10-15")
    course_df = get_course_kpis(df, as_of_date="2026-10-15")
    trends_df = get_monthly_completion_trends(df)
    dq_summary = {"total_records": 50, "valid_records": 50}

    exported = export_power_bi_datasets(
        clean_df=df,
        dept_df=dept_df,
        course_df=course_df,
        monthly_trends_df=trends_df,
        dq_summary=dq_summary,
        export_dir=tmp_path
    )

    assert "training_records_clean" in exported
    assert "department_kpis" in exported
    assert "course_kpis" in exported
    assert "monthly_training_trends" in exported
    assert "data_quality_summary" in exported

    # Verify clean CSV is readable
    clean_csv_df = pd.read_csv(exported["training_records_clean"])
    assert len(clean_csv_df) == len(df)
    assert "employee_id" in clean_csv_df.columns
