"""
cache_manager.py
----------------

Responsibilities

1. Load domain cache
2. Save domain cache
3. Get cached validation
4. Update cache
5. Batch update
"""

import os
import pandas as pd

from config import CACHE_FILE


class DomainCache:

    def __init__(self):

        self.cache = {}

        self.load()

    # ==========================================================
    # LOAD CACHE
    # ==========================================================

    def load(self):

        if not os.path.exists(CACHE_FILE):

            self.cache = {}

            return

        try:

            df = pd.read_csv(CACHE_FILE)

            required_columns = [
                "Domain",
                "Domain Status",
                "Validation Reason"
            ]

            for col in required_columns:

                if col not in df.columns:

                    self.cache = {}

                    return

            self.cache = {}

            for _, row in df.iterrows():

                self.cache[row["Domain"]] = {

                    "Domain": row["Domain"],

                    "Domain Status": row["Domain Status"],

                    "Validation Reason": row["Validation Reason"]
                }

        except Exception:

            self.cache = {}

    # ==========================================================
    # SAVE CACHE
    # ==========================================================

    def save(self):

        if len(self.cache) == 0:

            return

        df = pd.DataFrame(
            list(self.cache.values())
        )

        df.sort_values(
            "Domain",
            inplace=True
        )

        df.to_csv(
            CACHE_FILE,
            index=False
        )

    # ==========================================================
    # EXISTS
    # ==========================================================

    def exists(self, domain):

        if domain is None:

            return False

        return domain in self.cache

    # ==========================================================
    # GET
    # ==========================================================

    def get(self, domain):

        if domain is None:

            return None

        return self.cache.get(domain)

    # ==========================================================
    # ADD
    # ==========================================================

    def add(self, result):

        """
        result must be

        {
            "Domain": "...",
            "Domain Status": "...",
            "Validation Reason": "..."
        }
        """

        if result is None:

            return

        domain = result.get("Domain")

        if domain is None:

            return

        self.cache[domain] = result

    # ==========================================================
    # UPDATE MANY
    # ==========================================================

    def update(self, results):

        """
        results is a dictionary returned by
        validate_domains()
        """

        for domain, value in results.items():

            self.cache[domain] = value

    # ==========================================================
    # CLEAR CACHE
    # ==========================================================

    def clear(self):

        self.cache = {}

        if os.path.exists(CACHE_FILE):

            os.remove(CACHE_FILE)

    # ==========================================================
    # CACHE SIZE
    # ==========================================================

    def size(self):

        return len(self.cache)

    # ==========================================================
    # RETURN ALL
    # ==========================================================

    def all(self):

        return self.cache