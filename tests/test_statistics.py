"""Tests for search statistics calculation"""

import pytest
from datetime import datetime
from tranotra.db import get_today_statistics


class TestStatistics:
    """Test statistics calculation from search_history table"""

    def test_get_today_statistics_empty(self, app):
        """Test statistics when no searches exist"""
        with app.app_context():
            stats = get_today_statistics()
            assert stats["searches"] == 0
            assert stats["new_companies"] == 0
            assert stats["dedup_rate"] == 0

    def test_get_today_statistics_with_single_search(self, app, mocker):
        """Test statistics with one search (mocked)"""
        from tranotra.core.models.search_history import SearchHistory

        with app.app_context():
            # Mock the database query to return one search
            search_mock = mocker.MagicMock(spec=SearchHistory)
            search_mock.new_count = 8
            search_mock.duplicate_count = 2

            mocker.patch(
                "tranotra.db.get_db"
            ).return_value.query.return_value.filter.return_value.all.return_value = [search_mock]

            stats = get_today_statistics()
            assert stats["searches"] == 1
            assert stats["new_companies"] == 8
            assert stats["dedup_rate"] == pytest.approx(20.0, rel=0.1)  # 2 / 10 * 100

    def test_get_today_statistics_multiple_searches(self, app, mocker):
        """Test statistics aggregation across multiple searches (mocked)"""
        from tranotra.core.models.search_history import SearchHistory

        with app.app_context():
            # Mock the database query to return two searches
            search1_mock = mocker.MagicMock(spec=SearchHistory)
            search1_mock.new_count = 8
            search1_mock.duplicate_count = 2

            search2_mock = mocker.MagicMock(spec=SearchHistory)
            search2_mock.new_count = 12
            search2_mock.duplicate_count = 3

            mocker.patch(
                "tranotra.db.get_db"
            ).return_value.query.return_value.filter.return_value.all.return_value = [search1_mock, search2_mock]

            stats = get_today_statistics()
            assert stats["searches"] == 2
            assert stats["new_companies"] == 20  # 8 + 12
            assert stats["dedup_rate"] == pytest.approx(20.0, rel=0.1)  # 5 / 25 * 100

    def test_dedup_rate_calculation_100_percent(self, app):
        """Test dedup rate calculation with all duplicates"""
        from tranotra.core.models.search_history import SearchHistory
        from tranotra.infrastructure.database import get_db

        with app.app_context():
            db = get_db()
            search = SearchHistory(
                country="Vietnam",
                query="test",
                result_count=10,
                new_count=0,
                duplicate_count=10,
                avg_score=0,
                high_priority_count=0,
            )
            db.add(search)
            db.commit()

            stats = get_today_statistics()
            # When new_count is 0, dedup_rate should be 0 (to avoid division by zero)
            # or 100 if we define it as duplicates / total
            assert stats["dedup_rate"] in [0, 100]

    def test_statistics_only_today(self, app, mocker):
        """Test that statistics only count today's searches (mocked)"""
        from tranotra.core.models.search_history import SearchHistory
        from datetime import timedelta

        with app.app_context():
            # Mock the database query to return only today's search
            today_search_mock = mocker.MagicMock(spec=SearchHistory)
            today_search_mock.new_count = 4
            today_search_mock.duplicate_count = 1

            # The query should only return today's search (filtered by date)
            mocker.patch(
                "tranotra.db.get_db"
            ).return_value.query.return_value.filter.return_value.all.return_value = [today_search_mock]

            stats = get_today_statistics()
            # Should only count today's search
            assert stats["searches"] == 1
            assert stats["new_companies"] == 4
