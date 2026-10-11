"""Unit tests for synthetic dataset generator and determinism."""

import pytest
import pandas as pd
from src.data_generator import (
    generate_clean_dataset,
    generate_flawed_raw_dataset,
    COURSE_CATALOG
)


def test_clean_dataset_generation_count_and_columns():
    """Verify clean dataset generates >= 1,000 records with all required columns."""
    df = generate_clean_dataset(num_records=1100, seed=42)
    assert len(df) == 1100
    expected_cols = [
        "record_id", "employee_id", "employee_name", "department", "job_level",
        "course_id", "course_name", "training_category", "mandatory_training",
        "assigned_date", "due_date", "completion_date", "attendance_status",
        "completion_status", "assessment_score", "training_hours", "delivery_mode",
        "instructor", "region"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing required column: {col}"


def test_dataset_reproducibility():
    """Verify that same random seed produces identical records."""
    df1 = generate_clean_dataset(num_records=100, seed=123)
    df2 = generate_clean_dataset(num_records=100, seed=123)
    pd.testing.assert_frame_equal(df1, df2)


def test_clean_dataset_logical_integrity():
    """Verify no logically impossible dates or scores exist in clean dataset."""
    df = generate_clean_dataset(num_records=500, seed=42)

    # Date ordering: assigned <= due
    assert (df["assigned_date"] <= df["due_date"]).all()

    # Completed records have valid completion date >= assigned date
    completed = df[df["completion_status"] == "Completed"]
    assert (completed["completion_date"].notna()).all()
    assert (completed["completion_date"] >= completed["assigned_date"]).all()

    # Scores within 0-100
    scored = df[df["assessment_score"].notna()]
    assert (scored["assessment_score"] >= 0).all()
    assert (scored["assessment_score"] <= 100).all()


def test_flawed_raw_dataset_injects_anomalies():
    """Verify that flawed raw dataset injects duplicates, invalid scores, and anomalies."""
    clean_df = generate_clean_dataset(num_records=500, seed=42)
    raw_df = generate_flawed_raw_dataset(clean_df, seed=42)

    # Raw dataset has duplicates added
    assert len(raw_df) > len(clean_df)

    # Check for invalid scores (>100, <0, or string)
    invalid_scores = []
    for sc in raw_df["assessment_score"]:
        if isinstance(sc, str) or (isinstance(sc, (int, float)) and (sc < 0 or sc > 100)):
            invalid_scores.append(sc)
    assert len(invalid_scores) > 0, "Raw dataset should contain invalid scores"
