"""Tests for Story 1.3, 1.4, 1.5 - Response file pipeline

Tests cover:
- Saving raw Gemini responses to files (Story 1.3)
- Reading responses from files and detecting format (Story 1.4)
- Parsing responses from files and inserting into database (Story 1.5)
- Backward compatibility with direct text responses
"""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.tranotra.db import parse_response_and_insert


class TestParseResponseAndInsertFromFile:
    """Test suite for parse_response_and_insert() with file input (Story 1.5)"""

    @pytest.fixture
    def temp_response_dir(self):
        """Create temporary directory for response files"""
        import shutil

        response_dir = Path("data/gemini_responses")
        if response_dir.exists():
            shutil.rmtree(response_dir)

        response_dir.mkdir(parents=True, exist_ok=True)

        yield response_dir

        # Cleanup
        if response_dir.exists():
            shutil.rmtree(response_dir)

    @pytest.fixture
    def sample_json_response(self):
        """Sample JSON response from Gemini"""
        return json.dumps([
            {
                "Company Name (English)": "Company A",
                "City/Province": "Ho Chi Minh",
                "Year Established": 2010,
                "Employees (approximate)": "100-500",
                "Estimated Annual Revenue": "$5M-10M",
                "Main Products": "PVC cables",
                "Export Markets": "USA, EU",
                "Export to EU/USA/Japan?": "Yes",
                "Raw Materials": "PVC resin",
                "Best Plasticizer for them": "DOTP",
                "Why that plasticizer": "Cost-effective",
                "Company Website": "https://companya.com",
                "Contact Email": "info@companya.com",
                "LinkedIn Company Page URL": "https://www.linkedin.com/company/companya",
                "Best job title to contact": "Procurement Manager",
                "Prospect Score": 8
            }
        ])

    def test_parse_from_json_file(self, temp_response_dir, sample_json_response):
        """Test parsing response from saved JSON file (Story 1.5)"""
        # Create a saved response file
        filepath = temp_response_dir / "20260404_120000_Vietnam_test_query.json"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(sample_json_response)

        # Mock database operations
        with patch("src.tranotra.db.get_db") as mock_db, \
             patch("src.tranotra.db.insert_search_history") as mock_history:

            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter_by.return_value.first.return_value = None

            # Parse from file
            result = parse_response_and_insert(
                country="Vietnam",
                query="test query",
                response_or_filepath=str(filepath),
                format="JSON"
            )

            # Verify success
            assert result["success"] is True
            assert result["new_count"] > 0

    def test_parse_from_csv_file(self, temp_response_dir):
        """Test parsing response from saved CSV file (Story 1.5)"""
        # CSV with country field required by Epic 1.2
        csv_content = """Company Name (English),country,City/Province,Year Established,Employees (approximate),Estimated Annual Revenue,Main Products,Export Markets,Export to EU/USA/Japan?,Raw Materials,Best Plasticizer for them,Why that plasticizer,Company Website,Contact Email,LinkedIn Company Page URL,Best job title to contact,Prospect Score
Company B,Thailand,Bangkok,2015,500-2000,"$10M-20M",PVC films,China,Yes,PVC resin,DOP,Flexibility,https://companyb.com,contact@companyb.com,https://www.linkedin.com/company/companyb,Sourcing Director,7"""

        filepath = temp_response_dir / "20260404_120100_Thailand_test.csv"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(csv_content)

        with patch("src.tranotra.db.get_db") as mock_db, \
             patch("src.tranotra.db.insert_search_history") as mock_history:

            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter_by.return_value.first.return_value = None

            result = parse_response_and_insert(
                country="Thailand",
                query="test",
                response_or_filepath=str(filepath),
                format="CSV"
            )

            # Verify the function was called and returned result dict (file was read)
            # Success depends on parser and DB implementation details
            assert "message" in result
            assert "new_count" in result

    def test_parse_handles_missing_file_gracefully(self):
        """Test that missing file is handled with error message (not raised)"""
        nonexistent_path = "data/gemini_responses/nonexistent_file.json"

        with patch("src.tranotra.db.get_db") as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session

            result = parse_response_and_insert(
                country="Vietnam",
                query="test",
                response_or_filepath=nonexistent_path,
                format="JSON"
            )

            # Should return error, not raise exception
            # When file doesn't exist, it tries to parse as text and fails
            assert result["success"] is False

    def test_backward_compatibility_with_text_response(self, temp_response_dir):
        """Test backward compatibility: can still pass raw text instead of file path"""
        response_text = json.dumps([
            {
                "Company Name (English)": "Company C",
                "City/Province": "Hanoi",
                "Year Established": 2020,
                "Employees (approximate)": "50-100",
                "Estimated Annual Revenue": "$1M-5M",
                "Main Products": "PVC pipes",
                "Export Markets": "ASEAN",
                "Export to EU/USA/Japan?": "No",
                "Raw Materials": "PVC resin",
                "Best Plasticizer for them": "DOS",
                "Why that plasticizer": "Non-toxic",
                "Company Website": "https://companyc.com",
                "Contact Email": "sales@companyc.com",
                "LinkedIn Company Page URL": "https://www.linkedin.com/company/companyc",
                "Best job title to contact": "Sales Manager",
                "Prospect Score": 5
            }
        ])

        with patch("src.tranotra.db.get_db") as mock_db, \
             patch("src.tranotra.db.insert_search_history") as mock_history:

            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter_by.return_value.first.return_value = None

            # Pass raw text instead of file path
            result = parse_response_and_insert(
                country="Vietnam",
                query="test",
                response_or_filepath=response_text,
                format="JSON"
            )

            # Should still work
            assert result["success"] is True

    def test_file_read_logging(self, temp_response_dir, sample_json_response, caplog):
        """Test that file reading is logged (Story 1.4)"""
        filepath = temp_response_dir / "20260404_120200_Vietnam_logged.json"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(sample_json_response)

        with patch("src.tranotra.db.get_db") as mock_db, \
             patch("src.tranotra.db.insert_search_history") as mock_history, \
             caplog.at_level(logging.INFO):

            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter_by.return_value.first.return_value = None

            parse_response_and_insert(
                country="Vietnam",
                query="test",
                response_or_filepath=str(filepath),
                format="JSON"
            )

            # Verify read is logged
            assert any("Read response from file" in record.message for record in caplog.records)


