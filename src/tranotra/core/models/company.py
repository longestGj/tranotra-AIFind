"""Company SQLAlchemy model for database persistence"""

from datetime import datetime
from typing import Dict, Any

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, CheckConstraint
from sqlalchemy.sql import func

from . import Base


class Company(Base):
    """Company model for storing discovered companies

    Represents a company discovered through Gemini search with 23 fields including
    company information, export markets, and prospect scoring.
    """

    __tablename__ = "companies"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Company information (required)
    name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)

    # Company details
    city = Column(String(100), nullable=True)
    year_established = Column(Integer, nullable=True)
    employees = Column(String(100), nullable=True)
    estimated_revenue = Column(String(100), nullable=True)
    main_products = Column(Text, nullable=True)
    export_markets = Column(Text, nullable=True)
    eu_us_jp_export = Column(Boolean, nullable=True)
    raw_materials = Column(Text, nullable=True)

    # Tranotra recommendation
    recommended_product = Column(String(255), nullable=True)
    recommendation_reason = Column(Text, nullable=True)

    # Contact information
    website = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    linkedin_normalized = Column(String(255), nullable=True, unique=True, index=True)
    best_contact_title = Column(String(255), nullable=True)

    # Scoring and priority
    prospect_score = Column(Integer, nullable=True)  # 1-10, validated by CHECK constraint
    priority = Column(String(10), nullable=True)  # A, B, C (or HIGH, MEDIUM, LOW)

    # Source information (required)
    source_query = Column(String(255), nullable=False)

    # Timestamps (auto-managed)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Table constraints
    __table_args__ = (
        CheckConstraint("prospect_score >= 1 AND prospect_score <= 10", name="check_prospect_score"),
        CheckConstraint("priority IN ('A', 'B', 'C', 'HIGH', 'MEDIUM', 'LOW')", name="check_priority"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary

        Returns:
            Dict containing all 23 company fields
        """
        return {
            "id": self.id,
            "name": self.name,
            "country": self.country,
            "city": self.city,
            "year_established": self.year_established,
            "employees": self.employees,
            "estimated_revenue": self.estimated_revenue,
            "main_products": self.main_products,
            "export_markets": self.export_markets,
            "eu_us_jp_export": self.eu_us_jp_export,
            "raw_materials": self.raw_materials,
            "recommended_product": self.recommended_product,
            "recommendation_reason": self.recommendation_reason,
            "website": self.website,
            "contact_email": self.contact_email,
            "linkedin_url": self.linkedin_url,
            "linkedin_normalized": self.linkedin_normalized,
            "best_contact_title": self.best_contact_title,
            "prospect_score": self.prospect_score,
            "priority": self.priority,
            "source_query": self.source_query,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name} country={self.country}>"
