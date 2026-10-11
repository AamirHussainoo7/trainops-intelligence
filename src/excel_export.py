"""Excel Workbook Generation Engine for TrainOps Intelligence.

Generates executive-ready, multi-worksheet .xlsx workbooks utilizing openpyxl
with corporate typography, frozen panes, formula reconciliation, auto-filters,
and dedicated data dictionary and data quality audit sheets.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import pandas as pd
from src.config import DATA_EXPORT_DIR

# Enterprise Palette
NAVY_PRIMARY = "1B365D"
BLUE_ACCENT = "006699"
ICE_BLUE_BG = "F0F4F8"
WHITE = "FFFFFF"
GRAY_TEXT = "555555"
LIGHT_GRAY_BORDER = "D1D5DB"
SUCCESS_GREEN_BG = "E6F4EA"
WARNING_AMBER_BG = "FEF7E0"

# Styling Presets
FONT_TITLE = Font(name="Calibri", size=16, bold=True, color=NAVY_PRIMARY)
FONT_SECTION = Font(name="Calibri", size=13, bold=True, color=NAVY_PRIMARY)
FONT_HEADER = Font(name="Calibri", size=11, bold=True, color=WHITE)
FONT_SUBHEADER = Font(name="Calibri", size=11, bold=True, color=NAVY_PRIMARY)
FONT_BODY = Font(name="Calibri", size=10, bold=False, color="1F2937")
FONT_BOLD_BODY = Font(name="Calibri", size=10, bold=True, color="1F2937")
FONT_KPI_VAL = Font(name="Calibri", size=14, bold=True, color=NAVY_PRIMARY)
FONT_MUTED = Font(name="Calibri", size=9, italic=True, color=GRAY_TEXT)

FILL_NAVY = PatternFill(start_color=NAVY_PRIMARY, end_color=NAVY_PRIMARY, fill_type="solid")
FILL_ACCENT = PatternFill(start_color=BLUE_ACCENT, end_color=BLUE_ACCENT, fill_type="solid")
FILL_ICE_BLUE = PatternFill(start_color=ICE_BLUE_BG, end_color=ICE_BLUE_BG, fill_type="solid")
FILL_SUCCESS = PatternFill(start_color=SUCCESS_GREEN_BG, end_color=SUCCESS_GREEN_BG, fill_type="solid")

THIN_BORDER_SIDE = Side(border_style="thin", color=LIGHT_GRAY_BORDER)
BOX_BORDER = Border(left=THIN_BORDER_SIDE, right=THIN_BORDER_SIDE, top=THIN_BORDER_SIDE, bottom=THIN_BORDER_SIDE)
BOTTOM_DOUBLE = Border(
    left=THIN_BORDER_SIDE, right=THIN_BORDER_SIDE, top=THIN_BORDER_SIDE,
    bottom=Side(border_style="double", color=NAVY_PRIMARY)
)


def _auto_fit_columns(ws, min_width: int = 12, max_width: int = 50) -> None:
    """Adjust worksheet column widths to fit content comfortably."""
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            val_str = str(cell.value or "")
            if "\n" in val_str:
                val_str = max(val_str.split("\n"), key=len)
            max_len = max(max_len, len(val_str))
        ws.column_dimensions[col_letter].width = min(max_width, max(min_width, max_len + 3))


def generate_excel_workbook(
    clean_df: pd.DataFrame,
    kpis: Dict[str, Any],
    dept_df: pd.DataFrame,
    course_df: pd.DataFrame,
    dq_summary: Dict[str, Any],
    flagged_df: pd.DataFrame,
    output_filename: Optional[str] = None
) -> Path:
    """Generate professional corporate multi-sheet Excel workbook.
    
    Worksheets created:
    1. Executive Summary
    2. Training Records
    3. Department KPIs
    4. Course KPIs
    5. Data Quality Report
    6. Data Dictionary
    """
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = output_filename or f"TrainOps_Intelligence_Report_{timestamp_str}.xlsx"
    export_path = DATA_EXPORT_DIR / file_name

    # ==========================================
    # 1. Executive Summary Worksheet
    # ==========================================
    ws_exec = wb.create_sheet(title="Executive Summary")
    ws_exec.views.sheetView[0].showGridLines = True

    # Title Banner
    ws_exec.merge_cells("A1:G1")
    title_cell = ws_exec["A1"]
    title_cell.value = "TrainOps Intelligence — Training Operations Executive Summary"
    title_cell.font = FONT_TITLE
    title_cell.alignment = Alignment(vertical="center")
    ws_exec.row_dimensions[1].height = 32

    ws_exec["A2"].value = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  As-of Reference Date: {kpis.get('as_of_date', 'N/A')}"
    ws_exec["A2"].font = FONT_MUTED

    # Section 1: KPI Scorecard Block
    ws_exec["A4"].value = "1. Operational KPI Scorecard"
    ws_exec["A4"].font = FONT_SECTION

    kpi_headers = ["Metric Name", "Value", "Benchmark / Target", "Metric Definition"]
    for col_idx, h in enumerate(kpi_headers, start=1):
        cell = ws_exec.cell(row=5, column=col_idx, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_NAVY
        cell.alignment = Alignment(horizontal="left", vertical="center")
        cell.border = BOX_BORDER
    ws_exec.row_dimensions[5].height = 24

    kpi_rows = [
        ("Total Training Assignments", kpis.get("total_assignments", 0), "—", "Total course enrollments in scope"),
        ("Unique Employees Assigned", kpis.get("unique_employees", 0), "—", "Distinct headcount participating in training"),
        ("Training Completion Rate", (kpis.get("completion_rate_pct", 0) / 100.0), ">= 80.0%", "Completed assignments / Total eligible assignments"),
        ("Attendance Rate", (kpis.get("attendance_rate_pct", 0) / 100.0), ">= 90.0%", "Attended sessions / Tracked synchronous sessions"),
        ("Average Assessment Score", kpis.get("avg_assessment_score", "N/A"), ">= 80.0", "Mean score of valid completed assessments (0–100)"),
        ("Overdue Training Assignments", kpis.get("overdue_assignments", 0), "0", "Uncompleted assignments past due date"),
        ("Mandatory Training Completion Rate", (kpis.get("mandatory_completion_rate_pct", 0) / 100.0), "100.0%", "Completed mandatory assignments / Total mandatory"),
        ("Total Completed Training Hours", kpis.get("total_completed_hours", 0.0), "—", "Sum of curriculum credit hours successfully finished"),
    ]

    for r_idx, (m_name, m_val, m_bench, m_def) in enumerate(kpi_rows, start=6):
        c1 = ws_exec.cell(row=r_idx, column=1, value=m_name)
        c2 = ws_exec.cell(row=r_idx, column=2, value=m_val)
        c3 = ws_exec.cell(row=r_idx, column=3, value=m_bench)
        c4 = ws_exec.cell(row=r_idx, column=4, value=m_def)

        for cell in [c1, c2, c3, c4]:
            cell.font = FONT_BODY
            cell.border = BOX_BORDER
            cell.alignment = Alignment(vertical="center")

        c1.font = FONT_BOLD_BODY
        # Number formats
        if isinstance(m_val, float) and ("Rate" in m_name):
            c2.number_format = "0.0%"
            c2.alignment = Alignment(horizontal="right", vertical="center")
        elif isinstance(m_val, int):
            c2.number_format = "#,##0"
            c2.alignment = Alignment(horizontal="right", vertical="center")
        elif isinstance(m_val, float):
            c2.number_format = "0.0"
            c2.alignment = Alignment(horizontal="right", vertical="center")

        ws_exec.row_dimensions[r_idx].height = 20

    # Section 2: Department Highlights Summary Table
    start_dept_r = 16
    ws_exec.cell(row=start_dept_r, column=1, value="2. Department Performance Snapshot").font = FONT_SECTION

    dept_summary_headers = ["Department", "Assignments", "Completed", "Completion %", "Mandatory %", "Overdue", "Avg Score"]
    for col_idx, h in enumerate(dept_summary_headers, start=1):
        cell = ws_exec.cell(row=start_dept_r + 1, column=col_idx, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_ACCENT
        cell.border = BOX_BORDER
        cell.alignment = Alignment(horizontal="left", vertical="center")

    if not dept_df.empty:
        for idx, row in dept_df.iterrows():
            curr_r = start_dept_r + 2 + idx
            r_dept = ws_exec.cell(row=curr_r, column=1, value=row.get("department"))
            r_tot = ws_exec.cell(row=curr_r, column=2, value=int(row.get("total_assignments", 0)))
            r_comp = ws_exec.cell(row=curr_r, column=3, value=int(row.get("completed_assignments", 0)))
            r_rate = ws_exec.cell(row=curr_r, column=4, value=float(row.get("completion_rate_pct", 0) / 100.0))
            r_mrate = ws_exec.cell(row=curr_r, column=5, value=float(row.get("mandatory_completion_rate_pct", 0) / 100.0))
            r_over = ws_exec.cell(row=curr_r, column=6, value=int(row.get("overdue_assignments", 0)))
            r_sc = ws_exec.cell(row=curr_r, column=7, value=row.get("avg_assessment_score"))

            for cell in [r_dept, r_tot, r_comp, r_rate, r_mrate, r_over, r_sc]:
                cell.font = FONT_BODY
                cell.border = BOX_BORDER
                cell.alignment = Alignment(vertical="center")

            r_tot.number_format = "#,##0"
            r_comp.number_format = "#,##0"
            r_rate.number_format = "0.0%"
            r_mrate.number_format = "0.0%"
            r_over.number_format = "#,##0"
            if isinstance(row.get("avg_assessment_score"), (int, float)):
                r_sc.number_format = "0.0"

    _auto_fit_columns(ws_exec)

    # ==========================================
    # 2. Training Records Worksheet
    # ==========================================
    ws_records = wb.create_sheet(title="Training Records")
    ws_records.views.sheetView[0].showGridLines = True
    ws_records.freeze_panes = "A2"

    rec_headers = list(clean_df.columns) if not clean_df.empty else ["record_id"]
    for c_idx, col_name in enumerate(rec_headers, start=1):
        cell = ws_records.cell(row=1, column=c_idx, value=col_name.replace("_", " ").title())
        cell.font = FONT_HEADER
        cell.fill = FILL_NAVY
        cell.border = BOX_BORDER
        cell.alignment = Alignment(horizontal="left", vertical="center")
    ws_records.row_dimensions[1].height = 24

    if not clean_df.empty:
        for r_idx, row in clean_df.iterrows():
            row_num = r_idx + 2
            for c_idx, col_name in enumerate(rec_headers, start=1):
                val = row[col_name]
                if pd.isna(val):
                    val = None
                cell = ws_records.cell(row=row_num, column=c_idx, value=val)
                cell.font = FONT_BODY
                cell.border = BOX_BORDER
                cell.alignment = Alignment(vertical="center")

                # Formatting
                if "score" in col_name and isinstance(val, (int, float)):
                    cell.number_format = "0.0"
                elif "hours" in col_name and isinstance(val, (int, float)):
                    cell.number_format = "0.0"

        ws_records.auto_filter.ref = f"A1:{get_column_letter(len(rec_headers))}{len(clean_df) + 1}"
    _auto_fit_columns(ws_records)

    # ==========================================
    # 3. Department KPIs Worksheet
    # ==========================================
    ws_dept = wb.create_sheet(title="Department KPIs")
    ws_dept.views.sheetView[0].showGridLines = True
    ws_dept.freeze_panes = "A2"

    dept_cols = list(dept_df.columns) if not dept_df.empty else ["department"]
    for c_idx, col_name in enumerate(dept_cols, start=1):
        cell = ws_dept.cell(row=1, column=c_idx, value=col_name.replace("_", " ").title())
        cell.font = FONT_HEADER
        cell.fill = FILL_NAVY
        cell.border = BOX_BORDER
        cell.alignment = Alignment(horizontal="left", vertical="center")
    ws_dept.row_dimensions[1].height = 24

    if not dept_df.empty:
        for r_idx, row in dept_df.iterrows():
            row_num = r_idx + 2
            for c_idx, col_name in enumerate(dept_cols, start=1):
                val = row[col_name]
                if pd.isna(val):
                    val = None
                cell = ws_dept.cell(row=row_num, column=c_idx, value=val)
                cell.font = FONT_BODY
                cell.border = BOX_BORDER
                cell.alignment = Alignment(vertical="center")

                if "_pct" in col_name and isinstance(val, (int, float)):
                    cell.value = val / 100.0
                    cell.number_format = "0.0%"
                elif isinstance(val, int):
                    cell.number_format = "#,##0"
                elif isinstance(val, float):
                    cell.number_format = "0.0"

        ws_dept.auto_filter.ref = f"A1:{get_column_letter(len(dept_cols))}{len(dept_df) + 1}"
    _auto_fit_columns(ws_dept)

    # ==========================================
    # 4. Course KPIs Worksheet
    # ==========================================
    ws_course = wb.create_sheet(title="Course KPIs")
    ws_course.views.sheetView[0].showGridLines = True
    ws_course.freeze_panes = "A2"

    course_cols = list(course_df.columns) if not course_df.empty else ["course_id"]
    for c_idx, col_name in enumerate(course_cols, start=1):
        cell = ws_course.cell(row=1, column=c_idx, value=col_name.replace("_", " ").title())
        cell.font = FONT_HEADER
        cell.fill = FILL_NAVY
        cell.border = BOX_BORDER
        cell.alignment = Alignment(horizontal="left", vertical="center")
    ws_course.row_dimensions[1].height = 24

    if not course_df.empty:
        for r_idx, row in course_df.iterrows():
            row_num = r_idx + 2
            for c_idx, col_name in enumerate(course_cols, start=1):
                val = row[col_name]
                if pd.isna(val):
                    val = None
                cell = ws_course.cell(row=row_num, column=c_idx, value=val)
                cell.font = FONT_BODY
                cell.border = BOX_BORDER
                cell.alignment = Alignment(vertical="center")

                if "_pct" in col_name and isinstance(val, (int, float)):
                    cell.value = val / 100.0
                    cell.number_format = "0.0%"
                elif isinstance(val, int):
                    cell.number_format = "#,##0"
                elif isinstance(val, float):
                    cell.number_format = "0.0"

        ws_course.auto_filter.ref = f"A1:{get_column_letter(len(course_cols))}{len(course_df) + 1}"
    _auto_fit_columns(ws_course)

    # ==========================================
    # 5. Data Quality Report Worksheet
    # ==========================================
    ws_dq = wb.create_sheet(title="Data Quality Report")
    ws_dq.views.sheetView[0].showGridLines = True

    ws_dq["A1"].value = "Data Quality & Ingestion Validation Audit"
    ws_dq["A1"].font = FONT_TITLE
    ws_dq.row_dimensions[1].height = 28

    ws_dq["A3"].value = "Validation Summary Metrics"
    ws_dq["A3"].font = FONT_SECTION

    dq_metric_headers = ["Metric", "Count", "Assessment Notes"]
    for c_idx, h in enumerate(dq_metric_headers, start=1):
        cell = ws_dq.cell(row=4, column=c_idx, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_NAVY
        cell.border = BOX_BORDER

    dq_summary_rows = [
        ("Total Records Evaluated", dq_summary.get("total_records", 0), "All rows received from ingestion source"),
        ("Clean Validated Records", dq_summary.get("valid_records", 0), "Passed validation rules or safely standardized"),
        ("Flagged Records Requiring Review", dq_summary.get("flagged_records", 0), "Excluded from KPI calculation pending review"),
        ("Duplicate Records Identified", dq_summary.get("duplicates", 0), "Duplicate record_id or assignment combination"),
        ("Missing Required Fields", dq_summary.get("missing_fields", 0), "Null employee, course, or date identifier"),
        ("Date Relationship Errors", dq_summary.get("date_errors", 0), "Completion before assigned or unparseable date"),
        ("Assessment Score Errors", dq_summary.get("score_errors", 0), "Score < 0, score > 100, or non-numeric value"),
    ]

    for r_idx, (m, c, n) in enumerate(dq_summary_rows, start=5):
        c1 = ws_dq.cell(row=r_idx, column=1, value=m)
        c2 = ws_dq.cell(row=r_idx, column=2, value=c)
        c3 = ws_dq.cell(row=r_idx, column=3, value=n)
        for cell in [c1, c2, c3]:
            cell.font = FONT_BODY
            cell.border = BOX_BORDER
            cell.alignment = Alignment(vertical="center")
        c1.font = FONT_BOLD_BODY
        c2.number_format = "#,##0"

    # Flagged records detailed table
    start_flagged_r = 14
    ws_dq.cell(row=start_flagged_r, column=1, value="Flagged Records Detail Log").font = FONT_SECTION

    flagged_headers = ["Record ID", "Employee ID", "Course ID", "Issue Type", "Severity", "Description"]
    for c_idx, h in enumerate(flagged_headers, start=1):
        cell = ws_dq.cell(row=start_flagged_r + 1, column=c_idx, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_ACCENT
        cell.border = BOX_BORDER

    if not flagged_df.empty:
        for idx, row in flagged_df.iterrows():
            curr_r = start_flagged_r + 2 + idx
            for c_idx, field in enumerate(["record_id", "employee_id", "course_id", "issue_type", "issue_severity", "issue_description"], start=1):
                cell = ws_dq.cell(row=curr_r, column=c_idx, value=str(row.get(field, "")))
                cell.font = FONT_BODY
                cell.border = BOX_BORDER
                cell.alignment = Alignment(vertical="center")

    _auto_fit_columns(ws_dq)

    # ==========================================
    # 6. Data Dictionary Worksheet
    # ==========================================
    ws_dict = wb.create_sheet(title="Data Dictionary")
    ws_dict.views.sheetView[0].showGridLines = True
    ws_dict.freeze_panes = "A2"

    dict_headers = ["Field Name", "Data Type", "Required", "Allowable Values / Format", "Description & Business Rule"]
    for c_idx, h in enumerate(dict_headers, start=1):
        cell = ws_dict.cell(row=1, column=c_idx, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_NAVY
        cell.border = BOX_BORDER
    ws_dict.row_dimensions[1].height = 24

    dictionary_data = [
        ("record_id", "Text (String)", "Yes", "TR-XXXXX", "Unique surrogate identifier for each training assignment record."),
        ("employee_id", "Text (String)", "Yes", "EMP-XXXX", "Unique identifier for employee. Must exist in HRIS system."),
        ("employee_name", "Text (String)", "Yes", "First Last", "Full name of the employee."),
        ("department", "Text (String)", "Yes", "8 Canonical Departments", "Corporate business unit. Synonyms mapped to canonical name."),
        ("job_level", "Text (String)", "No", "Entry-Level, Mid-Level, Senior, Lead / Manager, Director / VP", "Organizational seniority level."),
        ("course_id", "Text (String)", "Yes", "CRS-XXX-XXX", "Unique course catalog identifier."),
        ("course_name", "Text (String)", "Yes", "Text", "Official title of the training course."),
        ("training_category", "Text (String)", "Yes", "5 Core Categories", "Curriculum domain (Compliance, Technical, Leadership, etc.)."),
        ("mandatory_training", "Boolean", "Yes", "TRUE / FALSE", "Indicates if compliance is legally or policy mandated."),
        ("assigned_date", "Date", "Yes", "YYYY-MM-DD", "Date training assignment was created in LMS."),
        ("due_date", "Date", "Yes", "YYYY-MM-DD", "Deadline for completion. Must be >= assigned_date."),
        ("completion_date", "Date", "No", "YYYY-MM-DD", "Date employee finished course. Required if status is Completed."),
        ("attendance_status", "Text (Enum)", "No", "Attended, Partial, Absent, Not Scheduled / Self-Paced, Excused", "Classroom/session attendance record."),
        ("completion_status", "Text (Enum)", "Yes", "Completed, In Progress, Not Started", "Current fulfillment state of the assignment."),
        ("assessment_score", "Float (Numeric)", "No", "0.0 – 100.0", "Final assessment percentage score. Null if uncompleted or non-graded."),
        ("training_hours", "Float (Numeric)", "Yes", "Positive Number (>0)", "Official credit hours allocated for course completion."),
        ("delivery_mode", "Text (Enum)", "No", "Virtual Instructor-Led, Self-Paced, In-Person, Hybrid", "Training instructional delivery mechanism."),
        ("instructor", "Text (String)", "No", "Instructor name or LMS Proctor", "Name of trainer or automated system proctor."),
        ("region", "Text (Enum)", "No", "North America, EMEA, APAC, LATAM", "Geographic business region of employee.")
    ]

    for r_idx, row_data in enumerate(dictionary_data, start=2):
        for c_idx, val in enumerate(row_data, start=1):
            cell = ws_dict.cell(row=r_idx, column=c_idx, value=val)
            cell.font = FONT_BODY
            cell.border = BOX_BORDER
            cell.alignment = Alignment(vertical="center")
        ws_dict.cell(row=r_idx, column=1).font = FONT_BOLD_BODY

    _auto_fit_columns(ws_dict)

    wb.save(export_path)
    return export_path
