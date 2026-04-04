"""Analytics metrics calculation module for dashboard

Provides functions to calculate key performance metrics from search history data.
All functions operate on search_history and company tables using SQLAlchemy ORM.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import logging

from sqlalchemy import func
from tranotra.infrastructure.database import get_db
from tranotra.core.models import Company, SearchHistory


logger = logging.getLogger(__name__)


def _get_date_range(days: int) -> tuple:
    """Get start and end dates for the specified period.

    Args:
        days: Number of days to look back (7, 14, 30, etc.)

    Returns:
        Tuple of (start_datetime, end_datetime) in UTC
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def _get_yesterday_range() -> tuple:
    """Get date range for yesterday (UTC).

    Returns:
        Tuple of (yesterday_start, yesterday_end) in UTC
    """
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    # Use UTC timezone to match database timestamps
    yesterday_start = datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc)
    yesterday_end = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc)

    return yesterday_start, yesterday_end


def _get_last_week_range() -> tuple:
    """Get date range for last week (7-14 days ago, UTC).

    Returns:
        Tuple of (last_week_start, last_week_end) in UTC
    """
    today = datetime.utcnow()
    # Round to midnight UTC for consistent week boundaries
    today = today.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    last_week_end = today - timedelta(days=7)
    last_week_start = last_week_end - timedelta(days=7)

    return last_week_start, last_week_end


def calculate_total_searches(days: int) -> int:
    """Calculate total number of distinct searches in period.

    Args:
        days: Number of days to look back

    Returns:
        Count of distinct search_history records
    """
    start_date, end_date = _get_date_range(days)
    db = get_db()

    try:
        count = db.query(func.count(func.distinct(SearchHistory.id))).filter(
            SearchHistory.created_at >= start_date,
            SearchHistory.created_at < end_date
        ).scalar() or 0

        logger.debug(f"Total searches for {days} days: {count}")
        return count
    except Exception as e:
        logger.error(f"Error calculating total_searches: {e}")
        return 0


def calculate_total_companies(days: int) -> int:
    """Calculate total distinct companies discovered in period.

    Args:
        days: Number of days to look back

    Returns:
        Count of distinct companies in search_history
    """
    start_date, end_date = _get_date_range(days)
    db = get_db()

    try:
        # Count distinct companies that appear in search_history during period
        count = db.query(func.count(func.distinct(Company.id))).join(
            SearchHistory
        ).filter(
            SearchHistory.created_at >= start_date,
            SearchHistory.created_at < end_date
        ).scalar() or 0

        logger.debug(f"Total companies for {days} days: {count}")
        return count
    except Exception as e:
        logger.error(f"Error calculating total_companies: {e}")
        return 0


def calculate_dedup_rate(days: int) -> float:
    """Calculate deduplication rate as percentage.

    Formula: (SUM(duplicate_count) / COUNT(DISTINCT company.id)) * 100

    Args:
        days: Number of days to look back

    Returns:
        Dedup rate as percentage (0-100), or 0 if no data
    """
    start_date, end_date = _get_date_range(days)
    db = get_db()

    try:
        # Single aggregated query: count distinct companies and sum duplicates
        result = db.query(
            func.count(func.distinct(Company.id)).label('total_companies'),
            func.sum(SearchHistory.duplicate_count).label('total_duplicates')
        ).join(SearchHistory).filter(
            SearchHistory.created_at >= start_date,
            SearchHistory.created_at < end_date
        ).first()

        total_companies = result.total_companies or 0
        total_duplicates = result.total_duplicates or 0

        if total_companies == 0:
            return 0.0

        rate = (total_duplicates / total_companies) * 100
        logger.debug(f"Dedup rate for {days} days: {rate:.1f}%")
        return round(rate, 1)
    except Exception as e:
        logger.error(f"Error calculating dedup_rate: {e}")
        return 0.0


def calculate_avg_hit_rate(days: int, total_searches: int) -> float:
    """Calculate average companies per search.

    Formula: total_companies / total_searches

    Args:
        days: Number of days to look back
        total_searches: Total number of searches (can pass precalculated value)

    Returns:
        Average hit rate (companies per search), or 0 if no searches
    """
    if total_searches == 0:
        return 0.0

    try:
        total_companies = calculate_total_companies(days)
        rate = total_companies / total_searches
        logger.debug(f"Avg hit rate for {days} days: {rate:.1f}")
        return round(rate, 1)
    except Exception as e:
        logger.error(f"Error calculating avg_hit_rate: {e}")
        return 0.0


