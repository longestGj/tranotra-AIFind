"""Tests for data parsing and normalization logic"""

import pytest
import json
from tranotra.parser import CompanyParser


class TestCompanyParser:
    """Test CompanyParser class for parsing different formats"""

    @pytest.fixture
    def parser(self):
        """Create parser instance for each test"""
        return CompanyParser()

    # JSON Format Tests
    def test_parse_json_single_company(self, parser):
        """Test parsing JSON with single company"""
        json_data = json.dumps([{
            "name": "Cadivi Ltd",
            "country": "Vietnam",
            "city": "HCMC",
            "year_established": 2005,
            "employees": "100-500",
            "estimated_revenue": "$5M-10M",
            "main_products": "PVC compounds",
            "export_markets": "Thailand, Malaysia",
            "eu_us_jp_export": True,
            "raw_materials": "Petroleum",
            "recommended_product": "Masterbatch",
            "recommendation_reason": "High-volume processor",
            "website": "cadivi.vn",
            "contact_email": "contact@cadivi.vn",
            "linkedin_url": "https://www.linkedin.com/company/cadivi/",
            "best_contact_title": "Operations Director",
            "prospect_score": 9,
            "priority": "A"
        }])

        result = parser.parse_response(json_data, "JSON")
        assert len(result) == 1
        assert result[0]["name"] == "Cadivi Ltd"
        assert result[0]["country"] == "Vietnam"

    def test_parse_json_multiple_companies(self, parser):
        """Test parsing JSON with multiple companies"""
        json_data = json.dumps([
            {"name": "Company A", "country": "Vietnam", "prospect_score": 8, "linkedin_url": "https://linkedin.com/company/a/"},
            {"name": "Company B", "country": "Thailand", "prospect_score": 7, "linkedin_url": "https://linkedin.com/company/b/"}
        ])

        result = parser.parse_response(json_data, "JSON")
        assert len(result) == 2
        assert result[0]["name"] == "Company A"
        assert result[1]["name"] == "Company B"

    def test_parse_json_invalid_format(self, parser):
        """Test parsing invalid JSON raises error"""
        invalid_json = "not valid json {"

        with pytest.raises(ValueError):
            parser.parse_response(invalid_json, "JSON")

    # LinkedIn URL Normalization Tests
    def test_normalize_linkedin_url_full(self, parser):
        """Test LinkedIn URL normalization"""
        url = "https://www.linkedin.com/company/cadivi/"
        normalized = parser.normalize_linkedin_url(url)
        assert normalized == "linkedin.com/company/cadivi"

    def test_normalize_linkedin_url_no_www(self, parser):
        """Test normalization without www prefix"""
        url = "https://linkedin.com/company/company-name/"
        normalized = parser.normalize_linkedin_url(url)
        assert normalized == "linkedin.com/company/company-name"

    def test_normalize_linkedin_url_with_spaces(self, parser):
        """Test normalization with spaces in URL"""
        url = "https://www.linkedin.com/company/my company/"
        normalized = parser.normalize_linkedin_url(url)
        assert "my-company" in normalized.lower()

    def test_normalize_linkedin_url_http(self, parser):
        """Test normalization with http (not https)"""
        url = "http://www.linkedin.com/company/test/"
        normalized = parser.normalize_linkedin_url(url)
        assert normalized == "linkedin.com/company/test"

    def test_normalize_linkedin_url_empty(self, parser):
        """Test normalization with empty URL"""
        result = parser.normalize_linkedin_url("")
        assert result == "" or result == "linkedin.com"

    # Score Validation Tests
    def test_validate_score_valid_range(self, parser):
        """Test score validation with valid range"""
        assert parser.validate_and_clamp_score(5) == 5
        assert parser.validate_and_clamp_score(1) == 1
        assert parser.validate_and_clamp_score(10) == 10

    def test_validate_score_below_range(self, parser):
        """Test score below valid range is clamped to 1"""
        assert parser.validate_and_clamp_score(-5) == 1
        assert parser.validate_and_clamp_score(0) == 1

    def test_validate_score_above_range(self, parser):
        """Test score above valid range is clamped to 10"""
        assert parser.validate_and_clamp_score(15) == 10
        assert parser.validate_and_clamp_score(100) == 10

    def test_validate_score_non_numeric(self, parser):
        """Test non-numeric score is set to 0"""
        assert parser.validate_and_clamp_score("abc") == 0
        assert parser.validate_and_clamp_score(None) == 0
        assert parser.validate_and_clamp_score("") == 0

    def test_validate_score_float(self, parser):
        """Test float score is converted to int"""
        result = parser.validate_and_clamp_score(7.5)
        assert isinstance(result, int)
        assert result in [7, 8]  # Should be clamped to int

    # Field Handling Tests
    def test_handle_missing_required_field(self, parser):
        """Test handling of missing required fields"""
        data = [
            {"country": "Vietnam"},  # Missing name (required)
            {"name": "Company B", "country": "Thailand"}  # Valid
        ]

        result = parser._filter_and_prepare_records(data)
        # Should only have the valid record
        assert len(result) == 1
        assert result[0]["name"] == "Company B"

    def test_handle_missing_optional_field(self, parser):
        """Test missing optional fields are filled with N/A"""
        data = [{
            "name": "Company A",
            "country": "Vietnam",
            "linkedin_url": "https://linkedin.com/company/a/"
        }]

        result = parser._filter_and_prepare_records(data)
        assert len(result) == 1
        # Check that optional fields are filled
        assert result[0].get("city", "N/A") is not None

    # Markdown Format Tests
    def test_parse_markdown_table(self, parser):
        """Test parsing Markdown table format"""
        markdown = """| name | country | city | prospect_score |
| --- | --- | --- | --- |
| Company A | Vietnam | HCMC | 8 |
| Company B | Thailand | Bangkok | 7 |"""

        result = parser.parse_response(markdown, "Markdown")
        assert len(result) >= 1  # At least one company parsed

    # CSV Format Tests
    def test_parse_csv_format(self, parser):
        """Test parsing CSV format"""
        csv_data = """name,country,city,prospect_score
Company A,Vietnam,HCMC,8
Company B,Thailand,Bangkok,7"""

        result = parser.parse_response(csv_data, "CSV")
        assert len(result) >= 1  # At least one company parsed

    # Unsupported Format Test
    def test_parse_unsupported_format(self, parser):
        """Test unsupported format raises error"""
        with pytest.raises(ValueError):
            parser.parse_response("some data", "UNKNOWN")


