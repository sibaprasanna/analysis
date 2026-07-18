"""
domain_validator.py
-------------------

Responsibilities

1. Validate a single domain
2. Validate multiple domains
3. ThreadPool support
4. DNS lookup
5. MX lookup
6. Return detailed validation status
"""

import socket
import dns.resolver

from concurrent.futures import ThreadPoolExecutor

from config import *


# ==========================================================
# SOCKET VALIDATION
# ==========================================================

def socket_validation(domain):
    """
    Checks whether the domain resolves to an IP.
    """

    try:

        socket.gethostbyname(domain)

        return True

    except socket.gaierror:

        return False

    except Exception:

        return False


# ==========================================================
# MX VALIDATION
# ==========================================================

def mx_validation(domain):
    """
    Checks whether the domain has MX records.
    """

    try:

        dns.resolver.resolve(
            domain,
            "MX",
            lifetime=DNS_TIMEOUT
        )

        return True

    except dns.resolver.NoAnswer:

        return False

    except dns.resolver.NXDOMAIN:

        return False

    except dns.resolver.Timeout:

        return False

    except Exception:

        return False


# ==========================================================
# A RECORD VALIDATION
# ==========================================================

def a_record_validation(domain):
    """
    Fallback if MX record is unavailable.
    """

    try:

        dns.resolver.resolve(
            domain,
            "A",
            lifetime=DNS_TIMEOUT
        )

        return True

    except Exception:

        return False


# ==========================================================
# SINGLE DOMAIN VALIDATION
# ==========================================================

def validate_domain(domain):

    if domain is None:

        return {

            "Domain": None,

            "Domain Status": "Invalid",

            "Validation Reason": "Empty Domain"

        }

    domain = domain.lower().strip()

    # ---------------------------------------
    # Step 1
    # Socket
    # ---------------------------------------

    if not socket_validation(domain):

        return {

            "Domain": domain,

            "Domain Status": "Invalid",

            "Validation Reason": "Socket Lookup Failed"

        }

    # ---------------------------------------
    # Step 2
    # MX Record
    # ---------------------------------------

    if mx_validation(domain):

        return {

            "Domain": domain,

            "Domain Status": "Valid",

            "Validation Reason": "MX Record Found"

        }

    # ---------------------------------------
    # Step 3
    # A Record
    # ---------------------------------------

    if a_record_validation(domain):

        return {

            "Domain": domain,

            "Domain Status": "Valid",

            "Validation Reason": "A Record Found"

        }

    # ---------------------------------------
    # Invalid
    # ---------------------------------------

    return {

        "Domain": domain,

        "Domain Status": "Invalid",

        "Validation Reason": "No MX/A Record"

    }


# ==========================================================
# MULTIPLE DOMAIN VALIDATION
# ==========================================================

def validate_domains(domain_list):

    results = {}

    unique_domains = list(set(domain_list))

    with ThreadPoolExecutor(
        max_workers=MAX_THREADS
    ) as executor:

        validation = executor.map(
            validate_domain,
            unique_domains
        )

        for item in validation:

            results[item["Domain"]] = item

    return results