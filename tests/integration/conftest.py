"""Integration test pytest configuration and fixtures"""

import os
import sys
from pathlib import Path

import pytest

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Set testing environment
os.environ["FLASK_ENV"] = "testing"

# Load API key from .env.development for real integration tests
# If not found, use dummy key for unit tests that mock the API
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / ".env.development"
if env_path.exists():
    load_dotenv(env_path)

# Only override if not already set by .env.development
if "GEMINI_API_KEY" not in os.environ or os.environ.get("GEMINI_API_KEY", "").startswith("test-"):
    # For real Gemini API integration tests, load from .env.development
    real_key = os.environ.get("GEMINI_API_KEY")
    if not real_key or real_key.startswith("test-"):
        # Fallback: use test-key-dummy-value
        os.environ["GEMINI_API_KEY"] = "test-key-dummy-value"


@pytest.fixture
def app():
    """Create Flask app for integration testing

    Yields:
        Flask: Test application instance
    """
    from tranotra.main import create_app

    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def db_session(app):
    """Create database session for integration testing

    Args:
        app: Flask application fixture

    Returns:
        Session: SQLAlchemy session for database operations
    """
    from tranotra.infrastructure.database import get_db

    with app.app_context():
        session = get_db()
        yield session
        try:
            session.expunge_all()
            session.close()
        except Exception:
            pass


@pytest.fixture
def sample_companies(db_session):
    """Create sample companies for integration testing

    Args:
        db_session: Database session fixture

    Yields:
        List: Sample company records
    """
    from tranotra.core.models import Company
    from tranotra.db import insert_company
    import time

    companies = []
    for i in range(5):
        # Use timestamp to ensure uniqueness
        unique_suffix = f"test_company_{i}_{int(time.time() * 1000)}"
        company_data = {
            "name": f"Test Company {i}",
            "country": "Vietnam" if i < 3 else "Thailand",
            "city": "Ho Chi Minh" if i < 3 else "Bangkok",
            "year_established": 2010 + i,
            "employees": f"{100 * (i + 1)}-{200 * (i + 1)}",
            "estimated_revenue": f"${10 * (i + 1)}M+",
            "main_products": f"Product {i}",
            "export_markets": "USA, ASEAN",
            "eu_us_jp_export": True if i % 2 == 0 else False,
            "raw_materials": f"Material {i}",
            "recommended_product": f"DOTP {i}",
            "recommendation_reason": f"Perfect fit for {i}",
            "website": f"company{unique_suffix}.com",
            "contact_email": f"contact{unique_suffix}@company.com",
            "linkedin_url": f"linkedin.com/company/{unique_suffix}",
            "linkedin_normalized": f"linkedin.com/company/{unique_suffix}",
            "best_contact_title": "Purchasing Manager",
            "prospect_score": 8 - i if i < 3 else 6 - i,
            "priority": "HIGH" if i < 2 else "MEDIUM" if i < 4 else "LOW",
            "source_query": "PVC manufacturer" if i < 3 else "Textile supplier"
        }
        company_id = insert_company(company_data)
        companies.append(company_id)

    yield companies

    # Cleanup - properly handle database resources
    try:
        db_session.query(Company).filter(Company.id.in_(companies)).delete()
        db_session.commit()
    except Exception as e:
        db_session.rollback()
    finally:
        db_session.expunge_all()


@pytest.fixture
def sample_companies_many(db_session):
    """Create many sample companies for pagination testing

    Args:
        db_session: Database session fixture

    Yields:
        List: Sample company IDs
    """
    from tranotra.core.models import Company
    from tranotra.db import insert_company

    companies = []
    for i in range(25):
        # Use timestamp to ensure uniqueness
        unique_suffix = f"large_company_test_{i}"
        company_data = {
            "name": f"Large Company {i}",
            "country": "Vietnam" if i % 2 == 0 else "Thailand",
            "city": "Ho Chi Minh" if i % 2 == 0 else "Bangkok",
            "year_established": 2015 + (i % 10),
            "employees": f"{100 * (i % 5 + 1)}-{200 * (i % 5 + 1)}",
            "estimated_revenue": f"${10 * (i % 10 + 1)}M+",
            "main_products": f"Product {i % 5}",
            "export_markets": "USA, ASEAN",
            "eu_us_jp_export": i % 2 == 0,
            "raw_materials": f"Material {i % 3}",
            "recommended_product": f"DOTP {i % 4}",
            "recommendation_reason": f"Perfect fit {i}",
            "website": f"company{unique_suffix}.com",
            "contact_email": f"contact{unique_suffix}@company.com",
            "linkedin_url": f"linkedin.com/company/{unique_suffix}",
            "linkedin_normalized": f"linkedin.com/company/{unique_suffix}",
            "best_contact_title": "Purchasing Manager",
            "prospect_score": (9 - (i % 9)) if i < 30 else (5 - (i % 5)),
            "priority": "HIGH" if i < 15 else "MEDIUM" if i < 35 else "LOW",
            "source_query": "Cable manufacturer"
        }
        try:
            company_id = insert_company(company_data)
            companies.append(company_id)
        except ValueError:
            # Skip duplicates
            pass

    yield companies

    # Cleanup - properly handle database resources
    try:
        db_session.query(Company).filter(Company.id.in_(companies)).delete()
        db_session.commit()
    except Exception as e:
        db_session.rollback()
    finally:
        db_session.expunge_all()


@pytest.fixture
def sample_companies_with_history(db_session, sample_companies):
    """Create sample companies with search history

    Args:
        db_session: Database session fixture
        sample_companies: Sample companies fixture

    Yields:
        Tuple: (companies, search_history_id)
    """
    from tranotra.db import insert_search_history

    history_data = {
        "country": "Vietnam",
        "query": "PVC manufacturer",
        "result_count": 15,
        "new_count": 12,
        "duplicate_count": 3,
        "avg_score": 8.1,
        "high_priority_count": 8
    }
    history_id = insert_search_history(history_data)

    yield sample_companies, history_id

    # Cleanup - properly handle database resources
    try:
        from tranotra.core.models import SearchHistory
        db_session.query(SearchHistory).filter_by(id=history_id).delete()
        db_session.commit()
    except Exception as e:
        db_session.rollback()
    finally:
        db_session.expunge_all()
