"""Seed Database and Generate Export Packages for TrainOps Intelligence."""

from src.config import DEFAULT_AS_OF_DATE
from src.data_generator import save_datasets
from src.database import init_db, log_validation_run, reset_and_seed_db, save_flagged_records
from src.validation import validate_training_dataset
from src.analytics import compute_kpis, get_department_kpis, get_course_kpis, get_monthly_completion_trends
from src.excel_export import generate_excel_workbook
from src.power_bi_export import export_power_bi_datasets

if __name__ == "__main__":
    print("1. Generating synthetic clean and raw datasets...")
    clean_df, raw_df = save_datasets(num_records=1250, seed=42)

    print("2. Running validation pipeline on raw dataset...")
    valid_df, flagged_df, summary = validate_training_dataset(raw_df)
    print(f"   - Ingested: {summary['total_records']}")
    print(f"   - Clean validated: {summary['valid_records']}")
    print(f"   - Flagged quarantined: {summary['flagged_records']}")
    print(f"   - Duplicates: {summary['duplicates']}")
    print(f"   - Date anomalies: {summary['date_errors']}")
    print(f"   - Score anomalies: {summary['score_errors']}")

    print("3. Persisting to SQLite database (data/trainops.db)...")
    init_db()
    reset_and_seed_db(valid_df, raw_df)
    save_flagged_records(flagged_df.to_dict(orient="records"))
    log_validation_run(summary)

    print("4. Computing deterministic KPIs...")
    kpis = compute_kpis(valid_df, as_of_date=DEFAULT_AS_OF_DATE)
    dept_df = get_department_kpis(valid_df, as_of_date=DEFAULT_AS_OF_DATE)
    course_df = get_course_kpis(valid_df, as_of_date=DEFAULT_AS_OF_DATE)
    trends_df = get_monthly_completion_trends(valid_df)

    print(f"   - Overall Completion Rate: {kpis['completion_rate_formatted']}")
    print(f"   - Mandatory Compliance: {kpis['mandatory_completion_rate_formatted']}")
    print(f"   - Overdue Assignments: {kpis['overdue_assignments']}")
    print(f"   - Avg Assessment Score: {kpis['avg_assessment_score_formatted']}")

    print("5. Generating master Power BI export package in data/exports/...")
    exported_pbi = export_power_bi_datasets(valid_df, dept_df, course_df, trends_df, summary)
    for k, v in exported_pbi.items():
        print(f"   - {k}.csv created at {v}")

    print("6. Generating initial Excel executive workbook...")
    excel_path = generate_excel_workbook(
        clean_df=valid_df,
        kpis=kpis,
        dept_df=dept_df,
        course_df=course_df,
        dq_summary=summary,
        flagged_df=flagged_df,
        output_filename="TrainOps_Master_Report.xlsx"
    )
    print(f"   - Master Excel report created at {excel_path}")
    print("\nDatabase initialization and artifact generation complete!")
