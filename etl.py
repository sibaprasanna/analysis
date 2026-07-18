"""
etl.py
-------

Main ETL Pipeline
"""

import os
import glob
import time

import pandas as pd

from config import *

from schema_mapper import map_columns

from logger import ETLLogger

from cache_manager import DomainCache

from email_cleaner import clean_email

from domain_validator import validate_domains


from domain_corrector import (
    build_domain_dictionary,
    correct_dataframe
)

from reports import ReportGenerator


# ==========================================================
# INITIALIZE
# ==========================================================

logger = ETLLogger()

cache = DomainCache()


# ==========================================================
# READ CSV FILES
# ==========================================================

def read_csv_files():

    csv_files = glob.glob(
        os.path.join(INPUT_FOLDER, "*.csv")
    )

    if len(csv_files) == 0:

        raise FileNotFoundError(
            "No CSV files found."
        )

    dataframes = []

    logger.info(
        f"Found {len(csv_files)} CSV files."
    )

    for file in csv_files:

        try:

            df = pd.read_csv(
                file,
                low_memory=False
            )

            logger.info(
                f"{os.path.basename(file)} Original Columns : {list(df.columns)}"
            )
            df = map_columns(df)
            logger.info(
                f"{os.path.basename(file)} Standardized Columns : {list(df.columns)}"
)

            df["Source File"] = os.path.basename(file)

            dataframes.append(df)

            logger.file_processed(
                os.path.basename(file),
                len(df)
            )

        except Exception as e:

            logger.exception(
                f"Failed reading {file}: {e}"
            )

    if len(dataframes) == 0:

        raise Exception(
            "No valid CSVs loaded."
        )

    return pd.concat(
        dataframes,
        ignore_index=True
    )


# ==========================================================
# REMOVE DUPLICATES
# ==========================================================

def remove_duplicates(df):

    before = len(df)

    df = df.drop_duplicates()

    after = len(df)

    logger.info(

        f"Duplicates Removed : {before-after}"

    )

    return df


# ==========================================================
# CLEAN EMAILS
# ==========================================================

def clean_email_column(df):

    if "recipient_email" not in df.columns:

        logger.warning(
            "Email column not found. Skipping email cleaning."
        )

        return df

    cleaned = df["recipient_email"].fillna("").apply(clean_email)

    cleaned = pd.DataFrame(cleaned.tolist())

    df = pd.concat(
        [df, cleaned],
        axis=1
    )

    return df


# ==========================================================
# BUILD DOMAIN DICTIONARY
# ==========================================================

def prepare_domains(df):

    logger.info(
        "Building Trusted Domains..."
    )

    trusted_domains, report = \
        build_domain_dictionary(df)

    logger.info(

        f"Trusted Domains : "

        f"{len(trusted_domains)}"

    )

    return df, trusted_domains, report


# ==========================================================
# LOAD CACHE
# ==========================================================

def load_cache():

    logger.cache_loaded(

        cache.size()

    )
# ==========================================================
# VALIDATE DOMAINS
# ==========================================================

def validate_all_domains(df):

    logger.info("Validating Domains...")

    # ---------------------------------------
    # Skip if Mail Domain column doesn't exist
    # ---------------------------------------
    if "Mail Domain" not in df.columns:

        logger.warning(
            "Mail Domain column not found. Skipping domain validation."
        )

        return df

    # Skip if Mail Domain is empty
    if df["Mail Domain"].dropna().empty:

        logger.warning(
            "No domains found for validation."
        )

        df["Domain Status"] = None
        df["Domain Validation Reason"] = None

        return df

    # ---------------------------------------
    # Get unique domains
    # ---------------------------------------
    unique_domains = (
        df["Mail Domain"]
        .dropna()
        .astype(str)
        .str.lower()
        .unique()
        .tolist()
    )

    cached_domains = {}
    uncached_domains = []

    # ---------------------------------------
    # Check Cache
    # ---------------------------------------
    for domain in unique_domains:

        if cache.exists(domain):

            cached_domains[domain] = cache.get(domain)

        else:

            uncached_domains.append(domain)

    logger.info(
        f"Cached Domains : {len(cached_domains)}"
    )

    logger.info(
        f"Domains To Validate : {len(uncached_domains)}"
    )

    # ---------------------------------------
    # Validate New Domains
    # ---------------------------------------
    new_results = {}

    if len(uncached_domains) > 0:

        new_results = validate_domains(
            uncached_domains
        )

        cache.update(new_results)

        cache.save()

        logger.cache_saved(
            cache.size()
        )

    # ---------------------------------------
    # Merge Results
    # ---------------------------------------
    validation_results = {

        **cached_domains,
        **new_results

    }

    # ---------------------------------------
    # Map Back to DataFrame
    # ---------------------------------------
    df["Domain Status"] = df["Mail Domain"].map(

        lambda x: validation_results
        .get(str(x).lower(), {})
        .get("Domain Status", "Unknown")

        if pd.notna(x) else None
    )

    df["Domain Validation Reason"] = df["Mail Domain"].map(

        lambda x: validation_results
        .get(str(x).lower(), {})
        .get("Validation Reason", "Unknown")

        if pd.notna(x) else None
    )

    return df


