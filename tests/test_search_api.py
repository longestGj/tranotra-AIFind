"""Tests for search API endpoint"""

import json
import pytest
from unittest.mock import patch, MagicMock


class TestSearchAPI:
    """Test POST /api/search endpoint"""

    def test_search_api_with_valid_data(self, client, mocker):
        """Test search API with valid country and keyword"""
        # Mock Gemini response
        mock_response = '[{"name": "Company A", "country": "Vietnam"}]'
        mocker.patch(
            "tranotra.routes.initialize_gemini",
            return_value=True
        )
        mocker.patch(
            "tranotra.routes.call_gemini_grounding_search",
            return_value=mock_response
        )

        response = client.post(
            "/api/search/",
            data={"country": "Vietnam", "keyword": "PVC manufacturer"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

    def test_search_api_missing_country(self, client):
        """Test search API without country field"""
        response = client.post(
            "/api/search/",
            data={"keyword": "PVC manufacturer"},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_search_api_missing_keyword(self, client):
        """Test search API without keyword field"""
        response = client.post(
            "/api/search/",
            data={"country": "Vietnam"},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_search_api_missing_api_key(self, client, mocker):
        """Test search API when Gemini API key is missing"""
        mocker.patch(
            "tranotra.routes.initialize_gemini",
            return_value=False
        )

        response = client.post(
            "/api/search/",
            data={"country": "Vietnam", "keyword": "PVC manufacturer"},
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "API" in data.get("message", "")

    def test_search_api_timeout(self, client, mocker):
        """Test search API timeout handling"""
        from tranotra.core.exceptions import GeminiTimeoutError

        mocker.patch(
            "tranotra.routes.initialize_gemini",
            return_value=True
        )
        mocker.patch(
            "tranotra.routes.call_gemini_grounding_search",
            side_effect=GeminiTimeoutError("Timeout")
        )

        response = client.post(
            "/api/search/",
            data={"country": "Vietnam", "keyword": "PVC manufacturer"},
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data["status"] == "timeout"
        msg = data.get("message", "")
        assert "超时".encode().decode('utf-8', errors='ignore') in msg or "timeout" in msg.lower()

    def test_search_api_format_detection_json(self, client, mocker):
        """Test search API with JSON format detection"""
        mock_response = '[{"name": "Company A", "country": "Vietnam", "linkedin_url": "https://linkedin.com/company/a/", "prospect_score": 8}]'
        mocker.patch(
            "tranotra.routes.initialize_gemini",
            return_value=True
        )
        mocker.patch(
            "tranotra.routes.call_gemini_grounding_search",
            return_value=mock_response
        )

        response = client.post(
            "/api/search/",
            data={"country": "Vietnam", "keyword": "PVC"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["format"] == "JSON"

    def test_search_api_format_detection_invalid(self, client, mocker):
        """Test search API with invalid format"""
        mock_response = "This is plain text without structure"
        mocker.patch(
            "tranotra.routes.initialize_gemini",
            return_value=True
        )
        mocker.patch(
            "tranotra.routes.call_gemini_grounding_search",
            return_value=mock_response
        )

        response = client.post(
            "/api/search/",
            data={"country": "Vietnam", "keyword": "PVC"},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        msg = data.get("message", "")
        assert "格式".encode().decode('utf-8', errors='ignore') in msg or "format" in msg.lower()
