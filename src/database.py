"""SQLite Database Access Layer for TrainOps Intelligence.

Manages relational persistence of raw and clean training records, flagged records,
validation run histories, and generated report audit logs.
"""

from datetime import datetime
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import pandas as pd
from src.config import DB_PATH


def get_db_connection() -> sqlite3.Connection:
    """Return an active connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn



def init_db() -> None:
    """Initialize SQLite tables and create required indexes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Raw training records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_training_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT,
            employee_id TEXT,
            employee_name TEXT,
            department TEXT,
            job_level TEXT,
            course_id TEXT,
            course_name TEXT,
            training_category TEXT,
            mandatory_training TEXT,
            assigned_date TEXT,
            due_date TEXT,
            completion_date TEXT,
            attendance_status TEXT,
            completion_status TEXT,
            assessment_score TEXT,
            training_hours REAL,
            delivery_mode TEXT,
            instructor TEXT,
            region TEXT,
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Clean validated training records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clean_training_records (
            record_id TEXT PRIMARY KEY,
            employee_id TEXT NOT NULL,
            employee_name TEXT NOT NULL,
            department TEXT NOT NULL,
            job_level TEXT,
            course_id TEXT NOT NULL,
            course_name TEXT NOT NULL,
            training_category TEXT NOT NULL,
            mandatory_training INTEGER NOT NULL,
            assigned_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            completion_date TEXT,
            attendance_status TEXT,
            completion_status TEXT NOT NULL,
            assessment_score REAL,
            training_hours REAL NOT NULL,
            delivery_mode TEXT,
            instructor TEXT,
            region TEXT,
            is_overdue INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Flagged records requiring review
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS flagged_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT,
            employee_id TEXT,
            course_id TEXT,
            issue_type TEXT NOT NULL,
            issue_severity TEXT NOT NULL,
            issue_description TEXT NOT NULL,
            raw_data_json TEXT NOT NULL,
            flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Validation runs audit table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS validation_runs (
            run_id TEXT PRIMARY KEY,
            run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_records_processed INTEGER NOT NULL,
            valid_records_count INTEGER NOT NULL,
            flagged_records_count INTEGER NOT NULL,
            duplicate_records_count INTEGER NOT NULL,
            missing_fields_count INTEGER NOT NULL,
            date_errors_count INTEGER NOT NULL,
            score_errors_count INTEGER NOT NULL,
            summary_json TEXT
        )
    """)

    # Generated reports audit table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS report_history (
            report_id TEXT PRIMARY KEY,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reporting_period_start TEXT,
            reporting_period_end TEXT,
            as_of_date TEXT,
            excel_filename TEXT,
            markdown_filename TEXT,
            ai_assisted INTEGER DEFAULT 0,
            kpis_json TEXT,
            status TEXT DEFAULT 'COMPLETED'
        )
    """)

    # Create indexes for high-performance querying
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clean_dept ON clean_training_records (department)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clean_course ON clean_training_records (course_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clean_status ON clean_training_records (completion_status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clean_assigned ON clean_training_records (assigned_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clean_due ON clean_training_records (due_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clean_mandatory ON clean_training_records (mandatory_training)")

    conn.commit()
    conn.close()


def save_clean_records(df: pd.DataFrame) -> None:
    """Save cleaned and validated training records to SQLite, replacing existing table content."""
    conn = get_db_connection()
    # Ensure boolean is integer
    df_to_save = df.copy()
    if "mandatory_training" in df_to_save.columns:
        df_to_save["mandatory_training"] = df_to_save["mandatory_training"].astype(int)
    if "is_overdue" in df_to_save.columns:
        df_to_save["is_overdue"] = df_to_save["is_overdue"].astype(int)

    df_to_save.to_sql("clean_training_records", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()


def save_raw_records(df: pd.DataFrame) -> None:
    """Save raw ingested training records to SQLite."""
    conn = get_db_connection()
    df.to_sql("raw_training_records", conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()


def save_flagged_records(flagged_list: List[Dict[str, Any]]) -> None:
    """Save flagged records with validation issue explanations."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM flagged_records")

    for item in flagged_list:
        cursor.execute("""
            INSERT INTO flagged_records (
                record_id, employee_id, course_id, issue_type,
                issue_severity, issue_description, raw_data_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(item.get("record_id", "")),
            str(item.get("employee_id", "")),
            str(item.get("course_id", "")),
            str(item.get("issue_type", "DATA_QUALITY_ISSUE")),
            str(item.get("issue_severity", "CRITICAL")),
            str(item.get("issue_description", "")),
            json.dumps(item.get("raw_record", {}), default=str)
        ))
    conn.commit()
    conn.close()


def log_validation_run(summary: Dict[str, Any]) -> None:
    """Log validation run metadata for auditability."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO validation_runs (
            run_id, total_records_processed, valid_records_count,
            flagged_records_count, duplicate_records_count, missing_fields_count,
            date_errors_count, score_errors_count, summary_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        summary.get("run_id", f"RUN-{int(datetime.now().timestamp())}"),
        int(summary.get("total_records", 0)),
        int(summary.get("valid_records", 0)),
        int(summary.get("flagged_records", 0)),
        int(summary.get("duplicates", 0)),
        int(summary.get("missing_fields", 0)),
        int(summary.get("date_errors", 0)),
        int(summary.get("score_errors", 0)),
        json.dumps(summary, default=str)
    ))
    conn.commit()
    conn.close()


def log_report_generation(report_meta: Dict[str, Any]) -> None:
    """Log report generation run into report history."""
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO report_history (
            report_id, reporting_period_start, reporting_period_end,
            as_of_date, excel_filename, markdown_filename, ai_assisted,
            kpis_json, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_meta.get("report_id"),
        report_meta.get("reporting_period_start"),
        report_meta.get("reporting_period_end"),
        report_meta.get("as_of_date"),
        report_meta.get("excel_filename"),
        report_meta.get("markdown_filename"),
        1 if report_meta.get("ai_assisted") else 0,
        json.dumps(report_meta.get("kpis", {}), default=str),
        report_meta.get("status", "COMPLETED")
    ))
    conn.commit()
    conn.close()


def get_clean_records_df() -> pd.DataFrame:
    """Fetch all cleaned training records from SQLite."""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT * FROM clean_training_records", conn)
        if "mandatory_training" in df.columns:
            df["mandatory_training"] = df["mandatory_training"].astype(bool)
        if "is_overdue" in df.columns:
            df["is_overdue"] = df["is_overdue"].astype(bool)
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def get_raw_records_df() -> pd.DataFrame:
    """Fetch raw records from SQLite."""
    conn = get_db_connection()
    try:
        return pd.read_sql_query("SELECT * FROM raw_training_records", conn)
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def get_flagged_records_df() -> pd.DataFrame:
    """Fetch flagged records from SQLite."""
    conn = get_db_connection()
    try:
        return pd.read_sql_query("SELECT * FROM flagged_records ORDER BY id DESC", conn)
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def get_validation_runs_df() -> pd.DataFrame:
    """Fetch historical validation runs."""
    conn = get_db_connection()
    try:
        return pd.read_sql_query("SELECT * FROM validation_runs ORDER BY run_timestamp DESC", conn)
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def get_report_history_df() -> pd.DataFrame:
    """Fetch history of generated reports."""
    conn = get_db_connection()
    try:
        return pd.read_sql_query("SELECT * FROM report_history ORDER BY generated_at DESC", conn)
    except Exception:
        return pd.DataFrame()
    finally:
        conn.close()


def reset_and_seed_db(clean_df: pd.DataFrame, raw_df: pd.DataFrame) -> None:
    """Reset the database and reseed with clean and raw datasets."""
    init_db()
    save_raw_records(raw_df)
    save_clean_records(clean_df)
