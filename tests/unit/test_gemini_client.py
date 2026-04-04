"""Tests for Gemini API client wrapper

Tests cover:
- Client initialization with valid/invalid API keys
- Grounding search API calls with mocked responses
- Timeout and retry logic
- Error handling and custom exceptions
- API key redaction in logs
"""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.tranotra.core.exceptions import (
    GeminiError,
    GeminiRateLimitError,
    GeminiTimeoutError,
)
from src.tranotra.gemini_client import (
    _redact_api_key,
    call_gemini_grounding_search,
    get_last_saved_response_path,
    initialize_gemini,
    save_raw_response,
)


class TestInitializeGemini:
    """Test suite for initialize_gemini() function"""

    def test_initialize_with_valid_api_key(self):
        """Test initialization with valid API key"""
        with patch("src.tranotra.gemini_client.genai") as mock_genai:
            mock_genai.GenerativeModel = MagicMock()
            result = initialize_gemini("sk_test_api_key_12345678901234567890")
            assert result is True
            mock_genai.configure.assert_called_once_with(api_key="sk_test_api_key_12345678901234567890")

    def test_initialize_with_empty_api_key(self):
        """Test initialization with empty API key raises ValueError"""
        with pytest.raises(ValueError, match="未找到 GEMINI_API_KEY"):
            initialize_gemini("")

    def test_initialize_with_none_api_key(self):
        """Test initialization with None API key raises ValueError"""
        with pytest.raises(ValueError, match="未找到 GEMINI_API_KEY"):
            initialize_gemini(None)

    def test_initialize_with_whitespace_api_key(self):
        """Test initialization with whitespace-only API key raises ValueError"""
        with pytest.raises(ValueError, match="未找到 GEMINI_API_KEY"):
            initialize_gemini("   ")

    def test_initialize_logs_api_key_redaction(self, caplog):
        """Test that API key is redacted in logs (only prefix shown)"""
        with patch("src.tranotra.gemini_client.genai") as mock_genai:
            mock_genai.GenerativeModel = MagicMock()
            with caplog.at_level(logging.INFO):
                initialize_gemini("sk_test1234567890abcdef")

            # Verify redacted key in log (should be "sk_te...***" - first 5 chars)
            assert any(
                "...***" in record.message for record in caplog.records
            ), f"Redacted key not found in logs: {[r.message for r in caplog.records]}"


class TestRedactApiKey:
    """Test suite for _redact_api_key() utility function"""

    def test_redact_long_api_key(self):
        """Test redaction of long API key"""
        result = _redact_api_key("sk_test1234567890abcdef")
        assert result == "sk_te...***"

    def test_redact_short_api_key(self):
        """Test redaction of short API key (< 5 chars)"""
        result = _redact_api_key("abc")
        assert result == "***"

    def test_redact_empty_api_key(self):
        """Test redaction of empty API key"""
        result = _redact_api_key("")
        assert result == "***"


class TestCallGeminiGroundingSearch:
    """Test suite for call_gemini_grounding_search() function"""

    @pytest.fixture
    def mock_gemini_client(self):
        """Fixture to mock the global _gemini_client"""
        import src.tranotra.gemini_client as gc

        mock_client = MagicMock()
        original_client = gc._gemini_client
        gc._gemini_client = mock_client

        yield mock_client

        # Cleanup: restore original client
        gc._gemini_client = original_client

    def test_search_returns_raw_response(self, mock_gemini_client):
        """Test that search returns raw response unchanged"""
        sample_response = '{"companies": [{"name": "Company A", "country": "Vietnam"}]}'

        mock_response = MagicMock()
        mock_response.text = sample_response
        mock_gemini_client.generate_content.return_value = mock_response

        result = call_gemini_grounding_search(country="Vietnam", query="PVC manufacturer")

        assert result == sample_response
        assert result.startswith("{")  # Raw JSON preserved

    def test_search_does_not_parse_response(self, mock_gemini_client):
        """Test that search does NOT parse or validate response"""
        # Return malformed JSON to verify no parsing happens
        malformed_json = '{"broken json": [1, 2'

        mock_response = MagicMock()
        mock_response.text = malformed_json
        mock_gemini_client.generate_content.return_value = mock_response

        result = call_gemini_grounding_search(country="Vietnam", query="test")

        # Should return raw response without parsing
        assert result == malformed_json

    def test_search_with_timeout(self, mock_gemini_client):
        """Test that search respects timeout and retries"""
        # Simulate timeout on all attempts
        mock_gemini_client.generate_content.side_effect = TimeoutError("Request timed out")

        with pytest.raises(GeminiTimeoutError, match="搜索超时"):
            call_gemini_grounding_search(
                country="Vietnam",
                query="test",
                timeout=30,
                max_retries=3,
            )

    def test_search_retry_success_on_third_attempt(self, mock_gemini_client):
        """Test that search succeeds on 3rd retry attempt"""
        # First 2 attempts fail with timeout, 3rd succeeds
        mock_response = MagicMock()
        mock_response.text = '{"companies": []}'
        mock_gemini_client.generate_content.side_effect = [
            TimeoutError("Timeout 1"),
            TimeoutError("Timeout 2"),
            mock_response,
        ]

        with patch("src.tranotra.gemini_client.time.sleep"):
            result = call_gemini_grounding_search(
                country="Vietnam",
                query="test",
                timeout=30,
                max_retries=3,
            )

        assert result == '{"companies": []}'

    def test_search_rate_limit_error(self, mock_gemini_client):
        """Test that rate limit errors are handled correctly"""
        mock_gemini_client.generate_content.side_effect = Exception("429 Quota exceeded")

        with patch("src.tranotra.gemini_client.time.sleep"):
            with pytest.raises(GeminiRateLimitError, match="配额"):
                call_gemini_grounding_search(
                    country="Vietnam",
                    query="test",
                    max_retries=1,
                )

    def test_search_not_initialized_raises_error(self):
        """Test that calling search without initialization raises error"""
        # Reset the global client
        import src.tranotra.gemini_client as gc

        original_client = gc._gemini_client
        gc._gemini_client = None

        try:
            with pytest.raises(GeminiError, match="not initialized"):
                call_gemini_grounding_search(country="Vietnam", query="test")
        finally:
            gc._gemini_client = original_client


