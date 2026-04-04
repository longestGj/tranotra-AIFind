"""Analytics API endpoints for dashboard metrics and reporting"""

from datetime import datetime
from typing import Tuple, Dict
import logging

from flask import Blueprint, request, jsonify

from tranotra.analytics import get_dashboard_metrics


logger = logging.getLogger(__name__)


# Create blueprint for analytics routes
analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


def _validate_days_param(days_param: str) -> Tuple[bool, int, str]:
    """Validate and parse the 'days' query parameter.

    Args:
        days_param: String value from query parameter

    Returns:
        Tuple of (is_valid, days_value, error_message)
    """
    if not days_param:
        return False, 0, "Parameter 'days' is required"

    try:
        days = int(days_param)
        if days not in (7, 14, 30):
            return False, 0, f"Parameter 'days' must be 7, 14, or 30 (got {days})"
        return True, days, ""
    except ValueError:
        return False, 0, f"Parameter 'days' must be integer (got '{days_param}')"


def _error_response(code: str, message: str, status: int) -> Tuple[Dict, int]:
    """Generate standardized error response.

    Args:
        code: Error code (e.g., "VALIDATION_ERROR")
        message: Human-readable error message
        status: HTTP status code

    Returns:
        Tuple of (response_dict, status_code)
    """
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }, status


@analytics_bp.route("/dashboard", methods=["GET"])
def get_dashboard() -> Tuple[Dict, int]:
    """Get dashboard metrics for specified period.

    Query Parameters:
        - days: int (7, 14, or 30) — Period for metrics calculation

    Returns:
        Tuple of (response_dict, status_code)

    Example Response (200 OK):
    {
        "success": true,
        "data": {
            "period": "last_7_days",
            "metrics": {
                "total_searches": 47,
                "total_companies": 312,
                "dedup_rate": 18.5,
                "avg_hit_rate": 20.8,
                "high_score_rate": 28.2,
                "day_on_day_growth": 22.1,
                "week_on_week_growth": 18.3
            },
            "timestamp": "2026-04-03T12:00:00Z"
        },
        "error": null
    }
    """
    try:
        # Get and validate 'days' parameter
        days_param = request.args.get("days", "")
        is_valid, days, error_msg = _validate_days_param(days_param)

        if not is_valid:
            logger.warning(f"Invalid days parameter: {error_msg}")
            return _error_response("VALIDATION_ERROR", error_msg, 400)

        # Calculate metrics
        logger.info(f"Calculating dashboard metrics for {days} days")
        metrics = get_dashboard_metrics(days)

        # Check if metrics calculation failed
        if not metrics:
            logger.warning(f"Failed to calculate metrics for {days} days")
            return _error_response(
                "CALCULATION_ERROR",
                "Unable to calculate dashboard metrics",
                500
            )

        # Build response
        period_map = {7: "last_7_days", 14: "last_14_days", 30: "last_30_days"}

        response = {
            "success": True,
            "data": {
                "period": period_map[days],
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "error": None
        }

        logger.info(f"Dashboard metrics calculated successfully for {days} days")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Error in get_dashboard: {e}", exc_info=True)
        return _error_response(
            "SERVER_ERROR",
            "Failed to calculate dashboard metrics",
            500
        )