# ==========================================================
# DOMAIN CORRECTION
# ==========================================================

# ==========================================================
# SPLIT DSN
# ==========================================================

# ==========================================================
# SPLIT DSN STATUS
# ==========================================================

def split_dsn(df):

    # Skip if DSN column doesn't exist
    if "dsn_status" not in df.columns:

        logger.warning(
            "DSN Status column not found. Skipping DSN split."
        )

        return df

    logger.info(
        "Splitting DSN..."
    )

    # Convert to string
    dsn = (
        df["dsn_status"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Extract DSN Code and Description
    extracted = dsn.str.extract(
        r"^([0-9]+\.[0-9]+\.[0-9]+)\s*(.*)$"
    )

    df["DSN"] = extracted[0]

    df["DSN Description"] = extracted[1]

    return df


# ==========================================================
# DELIVERY RESULT
# ==========================================================

def delivery_result(df):

    logger.info(

        "Creating Delivery Result..."

    )

    def classify(status):

        status = str(status).lower()

        if "2." in status:

            return "Delivered"

        elif "4." in status:

            return "Temporary Failure"

        elif "5." in status:

            return "Permanent Failure"

        return "Unknown"

    if "DSN" in df.columns:

        df["Delivery Result"] = (

            df["DSN"]

            .apply(classify)

        )

    return df


# ==========================================================
# INVALID EMAIL LOGGING
# ==========================================================

def log_invalid_emails(df):

    invalid = df[

        df["Format Status"] == "Invalid"

    ]

    for email in invalid["Original Email"]:

        logger.invalid_email(email)

    logger.info(

        f"Invalid Emails : {len(invalid)}"

    )

    return df

# ==========================================================
# GENERATE REPORTS
# ==========================================================

def generate_reports(df):

    logger.info("Generating Reports...")

    reports = ReportGenerator(df)

    reports.generate_all()

    logger.info("Reports Generated Successfully")


# ==========================================================
# ETL PIPELINE
# ==========================================================

def run_etl():

    start_time = time.time()

    try:

        logger.start()

        # -------------------------------------
        # Read CSV Files
        # -------------------------------------

        df = read_csv_files()

        logger.info(f"Total Records Loaded : {len(df)}")

        # -------------------------------------
        # Remove Duplicates
        # -------------------------------------

        df = remove_duplicates(df)

        # -------------------------------------
        # Clean Emails
        # -------------------------------------

        df = clean_email_column(df)

        # -------------------------------------
        # Build Trusted Domains
        # -------------------------------------

        df, trusted_domains, domain_report = prepare_domains(df)

        # -------------------------------------
        # Load Cache
        # -------------------------------------

        load_cache()

        # -------------------------------------
        # Validate Domains
        # -------------------------------------

        df = validate_all_domains(df)

        # -------------------------------------
        # Correct Invalid Domains
        # -------------------------------------

        logger.info(
            "Correcting Invalid Domains..."
        )

        df = correct_dataframe(
            df,
            trusted_domains
        )

        corrected = df[
            df["Correction Status"] == "Corrected"
        ]

        for _, row in corrected.iterrows():

            try:

                logger.domain_corrected(

                    row["Mail Domain"],

                    row["Corrected Domain"],

                    row["Similarity Score"]

                )

            except Exception:

                pass

        # -------------------------------------
        # Split DSN
        # -------------------------------------

        df = split_dsn(df)

        # -------------------------------------
        # Delivery Result
        # -------------------------------------

        df = delivery_result(df)

        # -------------------------------------
        # Log Invalid Emails
        # -------------------------------------

        log_invalid_emails(df)

        # -------------------------------------
        # Generate Reports
        # -------------------------------------

        generate_reports(df)

        # -------------------------------------
        # Save Final Output
        # -------------------------------------

        df.to_csv(
            OUTPUT_FILE,
            index=False
        )

        # -------------------------------------
        # Summary
        # -------------------------------------

        total = len(df)

        valid = (
            df["Format Status"] == "Valid"
        ).sum()

        corrected = (
            df["Correction Status"] == "Corrected"
        ).sum()

        invalid = (
            df["Format Status"] == "Invalid"
        ).sum()

        logger.summary(
            total,
            valid,
            corrected,
            invalid
        )

        elapsed = round(
            time.time() - start_time,
            2
        )

        logger.info(
            f"Execution Time : {elapsed} seconds"
        )

        logger.end()

        print("\n")
        print("=" * 70)
        print("EMAIL ETL COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"Output File : {OUTPUT_FILE}")
        print(f"Execution Time : {elapsed} seconds")
        print("=" * 70)

    except Exception as e:

        logger.exception(
            f"ETL Failed : {e}"
        )

        print("\nETL FAILED")

        raise


# ==========================================================
# MAIN
# ==========================================================

def main():

    run_etl()


# ==========================================================
# ENTRY POINT
# ==========================================================

if __name__ == "__main__":

    main()