"""Data parsing and normalization logic for company records"""

import json
import csv
import logging
from io import StringIO
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CompanyParser:
    """Handles parsing, normalization, and validation of company data from various formats"""

    # Required fields that cannot be missing
    REQUIRED_FIELDS = {"name", "country", "prospect_score"}

    # All expected company fields
    ALL_FIELDS = {
        "name", "country", "city", "year_established", "employees",
        "estimated_revenue", "main_products", "export_markets",
        "eu_us_jp_export", "raw_materials", "recommended_product",
        "recommendation_reason", "website", "contact_email",
        "linkedin_url", "best_contact_title", "prospect_score", "priority"
    }

    def parse_response(self, response: str, format: str) -> List[Dict]:
        """Parse raw response into list of company dicts

        Args:
            response: Raw string from Gemini API
            format: "JSON", "Markdown", or "CSV"

        Returns:
            List of company dicts (may be incomplete/invalid)

        Raises:
            ValueError: If format is unsupported or response malformed
        """
        if not response or not response.strip():
            return []

        try:
            if format == "JSON":
                return self._parse_json(response)
            elif format == "Markdown":
                return self._parse_markdown(response)
            elif format == "CSV":
                return self._parse_csv(response)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            logger.error(f"Error parsing {format} response: {e}")
            raise

    def _parse_json(self, response: str) -> List[Dict]:
        """Parse JSON array into company records"""
        data = json.loads(response)

        if not isinstance(data, list):
            data = [data]

        companies = []
        for item in data:
            if isinstance(item, dict):
                companies.append(item)

        return companies

    def _parse_markdown(self, response: str) -> List[Dict]:
        """Parse Markdown table into company records"""
        lines = response.strip().split("\n")
        if len(lines) < 3:  # Need header, separator, and at least one row
            return []

        # Extract header
        header_line = lines[0]
        headers = [h.strip() for h in header_line.split("|") if h.strip()]

        companies = []
        for line in lines[2:]:  # Skip header and separator
            if line.strip() and "|" in line:
                values = [v.strip() for v in line.split("|") if v.strip()]
                if len(values) == len(headers):
                    company = dict(zip(headers, values))
                    companies.append(company)

        return companies

    def _parse_csv(self, response: str) -> List[Dict]:
        """Parse CSV into company records"""
        f = StringIO(response)
        reader = csv.DictReader(f)

        companies = []
        if reader.fieldnames:
            for row in reader:
                # Filter out None keys that might come from malformed CSV
                clean_row = {k: v for k, v in row.items() if k is not None}
                companies.append(clean_row)

        return companies

    def _filter_and_prepare_records(self, companies: List[Dict]) -> List[Dict]:
        """Filter out invalid records and prepare for insertion

        - Skip records missing required fields
        - Fill optional fields with "N/A"
        - Normalize LinkedIn URLs
        - Validate scores

        Returns:
            List of valid, prepared company records
        """
        valid_records = []

        for idx, company in enumerate(companies):
            # Check required fields
            if not company.get("name") or not company.get("country"):
                logger.warning(
                    f"Row {idx}: Skipping company without name or country"
                )
                continue

            # Prepare record with all fields
            record = {}

            # Copy all fields, filling missing optional ones with "N/A"
            for field in self.ALL_FIELDS:
                if field in company:
                    record[field] = company[field]
                elif field in self.REQUIRED_FIELDS:
                    # Required field missing - should have been caught above
                    record[field] = None
                else:
                    # Optional field - fill with N/A
                    record[field] = "N/A"

            # Normalize LinkedIn URL if present
            if record.get("linkedin_url"):
                record["linkedin_normalized"] = self.normalize_linkedin_url(
                    record["linkedin_url"]
                )
            else:
                record["linkedin_normalized"] = ""

            # Validate and clamp score
            record["prospect_score"] = self.validate_and_clamp_score(
                record.get("prospect_score")
            )

            valid_records.append(record)

        return valid_records

    def normalize_linkedin_url(self, url: str) -> str:
        """Normalize LinkedIn URL to canonical form

        Example:
            Input: "https://www.linkedin.com/company/cadivi/"
            Output: "linkedin.com/company/cadivi"

        Args:
            url: Raw LinkedIn URL

        Returns:
            Normalized URL without protocol or www
        """
        if not url:
            return ""

        # Convert to lowercase
        url = url.lower().strip()

        # Remove protocol (https:// or http://)
        if url.startswith("https://"):
            url = url[8:]
        elif url.startswith("http://"):
            url = url[7:]

        # Remove www. prefix
        if url.startswith("www."):
            url = url[4:]

        # Remove trailing slashes
        url = url.rstrip("/")

        # Replace spaces with hyphens
        url = url.replace(" ", "-")

        return url

    def validate_and_clamp_score(self, score: Any) -> int:
        """Validate prospect score and clamp to 1-10 range

        Args:
            score: Prospect score from response (can be int, str, float, None)

        Returns:
            int: Clamped score 1-10, or 0 if invalid
        """
        if score is None or score == "":
            return 0

        try:
            # Try to convert to int
            if isinstance(score, str):
                score = int(float(score))
            else:
                score = int(score)

            # Clamp to 1-10
            if score < 1:
                return 1
            elif score > 10:
                return 10
            else:
                return score

        except (ValueError, TypeError):
            logger.warning(f"Invalid score value: {score}, setting to 0")
            return 0


__all__ = ["CompanyParser"]
