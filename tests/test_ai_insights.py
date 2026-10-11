"""Unit tests for AI insights generation and deterministic fallback resilience."""

from pathlib import Path
import pytest
import pandas as pd
from src.ai_insights import (
    generate_management_insights,
    prepare_llm_payload,
    _generate_deterministic_fallback
)
from src.analytics import compute_kpis, get_department_kpis, get_course_kpis
from src.data_generator import generate_clean_dataset
from src.reporting import generate_full_report_workflow


def test_prepare_llm_payload_aggregates_safely():
    """Verify metrics payload aggregates without including raw employee records."""
    df = generate_clean_dataset(num_records=50, seed=42)
    kpis = compute_kpis(df, as_of_date="2026-10-15")
    dept_df = get_department_kpis(df, as_of_date="2026-10-15")
    course_df = get_course_kpis(df, as_of_date="2026-10-15")
    dq = {"total_records": 50, "valid_records": 50}

    payload = prepare_llm_payload(kpis, dept_df, course_df, dq)

    assert "kpis" in payload
    assert "top_departments" in payload
    assert "top_courses" in payload
    # Raw individual employee records must not be in payload
    payload_str = str(payload)
    assert "TR-100" not in payload_str


def test_deterministic_fallback_schema_and_content():
    """Verify deterministic fallback produces all required schema keys."""
    df = generate_clean_dataset(num_records=50, seed=42)
    kpis = compute_kpis(df, as_of_date="2026-10-15")
    dept_df = get_department_kpis(df, as_of_date="2026-10-15")
    course_df = get_course_kpis(df, as_of_date="2026-10-15")
    dq = {"total_records": 50, "valid_records": 50}

    payload = prepare_llm_payload(kpis, dept_df, course_df, dq)
    fallback = _generate_deterministic_fallback(payload)

    assert "executive_summary" in fallback
    assert len(fallback["executive_summary"]) > 50
    assert "key_findings" in fallback
    assert isinstance(fallback["key_findings"], list)
    assert "risks_and_compliance_gaps" in fallback
    assert "recommended_actions" in fallback
    assert fallback["source"] == "DETERMINISTIC_FALLBACK"


def test_generate_insights_without_api_key():
    """Verify that calling generate_management_insights with empty key activates fallback cleanly."""
    payload = {"kpis": {"total_assignments": 100, "completion_rate_pct": 82.0}}
    insights, is_ai, status_msg = generate_management_insights(
        payload=payload,
        api_key="",
        model_name="llama-3.3-70b-versatile"
    )

    assert is_ai is False
    assert "not configured" in status_msg.lower() or "fallback" in status_msg.lower()
    assert insights["source"] == "DETERMINISTIC_FALLBACK"
    assert "executive_summary" in insights


def test_report_workflow_end_to_end(tmp_path):
    """Verify full report generation workflow creates Excel and Markdown files without an API key."""
    df = generate_clean_dataset(num_records=50, seed=42)
    dq = {"total_records": 50, "valid_records": 50, "flagged_records": 0}
    flagged_df = pd.DataFrame()

    result = generate_full_report_workflow(
        df=df,
        dq_summary=dq,
        flagged_df=flagged_df,
        as_of_date="2026-10-15",
        period_start="2026-01-01",
        period_end="2026-12-31",
        api_key="",  # No key
    )

    assert "report_id" in result
    assert result["is_ai_assisted"] is False
    assert Path(result["excel_path"]).exists()
    assert Path(result["markdown_path"]).exists()
    assert len(result["markdown_content"]) > 100
