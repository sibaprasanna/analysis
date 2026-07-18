"""
reports.py
----------

Creates all ETL output reports.
"""

import pandas as pd

from config import (
    OUTPUT_FILE,
    INVALID_FILE,
    DOMAIN_REPORT,
    CORRECTION_REPORT,
    SUMMARY_REPORT
)


class ReportGenerator:

    def __init__(self, df):

        self.df = df.copy()

    # ==========================================================
    # MAIN OUTPUT
    # ==========================================================

    def cleaned_report(self):

        self.df.to_csv(
            OUTPUT_FILE,
            index=False
        )

    # ==========================================================
    # INVALID EMAIL REPORT
    # ==========================================================

    def invalid_report(self):

        if "Format Status" not in self.df.columns:
            return

        invalid = self.df[
            self.df["Format Status"] == "Invalid"
        ]

        invalid.to_csv(
            INVALID_FILE,
            index=False
        )

    # ==========================================================
    # DOMAIN FREQUENCY REPORT
    # ==========================================================

    def domain_frequency_report(self):

        if "Mail Domain" not in self.df.columns:
            return

        report = (
            self.df["Mail Domain"]
            .dropna()
            .value_counts()
            .reset_index()
        )

        report.columns = [
            "Domain",
            "Count"
        ]

        report.to_csv(
            DOMAIN_REPORT,
            index=False
        )

    # ==========================================================
    # DOMAIN CORRECTION REPORT
    # ==========================================================

    def correction_report(self):

        if "Correction Status" not in self.df.columns:
            return

        corrected = self.df[
            self.df["Correction Status"] == "Corrected"
        ]

        cols = [
            "Original Email",
            "Clean Email",
            "Corrected Email",
            "Mail Domain",
            "Corrected Domain",
            "Similarity Score",
            "Correction Status"
        ]

        cols = [
            c for c in cols
            if c in corrected.columns
        ]

        if len(cols) == 0:
            return

        corrected[cols].to_csv(
            CORRECTION_REPORT,
            index=False
        )

    # ==========================================================
    # VALIDATION SUMMARY
    # ==========================================================

    def summary_report(self):

        total = len(self.df)

        valid = (
            (self.df["Format Status"] == "Valid").sum()
            if "Format Status" in self.df.columns
            else 0
        )

        corrected = (
            (self.df["Correction Status"] == "Corrected").sum()
            if "Correction Status" in self.df.columns
            else 0
        )

        invalid = (
            (self.df["Format Status"] == "Invalid").sum()
            if "Format Status" in self.df.columns
            else 0
        )

        unique_domains = (
            self.df["Mail Domain"].dropna().nunique()
            if "Mail Domain" in self.df.columns
            else 0
        )

        summary = {

            "Metric": [
                "Total Records",
                "Valid Emails",
                "Corrected Emails",
                "Invalid Emails",
                "Unique Domains"
            ],

            "Value": [
                total,
                valid,
                corrected,
                invalid,
                unique_domains
            ]

        }

        pd.DataFrame(summary).to_csv(
            SUMMARY_REPORT,
            index=False
        )

    # ==========================================================
    # RUN ALL REPORTS
    # ==========================================================

    def generate_all(self):

        self.cleaned_report()

        self.invalid_report()

        self.domain_frequency_report()

        self.correction_report()

        self.summary_report()