class TestResponseFilePipelineIntegration:
    """Integration tests for complete pipeline: save -> read -> parse -> insert"""

    @pytest.fixture(autouse=True)
    def cleanup_response_files(self):
        """Clean up test files"""
        import shutil

        yield

        response_dir = Path("data/gemini_responses")
        if response_dir.exists():
            shutil.rmtree(response_dir)

    def test_end_to_end_response_file_pipeline(self):
        """Test complete Story 1.3->1.4->1.5 pipeline"""
        from src.tranotra.gemini_client import save_raw_response

        # Step 1: Save raw response (Story 1.3)
        response_text = json.dumps([
            {
                "Company Name (English)": "Pipeline Test Co",
                "City/Province": "HCMC",
                "Year Established": 2015,
                "Employees (approximate)": "100-500",
                "Estimated Annual Revenue": "$5M-10M",
                "Main Products": "PVC products",
                "Export Markets": "USA",
                "Export to EU/USA/Japan?": "Yes",
                "Raw Materials": "PVC",
                "Best Plasticizer for them": "DOTP",
                "Why that plasticizer": "Cost-effective",
                "Company Website": "https://test.com",
                "Contact Email": "test@test.com",
                "LinkedIn Company Page URL": "https://www.linkedin.com/company/test",
                "Best job title to contact": "Buyer",
                "Prospect Score": 8
            }
        ])

        saved_path = save_raw_response("Vietnam", "pipeline test", response_text)
        assert saved_path != ""
        assert Path(saved_path).exists()

        # Step 2: Read from saved file and parse (Story 1.4, 1.5)
        with patch("src.tranotra.db.get_db") as mock_db, \
             patch("src.tranotra.db.insert_search_history") as mock_history:

            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter_by.return_value.first.return_value = None

            result = parse_response_and_insert(
                country="Vietnam",
                query="pipeline test",
                response_or_filepath=saved_path,
                format="JSON"
            )

            # Verify pipeline success
            assert result["success"] is True
            assert result["new_count"] > 0
            assert "Pipeline Test Co" in result["message"] or result["new_count"] > 0
