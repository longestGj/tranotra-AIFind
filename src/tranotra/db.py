"""Database layer with CRUD operations for Company and SearchHistory"""

from typing import List, Dict, Optional
import logging

from sqlalchemy.exc import IntegrityError
from tranotra.infrastructure.database import get_db
from tranotra.core.models import Company, SearchHistory


logger = logging.getLogger(__name__)


# Company CRUD Operations


def insert_company(data: Dict) -> int:
    """Insert a new company into the database

    Skips insertion if linkedin_normalized already exists (deduplication).

    Args:
        data: Dictionary with company fields

    Returns:
        int: Company ID if inserted, or existing company ID if duplicate

    Raises:
        ValueError: If required fields missing or validation fails
    """
    # Validate required fields
    if not data.get("name"):
        raise ValueError("Company name is required")
    if not data.get("country"):
        raise ValueError("Country is required")
    if not data.get("source_query"):
        raise ValueError("Source query is required")

    # Validate prospect_score if provided
    if "prospect_score" in data and data["prospect_score"] is not None:
        score = data["prospect_score"]
        if not isinstance(score, int) or score < 1 or score > 10:
            raise ValueError("prospect_score must be integer between 1-10")

    # Validate priority if provided
    if "priority" in data and data["priority"] is not None:
        priority = str(data["priority"]).upper()
        if priority not in ("A", "B", "C", "HIGH", "MEDIUM", "LOW"):
            raise ValueError("priority must be one of: A, B, C, HIGH, MEDIUM, LOW")

    db = get_db()
    try:
        # Create new company
        company = Company(**data)
        db.add(company)
        db.commit()
        logger.info(f"Inserted company: {company.name} (ID: {company.id})")
        return company.id

    except IntegrityError as e:
        db.rollback()
        # If duplicate linkedin_normalized, return existing company ID
        if "linkedin_normalized" in str(e).lower() and data.get("linkedin_normalized"):
            existing = db.query(Company).filter_by(
                linkedin_normalized=data["linkedin_normalized"]
            ).first()
            if existing:
                logger.info(f"Skipping duplicate: {data['name']} (linkedin_normalized already exists)")
                return existing.id
        logger.error(f"Database integrity error inserting company: {e}")
        raise ValueError(f"Database constraint violated: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting company: {e}")
        raise


def update_company(id: int, data: Dict) -> bool:
    """Update company fields by ID

    Args:
        id: Company ID
        data: Dictionary with fields to update

    Returns:
        bool: True if updated, False if company not found
    """
    db = get_db()
    try:
        company = db.query(Company).filter_by(id=id).first()
        if not company:
            logger.warning(f"Company not found: ID {id}")
            return False

        # Update fields from data dict
        for key, value in data.items():
            if hasattr(company, key):
                setattr(company, key, value)

        db.commit()
        logger.info(f"Updated company: ID {id}")
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating company: {e}")
        raise


def get_companies_by_score(min_score: int) -> List[Company]:
    """Get all companies with prospect_score >= min_score

    Args:
        min_score: Minimum prospect score (1-10)

    Returns:
        List of Company objects sorted by score descending
    """
    db = get_db()
    try:
        companies = db.query(Company).filter(
            Company.prospect_score >= min_score
        ).order_by(Company.prospect_score.desc()).all()
        logger.info(f"Retrieved {len(companies)} companies with score >= {min_score}")
        return companies

    except Exception as e:
        logger.error(f"Error retrieving companies by score: {e}")
        raise


def get_companies_by_search(country: str, query: str) -> List[Company]:
    """Get companies from a specific search

    Args:
        country: Country name
        query: Search keyword

    Returns:
        List of Company objects from this search
    """
    db = get_db()
    try:
        companies = db.query(Company).filter(
            Company.country == country,
            Company.source_query == query
        ).order_by(Company.prospect_score.desc()).all()
        logger.info(f"Retrieved {len(companies)} companies for {country}/{query}")
        return companies

    except Exception as e:
        logger.error(f"Error retrieving companies by search: {e}")
        raise


# Search History Operations


def insert_search_history(data: Dict) -> int:
    """Insert a search history record

    Args:
        data: Dictionary with search history fields

    Returns:
        int: Search history record ID

    Raises:
        ValueError: If required fields missing
    """
    # Validate required fields
    if not data.get("country"):
        raise ValueError("Country is required")
    if not data.get("query"):
        raise ValueError("Query is required")

    db = get_db()
    try:
        history = SearchHistory(**data)
        db.add(history)
        db.commit()
        logger.info(f"Inserted search history: {data['country']}/{data['query']} (ID: {history.id})")
        return history.id

    except Exception as e:
        db.rollback()
        logger.error(f"Error inserting search history: {e}")
        raise


def get_search_history(limit: int = 20) -> List[SearchHistory]:
    """Get recent search history records

    Args:
        limit: Maximum number of records to return (default 20)

    Returns:
        List of SearchHistory objects, most recent first
    """
    db = get_db()
    try:
        history = db.query(SearchHistory).order_by(
            SearchHistory.created_at.desc()
        ).limit(limit).all()
        logger.info(f"Retrieved {len(history)} recent search history records")
        return history

    except Exception as e:
        logger.error(f"Error retrieving search history: {e}")
        raise


def get_today_statistics() -> Dict:
    """Get search statistics for today

    Returns:
        Dict: Statistics including searches, new_companies, dedup_rate
    """
    from datetime import date
    from sqlalchemy import func

    try:
        db = get_db()
        today = date.today()

        # Query all searches from today
        today_searches = db.query(SearchHistory).filter(
            func.date(SearchHistory.created_at) == today
        ).all()

        total_searches = len(today_searches)
        total_new = sum(s.new_count for s in today_searches)
        total_duplicates = sum(s.duplicate_count for s in today_searches)

        # Calculate dedup rate
        total = total_new + total_duplicates
        dedup_rate = (total_duplicates / total * 100) if total > 0 else 0

        return {
            "searches": total_searches,
            "new_companies": total_new,
            "dedup_rate": round(dedup_rate, 1)
        }
    except Exception as e:
        logger.error(f"Error getting today's statistics: {e}")
        return {
            "searches": 0,
            "new_companies": 0,
            "dedup_rate": 0
        }


# Phase 2+ Placeholder Functions


def insert_contact(data: Dict) -> int:
    """Insert contact (Phase 2+)

    Raises:
        NotImplementedError: This is Phase 2+ functionality
    """
    raise NotImplementedError("Contact management is Phase 2+ functionality")


def insert_email(data: Dict) -> int:
    """Insert email draft (Phase 2+)

    Raises:
        NotImplementedError: This is Phase 2+ functionality
    """
    raise NotImplementedError("Email drafting is Phase 2+ functionality")


__all__ = [
    "insert_company",
    "update_company",
    "get_companies_by_score",
    "get_companies_by_search",
    "insert_search_history",
    "get_search_history",
    "insert_contact",
    "insert_email",
]
