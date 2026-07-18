"""
domain_corrector.py
-------------------

Responsibilities

1. Build trusted domain dictionary
2. Correct invalid domains
3. Run correction using threads
4. Rebuild corrected emails
"""

import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from rapidfuzz import process

from config import TOP_DOMAINS, SIMILARITY_THRESHOLD
from domain_validator import validate_domain

MAX_THREADS = 20


# ==========================================================
# BUILD TRUSTED DOMAIN LIST
# ==========================================================

def build_domain_dictionary(df):

    domains = (
        df["Mail Domain"]
        .dropna()
        .astype(str)
        .str.lower()
        .str.strip()
    )

    frequency = (
        domains
        .value_counts()
        .reset_index()
    )

    frequency.columns = [
        "Domain",
        "Count"
    ]

    trusted_domains = []

    for domain in frequency["Domain"]:

        result = validate_domain(domain)

        if result["Domain Status"] == "Valid":

            trusted_domains.append(domain)

        if len(trusted_domains) >= TOP_DOMAINS:

            break

    return trusted_domains, frequency


# ==========================================================
# FIND BEST MATCH
# ==========================================================

def find_best_domain(domain, trusted_domains):

    if not trusted_domains:
        return None, 0

    match = process.extractOne(
        domain,
        trusted_domains
    )

    if match is None:
        return None, 0

    return match[0], match[1]


# ==========================================================
# CORRECT DOMAIN
# ==========================================================

def correct_domain(domain, trusted_domains):

    if pd.isna(domain):
        return {
            "Corrected Domain": None,
            "Similarity Score": 0,
            "Correction Status": "No Domain"
        }

    domain = str(domain).strip().lower()

    validation = validate_domain(domain)

    if validation["Domain Status"] == "Valid":
        return {
            "Corrected Domain": domain,
            "Similarity Score": 100,
            "Correction Status": "Already Valid"
        }

    suggested, score = find_best_domain(
        domain,
        trusted_domains
    )

    if suggested is None:
        return {
            "Corrected Domain": domain,
            "Similarity Score": 0,
            "Correction Status": "No Match"
        }

    if score < SIMILARITY_THRESHOLD:
        return {
            "Corrected Domain": domain,
            "Similarity Score": score,
            "Correction Status": "Low Confidence"
        }

    validation = validate_domain(suggested)

    if validation["Domain Status"] != "Valid":
        return {
            "Corrected Domain": domain,
            "Similarity Score": score,
            "Correction Status": "Suggested Domain Invalid"
        }

    return {
        "Corrected Domain": suggested,
        "Similarity Score": score,
        "Correction Status": "Corrected"
    }

# ==========================================================
# REBUILD EMAIL
# ==========================================================

def rebuild_email(email, corrected_domain):

    if pd.isna(email):
        return None

    email = str(email)

    if "@" not in email:
        return email

    username = email.split("@")[0]

    return f"{username}@{corrected_domain}"


# ==========================================================
# COMPLETE EMAIL CORRECTION
# ==========================================================

def correct_email(email, trusted_domains):

    if pd.isna(email):

        return {

            "Corrected Email": None,
            "Corrected Domain": None,
            "Similarity Score": 0,
            "Correction Status": "Empty Email"

        }

    email = str(email).strip()

    if "@" not in email:

        return {

            "Corrected Email": email,
            "Corrected Domain": None,
            "Similarity Score": 0,
            "Correction Status": "Invalid Format"

        }

    username, domain = email.split("@", 1)

    result = correct_domain(
        domain,
        trusted_domains
    )

    corrected_email = rebuild_email(
        email,
        result["Corrected Domain"]
    )

    return {

        "Corrected Email": corrected_email,

        "Corrected Domain": result["Corrected Domain"],

        "Similarity Score": result["Similarity Score"],

        "Correction Status": result["Correction Status"]

    }


# ==========================================================
# THREAD WORKER
# ==========================================================

def process_email(args):

    email, trusted_domains = args

    try:

        return correct_email(
            email,
            trusted_domains
        )

    except Exception:

        return {

            "Corrected Email": email,

            "Corrected Domain": None,

            "Similarity Score": 0,

            "Correction Status": "Error"

        }


# ==========================================================
# MULTITHREADED DATAFRAME CORRECTION
# ==========================================================

def process_domain(args):

    domain, trusted_domains = args

    result = correct_domain(domain, trusted_domains)

    return (
        domain,
        result["Corrected Domain"],
        result["Similarity Score"],
        result["Correction Status"]
    )

def correct_dataframe(df, trusted_domains):

    if "Mail Domain" not in df.columns:

        return df

    # -------------------------------
    # Unique domains only
    # -------------------------------

    unique_domains = (
        df["Mail Domain"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
        .unique()
        .tolist()
    )

    # -------------------------------
    # Repair unique domains
    # -------------------------------

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:

        results = list(

            executor.map(

                process_domain,

                [

                    (domain, trusted_domains)

                    for domain in unique_domains

                ]

            )

        )

    # -------------------------------
    # Build mapping
    # -------------------------------

    corrected_domain = {}
    similarity = {}
    status = {}

    for old, new, score, stat in results:

        corrected_domain[old] = new
        similarity[old] = score
        status[old] = stat

    # -------------------------------
    # Update dataframe
    # -------------------------------

    domain_key = (
        df["Mail Domain"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    df["Corrected Domain"] = (
        domain_key
        .map(corrected_domain)
    )

    df["Similarity Score"] = (
        domain_key
        .map(similarity)
    )

    df["Correction Status"] = (
        domain_key
        .map(status)
    )

    # -------------------------------
    # Rebuild email
    # -------------------------------

    df["Corrected Email"] = (
        df["Username"]
        + "@"
        + df["Corrected Domain"]
    )

    return df