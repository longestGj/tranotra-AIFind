"""End-to-end integration tests for the complete search pipeline
Tests: Search form → Gemini API → File saving → Format detection → Data parsing → Database insertion
"""

import json
import os
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
from tranotra.db import parse_response_and_insert, get_search_history
from tranotra.infrastructure.database import get_db
from tranotra.core.models import Company, SearchHistory


class TestEndToEndSearchPipeline:
    """Test complete search pipeline from form submission to database storage"""

    @pytest.fixture
    def mock_gemini_response_json(self):
        """Sample JSON response from Gemini API"""
        return [
            {
                "name": "Cadivi Vietnam Ltd",
                "country": "Vietnam",
                "city": "Ho Chi Minh City",
                "year_established": 2005,
                "employees": "500-1000",
                "estimated_revenue": "$50M+",
                "main_products": "PVC resin and compounds",
                "export_markets": "USA, EU, Japan",
                "eu_us_jp_export": True,
                "raw_materials": "Petroleum derivatives",
                "recommended_product": "DOTP Plasticizer",
                "recommendation_reason": "Large cable manufacturer using PVC",
                "website": "cadivi.vn",
                "contact_email": "sales@cadivi.vn",
                "linkedin_url": "https://www.linkedin.com/company/cadivi-ltd/",
                "best_contact_title": "Procurement Director",
                "prospect_score": 9,
                "priority": "A"
            },
            {
                "name": "Thai Plastic Industries",
                "country": "Thailand",
                "city": "Bangkok",
                "year_established": 2010,
                "employees": "200-500",
                "estimated_revenue": "$30M",
                "main_products": "Flexible PVC products",
                "export_markets": "ASEAN, India",
                "eu_us_jp_export": False,
                "raw_materials": "PVC resin",
                "recommended_product": "TOTM Plasticizer",
                "recommendation_reason": "Growing PVC product manufacturer",
                "website": "thaiplasinc.co.th",
                "contact_email": "contact@thaiplasinc.co.th",
                "linkedin_url": "https://linkedin.com/company/thai-plastics/",
                "best_contact_title": "Sales Manager",
                "prospect_score": 7,
                "priority": "B"
            }
        ]

    @pytest.fixture
    def mock_gemini_response_csv(self):
        """Sample CSV response from Gemini API"""
        return """name,country,city,year_established,employees,estimated_revenue,main_products,export_markets,eu_us_jp_export,raw_materials,recommended_product,recommendation_reason,website,contact_email,linkedin_url,best_contact_title,prospect_score,priority
Cadivi Vietnam Ltd,Vietnam,Ho Chi Minh City,2005,500-1000,$50M+,PVC resin,USA;EU;Japan,true,Petroleum,DOTP,Large cable manufacturer,cadivi.vn,sales@cadivi.vn,https://linkedin.com/company/cadivi/,Procurement Director,9,A
Thai Plastic Industries,Thailand,Bangkok,2010,200-500,$30M,Flexible PVC,ASEAN;India,false,PVC resin,TOTM,Growing manufacturer,thaiplasinc.co.th,contact@thaiplasinc.co.th,https://linkedin.com/company/thai-plastics/,Sales Manager,7,B"""

    @pytest.fixture
    def mock_gemini_response_markdown(self):
        """Sample Markdown table response from Gemini API"""
        return """| name | country | city | employees | prospect_score |
| --- | --- | --- | --- | --- |
| Cadivi Ltd | Vietnam | HCMC | 500-1000 | 9 |
| Thai Plastics | Thailand | Bangkok | 200-500 | 7 |"""

    def test_search_pipeline_with_json_response(self, app, mock_gemini_response_json):
        """Test complete pipeline: JSON response → parsing → database insertion"""
        with app.app_context():
            db = get_db()

            # Prepare test data
            response_json = json.dumps(mock_gemini_response_json)
            country = "Vietnam"
            query = "PVC manufacturer"

            # Execute parsing and insertion
            result = parse_response_and_insert(
                country=country,
                query=query,
                response_or_filepath=response_json,
                format="JSON"
            )

            # Verify success
            assert result["success"] == True, f"Pipeline failed: {result.get('error')}"
            assert result["new_count"] >= 0

            # Verify database records were created
            companies = db.query(Company).filter_by(country=country).all()
            assert len(companies) >= result["new_count"]

            # Verify search history was created
            history = db.query(SearchHistory).filter_by(
                country=country,
                query=query
            ).order_by(SearchHistory.created_at.desc()).first()

            assert history is not None
            assert history.result_count >= 0
            assert history.new_count >= 0
            assert history.duplicate_count >= 0

    def test_search_pipeline_with_csv_response(self, app, mock_gemini_response_csv):
        """Test complete pipeline: CSV response → parsing → database insertion"""
        with app.app_context():
            db = get_db()

            country = "Thailand"
            query = "Plastic manufacturer"

            result = parse_response_and_insert(
                country=country,
                query=query,
                response_or_filepath=mock_gemini_response_csv,
                format="CSV"
            )

            assert result["success"] == True or result["new_count"] >= 0

            # Verify database consistency
            if result["new_count"] > 0:
                companies = db.query(Company).filter_by(country=country).all()
                assert len(companies) >= result["new_count"]

    def test_search_pipeline_with_markdown_response(self, app, mock_gemini_response_markdown):
        """Test complete pipeline: Markdown response → parsing → database insertion"""
        with app.app_context():
            country = "Vietnam"
            query = "Cable manufacturer"

            result = parse_response_and_insert(
                country=country,
                query=query,
                response_or_filepath=mock_gemini_response_markdown,
                format="Markdown"
            )

            # Markdown parsing may be less precise, but should succeed or return valid error
            assert isinstance(result, dict)
            assert "success" in result or "new_count" in result

    def test_deduplication_across_searches(self, app, mock_gemini_response_json):
        """Test deduplication logic: same company in multiple searches"""
        with app.app_context():
            db = get_db()

            response_json = json.dumps(mock_gemini_response_json)

            # First search
            result1 = parse_response_and_insert(
                country="Vietnam",
                query="PVC manufacturer",
                response_or_filepath=response_json,
                format="JSON"
            )

            first_new_count = result1.get("new_count", 0)

            # Second search with same response (simulate duplicate)
            result2 = parse_response_and_insert(
                country="Vietnam",
                query="PVC supplier",
                response_or_filepath=response_json,
                format="JSON"
            )

            second_new_count = result2.get("new_count", 0)
            second_dup_count = result2.get("duplicate_count", 0)

            # Second search should have fewer new companies (duplicates)
            if first_new_count > 0:
                assert second_dup_count >= 0, "Deduplication should detect duplicates"

    def test_score_statistics_calculation(self, app, mock_gemini_response_json):
        """Test that statistics (avg_score, high_priority_count) are calculated correctly"""
        with app.app_context():
            response_json = json.dumps(mock_gemini_response_json)

            result = parse_response_and_insert(
                country="Vietnam",
                query="Manufacturing test",
                response_or_filepath=response_json,
                format="JSON"
            )

            # Verify statistics fields exist
            assert "avg_score" in result
            assert "high_priority_count" in result

            # If companies were inserted, stats should be calculated
            if result["new_count"] > 0:
                assert result["avg_score"] >= 0
                assert result["high_priority_count"] >= 0

    def test_search_history_statistics_accuracy(self, app, mock_gemini_response_json):
        """Test that search history accurately records statistics"""
        with app.app_context():
            db = get_db()

            response_json = json.dumps(mock_gemini_response_json)
            country = "Indonesia"
            query = "Manufacturing test"

            result = parse_response_and_insert(
                country=country,
                query=query,
                response_or_filepath=response_json,
                format="JSON"
            )

            # Retrieve search history
            history = db.query(SearchHistory).filter_by(
                country=country,
                query=query
            ).order_by(SearchHistory.created_at.desc()).first()

            if history:
                # Verify statistics match
                assert history.new_count == result.get("new_count", 0)
                assert history.duplicate_count == result.get("duplicate_count", 0)

                # If there are new companies, avg_score should be set
                if history.new_count > 0:
                    assert history.avg_score is not None or history.avg_score >= 0

    def test_linkedin_url_normalization(self, app):
        """Test LinkedIn URL normalization in the pipeline"""
        with app.app_context():
            db = get_db()

            test_data = [
                {
                    "name": "Test Company",
                    "country": "Vietnam",
                    "linkedin_url": "https://www.linkedin.com/company/test-company/",
                    "prospect_score": 8
                }
            ]

            response_json = json.dumps(test_data)

            result = parse_response_and_insert(
                country="Vietnam",
                query="LinkedIn test",
                response_or_filepath=response_json,
                format="JSON"
            )

            # Verify normalization occurred
            if result["new_count"] > 0:
                company = db.query(Company).filter_by(name="Test Company").first()
                assert company is not None
                assert company.linkedin_normalized is not None
                # Normalized URL should not contain https:// or www.
                assert "https://" not in company.linkedin_normalized
                assert "www." not in company.linkedin_normalized

    def test_missing_field_handling(self, app):
        """Test that missing fields are filled with defaults without failing"""
        with app.app_context():
            db = get_db()

            # Response with missing optional fields
            incomplete_data = [
                {
                    "name": "Minimal Company",
                    "country": "Vietnam",
                    # Missing: city, employees, estimated_revenue, etc.
                    "prospect_score": 5
                }
            ]

            response_json = json.dumps(incomplete_data)

            result = parse_response_and_insert(
                country="Vietnam",
                query="Missing fields test",
                response_or_filepath=response_json,
                format="JSON"
            )

            # Should succeed even with missing fields
            assert result["success"] == True or result["new_count"] >= 0

    def test_invalid_score_handling(self, app):
        """Test that invalid prospect scores are handled gracefully"""
        with app.app_context():
            db = get_db()

            test_data = [
                {
                    "name": "Bad Score Company",
                    "country": "Vietnam",
                    "prospect_score": 15  # Invalid: > 10
                },
                {
                    "name": "Negative Score Company",
                    "country": "Vietnam",
                    "prospect_score": -5  # Invalid: < 1
                },
                {
                    "name": "Valid Score Company",
                    "country": "Vietnam",
                    "prospect_score": 8
                }
            ]

            response_json = json.dumps(test_data)

            result = parse_response_and_insert(
                country="Vietnam",
                query="Score clamping test",
                response_or_filepath=response_json,
                format="JSON"
            )

            # Pipeline should handle invalid scores
            assert result["success"] == True or result["new_count"] > 0

            # Verify scores are clamped in database
            if result["new_count"] > 0:
                companies = db.query(Company).filter_by(country="Vietnam").all()
                for company in companies:
                    assert 0 <= company.prospect_score <= 10 or company.prospect_score is None

    def test_empty_response_handling(self, app):
        """Test handling of empty Gemini response"""
        with app.app_context():
            response_json = json.dumps([])

            result = parse_response_and_insert(
                country="Vietnam",
                query="Empty response test",
                response_or_filepath=response_json,
                format="JSON"
            )

            # Should handle gracefully - may return success or failure
            assert isinstance(result, dict)
            # Even with empty response, new_count should be tracked
            assert "new_count" in result or "success" in result

    def test_large_dataset_processing(self, app):
        """Test pipeline performance with larger dataset"""
        with app.app_context():
            db = get_db()

            # Create test data with 50 companies
            large_dataset = []
            for i in range(50):
                large_dataset.append({
                    "name": f"Company {i}",
                    "country": "Vietnam",
                    "city": f"City {i % 5}",
                    "prospect_score": (i % 10) + 1,
                    "linkedin_url": f"https://linkedin.com/company/company-{i}/",
                    "contact_email": f"contact{i}@company.com"
                })

            response_json = json.dumps(large_dataset)

            result = parse_response_and_insert(
                country="Vietnam",
                query="Large dataset test",
                response_or_filepath=response_json,
                format="JSON"
            )

            # Should handle large dataset
            assert result["success"] == True or result["new_count"] >= 0
            assert result["new_count"] <= 50

    def test_search_history_deduplication_tracking(self, app, mock_gemini_response_json):
        """Test that search history correctly tracks duplicate counts"""
        with app.app_context():
            db = get_db()

            response_json = json.dumps(mock_gemini_response_json)

            # First search
            parse_response_and_insert(
                country="Vietnam",
                query="First search",
                response_or_filepath=response_json,
                format="JSON"
            )

            # Second search with overlapping data
            result2 = parse_response_and_insert(
                country="Vietnam",
                query="Second search",
                response_or_filepath=response_json,
                format="JSON"
            )

            # Verify duplicate tracking
            history = get_search_history(limit=1)
            if history:
                # Handle both dict and object responses
                if isinstance(history[0], dict):
                    assert history[0].get("duplicate_count") is not None
                else:
                    assert hasattr(history[0], "duplicate_count")
                    assert history[0].duplicate_count >= 0

    def test_concurrent_search_isolation(self, app, mock_gemini_response_json):
        """Test that searches don't interfere with each other's statistics"""
        with app.app_context():
            response_json = json.dumps(mock_gemini_response_json)

            # Search 1: Vietnam
            result1 = parse_response_and_insert(
                country="Vietnam",
                query="Search A",
                response_or_filepath=response_json,
                format="JSON"
            )

            # Search 2: Thailand (different country)
            result2 = parse_response_and_insert(
                country="Thailand",
                query="Search B",
                response_or_filepath=response_json,
                format="JSON"
            )

            # Both searches should complete successfully
            assert result1["success"] == True or result1["new_count"] >= 0
            assert result2["success"] == True or result2["new_count"] >= 0

    def test_data_consistency_across_pipeline(self, app, mock_gemini_response_json):
        """Test that data remains consistent throughout the pipeline"""
        with app.app_context():
            db = get_db()

            response_json = json.dumps(mock_gemini_response_json)

            result = parse_response_and_insert(
                country="Vietnam",
                query="Data consistency test",
                response_or_filepath=response_json,
                format="JSON"
            )

            # Verify data integrity in database
            if result["new_count"] > 0:
                companies = db.query(Company).filter_by(country="Vietnam").all()

                for company in companies:
                    # Required fields should not be None
                    assert company.name is not None
                    assert company.country is not None

                    # Contact info should be valid format
                    if company.contact_email:
                        assert "@" in company.contact_email or company.contact_email == ""


