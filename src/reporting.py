"""Automated Management Reporting Engine for TrainOps Intelligence.

Orchestrates deterministic KPI calculation, executive insights synthesis,
Excel workbook generation, and Markdown management briefings, logging each run to SQLite.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import pandas as pd
from src.ai_insights import generate_management_insights, prepare_llm_payload
from src.analytics import (
    compute_kpis,
    get_course_kpis,
    get_department_kpis,
    get_monthly_completion_trends,
)
from src.config import DATA_EXPORT_DIR, OUTPUT_DIR
from src.database import log_report_generation
from src.excel_export import generate_excel_workbook


def generate_markdown_report(
    kpis: Dict[str, Any],
    dept_df: pd.DataFrame,
    course_df: pd.DataFrame,
    dq_summary: Dict[str, Any],
    insights: Dict[str, Any],
    as_of_date: str,
    period_start: str,
    period_end: str,
    is_ai: bool
) -> str:
    """Compose a clean, executive-ready Markdown management briefing document."""
    report_md = f"""# TrainOps Intelligence — Executive Training Operations Report

**Report Generation Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Reporting Period:** {period_start} to {period_end}  
**As-Of Reference Date:** {as_of_date}  
**Insights Engine:** {"Groq GenAI (" + str(insights.get("model_used", "LLM")) + ")" if is_ai else "Deterministic Rule-Based Analytics Template"}

---

## 1. Executive Summary

{insights.get("executive_summary", "Operational training metrics aggregated across all active divisions.")}

---

## 2. Operational KPI Scorecard

| Metric | Result | Target Benchmark | Status & Formula |
| :--- | :---: | :---: | :--- |
| **Total Assignments** | {kpis.get('total_assignments', 0):,} | — | All enrollments in scope |
| **Unique Headcount** | {kpis.get('unique_employees', 0):,} | — | Distinct learners enrolled |
| **Completion Rate** | {kpis.get('completion_rate_formatted', '0.0%')} | >= 80.0% | Completed / Total Eligible |
| **Attendance Rate** | {kpis.get('attendance_rate_formatted', 'N/A')} | >= 90.0% | Attended / Tracked Synchronous |
| **Average Assessment Score** | {kpis.get('avg_assessment_score_formatted', 'N/A')} / 100 | >= 80.0 | Mean of valid completed tests |
| **Overdue Assignments** | {kpis.get('overdue_assignments', 0):,} | 0 | Uncompleted & past due date |
| **Mandatory Compliance Rate** | {kpis.get('mandatory_completion_rate_formatted', '0.0%')} | 100.0% | Mandatory completed / Mandatory total |
| **Completed Training Hours** | {kpis.get('total_completed_hours', 0.0):,.1f} hrs | — | Total verified curriculum hours delivered |

---

## 3. Key Operational Findings

"""
    for bullet in insights.get("key_findings", []):
        report_md += f"- {bullet}\n"

    report_md += """
---

## 4. Compliance Risks & Critical Exceptions

"""
    for risk in insights.get("risks_and_compliance_gaps", []):
        report_md += f"- **Risk:** {risk}\n"

    report_md += """
---

## 5. Department Performance Breakdown

| Department | Assignments | Completed | Completion Rate | Mandatory Rate | Overdue | Avg Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    if not dept_df.empty:
        for _, r in dept_df.iterrows():
            avg_sc_str = f"{r.get('avg_assessment_score'):.1f}" if pd.notna(r.get('avg_assessment_score')) else "N/A"
            report_md += f"| {r.get('department')} | {int(r.get('total_assignments', 0)):,} | {int(r.get('completed_assignments', 0)):,} | {r.get('completion_rate_pct'):.1f}% | {r.get('mandatory_completion_rate_pct'):.1f}% | {int(r.get('overdue_assignments', 0)):,} | {avg_sc_str} |\n"

    report_md += f"""
---

## 6. Recommended Action Plan

"""
    for action in insights.get("recommended_actions", []):
        report_md += f"- [ ] {action}\n"

    report_md += f"""
---

## 7. Data Quality & Audit Disclosures

- **Total Ingested Records:** {dq_summary.get('total_records', 0):,}
- **Validated Clean Records:** {dq_summary.get('valid_records', 0):,}
- **Flagged Quarantined Records:** {dq_summary.get('flagged_records', 0):,}
- **Duplicates Identified:** {dq_summary.get('duplicates', 0)}
- **Missing Required Identifiers:** {dq_summary.get('missing_fields', 0)}
- **Date Logic Anomalies:** {dq_summary.get('date_errors', 0)}
- **Score Range Errors:** {dq_summary.get('score_errors', 0)}

*Note: All quarantined records are held in the flagged review table and excluded from numeric KPI denominators to prevent metrics contamination.*
"""
    return report_md


def generate_full_report_workflow(
    df: pd.DataFrame,
    dq_summary: Dict[str, Any],
    flagged_df: pd.DataFrame,
    as_of_date: str,
    period_start: str,
    period_end: str,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """Execute end-to-end report generation workflow."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp_slug = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_id = f"RPT-{timestamp_slug}"

    # 1. Deterministic KPIs
    kpis = compute_kpis(df, as_of_date=as_of_date)
    dept_df = get_department_kpis(df, as_of_date=as_of_date)
    course_df = get_course_kpis(df, as_of_date=as_of_date)
    trends_df = get_monthly_completion_trends(df)

    # 2. Insights Synthesis
    payload = prepare_llm_payload(kpis, dept_df, course_df, dq_summary)
    insights, is_ai, status_msg = generate_management_insights(payload, api_key=api_key, model_name=model_name)

    # 3. Excel Workbook
    excel_filename = f"TrainOps_Report_{timestamp_slug}.xlsx"
    excel_path = generate_excel_workbook(
        clean_df=df,
        kpis=kpis,
        dept_df=dept_df,
        course_df=course_df,
        dq_summary=dq_summary,
        flagged_df=flagged_df,
        output_filename=excel_filename
    )
    # Also copy or save to OUTPUT_DIR
    output_excel_path = OUTPUT_DIR / excel_filename
    if excel_path.exists():
        import shutil
        shutil.copy(excel_path, output_excel_path)

    # 4. Markdown Briefing Document
    md_filename = f"TrainOps_Executive_Brief_{timestamp_slug}.md"
    md_content = generate_markdown_report(
        kpis=kpis,
        dept_df=dept_df,
        course_df=course_df,
        dq_summary=dq_summary,
        insights=insights,
        as_of_date=as_of_date,
        period_start=period_start,
        period_end=period_end,
        is_ai=is_ai
    )
    md_path = OUTPUT_DIR / md_filename
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 5. Log to SQLite
    report_meta = {
        "report_id": report_id,
        "reporting_period_start": period_start,
        "reporting_period_end": period_end,
        "as_of_date": as_of_date,
        "excel_filename": excel_filename,
        "markdown_filename": md_filename,
        "ai_assisted": is_ai,
        "kpis": kpis,
        "status": "COMPLETED"
    }
    log_report_generation(report_meta)

    return {
        "report_id": report_id,
        "excel_path": str(output_excel_path),
        "excel_filename": excel_filename,
        "markdown_path": str(md_path),
        "markdown_filename": md_filename,
        "markdown_content": md_content,
        "kpis": kpis,
        "insights": insights,
        "is_ai_assisted": is_ai,
        "status_message": status_msg
    }
