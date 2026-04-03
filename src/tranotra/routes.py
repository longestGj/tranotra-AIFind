"""Flask Blueprint for search-related routes"""

import logging
import time
import json
import threading
from typing import Tuple, Dict, Optional
from functools import lru_cache
from collections import OrderedDict

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
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
        self.lock = threading.RLock()

    def _generate_key(self, country: Optional[str], query: Optional[str], page: int) -> str:
        """Generate cache key using JSON serialization to avoid collisions"""
        key_dict = {
            'country': country,
            'query': query,
            'page': page
        }
        return json.dumps(key_dict, sort_keys=True)

    def get(self, country: Optional[str], query: Optional[str], page: int) -> Optional[Dict]:
        """Get cached result if exists and not expired"""
        key = self._generate_key(country, query, page)

        with self.lock:
            if key not in self.cache:
                return None

            value, timestamp = self.cache[key]

            # Check if expired
            if time.time() - timestamp > self.ttl:
                del self.cache[key]
                return None

            # Move to end (mark as recently used for LRU)
            self.cache.move_to_end(key)
            return value

    def set(self, country: Optional[str], query: Optional[str], page: int, value: Dict) -> None:
        """Set cache with LRU eviction (thread-safe)"""
        key = self._generate_key(country, query, page)

        with self.lock:
            # Remove oldest entry if cache is full (before adding new item)
            if len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]

            # Store value with timestamp
            self.cache[key] = (value, time.time())
            self.cache.move_to_end(key)

    def clear(self):
        """Clear entire cache"""
        with self.lock:
            self.cache.clear()


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
                "message": "Search API ready (implemented in Story 1.4)"
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

        # Validate pagination parameters
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "message": "参数错误：页码和每页数量必须是整数"
            }), 400

        # Validate page and per_page bounds
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = min(max(per_page, 1), 100)

        # Check cache first
        cached_result = results_cache.get(country, query, page)
        if cached_result:
            logger.debug(f"Cache hit: country={country}, query={query}, page={page}")
            return jsonify({
                "success": True,
                "timestamp": cached_result.get('timestamp'),
                "cached": True,
                "has_next": cached_result.get('has_next', False),
                "has_previous": cached_result.get('has_previous', False),
                **{k: v for k, v in cached_result.items() if k not in ['timestamp', 'has_next', 'has_previous']}
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

            # Calculate pagination metadata
            has_next = page < result['total_pages']
            has_previous = page > 1

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
                "has_next": has_next,
                "has_previous": has_previous,
                "companies": result['companies']
            }

            # Cache the result
            results_cache.set(country, query, page, response_data)

            logger.info(f"Query complete in {elapsed:.2f}s: country={country}, query={query}, page={page}, results={len(result['companies'])}")

            return jsonify(response_data), 200

        except Exception as db_error:
            elapsed = time.time() - start_time

            # If query timeout, try to return cached result if available
            if elapsed > timeout_seconds:
                logger.warning(f"Database query timeout (>{timeout_seconds}s): {db_error}")
                cached_result = results_cache.get(country, query, page)
                if cached_result:
                    logger.info(f"Returning cached fallback for timeout")
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
                "message": "搜索失败，请稍后重试"
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
            "message": "搜索失败，请稍后重试"
        }), 500
