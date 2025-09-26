"""
Tests for Data Synchronization Manager functionality
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import asyncio
import time
from datetime import datetime, timedelta
from config.logging_config import setup_logging, get_logger
from src.data.sync_manager import DataSyncManager
from src.data.cex_connector import CEXConnector
from src.data.dex_connector import DEXConnector

# Initialize logging
setup_logging()
logger = get_logger("test.sync_manager")

class MockConnector:
    """Mock connector for testing"""
    
    def __init__(self, name: str, connector_type: str = "CEXConnector"):
        self.name = name
        self.connector_type = connector_type
        self.data = {
            'orderbook': {
                'bids': [[50000, 1.0], [49999, 0.5]],
                'asks': [[50001, 1.0], [50002, 0.5]],
                'timestamp': int(time.time() * 1000)
            },
            'trades': [
                {'price': 50000, 'amount': 0.1, 'timestamp': int(time.time() * 1000)},
                {'price': 50001, 'amount': 0.05, 'timestamp': int(time.time() * 1000) - 1000}
            ],
            'price': {'value': 50000, 'timestamp': int(time.time() * 1000)},
            'liquidity': {'liquidity': 1000000, 'volume24h': 500000}
        }
    
    def get_orderbook(self, symbol: str):
        """Mock orderbook data"""
        return self.data['orderbook']
    
    def get_trades(self, symbol: str, limit: int = 50):
        """Mock trades data"""
        return self.data['trades'][:limit]
    
    def get_stored_trades(self, symbol: str, limit: int = 50):
        """Mock stored trades data"""
        return self.data['trades'][:limit]
    
    def get_stored_price(self, symbol: str):
        """Mock price data"""
        return self.data['price']
    
    def get_stored_liquidity(self, symbol: str):
        """Mock liquidity data"""
        return self.data['liquidity']

def test_sync_manager_initialization():
    """Test sync manager initialization"""
    print("=== Sync Manager Initialization Test ===")
    
    try:
        sync_manager = DataSyncManager()
        
        # Check initial state
        if (hasattr(sync_manager, 'sync_tasks') and 
            hasattr(sync_manager, 'connectors') and
            hasattr(sync_manager, 'sync_intervals')):
            print("✓ Sync manager initialized successfully")
            print(f"  Sync intervals: {sync_manager.sync_intervals}")
            print(f"  Latency compensation enabled: {sync_manager.latency_compensation['enabled']}")
            return True
        else:
            print("✗ Sync manager initialization failed - missing attributes")
            return False
            
    except Exception as e:
        print(f"✗ Sync manager initialization failed: {e}")
        return False

def test_connector_management():
    """Test adding and managing connectors"""
    print("\n=== Connector Management Test ===")
    
    try:
        sync_manager = DataSyncManager()
        
        # Add mock connectors
        cex_connector = MockConnector("binance", "CEXConnector")
        dex_connector = MockConnector("birdeye", "DEXConnector")
        
        sync_manager.add_connector("binance_cex", cex_connector)
        sync_manager.add_connector("birdeye_dex", dex_connector)
        
        # Check connectors were added
        if len(sync_manager.connectors) == 2:
            print("✓ Connectors added successfully")
            print(f"  Total connectors: {len(sync_manager.connectors)}")
        else:
            print(f"✗ Expected 2 connectors, got {len(sync_manager.connectors)}")
            return False
        
        # Check sync health initialization
        health = sync_manager.get_sync_health()
        if len(health) == 2 and all(h['status'] == 'inactive' for h in health.values()):
            print("✓ Sync health initialized correctly")
        else:
            print("✗ Sync health initialization failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Connector management test failed: {e}")
        return False

async def test_data_synchronization():
    """Test basic data synchronization"""
    print("\n=== Data Synchronization Test ===")
    
    try:
        sync_manager = DataSyncManager()
        
        # Add mock connectors
        cex_connector = MockConnector("binance", "CEXConnector")
        dex_connector = MockConnector("birdeye", "DEXConnector")
        
        sync_manager.add_connector("binance_cex", cex_connector)
        sync_manager.add_connector("birdeye_dex", dex_connector)
        
        # Start sync for a short period
        await sync_manager.start_sync("BTC/USDT", ["price"])
        
        # Wait for some sync cycles
        await asyncio.sleep(2)
        
        # Check if data was synchronized
        synced_data = sync_manager.get_synchronized_data("BTC/USDT", "price")
        
        if synced_data and 'data' in synced_data:
            print("✓ Data synchronization working")
            print(f"  Sources: {synced_data['source_count']}")
            print(f"  Sync timestamp: {synced_data['sync_timestamp']}")
        else:
            print("✗ No synchronized data found")
            await sync_manager.stop_all_sync()
            return False
        
        # Check data quality
        quality = sync_manager.get_data_quality("BTC/USDT")
        if quality:
            print("✓ Data quality tracking working")
            for key, score in quality.items():
                print(f"  {key}: {score['overall_quality']:.2f}")
        
        # Stop sync
        await sync_manager.stop_all_sync()
        return True
        
    except Exception as e:
        print(f"✗ Data synchronization test failed: {e}")
        return False

def test_latency_compensation():
    """Test latency compensation functionality"""
    print("\n=== Latency Compensation Test ===")
    
    try:
        sync_manager = DataSyncManager()
        
        # Test compensation calculation
        test_results = {
            'connector1': {
                'data': {'price': 50000},
                'timestamp': datetime.utcnow(),
                'latency_ms': 100,
                'connector_type': 'CEXConnector'
            },
            'connector2': {
                'data': {'price': 50001},
                'timestamp': datetime.utcnow(),
                'latency_ms': 200,
                'connector_type': 'DEXConnector'
            }
        }
        
        # Apply compensation
        compensated = sync_manager._apply_latency_compensation(test_results)
        
        # Check compensation was applied
        if all('compensated_timestamp' in result for result in compensated.values()):
            print("✓ Latency compensation applied successfully")
            
            # Check compensation amounts
            for name, result in compensated.items():
                compensation = result['compensation_ms']
                print(f"  {name}: {compensation}ms compensation")
        else:
            print("✗ Latency compensation not applied")
            return False
        
        # Test compensation stats
        stats = sync_manager.get_compensation_stats()
        if stats['enabled']:
            print("✓ Compensation statistics working")
            print(f"  Compensations applied: {stats['compensations_applied']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Latency compensation test failed: {e}")
        return False

def test_data_quality_calculation():
    """Test data quality calculation"""
    print("\n=== Data Quality Calculation Test ===")
    
    try:
        sync_manager = DataSyncManager()
        
        # Test with good data
        good_results = {
            'connector1': {
                'data': {'price': 50000},
                'timestamp': datetime.utcnow(),
                'latency_ms': 50,
                'connector_type': 'CEXConnector'
            }
        }
        
        quality_scores = sync_manager._calculate_sync_quality(good_results)
        
        if quality_scores['connector1'] > 0.8:
            print(f"✓ Good data quality calculation working - score: {quality_scores['connector1']:.2f}")
        else:
            print(f"✗ Good data quality calculation failed - score: {quality_scores['connector1']:.2f}")
            return False
        
        # Test with bad data (high latency)
        bad_results = {
            'connector2': {
                'data': {'price': 50000},
                'timestamp': datetime.utcnow() - timedelta(seconds=60),  # Old timestamp
                'latency_ms': 2000,  # High latency
                'connector_type': 'CEXConnector'
            }
        }
        
        bad_quality_scores = sync_manager._calculate_sync_quality(bad_results)
        
        if bad_quality_scores['connector2'] < 0.5:
            print(f"✓ Bad data quality detection working - score: {bad_quality_scores['connector2']:.2f}")
        else:
            print(f"✗ Bad data quality detection failed - score: {bad_quality_scores['connector2']:.2f}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Data quality calculation test failed: {e}")
        return False

def test_sync_health_monitoring():
    """Test sync health monitoring"""
    print("\n=== Sync Health Monitoring Test ===")
    
    try:
        sync_manager = DataSyncManager()
        
        # Add a connector
        sync_manager.add_connector("test_connector", MockConnector("test"))
        
        # Test successful sync health update
        sync_manager._update_sync_health("test_connector_price", True)
        
        health = sync_manager.get_sync_health()
        
        if health['test_connector']['status'] == 'active':
            print("✓ Sync health monitoring working")
            print(f"  Status: {health['test_connector']['status']}")
            print(f"  Success count: {health['test_connector']['success_count']}")
        else:
            print("✗ Sync health monitoring failed")
            return False
        
        # Test error handling
        for i in range(6):  # Trigger error status
            sync_manager._update_sync_health("test_connector_price", False)
        
        health = sync_manager.get_sync_health()
        
        if health['test_connector']['status'] == 'error':
            print("✓ Error detection working")
            print(f"  Error count: {health['test_connector']['error_count']}")
        else:
            print("✗ Error detection failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Sync health monitoring test failed: {e}")
        return False

def test_data_freshness():
    """Test data freshness tracking"""
    print("\n=== Data Freshness Test ===")
    
    try:
        sync_manager = DataSyncManager()
        
        # Test fresh data
        symbol = "BTC/USDT"
        data_type = "price"
        
        # Manually set fresh data
        key = f"{symbol}_{data_type}"
        sync_manager.data_freshness[key] = datetime.utcnow()
        
        is_stale = sync_manager.is_data_stale(symbol, data_type)
        
        if not is_stale:
            print("✓ Fresh data detection working")
        else:
            print("✗ Fresh data detection failed")
            return False
        
        # Test stale data
        sync_manager.data_freshness[key] = datetime.utcnow() - timedelta(seconds=120)  # 2 minutes old
        
        is_stale = sync_manager.is_data_stale(symbol, data_type)
        
        if is_stale:
            print("✓ Stale data detection working")
        else:
            print("✗ Stale data detection failed")
            return False
        
        # Test freshness info
        freshness = sync_manager.get_data_freshness(symbol)
        
        if freshness and key in freshness:
            print("✓ Data freshness tracking working")
            print(f"  Last update: {freshness[key]}")
        else:
            print("✗ Data freshness tracking failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Data freshness test failed: {e}")
        return False

def test_sync_summary():
    """Test sync summary functionality"""
    print("\n=== Sync Summary Test ===")
    
    try:
        sync_manager = DataSyncManager()
        
        # Add connectors
        sync_manager.add_connector("binance_cex", MockConnector("binance"))
        sync_manager.add_connector("birdeye_dex", MockConnector("birdeye"))
        
        # Get summary
        summary = sync_manager.get_sync_summary()
        
        expected_fields = [
            'active_tasks', 'total_connectors', 'healthy_connectors',
            'health_percentage', 'average_quality', 'average_latency_ms',
            'compensation_enabled', 'data_types_synced', 'symbols_synced'
        ]
        
        if all(field in summary for field in expected_fields):
            print("✓ Sync summary working")
            print(f"  Total connectors: {summary['total_connectors']}")
            print(f"  Health percentage: {summary['health_percentage']:.1f}%")
            print(f"  Compensation enabled: {summary['compensation_enabled']}")
        else:
            print("✗ Sync summary missing fields")
            return False
        
        # Test string representation
        repr_str = str(sync_manager)
        
        if "DataSyncManager" in repr_str:
            print("✓ String representation working")
            print(f"  Repr: {repr_str}")
        else:
            print("✗ String representation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Sync summary test failed: {e}")
        return False

async def main():
    """Run all sync manager tests"""
    print("Starting Data Sync Manager Tests...\n")
    
    tests = [
        test_sync_manager_initialization,
        test_connector_management,
        test_latency_compensation,
        test_data_quality_calculation,
        test_sync_health_monitoring,
        test_data_freshness,
        test_sync_summary,
        test_data_synchronization
    ]
    
    results = []
    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 All sync manager tests passed!")
    else:
        print("⚠️  Some tests failed - check the output above for details")
    
    return all(results)

if __name__ == "__main__":
    asyncio.run(main())