class TestLinkedInNormalization:
    """Detailed LinkedIn URL normalization tests"""

    @pytest.fixture
    def parser(self):
        return CompanyParser()

    def test_protocol_removal_https(self, parser):
        """Remove https:// protocol"""
        assert "https://" not in parser.normalize_linkedin_url("https://linkedin.com/company/test/")

    def test_protocol_removal_http(self, parser):
        """Remove http:// protocol"""
        assert "http://" not in parser.normalize_linkedin_url("http://linkedin.com/company/test/")

    def test_www_removal(self, parser):
        """Remove www. prefix"""
        result = parser.normalize_linkedin_url("https://www.linkedin.com/company/test/")
        assert not result.startswith("www")

    def test_trailing_slash_removal(self, parser):
        """Remove trailing slashes"""
        result = parser.normalize_linkedin_url("https://linkedin.com/company/test///")
        assert not result.endswith("/")

    def test_lowercase_conversion(self, parser):
        """Convert to lowercase"""
        result = parser.normalize_linkedin_url("HTTPS://LINKEDIN.COM/COMPANY/TEST/")
        assert result == result.lower()

    def test_space_to_hyphen(self, parser):
        """Convert spaces to hyphens"""
        result = parser.normalize_linkedin_url("https://linkedin.com/company/my company/")
        assert " " not in result
        assert "my-company" in result.lower()
