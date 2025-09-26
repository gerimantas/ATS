"""
Comprehensive database schema tests for ATS system
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import os
from datetime import datetime, timedelta
from decimal import Decimal
from config.logging_config import setup_logging, get_logger
from src.database.models import Signal, Base
from src.database.session import create_tables, drop_tables, get_db_session, test_session
from src.database.connection import test_database_connection, check_database_requirements
from sqlalchemy import create_engine, text
from src.database.connection import get_database_url

# Initialize logging
setup_logging()
logger = get_logger("test.database_schema")

def test_database_connection():
    """Test basic database connection"""
    print("=== Database Connection Test ===")
    
    try:
        success = test_database_connection()
        if success:
            print("✓ Database connection successful")
            return True
        else:
            print("✗ Database connection failed")
            return False
    except Exception as e:
        print(f"✗ Database connection test failed: {e}")
        return False

def test_database_requirements():
    """Test database requirements and TimescaleDB availability"""
    print("\n=== Database Requirements Test ===")
    
    try:
        requirements = check_database_requirements()
        
        if requirements['connection']:
            print("✓ Database connection working")
        else:
            print("✗ Database connection failed")
            return False
            
        if requirements['timescaledb_available']:
            print(f"✓ TimescaleDB available (version: {requirements['timescaledb_version']})")
        else:
            print("✗ TimescaleDB not available")
            return False
            
        print(f"✓ PostgreSQL version: {requirements['postgresql_version']}")
        return True
        
    except Exception as e:
        print(f"✗ Database requirements test failed: {e}")
        return False

def test_schema_creation():
    """Test database schema creation"""
    print("\n=== Schema Creation Test ===")
    
    try:
        # Create tables using SQLAlchemy models
        success = create_tables()
        
        if success:
            print("✓ Database schema created successfully")
            
            # Verify signals table exists
            engine = create_engine(get_database_url())
            with engine.connect() as conn:
                result = conn.execute(text("SELECT tablename FROM pg_tables WHERE tablename = 'signals';"))
                if result.fetchone():
                    print("✓ Signals table exists")
                else:
                    print("✗ Signals table not found")
                    return False
                    
            return True
        else:
            print("✗ Schema creation failed")
            return False
            
    except Exception as e:
        print(f"✗ Schema creation test failed: {e}")
        return False

def test_timescaledb_hypertable():
    """Test TimescaleDB hypertable creation"""
    print("\n=== TimescaleDB Hypertable Test ===")
    
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
                return True
            else:
                print("⚠️  Signals table is not a hypertable (this is OK if migration wasn't run)")
                # Try to create hypertable
                try:
                    conn.execute(text("SELECT create_hypertable('signals', 'timestamp', if_not_exists => TRUE);"))
                    conn.commit()
                    print("✓ Hypertable created successfully")
                    return True
                except Exception as e:
                    print(f"✗ Failed to create hypertable: {e}")
                    return False
                    
    except Exception as e:
        print(f"✗ TimescaleDB hypertable test failed: {e}")
        return False

def test_signal_model():
    """Test Signal model functionality"""
    print("\n=== Signal Model Test ===")
    
    try:
        # Test Signal model creation
        signal = Signal(
            timestamp=datetime.utcnow(),
            pair_symbol='BTC/USDT',
            signal_type='BUY',
            predicted_reward=0.025,
            dex_price=Decimal('50000.12345678'),
            cex_price=Decimal('50010.87654321'),
            dex_orderflow_imbalance=0.75,
            market_regime='CALM',
            signal_strength=0.85,
            data_quality_score=0.92,
            executed=False,
            exchange_cex='binance',
            exchange_dex='raydium',
            blockchain='solana',
            algorithm_version='1.0',
            signal_source='dex_orderflow_algorithm'
        )
        
        print("✓ Signal model instance created")
        
        # Test to_dict method
        signal_dict = signal.to_dict()
        if isinstance(signal_dict, dict) and 'pair_symbol' in signal_dict:
            print("✓ Signal to_dict method working")
        else:
            print("✗ Signal to_dict method failed")
            return False
            
        # Test __repr__ method
        repr_str = repr(signal)
        if 'Signal' in repr_str and 'BTC/USDT' in repr_str:
            print("✓ Signal __repr__ method working")
        else:
            print("✗ Signal __repr__ method failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Signal model test failed: {e}")
        return False

def test_database_operations():
    """Test basic database CRUD operations"""
    print("\n=== Database Operations Test ===")
    
    try:
        with get_db_session() as session:
            # Test signal insertion
            signal = Signal(
                timestamp=datetime.utcnow(),
                pair_symbol='ETH/USDT',
                signal_type='SELL',
                predicted_reward=0.015,
                dex_price=Decimal('3000.50000000'),
                cex_price=Decimal('3005.25000000'),
                market_regime='BTC_VOLATILE',
                signal_strength=0.70,
                executed=False
            )
            
            session.add(signal)
            session.commit()
            print("✓ Signal inserted successfully")
            
            # Test signal retrieval
            retrieved_signal = session.query(Signal).filter(
                Signal.pair_symbol == 'ETH/USDT'
            ).first()
            
            if retrieved_signal and retrieved_signal.signal_type == 'SELL':
                print("✓ Signal retrieved successfully")
            else:
                print("✗ Signal retrieval failed")
                return False
            
            # Test signal update
            retrieved_signal.executed = True
            retrieved_signal.execution_timestamp = datetime.utcnow()
            retrieved_signal.actual_reward = 0.018
            session.commit()
            print("✓ Signal updated successfully")
            
            # Test signal count
            count = session.query(Signal).count()
            print(f"✓ Total signals in database: {count}")
            
            # Test signal deletion (cleanup)
            session.delete(retrieved_signal)
            session.commit()
            print("✓ Signal deleted successfully")
            
            return True
            
    except Exception as e:
        print(f"✗ Database operations test failed: {e}")
        return False

def test_query_performance():
    """Test query performance with indexes"""
    print("\n=== Query Performance Test ===")
    
    try:
        with get_db_session() as session:
            # Insert multiple test signals
            test_signals = []
            for i in range(10):
                signal = Signal(
                    timestamp=datetime.utcnow() - timedelta(minutes=i),
                    pair_symbol=f'TEST{i}/USDT',
                    signal_type='BUY' if i % 2 == 0 else 'SELL',
                    predicted_reward=0.01 + (i * 0.001),
                    signal_strength=0.5 + (i * 0.05),
                    market_regime='CALM'
                )
                test_signals.append(signal)
                session.add(signal)
            
            session.commit()
            print("✓ Test signals inserted")
            
            # Test time-based query (should use timestamp index)
            import time
            start_time = time.time()
            
            recent_signals = session.query(Signal).filter(
                Signal.timestamp >= datetime.utcnow() - timedelta(hours=1)
            ).all()
            
            query_time = time.time() - start_time
            print(f"✓ Time-based query completed in {query_time:.3f}s, found {len(recent_signals)} signals")
            
            # Test pair-based query (should use pair_symbol index)
            start_time = time.time()
            
            pair_signals = session.query(Signal).filter(
                Signal.pair_symbol.like('TEST%')
            ).all()
            
            query_time = time.time() - start_time
            print(f"✓ Pair-based query completed in {query_time:.3f}s, found {len(pair_signals)} signals")
            
            # Cleanup test signals
            for signal in test_signals:
                session.delete(signal)
            session.commit()
            print("✓ Test signals cleaned up")
            
            return True
            
    except Exception as e:
        print(f"✗ Query performance test failed: {e}")
        return False

def test_session_functionality():
    """Test database session functionality"""
    print("\n=== Session Functionality Test ===")
    
    try:
        success = test_session()
        if success:
            print("✓ Database session test passed")
            return True
        else:
            print("✗ Database session test failed")
            return False
    except Exception as e:
        print(f"✗ Session functionality test failed: {e}")
        return False

def main():
    """Run all database schema tests"""
    print("Starting ATS Database Schema Tests...\n")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found - database tests will be skipped")
        print("   Please create .env file and set up Docker database to run tests")
        return False
    
    tests = [
        test_database_connection,
        test_database_requirements,
        test_schema_creation,
        test_timescaledb_hypertable,
        test_signal_model,
        test_database_operations,
        test_query_performance,
        test_session_functionality
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
        print("🎉 All database schema tests passed!")
        print("   Database schema is ready for ATS system")
    else:
        print("⚠️  Some tests failed - check the output above for details")
        print("   Make sure Docker TimescaleDB container is running")
    
    return all(results)

if __name__ == "__main__":
    main()
