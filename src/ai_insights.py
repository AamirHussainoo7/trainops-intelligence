"""Groq AI Insights & Management Reporting Engine for TrainOps Intelligence.

Provides grounded GenAI analysis via Groq SDK with strict factual bounds,
structured JSON response schemas, prompt inspection transparency, and a robust
deterministic template-based fallback when no API key is configured or requests fail.
"""

from datetime import datetime
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from groq import Groq
from src.config import GROQ_API_KEY, GROQ_MODEL

SYSTEM_PROMPT = """You are an executive Training Operations & Analytics Advisor assisting corporate leadership.
Your role is to analyze the provided deterministic KPIs and aggregated training metrics and produce an executive-ready operational summary.

STRICT FACTUAL GROUNDING RULES:
1. Ground every statement strictly in the provided metrics snapshot.
2. NEVER invent, extrapolate, or hallucinate metrics, percentages, department names, root causes, or headcount figures.
3. Distinguish directly observed facts from recommendations or hypotheses.
4. Do not assume or assert employee motivations or why a department underperformed without evidence.
5. Reference the specific denominator or reporting period where appropriate.
6. Clearly disclose any data-quality limitations or flagged record counts.
7. Maintain an executive, constructive, and concise tone.
8. NEVER include personally identifiable individual employee names or IDs.

OUTPUT FORMAT REQUIREMENTS:
You MUST respond with valid JSON ONLY (do not include markdown ticks ```json ... ``` outside or inside the JSON string).
Your JSON must strictly conform to this schema:
{
  "executive_summary": "2-3 concise paragraphs summarizing overarching training operations health, completion rate, overdue volume, and compliance status.",
  "key_findings": [
    "String bullet point 1 citing specific metrics",
    "String bullet point 2 citing department or course performance",
    "String bullet point 3 citing attendance or scores"
  ],
  "risks_and_compliance_gaps": [
    "Risk bullet 1 highlighting overdue mandatory courses or low compliance units",
    "Risk bullet 2 regarding assessment score anomalies or data validation flags"
  ],
  "recommended_actions": [
    "Action item 1 for Department Managers and L&D coordinators with timeline",
    "Action item 2 regarding LMS notifications or re-engagement",
    "Action item 3 regarding data governance follow-up"
  ]
}
"""


