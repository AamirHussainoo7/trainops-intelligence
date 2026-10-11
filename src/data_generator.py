"""Synthetic Training Dataset Generator for TrainOps Intelligence.

Generates realistic corporate training records with deterministic random seed,
creating both a clean reference dataset and an intentionally flawed raw dataset
with controlled data-quality anomalies.
"""

from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from src.config import (
    CANONICAL_DEPARTMENTS,
    DATA_PROCESSED_DIR,
    DATA_RAW_DIR,
    DELIVERY_MODES,
    JOB_LEVELS,
    RANDOM_SEED,
    REGIONS,
)

# Realistic course catalog
COURSE_CATALOG = [
    {
        "course_id": "CRS-SEC-101",
        "course_name": "Cybersecurity Fundamentals & Phishing Defense",
        "training_category": "Compliance & Security",
        "mandatory_training": True,
        "training_hours": 2.0,
        "default_mode": "Self-Paced E-Learning",
        "instructor": "LMS Automated Proctor",
    },
    {
        "course_id": "CRS-DTA-101",
        "course_name": "Data Privacy, GDPR & AI Ethics",
        "training_category": "Compliance & Security",
        "mandatory_training": True,
        "training_hours": 1.5,
        "default_mode": "Self-Paced E-Learning",
        "instructor": "LMS Automated Proctor",
    },
    {
        "course_id": "CRS-SAF-101",
        "course_name": "Workplace Health, Safety & Ergonomics",
        "training_category": "Health & Safety",
        "mandatory_training": True,
        "training_hours": 1.0,
        "default_mode": "Virtual Instructor-Led",
        "instructor": "Dr. Sarah Jenkins",
    },
    {
        "course_id": "CRS-FIN-101",
        "course_name": "Anti-Money Laundering & Financial Compliance",
        "training_category": "Finance & Governance",
        "mandatory_training": True,
        "training_hours": 2.5,
        "default_mode": "Virtual Instructor-Led",
        "instructor": "Marcus Sterling",
    },
    {
        "course_id": "CRS-SEC-201",
        "course_name": "Secure Coding & Cloud Security Architecture",
        "training_category": "Compliance & Security",
        "mandatory_training": False,
        "training_hours": 6.0,
        "default_mode": "Hybrid Workshop",
        "instructor": "Alex Chen",
    },
    {
        "course_id": "CRS-AI-101",
        "course_name": "Enterprise Generative AI & Prompt Engineering",
        "training_category": "Technical & Data",
        "mandatory_training": False,
        "training_hours": 3.5,
        "default_mode": "Virtual Instructor-Led",
        "instructor": "Priya Nair",
    },
    {
        "course_id": "CRS-AI-201",
        "course_name": "Analytics Engineering with SQL & dbt",
        "training_category": "Technical & Data",
        "mandatory_training": False,
        "training_hours": 8.0,
        "default_mode": "Hybrid Workshop",
        "instructor": "David Kim",
    },
    {
        "course_id": "CRS-DTA-202",
        "course_name": "Power BI & Business Intelligence Reporting",
        "training_category": "Technical & Data",
        "mandatory_training": False,
        "training_hours": 4.5,
        "default_mode": "Virtual Instructor-Led",
        "instructor": "David Kim",
    },
    {
        "course_id": "CRS-LDR-201",
        "course_name": "Inclusive Leadership & Coaching Excellence",
        "training_category": "Leadership & Soft Skills",
        "mandatory_training": False,
        "training_hours": 4.0,
        "default_mode": "In-Person Classroom",
        "instructor": "Victoria Vance",
    },
    {
        "course_id": "CRS-LDR-301",
        "course_name": "Operational Project Management & Agile Delivery",
        "training_category": "Leadership & Soft Skills",
        "mandatory_training": False,
        "training_hours": 5.0,
        "default_mode": "Virtual Instructor-Led",
        "instructor": "Victoria Vance",
    },
    {
        "course_id": "CRS-ESG-101",
        "course_name": "Corporate Sustainability & ESG Reporting",
        "training_category": "Finance & Governance",
        "mandatory_training": False,
        "training_hours": 2.0,
        "default_mode": "Self-Paced E-Learning",
        "instructor": "LMS Automated Proctor",
    },
    {
        "course_id": "CRS-CUS-101",
        "course_name": "Customer Escalation & Strategic Communications",
        "training_category": "Leadership & Soft Skills",
        "mandatory_training": False,
        "training_hours": 3.0,
        "default_mode": "In-Person Classroom",
        "instructor": "Rachel Torres",
    },
]

