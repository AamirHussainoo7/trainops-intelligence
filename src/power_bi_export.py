"""Power BI Export Engine for TrainOps Intelligence.

Exports clean, relational CSV datasets with stable schema and non-decorated numeric
values specifically designed for direct import and modeling in Microsoft Power BI Desktop.
"""

from pathlib import Path
from typing import Any, Dict
import pandas as pd
from src.config import DATA_EXPORT_DIR


def export_power_bi_datasets(
    clean_df: pd.DataFrame,
    dept_df: pd.DataFrame,
    course_df: pd.DataFrame,
    monthly_trends_df: pd.DataFrame,
    dq_summary: Dict[str, Any],
    export_dir: Path = DATA_EXPORT_DIR
) -> Dict[str, Path]:
    """Export clean, stable CSV files configured for seamless Power BI Desktop modeling.
    
    Returns:
        Dictionary mapping dataset names to absolute file paths.
    """
    export_dir.mkdir(parents=True, exist_ok=True)
    exported_files = {}

    # 1. Fact Table: clean training records
    # Ensure consistent data types and formats
    clean_pbi = clean_df.copy()
    if not clean_pbi.empty:
        # Guarantee boolean is TRUE/FALSE string or bool
        if "mandatory_training" in clean_pbi.columns:
            clean_pbi["mandatory_training"] = clean_pbi["mandatory_training"].astype(bool)

    clean_records_path = export_dir / "training_records_clean.csv"
    clean_pbi.to_csv(clean_records_path, index=False, date_format="%Y-%m-%d")
    exported_files["training_records_clean"] = clean_records_path

    # 2. Dimension / Aggregate Table: Department KPIs
    dept_pbi = dept_df.copy()
    dept_path = export_dir / "department_kpis.csv"
    dept_pbi.to_csv(dept_path, index=False)
    exported_files["department_kpis"] = dept_path

    # 3. Dimension / Aggregate Table: Course KPIs
    course_pbi = course_df.copy()
    course_path = export_dir / "course_kpis.csv"
    course_pbi.to_csv(course_path, index=False)
    exported_files["course_kpis"] = course_path

    # 4. Time Series Trend: Monthly training trends
    monthly_path = export_dir / "monthly_training_trends.csv"
    monthly_trends_df.to_csv(monthly_path, index=False)
    exported_files["monthly_training_trends"] = monthly_path

    # 5. Data Quality Summary
    dq_records = [
        {"metric_name": k, "metric_value": v}
        for k, v in dq_summary.items()
        if k != "issues_by_category"
    ]
    if "issues_by_category" in dq_summary and isinstance(dq_summary["issues_by_category"], dict):
        for cat, cnt in dq_summary["issues_by_category"].items():
            dq_records.append({"metric_name": f"issue_cat_{cat}", "metric_value": cnt})

    dq_df = pd.DataFrame(dq_records)
    dq_path = export_dir / "data_quality_summary.csv"
    dq_df.to_csv(dq_path, index=False)
    exported_files["data_quality_summary"] = dq_path

    return exported_files