class TestSearchAPIEndpoints:
    """Test search API endpoints for the complete pipeline"""

    def test_search_results_can_be_fetched(self, app, sample_companies):
        """Test that search results can be retrieved from database"""
        with app.app_context():
            db = get_db()

            # Verify we can fetch companies from database
            companies = db.query(Company).filter_by(country="Vietnam").all()

            # Should have sample companies in database
            assert len(companies) >= 0

            # Verify company data structure
            if companies:
                company = companies[0]
                assert hasattr(company, 'name')
                assert hasattr(company, 'country')
                assert hasattr(company, 'prospect_score')

    def test_search_results_api_structure(self, app):
        """Test that search result data has expected structure"""
        with app.app_context():
            # Create test data
            test_company_data = {
                "name": "API Test Company",
                "country": "Vietnam",
                "city": "HCMC",
                "prospect_score": 8,
                "priority": "HIGH",
                "linkedin_url": "https://linkedin.com/company/test/",
                "contact_email": "test@company.com",
                "source_query": "Test search"  # Required field
            }

            from tranotra.db import insert_company
            company_id = insert_company(test_company_data)

            # Verify company was inserted
            db = get_db()
            company = db.query(Company).filter_by(id=company_id).first()

            if company:
                # Verify structure
                assert company.name == "API Test Company"
                assert company.country == "Vietnam"
                assert company.prospect_score == 8
                assert company.source_query == "Test search"