# Fictional Employee names generator
FIRST_NAMES = [
    "Aaron", "Abigail", "Adam", "Aisha", "Alexander", "Alicia", "Amara", "Andrew", "Ananya", "Anthony",
    "Benjamin", "Bianca", "Brendan", "Camila", "Carlos", "Chloe", "Christopher", "Daniel", "Daria", "David",
    "Elena", "Elijah", "Emily", "Eric", "Fatima", "Gabriel", "Grace", "Hannah", "Hassan", "Isabella",
    "Jack", "James", "Jasmine", "Jessica", "John", "Jordan", "Julia", "Kai", "Karen", "Kavita",
    "Leo", "Liam", "Lucas", "Maya", "Marcus", "Mei", "Michael", "Nathan", "Nina", "Noah",
    "Olivia", "Omar", "Patrick", "Priya", "Rachel", "Rohan", "Samantha", "Samuel", "Sophia", "Tariq",
    "Victor", "Victoria", "William", "Yuki", "Zoe"
]

LAST_NAMES = [
    "Adams", "Alvarez", "Bakker", "Bennett", "Campbell", "Chen", "Chowdhury", "Davies", "Dubois", "Fischer",
    "Garcia", "Gomez", "Gupta", "Hansen", "Hernandez", "Ivanov", "Jackson", "Jenkins", "Johansson", "Kim",
    "Kumar", "Larsson", "Lee", "Lopez", "Martin", "Miller", "Moreau", "Muller", "Nair", "Nakamura",
    "Novak", "O'Connor", "Patel", "Perez", "Petrov", "Quinn", "Reyes", "Rossi", "Saito", "Santos",
    "Schmidt", "Schneider", "Sharma", "Silva", "Singh", "Smith", "Taylor", "Torres", "Vance", "Wagner",
    "Wang", "Williams", "Wilson", "Wright", "Yamamoto", "Zhang"
]


def _generate_employee_pool(num_employees: int = 260, seed: int = RANDOM_SEED) -> List[Dict]:
    """Generate a realistic employee pool with fixed departments, job levels, and regions."""
    rng = random.Random(seed)
    employees = []
    for i in range(1, num_employees + 1):
        emp_id = f"EMP-{i:04d}"
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        name = f"{first} {last}"
        dept = rng.choice(CANONICAL_DEPARTMENTS)
        level = rng.choices(
            JOB_LEVELS,
            weights=[0.30, 0.35, 0.20, 0.10, 0.05],
            k=1
        )[0]
        region = rng.choices(
            REGIONS,
            weights=[0.40, 0.25, 0.20, 0.15],
            k=1
        )[0]
        employees.append({
            "employee_id": emp_id,
            "employee_name": name,
            "department": dept,
            "job_level": level,
            "region": region,
        })
    return employees


