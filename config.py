"""
Configuration File
------------------
Stores all project settings in one place.
"""

import os

# ==========================================================
# PROJECT PATHS
# ==========================================================

BASE_DIR = r"C:\Users\sibap\Downloads\demo_pbi"

INPUT_FOLDER = os.path.join(BASE_DIR, "input")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")
CACHE_FOLDER = os.path.join(BASE_DIR, "cache")
LOG_FOLDER = os.path.join(BASE_DIR, "logs")

# ==========================================================
# CREATE FOLDERS
# ==========================================================

os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(CACHE_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

# ==========================================================
# OUTPUT FILES
# ==========================================================

OUTPUT_FILE = os.path.join(
    OUTPUT_FOLDER,
    "cleaned_mail_logs.csv"
)

INVALID_FILE = os.path.join(
    OUTPUT_FOLDER,
    "invalid_emails.csv"
)

DOMAIN_REPORT = os.path.join(
    OUTPUT_FOLDER,
    "domain_frequency.csv"
)

CORRECTION_REPORT = os.path.join(
    OUTPUT_FOLDER,
    "domain_corrections.csv"
)

SUMMARY_REPORT = os.path.join(
    OUTPUT_FOLDER,
    "validation_summary.csv"
)

CACHE_FILE = os.path.join(
    CACHE_FOLDER,
    "domain_cache.csv"
)

LOG_FILE = os.path.join(
    LOG_FOLDER,
    "etl.log"
)

# ==========================================================
# THREAD SETTINGS
# ==========================================================

MAX_THREADS = 20

# ==========================================================
# DNS SETTINGS
# ==========================================================

DNS_TIMEOUT = 2

# ==========================================================
# RAPIDFUZZ SETTINGS
# ==========================================================

SIMILARITY_THRESHOLD = 95

# Number of most common domains
TOP_DOMAINS = 100

# ==========================================================
# EMAIL VALIDATION
# ==========================================================

EMAIL_REGEX = (
    r"^[A-Za-z0-9._%+-]+@"
    r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)