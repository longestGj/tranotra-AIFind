"""Tests for Gemini API client wrapper

Tests cover:
- Client initialization with valid/invalid API keys
- Grounding search API calls with mocked responses
- Timeout and retry logic
- Error handling and custom exceptions
- API key redaction in logs
"""

import logging
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
    initialize_gemini,
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
