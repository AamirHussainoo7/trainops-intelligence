"""Data Validation & Cleaning Engine for TrainOps Intelligence.

Implements enterprise data quality checks, schema validation, safe standardization,
duplicate detection, date logic rules, score constraints, and auditable traceability.
"""

from datetime import datetime
import re
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from src.config import (
    ATTENDANCE_STATUSES,
    CANONICAL_DEPARTMENTS,
    COMPLETION_STATUS_SYNONYMS,
    DEPARTMENT_SYNONYMS,
)

REQUIRED_COLUMNS = [
    "record_id",
    "employee_id",
    "employee_name",
    "department",
    "course_id",
    "course_name",
    "assigned_date",
    "due_date",
    "mandatory_training",
    "completion_status"
]

ALL_EXPECTED_COLUMNS = [
    "record_id",
    "employee_id",
    "employee_name",
    "department",
    "job_level",
    "course_id",
    "course_name",
    "training_category",
    "mandatory_training",
    "assigned_date",
    "due_date",
    "completion_date",
    "attendance_status",
    "completion_status",
    "assessment_score",
    "training_hours",
    "delivery_mode",
    "instructor",
    "region"
]


def parse_date_safely(date_val: Any) -> Optional[datetime]:
    """Attempt parsing multiple standard date string formats into datetime object."""
    if date_val is None or pd.isna(date_val):
        return None
    val_str = str(date_val).strip()
    if val_str.lower() in ["none", "nan", "nat", "n/a", "null", ""]:
        return None

    # Handle standard formats
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(val_str, fmt)
        except ValueError:
            continue
    return None


def standardize_department(dept_raw: Any) -> Tuple[Optional[str], Optional[str]]:
    """Standardize department string against synonym mappings and canonical departments.
    
    Returns (standardized_dept, issue_description).
    """
    if dept_raw is None or pd.isna(dept_raw):
        return None, "Missing department"

    dept_clean = str(dept_raw).strip()
    if not dept_clean:
        return None, "Empty department string"

    # Exact canonical check
    for canonical in CANONICAL_DEPARTMENTS:
        if dept_clean.lower() == canonical.lower():
            return canonical, None

    # Synonym lookup
    lookup = dept_clean.lower()
    if lookup in DEPARTMENT_SYNONYMS:
        return DEPARTMENT_SYNONYMS[lookup], None

    # Partial match heuristic
    for key, val in DEPARTMENT_SYNONYMS.items():
        if key in lookup:
            return val, None

    return dept_clean, f"Non-canonical department '{dept_clean}'"


def standardize_status(status_raw: Any) -> Tuple[Optional[str], Optional[str]]:
    """Standardize completion status to canonical enum.
    
    Returns (standardized_status, issue_description).
    """
    if status_raw is None or pd.isna(status_raw):
        return None, "Missing completion status"

    clean_str = str(status_raw).strip().lower()
    if clean_str in COMPLETION_STATUS_SYNONYMS:
        return COMPLETION_STATUS_SYNONYMS[clean_str], None

    return None, f"Unrecognized completion status '{status_raw}'"


