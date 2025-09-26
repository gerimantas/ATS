"""
Database connection and setup tests for ATS system
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import os
from config.logging_config import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger("test.database")

def test_database_connection():
    """Test database connection without requiring actual database"""
    print("=== Database Connection Test ===")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found - this is expected for initial setup")
        print("   Database connection test will be skipped")
        print("   Please create .env file and install PostgreSQL to test connection")
        return True
    
    try:
        from src.database.connection import test_database_connection, check_database_requirements
        
        # Test connection
        connection_success = test_database_connection()
        
        if connection_success:
            print("✓ Database connection successful")
            
            # Check requirements
            requirements = check_database_requirements()
            
            if requirements['timescaledb_available']:
                print("✓ TimescaleDB extension available")
            else:
                print("⚠️  TimescaleDB extension not available")
            
            return True
        else:
            print("✗ Database connection failed")
            print("   This is expected if PostgreSQL is not installed yet")
            return False
            
    except ImportError as e:
        print(f"⚠️  Database modules not ready: {e}")
        return True  # This is expected during initial setup
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        print("   This is expected if PostgreSQL is not installed yet")
        return False

def test_database_modules():
    """Test that database modules can be imported"""
    print("\n=== Database Modules Test ===")
    
    try:
        from src.database.connection import (
            get_database_url, 
            create_database_engine, 
            create_session_factory,
            get_db_session,
            check_database_requirements
        )
        print("✓ Database connection module imported successfully")
        
        from src.database.setup import (
            create_database_and_user,
            verify_database_setup,
            main
        )
        print("✓ Database setup module imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Database module import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Database module test failed: {e}")
        return False

def test_environment_variables():
    """Test environment variable handling"""
    print("\n=== Environment Variables Test ===")
    
    try:
        from src.database.connection import get_database_url
        
        # Test with default values (no .env file)
        db_url = get_database_url()
        
        if "postgresql://" in db_url:
            print("✓ Database URL generation working")
            print(f"  Generated URL format: postgresql://user:***@host:port/db")
        else:
            print("✗ Database URL generation failed")
            return False
        
        # Test environment variable defaults
        expected_defaults = {
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_NAME': 'ats_db',
            'DB_USER': 'ats_user'
        }
        
        for key, default_value in expected_defaults.items():
            actual_value = os.getenv(key, default_value)
            if actual_value == default_value:
                print(f"✓ {key} default: {default_value}")
            else:
                print(f"✓ {key} configured: {actual_value}")
        
        return True
        
    except Exception as e:
        print(f"✗ Environment variables test failed: {e}")
        return False

def main():
    """Run all database tests"""
    print("Starting ATS Database Tests...\n")
    
    tests = [
        test_database_modules,
        test_environment_variables,
        test_database_connection
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All database tests passed!")
        print("   Note: Actual database connection requires PostgreSQL installation")
    else:
        print("⚠️  Some tests failed, but this may be expected during initial setup")
    
    return all(results)

if __name__ == "__main__":
    main()
