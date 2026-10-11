# Power BI Implementation Guide — TrainOps Intelligence

This guide provides end-to-end instructions for loading, modeling, and visualizing the **TrainOps Intelligence** data package in Microsoft Power BI Desktop.

---

## 1. Overview of Exported Datasets

When you click **Export Power BI Data Package** in the application (or run `python -m seed_db`), five clean, schema-stabilized CSV files are generated in `data/exports/`:

| File Name | Role in Model | Key Columns | Grain |
| :--- | :--- | :--- | :--- |
| `training_records_clean.csv` | **Fact Table** | `record_id`, `employee_id`, `department`, `course_id`, `assigned_date`, `due_date`, `completion_date`, `completion_status`, `assessment_score`, `training_hours`, `mandatory_training` | One row per training enrollment |
| `department_kpis.csv` | **Dimension / Summary** | `department`, `total_assignments`, `unique_employees`, `completion_rate_pct`, `mandatory_completion_rate_pct`, `overdue_assignments`, `completed_training_hours` | One row per canonical department |
| `course_kpis.csv` | **Dimension / Catalog** | `course_id`, `course_name`, `training_category`, `mandatory_training`, `delivery_mode`, `unit_hours`, `total_assignments` | One row per course |
| `monthly_training_trends.csv` | **Time-Series Dimension** | `completion_month`, `completions`, `total_hours`, `avg_score`, `cumulative_completions` | One row per month (`YYYY-MM`) |
| `data_quality_summary.csv` | **Audit Table** | `metric_name`, `metric_value` | Key-value pairs for ingestion quality |

---

## 2. Importing Files into Power BI Desktop

1. Launch **Power BI Desktop**.
2. On the **Home** tab, select **Get Data** > **Text/CSV**.
3. Navigate to the project directory: `d:\DATA ANALYTICS\trainops-intelligence\data\exports\`.
4. Select `training_records_clean.csv` and click **Open**.
5. In the preview dialog, click **Transform Data** to open Power Query Editor.
6. Verify and set data types:
   - `record_id`: Text
   - `employee_id`: Text
   - `department`: Text
   - `assigned_date`: Date
   - `due_date`: Date
   - `completion_date`: Date
   - `mandatory_training`: True/False
   - `assessment_score`: Decimal Number
   - `training_hours`: Decimal Number
7. Repeat **New Source** > **CSV** for:
   - `department_kpis.csv`
   - `course_kpis.csv`
   - `monthly_training_trends.csv`
   - `data_quality_summary.csv`
8. Click **Close & Apply**.

---

## 3. Data Modeling & Relationships

In the **Model View** tab of Power BI Desktop:

1. **Star Schema Architecture:**
   - Fact Table: `training_records_clean`
   - Dimensions: `department_kpis` and `course_kpis`
2. **Relationships:**
   - Link `department_kpis[department]` (1) to `training_records_clean[department]` (*) — Cardinality: **1 to Many (1:*)**, Cross filter direction: **Single**.
   - Link `course_kpis[course_id]` (1) to `training_records_clean[course_id]` (*) — Cardinality: **1 to Many (1:*)**, Cross filter direction: **Single**.
3. **Dedicated Date Table (Recommended):**
   In Power BI, click **Modeling** > **New Table** and enter:
   ```dax
   DimDate = 
   ADDCOLUMNS(
       CALENDAR(DATE(2026, 1, 1), DATE(2026, 12, 31)),
       "Year", YEAR([Date]),
       "MonthNumber", MONTH([Date]),
       "MonthName", FORMAT([Date], "mmmm"),
       "MonthYear", FORMAT([Date], "yyyy-mm"),
       "Quarter", "Q" & FORMAT([Date], "q")
   )
   ```
   Link `DimDate[Date]` (1) to `training_records_clean[assigned_date]` (*).

---

## 4. DAX Measures (Reconciled with TrainOps Python Engine)

Create a dedicated measure table called `_Measures`. Add the following DAX measures:

### Total Assignments
```dax
Total Assignments = COUNTROWS('training_records_clean')
```

### Unique Employees Assigned
```dax
Unique Learners = DISTINCTCOUNT('training_records_clean'[employee_id])
```

### Training Completion Rate (%)
```dax
Completion Rate % = 
VAR CompletedCount = CALCULATE(
    COUNTROWS('training_records_clean'),
    'training_records_clean'[completion_status] = "Completed"
)
VAR TotalCount = COUNTROWS('training_records_clean')
RETURN
DIVIDE(CompletedCount, TotalCount, 0)
```
*Format as Percentage (0.0%).*

### Attendance Rate (%)
```dax
Attendance Rate % = 
VAR AttendedCount = CALCULATE(
    COUNTROWS('training_records_clean'),
    'training_records_clean'[attendance_status] = "Attended"
)
VAR TrackedTotal = CALCULATE(
    COUNTROWS('training_records_clean'),
    'training_records_clean'[attendance_status] IN {"Attended", "Partial", "Absent"}
)
RETURN
DIVIDE(AttendedCount, TrackedTotal, 1.0)
```
*Format as Percentage (0.0%).*

### Mandatory Training Completion Rate (%)
```dax
Mandatory Completion Rate % = 
VAR MandCompleted = CALCULATE(
    COUNTROWS('training_records_clean'),
    'training_records_clean'[completion_status] = "Completed",
    'training_records_clean'[mandatory_training] = TRUE()
)
VAR MandTotal = CALCULATE(
    COUNTROWS('training_records_clean'),
    'training_records_clean'[mandatory_training] = TRUE()
)
RETURN
DIVIDE(MandCompleted, MandTotal, 0)
```
*Format as Percentage (0.0%).*

### Overdue Training Assignments
```dax
AsOfReferenceDate = DATE(2026, 10, 15)

