"""
Database setup and initialization script for ATS system
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config.logging_config import setup_logging, get_logger
from src.database.connection import get_database_url, check_database_requirements
from src.database.session import create_tables, get_db_session
from src.database.models import Signal
from datetime import datetime
from decimal import Decimal

# Initialize logging
setup_logging()
logger = get_logger("database.setup")

def create_database_and_user():
    """
    Create ATS database and user (requires superuser privileges)
    This function provides the SQL commands that need to be run manually
    """
    logger.info("Database and user creation commands:")
    
    sql_commands = """
    -- Connect to PostgreSQL as superuser (postgres)
    -- Run these commands in pgAdmin or psql:
    
    -- Create dedicated user for ATS
    CREATE USER ats_user WITH PASSWORD 'your_secure_password_here';
    
    -- Create database
    CREATE DATABASE ats_db OWNER ats_user;
    
    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE ats_db TO ats_user;
    
    -- Connect to ats_db database
    \\c ats_db
    
    -- Enable TimescaleDB extension
    CREATE EXTENSION IF NOT EXISTS timescaledb;
    
    -- Grant usage on schema
    GRANT USAGE ON SCHEMA public TO ats_user;
    GRANT CREATE ON SCHEMA public TO ats_user;
    """
    
    print(sql_commands)
    logger.info("Please run the above SQL commands manually in PostgreSQL")
    return sql_commands

def verify_database_setup():
    """
    Verify database setup and requirements
    
    Returns:
        True if setup is complete, False otherwise
    """
    logger.info("Verifying database setup...")
    
    try:
        requirements = check_database_requirements()
        
        print("\n=== Database Setup Verification ===")
        
        if requirements['connection']:
            print("✓ Database connection successful")
            print(f"  PostgreSQL version: {requirements['postgresql_version']}")
        else:
            print("✗ Database connection failed")
            return False
        
        if requirements['timescaledb_available']:
            print("✓ TimescaleDB extension available")
            print(f"  TimescaleDB version: {requirements['timescaledb_version']}")
        else:
            print("✗ TimescaleDB extension not available")
            print("  Please install TimescaleDB extension")
        
        if requirements['required_extensions']:
            print(f"✓ Available extensions: {', '.join(requirements['required_extensions'])}")
        
        # Test schema creation
        try:
            success = create_tables()
            if success:
                print("✓ Database schema created successfully")
            else:
                print("✗ Database schema creation failed")
                return False
        except Exception as e:
            print(f"✗ Database schema creation failed: {e}")
            return False
        
        # Test basic operations with Signal model
        try:
            with get_db_session() as session:
                # Test basic query
                result = session.execute(text("SELECT 1 as test;"))
                test_value = result.fetchone()[0]
                if test_value == 1:
                    print("✓ Database operations working")
                else:
                    print("✗ Database operations failed")
                    return False
                
                # Test Signal model operations
                test_signal = Signal(
                    timestamp=datetime.utcnow(),
                    pair_symbol='TEST/USDT',
                    signal_type='BUY',
                    predicted_reward=0.01,
                    signal_strength=0.75
                )
                
                session.add(test_signal)
                session.commit()
                print("✓ Signal model operations working")
                
                # Cleanup test signal
                session.delete(test_signal)
                session.commit()
                print("✓ Test signal cleaned up")
                
        except Exception as e:
            print(f"✗ Database operations test failed: {e}")
            return False
        
        # Test TimescaleDB hypertable
        try:
            engine = create_engine(get_database_url())
            with engine.connect() as conn:
                # Check if signals table is a hypertable
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM timescaledb_information.hypertables 
                    WHERE table_name = 'signals';
                """))
                
                hypertable = result.fetchone()
                if hypertable:
                    print("✓ Signals table is a TimescaleDB hypertable")
                else:
                    print("⚠️  Signals table is not a hypertable")
                    # Try to create hypertable
                    try:
                        conn.execute(text("SELECT create_hypertable('signals', 'timestamp', if_not_exists => TRUE);"))
                        conn.commit()
                        print("✓ Hypertable created successfully")
                    except Exception as e:
                        print(f"⚠️  Could not create hypertable: {e}")
                        
        except Exception as e:
            print(f"⚠️  TimescaleDB hypertable test failed: {e}")
        
        success = (requirements['connection'] and 
                  requirements['timescaledb_available'])
        
        if success:
            print("\n🎉 Database setup verification successful!")
            print("   Database schema is ready for ATS system")
        else:
            print("\n❌ Database setup incomplete. Please check the issues above.")
        
        return success
        
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        print(f"✗ Database verification failed: {e}")
        return False

def main():
    """
    Main database setup function
    """
    print("ATS Database Setup Script")
    print("=" * 40)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found. Please create one based on .env.example")
        print("   Make sure to set your database credentials:")
        print("   - DB_HOST=localhost")
        print("   - DB_PORT=5432") 
        print("   - DB_NAME=ats_db")
        print("   - DB_USER=ats_user")
        print("   - DB_PASSWORD=your_secure_password")
        return False
    
    print("1. Database and User Creation Commands:")
    create_database_and_user()
    
    print("\n2. After running the SQL commands above, press Enter to verify setup...")
    input()
    
    print("3. Verifying Database Setup:")
    success = verify_database_setup()
    
    if success:
        logger.info("Database setup completed successfully")
    else:
        logger.error("Database setup failed")
    
    return success

if __name__ == "__main__":
    main()
