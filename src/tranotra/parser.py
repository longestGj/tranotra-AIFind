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
        and maps Gemini field names to internal field names.
        Tolerates malformed JSON with inline comments - extracts what it can.
        """
        import re

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

        # Clean up common malformed JSON patterns
        # 1. Numbers with inline comments: "1996 (Joint Venture...)" -> "1996"
        json_str = re.sub(r':\s*(\d+)\s+\([^)]*\)', r': \1', json_str)

        # 2. Remove trailing commas before closing braces/brackets
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)

        # 3. Handle &amp; and other HTML entities
        json_str = json_str.replace('&amp;', '&')

        # Try to parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # If standard parsing fails, try line-by-line parsing as fallback
            logger.warning(f"JSON parse error: {e}. Attempting line-by-line fallback parsing")
            data = self._parse_json_fallback(json_str)
            if not data:
                raise ValueError(f"Failed to parse JSON even with fallback: {e}")

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

    def _parse_json_fallback(self, json_str: str) -> List[Dict]:
        """Fallback JSON parser for malformed JSON

        Attempts to extract company objects by:
        1. Finding {...} blocks (potential company objects)
        2. Extracting key-value pairs from each block
        3. Building dictionaries from parsed fields
        """
        import re

        companies = []

        # Find all {...} blocks that look like company objects
        # Use regex to find balanced braces
        brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        blocks = re.findall(brace_pattern, json_str)

        logger.info(f"Fallback parser found {len(blocks)} potential company objects")

        for block in blocks:
            # Extract key-value pairs using regex
            # Pattern: "key": value (handles strings, numbers, booleans)
            company = {}

            # Find all "key": value pairs
            pair_pattern = r'"([^"]+)"\s*:\s*([^,}]+)'
            matches = re.findall(pair_pattern, block)

            for key, value in matches:
                # Clean up value
                value = value.strip()

                # Remove quotes if string
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]

                # Try to convert to int if numeric
                if value.isdigit():
                    value = int(value)

                company[key] = value

            # Only keep blocks with at least company name
            if company.get("Company Name (English)") or company.get("name"):
                companies.append(company)

        logger.info(f"Fallback parser extracted {len(companies)} companies")
        return companies

    def _parse_markdown(self, response: str) -> List[Dict]:
        """Parse Markdown table into company records

        Handles two formats:
        1. Field-as-rows format: Fields in first column, companies in subsequent columns
        2. Field-as-columns format: Fields as headers, one company per row
        """
        lines = response.strip().split("\n")
        if not lines:
            return []

        # Find all lines that look like table rows (start with |)
        table_lines = []
        table_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith("|"):
                if table_start == -1:
                    table_start = i
                table_lines.append((i, line))

        if not table_lines:
            logger.warning("No Markdown table found in response")
            return []

        # Get header line (first table line)
        header_line = table_lines[0][1]
        headers = [h.strip() for h in header_line.split("|")]
        headers = [h for h in headers if h.strip()]

        # Check if this is field-as-rows format (first column has "Field" or row numbers)
        is_field_rows_format = (
            len(headers) > 1 and
            ("Field" in headers[0] or "Company Name" in headers[1] or "VINA" in headers[1])
        )

        logger.debug(f"Markdown table format: {'field-as-rows' if is_field_rows_format else 'field-as-columns'}")

        companies = []

        if is_field_rows_format:
            # Field-as-rows format: companies are columns, fields are rows
            # Extract company names from header (skip first column which is field labels)
            company_names = headers[1:]  # Skip "Field" column

            if len(company_names) == 0:
                return []

            # Field name mappings for Markdown tables
            field_mapping = {
                "Company Name (English)": "name",
                "City/Province": "city",
                "City\\Province": "city",
                "Year Established": "year_established",
                "Employees (approximate)": "employees",
                "Estimated Annual Revenue": "estimated_revenue",
                "Main Products": "main_products",
                "Export Markets": "export_markets",
                "Export to EU/USA/Japan?": "eu_us_jp_export",
                "Export to EU\\USA\\Japan?": "eu_us_jp_export",
                "Raw Materials": "raw_materials",
                "Best Plasticizer for them": "recommended_product",
                "Why that plasticizer": "recommendation_reason",
                "Company Website": "website",
                "Contact Email": "contact_email",
                "LinkedIn Company Page URL": "linkedin_url",
                "Best job title to contact": "best_contact_title",
                "Prospect Score (1-10)": "prospect_score"
            }

            # Initialize company dicts
            for i, company_name in enumerate(company_names):
                companies.append({"name": company_name})

            # Parse data rows (skip header and separator)
            for row_idx in range(2, len(table_lines)):  # Skip header + separator
                line = table_lines[row_idx][1]
                cells = [c.strip() for c in line.split("|")]
                cells = [c for c in cells if c]

                if len(cells) < 2:
                    continue

                # First cell contains field name/label
                field_label = cells[0]
                # Clean up field label (remove markdown formatting)
                field_label = field_label.replace("**", "").strip()

                # Remove numbering prefix (e.g., "1. " or "2. ")
                import re
                field_label = re.sub(r'^\d+\.\s*', '', field_label)

                # Map field name
                internal_field = field_mapping.get(field_label, field_label.lower().replace(" ", "_"))

                # Assign values to companies
                for company_idx, value in enumerate(cells[1:]):
                    if company_idx < len(companies):
                        companies[company_idx][internal_field] = value

        else:
            # Field-as-columns format: one company per row
            for row_idx in range(2, len(table_lines)):  # Skip header + separator
                line = table_lines[row_idx][1]
                values = [v.strip() for v in line.split("|")]
                values = [v for v in values if v]

                if len(values) != len(headers):
                    continue

                company = dict(zip(headers, values))
                companies.append(company)

        # Ensure country is set for all companies
        for company in companies:
            if "country" not in company:
                company["country"] = "Vietnam"  # Default

        logger.info(f"Parsed {len(companies)} companies from Markdown table (field-rows format)")
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

        Tolerant filtering strategy:
        - Skip only if missing REQUIRED fields (name, country)
        - For optional fields with format errors, attempt to clean or skip gracefully
        - Don't reject entire record just because one field is malformed

        Returns:
            List of valid, prepared company records
        """
        valid_records = []

        for idx, company in enumerate(companies):
            # Check required fields - only these are hard requirements
            name = company.get("name") or company.get("Company Name (English)")
            country = company.get("country") or company.get("Country")

            if not name or not country:
                logger.warning(
                    f"Row {idx}: Skipping company without name or country. Has: {list(company.keys())}"
                )
                continue

            # Prepare record with all fields
            record = {}

            # Copy all fields, filling missing optional ones with "N/A"
            for field in self.ALL_FIELDS:
                if field in company:
                    value = company[field]
                    # Try to clean problematic values
                    if value and isinstance(value, str):
                        value = value.strip()
                    record[field] = value if value else "N/A"
                elif field in self.REQUIRED_FIELDS:
                    # Required field missing - should have been caught above
                    record[field] = None
                else:
                    # Optional field - fill with N/A
                    record[field] = "N/A"

            # Ensure name and country are set
            record["name"] = name
            record["country"] = country

            # Normalize LinkedIn URL if present and valid
            try:
                if record.get("linkedin_url") and record["linkedin_url"] != "N/A":
                    record["linkedin_normalized"] = self.normalize_linkedin_url(
                        record["linkedin_url"]
                    )
                else:
                    record["linkedin_normalized"] = ""
            except Exception as e:
                logger.debug(f"Failed to normalize LinkedIn URL for {name}: {e}")
                record["linkedin_normalized"] = ""

            # Validate and clamp score (tolerant - converts to valid range even if malformed)
            try:
                record["prospect_score"] = self.validate_and_clamp_score(
                    record.get("prospect_score")
                )
            except Exception as e:
                logger.debug(f"Failed to validate score for {name}: {e}")
                record["prospect_score"] = 5  # Default middle score

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