class TestSaveRawResponse:
    """Test suite for save_raw_response() function (Story 1.3)"""

    @pytest.fixture(autouse=True)
    def cleanup_response_files(self):
        """Clean up saved response files after each test"""
        import shutil
        from pathlib import Path

        yield

        # Cleanup
        response_dir = Path("data/gemini_responses")
        if response_dir.exists():
            shutil.rmtree(response_dir, ignore_errors=True)

    def test_save_raw_response_creates_directory(self):
        """Test that save_raw_response creates data/gemini_responses directory"""
        from pathlib import Path

        response_dir = Path("data/gemini_responses")
        if response_dir.exists():
            import shutil
            shutil.rmtree(response_dir)

        response_text = '{"companies": [{"name": "Test Co"}]}'
        filepath = save_raw_response("Vietnam", "PVC manufacturer", response_text)

        assert filepath != ""
        assert Path(filepath).exists()
        response_dir = Path("data/gemini_responses")
        assert response_dir.exists()

    def test_save_raw_response_creates_file_with_correct_content(self):
        """Test that response content is correctly written to file"""
        response_text = '{"companies": [{"name": "Company A", "country": "Vietnam"}]}'
        filepath = save_raw_response("Vietnam", "cable manufacturer", response_text)

        assert Path(filepath).exists()
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert content == response_text
        assert "Company A" in content

    def test_save_raw_response_filename_format(self):
        """Test that filename follows format: {timestamp}_{country}_{query}.json"""
        response_text = "test response"
        filepath = save_raw_response("Vietnam", "PVC manufacturer", response_text)

        filename = Path(filepath).name
        # Format: {YYYYMMDD_HHMMSS}_{country}_{query}.json
        # Example: 20260404_120530_Vietnam_PVC_manufactur.json
        assert filename.startswith("202")  # Start of year 2026
        assert "_Vietnam_" in filename
        assert filename.endswith(".json")

    def test_save_raw_response_sanitizes_query(self):
        """Test that query is sanitized (spaces -> underscores, max 30 chars)"""
        response_text = "test"
        filepath = save_raw_response("Vietnam", "very long query with many spaces here", response_text)

        filename = Path(filepath).name
        # Query should have spaces replaced with underscores and be truncated
        assert "very_long_query_with_many_sp" in filename

    def test_save_raw_response_returns_filepath_as_string(self):
        """Test that function returns filepath as string"""
        response_text = "test"
        filepath = save_raw_response("Vietnam", "test query", response_text)

        assert isinstance(filepath, str)
        assert len(filepath) > 0
        assert filepath.endswith(".json")

    def test_save_raw_response_error_handling(self, caplog):
        """Test that errors are raised (not silent)"""
        # Try to save with invalid path that can't be created
        with patch("pathlib.Path.mkdir", side_effect=PermissionError("Permission denied")):
            with caplog.at_level(logging.ERROR):
                with pytest.raises(GeminiError, match="Failed to save raw response"):
                    save_raw_response("Vietnam", "test", "response")

            assert any("Failed to save raw response" in record.message for record in caplog.records)

    def test_save_raw_response_special_characters_sanitized(self):
        """Test that special characters are sanitized from query"""
        from pathlib import Path

        # Query with illegal Windows filename characters
        response_text = "test"
        filepath = save_raw_response("Vietnam", "PVC<>:|?*\\/test", response_text)

        # Extract filename from path
        filename = Path(filepath).name
        # Should not contain illegal characters
        assert '<' not in filename
        assert '>' not in filename
        assert ':' not in filename
        assert '|' not in filename
        assert '?' not in filename
        assert '*' not in filename
        assert '\\' not in filename
        assert '/' not in filename

    def test_save_raw_response_file_verification(self):
        """Test that file write is verified before returning path"""
        response_text = "test response content"
        saved_path = save_raw_response("Vietnam", "test query", response_text)

        # Verify file actually exists and has content
        assert Path(saved_path).exists()
        with open(saved_path, "r") as f:
            content = f.read()
        assert content == response_text


