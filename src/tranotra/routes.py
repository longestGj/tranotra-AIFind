"""Flask Blueprint for search-related routes"""

import logging
from typing import Tuple

from flask import Blueprint, Response, jsonify, request, current_app

from tranotra.gemini_client import initialize_gemini, call_gemini_grounding_search
from tranotra.core.exceptions import GeminiTimeoutError, GeminiError

logger = logging.getLogger(__name__)

# Create blueprint
search_bp = Blueprint("search", __name__, url_prefix="/api/search")


def detect_response_format(response: str) -> str:
    """Detect response format (JSON, Markdown, CSV, or UNKNOWN)"""
    if not response:
        return "UNKNOWN"

    response = response.strip()

    # Check for JSON
    if response.startswith('{') or response.startswith('['):
        return "JSON"

    # Check for Markdown table
    if '|' in response and '---' in response:
        return "Markdown"

    # Check for CSV
    lines = response.split('\n')
    if len(lines) >= 2:
        first_line = lines[0]
        if (',' in first_line or '\t' in first_line) and len(first_line.split(',')) >= 2:
            return "CSV"

    return "UNKNOWN"


@search_bp.route("/", methods=["GET"])
def search_index() -> Tuple[Response, int]:
    """Search endpoint index

    Returns:
        Tuple[Response, int]: JSON response and HTTP status code
    """
    return (
        jsonify(
            {
                "success": True,
                "data": {"message": "Search API ready (implemented in Story 1.4)"},
                "error": None,
            }
        ),
        200,
    )


@search_bp.route("/", methods=["POST"])
def search_api() -> Tuple[Response, int]:
    """Handle search API request"""
    country = request.form.get('country', '').strip()
    keyword = request.form.get('keyword', '').strip()

    # Validate input
    if not country or not keyword:
        return (
            jsonify({
                "status": "error",
                "message": "国家和关键词不能为空"
            }),
            400
        )

    try:
        # Initialize Gemini
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not initialize_gemini(api_key):
            logger.error("Gemini initialization failed")
            return (
                jsonify({
                    "status": "error",
                    "message": "API密钥配置错误，请检查.env文件"
                }),
                500
            )

        # Call Gemini API
        response = call_gemini_grounding_search(country, keyword)

        # Detect format
        fmt = detect_response_format(response)
        if fmt == "UNKNOWN":
            logger.warning(f"Unknown response format for {country}/{keyword}")
            return (
                jsonify({
                    "status": "error",
                    "message": "搜索失败：格式错误，请稍后重试"
                }),
                400
            )

        logger.info(f"Search successful: country={country}, format={fmt}")
        return (
            jsonify({
                "status": "success",
                "format": fmt,
                "message": "搜索成功，正在处理结果..."
            }),
            200
        )

    except GeminiTimeoutError as e:
        logger.error(f"Gemini timeout: {e}")
        return (
            jsonify({
                "status": "timeout",
                "message": "搜索超时，请重试"
            }),
            500
        )

    except GeminiError as e:
        logger.error(f"Gemini API error: {e}")
        return (
            jsonify({
                "status": "error",
                "message": "搜索失败，请稍后重试"
            }),
            500
        )

    except Exception as e:
        logger.error(f"Unexpected error in search: {e}")
        return (
            jsonify({
                "status": "error",
                "message": "搜索失败，请稍后重试"
            }),
            500
        )
