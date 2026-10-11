"""Configuration module for TrainOps Intelligence."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Database & Storage paths
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "data" / "trainops.db")))
if not DB_PATH.is_absolute():
    DB_PATH = BASE_DIR / DB_PATH

DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATA_EXPORT_DIR = BASE_DIR / "data" / "exports"
OUTPUT_DIR = BASE_DIR / "output"

# Ensure directories exist
for directory in [DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_EXPORT_DIR, OUTPUT_DIR, DB_PATH.parent]:
    directory.mkdir(parents=True, exist_ok=True)

# LLM Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Application Settings
DEFAULT_AS_OF_DATE = os.getenv("DEFAULT_AS_OF_DATE", "2026-10-15")
RANDOM_SEED = 42

# Canonical values for standardizations and validations
CANONICAL_DEPARTMENTS = [
    "Information Technology",
    "Engineering",
    "Operations",
    "Human Resources",
    "Finance",
    "Sales & Marketing",
    "Customer Support",
    "Legal & Compliance"
]

DEPARTMENT_SYNONYMS = {
    "it": "Information Technology",
    "information tech": "Information Technology",
    "info tech": "Information Technology",
    "eng": "Engineering",
    "eng.": "Engineering",
    "software": "Engineering",
    "ops": "Operations",
    "operations & logistics": "Operations",
    "hr": "Human Resources",
    "human-resources": "Human Resources",
    "people": "Human Resources",
    "finance": "Finance",
    "fin": "Finance",
    "finance & accounting": "Finance",
    "finance & ops": "Finance",
    "sales": "Sales & Marketing",
    "marketing": "Sales & Marketing",
    "sales and marketing": "Sales & Marketing",
    "support": "Customer Support",
    "cust support": "Customer Support",
    "customer service": "Customer Support",
    "legal": "Legal & Compliance",
    "compliance": "Legal & Compliance",
    "legal & risk": "Legal & Compliance"
}

COMPLETION_STATUS_SYNONYMS = {
    "completed": "Completed",
    "done": "Completed",
    "finished": "Completed",
    "complete": "Completed",
    "in progress": "In Progress",
    "in-progress": "In Progress",
    "pending": "In Progress",
    "ongoing": "In Progress",
    "not started": "Not Started",
    "not-started": "Not Started",
    "assigned": "Not Started",
    "unstarted": "Not Started",
    "overdue": "Overdue"
}

ATTENDANCE_STATUSES = [
    "Attended",
    "Partial",
    "Absent",
    "Not Scheduled / Self-Paced",
    "Excused"
]

DELIVERY_MODES = [
    "Virtual Instructor-Led",
    "Self-Paced E-Learning",
    "In-Person Classroom",
    "Hybrid Workshop"
]

REGIONS = [
    "North America",
    "EMEA",
    "APAC",
    "LATAM"
]

JOB_LEVELS = [
    "Entry-Level",
    "Mid-Level",
    "Senior",
    "Lead / Manager",
    "Director / VP"
]