class TestGetLastSavedResponsePath:
    """Test suite for get_last_saved_response_path() function (Story 1.3)"""

    @pytest.fixture(autouse=True)
    def reset_global_path(self):
        """Reset global path tracker before and after each test"""
        import src.tranotra.gemini_client as gc

        original_path = gc._last_saved_response_path
        gc._last_saved_response_path = ""

        yield

        # Cleanup
        import shutil
        from pathlib import Path

        response_dir = Path("data/gemini_responses")
        if response_dir.exists():
            shutil.rmtree(response_dir, ignore_errors=True)

        gc._last_saved_response_path = original_path

    def test_get_last_saved_response_path_returns_empty_initially(self):
        """Test that function returns empty string before any save"""
        import src.tranotra.gemini_client as gc
        gc._last_saved_response_path = ""

        path = get_last_saved_response_path()
        assert path == ""

    def test_get_last_saved_response_path_returns_saved_path(self):
        """Test that function returns path after save_raw_response is called"""
        response_text = "test response"
        saved_path = save_raw_response("Vietnam", "test query", response_text)

        retrieved_path = get_last_saved_response_path()
        assert retrieved_path == saved_path
        assert retrieved_path != ""

    def test_concurrent_saves_thread_safe(self):
        """Test that concurrent saves don't create race conditions"""
        import threading

        results = []

        def save_in_thread(country, query, index):
            response_text = f"response_{index}"
            path = save_raw_response(country, query, response_text)
            results.append((index, path))

        threads = [
            threading.Thread(target=save_in_thread, args=(f"Country{i}", f"Query{i}", i))
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All saves should complete without error
        assert len(results) == 5
        # All paths should be unique
        paths = [r[1] for r in results]
        assert len(set(paths)) == 5, "Concurrent saves should create unique files"


class TestIntegration:
    """Integration tests for full workflow"""

    def test_config_to_initialize_to_search_flow(self):
        """Test end-to-end flow from config loading to API call"""
        with patch("src.tranotra.gemini_client.genai") as mock_genai:
            # Mock Gemini API
            mock_response = MagicMock()
            mock_response.text = '{"companies": [{"name": "Test Co"}]}'
            mock_instance = MagicMock()
            mock_instance.generate_content.return_value = mock_response
            mock_genai.GenerativeModel.return_value = mock_instance

            # Initialize with valid-length API key
            result = initialize_gemini("sk_test_api_key_12345678901234567890")
            assert result is True

            # Call search
            response = call_gemini_grounding_search(country="Vietnam", query="manufacturer")
            assert '{"companies"' in response

    def test_search_auto_saves_response_to_file(self):
        """Test that call_gemini_grounding_search automatically saves response (Story 1.3)"""
        import shutil
        from pathlib import Path

        # Cleanup before test
        response_dir = Path("data/gemini_responses")
        if response_dir.exists():
            shutil.rmtree(response_dir)

        try:
            with patch("src.tranotra.gemini_client.genai") as mock_genai:
                # Mock Gemini API
                test_response_text = '{"companies": [{"name": "TestCo", "country": "Vietnam"}]}'
                mock_response = MagicMock()
                mock_response.text = test_response_text
                mock_instance = MagicMock()
                mock_instance.generate_content.return_value = mock_response
                mock_genai.GenerativeModel.return_value = mock_instance

                # Initialize
                initialize_gemini("sk_test_api_key_12345678901234567890")

                # Call search
                result = call_gemini_grounding_search(country="Vietnam", query="test")

                # Verify response returned
                assert result == test_response_text

                # Verify file was saved
                saved_path = get_last_saved_response_path()
                assert saved_path != ""
                assert Path(saved_path).exists()

                # Verify file content
                with open(saved_path, "r", encoding="utf-8") as f:
                    saved_content = f.read()
                assert saved_content == test_response_text
        finally:
            # Cleanup
            response_dir = Path("data/gemini_responses")
            if response_dir.exists():
                shutil.rmtree(response_dir)
