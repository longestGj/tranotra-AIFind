"""SQLAlchemy database models and session management"""

import os
from threading import Lock
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool
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
    For SQLite in test mode, uses StaticPool to avoid connection pool exhaustion.

    Args:
        database_url: SQLAlchemy database URL
    """
    global engine, SessionLocal

    with _init_lock:
        # Avoid re-initialization if already done
        if SessionLocal is not None:
            return

        # Use StaticPool for SQLite in testing to avoid pool exhaustion
        is_test_mode = os.environ.get("FLASK_ENV") == "testing"
        is_sqlite = "sqlite" in database_url.lower()

        if is_test_mode and is_sqlite:
            # StaticPool: one connection, reused for all threads
            engine = create_engine(
                database_url,
                echo=False,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False}
            )
        else:
            # Production: normal QueuePool with configurable size
            engine = create_engine(database_url, echo=False, pool_pre_ping=True)

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