def generate_clean_dataset(
    num_records: int = 1250,
    seed: int = RANDOM_SEED,
    start_date: datetime = datetime(2026, 1, 15),
    end_date: datetime = datetime(2026, 9, 30),
) -> pd.DataFrame:
    """Generate a deterministic, logically consistent clean synthetic training dataset."""
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    employees = _generate_employee_pool(num_employees=280, seed=seed)
    records = []
    record_id_counter = 10001
    date_delta_days = (end_date - start_date).days

    assigned_pairs = set()

    for _ in range(num_records):
        emp = rng.choice(employees)
        course = rng.choice(COURSE_CATALOG)

        # Avoid exact duplicate employee-course-date in clean dataset
        # Random assigned date within window
        days_offset = rng.randint(0, date_delta_days)
        assigned_dt = start_date + timedelta(days=days_offset)
        assigned_str = assigned_dt.strftime("%Y-%m-%d")

        pair_key = (emp["employee_id"], course["course_id"], assigned_str)
        if pair_key in assigned_pairs:
            days_offset = (days_offset + 5) % date_delta_days
            assigned_dt = start_date + timedelta(days=days_offset)
            assigned_str = assigned_dt.strftime("%Y-%m-%d")
        assigned_pairs.add(pair_key)

        # Due date: 30 or 45 days after assigned
        due_window = rng.choice([30, 45])
        due_dt = assigned_dt + timedelta(days=due_window)
        due_str = due_dt.strftime("%Y-%m-%d")

        # Determine outcome probabilistically
        # ~78% completed, ~12% in progress, ~7% not started, ~3% excused/absent
        outcome_roll = rng.random()

        if outcome_roll < 0.78:
            completion_status = "Completed"
            # Completion date is usually before due date (~85%) or slightly after (~15%)
            if rng.random() < 0.85:
                comp_days = rng.randint(2, due_window - 1)
            else:
                comp_days = rng.randint(due_window + 1, due_window + 20)
            comp_dt = assigned_dt + timedelta(days=comp_days)
            completion_str = comp_dt.strftime("%Y-%m-%d")

            # Assessment score: passing is typically >= 70
            # Distribution: mean 84, std 10, clipped 55-100
            raw_score = float(np_rng.normal(84.0, 9.5))
            score = round(max(55.0, min(100.0, raw_score)), 1)

            if course["default_mode"] == "Self-Paced E-Learning":
                attendance_status = rng.choices(
                    ["Not Scheduled / Self-Paced", "Attended"], weights=[0.8, 0.2], k=1
                )[0]
            else:
                attendance_status = "Attended"

        elif outcome_roll < 0.90:
            completion_status = "In Progress"
            completion_str = None
            score = None
            if course["default_mode"] == "Self-Paced E-Learning":
                attendance_status = "Not Scheduled / Self-Paced"
            else:
                attendance_status = rng.choices(["Attended", "Partial"], weights=[0.7, 0.3], k=1)[0]

        elif outcome_roll < 0.97:
            completion_status = "Not Started"
            completion_str = None
            score = None
            if course["default_mode"] == "Self-Paced E-Learning":
                attendance_status = "Not Scheduled / Self-Paced"
            else:
                attendance_status = rng.choices(["Absent", "Not Scheduled / Self-Paced"], weights=[0.6, 0.4], k=1)[0]

        else:
            completion_status = "Not Started"
            completion_str = None
            score = None
            attendance_status = "Excused"

        records.append({
            "record_id": f"TR-{record_id_counter}",
            "employee_id": emp["employee_id"],
            "employee_name": emp["employee_name"],
            "department": emp["department"],
            "job_level": emp["job_level"],
            "course_id": course["course_id"],
            "course_name": course["course_name"],
            "training_category": course["training_category"],
            "mandatory_training": course["mandatory_training"],
            "assigned_date": assigned_str,
            "due_date": due_str,
            "completion_date": completion_str,
            "attendance_status": attendance_status,
            "completion_status": completion_status,
            "assessment_score": score,
            "training_hours": course["training_hours"],
            "delivery_mode": course["default_mode"],
            "instructor": course["instructor"],
            "region": emp["region"],
        })
        record_id_counter += 1

    df = pd.DataFrame(records)
    return df


