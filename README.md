# TrainOps Intelligence — Training Analytics, Reporting & AI Insights

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B.svg)](https://streamlit.io/)
[![Groq SDK](https://img.shields.io/badge/Groq%20API-Llama--3.3--70B-orange.svg)](https://groq.com/)
[![Tests](https://img.shields.io/badge/pytest-18%20passed-brightgreen.svg)](https://pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**TrainOps Intelligence** is an enterprise-grade corporate Learning & Development (L&D) analytics, data governance, and automated reporting application. It simulates how modern corporate HR/L&D operations teams manage thousands of employee training assignments, enforce data quality standards, monitor compliance KPIs, export model-ready data for Power BI and Excel, and leverage Generative AI (via the Groq Python SDK) to automate executive briefings.

---

## 1. Business Problem & Solution Overview

### The Corporate Challenge
Corporate training administration teams manage hundreds of mandatory compliance courses, leadership workshops, and technical certifications across multiple departments. They routinely encounter:
- **Data Quality Issues:** Fragmented LMS records, duplicate enrollments, inconsistent department naming ("IT" vs "Information Tech"), date order violations (completion before assignment), and invalid assessment scores.
- **Compliance Exposure:** Inability to pinpoint overdue mandatory courses before regulatory audits.
- **Reporting Burden:** Manual aggregation of spreadsheets into PowerPoint decks for senior leadership.
- **AI Hallucination Risk:** Pressure to adopt AI without governance or factual grounding.

### The Solution: TrainOps Intelligence
- **Data Quality & Validation Engine:** Automated validation pipeline that standardizes schema, detects duplicates, flags anomalies, and preserves an auditable quarantine log.
- **Deterministic Analytics Engine:** Rigorous KPI calculation engine with zero-division protection and an adjustable As-of reference date for reproducible overdue calculations.
- **Multi-Sheet Excel Automation:** Automatically generates styled 6-sheet `.xlsx` workbooks with frozen panes, formatting, and auto-filters.
- **Power BI Data Package:** One-click export of clean relational CSV fact and dimension tables.
- **Grounded Groq AI Integration:** Translates verified macro KPIs into structured executive management summaries (`executive_summary`, `key_findings`, `risks_and_compliance_gaps`, `recommended_actions`) with a deterministic rule-based fallback when offline.

---

## 2. Key Features

- **Executive KPI Dashboard:** Real-time visibility into Completion Rate, Mandatory Compliance, Overdue Assignments, Attendance Rate, Average Assessment Score, and Total Curriculum Hours.
- **Interactive Visualizations:** Monthly completion trends, department completion vs 80% benchmark, attendance by category, score distributions, and course hours.
- **Training Records Registry:** Fast search, pagination, detailed record inspector, and external dataset upload (CSV/Excel) with pre-import validation gating.
- **Data Governance Audit:** Quarantined record log explaining the exact reason each anomaly was rejected.
- **One-Click Management Report Generation:** Produces both a 6-worksheet Excel workbook and an executive Markdown brief, logged to an audit table in SQLite.
- **AI Prompt Transparency:** Full inspection of the grounded JSON payload and system prompt supplied to the LLM.

---

## 3. Technology Stack

- **Application & Dashboard:** [Streamlit](https://streamlit.io/) (Enterprise UI with custom Inter typography and navy theme)
- **Data Processing:** [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/)
- **Database:** Local [SQLite](https://www.sqlite.org/) with indexed fact and audit tables
- **Visualizations:** [Plotly](https://plotly.com/python/) (Custom corporate theme)
- **Excel Automation:** [openpyxl](https://openpyxl.readthedocs.io/) (Styled multi-sheet workbooks)
- **AI Integration:** [Groq Python SDK](https://console.groq.com/) (`llama-3.3-70b-versatile`)
- **Testing:** [pytest](https://docs.pytest.org/) (18 automated unit tests covering data generation, validation, KPIs, exports, and AI fallback)
- **Business Intelligence:** Microsoft Power BI Desktop & Excel Power Query (M)

---

## 4. Project Structure

```text
trainops-intelligence/
├── app.py                     # Main Streamlit analytics application
├── requirements.txt           # Project dependencies
├── .env.example               # Template environment variables
├── .env                       # Local configuration (ignored in git)
├── .gitignore                 # Git ignore rules
├── pytest.ini                 # Pytest pythonpath configuration
├── seed_db.py                 # Database initialization and export generator
├── README.md                  # Comprehensive documentation
├── data/
│   ├── raw/                   # Intentionally flawed raw dataset (raw_training_records.csv)
│   ├── processed/             # Clean reference dataset (clean_training_records_reference.csv)
│   ├── exports/               # Power BI CSVs and master Excel workbooks
│   └── trainops.db            # Local SQLite database
├── src/
│   ├── __init__.py
│   ├── config.py              # Environment variables, file paths, and canonical maps
│   ├── data_generator.py      # Deterministic synthetic data generator (seed 42)
│   ├── database.py            # SQLite schema, persistence, and audit logging
│   ├── validation.py          # Data quality rules, standardization, and quarantine logic
│   ├── analytics.py           # Deterministic KPI calculations and aggregations
│   ├── excel_export.py        # 6-sheet corporate Excel workbook generator
│   ├── power_bi_export.py     # Power BI relational CSV package generator
│   ├── reporting.py           # End-to-end report generation workflow
│   ├── ai_insights.py         # Groq LLM integration and deterministic fallback
│   └── utils.py               # Enterprise CSS styling and Plotly chart layouts
├── tests/
│   ├── test_data_generator.py # Tests for determinism, counts, and anomaly injection
│   ├── test_validation.py     # Tests for duplicates, date violations, and scores
│   ├── test_analytics.py      # Tests for zero-division, KPIs, and overdue logic
│   ├── test_exports.py        # Tests for Excel sheets and Power BI CSV schemas
│   └── test_ai_insights.py    # Tests for AI payload safety, fallback, and reporting
├── docs/
│   ├── POWER_BI_GUIDE.md      # Power BI modeling, star schema, DAX measures, and refresh
│   ├── EXCEL_POWER_QUERY_GUIDE.md # Power Query (M) cleaning script and workbook structure
│   ├── KPI_DEFINITIONS.md     # Official mathematical formulas and edge-case rules
│   └── ARCHITECTURE.md        # Technical architecture, schemas, and AI governance
└── output/                    # Timestamped generated reports (Excel & Markdown)
```

---

## 5. Installation & Setup (Windows)

### Prerequisites
- Python 3.10 to 3.13 installed. Verify via PowerShell:
  ```powershell
  python --version
  ```

### Step 1: Clone or Navigate to Repository
```powershell
cd "d:\DATA ANALYTICS\trainops-intelligence"
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Open `.env` in any text editor and optionally configure your Groq API key:
```ini
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```
> **Note:** If you do not have a Groq API key, leave `GROQ_API_KEY=` blank. The application will seamlessly use its built-in **Deterministic Verified Analytics Fallback Engine**, keeping 100% of the dashboard and reporting workflow operational!

### Step 5: Seed the Database & Generate Initial Assets
```powershell
python -m seed_db
```
This command:
1. Generates 1,250 synthetic records deterministically.
2. Injects controlled data-quality anomalies into the raw dataset.
3. Runs the validation pipeline to quarantine anomalies.
4. Initializes and seeds the SQLite database (`data/trainops.db`).
5. Generates the master Power BI CSV data package in `data/exports/`.
6. Generates the master Excel workbook `data/exports/TrainOps_Master_Report.xlsx`.

---

## 6. How to Run the Application

Launch the Streamlit analytics application:
```powershell
streamlit run app.py
```
Open your browser to: **`http://localhost:8501`**

---

## 7. How to Run the Automated Test Suite

Run the full pytest test suite:
```powershell
pytest -v
```
All 18 unit tests should pass:
```text
tests/test_ai_insights.py::test_prepare_llm_payload_aggregates_safely PASSED
tests/test_ai_insights.py::test_deterministic_fallback_schema_and_content PASSED
tests/test_ai_insights.py::test_generate_insights_without_api_key PASSED
tests/test_ai_insights.py::test_report_workflow_end_to_end PASSED
tests/test_analytics.py::test_empty_dataset_kpis PASSED
tests/test_analytics.py::test_standard_kpi_calculations PASSED
tests/test_analytics.py::test_department_and_course_aggregations PASSED
tests/test_data_generator.py::test_clean_dataset_generation_count_and_columns PASSED
tests/test_data_generator.py::test_dataset_reproducibility PASSED
tests/test_data_generator.py::test_clean_dataset_logical_integrity PASSED
tests/test_data_generator.py::test_flawed_raw_dataset_injects_anomalies PASSED
tests/test_exports.py::test_excel_workbook_generation_and_sheets PASSED
tests/test_exports.py::test_power_bi_csv_export_package PASSED
tests/test_validation.py::test_standardize_department PASSED
tests/test_validation.py::test_standardize_status PASSED
tests/test_validation.py::test_duplicate_detection PASSED
tests/test_validation.py::test_date_relationship_violations PASSED
tests/test_validation.py::test_invalid_assessment_scores PASSED
============================= 18 passed in 2.39s =============================
```

---

## 8. Responsible AI, Privacy & Synthetic Data Considerations

- **100% Synthetic Data:** All employee names, IDs, departments, courses, and scores are deterministically generated synthetic data. No real employee personal identifiable information (PII) is used.
- **Privacy Gating:** Only high-level macro statistics (counts, percentages, top/lagging departments) are ever sent to the LLM API. Individual employee records and IDs are strictly excluded from AI prompts.
- **Strict Grounding:** The LLM prompt prohibits extrapolation, hallucinated metrics, or attributing causes without data. All calculations are executed deterministically in Python/SQL.
- **Zero Downtime Fallback:** When the Groq API key is not present or an API error occurs, the system automatically uses a deterministic template clearly labeled as such.

---

## 9. Power BI and Excel Integration

- For complete instructions on importing CSVs, building relationships, creating DAX measures, and dashboard construction, see [POWER_BI_GUIDE.md](docs/POWER_BI_GUIDE.md).
- For Power Query (M) script and Excel workbook architecture, see [EXCEL_POWER_QUERY_GUIDE.md](docs/EXCEL_POWER_QUERY_GUIDE.md).
- For mathematical definitions and denominator treatments, see [KPI_DEFINITIONS.md](docs/KPI_DEFINITIONS.md).
- For technical schemas and architectural blueprints, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 10. Known Limitations & Future Enhancements

- **Current Scope:** Designed for local single-node execution using SQLite; multi-tenant cloud deployments would benefit from PostgreSQL and object storage (e.g., S3/GCS) for exported workbooks.
- **LMS API Webhooks:** Future versions could integrate live webhooks to pull real-time SCORM/xAPI completions from platforms like Cornerstone, Workday Learning, or Canvas.
- **Automated Scheduling:** Future iterations could include a Celery or cron worker to trigger weekly automated report generation to an executive email distribution list.
