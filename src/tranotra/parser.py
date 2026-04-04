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
    REQUIRED_FIELDS = {"name", "country"}

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
        except ValueError as e:
            # Re-raise validation errors (format not supported, malformed data)
            logger.error(f"Validation error parsing {format} response: {e}")
            raise
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            # JSON parsing or encoding errors
            logger.error(f"Format parsing error ({format}): {e}")
            raise ValueError(f"Invalid {format} format: {str(e)}")
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error parsing {format} response: {e}")
            raise ValueError(f"Parser error: {str(e)}")

    def _parse_json(self, response: str) -> List[Dict]:
        """Parse JSON array into company records

        Handles JSON wrapped in Markdown code blocks (```json ... ```)
        and maps Gemini field names to internal field names
        """
        # Check if JSON is wrapped in Markdown code block
        json_str = response.strip()

        # Extract JSON from Markdown code block if present
        if "```json" in json_str:
            start = json_str.find("```json") + len("```json")
            end = json_str.find("```", start)
            if end > start:
                json_str = json_str[start:end].strip()
        elif "```" in json_str:
            start = json_str.find("```") + len("```")
            end = json_str.find("```", start)
            if end > start:
                json_str = json_str[start:end].strip()

        # Parse JSON
        data = json.loads(json_str)

        if not isinstance(data, list):
            data = [data]

        # Field name mappings from Gemini's response format to internal format
        field_mapping = {
            "Company Name (English)": "name",
            "City/Province": "city",
            "Year Established": "year_established",
            "Employees (approximate)": "employees",
            "Employees (approximate: <100 / 100-500 / 500-2000 / 2000+)": "employees",
            "Estimated Annual Revenue": "estimated_revenue",
            "Main Products": "main_products",
            "Main Products (specific)": "main_products",
            "Export Markets": "export_markets",
            "Export to EU/USA/Japan?": "eu_us_jp_export",
            "Raw Materials": "raw_materials",
            "Best Plasticizer for them": "recommended_product",
            "Why that plasticizer": "recommendation_reason",
            "Company Website": "website",
            "Contact Email": "contact_email",
            "LinkedIn Company Page URL": "linkedin_url",
            "Best job title to contact": "best_contact_title",
            "Prospect Score": "prospect_score",
            "Prospect Score (1-10)": "prospect_score"
        }

        companies = []
        for item in data:
            if isinstance(item, dict):
                # Map field names
                mapped_item = {}
                for gemini_field, value in item.items():
                    internal_field = field_mapping.get(gemini_field, gemini_field.lower())
                    mapped_item[internal_field] = value

                # Ensure country field is set (default to search country if missing)
                if "country" not in mapped_item:
                    mapped_item["country"] = "Vietnam"  # Default - would be better if passed as parameter

                companies.append(mapped_item)

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
        """Parse CSV into company records

        Handles UTF-8 BOM and various delimiters (comma, tab, semicolon)
        """
        # Remove UTF-8 BOM if present
        if response.startswith('\ufeff'):
            response = response[1:]

        f = StringIO(response)

        # Try to detect delimiter
        first_line = response.split('\n')[0] if response else ""
        if '\t' in first_line:
            delimiter = '\t'
        elif ';' in first_line:
            delimiter = ';'
        else:
            delimiter = ','  # Default to comma

        reader = csv.DictReader(f, delimiter=delimiter)

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

            # Set priority based on prospect_score if not provided
            if record.get("priority") == "N/A":
                score = record.get("prospect_score", 5)
                if score >= 8:
                    record["priority"] = "HIGH"
                elif score >= 6:
                    record["priority"] = "MEDIUM"
                else:
                    record["priority"] = "LOW"

            # Convert eu_us_jp_export to boolean if it's a string
            eu_us_jp = record.get("eu_us_jp_export")
            if isinstance(eu_us_jp, str):
                record["eu_us_jp_export"] = eu_us_jp.lower() in ("yes", "true", "1", "y")
            elif eu_us_jp == "N/A":
                record["eu_us_jp_export"] = False
            # If it's already a boolean, leave it as is

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
            Normalized URL without protocol or www, or empty string if invalid
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

        # Validate: normalized URL should contain at least 'linkedin.com'
        if not url or len(url) < 5:
            logger.warning(f"Invalid LinkedIn URL after normalization: {url}")
            return ""

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
