"""
logger.py
----------

Project Logging Module
"""

import logging
import os

from config import LOG_FILE


class ETLLogger:

    def __init__(self):

        self.logger = logging.getLogger("Email_ETL")

        self.logger.setLevel(logging.INFO)

        # Prevent duplicate handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        formatter = logging.Formatter(

            "%(asctime)s | %(levelname)s | %(message)s",

            "%Y-%m-%d %H:%M:%S"

        )

        # -------------------------------------------------
        # File Handler
        # -------------------------------------------------

        file_handler = logging.FileHandler(

            LOG_FILE,

            mode="a",

            encoding="utf-8"

        )

        file_handler.setFormatter(formatter)

        # -------------------------------------------------
        # Console Handler
        # -------------------------------------------------

        console_handler = logging.StreamHandler()

        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

        self.logger.addHandler(console_handler)

    # =====================================================
    # INFO
    # =====================================================

    def info(self, message):

        self.logger.info(message)

    # =====================================================
    # WARNING
    # =====================================================

    def warning(self, message):

        self.logger.warning(message)

    # =====================================================
    # ERROR
    # =====================================================

    def error(self, message):

        self.logger.error(message)

    # =====================================================
    # EXCEPTION
    # =====================================================

    def exception(self, message):

        self.logger.exception(message)

    # =====================================================
    # ETL START
    # =====================================================

    def start(self):

        self.info("=" * 70)

        self.info("EMAIL ETL STARTED")

        self.info("=" * 70)

    # =====================================================
    # ETL END
    # =====================================================

    def end(self):

        self.info("=" * 70)

        self.info("EMAIL ETL COMPLETED")

        self.info("=" * 70)

    # =====================================================
    # FILE
    # =====================================================

    def file_processed(self, filename, records):

        self.info(

            f"Processed File : {filename} | Records : {records}"

        )

    # =====================================================
    # CACHE
    # =====================================================

    def cache_loaded(self, size):

        self.info(

            f"Cache Loaded : {size} Domains"

        )

    def cache_saved(self, size):

        self.info(

            f"Cache Saved : {size} Domains"

        )

    # =====================================================
    # DOMAIN
    # =====================================================

    def domain_validated(self, domain):

        self.info(

            f"Validated Domain : {domain}"

        )

    def domain_corrected(

        self,

        old_domain,

        new_domain,

        score

    ):

        self.info(

            f"Domain Corrected : "

            f"{old_domain} -> {new_domain} "

            f"(Score={score})"

        )

    # =====================================================
    # EMAIL
    # =====================================================

    def invalid_email(self, email):

        self.warning(

            f"Invalid Email : {email}"

        )

    # =====================================================
    # SUMMARY
    # =====================================================

    def summary(

        self,

        total,

        valid,

        corrected,

        invalid

    ):

        self.info("-" * 60)

        self.info(f"Total Emails      : {total}")

        self.info(f"Valid Emails      : {valid}")

        self.info(f"Corrected Emails  : {corrected}")

        self.info(f"Invalid Emails    : {invalid}")

        self.info("-" * 60)