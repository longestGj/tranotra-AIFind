"""Flask Blueprint for search-related routes"""

import logging
import time
from typing import Tuple, Dict, Optional
from functools import lru_cache

from flask import Blueprint, Response, jsonify, request, render_template, current_app

from tranotra.gemini_client import initialize_gemini, call_gemini_grounding_search
from tranotra.core.exceptions import GeminiTimeoutError, GeminiError
from tranotra.db import get_today_statistics, get_companies_paginated

logger = logging.getLogger(__name__)

# Create blueprint
search_bp = Blueprint("search", __name__, url_prefix="/api/search")


# Simple in-memory cache for search results (TTL: 5 minutes)
class SearchResultsCache:
    def __init__(self, max_size: int = 50, ttl: int = 300):
        self.cache: Dict = {}
        self.timestamps: Dict = {}
        self.max_size = max_size
        self.ttl = ttl

    def get(self, key: str) -> Optional[Dict]:
        """Get cached result if exists and not expired"""
        if key not in self.cache:
            return None

        # Check if expired
        if time.time() - self.timestamps[key] > self.ttl:
            del self.cache[key]
            del self.timestamps[key]
            return None

        return self.cache[key]

    def set(self, key: str, value: Dict) -> None:
        """Set cache with LRU eviction"""
        # Remove oldest entry if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.timestamps, key=self.timestamps.get)
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]

        self.cache[key] = value
        self.timestamps[key] = time.time()

    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
        self.timestamps.clear()


# Global cache instance
results_cache = SearchResultsCache()


def detect_response_format(response: str) -> str:
    """Detect response format (JSON, Markdown, CSV, or UNKNOWN)

    Args:
        response: Raw response string from Gemini API

    Returns:
        str: One of "JSON", "Markdown", "CSV", or "UNKNOWN"
    """
    if not response:
        return "UNKNOWN"

    response = response.strip()

    # Check for JSON (starts with { or [)
    if response.startswith('{') or response.startswith('['):
        return "JSON"

    # Check for Markdown table (contains | and ---)
    if '|' in response and '---' in response:
        return "Markdown"

    # Check for CSV (comma or tab-separated, has header-like pattern)
    lines = response.split('\n')
    if len(lines) >= 2:
        first_line = lines[0]
        # Check if first line contains commas or tabs
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
    """Handle search API request

    Returns:
        Tuple[Response, int]: JSON response and HTTP status code
    """
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


@search_bp.route("/results", methods=["GET"])
def get_search_results() -> Tuple[Response, int]:
    """Fetch paginated search results with optional filtering

    Query Parameters:
    - country: optional string
    - query: optional string (source_query field)
    - page: optional int (default=1)
    - per_page: optional int (default=20, max=100)

    Returns:
        Tuple[Response, int]: JSON response with companies and metadata
    """
    try:
        # Extract and validate query parameters
        country = request.args.get('country', '').strip() or None
        query = request.args.get('query', '').strip() or None
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        # Build cache key
        cache_key = f"{country or 'all'}#{query or 'all'}#{page}"

        # Check cache first
        cached_result = results_cache.get(cache_key)
        if cached_result:
            cached_result['cached'] = True
            logger.debug(f"Cache hit for: {cache_key}")
            return jsonify({
                "success": True,
                "timestamp": cached_result.get('timestamp'),
                "cached": True,
                **{k: v for k, v in cached_result.items() if k != 'timestamp'}
            }), 200

        # Fetch from database with timeout
        start_time = time.time()
        timeout_seconds = 3

        # Execute query
        try:
            result = get_companies_paginated(
                country=country,
                query=query,
                page=page,
                per_page=per_page
            )

            elapsed = time.time() - start_time

            # Prepare response
            response_data = {
                "success": True,
                "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                "cached": False,
                "new_count": result['new_count'],
                "duplicate_count": result['duplicate_count'],
                "avg_score": result['avg_score'],
                "total_count": result['total'],
                "current_page": result['current_page'],
                "per_page": result['per_page'],
                "total_pages": result['total_pages'],
                "companies": result['companies']
            }

            # Cache the result
            results_cache.set(cache_key, response_data)

            logger.info(f"Query complete in {elapsed:.2f}s: country={country}, query={query}, page={page}, results={len(result['companies'])}")

            return jsonify(response_data), 200

        except Exception as db_error:
            elapsed = time.time() - start_time

            # If query timeout, try to return cached result if available
            if elapsed > timeout_seconds:
                logger.warning(f"Database query timeout (>{timeout_seconds}s): {db_error}")
                cached_result = results_cache.get(cache_key)
                if cached_result:
                    cached_result['cached'] = True
                    logger.info(f"Returning cached fallback for timeout: {cache_key}")
                    return jsonify({
                        "success": True,
                        "timestamp": cached_result.get('timestamp'),
                        "cached": True,
                        "message": "数据加载中（显示缓存结果）",
                        **{k: v for k, v in cached_result.items() if k != 'timestamp'}
                    }), 200

            # No cache available, return error
            logger.error(f"Database error retrieving results: {db_error}")
            return jsonify({
                "success": False,
                "message": "加载失败，请重试"
            }), 500

    except ValueError as e:
        logger.warning(f"Invalid parameter: {e}")
        return jsonify({
            "success": False,
            "message": "参数错误"
        }), 400

    except Exception as e:
        logger.error(f"Unexpected error in get_search_results: {e}")
        return jsonify({
            "success": False,
            "message": "加载失败，请重试"
        }), 500
