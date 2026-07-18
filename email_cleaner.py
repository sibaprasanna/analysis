"""
email_cleaner.py
----------------

Responsible for:

1. Normalize email
2. Remove spaces
3. Fix @@
4. Remove invalid characters
5. Remove multiple dots
6. Validate email format
7. Extract username
8. Extract domain
"""

import re
import pandas as pd
from config import EMAIL_REGEX

import string
from itertools import product

from domain_validator import validate_domain

EMAIL_PATTERN = re.compile(EMAIL_REGEX)

COMMON_TLDS = [
    "com",
    "org",
    "net",
    "edu",
    "gov",
    "co",
    "in",
    "io",
    "ai",
    "me",
    "info"
]

LETTERS = string.ascii_lowercase

# ==========================================================
# NORMALIZE
# ==========================================================

def normalize(email):

    if pd.isna(email):
        return None

    email = str(email)

    email = email.strip()

    email = email.lower()

    return email


# ==========================================================
# REMOVE SPACES
# ==========================================================

def remove_spaces(email):

    if email is None:
        return None

    return email.replace(" ", "")


# ==========================================================
# FIX @@
# ==========================================================

def fix_multiple_at(email):

    if email is None:
        return None

    while "@@" in email:
        email = email.replace("@@", "@")

    return email


# ==========================================================
# REMOVE INVALID CHARACTERS
# ==========================================================

def remove_invalid_characters(email):

    if email is None:
        return None

    return re.sub(
        r"[^A-Za-z0-9@._%+-]",
        "",
        email
    )


# ==========================================================
# FIX MULTIPLE DOTS
# ==========================================================

def fix_multiple_dots(email):

    if email is None:
        return None

    while ".." in email:
        email = email.replace("..", ".")

    return email


# ==========================================================
# FORMAT VALIDATION
# ==========================================================

def validate_format(email):

    if email is None:
        return False

    return bool(
        EMAIL_PATTERN.match(email)
    )


# ==========================================================
# USERNAME
# ==========================================================

def extract_username(email):

    if email is None:
        return None

    if "@" not in email:
        return None

    return email.split("@")[0]


# ==========================================================
# DOMAIN
# ==========================================================

def extract_domain(email):

    if email is None:
        return None

    if "@" not in email:
        return None

    return email.split("@")[1]

def generate_domain_candidates(domain):
    """
    Generate possible domain corrections.
    No hardcoded providers.
    """

    if not domain:
        return []

    domain = domain.lower()

    candidates = set()

    candidates.add(domain)

    # ------------------------------------
    # Split name + TLD
    # ------------------------------------

    if "." in domain:

        name, tld = domain.rsplit(".", 1)

    else:

        name = domain
        tld = ""

    # ------------------------------------
    # TLD replacement
    # ------------------------------------

    for new_tld in COMMON_TLDS:

        candidates.add(f"{name}.{new_tld}")

    # ------------------------------------
    # Remove duplicate letters
    # ------------------------------------

    for i in range(len(name)-1):

        if name[i] == name[i+1]:

            candidates.add(
                name[:i] +
                name[i+1:] +
                "." +
                tld
            )

    # ------------------------------------
    # Swap adjacent letters
    # ------------------------------------

    for i in range(len(name)-1):

        chars = list(name)

        chars[i], chars[i+1] = chars[i+1], chars[i]

        candidates.add(
            "".join(chars) +
            "." +
            tld
        )

    # ------------------------------------
    # Delete one letter
    # ------------------------------------

    for i in range(len(name)):

        candidates.add(
            name[:i] +
            name[i+1:] +
            "." +
            tld
        )

    # ------------------------------------
    # Insert one letter
    # ------------------------------------

    for i in range(len(name)+1):

        for ch in LETTERS:

            candidates.add(
                name[:i] +
                ch +
                name[i:] +
                "." +
                tld
            )

    # ------------------------------------
    # Replace one letter
    # ------------------------------------

    for i in range(len(name)):

        for ch in LETTERS:

            candidates.add(
                name[:i] +
                ch +
                name[i+1:] +
                "." +
                tld
            )

    return list(candidates)

def repair_domain(email):

    if email is None:

        return email

    if "@" not in email:

        return email

    username, domain = email.rsplit("@", 1)

    validation = validate_domain(domain)

    if validation["Domain Status"] == "Valid":

        return email

    candidates = generate_domain_candidates(domain)

    best_score = -1
    best_domain = domain

    for candidate in candidates:

        result = validate_domain(candidate)

        if result["Domain Status"] != "Valid":

            continue

        score = 0

        if candidate == domain:

            score = 100

        else:

            # similarity without RapidFuzz
            matches = sum(
                a == b
                for a, b in zip(candidate, domain)
            )

            score = matches

        if score > best_score:

            best_score = score
            best_domain = candidate

    return f"{username}@{best_domain}"
# ==========================================================
# COMPLETE CLEANING PIPELINE
# ==========================================================

def clean_email(email):

    original = email

    email = normalize(email)

    if email is None:

        return {
            "Original Email": original,
            "Clean Email": None,
            "Format Status": "Invalid",
            "Validation Reason": "Null Email",
            "Username": None,
            "Mail Domain": None
        }

    # ----------------------------------------
    # Already valid?
    # ----------------------------------------

    if validate_format(email):

        return {

            "Original Email": original,

            "Clean Email": email,

            "Format Status": "Valid",

            "Validation Reason": "Original Format Valid",

            "Username": extract_username(email),

            "Mail Domain": extract_domain(email)
        }

    # ----------------------------------------
    # Cleaning
    # ----------------------------------------

    email = remove_spaces(email)

    email = fix_multiple_at(email)

    email = remove_invalid_characters(email)

    email = fix_multiple_dots(email)

    # ----------------------------------------
    # Validate Again
    # ----------------------------------------

    if validate_format(email):

        return {

            "Original Email": original,

            "Clean Email": email,

            "Format Status": "Corrected",

            "Validation Reason": "Formatting Corrected",

            "Username": extract_username(email),

            "Mail Domain": extract_domain(email)
        }

    return {

        "Original Email": original,

        "Clean Email": email,

        "Format Status": "Invalid",

        "Validation Reason": "Invalid Email Format",

        "Username": None,

        "Mail Domain": None
    }