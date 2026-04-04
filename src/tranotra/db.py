"""Database layer with CRUD operations for Company and SearchHistory"""

from typing import List, Dict, Optional
import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
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


def get_companies_paginated(
    country: Optional[str] = None,
    query: Optional[str] = None,
    page: int = 1,
    per_page: int = 20
) -> Dict:
    """Get paginated company results with optional filtering

    Args:
        country: Optional country filter
        query: Optional search keyword filter
        page: Page number (1-indexed, default=1)
        per_page: Results per page (default=20, max=100)

    Returns:
        Dict containing:
            - total: Total number of matching companies
            - total_pages: Total number of pages
            - current_page: Current page number
            - per_page: Results per page
            - companies: List of company dicts (23 fields each)
            - new_count: Count of new companies (from search_history)
            - duplicate_count: Count of duplicates (from search_history)
            - avg_score: Average prospect score (from search_history)
    """
    db = get_db()
    try:
        # Validate pagination parameters
        page = max(1, int(page))
        per_page = min(100, max(1, int(per_page)))

        # Build base query
        query_obj = db.query(Company)

        # Apply filters if provided
        if country:
            query_obj = query_obj.filter(Company.country == country)
        if query:
            query_obj = query_obj.filter(Company.source_query == query)

        # Get total count before pagination
        total_count = query_obj.count()

        # Calculate pagination
        offset = max(0, (page - 1) * per_page)
        if total_count == 0:
            total_pages = 1
        else:
            total_pages = (total_count + per_page - 1) // per_page

        # Get paginated results, sorted by score descending (handle NULLs)
        # Use COALESCE to treat NULL scores as 0 for consistent sorting
        companies = query_obj.order_by(
            func.coalesce(Company.prospect_score, 0).desc()
        ).offset(offset).limit(per_page).all()

        # Convert to dicts
        companies_data = []
        for company in companies:
            companies_data.append({
                "id": company.id,
                "name": company.name,
                "country": company.country,
                "city": company.city,
                "year_established": company.year_established,
                "employees": company.employees,
                "estimated_revenue": company.estimated_revenue,
                "main_products": company.main_products,
                "export_markets": company.export_markets,
                "eu_us_jp_export": company.eu_us_jp_export,
                "raw_materials": company.raw_materials,
                "recommended_product": company.recommended_product,
                "recommendation_reason": company.recommendation_reason,
                "website": company.website,
                "contact_email": company.contact_email,
                "linkedin_url": company.linkedin_url,
                "linkedin_normalized": company.linkedin_normalized,
                "best_contact_title": company.best_contact_title,
                "prospect_score": company.prospect_score,
                "priority": company.priority,
                "source_query": company.source_query,
                "created_at": company.created_at.isoformat() if company.created_at else None,
                "updated_at": company.updated_at.isoformat() if company.updated_at else None,
            })

        # Get search history stats if filters provided
        new_count = 0
        duplicate_count = 0
        avg_score = 0.0

        if country and query:
            history = db.query(SearchHistory).filter(
                SearchHistory.country == country,
                SearchHistory.query == query
            ).order_by(SearchHistory.created_at.desc()).first()

            if history:
                new_count = history.new_count or 0
                duplicate_count = history.duplicate_count or 0
                avg_score = round(history.avg_score or 0.0, 1)

        logger.info(f"Retrieved {len(companies_data)} companies (page {page}/{total_pages}) for filters: country={country}, query={query}")

        return {
            "total": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": per_page,
            "companies": companies_data,
            "new_count": new_count,
            "duplicate_count": duplicate_count,
            "avg_score": avg_score,
        }

    except Exception as e:
        logger.error(f"Error retrieving paginated companies: {e}")
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


# Parsing and Insertion Pipeline (Story 1-5)