Overdue Assignments = 
CALCULATE(
    COUNTROWS('training_records_clean'),
    'training_records_clean'[completion_status] <> "Completed",
    'training_records_clean'[due_date] < [AsOfReferenceDate]
)
```

### Average Assessment Score
```dax
Average Assessment Score = 
AVERAGE('training_records_clean'[assessment_score])
```
*Format as Decimal (0.0).*

### Total Completed Training Hours
```dax
Completed Training Hours = 
CALCULATE(
    SUM('training_records_clean'[training_hours]),
    'training_records_clean'[completion_status] = "Completed"
)
```

---

## 5. Building the Dashboard Canvas

Configure visuals matching the TrainOps application layout:

1. **Top Row — KPI Cards:**
   - Card 1: `[Total Assignments]`
   - Card 2: `[Completion Rate %]`
   - Card 3: `[Mandatory Completion Rate %]`
   - Card 4: `[Overdue Assignments]`
   - Card 5: `[Attendance Rate %]`
   - Card 6: `[Average Assessment Score]`
   - Card 7: `[Completed Training Hours]`
2. **Visual 1 — Clustered Bar Chart:**
   - Axis (Y): `department_kpis[department]`
   - Values (X): `[Completion Rate %]`
   - Add Constant Line at `0.80` (80% target).
3. **Visual 2 — Line & Clustered Column Chart:**
   - Shared Axis (X): `monthly_training_trends[completion_month]`
   - Column Values: `monthly_training_trends[total_hours]`
   - Line Values: `monthly_training_trends[completions]`
4. **Visual 3 — Donut Chart:**
   - Legend: `training_records_clean[completion_status]`
   - Values: `[Total Assignments]`
5. **Visual 4 — Matrix Table:**
   - Rows: `department_kpis[department]`
   - Columns/Values: `[Total Assignments]`, `[Completion Rate %]`, `[Mandatory Completion Rate %]`, `[Overdue Assignments]`, `[Average Assessment Score]`
6. **Slicers:**
   - Slicer 1: `training_records_clean[department]`
   - Slicer 2: `course_kpis[training_category]`
   - Slicer 3: `course_kpis[mandatory_training]`
   - Slicer 4: Date Range slider on `DimDate[Date]`.

---

## 6. Verifying Reconciliation with Python

To confirm that Power BI matches the Python Streamlit engine:
1. Set the date slicer to the entire range (`2026-01-15` to `2026-09-30`).
2. Verify total records = **1,139** (clean validated records).
3. Verify overall completion rate = **78.0%**.
4. Verify mandatory compliance rate = **76.5%**.
5. Verify overdue assignments = **225**.
6. Verify average assessment score = **83.7**.

When both tools yield identical values down to the decimal point, your data governance reconciliation is certified.

---

## 7. Dataset Refresh Workflow

When you import new employee records or click **Reset / Regenerate** in the application:
1. The updated files are automatically re-written to `data/exports/`.
2. In Power BI Desktop, click **Home** > **Refresh**.
3. Power BI re-evaluates all DAX measures and re-renders visuals automatically.
