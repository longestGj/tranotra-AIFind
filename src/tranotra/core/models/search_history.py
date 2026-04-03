"""SearchHistory SQLAlchemy model for tracking search operations"""

from datetime import datetime
from typing import Dict, Any

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

from . import Base


class SearchHistory(Base):
    """SearchHistory model for tracking company searches

    Records statistics about each search operation including search parameters,
    result counts, deduplication metrics, and scoring statistics.
    """

    __tablename__ = "search_history"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Search parameters (required)
    country = Column(String(100), nullable=False, index=True)
    query = Column(String(255), nullable=False)

    # Result counts
    result_count = Column(Integer, nullable=True)  # Total results from Gemini
    new_count = Column(Integer, nullable=True)  # New companies inserted
    duplicate_count = Column(Integer, nullable=True)  # Duplicates skipped
    avg_score = Column(Float, nullable=True)  # Average prospect score of new companies
    high_priority_count = Column(Integer, nullable=True)  # Count of HIGH/A priority companies

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary

        Returns:
            Dict containing all 9 search history fields
        """
        return {
            "id": self.id,
            "country": self.country,
            "query": self.query,
            "result_count": self.result_count,
            "new_count": self.new_count,
            "duplicate_count": self.duplicate_count,
            "avg_score": self.avg_score,
            "high_priority_count": self.high_priority_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<SearchHistory id={self.id} country={self.country} query={self.query}>"
