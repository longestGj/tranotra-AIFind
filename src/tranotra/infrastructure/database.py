"""Database initialization and management"""

from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional

from tranotra.core.models import Base, init_db_engine


def init_db(database_url: str = "sqlite:///./data/leads.db") -> None:
    """Initialize database and create tables

    Creates the ./data/ directory if missing, initializes the SQLite database,
    and creates all tables from SQLAlchemy models. Safe to call multiple times
    (idempotent).

    Args:
        database_url: SQLAlchemy database URL (default: local SQLite)

    Raises:
        Exception: If database initialization fails
    """
    # Create data directory if missing
    data_dir = Path("./data")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Initialize database engine and session maker
    init_db_engine(database_url)


def get_db() -> Session:
    """Get database session

    Returns:
        Session: SQLAlchemy session

    Raises:
        RuntimeError: If database not initialized
    """
    from tranotra.core.models import SessionLocal

    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return SessionLocal()


__all__ = ["init_db", "get_db"]
