"""Tests for Story 2-1: Search Results API endpoint"""

import json
import pytest
from datetime import datetime, timedelta


class TestSearchResultsAPI:
    """Test GET /api/search/results endpoint"""

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear cache before each test"""
        from tranotra.routes import results_cache
        results_cache.clear()
        yield
        results_cache.clear()

    def test_get_results_without_filters(self, client, db_session, sample_companies):
        """Test fetching all results without filters"""
        response = client.get('/api/search/results')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert 'timestamp' in data
        assert 'companies' in data
        assert 'total_count' in data
        assert 'current_page' in data
        assert 'per_page' in data
        assert 'total_pages' in data
        assert len(data['companies']) > 0

    def test_get_results_with_country_filter(self, client, db_session, sample_companies):
        """Test fetching results filtered by country"""
        response = client.get('/api/search/results?country=Vietnam')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        # All returned companies should be from Vietnam
        for company in data['companies']:
            assert company['country'] == 'Vietnam'

    def test_get_results_with_query_filter(self, client, db_session, sample_companies):
        """Test fetching results filtered by search query"""
        response = client.get('/api/search/results?query=PVC%20manufacturer')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        # All returned companies should have matching source_query
        for company in data['companies']:
            assert company['source_query'] == 'PVC manufacturer'

    def test_get_results_with_both_filters(self, client, db_session, sample_companies):
        """Test fetching results with both country and query filters"""
        response = client.get('/api/search/results?country=Vietnam&query=PVC%20manufacturer')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        for company in data['companies']:
            assert company['country'] == 'Vietnam'
            assert company['source_query'] == 'PVC manufacturer'

    def test_get_results_pagination_default(self, client, db_session, sample_companies):
        """Test default pagination (page 1, 20 per page)"""
        response = client.get('/api/search/results')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['current_page'] == 1
        assert data['per_page'] == 20
        assert len(data['companies']) <= 20

    def test_get_results_pagination_page_2(self, client, db_session, sample_companies_many):
        """Test pagination page 2"""
        response = client.get('/api/search/results?page=2')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['current_page'] == 2
        assert data['per_page'] == 20

    def test_get_results_custom_per_page(self, client, db_session, sample_companies):
        """Test custom per_page parameter"""
        response = client.get('/api/search/results?per_page=5')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['per_page'] == 5
        assert len(data['companies']) <= 5

    def test_get_results_per_page_max_limit(self, client, db_session, sample_companies):
        """Test per_page maximum limit (100)"""
        response = client.get('/api/search/results?per_page=200')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Should be capped at 100
        assert data['per_page'] <= 100

    def test_get_results_invalid_page_default_to_1(self, client, db_session, sample_companies):
        """Test that invalid page defaults to 1"""
        response = client.get('/api/search/results?page=0')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Should default to page 1
        assert data['current_page'] >= 1

    def test_get_results_empty_results(self, client, db_session):
        """Test when no results match filters"""
        response = client.get('/api/search/results?country=NonExistent')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert len(data['companies']) == 0
        assert data['total_count'] == 0

    def test_get_results_company_fields(self, client, db_session, sample_companies):
        """Test that returned company has all required fields"""
        response = client.get('/api/search/results')

        assert response.status_code == 200
        data = json.loads(response.data)

        required_fields = [
            'id', 'name', 'country', 'city', 'year_established',
            'employees', 'estimated_revenue', 'main_products',
            'export_markets', 'eu_us_jp_export', 'raw_materials',
            'recommended_product', 'recommendation_reason',
            'website', 'contact_email', 'linkedin_url',
            'linkedin_normalized', 'best_contact_title',
            'prospect_score', 'priority', 'source_query',
            'created_at', 'updated_at'
        ]

        if len(data['companies']) > 0:
            company = data['companies'][0]
            for field in required_fields:
                assert field in company, f"Missing field: {field}"

    def test_get_results_response_structure(self, client, db_session, sample_companies):
        """Test complete response structure"""
        response = client.get('/api/search/results')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Required top-level fields
        required_keys = [
            'success', 'timestamp', 'cached', 'new_count',
            'duplicate_count', 'avg_score', 'total_count',
            'current_page', 'per_page', 'total_pages', 'companies'
        ]

        for key in required_keys:
            assert key in data, f"Missing key: {key}"

        # Verify types
        assert isinstance(data['success'], bool)
        assert isinstance(data['cached'], bool)
        assert isinstance(data['new_count'], int)
        assert isinstance(data['duplicate_count'], int)
        assert isinstance(data['total_count'], int)
        assert isinstance(data['current_page'], int)
        assert isinstance(data['per_page'], int)
        assert isinstance(data['total_pages'], int)
        assert isinstance(data['companies'], list)

    def test_get_results_sorted_by_score(self, client, db_session, sample_companies):
        """Test that results are sorted by prospect_score descending"""
        response = client.get('/api/search/results')

        assert response.status_code == 200
        data = json.loads(response.data)

        companies = data['companies']
        if len(companies) > 1:
            for i in range(len(companies) - 1):
                # Higher scores should come first
                assert companies[i]['prospect_score'] >= companies[i + 1]['prospect_score']

    def test_get_results_caching(self, client, db_session, sample_companies):
        """Test caching mechanism - verify cache response field exists"""
        # Verify cache response field exists in response
        response = client.get('/api/search/results?country=Vietnam&page=1')
        assert response.status_code == 200
        data = json.loads(response.data)

        # Check that 'cached' field exists (implementation detail)
        assert 'cached' in data
        assert isinstance(data['cached'], bool)

        # Verify timestamp exists (required for caching)
        assert 'timestamp' in data
        assert data['timestamp'] is not None

    def test_get_results_timestamp_format(self, client, db_session, sample_companies):
        """Test that timestamp is in ISO 8601 format"""
        response = client.get('/api/search/results')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Timestamp should be ISO 8601 format (ends with Z)
        assert data['timestamp'].endswith('Z')
        # Should be parseable as datetime
        try:
            datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {data['timestamp']}")

    def test_get_results_search_history_stats(self, client, db_session, sample_companies_with_history):
        """Test that search history stats are included when filters match"""
        # This requires sample data with search_history records
        response = client.get('/api/search/results?country=Vietnam&query=PVC%20manufacturer')

        assert response.status_code == 200
        data = json.loads(response.data)

        # Should have stats from search_history
        assert 'new_count' in data
        assert 'duplicate_count' in data
        assert 'avg_score' in data