def calculate_high_score_rate(days: int) -> float:
    """Calculate percentage of high-score companies (score >= 8).

    Formula: (COUNT(company WHERE prospect_score >= 8) / total_companies) * 100

    Args:
        days: Number of days to look back

    Returns:
        High-score rate as percentage (0-100), or 0 if no data
    """
    start_date, end_date = _get_date_range(days)
    db = get_db()

    try:
        total_companies = calculate_total_companies(days)
        if total_companies == 0:
            return 0.0

        high_score_count = db.query(func.count(func.distinct(Company.id))).join(
            SearchHistory
        ).filter(
            SearchHistory.created_at >= start_date,
            SearchHistory.created_at < end_date,
            Company.prospect_score >= 8
        ).scalar() or 0

        rate = (high_score_count / total_companies) * 100
        logger.debug(f"High-score rate for {days} days: {rate:.1f}%")
        return round(rate, 1)
    except Exception as e:
        logger.error(f"Error calculating high_score_rate: {e}")
        return 0.0


def calculate_day_on_day_growth() -> float:
    """Calculate day-on-day growth percentage.

    Formula: ((today_companies - yesterday_companies) / yesterday_companies) * 100

    Returns:
        Growth percentage, or 0 if no data or division by zero
    """
    db = get_db()

    try:
        # Today (last 24 hours)
        today_start, today_end = _get_date_range(1)
        today_count = db.query(func.count(func.distinct(Company.id))).join(
            SearchHistory
        ).filter(
            SearchHistory.created_at >= today_start,
            SearchHistory.created_at < today_end
        ).scalar() or 0

        # Yesterday
        yesterday_start, yesterday_end = _get_yesterday_range()
        yesterday_count = db.query(func.count(func.distinct(Company.id))).join(
            SearchHistory
        ).filter(
            SearchHistory.created_at >= yesterday_start,
            SearchHistory.created_at < yesterday_end
        ).scalar() or 0

        if yesterday_count == 0:
            return 0.0

        growth = ((today_count - yesterday_count) / yesterday_count) * 100
        logger.debug(f"Day-on-day growth: {growth:.1f}%")
        return round(growth, 1)
    except Exception as e:
        logger.error(f"Error calculating day_on_day_growth: {e}")
        return 0.0


def calculate_week_on_week_growth() -> float:
    """Calculate week-on-week growth percentage.

    Formula: ((this_week_companies - last_week_companies) / last_week_companies) * 100

    Returns:
        Growth percentage, or 0 if no data or division by zero
    """
    db = get_db()

    try:
        # This week (last 7 days)
        this_week_start, this_week_end = _get_date_range(7)
        this_week_count = db.query(func.count(func.distinct(Company.id))).join(
            SearchHistory
        ).filter(
            SearchHistory.created_at >= this_week_start,
            SearchHistory.created_at < this_week_end
        ).scalar() or 0

        # Last week (7-14 days ago)
        last_week_start, last_week_end = _get_last_week_range()
        last_week_count = db.query(func.count(func.distinct(Company.id))).join(
            SearchHistory
        ).filter(
            SearchHistory.created_at >= last_week_start,
            SearchHistory.created_at < last_week_end
        ).scalar() or 0

        if last_week_count == 0:
            return 0.0

        growth = ((this_week_count - last_week_count) / last_week_count) * 100
        logger.debug(f"Week-on-week growth: {growth:.1f}%")
        return round(growth, 1)
    except Exception as e:
        logger.error(f"Error calculating week_on_week_growth: {e}")
        return 0.0


def get_dashboard_metrics(days: int) -> Dict:
    """Aggregate all metrics for dashboard display.

    This is the main function called by the API endpoint.
    Returns all 7 metrics with timestamp.

    Args:
        days: Number of days to look back (7, 14, 30, etc.)

    Returns:
        Dictionary with all metrics and timestamp
    """
    logger.info(f"Calculating dashboard metrics for {days} days")

    try:
        total_searches = calculate_total_searches(days)
        total_companies = calculate_total_companies(days)

        metrics = {
            "total_searches": total_searches,
            "total_companies": total_companies,
            "dedup_rate": calculate_dedup_rate(days),
            "avg_hit_rate": calculate_avg_hit_rate(days, total_searches),
            "high_score_rate": calculate_high_score_rate(days),
            "day_on_day_growth": calculate_day_on_day_growth(),
            "week_on_week_growth": calculate_week_on_week_growth(),
        }

        logger.info(f"Dashboard metrics calculated successfully: {metrics}")
        return metrics
    except Exception as e:
        logger.error(f"Error aggregating dashboard metrics: {e}")
        return {}