def _generate_deterministic_fallback(
    metrics_payload: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate a high-quality, completely factual deterministic summary when LLM is offline."""
    kpis = metrics_payload.get("kpis", {})
    top_depts = metrics_payload.get("top_departments", [])
    lagging_depts = metrics_payload.get("lagging_departments", [])
    top_courses = metrics_payload.get("top_courses", [])
    dq = metrics_payload.get("data_quality_summary", {})
    as_of = metrics_payload.get("as_of_date", datetime.today().strftime("%Y-%m-%d"))

    total = kpis.get("total_assignments", 0)
    completed = kpis.get("completed_assignments", 0)
    comp_rate = kpis.get("completion_rate_pct", 0.0)
    mand_rate = kpis.get("mandatory_completion_rate_pct", 0.0)
    overdue = kpis.get("overdue_assignments", 0)
    avg_score = kpis.get("avg_assessment_score", "N/A")
    hours = kpis.get("total_completed_hours", 0.0)
    attend_rate = kpis.get("attendance_rate_formatted", "N/A")

    # High and low departments
    top_dept_str = ", ".join([f"{d.get('department')} ({d.get('completion_rate_pct')}%)" for d in top_depts[:2]]) if top_depts else "N/A"
    lag_dept_str = ", ".join([f"{d.get('department')} ({d.get('completion_rate_pct')}%)" for d in lagging_depts[:2]]) if lagging_depts else "N/A"

    exec_summary = (
        f"As of reference date {as_of}, the organization has recorded a total of {total:,} training assignments across all divisions, "
        f"achieving an overall completion rate of {comp_rate:.1f}% ({completed:,} completed assignments) and delivering {hours:,.1f} cumulative training hours. "
        f"Mandatory compliance training completion currently stands at {mand_rate:.1f}%. "
        f"A total of {overdue:,} assignments are overdue relative to their assigned deadlines and require prompt intervention."
    )

    findings = [
        f"Overall training completion rate is {comp_rate:.1f}%, with {completed:,} out of {total:,} enrolled assignments marked Completed.",
        f"Mandatory regulatory compliance completion stands at {mand_rate:.1f}%, while optional skills training completed at {kpis.get('optional_completion_rate_pct', 0.0):.1f}%.",
        f"Average learner assessment score across completed courses is {avg_score} (out of 100), reflecting solid subject matter mastery.",
        f"Leading completion departments include {top_dept_str}, whereas departments requiring operational focus include {lag_dept_str}."
    ]

    risks = [
        f"{overdue:,} training assignments are currently past due as of {as_of}, representing potential audit exposure in mandatory categories.",
        f"Data quality ingestion pipeline flagged {dq.get('flagged_records', 0):,} records ({dq.get('duplicates', 0)} duplicates, {dq.get('missing_fields', 0)} missing keys) which are quarantined from KPI metrics."
    ]

    actions = [
        "L&D Operations: Issue automated escalation reminders to learners and line managers with overdue mandatory assignments.",
        f"Department Leads in {lag_dept_str}: Schedule dedicated department catch-up study hours prior to end-of-quarter audits.",
        "Data Governance: Review quarantined ingestion records in the Data Quality table to resolve missing employee identifiers and date formatting anomalies."
    ]

    return {
        "executive_summary": exec_summary,
        "key_findings": findings,
        "risks_and_compliance_gaps": risks,
        "recommended_actions": actions,
        "source": "DETERMINISTIC_FALLBACK",
        "model_used": "Deterministic Rule-Based Analytics Template",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def prepare_llm_payload(
    kpis: Dict[str, Any],
    dept_df: Any,
    course_df: Any,
    dq_summary: Dict[str, Any]
) -> Dict[str, Any]:
    """Aggregate high-level numeric metrics for safe submission to LLM."""
    top_depts = []
    lagging_depts = []
    if hasattr(dept_df, "empty") and not dept_df.empty:
        records = dept_df.to_dict(orient="records")
        sorted_depts = sorted(records, key=lambda x: x.get("completion_rate_pct", 0), reverse=True)
        top_depts = sorted_depts[:3]
        lagging_depts = sorted_depts[-3:]

    top_courses = []
    if hasattr(course_df, "empty") and not course_df.empty:
        c_records = course_df.to_dict(orient="records")
        top_courses = sorted(c_records, key=lambda x: x.get("total_assignments", 0), reverse=True)[:5]

    return {
        "as_of_date": kpis.get("as_of_date"),
        "kpis": kpis,
        "top_departments": top_depts,
        "lagging_departments": lagging_depts,
        "top_courses": top_courses,
        "data_quality_summary": {
            "total_records": dq_summary.get("total_records", 0),
            "valid_records": dq_summary.get("valid_records", 0),
            "flagged_records": dq_summary.get("flagged_records", 0),
            "duplicates": dq_summary.get("duplicates", 0),
            "missing_fields": dq_summary.get("missing_fields", 0),
            "date_errors": dq_summary.get("date_errors", 0),
            "score_errors": dq_summary.get("score_errors", 0),
        }
    }


def generate_management_insights(
    payload: Dict[str, Any],
    api_key: Optional[str] = None,
    model_name: Optional[str] = None
) -> Tuple[Dict[str, Any], bool, str]:
    """Generate management insights using Groq API, falling back to deterministic template if unavailable.
    
    Returns:
        (insights_dict, is_ai_generated, status_message)
    """
    effective_api_key = api_key if (api_key and api_key.strip()) else GROQ_API_KEY
    effective_model = model_name if (model_name and model_name.strip()) else GROQ_MODEL

    # If no API key configured, return deterministic fallback
    if not effective_api_key or not effective_api_key.strip() or effective_api_key == "your_groq_api_key_here":
        fallback = _generate_deterministic_fallback(payload)
        return (
            fallback,
            False,
            "Groq API key not configured. Displaying verified deterministic rule-based management summary."
        )

    # Attempt calling Groq API
    try:
        client = Groq(api_key=effective_api_key)
        user_prompt = f"Please analyze this training operations metrics snapshot and generate the executive summary JSON:\n\n{json.dumps(payload, indent=2)}"

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            model=effective_model,
            temperature=0.2,  # Low temperature for strict factual accuracy
            max_tokens=1500,
            response_format={"type": "json_object"}
        )

        response_content = chat_completion.choices[0].message.content

        # Parse JSON
        parsed_json = json.loads(response_content)

        # Validate required schema keys
        required_keys = ["executive_summary", "key_findings", "risks_and_compliance_gaps", "recommended_actions"]
        for k in required_keys:
            if k not in parsed_json:
                raise ValueError(f"Missing required response key: '{k}'")

        parsed_json["source"] = "GROQ_LLM"
        parsed_json["model_used"] = effective_model
        parsed_json["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return parsed_json, True, f"Successfully generated AI management insights using Groq ({effective_model})."

    except Exception as e:
        error_msg = f"Groq API call error ({type(e).__name__}): {str(e)}. Fallback activated."
        fallback = _generate_deterministic_fallback(payload)
        fallback["error_details"] = str(e)
        return fallback, False, error_msg
