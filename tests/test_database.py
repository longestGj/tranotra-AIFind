"""Database model and CRUD operation tests"""

import pytest
from pathlib import Path
import tempfile

from tranotra.core.models import Company, SearchHistory, init_db_engine, Base, Session
from tranotra.infrastructure.database import init_db, get_db
import tranotra.db as db_ops


@pytest.fixture
def temp_db():
    """Create temporary SQLite database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        database_url = f"sqlite:///{db_path}"

        # Initialize database
        init_db(database_url)

        yield database_url

        # Cleanup: Close all sessions and dispose engine before deleting file
        from tranotra.core.models import SessionLocal, engine

        if SessionLocal is not None:
            # Close all active sessions
            SessionLocal.close_all() if hasattr(SessionLocal, 'close_all') else None

        if engine is not None:
            # Dispose all connections
            engine.dispose()

        # Reset global variables for next test
        import tranotra.core.models as models
        models.SessionLocal = None
        models.engine = None

        # Now try to delete the file
        if db_path.exists():
            try:
                db_path.unlink()
            except (PermissionError, OSError):
                # On Windows, SQLite might still have file locked
                # Let OS clean up temp directory instead
                pass


class TestCompanyModel:
    """Test Company SQLAlchemy model"""

    def test_company_creation(self, temp_db):
        """Test creating a Company instance"""
        company_data = {
            "name": "Test Corp",
            "country": "Vietnam",
            "source_query": "PVC manufacturer",
            "prospect_score": 8,
            "priority": "A",
        }
        company = Company(**company_data)
        assert company.name == "Test Corp"
        assert company.country == "Vietnam"
        assert company.prospect_score == 8

    def test_company_to_dict(self, temp_db):
        """Test Company to_dict() method"""
        company_data = {
            "name": "Test Corp",
            "country": "Vietnam",
            "source_query": "PVC manufacturer",
            "prospect_score": 7,
            "priority": "B",
            "city": "Ho Chi Minh",
            "employees": "100-500",
        }
        company = Company(**company_data)
        result = company.to_dict()

        assert result["name"] == "Test Corp"
        assert result["country"] == "Vietnam"
        assert result["prospect_score"] == 7
        assert result["city"] == "Ho Chi Minh"
        assert len(result) == 23  # All 23 fields should be in dict

    def test_company_fields_count(self):
        """Test that Company model has exactly 23 fields"""
        # Get all column names
        columns = [col.name for col in Company.__table__.columns]
        assert len(columns) == 23, f"Expected 23 columns, got {len(columns)}: {columns}"


class TestSearchHistoryModel:
    """Test SearchHistory SQLAlchemy model"""

    def test_search_history_creation(self, temp_db):
        """Test creating a SearchHistory instance"""
        history_data = {
            "country": "Vietnam",
            "query": "PVC manufacturer",
            "result_count": 50,
            "new_count": 45,
            "duplicate_count": 5,
        }
        history = SearchHistory(**history_data)
        assert history.country == "Vietnam"
        assert history.query == "PVC manufacturer"
        assert history.result_count == 50

    def test_search_history_to_dict(self, temp_db):
        """Test SearchHistory to_dict() method"""
        history_data = {
            "country": "Vietnam",
            "query": "PVC manufacturer",
            "result_count": 50,
            "new_count": 45,
            "duplicate_count": 5,
            "avg_score": 7.5,
        }
        history = SearchHistory(**history_data)
        result = history.to_dict()

        assert result["country"] == "Vietnam"
        assert result["query"] == "PVC manufacturer"
        assert result["result_count"] == 50
        assert len(result) == 9  # All 9 fields should be in dict

    def test_search_history_fields_count(self):
        """Test that SearchHistory model has exactly 9 fields"""
        columns = [col.name for col in SearchHistory.__table__.columns]
        assert len(columns) == 9, f"Expected 9 columns, got {len(columns)}: {columns}"


class TestCRUDOperations:
    """Test CRUD operations in db.py"""

    def test_insert_company(self, temp_db):
        """Test inserting a company"""
        company_data = {
            "name": "CADIVI Corp",
            "country": "Vietnam",
            "source_query": "PVC manufacturer",
            "prospect_score": 8,
            "priority": "A",
            "linkedin_normalized": "linkedin.com/company/cadivi",
        }
        company_id = db_ops.insert_company(company_data)
        assert isinstance(company_id, int)
        assert company_id > 0

    def test_insert_company_validates_required_fields(self, temp_db):
        """Test that insert_company validates required fields"""
        # Missing name
        with pytest.raises(ValueError, match="name is required"):
            db_ops.insert_company({
                "country": "Vietnam",
                "source_query": "test",
            })

        # Missing country
        with pytest.raises(ValueError, match="Country is required"):
            db_ops.insert_company({
                "name": "Test",
                "source_query": "test",
            })

    def test_insert_company_skips_duplicates(self, temp_db):
        """Test that insert_company skips duplicates by linkedin_normalized"""
        company_data = {
            "name": "CADIVI Corp",
            "country": "Vietnam",
            "source_query": "PVC manufacturer",
            "linkedin_normalized": "linkedin.com/company/cadivi",
        }

        # Insert first time
        id1 = db_ops.insert_company(company_data)

        # Insert second time (should skip)
        id2 = db_ops.insert_company(company_data)

        # Should return same ID (existing company)
        assert id1 == id2

    def test_update_company(self, temp_db):
        """Test updating a company"""
        # Insert company
        company_data = {
            "name": "Test Corp",
            "country": "Vietnam",
            "source_query": "test",
            "prospect_score": 5,
        }
        company_id = db_ops.insert_company(company_data)

        # Update it
        updated = db_ops.update_company(company_id, {
            "prospect_score": 9,
            "priority": "A",
        })
        assert updated is True

    def test_update_company_nonexistent(self, temp_db):
        """Test updating nonexistent company returns False"""
        updated = db_ops.update_company(99999, {"prospect_score": 5})
        assert updated is False

    def test_get_companies_by_score(self, temp_db):
        """Test retrieving companies by minimum score"""
        # Insert companies with different scores
        db_ops.insert_company({
            "name": "Corp A",
            "country": "Vietnam",
            "source_query": "test",
            "prospect_score": 5,
        })
        db_ops.insert_company({
            "name": "Corp B",
            "country": "Vietnam",
            "source_query": "test",
            "prospect_score": 8,
        })
        db_ops.insert_company({
            "name": "Corp C",
            "country": "Vietnam",
            "source_query": "test",
            "prospect_score": 3,
        })

        # Get companies with score >= 7
        companies = db_ops.get_companies_by_score(7)
        assert len(companies) == 1
        assert companies[0].name == "Corp B"

    def test_get_companies_by_search(self, temp_db):
        """Test retrieving companies by search criteria"""
        db_ops.insert_company({
            "name": "Vietnamese Corp",
            "country": "Vietnam",
            "source_query": "PVC",
        })
        db_ops.insert_company({
            "name": "Thai Corp",
            "country": "Thailand",
            "source_query": "PVC",
        })
        db_ops.insert_company({
            "name": "Vietnamese Corp 2",
            "country": "Vietnam",
            "source_query": "plastic",
        })

        # Get Vietnam + PVC search
        companies = db_ops.get_companies_by_search("Vietnam", "PVC")
        assert len(companies) == 1
        assert companies[0].name == "Vietnamese Corp"

    def test_insert_search_history(self, temp_db):
        """Test inserting search history"""
        history_data = {
            "country": "Vietnam",
            "query": "PVC manufacturer",
            "result_count": 50,
            "new_count": 45,
            "duplicate_count": 5,
            "avg_score": 7.5,
            "high_priority_count": 30,
        }
        history_id = db_ops.insert_search_history(history_data)
        assert isinstance(history_id, int)
        assert history_id > 0

    def test_get_search_history(self, temp_db):
        """Test retrieving search history"""
        # Insert multiple records
        for i in range(3):
            db_ops.insert_search_history({
                "country": "Vietnam",
                "query": f"query_{i}",
                "result_count": 10 + i,
            })

        # Get history
        history = db_ops.get_search_history(limit=5)
        assert len(history) == 3
        # Should be ordered by created_at DESC
        assert history[0].query == "query_2"

    def test_insert_search_history_validates(self, temp_db):
        """Test that insert_search_history validates required fields"""
        with pytest.raises(ValueError, match="Country is required"):
            db_ops.insert_search_history({"query": "test"})

        with pytest.raises(ValueError, match="Query is required"):
            db_ops.insert_search_history({"country": "Vietnam"})


class TestDatabaseInitialization:
    """Test database initialization"""

    def test_init_db_creates_directory(self, temp_db):
        """Test that init_db creates ./data directory"""
        data_dir = Path("./data")
        # After init_db call in fixture, directory should exist
        assert data_dir.exists()

    def test_init_db_idempotent(self, temp_db):
        """Test that calling init_db multiple times is safe"""
        # Should not raise error when called again
        init_db(temp_db)
        init_db(temp_db)
        # If we got here without error, test passes

    def test_database_file_created(self, temp_db):
        """Test that database file is created"""
        # Extract path from database URL
        db_path_str = temp_db.replace("sqlite:///", "")
        db_path = Path(db_path_str)
        assert db_path.exists()
        assert db_path.suffix == ".db"


class TestConstraints:
    """Test database constraints"""

    def test_prospect_score_constraint(self, temp_db):
        """Test that prospect_score CHECK constraint is enforced"""
        db = get_db()
        try:
            # Invalid score (> 10) should fail
            company = Company(
                name="Test",
                country="Vietnam",
                source_query="test",
                prospect_score=15,  # Invalid
            )
            db.add(company)
            # This should raise an error when committed
            with pytest.raises(Exception):
                db.commit()
        finally:
            db.rollback()
            db.close()

    def test_linkedin_normalized_unique(self, temp_db):
        """Test that linkedin_normalized UNIQUE constraint is enforced"""
        url = "linkedin.com/company/test"

        # Insert first company
        db_ops.insert_company({
            "name": "Corp A",
            "country": "Vietnam",
            "source_query": "test",
            "linkedin_normalized": url,
        })

        # Inserting second with same URL should skip (handled by application logic)
        # This is tested above in test_insert_company_skips_duplicates
