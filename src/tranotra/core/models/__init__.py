"""SQLAlchemy database models and session management"""

from threading import Lock
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Optional

# Declarative base for all models
Base = declarative_base()

# Global session maker (will be initialized per app)
SessionLocal: Optional[sessionmaker] = None
engine = None
_init_lock = Lock()


def init_db_engine(database_url: str):
    """Initialize database engine and session maker

    Thread-safe initialization to prevent race conditions in multi-worker deployments.

    Args:
        database_url: SQLAlchemy database URL
    """
    global engine, SessionLocal

    with _init_lock:
        # Avoid re-initialization if already done
        if SessionLocal is not None:
            return

        engine = create_engine(database_url, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Create all tables
        Base.metadata.create_all(bind=engine)


def get_db_session() -> Session:
    """Get a database session

    Returns:
        Session: SQLAlchemy session

    Raises:
        RuntimeError: If database not initialized
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db_engine() first.")
    return SessionLocal()


# Import models so they're registered with Base
from .company import Company
from .search_history import SearchHistory

__all__ = ["Base", "Company", "SearchHistory", "init_db_engine", "get_db_session", "Session", "SessionLocal"]