def generate_flawed_raw_dataset(clean_df: pd.DataFrame, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Generate an intentionally imperfect raw dataset with controlled, known data quality issues."""
    rng = random.Random(seed)
    raw_df = clean_df.copy()
    raw_df["assessment_score"] = raw_df["assessment_score"].astype(object)
    raw_df["due_date"] = raw_df["due_date"].astype(object)
    raw_df["completion_date"] = raw_df["completion_date"].astype(object)
    raw_df["department"] = raw_df["department"].astype(object)
    raw_df["completion_status"] = raw_df["completion_status"].astype(object)
    raw_df["attendance_status"] = raw_df["attendance_status"].astype(object)

    total_len = len(raw_df)

    # 1. Inject duplicate records (~35 records)
    dup_indices = rng.sample(range(total_len), 35)
    duplicates = raw_df.iloc[dup_indices].copy()
    # Half keep identical record_id, half keep same employee+course+date with new record_id
    for idx, (real_idx, row) in enumerate(duplicates.iterrows()):
        if idx % 2 == 1:
            row["record_id"] = f"TR-DUP-{90000 + idx}"
    raw_df = pd.concat([raw_df, duplicates], ignore_index=True)

    # 2. Inject Inconsistent Department Names (~60 records)
    dept_synonym_list = [
        "IT", "it", "information tech", "HR", "human-resources", "People",
        "Ops", "operations & logistics", "Eng.", "Software", "Fin",
        "Finance & Ops", "Sales", "Support", "Legal"
    ]
    dept_indices = rng.sample(range(total_len), 60)
    for idx in dept_indices:
        raw_df.at[idx, "department"] = rng.choice(dept_synonym_list)

    # 3. Inject Missing Employee / Course fields (~40 records)
    missing_emp_name_idx = rng.sample(range(total_len), 15)
    for idx in missing_emp_name_idx:
        raw_df.at[idx, "employee_name"] = None

    missing_emp_id_idx = rng.sample(range(total_len), 12)
    for idx in missing_emp_id_idx:
        raw_df.at[idx, "employee_id"] = None

    missing_course_name_idx = rng.sample(range(total_len), 13)
    for idx in missing_course_name_idx:
        raw_df.at[idx, "course_name"] = None

    # 4. Inject Invalid Assessment Scores (~30 records)
    # > 100, < 0, or string
    score_indices = rng.sample(range(total_len), 30)
    for i, idx in enumerate(score_indices):
        if i % 3 == 0:
            raw_df.at[idx, "assessment_score"] = rng.choice([105.0, 150.0, 950.0])
        elif i % 3 == 1:
            raw_df.at[idx, "assessment_score"] = rng.choice([-10.0, -25.0])
        else:
            raw_df.at[idx, "assessment_score"] = "Pass"

    # 5. Inject Invalid Dates / Date Order Violations (~35 records)
    date_violation_indices = rng.sample(range(total_len), 35)
    for i, idx in enumerate(date_violation_indices):
        if i % 3 == 0:
            # Completion date BEFORE assigned date
            assigned = raw_df.at[idx, "assigned_date"]
            if assigned and isinstance(assigned, str):
                try:
                    ass_dt = datetime.strptime(assigned, "%Y-%m-%d")
                    raw_df.at[idx, "completion_date"] = (ass_dt - timedelta(days=15)).strftime("%Y-%m-%d")
                    raw_df.at[idx, "completion_status"] = "Completed"
                except Exception:
                    pass
        elif i % 3 == 1:
            # Malformed date strings
            raw_df.at[idx, "due_date"] = "2026/13/45"
        else:
            # Unparseable date
            raw_df.at[idx, "completion_date"] = "N/A"

    # 6. Inject Inconsistent Status Values (~50 records)
    status_variations = ["Done", "finished", "PENDING", "completed ", "unstarted", "Unknown"]
    status_indices = rng.sample(range(total_len), 50)
    for idx in status_indices:
        raw_df.at[idx, "completion_status"] = rng.choice(status_variations)

    # 7. Inject Missing Attendance (~40 records)
    attend_indices = rng.sample(range(total_len), 40)
    for idx in attend_indices:
        raw_df.at[idx, "attendance_status"] = None

    return raw_df


def save_datasets(
    clean_path: str = None,
    raw_path: str = None,
    seed: int = RANDOM_SEED,
    num_records: int = 1250
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generate both datasets and persist them to their respective directories."""
    clean_df = generate_clean_dataset(num_records=num_records, seed=seed)
    raw_df = generate_flawed_raw_dataset(clean_df=clean_df, seed=seed)

    clean_file = clean_path or (DATA_PROCESSED_DIR / "clean_training_records_reference.csv")
    raw_file = raw_path or (DATA_RAW_DIR / "raw_training_records.csv")

    clean_df.to_csv(clean_file, index=False)
    raw_df.to_csv(raw_file, index=False)

    return clean_df, raw_df


if __name__ == "__main__":
    clean, raw = save_datasets()
    print(f"Generated clean dataset: {len(clean)} records")
    print(f"Generated raw dataset: {len(raw)} records")
