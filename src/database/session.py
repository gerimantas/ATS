"""
Database session management for ATS system
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from config.logging_config import get_logger
from .connection import get_database_url
from .models import Base

logger = get_logger("database.session")

# Create engine and session factory
engine = create_engine(get_database_url(), pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """
    Create all database tables defined in models
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return False


def drop_tables():
    """
    Drop all database tables (use with caution!)
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
        return True
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        return False


@contextmanager
def get_db_session() -> Session:
    """
    Context manager for database sessions with automatic commit/rollback

    Usage:
        with get_db_session() as session:
            # database operations
            signal = Signal(...)
            session.add(signal)
            # automatic commit on success, rollback on exception
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
        logger.debug("Database session committed successfully")
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error, rolling back: {e}")
        raise
    finally:
        session.close()
        logger.debug("Database session closed")


def get_session_factory():
    """
    Get the session factory for advanced usage

    Returns:
        SQLAlchemy session factory
    """
    return SessionLocal


def test_session():
    """
    Test database session functionality

    Returns:
        True if session test passes, False otherwise
    """
    try:
        with get_db_session() as session:
            # Test basic query
            result = session.execute(text("SELECT 1 as test;"))
            test_value = result.fetchone()[0]

            if test_value == 1:
                logger.info("Database session test passed")
                return True
            else:
                logger.error("Database session test failed: unexpected result")
                return False

    except Exception as e:
        logger.error(f"Database session test failed: {e}")
        return False
