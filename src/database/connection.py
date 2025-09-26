"""
Database connection management for ATS system
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from dotenv import load_dotenv
from config.logging_config import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("database.connection")

def get_database_url() -> str:
    """
    Construct database URL from environment variables
    
    Returns:
        Database URL string
    """
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    name = os.getenv('DB_NAME', 'ats_db')
    user = os.getenv('DB_USER', 'ats_user')
    password = os.getenv('DB_PASSWORD', '')
    
    if not password:
        logger.warning("Database password not set in environment variables")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"

def create_database_engine(echo: bool = False):
    """
    Create SQLAlchemy database engine
    
    Args:
        echo: Whether to echo SQL statements
        
    Returns:
        SQLAlchemy engine instance
    """
    try:
        database_url = get_database_url()
        engine = create_engine(
            database_url,
            echo=echo,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600    # Recycle connections every hour
        )
        logger.info("Database engine created successfully")
        return engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise

def test_database_connection() -> bool:
    """
    Test database connection
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        engine = create_database_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            logger.info(f"Database connection successful. PostgreSQL version: {version}")
            
            # Test TimescaleDB extension
            try:
                result = conn.execute(text("SELECT * FROM timescaledb_information.license LIMIT 1;"))
                license_info = result.fetchone()
                if license_info:
                    logger.info("TimescaleDB extension is available")
                else:
                    logger.warning("TimescaleDB extension not found")
            except SQLAlchemyError:
                logger.warning("TimescaleDB extension not installed or not accessible")
            
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def create_session_factory():
    """
    Create session factory for database operations
    
    Returns:
        SQLAlchemy session factory
    """
    engine = create_database_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db_session() -> Session:
    """
    Context manager for database sessions
    
    Yields:
        SQLAlchemy session
    """
    SessionLocal = create_session_factory()
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

def check_database_requirements() -> dict:
    """
    Check database requirements and configuration
    
    Returns:
        Dictionary with requirement check results
    """
    results = {
        'connection': False,
        'postgresql_version': None,
        'timescaledb_available': False,
        'timescaledb_version': None,
        'required_extensions': []
    }
    
    try:
        engine = create_database_engine()
        with engine.connect() as conn:
            # Check PostgreSQL version
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            results['postgresql_version'] = version
            results['connection'] = True
            logger.info(f"PostgreSQL version: {version}")
            
            # Check TimescaleDB
            try:
                result = conn.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';"))
                ts_version = result.fetchone()
                if ts_version:
                    results['timescaledb_available'] = True
                    results['timescaledb_version'] = ts_version[0]
                    logger.info(f"TimescaleDB version: {ts_version[0]}")
                else:
                    logger.warning("TimescaleDB extension not installed")
            except SQLAlchemyError as e:
                logger.warning(f"Could not check TimescaleDB: {e}")
            
            # Check for other required extensions
            try:
                result = conn.execute(text("SELECT extname FROM pg_extension;"))
                extensions = [row[0] for row in result.fetchall()]
                results['required_extensions'] = extensions
                logger.info(f"Available extensions: {extensions}")
            except SQLAlchemyError as e:
                logger.warning(f"Could not list extensions: {e}")
                
    except Exception as e:
        logger.error(f"Database requirements check failed: {e}")
    
    return results
