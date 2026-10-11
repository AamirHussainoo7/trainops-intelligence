"""Unit tests for the Data Validation & Cleaning Pipeline."""

import pytest
import pandas as pd
from src.validation import (
    validate_training_dataset,
    standardize_department,
    standardize_status,
    parse_date_safely
)


def test_standardize_department():
    """Verify department normalization and synonym mapping."""
    dept, err = standardize_department("it")
    assert dept == "Information Technology"
    assert err is None

    dept, err = standardize_department("HR")
    assert dept == "Human Resources"
    assert err is None

    dept, err = standardize_department("Engineering")
    assert dept == "Engineering"
    assert err is None

    dept, err = standardize_department(None)
    assert dept is None
    assert "Missing" in err


def test_standardize_status():
    """Verify status normalization."""
    status, err = standardize_status("done")
    assert status == "Completed"

    status, err = standardize_status("PENDING")
    assert status == "In Progress"

    status, err = standardize_status("InvalidXYZ")
    assert status is None
    assert "Unrecognized" in err


def test_duplicate_detection():
    """Verify pipeline catches duplicate record_ids and assignment keys."""
    raw_data = [
        {
            "record_id": "TR-100",
            "employee_id": "EMP-1",
            "employee_name": "Test User",
            "department": "IT",
            "course_id": "CRS-1",
            "course_name": "Course 1",
            "assigned_date": "2026-02-01",
            "due_date": "2026-03-01",
            "mandatory_training": True,
            "completion_status": "Completed",
            "completion_date": "2026-02-15",
            "assessment_score": 85.0
        },
        {
            "record_id": "TR-100",  # Duplicate ID
            "employee_id": "EMP-2",
            "employee_name": "Second User",
            "department": "HR",
            "course_id": "CRS-2",
            "course_name": "Course 2",
            "assigned_date": "2026-02-01",
            "due_date": "2026-03-01",
            "mandatory_training": False,
            "completion_status": "Not Started"
        }
    ]
    df = pd.DataFrame(raw_data)
    valid_df, flagged_df, summary = validate_training_dataset(df)

    assert summary["duplicates"] >= 1
    assert len(valid_df) == 1
    assert len(flagged_df) >= 1
    assert "TR-100" in flagged_df["record_id"].values


def test_date_relationship_violations():
    """Verify date errors: completion before assigned, or due before assigned."""
    bad_dates = [
        {
            "record_id": "TR-101",
            "employee_id": "EMP-1",
            "employee_name": "User 1",
            "department": "Engineering",
            "course_id": "CRS-1",
            "course_name": "Course 1",
            "assigned_date": "2026-03-01",
            "due_date": "2026-02-01",  # Due before assigned!
            "mandatory_training": True,
            "completion_status": "In Progress"
        },
        {
            "record_id": "TR-102",
            "employee_id": "EMP-2",
            "employee_name": "User 2",
            "department": "Operations",
            "course_id": "CRS-2",
            "course_name": "Course 2",
            "assigned_date": "2026-04-10",
            "due_date": "2026-05-10",
            "mandatory_training": True,
            "completion_status": "Completed",
            "completion_date": "2026-03-10",  # Completed before assigned!
            "assessment_score": 90.0
        }
    ]
    df = pd.DataFrame(bad_dates)
    valid_df, flagged_df, summary = validate_training_dataset(df)

    assert len(valid_df) == 0
    assert summary["date_errors"] >= 2


def test_invalid_assessment_scores():
    """Verify that scores < 0, > 100, or non-numeric strings are flagged."""
    bad_scores = [
        {
            "record_id": "TR-201",
            "employee_id": "EMP-1",
            "employee_name": "User 1",
            "department": "Finance",
            "course_id": "CRS-1",
            "course_name": "Course 1",
            "assigned_date": "2026-01-01",
            "due_date": "2026-02-01",
            "mandatory_training": True,
            "completion_status": "Completed",
            "completion_date": "2026-01-15",
            "assessment_score": 150.0  # > 100
        },
        {
            "record_id": "TR-202",
            "employee_id": "EMP-2",
            "employee_name": "User 2",
            "department": "Finance",
            "course_id": "CRS-1",
            "course_name": "Course 1",
            "assigned_date": "2026-01-01",
            "due_date": "2026-02-01",
            "mandatory_training": True,
            "completion_status": "Completed",
            "completion_date": "2026-01-15",
            "assessment_score": "Not Gradable"  # Non-numeric
        }
    ]
    df = pd.DataFrame(bad_scores)
    valid_df, flagged_df, summary = validate_training_dataset(df)

    assert summary["score_errors"] >= 2
    assert len(valid_df) == 0
