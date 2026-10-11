"""Deterministic KPI Analytics Engine for TrainOps Intelligence.

Calculates corporate L&D metrics, protects against zero-division edge cases,
computes overdue status based on configurable as-of dates, and aggregates chart datasets.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd


def compute_kpis(
    df: pd.DataFrame,
    as_of_date: Optional[str] = None
) -> Dict[str, Any]:
    """Compute enterprise training operations KPIs deterministically.
    
    Args:
        df: Filtered clean training records DataFrame.
        as_of_date: Reference date string (YYYY-MM-DD) for calculating overdue status.
                    Defaults to today if not provided.
    
    Returns:
        Dictionary containing metric counts, percentages, and formatted strings.
    """
    if df.empty:
        return {
            "total_assignments": 0,
            "unique_employees": 0,
            "completed_assignments": 0,
            "completion_rate_pct": 0.0,
            "completion_rate_formatted": "0.0%",
            "attendance_rate_pct": 0.0,
            "attendance_rate_formatted": "N/A",
            "attended_count": 0,
            "attendance_eligible_count": 0,
            "avg_assessment_score": None,
            "avg_assessment_score_formatted": "N/A",
            "scored_assignments_count": 0,
            "overdue_assignments": 0,
            "overdue_rate_pct": 0.0,
            "overdue_rate_formatted": "0.0%",
            "mandatory_assignments": 0,
            "mandatory_completed": 0,
            "mandatory_completion_rate_pct": 0.0,
            "mandatory_completion_rate_formatted": "0.0%",
            "optional_assignments": 0,
            "optional_completed": 0,
            "optional_completion_rate_pct": 0.0,
            "total_completed_hours": 0.0,
            "total_assigned_hours": 0.0,
            "in_progress_count": 0,
            "not_started_count": 0,
            "as_of_date": as_of_date or datetime.today().strftime("%Y-%m-%d"),
        }

    as_of_str = as_of_date or datetime.today().strftime("%Y-%m-%d")
    total_assignments = len(df)
    unique_employees = int(df["employee_id"].nunique())

    # 1. Completion Rate
    completed_df = df[df["completion_status"] == "Completed"]
    completed_count = len(completed_df)
    completion_rate_pct = (completed_count / total_assignments * 100.0) if total_assignments > 0 else 0.0

    # 2. Attendance Rate
    # Eligible for attendance analysis: records where attendance was tracked (Attended, Partial, Absent)
    tracked_attendance = df[df["attendance_status"].isin(["Attended", "Partial", "Absent"])]
    attendance_eligible_count = len(tracked_attendance)
    attended_count = len(df[df["attendance_status"] == "Attended"])
    if attendance_eligible_count > 0:
        attendance_rate_pct = (attended_count / attendance_eligible_count) * 100.0
        attendance_rate_formatted = f"{attendance_rate_pct:.1f}%"
    else:
        # If all courses are self-paced / asynchronous
        attendance_rate_pct = 100.0
        attendance_rate_formatted = "100.0% (Self-Paced)"

    # 3. Average Assessment Score
    valid_scores = df["assessment_score"].dropna()
    valid_scores = valid_scores[valid_scores.apply(lambda x: isinstance(x, (int, float)) and not np.isnan(x))]
    scored_count = len(valid_scores)
    if scored_count > 0:
        avg_score = float(valid_scores.mean())
        avg_score_formatted = f"{avg_score:.1f}"
    else:
        avg_score = None
        avg_score_formatted = "N/A"

    # 4. Overdue Training Assignments
    # An assignment is overdue if it is not completed and due_date < as_of_date
    uncompleted_mask = df["completion_status"] != "Completed"
    overdue_mask = uncompleted_mask & (df["due_date"] < as_of_str)
    overdue_count = int(overdue_mask.sum())
    overdue_rate_pct = (overdue_count / total_assignments * 100.0) if total_assignments > 0 else 0.0

    # 5. Mandatory vs Optional Completion Rates
    # Mandatory
    mandatory_df = df[df["mandatory_training"] == True]
    mandatory_total = len(mandatory_df)
    mandatory_completed = len(mandatory_df[mandatory_df["completion_status"] == "Completed"])
    if mandatory_total > 0:
        mandatory_comp_rate = (mandatory_completed / mandatory_total) * 100.0
        mandatory_comp_formatted = f"{mandatory_comp_rate:.1f}%"
    else:
        mandatory_comp_rate = 0.0
        mandatory_comp_formatted = "N/A"

    # Optional
    optional_df = df[df["mandatory_training"] == False]
    optional_total = len(optional_df)
    optional_completed = len(optional_df[optional_df["completion_status"] == "Completed"])
    optional_comp_rate = (optional_completed / optional_total * 100.0) if optional_total > 0 else 0.0

    # 6. Training Hours
    total_completed_hours = float(completed_df["training_hours"].sum()) if not completed_df.empty else 0.0
    total_assigned_hours = float(df["training_hours"].sum())

    # Status counts
    in_progress_count = int((df["completion_status"] == "In Progress").sum())
    not_started_count = int((df["completion_status"] == "Not Started").sum())

    return {
        "total_assignments": total_assignments,
        "unique_employees": unique_employees,
        "completed_assignments": completed_count,
        "completion_rate_pct": round(completion_rate_pct, 1),
        "completion_rate_formatted": f"{completion_rate_pct:.1f}%",
        "attendance_rate_pct": round(attendance_rate_pct, 1),
        "attendance_rate_formatted": attendance_rate_formatted,
        "attended_count": attended_count,
        "attendance_eligible_count": attendance_eligible_count,
        "avg_assessment_score": round(avg_score, 1) if avg_score is not None else None,
        "avg_assessment_score_formatted": avg_score_formatted,
        "scored_assignments_count": scored_count,
        "overdue_assignments": overdue_count,
        "overdue_rate_pct": round(overdue_rate_pct, 1),
        "overdue_rate_formatted": f"{overdue_rate_pct:.1f}%",
        "mandatory_assignments": mandatory_total,
        "mandatory_completed": mandatory_completed,
        "mandatory_completion_rate_pct": round(mandatory_comp_rate, 1),
        "mandatory_completion_rate_formatted": mandatory_comp_formatted,
        "optional_assignments": optional_total,
        "optional_completed": optional_completed,
        "optional_completion_rate_pct": round(optional_comp_rate, 1),
        "total_completed_hours": round(total_completed_hours, 1),
        "total_assigned_hours": round(total_assigned_hours, 1),
        "in_progress_count": in_progress_count,
        "not_started_count": not_started_count,
        "as_of_date": as_of_str,
    }


def get_department_kpis(df: pd.DataFrame, as_of_date: Optional[str] = None) -> pd.DataFrame:
    """Aggregate KPIs per department."""
    if df.empty:
        return pd.DataFrame()

    as_of_str = as_of_date or datetime.today().strftime("%Y-%m-%d")
    records = []

    for dept, group in df.groupby("department"):
        total = len(group)
        unique_emp = group["employee_id"].nunique()
        completed = len(group[group["completion_status"] == "Completed"])
        comp_rate = round(completed / total * 100.0, 1) if total > 0 else 0.0

        # Mandatory
        mand_grp = group[group["mandatory_training"] == True]
        mand_total = len(mand_grp)
        mand_comp = len(mand_grp[mand_grp["completion_status"] == "Completed"])
        mand_rate = round(mand_comp / mand_total * 100.0, 1) if mand_total > 0 else 0.0

        # Overdue
        uncomp = group[group["completion_status"] != "Completed"]
        overdue = len(uncomp[uncomp["due_date"] < as_of_str])

        # Avg score
        scores = group["assessment_score"].dropna()
        avg_sc = round(float(scores.mean()), 1) if len(scores) > 0 else None

        # Attendance
        attend_known = group[group["attendance_status"].isin(["Attended", "Partial", "Absent"])]
        attended = len(group[group["attendance_status"] == "Attended"])
        attend_rate = round(attended / len(attend_known) * 100.0, 1) if len(attend_known) > 0 else 100.0

        # Completed hours
        comp_hours = round(float(group[group["completion_status"] == "Completed"]["training_hours"].sum()), 1)

        records.append({
            "department": dept,
            "total_assignments": total,
            "unique_employees": unique_emp,
            "completed_assignments": completed,
            "completion_rate_pct": comp_rate,
            "mandatory_assignments": mand_total,
            "mandatory_completion_rate_pct": mand_rate,
            "overdue_assignments": overdue,
            "avg_assessment_score": avg_sc,
            "attendance_rate_pct": attend_rate,
            "completed_training_hours": comp_hours,
        })

    dept_df = pd.DataFrame(records).sort_values("completion_rate_pct", ascending=False)
    return dept_df.reset_index(drop=True)


def get_course_kpis(df: pd.DataFrame, as_of_date: Optional[str] = None) -> pd.DataFrame:
    """Aggregate KPIs per course."""
    if df.empty:
        return pd.DataFrame()

    as_of_str = as_of_date or datetime.today().strftime("%Y-%m-%d")
    records = []

    for (cid, cname), group in df.groupby(["course_id", "course_name"]):
        total = len(group)
        completed = len(group[group["completion_status"] == "Completed"])
        comp_rate = round(completed / total * 100.0, 1) if total > 0 else 0.0

        category = group["training_category"].iloc[0]
        mandatory = bool(group["mandatory_training"].iloc[0])
        mode = group["delivery_mode"].iloc[0]
        unit_hours = float(group["training_hours"].iloc[0])

        uncomp = group[group["completion_status"] != "Completed"]
        overdue = len(uncomp[uncomp["due_date"] < as_of_str])

        scores = group["assessment_score"].dropna()
        avg_sc = round(float(scores.mean()), 1) if len(scores) > 0 else None

        records.append({
            "course_id": cid,
            "course_name": cname,
            "training_category": category,
            "mandatory_training": mandatory,
            "delivery_mode": mode,
            "unit_hours": unit_hours,
            "total_assignments": total,
            "completed_assignments": completed,
            "completion_rate_pct": comp_rate,
            "overdue_assignments": overdue,
            "avg_assessment_score": avg_sc,
            "total_hours_delivered": round(completed * unit_hours, 1)
        })

    course_df = pd.DataFrame(records).sort_values("total_assignments", ascending=False)
    return course_df.reset_index(drop=True)


def get_monthly_completion_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Compute monthly completions, assignments, and cumulative trends."""
    if df.empty:
        return pd.DataFrame()

    df_copy = df.copy()
    # Filter completed records with valid completion dates
    comp_df = df_copy[df_copy["completion_status"] == "Completed"].copy()
    comp_df = comp_df[comp_df["completion_date"].notna()]

    if comp_df.empty:
        return pd.DataFrame()

    comp_df["completion_month"] = comp_df["completion_date"].str.slice(0, 7)
    monthly = comp_df.groupby("completion_month").agg(
        completions=("record_id", "count"),
        total_hours=("training_hours", "sum"),
        avg_score=("assessment_score", "mean")
    ).reset_index()

    monthly["avg_score"] = monthly["avg_score"].round(1)
    monthly["total_hours"] = monthly["total_hours"].round(1)
    monthly = monthly.sort_values("completion_month")
    monthly["cumulative_completions"] = monthly["completions"].cumsum()

    return monthly