def parse_response_and_insert(
    country: str,
    query: str,
    response: str,
    format: str
) -> Dict:
    """Parse Gemini response and insert companies into database

    Args:
        country: Country from search request
        query: Search keyword from request
        response: Raw response from Gemini API
        format: Response format ("JSON", "Markdown", or "CSV")

    Returns:
        Dict with insertion results:
        {
            "success": bool,
            "new_count": int,
            "duplicate_count": int,
            "error_count": int,
            "avg_score": float,
            "high_priority_count": int,
            "message": str
        }
    """
    from tranotra.parser import CompanyParser

    db = get_db()
    parser = CompanyParser()

    result = {
        "success": False,
        "new_count": 0,
        "duplicate_count": 0,
        "error_count": 0,
        "avg_score": 0.0,
        "high_priority_count": 0,
        "message": ""
    }

    try:
        # Parse response into company records
        parsed_companies = parser.parse_response(response, format)
        if not parsed_companies:
            result["message"] = "解析失败：返回数据为空"
            logger.error(f"Empty response from {format} parser")
            return result

        logger.info(f"Parsed {len(parsed_companies)} companies from {format} response")

        # Filter and prepare records
        prepared_companies = parser._filter_and_prepare_records(parsed_companies)
        if not prepared_companies:
            result["message"] = "解析失败：没有有效的公司记录"
            logger.error("No valid companies after filtering")
            return result

        # Process companies: check for duplicates and insert
        new_companies = []
        scores_for_avg = []

        try:
            for company_data in prepared_companies:
                linkedin_normalized = company_data.get("linkedin_normalized", "")

                # Check for duplicate by linkedin_normalized
                if linkedin_normalized:
                    existing = db.query(Company).filter_by(
                        linkedin_normalized=linkedin_normalized
                    ).first()

                    if existing:
                        result["duplicate_count"] += 1
                        logger.info(f"跳过重复: {company_data.get('name')}")
                        continue

                # Insert new company
                try:
                    company_data["source_query"] = query
                    company_id = insert_company(company_data)
                    result["new_count"] += 1
                    new_companies.append(company_data)

                    # Collect score for average calculation
                    score = company_data.get("prospect_score", 0)
                    if isinstance(score, int) and 1 <= score <= 10:
                        scores_for_avg.append(score)

                    logger.info(f"插入新公司: {company_data.get('name')}")

                except ValueError as e:
                    result["error_count"] += 1
                    logger.error(f"插入失败 {company_data.get('name')}: {e}")
                    continue

            # Calculate statistics for search history
            if scores_for_avg:
                result["avg_score"] = round(sum(scores_for_avg) / len(scores_for_avg), 1)
                result["high_priority_count"] = sum(1 for s in scores_for_avg if s >= 8)
            else:
                result["avg_score"] = 0.0
                result["high_priority_count"] = 0

            # Create search history record (must succeed or rollback all)
            total_count = len(parsed_companies)
            history_data = {
                "country": country,
                "query": query,
                "result_count": total_count,
                "new_count": result["new_count"],
                "duplicate_count": result["duplicate_count"],
                "avg_score": result["avg_score"],
                "high_priority_count": result["high_priority_count"]
            }

            # Insert search history - any failure here will trigger rollback
            insert_search_history(history_data)
            logger.info(
                f"创建搜索历史: {country}/{query} "
                f"(新增{result['new_count']}, 重复{result['duplicate_count']})"
            )

            # Commit all changes (companies + search history)
            db.commit()

            # Build result message
            result["success"] = True
            result["message"] = (
                f"处理 {total_count} 条结果，"
                f"新增 {result['new_count']} 条，"
                f"重复 {result['duplicate_count']} 条"
            )

            logger.info(f"Parse and insert complete: {result['message']}")

        except Exception as e:
            db.rollback()
            logger.error(f"Error during insertion pipeline: {e}")
            result["message"] = "数据保存失败，请稍后重试"
            result["error_count"] += 1
            return result

    except ValueError as e:
        logger.error(f"Parser error: {e}")
        result["message"] = f"搜索失败：{str(e)}"
        result["error_count"] += 1
    except Exception as e:
        logger.error(f"Unexpected error in parse_response_and_insert: {e}")
        result["message"] = "搜索失败，请稍后重试"
        result["error_count"] += 1

    return result


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


def get_today_statistics() -> Dict:
    """Get search statistics for today

    Returns:
        Dict: Statistics including searches, new_companies, dedup_rate

    Raises:
        RuntimeError: If database session cannot be obtained
    """
    from datetime import datetime, date
    from sqlalchemy import func

    try:
        session = get_db()
        today = date.today()

        # Query all searches from today
        today_searches = session.query(SearchHistory).filter(
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


__all__ = [
    "insert_company",
    "update_company",
    "get_companies_by_score",
    "get_companies_by_search",
    "get_companies_paginated",
    "insert_search_history",
    "get_search_history",
    "get_today_statistics",
    "parse_response_and_insert",
    "insert_contact",
    "insert_email",
    "get_today_statistics",
]
