"""Custom exceptions for Tranotra Leads

Defines exception hierarchy for API clients, business logic, and validation errors.
"""


class APIError(Exception):
    """Base exception for all API errors"""

    pass


class GeminiError(APIError):
    """Base exception for Gemini API errors"""

    pass


class GeminiTimeoutError(GeminiError):
    """Raised when Gemini API call times out"""

    pass


class GeminiRateLimitError(GeminiError):
    """Raised when Gemini API rate limit is exceeded"""

    pass


class GeminiParseError(GeminiError):
    """Raised when Gemini response cannot be parsed"""

    pass
