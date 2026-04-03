"""Gemini API client wrapper for Tranotra Leads

Provides interface for Gemini Grounding Search API with:
- Client initialization with API key validation
- Grounding search with timeout and retry logic
- Comprehensive error handling and logging
- API key redaction in logs for security
"""

import logging
import threading
import time
from typing import Optional

import google.generativeai as genai

from .core.exceptions import (
    GeminiError,
    GeminiParseError,
    GeminiRateLimitError,
    GeminiTimeoutError,
)

logger = logging.getLogger(__name__)

# Global Gemini client instance with thread safety
_gemini_client: Optional[genai.GenerativeModel] = None
_lock = threading.Lock()


def _redact_api_key(api_key: str) -> str:
    """Redact API key for safe logging

    Args:
        api_key: Full API key

    Returns:
        Redacted API key in format "sk_...***" (first 5 chars + ...)
    """
    if not api_key or len(api_key) < 5:
        return "***"
    return f"{api_key[:5]}...***"


def initialize_gemini(api_key: str) -> bool:
    """Initialize Gemini client with API key

    Args:
        api_key: Gemini API key from environment or config

    Returns:
        True if initialization successful, False otherwise

    Raises:
        ValueError: If API key is empty, too short, or invalid
    """
    global _gemini_client

    # Validate API key
    if not api_key or not isinstance(api_key, str) or len(api_key.strip()) < 20:
        error_msg = "未找到 GEMINI_API_KEY，请检查 .env 文件"
        logger.error(error_msg)
        logger.error("获取 API 密钥: https://aistudio.google.com/app/apikey")
        raise ValueError(error_msg)

    try:
        with _lock:
            # Configure Gemini API with provided key
            genai.configure(api_key=api_key)

            # Create client instance
            _gemini_client = genai.GenerativeModel("gemini-2.5-flash")

            # Log successful initialization (without revealing full API key)
            logger.info(f"Gemini client initialized (key: {_redact_api_key(api_key)})")
        return True

    except Exception as e:
        error_msg = f"Failed to initialize Gemini client: {str(e)}"
        logger.error(error_msg)
        return False


def call_gemini_grounding_search(
    country: str,
    query: str,
    timeout: int = 30,
    max_retries: int = 3,
) -> str:
    """Call Gemini Grounding Search API to find companies

    Args:
        country: Country/region to search in (e.g., "Vietnam", "Thailand")
        query: Search query string (e.g., "PVC manufacturer")
        timeout: Request timeout in seconds (default: 30)
        max_retries: Maximum number of retry attempts (default: 3)

    Returns:
        Raw response from Gemini API as string (JSON/CSV/Markdown format
        preserved)

    Raises:
        GeminiTimeoutError: If request times out after all retries
        GeminiError: If API call fails for other reasons
    """
    if _gemini_client is None:
        error_msg = "Gemini client not initialized. Call initialize_gemini() first."
        logger.error(error_msg)
        raise GeminiError(error_msg)

    # Build prompt for company discovery
    prompt = f"""Find companies in {country} that match the following criteria: {query}

Return the results in JSON format with the following fields for each company:
- name
- country
- city
- main_products
- estimated_revenue
- prospect_score (1-10)
- priority (HIGH/MEDIUM/LOW)
- website
- linkedin_url

Please be thorough and return as many relevant companies as possible."""

    # Retry logic with exponential backoff
    retry_count = 0
    backoff_times = [2, 4, 8, 16]  # Exponential backoff: 2s, 4s, 8s, 16s

    start_time = time.time()

    while retry_count < max_retries:
        try:
            # Check timeout before attempting
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(f"Overall timeout exceeded ({elapsed:.1f}s > {timeout}s)")

            logger.info(
                f"Calling Gemini API (attempt {retry_count + 1}/{max_retries}): "
                f'search for "{query}" in {country}'
            )

            # Call Gemini with global client instance
            response = _gemini_client.generate_content(prompt)
            result_text = response.text

            logger.info(f"Gemini API call successful: {len(result_text)} characters returned")
            return result_text

        except TimeoutError as e:
            retry_count += 1
            if retry_count >= max_retries:
                error_msg = f"Gemini API timeout after {max_retries} attempts: {str(e)}"
                logger.error(error_msg)
                raise GeminiTimeoutError("搜索超时，请在 30 秒后重试") from e

            # Wait with exponential backoff before retry
            wait_idx = min(retry_count - 1, len(backoff_times) - 1)  # Prevent index overflow
            wait_time = backoff_times[wait_idx]
            logger.warning(f"Timeout on attempt {retry_count}, retrying in {wait_time}s...")
            time.sleep(wait_time)

        except Exception as e:
            # Handle rate limiting
            if "429" in str(e) or "quota" in str(e).lower():
                retry_count += 1
                if retry_count >= max_retries:
                    error_msg = f"Gemini API rate limit exceeded after {max_retries} attempts"
                    logger.error(error_msg)
                    raise GeminiRateLimitError("API 配额已用尽，请稍后再试") from e

                wait_idx = min(retry_count - 1, len(backoff_times) - 1)  # Prevent index overflow
                wait_time = backoff_times[wait_idx]
                logger.warning(f"Rate limited, retrying in {wait_time}s...")
                time.sleep(wait_time)

            # Handle other API errors
            else:
                error_msg = f"Gemini API error: {str(e)}"
                logger.error(error_msg)
                raise GeminiError("搜索失败，请检查 API 密钥或稍后重试") from e

    # Should not reach here, but just in case
    raise GeminiTimeoutError("搜索超时，请在 30 秒后重试")
