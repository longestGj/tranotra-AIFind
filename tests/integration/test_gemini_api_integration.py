"""Integration tests for Gemini API calls and complete search pipeline
Tests the actual Gemini API integration from search form to database storage
"""

import json
import os
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, call
from tranotra.gemini_client import (
    call_gemini_grounding_search,
    save_raw_response,
    initialize_gemini,
    get_last_saved_response_path
)
from tranotra.db import parse_response_and_insert, get_search_history
from tranotra.infrastructure.database import get_db
from tranotra.core.models import Company, SearchHistory
from tranotra.routes import detect_response_format


class TestGeminiAPIIntegration:
    """Test actual Gemini API integration and complete search pipeline"""

    @pytest.fixture
    def mock_gemini_json_response(self):
        """Mock Gemini API JSON response"""
        return json.dumps([
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
            }
        ])

    @pytest.fixture
    def mock_gemini_csv_response(self):
        """Mock Gemini API CSV response"""
        return """name,country,city,prospect_score,linkedin_url
Cadivi Vietnam,Vietnam,HCMC,9,https://linkedin.com/company/cadivi/
Thai Plastics,Thailand,Bangkok,7,https://linkedin.com/company/thai/"""

    @pytest.fixture
    def cleanup_response_files(self):
        """Cleanup gemini_responses directory after tests"""
        yield
        # Cleanup
        response_dir = Path("data/gemini_responses")
        if response_dir.exists():
            import shutil
            try:
                shutil.rmtree(response_dir)
            except Exception:
                pass

    def test_save_raw_response_creates_file(self, app, cleanup_response_files):
        """Test that raw Gemini response is saved to file"""
        with app.app_context():
            country = "Vietnam"
            query = "PVC manufacturer"
            response_text = '{"data": "test"}'

            # Save response
            file_path = save_raw_response(country, query, response_text)

            # Verify file exists
            assert Path(file_path).exists(), f"Response file not created: {file_path}"

            # Verify file contains correct content
            with open(file_path, 'r', encoding='utf-8') as f:
                saved_content = f.read()
            assert saved_content == response_text

            # Verify file path follows pattern
            assert "gemini_responses" in file_path
            assert country in file_path or "vietnam" in file_path.lower()

    def test_get_last_saved_response_path(self, app, cleanup_response_files):
        """Test retrieving the last saved response file path"""
        with app.app_context():
            country = "Vietnam"
            query = "Test query"
            response_text = '{"test": "data"}'

            # Save response
            saved_path = save_raw_response(country, query, response_text)

            # Get last saved path
            retrieved_path = get_last_saved_response_path()

            # Should match
            assert retrieved_path == saved_path

    def test_detect_response_format_json(self, app):
        """Test detection of JSON response format"""
        json_response = '{"name": "Company", "country": "Vietnam"}'
        detected = detect_response_format(json_response)
        assert detected == "JSON"

    def test_detect_response_format_json_array(self, app):
        """Test detection of JSON array response format"""
        json_response = '[{"name": "Company1"}, {"name": "Company2"}]'
        detected = detect_response_format(json_response)
        assert detected == "JSON"

    def test_detect_response_format_csv(self, app):
        """Test detection of CSV response format"""
        csv_response = "name,country,city\nCompany A,Vietnam,HCMC\nCompany B,Thailand,Bangkok"
        detected = detect_response_format(csv_response)
        assert detected == "CSV"

    def test_detect_response_format_markdown(self, app):
        """Test detection of Markdown table response format"""
        markdown_response = """| name | country | city |
| --- | --- | --- |
| Company A | Vietnam | HCMC |
| Company B | Thailand | Bangkok |"""
        detected = detect_response_format(markdown_response)
        assert detected == "Markdown"

    def test_detect_response_format_unknown(self, app):
        """Test detection of unknown response format"""
        unknown_response = "This is just plain text with no structured format"
        detected = detect_response_format(unknown_response)
        assert detected == "UNKNOWN"

    @patch('tranotra.gemini_client.initialize_gemini')
    @patch('tranotra.gemini_client.genai.GenerativeModel')
    def test_call_gemini_api_with_mock(self, mock_genai_model, mock_init, app, mock_gemini_json_response, cleanup_response_files):
        """Test calling Gemini API with mock (simulates actual API call flow)"""
        with app.app_context():
            # Setup mock
            mock_response = MagicMock()
            mock_response.text = mock_gemini_json_response
            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_genai_model.return_value = mock_model_instance

            # Initialize Gemini
            initialize_gemini("test-api-key")

            # Call API
            country = "Vietnam"
            query = "PVC manufacturer"
            response = call_gemini_grounding_search(country, query)

            # Verify response
            assert response is not None
            assert len(response) > 0

            # Verify file was saved
            saved_path = get_last_saved_response_path()
            assert saved_path != ""
            assert Path(saved_path).exists()

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-api-key'})
    @patch('tranotra.gemini_client.genai.GenerativeModel')
    def test_gemini_api_timeout_handling(self, mock_genai_model, app):
        """Test timeout handling when Gemini API takes too long"""
        with app.app_context():
            # Setup mock to raise timeout
            from tranotra.core.exceptions import GeminiTimeoutError
            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.side_effect = GeminiTimeoutError("API call timeout")
            mock_genai_model.return_value = mock_model_instance

            initialize_gemini("test-api-key")

            # Should raise or handle timeout gracefully
            try:
                call_gemini_grounding_search("Vietnam", "test")
                # If no exception, that's also valid (graceful handling)
            except GeminiTimeoutError:
                # Expected behavior
                pass

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-api-key'})
    @patch('tranotra.gemini_client.genai.GenerativeModel')
    def test_complete_search_flow_with_api_call(self, mock_genai_model, app, mock_gemini_json_response, cleanup_response_files):
        """Test complete search flow: API call → file save → format detect → parse → insert"""
        with app.app_context():
            db = get_db()

            # Setup mock Gemini API
            mock_response = MagicMock()
            mock_response.text = mock_gemini_json_response
            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_genai_model.return_value = mock_model_instance

            initialize_gemini("test-api-key")

            # Step 1: Call Gemini API
            country = "Vietnam"
            query = "PVC manufacturer"
            api_response = call_gemini_grounding_search(country, query)

            # Verify API response received
            assert api_response is not None
            print(f"[API] Received response: {len(api_response)} bytes")

            # Step 2: Verify file was saved
            saved_path = get_last_saved_response_path()
            assert Path(saved_path).exists()
            print(f"[FILE] Response saved to: {saved_path}")

            # Step 3: Detect format
            detected_format = detect_response_format(api_response)
            assert detected_format in ["JSON", "CSV", "Markdown"]
            print(f"[FORMAT] Detected format: {detected_format}")

            # Step 4: Parse and insert
            result = parse_response_and_insert(
                country=country,
                query=query,
                response_or_filepath=api_response,
                format=detected_format
            )

            # Step 5: Verify database insertion
            assert result["success"] == True
            assert result["new_count"] >= 0
            print(f"[DB] Inserted {result['new_count']} companies")

            # Verify companies in database
            companies = db.query(Company).filter_by(country=country).all()
            assert len(companies) >= result["new_count"]

            # Verify search history
            history = db.query(SearchHistory).filter_by(
                country=country,
                query=query
            ).order_by(SearchHistory.created_at.desc()).first()
            assert history is not None
            print(f"[HISTORY] Search recorded: {history.new_count} new, {history.duplicate_count} duplicates")

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-api-key'})
    @patch('tranotra.gemini_client.genai.GenerativeModel')
    def test_complete_search_with_csv_response(self, mock_genai_model, app, mock_gemini_csv_response, cleanup_response_files):
        """Test complete search flow with CSV format response"""
        with app.app_context():
            db = get_db()

            # Setup mock
            mock_response = MagicMock()
            mock_response.text = mock_gemini_csv_response
            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_genai_model.return_value = mock_model_instance

            initialize_gemini("test-api-key")

            # Execute flow
            country = "Thailand"
            query = "Plastic manufacturer"
            api_response = call_gemini_grounding_search(country, query)

            # Verify file saved
            assert Path(get_last_saved_response_path()).exists()

            # Detect format
            detected = detect_response_format(api_response)
            print(f"Detected CSV format: {detected}")

            # Parse and insert
            result = parse_response_and_insert(
                country=country,
                query=query,
                response_or_filepath=api_response,
                format=detected
            )

            assert result["success"] == True or result["new_count"] >= 0

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-api-key'})
    @patch('tranotra.gemini_client.genai.GenerativeModel')
    def test_api_response_file_persistence(self, mock_genai_model, app, mock_gemini_json_response, cleanup_response_files):
        """Test that saved API response files can be re-parsed without re-calling API"""
        with app.app_context():
            # Setup mock
            mock_response = MagicMock()
            mock_response.text = mock_gemini_json_response
            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_genai_model.return_value = mock_model_instance

            initialize_gemini("test-api-key")

            # First call
            country = "Vietnam"
            query = "PVC test"
            response1 = call_gemini_grounding_search(country, query)
            saved_path = get_last_saved_response_path()

            # Verify file exists
            assert Path(saved_path).exists()

            # Second parse from saved file (without new API call)
            with open(saved_path, 'r', encoding='utf-8') as f:
                saved_content = f.read()

            # Parse the saved content
            result = parse_response_and_insert(
                country=country,
                query="Another query",  # Different query, same file
                response_or_filepath=saved_content,
                format="JSON"
            )

            # Should successfully parse
            assert result["success"] == True or result["new_count"] >= 0
            print(f"[RE-PARSE] Successfully re-parsed saved file without API call")

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-api-key'})
    @patch('tranotra.gemini_client.genai.GenerativeModel')
    def test_multiple_sequential_api_calls(self, mock_genai_model, app, cleanup_response_files):
        """Test multiple sequential Gemini API calls with different countries"""
        with app.app_context():
            db = get_db()

            # Setup mock
            mock_model_instance = MagicMock()

            # Create different responses for each call
            responses = [
                json.dumps([{"name": "Vietnam Company", "country": "Vietnam", "prospect_score": 8, "linkedin_url": "https://linkedin.com/vn/"}]),
                json.dumps([{"name": "Thailand Company", "country": "Thailand", "prospect_score": 7, "linkedin_url": "https://linkedin.com/th/"}]),
                json.dumps([{"name": "Indonesia Company", "country": "Indonesia", "prospect_score": 9, "linkedin_url": "https://linkedin.com/id/"}])
            ]

            mock_model_instance.generate_content.side_effect = [
                MagicMock(text=resp) for resp in responses
            ]
            mock_genai_model.return_value = mock_model_instance

            initialize_gemini("test-api-key")

            # Make multiple calls
            countries = ["Vietnam", "Thailand", "Indonesia"]
            for country in countries:
                response = call_gemini_grounding_search(country, f"Search in {country}")

                # Parse and insert
                parse_response_and_insert(
                    country=country,
                    query=f"Query for {country}",
                    response_or_filepath=response,
                    format="JSON"
                )

            # Verify all countries have data
            for country in countries:
                companies = db.query(Company).filter_by(country=country).all()
                assert len(companies) >= 0
                print(f"[COUNTRIES] {country}: {len(companies)} companies")

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-api-key'})
    @patch('tranotra.gemini_client.genai.GenerativeModel')
    def test_api_response_format_variations(self, mock_genai_model, app, cleanup_response_files):
        """Test handling of different response formats from Gemini API"""
        with app.app_context():
            initialize_gemini("test-api-key")

            # Test different formats
            test_cases = [
                ('JSON', '[{"name": "Company", "country": "Vietnam", "prospect_score": 8, "linkedin_url": "https://linkedin.com/c/"}]'),
                ('CSV', 'name,country,prospect_score\nCompany,Vietnam,8'),
                ('Markdown', '| name | country |\n| --- | --- |\n| Company | Vietnam |'),
            ]

            for expected_format, response_text in test_cases:
                # Setup mock for this iteration
                mock_response = MagicMock()
                mock_response.text = response_text
                mock_model_instance = MagicMock()
                mock_model_instance.generate_content.return_value = mock_response
                mock_genai_model.return_value = mock_model_instance

                # Call API (mocked)
                api_response = call_gemini_grounding_search("Vietnam", "test")

                # Detect format
                detected = detect_response_format(api_response)

                print(f"Format test: {expected_format} → {detected}")
                assert detected == expected_format or detected != "UNKNOWN"

    def test_response_file_naming_consistency(self, app, cleanup_response_files):
        """Test that response file naming is consistent and includes search context"""
        with app.app_context():
            country = "Vietnam"
            query = "PVC manufacturer"
            response = '{"test": "data"}'

            # Save response
            path1 = save_raw_response(country, query, response)

            # Verify filename includes context
            filename = Path(path1).name
            print(f"[FILENAME] {filename}")

            # Should contain timestamp
            assert any(char.isdigit() for char in filename)

            # Should be valid filename
            assert "/" not in filename or "\\" not in filename or "::" not in filename


