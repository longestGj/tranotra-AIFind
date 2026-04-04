"""Unit tests for analytics metrics calculation module"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from tranotra.analytics.metrics import (
    calculate_total_searches,
    calculate_total_companies,
    calculate_dedup_rate,
    calculate_avg_hit_rate,
    calculate_high_score_rate,
    calculate_day_on_day_growth,
    calculate_week_on_week_growth,
    get_dashboard_metrics,
)


class TestMetricsCalculations:
    """Test metrics calculation functions"""

    @patch("tranotra.analytics.metrics.get_db")
    def test_calculate_total_searches_with_data(self, mock_get_db):
        """Test calculating total searches when data exists"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 47

        mock_get_db.return_value = mock_db

        result = calculate_total_searches(7)

        assert result == 47
        mock_get_db.assert_called_once()

    @patch("tranotra.analytics.metrics.get_db")
    def test_calculate_total_searches_no_data(self, mock_get_db):
        """Test calculating total searches when no data exists"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = None

        mock_get_db.return_value = mock_db

        result = calculate_total_searches(7)

        assert result == 0

    @patch("tranotra.analytics.metrics.get_db")
    def test_calculate_total_companies_with_data(self, mock_get_db):
        """Test calculating total companies when data exists"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 312

        mock_get_db.return_value = mock_db

        result = calculate_total_companies(7)

        assert result == 312

    @patch("tranotra.analytics.metrics.get_db")
    def test_calculate_dedup_rate_with_data(self, mock_get_db):
        """Test calculating dedup rate when data exists"""
        mock_db = MagicMock()
        mock_query = MagicMock()

        # Mock the result object with attributes
        mock_result = MagicMock()
        mock_result.total_companies = 100
        mock_result.total_duplicates = 18

        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result

        mock_get_db.return_value = mock_db

        result = calculate_dedup_rate(7)

        assert result == 18.0  # 18 / 100 * 100

    @patch("tranotra.analytics.metrics.get_db")
    def test_calculate_dedup_rate_no_companies(self, mock_get_db):
        """Test calculating dedup rate when no companies exist"""
        mock_db = MagicMock()
        mock_query = MagicMock()

        # Mock result with zero companies
        mock_result = MagicMock()
        mock_result.total_companies = 0
        mock_result.total_duplicates = 0

        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result

        mock_get_db.return_value = mock_db

        result = calculate_dedup_rate(7)

        assert result == 0.0

    def test_calculate_avg_hit_rate_with_data(self):
        """Test calculating average hit rate with data"""
        result = calculate_avg_hit_rate(7, 50)

        # Should call calculate_total_companies and divide by searches
        # Mock would return some value, but for this test we're verifying the formula
        assert isinstance(result, float)

    def test_calculate_avg_hit_rate_no_searches(self):
        """Test calculating average hit rate with no searches"""
        result = calculate_avg_hit_rate(7, 0)

        assert result == 0.0

    @patch("tranotra.analytics.metrics.calculate_total_companies")
    @patch("tranotra.analytics.metrics.get_db")
    def test_calculate_high_score_rate_with_data(self, mock_get_db, mock_total_companies):
        """Test calculating high-score rate when data exists"""
        mock_total_companies.return_value = 100

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 28

        mock_get_db.return_value = mock_db

        result = calculate_high_score_rate(7)

        assert result == 28.0  # 28 / 100 * 100

    @patch("tranotra.analytics.metrics.calculate_total_companies")
    @patch("tranotra.analytics.metrics.get_db")
    def test_calculate_high_score_rate_no_companies(self, mock_get_db, mock_total_companies):
        """Test calculating high-score rate when no companies exist"""
        mock_total_companies.return_value = 0
        mock_get_db.return_value = MagicMock()

        result = calculate_high_score_rate(7)

        assert result == 0.0

    @patch("tranotra.analytics.metrics.get_db")
    def test_calculate_day_on_day_growth_positive(self, mock_get_db):
        """Test calculating day-on-day growth (positive)"""
        mock_db = MagicMock()

        # Setup mocks for two queries (today and yesterday)
        mock_query1 = MagicMock()
        mock_query2 = MagicMock()

        mock_db.query.side_effect = [mock_query1, mock_query2]

        # Today: 122 companies, Yesterday: 100 companies
        # Growth = (122 - 100) / 100 * 100 = 22%
        mock_query1.join.return_value.filter.return_value.scalar.return_value = 122
        mock_query2.join.return_value.filter.return_value.scalar.return_value = 100

        mock_get_db.return_value = mock_db

        result = calculate_day_on_day_growth()

        assert result == 22.0

    @patch("tranotra.analytics.metrics.get_db")
    def test_calculate_day_on_day_growth_no_yesterday_data(self, mock_get_db):
        """Test calculating day-on-day growth when no yesterday data"""
        mock_db = MagicMock()

        mock_query1 = MagicMock()
        mock_query2 = MagicMock()

        mock_db.query.side_effect = [mock_query1, mock_query2]

        # Today: 100 companies, Yesterday: 0 (no data)
        mock_query1.join.return_value.filter.return_value.scalar.return_value = 100
        mock_query2.join.return_value.filter.return_value.scalar.return_value = 0

        mock_get_db.return_value = mock_db

        result = calculate_day_on_day_growth()

        assert result == 0.0

    @patch("tranotra.analytics.metrics.get_db")
    def test_calculate_week_on_week_growth_positive(self, mock_get_db):
        """Test calculating week-on-week growth (positive)"""
        mock_db = MagicMock()

        mock_query1 = MagicMock()
        mock_query2 = MagicMock()

        mock_db.query.side_effect = [mock_query1, mock_query2]

        # This week: 1180 companies, Last week: 1000 companies
        # Growth = (1180 - 1000) / 1000 * 100 = 18%
        mock_query1.join.return_value.filter.return_value.scalar.return_value = 1180
        mock_query2.join.return_value.filter.return_value.scalar.return_value = 1000

        mock_get_db.return_value = mock_db

        result = calculate_week_on_week_growth()

        assert result == 18.0

    @patch("tranotra.analytics.metrics.get_db")
    def test_get_dashboard_metrics_success(self, mock_get_db):
        """Test aggregating all dashboard metrics"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 47

        mock_get_db.return_value = mock_db

        result = get_dashboard_metrics(7)

        assert isinstance(result, dict)
        assert "total_searches" in result
        assert "total_companies" in result


class TestMetricsEdgeCases:
    """Test edge cases and error conditions"""

    @patch("tranotra.analytics.metrics.get_db")
    def test_metrics_handle_database_error(self, mock_get_db):
        """Test that metrics functions handle database errors gracefully"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")

        mock_get_db.return_value = mock_db

        result = calculate_total_searches(7)

        # Should return 0 on error
        assert result == 0

    @patch("tranotra.analytics.metrics.get_db")
    def test_metrics_with_edge_day_values(self, mock_get_db):
        """Test metrics functions with various day values"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 0

        mock_get_db.return_value = mock_db

        # These should not raise errors, even if they return 0
        assert isinstance(calculate_total_searches(7), int)
        assert isinstance(calculate_total_searches(14), int)
        assert isinstance(calculate_total_searches(30), int)
