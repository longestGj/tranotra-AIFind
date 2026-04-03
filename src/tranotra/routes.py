"""Flask Blueprint for search-related routes"""

from typing import Tuple

from flask import Blueprint, Response, jsonify

# Create blueprint
search_bp = Blueprint("search", __name__, url_prefix="/api/search")


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
