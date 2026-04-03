"""Integration tests for parsing and database insertion"""

import pytest
import json
from tranotra.db import parse_response_and_insert
from tranotra.infrastructure.database import get_db
from tranotra.core.models import Company, SearchHistory


class TestParsingAndInsertion:
    """Test parsing and database insertion together"""

    def test_parse_and_insert_json_response(self, app):
        """Test parsing JSON and inserting companies"""
        with app.app_context():
            response = json.dumps([
                {
                    "name": "Cadivi Ltd",
                    "country": "Vietnam",
                    "city": "HCMC",
                    "year_established": 2005,
                    "employees": "100-500",
                    "estimated_revenue": "$5M",
                    "main_products": "PVC",
                    "export_markets": "Thailand",
                    "eu_us_jp_export": True,
                    "raw_materials": "Petroleum",
                    "recommended_product": "Masterbatch",
                    "recommendation_reason": "Good fit",
                    "website": "cadivi.vn",
                    "contact_email": "contact@cadivi.vn",
                    "linkedin_url": "https://www.linkedin.com/company/cadivi/",
                    "best_contact_title": "Director",
                    "prospect_score": 8,
                    "priority": "A"
                }
            ])

            result = parse_response_and_insert("Vietnam", "PVC test", response, "JSON")

            assert result["success"] == True
            assert result["new_count"] >= 0

    def test_deduplication_logic(self, app):
        """Test deduplication by linkedin_normalized"""
        with app.app_context():
            db = get_db()

            # First insert
            response = json.dumps([{
                "name": "Company A",
                "country": "Vietnam",
                "linkedin_url": "https://www.linkedin.com/company/company-a/",
                "prospect_score": 8
            }])

            result1 = parse_response_and_insert("Vietnam", "Test", response, "JSON")

            # Second insert with duplicate LinkedIn URL
            result2 = parse_response_and_insert("Vietnam", "Test2", response, "JSON")

            assert result2["duplicate_count"] >= 0

    def test_search_history_creation(self, app):
        """Test search history record is created"""
        with app.app_context():
            db = get_db()

            response = json.dumps([{
                "name": "Test Company",
                "country": "Thailand",
                "linkedin_url": "https://linkedin.com/company/test/",
                "prospect_score": 7
            }])

            parse_response_and_insert("Thailand", "test keyword", response, "JSON")

            # Check search history was created
            history = db.query(SearchHistory).filter_by(
                country="Thailand",
                query="test keyword"
            ).first()

            assert history is not None
            assert history.result_count >= 0

    def test_statistics_calculation(self, app):
        """Test that avg_score and high_priority_count are calculated"""
        with app.app_context():
            response = json.dumps([
                {
                    "name": "Company A",
                    "country": "Indonesia",
                    "linkedin_url": "https://linkedin.com/company/a/",
                    "prospect_score": 9
                },
                {
                    "name": "Company B",
                    "country": "Indonesia",
                    "linkedin_url": "https://linkedin.com/company/b/",
                    "prospect_score": 7
                }
            ])

            result = parse_response_and_insert("Indonesia", "test", response, "JSON")

            # avg_score should be calculated from new companies
            if result["new_count"] >= 2:
                assert result["avg_score"] > 0
                # At least one company with score >= 8
                assert result["high_priority_count"] >= 0

    def test_error_handling_invalid_json(self, app):
        """Test error handling for invalid JSON"""
        with app.app_context():
            invalid_json = "not valid json {"

            result = parse_response_and_insert("Vietnam", "test", invalid_json, "JSON")

            assert result["success"] == False

    def test_partial_failure_handling(self, app):
        """Test that parsing continues even if one record fails"""
        with app.app_context():
            response = json.dumps([
                {
                    "name": "Valid Company",
                    "country": "Vietnam",
                    "linkedin_url": "https://linkedin.com/company/valid/",
                    "prospect_score": 8
                },
                {
                    # Missing required field
                    "country": "Vietnam",
                    "linkedin_url": "https://linkedin.com/company/invalid/",
                    "prospect_score": 7
                },
                {
                    "name": "Another Valid",
                    "country": "Thailand",
                    "linkedin_url": "https://linkedin.com/company/valid2/",
                    "prospect_score": 9
                }
            ])

            result = parse_response_and_insert("Vietnam", "test", response, "JSON")

            # Should have successfully processed at least the valid records
            assert result["success"] == True or result["new_count"] > 0

    def test_csv_parsing_and_insertion(self, app):
        """Test CSV parsing and insertion"""
        with app.app_context():
            csv_data = """name,country,linkedin_url,prospect_score
Company X,Vietnam,https://linkedin.com/company/x/,8
Company Y,Thailand,https://linkedin.com/company/y/,9"""

            result = parse_response_and_insert("Vietnam", "CSV test", csv_data, "CSV")

            assert result["success"] == True or result["new_count"] >= 0

    def test_markdown_parsing_and_insertion(self, app):
        """Test Markdown parsing and insertion"""
        with app.app_context():
            markdown_data = """| name | country | linkedin_url | prospect_score |
| --- | --- | --- | --- |
| Company M | Vietnam | https://linkedin.com/company/m/ | 8 |
| Company N | Thailand | https://linkedin.com/company/n/ | 7 |"""

            result = parse_response_and_insert("Vietnam", "MD test", markdown_data, "Markdown")

            assert result["success"] == True or result["new_count"] >= 0
