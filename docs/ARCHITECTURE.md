# System Architecture & Technical Specifications — TrainOps Intelligence

This document details the architectural design, database schemas, validation pipelines, and responsible AI mechanics behind **TrainOps Intelligence**.

---

## 1. Architectural Overview & Component Boundaries

The project is structured with a strict separation of concerns across generation, ingestion, validation, persistence, analytics, reporting, and presentation:

```
[ Ingestion & Generation ] 
        │
        ▼
[ Validation & Quality Pipeline ] ─── (src/validation.py)
        │
        ├──▶ Flagged Quarantine Table (flagged_records in SQLite)
        │
        ▼
[ Relational Storage Engine ] ──────── (src/database.py & SQLite)
        │
        ├──▶ clean_training_records (Indexed Fact Table)
        ├──▶ raw_training_records
        ├──▶ validation_runs (Audit History)
        └──▶ report_history (Generation Logs)
        │
        ▼
[ Deterministic Analytics Engine ] ─── (src/analytics.py)
        │
        ├──▶ KPIs & Ratios (Zero-division safeguarded)
        ├──▶ Departmental & Course Aggregations
        └──▶ Time-Series Trend Aggregations
        │
        ├───────────────────────────────┬───────────────────────────────┐
        ▼                               ▼                               ▼
[ Multi-Sheet Excel Engine ]    [ Power BI Export Engine ]    [ Groq AI Insights Engine ]
 (src/excel_export.py)           (src/power_bi_export.py)      (src/ai_insights.py)
   ├── Executive Summary           ├── Fact & Dimension CSVs    ├── Factual JSON Schema
   ├── Training Records            └── Relational Models        ├── Grounded System Prompt
   ├── Department KPIs                                          └── Deterministic Fallback
   ├── Course KPIs
   ├── Data Quality Report
   └── Data Dictionary
        │                               │                               │
        └───────────────────────────────┼───────────────────────────────┘
                                        │
                                        ▼
                        [ Interactive Streamlit UI ]
                                 (app.py)
                        ├── 1. Overview Dashboard
                        ├── 2. Training Records
                        ├── 3. Data Quality & Validation
                        ├── 4. Reports & Exports
                        ├── 5. AI Insights
                        └── 6. Data Dictionary & Methodology
```

---

## 2. Relational Database Schema (SQLite)

The local SQLite database (`data/trainops.db`) provides relational persistence with parameterized queries:

### 1. `clean_training_records` (Fact Table)
- `record_id` (TEXT PRIMARY KEY)
- `employee_id` (TEXT NOT NULL)
- `employee_name` (TEXT NOT NULL)
- `department` (TEXT NOT NULL) — Canonical name
- `job_level` (TEXT)
- `course_id` (TEXT NOT NULL)
- `course_name` (TEXT NOT NULL)
- `training_category` (TEXT NOT NULL)
- `mandatory_training` (INTEGER NOT NULL) — 1 / 0
- `assigned_date` (TEXT NOT NULL) — `YYYY-MM-DD`
- `due_date` (TEXT NOT NULL) — `YYYY-MM-DD`
- `completion_date` (TEXT) — `YYYY-MM-DD` or NULL
- `attendance_status` (TEXT)
- `completion_status` (TEXT NOT NULL) — Completed, In Progress, Not Started
- `assessment_score` (REAL) — 0.0 to 100.0 or NULL
- `training_hours` (REAL NOT NULL)
- `delivery_mode` (TEXT)
- `instructor` (TEXT)
- `region` (TEXT)
- `is_overdue` (INTEGER DEFAULT 0)
- `updated_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

**Indexes:**
- `idx_clean_dept` on `department`
- `idx_clean_course` on `course_id`
- `idx_clean_status` on `completion_status`
- `idx_clean_assigned` on `assigned_date`
- `idx_clean_due` on `due_date`
- `idx_clean_mandatory` on `mandatory_training`

### 2. `flagged_records` (Quarantine Audit)
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `record_id` (TEXT)
- `employee_id` (TEXT)
- `course_id` (TEXT)
- `issue_type` (TEXT NOT NULL)
- `issue_severity` (TEXT NOT NULL)
- `issue_description` (TEXT NOT NULL)
- `raw_data_json` (TEXT NOT NULL) — Preserves full original row for auditability
- `flagged_at` (TIMESTAMP DEFAULT CURRENT_TIMESTAMP)

### 3. `validation_runs` (Audit Trail)
- `run_id` (TEXT PRIMARY KEY)
- `run_timestamp` (TIMESTAMP)
- `total_records_processed` (INTEGER)
- `valid_records_count` (INTEGER)
- `flagged_records_count` (INTEGER)
- `duplicate_records_count` (INTEGER)
- `missing_fields_count` (INTEGER)
- `date_errors_count` (INTEGER)
- `score_errors_count` (INTEGER)
- `summary_json` (TEXT)

### 4. `report_history` (Report Audit Log)
- `report_id` (TEXT PRIMARY KEY)
- `generated_at` (TIMESTAMP)
- `reporting_period_start` (TEXT)
- `reporting_period_end` (TEXT)
- `as_of_date` (TEXT)
- `excel_filename` (TEXT)
- `markdown_filename` (TEXT)
- `ai_assisted` (INTEGER)
- `kpis_json` (TEXT)
- `status` (TEXT)

---

## 3. Data Validation & Transformation Rules

1. **Schema Check:** Verifies presence of all 10 critical columns.
2. **Key Uniqueness:** Identifies duplicate `record_id` and duplicate `(employee_id, course_id, assigned_date)` tuples.
3. **Department Standardization:** Uses synonym map (`DEPARTMENT_SYNONYMS`) to normalize values (e.g., "IT" -> "Information Technology", "Ops" -> "Operations", "HR" -> "Human Resources").
4. **Status Normalization:** Maps variations ("done", "finished", "completed ") to canonical enum `Completed`.
5. **Date Logic:**
   - Enforces `assigned_date <= due_date`.
   - Enforces `assigned_date <= completion_date` for completed records.
6. **Score Bounds:** Enforces $0.0 \le \text{score} \le 100.0$.
7. **Quarantine Logic:** Any record failing a critical rule is preserved in `flagged_records` with raw JSON and excluded from `clean_training_records`.

---

## 4. Responsible AI & Groq LLM Integration

### Strict Grounding Principles
- **No Calculation Delegation:** Numeric calculations are executed exclusively by Python or SQL. The LLM is never asked to calculate sums, averages, or percentages.
- **Aggregated Payloads Only:** Only macro metrics (KPI counts, top/lagging departments, course hours, data quality summary) are submitted to the LLM. Individual employee records and IDs are strictly excluded to protect privacy.
- **Factual System Prompt:** The system prompt explicitly instructs the model:
  - Do not hallucinate statistics or department names.
  - Distinguish observed metrics from recommendations.
  - Return JSON conforming strictly to `{executive_summary, key_findings, risks_and_compliance_gaps, recommended_actions}`.
- **Deterministic Rule-Based Fallback:** If `GROQ_API_KEY` is absent or the API returns an error, the system automatically activates a deterministic rule-based template that compiles verified metrics without downtime.
- **Explainability:** The UI provides an **AI Prompt Transparency** drawer displaying the exact JSON payload, system prompt, and response source.
