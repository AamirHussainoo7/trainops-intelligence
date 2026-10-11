# Excel & Power Query Workflow Guide — TrainOps Intelligence

This guide documents the automated Excel workbook structure and provides copy-paste ready Power Query (M) scripts for transforming raw corporate training records directly within Microsoft Excel.

---

## 1. Automated Excel Workbook Structure

The TrainOps application automatically generates a 6-worksheet `.xlsx` workbook using `openpyxl`. The workbook follows corporate enterprise design principles:

### Worksheet Breakdown

1. **Executive Summary**
   - High-level KPI Scorecard with baseline benchmarks.
   - Dynamic departmental performance snapshot table.
   - Generation metadata (run timestamp, as-of reference date, scope).
2. **Training Records**
   - Filtered active training records.
   - Frozen header row (`A2`).
   - Excel AutoFilter enabled across all columns (`A1:S[N]`).
   - Standardized number and date formats.
3. **Department KPIs**
   - Aggregate statistics grouped by business unit.
   - Formatted percentages (`0.0%`) and integer counts (`#,##0`).
4. **Course KPIs**
   - Catalog-level enrollment, completion, and credit hours delivered.
5. **Data Quality Report**
   - Summary of data quality health and error counts.
   - Detailed log of quarantined records with exact issue explanations.
6. **Data Dictionary**
   - Master reference defining all 19 schema columns, data types, nullability, and business rules.

---

## 2. Power Query (M) Script for Raw Data Transformation

If you are an analyst who receives the raw, unvalidated CSV file (`data/raw/raw_training_records.csv`) and wants to perform data cleaning entirely in Microsoft Excel without running Python, use this Power Query M script.

### How to Apply the Power Query Script in Excel

1. Open Microsoft Excel.
2. Go to **Data** > **Get Data** > **From Other Sources** > **Blank Query**.
3. In the Power Query Editor, click **Advanced Editor** on the **Home** tab.
4. Replace the existing template with the M code below (update the file path to match your local repository):

```powerquery
let
    // 1. Source CSV Ingestion
    Source = Csv.Document(
        File.Contents("D:\DATA ANALYTICS\trainops-intelligence\data\raw\raw_training_records.csv"),
        [Delimiter=",", Columns=19, Encoding=65001, QuoteStyle=QuoteStyle.Csv]
    ),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),

    // 2. Remove Blank Critical Identifiers
    #"Filtered Empty Keys" = Table.SelectRows(#"Promoted Headers", each 
        [record_id] <> null and [record_id] <> "" and
        [employee_id] <> null and [employee_id] <> "" and
        [course_id] <> null and [course_id] <> ""
    ),

    // 3. Remove Duplicate Record IDs
    #"Removed Duplicate IDs" = Table.Distinct(#"Filtered Empty Keys", {"record_id"}),

    // 4. Standardize Department Names
    #"Trimmed Department" = Table.TransformColumns(#"Removed Duplicate IDs", {{"department", Text.Trim, type text}}),
    #"Standardized Dept" = Table.AddColumn(#"Trimmed Department", "Department_Clean", each 
        let d = Text.Lower([department]) in
        if Text.Contains(d, "it") or Text.Contains(d, "tech") then "Information Technology"
        else if Text.Contains(d, "hr") or Text.Contains(d, "human") or Text.Contains(d, "people") then "Human Resources"
        else if Text.Contains(d, "eng") or Text.Contains(d, "software") then "Engineering"
        else if Text.Contains(d, "ops") or Text.Contains(d, "operation") then "Operations"
        else if Text.Contains(d, "fin") or Text.Contains(d, "account") then "Finance"
        else if Text.Contains(d, "sales") or Text.Contains(d, "market") then "Sales & Marketing"
        else if Text.Contains(d, "support") or Text.Contains(d, "service") then "Customer Support"
        else if Text.Contains(d, "legal") or Text.Contains(d, "compliance") then "Legal & Compliance"
        else [department], 
        type text
    ),
    #"Removed Old Dept" = Table.RemoveColumns(#"Standardized Dept", {"department"}),
    #"Renamed Dept" = Table.RenameColumns(#"Removed Old Dept", {{"Department_Clean", "department"}}),

    // 5. Standardize Completion Status
    #"Standardized Status" = Table.AddColumn(#"Renamed Dept", "Status_Clean", each
        let s = Text.Lower(Text.Trim([completion_status])) in
        if s = "completed" or s = "done" or s = "finished" or s = "complete" then "Completed"
        else if Text.Contains(s, "progress") or s = "pending" or s = "ongoing" then "In Progress"
        else if Text.Contains(s, "not started") or s = "unstarted" or s = "assigned" then "Not Started"
        else "Quarantine_Invalid",
        type text
    ),
    #"Filter Valid Status" = Table.SelectRows(#"Standardized Status", each [Status_Clean] <> "Quarantine_Invalid"),
    #"Removed Old Status" = Table.RemoveColumns(#"Filter Valid Status", {"completion_status"}),
    #"Renamed Status" = Table.RenameColumns(#"Removed Old Status", {{"Status_Clean", "completion_status"}}),

    // 6. Type Conversions & Safe Date Parsing
    #"Parsed Dates" = Table.TransformColumnTypes(#"Renamed Status", {
        {"assigned_date", type date},
        {"due_date", type date},
        {"completion_date", type date},
        {"training_hours", type number},
        {"mandatory_training", type logical}
    }),

    // 7. Validate Date Logic (assigned <= due)
    #"Filtered Valid Date Order" = Table.SelectRows(#"Parsed Dates", each 
        [assigned_date] <= [due_date] and 
        ([completion_date] = null or [completion_date] >= [assigned_date])
    ),

    // 8. Clean Assessment Scores (Range 0 - 100)
    #"Parsed Score Number" = Table.TransformColumns(#"Filtered Valid Date Order", {
        {"assessment_score", each try Value.FromText(_) otherwise null, type any}
    }),
    #"Cleaned Scores" = Table.AddColumn(#"Parsed Score Number", "Score_Valid", each
        if [assessment_score] = null then null
        else if Value.Is([assessment_score], type number) and [assessment_score] >= 0 and [assessment_score] <= 100 then [assessment_score]
        else null,
        type number
    ),
    #"Removed Old Score" = Table.RemoveColumns(#"Cleaned Scores", {"assessment_score"}),
    #"Renamed Score" = Table.RenameColumns(#"Removed Old Score", {{"Score_Valid", "assessment_score"}}),

    // 9. Reorder Columns to Canonical Order
    #"Reordered Columns" = Table.ReorderColumns(#"Renamed Score", {
        "record_id", "employee_id", "employee_name", "department", "job_level",
        "course_id", "course_name", "training_category", "mandatory_training",
        "assigned_date", "due_date", "completion_date", "attendance_status",
        "completion_status", "assessment_score", "training_hours", "delivery_mode",
        "instructor", "region"
    })
in
    #"Reordered Columns"
```

5. Click **Done**, then click **Close & Load To...** > **Table** in a new worksheet named `Clean_Training_Records`.

---

## 3. Refreshing the Data in Excel

To refresh the cleaned dataset whenever new records are appended to the raw CSV:
1. In Excel, go to the **Data** tab.
2. Click **Refresh All** (or `Ctrl + Alt + F5`).
3. Power Query re-executes all transformation steps in memory and repopulates the clean table in seconds.