def validate_training_dataset(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Execute complete data validation pipeline on ingested training records.
    
    Returns:
        valid_df: Cleaned, validated records safe for KPI calculations.
        flagged_df: Rejected records requiring human review with reason tags.
        summary: Structured summary of all data quality metrics and issues.
    """
    if df_raw.empty:
        summary = {
            "total_records": 0,
            "valid_records": 0,
            "flagged_records": 0,
            "duplicates": 0,
            "missing_fields": 0,
            "date_errors": 0,
            "score_errors": 0,
            "status_errors": 0,
            "issues_by_category": {}
        }
        return pd.DataFrame(), pd.DataFrame(), summary

    df = df_raw.copy()
    total_input = len(df)

    # Track issues
    flagged_records_list: List[Dict[str, Any]] = []
    valid_rows: List[Dict[str, Any]] = []

    # Category counts
    category_counts: Dict[str, int] = {
        "Duplicate Record": 0,
        "Missing Required Field": 0,
        "Date Relationship Error": 0,
        "Invalid Assessment Score": 0,
        "Invalid Status Value": 0,
        "Attendance Inconsistency": 0,
        "Schema / Type Error": 0
    }

    # Tracking seen keys for duplicate detection
    seen_record_ids = set()
    seen_assignment_keys = set()

    for idx, row in df.iterrows():
        raw_dict = row.to_dict()
        record_id = str(row.get("record_id", "")).strip() if pd.notna(row.get("record_id")) else ""
        emp_id = str(row.get("employee_id", "")).strip() if pd.notna(row.get("employee_id")) else ""
        course_id = str(row.get("course_id", "")).strip() if pd.notna(row.get("course_id")) else ""
        assigned_date_raw = row.get("assigned_date")

        row_issues: List[Dict[str, str]] = []

        # 1. Missing Critical Identifiers
        if not record_id or record_id.lower() in ["nan", "none", "null"]:
            row_issues.append({
                "type": "Missing Required Field",
                "severity": "CRITICAL",
                "desc": "Missing record_id"
            })
        if not emp_id or emp_id.lower() in ["nan", "none", "null"]:
            row_issues.append({
                "type": "Missing Required Field",
                "severity": "CRITICAL",
                "desc": "Missing employee_id"
            })
        if not course_id or course_id.lower() in ["nan", "none", "null"]:
            row_issues.append({
                "type": "Missing Required Field",
                "severity": "CRITICAL",
                "desc": "Missing course_id"
            })

        emp_name = str(row.get("employee_name", "")).strip() if pd.notna(row.get("employee_name")) else ""
        if not emp_name or emp_name.lower() in ["nan", "none", "null"]:
            row_issues.append({
                "type": "Missing Required Field",
                "severity": "CRITICAL",
                "desc": "Missing employee_name"
            })

        course_name = str(row.get("course_name", "")).strip() if pd.notna(row.get("course_name")) else ""
        if not course_name or course_name.lower() in ["nan", "none", "null"]:
            row_issues.append({
                "type": "Missing Required Field",
                "severity": "CRITICAL",
                "desc": "Missing course_name"
            })

        # 2. Duplicate Detection
        if record_id:
            if record_id in seen_record_ids:
                row_issues.append({
                    "type": "Duplicate Record",
                    "severity": "CRITICAL",
                    "desc": f"Duplicate record_id '{record_id}' detected"
                })
            else:
                seen_record_ids.add(record_id)

        assignment_key = (emp_id, course_id, str(assigned_date_raw).strip())
        if emp_id and course_id and pd.notna(assigned_date_raw):
            if assignment_key in seen_assignment_keys:
                row_issues.append({
                    "type": "Duplicate Record",
                    "severity": "CRITICAL",
                    "desc": f"Duplicate assignment key (emp: {emp_id}, course: {course_id}, date: {assigned_date_raw})"
                })
            else:
                seen_assignment_keys.add(assignment_key)

        # 3. Department Standardization
        dept_standard, dept_err = standardize_department(row.get("department"))
        if not dept_standard:
            row_issues.append({
                "type": "Missing Required Field",
                "severity": "CRITICAL",
                "desc": dept_err or "Invalid department"
            })

        # 4. Completion Status Standardization
        status_standard, status_err = standardize_status(row.get("completion_status"))
        if not status_standard:
            row_issues.append({
                "type": "Invalid Status Value",
                "severity": "CRITICAL",
                "desc": status_err or "Invalid completion status"
            })

        # 5. Date Relationship Validation
        dt_assigned = parse_date_safely(assigned_date_raw)
        dt_due = parse_date_safely(row.get("due_date"))
        dt_completion = parse_date_safely(row.get("completion_date"))

        if dt_assigned is None:
            row_issues.append({
                "type": "Date Relationship Error",
                "severity": "CRITICAL",
                "desc": f"Invalid or missing assigned_date: '{assigned_date_raw}'"
            })
        if dt_due is None:
            row_issues.append({
                "type": "Date Relationship Error",
                "severity": "CRITICAL",
                "desc": f"Invalid or missing due_date: '{row.get('due_date')}'"
            })

        if dt_assigned and dt_due and dt_due < dt_assigned:
            row_issues.append({
                "type": "Date Relationship Error",
                "severity": "CRITICAL",
                "desc": f"Due date ({dt_due.strftime('%Y-%m-%d')}) precedes assigned date ({dt_assigned.strftime('%Y-%m-%d')})"
            })

        if dt_completion and dt_assigned and dt_completion < dt_assigned:
            row_issues.append({
                "type": "Date Relationship Error",
                "severity": "CRITICAL",
                "desc": f"Completion date ({dt_completion.strftime('%Y-%m-%d')}) precedes assigned date ({dt_assigned.strftime('%Y-%m-%d')})"
            })

        # If completed, must have completion date
        if status_standard == "Completed" and dt_completion is None:
            row_issues.append({
                "type": "Date Relationship Error",
                "severity": "CRITICAL",
                "desc": "Record marked Completed but missing valid completion_date"
            })

        # 6. Assessment Score Validation
        score_val = row.get("assessment_score")
        cleaned_score = None
        if score_val is not None and not pd.isna(score_val):
            try:
                score_num = float(score_val)
                if score_num < 0.0 or score_num > 100.0:
                    row_issues.append({
                        "type": "Invalid Assessment Score",
                        "severity": "CRITICAL",
                        "desc": f"Assessment score {score_num} is out of allowable range (0–100)"
                    })
                else:
                    cleaned_score = round(score_num, 1)
            except (ValueError, TypeError):
                row_issues.append({
                    "type": "Invalid Assessment Score",
                    "severity": "CRITICAL",
                    "desc": f"Assessment score '{score_val}' is non-numeric"
                })

        # 7. Safe Mandatory boolean conversion
        mand_raw = row.get("mandatory_training")
        if isinstance(mand_raw, bool):
            mandatory_bool = mand_raw
        elif isinstance(mand_raw, (int, float)):
            mandatory_bool = bool(mand_raw)
        elif isinstance(mand_raw, str):
            mandatory_bool = mand_raw.strip().lower() in ["true", "1", "yes", "t", "y"]
        else:
            mandatory_bool = False

        # 8. Training hours validation
        hours_raw = row.get("training_hours", 2.0)
        try:
            cleaned_hours = float(hours_raw) if pd.notna(hours_raw) else 2.0
            if cleaned_hours <= 0:
                cleaned_hours = 1.0
        except (ValueError, TypeError):
            cleaned_hours = 2.0

        # Attendance check
        attend_raw = row.get("attendance_status")
        if pd.isna(attend_raw) or not str(attend_raw).strip():
            attend_clean = "Not Scheduled / Self-Paced" if row.get("delivery_mode") == "Self-Paced E-Learning" else "Absent"
        else:
            attend_clean = str(attend_raw).strip()

        # Separate Critical from Clean
        critical_issues = [iss for iss in row_issues if iss["severity"] == "CRITICAL"]

        if critical_issues:
            # Record flagged for human review
            for iss in critical_issues:
                category_counts[iss["type"]] = category_counts.get(iss["type"], 0) + 1
                flagged_records_list.append({
                    "record_id": record_id or f"ROW-{idx}",
                    "employee_id": emp_id or "UNKNOWN",
                    "course_id": course_id or "UNKNOWN",
                    "issue_type": iss["type"],
                    "issue_severity": iss["severity"],
                    "issue_description": iss["desc"],
                    "raw_record": raw_dict,
                })
        else:
            # Safe clean record
            valid_rows.append({
                "record_id": record_id,
                "employee_id": emp_id,
                "employee_name": emp_name,
                "department": dept_standard,
                "job_level": str(row.get("job_level", "Mid-Level")).strip(),
                "course_id": course_id,
                "course_name": course_name,
                "training_category": str(row.get("training_category", "Compliance & Security")).strip(),
                "mandatory_training": mandatory_bool,
                "assigned_date": dt_assigned.strftime("%Y-%m-%d"),
                "due_date": dt_due.strftime("%Y-%m-%d"),
                "completion_date": dt_completion.strftime("%Y-%m-%d") if dt_completion else None,
                "attendance_status": attend_clean,
                "completion_status": status_standard,
                "assessment_score": cleaned_score,
                "training_hours": cleaned_hours,
                "delivery_mode": str(row.get("delivery_mode", "Self-Paced E-Learning")).strip(),
                "instructor": str(row.get("instructor", "LMS Proctor")).strip(),
                "region": str(row.get("region", "North America")).strip(),
            })

    valid_df = pd.DataFrame(valid_rows)
    flagged_df = pd.DataFrame(flagged_records_list)

    # Calculate summary numbers
    duplicate_count = category_counts["Duplicate Record"]
    missing_count = category_counts["Missing Required Field"]
    date_err_count = category_counts["Date Relationship Error"]
    score_err_count = category_counts["Invalid Assessment Score"]
    status_err_count = category_counts["Invalid Status Value"]

    unique_flagged_count = len({item["record_id"] for item in flagged_records_list}) if flagged_records_list else 0

    summary = {
        "run_id": f"VRUN-{int(datetime.now().timestamp())}",
        "total_records": total_input,
        "valid_records": len(valid_df),
        "flagged_records": unique_flagged_count,
        "total_issues_logged": len(flagged_records_list),
        "duplicates": duplicate_count,
        "missing_fields": missing_count,
        "date_errors": date_err_count,
        "score_errors": score_err_count,
        "status_errors": status_err_count,
        "issues_by_category": category_counts
    }

    return valid_df, flagged_df, summary