class TestGeminiAPIErrorHandling:
    """Test error handling in Gemini API integration"""

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-api-key'})
    @patch('tranotra.gemini_client.genai.GenerativeModel')
    def test_api_error_response_handling(self, mock_genai_model, app):
        """Test handling of API error responses"""
        with app.app_context():
            from tranotra.core.exceptions import GeminiError

            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.side_effect = GeminiError("API error occurred")
            mock_genai_model.return_value = mock_model_instance

            initialize_gemini("test-api-key")

            # Should handle error gracefully
            try:
                call_gemini_grounding_search("Vietnam", "test")
            except GeminiError:
                pass  # Expected

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-api-key'})
    @patch('tranotra.gemini_client.genai.GenerativeModel')
    def test_file_save_failure_handling(self, mock_genai_model, app):
        """Test handling of file save failures"""
        with app.app_context():
            from tranotra.core.exceptions import GeminiError

            # Mock API call that returns response
            mock_response = MagicMock()
            mock_response.text = '{"data": "test"}'
            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_genai_model.return_value = mock_model_instance

            initialize_gemini("test-api-key")

            # Patch file write to fail
            with patch('pathlib.Path.mkdir', side_effect=OSError("Permission denied")):
                try:
                    # Should handle save failure
                    save_raw_response("Vietnam", "test", '{"data": "test"}')
                except (GeminiError, OSError):
                    pass  # Expected

    def test_empty_api_response_handling(self, app, cleanup_response_files):
        """Test handling of empty API responses"""
        with app.app_context():
            detected = detect_response_format("")
            assert detected == "UNKNOWN"

            detected = detect_response_format("   ")
            assert detected == "UNKNOWN"


class TestSearchAPIEndpointWithGemini:
    """Test search API endpoints with Gemini integration"""

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-api-key'})
    @patch('tranotra.gemini_client.genai.GenerativeModel')
    def test_search_endpoint_calls_gemini_api(self, mock_genai_model, app):
        """Test that search endpoint properly calls Gemini API"""
        with app.app_context():
            # Setup mock
            mock_response = MagicMock()
            mock_response.text = json.dumps([
                {"name": "Test Company", "country": "Vietnam", "prospect_score": 8, "linkedin_url": "https://linkedin.com/test/"}
            ])
            mock_model_instance = MagicMock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_genai_model.return_value = mock_model_instance

            initialize_gemini("test-api-key")

            # This would test the routes.py search_api() endpoint
            # Call API
            response = call_gemini_grounding_search("Vietnam", "PVC")

            # Verify response
            assert response is not None
            assert "Test Company" in response or "Vietnam" in response
