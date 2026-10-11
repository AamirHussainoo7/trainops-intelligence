"""Unit tests for deterministic KPI calculations and zero-denominator handling."""

import pytest
import pandas as pd
from src.analytics import (
    compute_kpis,
    get_department_kpis,
    get_course_kpis,
    get_monthly_completion_trends
)


def test_empty_dataset_kpis():
    """Verify compute_kpis handles empty DataFrame without division by zero."""
    empty_df = pd.DataFrame()
    kpis = compute_kpis(empty_df, as_of_date="2026-10-15")

    assert kpis["total_assignments"] == 0
    assert kpis["unique_employees"] == 0
    assert kpis["completion_rate_pct"] == 0.0
    assert kpis["attendance_rate_formatted"] == "N/A"
    assert kpis["avg_assessment_score"] is None
    assert kpis["overdue_assignments"] == 0
    assert kpis["mandatory_completion_rate_pct"] == 0.0
    assert kpis["total_completed_hours"] == 0.0


def test_standard_kpi_calculations():
    """Verify KPI calculation accuracy on synthetic test records."""
    records = [
        # Record 1: Completed, mandatory, attended, on time
        {
            "record_id": "TR-1",
            "employee_id": "EMP-1",
            "department": "Engineering",
            "course_id": "CRS-1",
            "course_name": "Security",
            "training_category": "Compliance",
            "mandatory_training": True,
            "assigned_date": "2026-01-01",
            "due_date": "2026-02-01",
            "completion_date": "2026-01-20",
            "attendance_status": "Attended",
            "completion_status": "Completed",
            "assessment_score": 90.0,
            "training_hours": 2.0,
            "delivery_mode": "Virtual Instructor-Led"
        },
        # Record 2: In Progress, optional, attended, OVERDUE as of 2026-10-15
        {
            "record_id": "TR-2",
            "employee_id": "EMP-2",
            "department": "Engineering",
            "course_id": "CRS-2",
            "course_name": "AI Basics",
            "training_category": "Technical",
            "mandatory_training": False,
            "assigned_date": "2026-01-01",
            "due_date": "2026-02-01",
            "completion_date": None,
            "attendance_status": "Attended",
            "completion_status": "In Progress",
            "assessment_score": None,
            "training_hours": 4.0,
            "delivery_mode": "Virtual Instructor-Led"
        },
        # Record 3: Completed, mandatory, self-paced
        {
            "record_id": "TR-3",
            "employee_id": "EMP-1",  # Same employee EMP-1
            "department": "Engineering",
            "course_id": "CRS-3",
            "course_name": "Data Privacy",
            "training_category": "Compliance",
            "mandatory_training": True,
            "assigned_date": "2026-01-01",
            "due_date": "2026-03-01",
            "completion_date": "2026-02-15",
            "attendance_status": "Not Scheduled / Self-Paced",
            "completion_status": "Completed",
            "assessment_score": 80.0,
            "training_hours": 1.5,
            "delivery_mode": "Self-Paced E-Learning"
        },
        # Record 4: Not Started, optional, absent, not overdue
        {
            "record_id": "TR-4",
            "employee_id": "EMP-3",
            "department": "Finance",
            "course_id": "CRS-4",
            "course_name": "AML",
            "training_category": "Finance",
            "mandatory_training": False,
            "assigned_date": "2026-10-01",
            "due_date": "2026-11-01",
            "completion_date": None,
            "attendance_status": "Absent",
            "completion_status": "Not Started",
            "assessment_score": None,
            "training_hours": 3.0,
            "delivery_mode": "In-Person Classroom"
        }
    ]
    df = pd.DataFrame(records)
    kpis = compute_kpis(df, as_of_date="2026-10-15")

    # 4 assignments, 3 unique employees (EMP-1, EMP-2, EMP-3)
    assert kpis["total_assignments"] == 4
    assert kpis["unique_employees"] == 3

    # 2 completed out of 4 -> 50.0%
    assert kpis["completion_rate_pct"] == 50.0

    # Mandatory: 2 mandatory (TR-1, TR-3), both completed -> 100.0%
    assert kpis["mandatory_assignments"] == 2
    assert kpis["mandatory_completion_rate_pct"] == 100.0

    # Average score: (90 + 80) / 2 = 85.0
    assert kpis["avg_assessment_score"] == 85.0

    # Overdue: TR-2 is uncompleted and due_date '2026-02-01' < '2026-10-15' -> 1 overdue
    assert kpis["overdue_assignments"] == 1

    # Total completed hours: 2.0 + 1.5 = 3.5
    assert kpis["total_completed_hours"] == 3.5


def test_department_and_course_aggregations():
    """Verify department and course summaries aggregate without error."""
    records = [
        {
            "record_id": "TR-1", "employee_id": "EMP-1", "department": "IT",
            "course_id": "CRS-1", "course_name": "Security", "training_category": "Compliance",
            "mandatory_training": True, "assigned_date": "2026-01-01", "due_date": "2026-02-01",
            "completion_date": "2026-01-10", "attendance_status": "Attended",
            "completion_status": "Completed", "assessment_score": 85.0, "training_hours": 2.0,
            "delivery_mode": "Self-Paced"
        }
    ]
    df = pd.DataFrame(records)
    dept_df = get_department_kpis(df, as_of_date="2026-10-15")
    course_df = get_course_kpis(df, as_of_date="2026-10-15")

    assert len(dept_df) == 1
    assert dept_df.iloc[0]["department"] == "IT"
    assert dept_df.iloc[0]["completion_rate_pct"] == 100.0

    assert len(course_df) == 1
    assert course_df.iloc[0]["course_id"] == "CRS-1"
