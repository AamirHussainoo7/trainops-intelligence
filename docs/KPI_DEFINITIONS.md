# KPI Definitions & Measurement Standards — TrainOps Intelligence

This document specifies the exact business rules, mathematical formulas, and governance treatment applied by the TrainOps analytics engine.

---

## 1. Summary Metric Reference

| KPI Name | Target / Benchmark | Formula | Denominator Treatment | Edge Case Rule |
| :--- | :--- | :--- | :--- | :--- |
| **Total Training Assignments** | Operating Volume | $\sum \text{Eligible Records}$ | All active records within filter scope | Empty filter returns `0`. |
| **Unique Employees Assigned** | Headcount Reach | $\text{Count Distinct}(\text{employee\_id})$ | Enrolled learners | Deduplicates multiple course assignments per employee. |
| **Training Completion Rate** | $\ge 80.0\%$ | $\frac{\text{Completed Assignments}}{\text{Total Eligible Assignments}} \times 100$ | Total filtered records | If denominator = 0, returns `0.0%`. |
| **Attendance Rate** | $\ge 90.0\%$ | $\frac{\text{Attended Sessions}}{\text{Tracked Attendance Sessions}} \times 100$ | Sessions with status $\in$ [`Attended`, `Partial`, `Absent`] | Asynchronous/self-paced courses are excluded or return `100.0%`. |
| **Average Assessment Score** | $\ge 80.0$ | $\frac{\sum \text{Assessment Score}}{\text{Count}(\text{Graded Assignments})}$ | Completed assignments with non-null scores | Returns `N/A` if no scored courses exist. |
| **Overdue Training Assignments** | $0$ (Zero Tolerance) | $\sum [\text{status} \ne \text{Completed} \land \text{due\_date} < \text{as\_of\_date}]$ | Total active assignments | Controlled via configurable **As-of Reference Date**. |
| **Mandatory Compliance Rate** | $100.0\%$ | $\frac{\text{Completed Mandatory}}{\text{Total Mandatory}} \times 100$ | Only records where `mandatory_training == True` | If no mandatory courses in scope, returns `N/A`. |
| **Total Completed Training Hours** | Curriculum Volume | $\sum \text{training\_hours} \text{ for Completed records}$ | Completed records only | Excludes uncompleted or in-progress hours. |

---

## 2. Detailed Calculation Rules & Edge Cases

### Rule 1: Training Completion Rate
- **Numerator:** Count of assignments where `completion_status == "Completed"`.
- **Denominator:** Total training assignments matching the active filters (reporting period, department, category, etc.).
- **Zero-Denominator Defense:** If the active filters match 0 records, the function deterministically yields `0.0%` rather than throwing a `ZeroDivisionError`.
- **Exclusion of Flagged Records:** Records quarantined during ingestion validation (e.g., duplicate assignments, date sequence violations) are excluded from both numerator and denominator.

### Rule 2: Attendance Rate
- **Business Rationale:** Synchronous sessions (Virtual Instructor-Led, Classroom, Hybrid Workshops) require attendance verification. Asynchronous e-learning courses are self-paced and do not have an in-person roll call.
- **Numerator:** Records where `attendance_status == "Attended"`.
- **Denominator:** Records with explicit synchronous tracking outcomes (`attendance_status` is one of `Attended`, `Partial`, or `Absent`).
- **Edge Case:** If a filter contains exclusively self-paced courses, the attendance rate is presented as `"100.0% (Self-Paced)"` to prevent misrepresenting compliance.

### Rule 3: Average Assessment Score
- **Numerator:** Sum of numerical scores for validated completed assessments.
- **Denominator:** Count of records with valid numeric scores $\in [0.0, 100.0]$.
- **Edge Case:** Non-graded courses or courses where learners are in-progress return `null`. The average score function ignores nulls and computes the mean only over scored records. If no scored records exist, it displays `"N/A"`.

### Rule 4: Overdue Training Assignments
- **Overdue Definition:** An assignment is deemed overdue if:
  1. `completion_status != "Completed"` (i.e. status is "In Progress" or "Not Started"), **AND**
  2. `due_date < as_of_date`.
- **Reproducibility with As-of Date:** To support reproducible audit reporting across historical quarters, the user can configure an arbitrary reference date (default: `2026-10-15`). All overdue calculations evaluate against this exact date.

### Rule 5: Mandatory Compliance Rate
- **Numerator:** Count of assignments where `mandatory_training == True` AND `completion_status == "Completed"`.
- **Denominator:** Count of assignments where `mandatory_training == True`.
- **Target:** 100% compliance is legally or contractually mandated for regulatory courses (AML, Data Privacy, Workplace Safety, Cybersecurity). Any shortfall is highlighted with an alert badge in the UI.

---

## 3. Quarantined Record Governance

To guarantee metrics accuracy:
1. Records failing critical checks (e.g. missing employee IDs, unparseable dates, scores $>100$, or completion date prior to assignment date) are written to `flagged_records` in SQLite.
2. Quarantined records are **never silently deleted** or modified without audit traces.
3. Quarantined records are isolated from the clean fact table (`clean_training_records`) so that they do not contaminate executive scorecard calculations.
