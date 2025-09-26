"""
Tests for CEX connector functionality
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import asyncio
import os
import time
from config.logging_config import setup_logging, get_logger
from src.data.cex_connector import CEXConnector

# Initialize logging
setup_logging()
logger = get_logger("test.cex_connector")

async def test_cex_connector_initialization():
    """Test CEX connector initialization"""
    print("=== CEX Connector Initialization Test ===")
    
    try:
        # Test with Binance (most commonly supported)
        connector = CEXConnector('binance', sandbox=True)
        
        if connector.exchange_id == 'binance':
            print("✓ CEX connector initialized successfully")
            print(f"  Exchange: {connector.exchange_id}")
            print(f"  Sandbox mode: {connector.sandbox}")
            return True
        else:
            print("✗ CEX connector initialization failed")
            return False
            
    except Exception as e:
        print(f"✗ CEX connector initialization failed: {e}")
        return False

async def test_connection():
    """Test exchange connection (requires internet)"""
    print("\n=== Exchange Connection Test ===")
    
    try:
        connector = CEXConnector('binance', sandbox=True)
        
        # Test connection
        connected = await connector.connect()
        
        if connected:
            print("✓ Exchange connection successful")
            
            # Check connection status
            status = connector.get_connection_status()
            if status.get('binance', {}).get('connected'):
                print("✓ Connection status verified")
                print(f"  Markets loaded: {status['binance'].get('markets_count', 0)}")
            else:
                print("✗ Connection status check failed")
                return False
                
            # Cleanup
            await connector.close()
            return True
        else:
            print("✗ Exchange connection failed")
            print("  This may be expected if no internet connection or API issues")
            return False
            
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        print("  This may be expected if no internet connection or CCXT Pro not available")
        return False

async def test_orderbook_subscription():
    """Test orderbook subscription (requires internet and CCXT Pro)"""
    print("\n=== Orderbook Subscription Test ===")
    
    try:
        connector = CEXConnector('binance', sandbox=True)
        
        # Connect first
        connected = await connector.connect()
        if not connected:
            print("⚠️  Skipping orderbook test - connection failed")
            return True  # Not a failure, just can't test
        
        # Subscribe to orderbook
        await connector.subscribe_orderbook('BTC/USDT', limit=10)
        
        # Wait for some data
        await asyncio.sleep(3)
        
        # Check if we received orderbook data
        orderbook = connector.get_orderbook('BTC/USDT')
        
        if orderbook and orderbook.get('bids') and orderbook.get('asks'):
            print("✓ Orderbook subscription successful")
            print(f"  Bids: {len(orderbook['bids'])}, Asks: {len(orderbook['asks'])}")
            
            # Check data quality
            quality_scores = connector.get_data_quality_scores()
            if quality_scores:
                print(f"  Data quality: {quality_scores}")
            
            # Check latency stats
            latency_stats = connector.get_latency_stats('BTC/USDT')
            if latency_stats:
                for key, stats in latency_stats.items():
                    print(f"  {key} avg latency: {stats['avg_latency']:.2f}ms")
        else:
            print("✗ No orderbook data received")
            await connector.close()
            return False
        
        # Cleanup
        await connector.unsubscribe('BTC/USDT', 'orderbook')
        await connector.close()
        return True
        
    except Exception as e:
        print(f"✗ Orderbook subscription test failed: {e}")
        print("  This may be expected if CCXT Pro not available or network issues")
        return False

async def test_trades_subscription():
    """Test trades subscription (requires internet and CCXT Pro)"""
    print("\n=== Trades Subscription Test ===")
    
    try:
        connector = CEXConnector('binance', sandbox=True)
        
        # Connect first
        connected = await connector.connect()
        if not connected:
            print("⚠️  Skipping trades test - connection failed")
            return True  # Not a failure, just can't test
        
        # Subscribe to trades
        await connector.subscribe_trades('BTC/USDT')
        
        # Wait for some data
        await asyncio.sleep(3)
        
        # Check if we received trades data
        trades = connector.get_trades('BTC/USDT', limit=10)
        
        if trades:
            print("✓ Trades subscription successful")
            print(f"  Received {len(trades)} trades")
            
            # Show sample trade
            if trades:
                sample_trade = trades[-1]
                print(f"  Latest trade: {sample_trade.get('price', 'N/A')} @ {sample_trade.get('amount', 'N/A')}")
        else:
            print("⚠️  No trades data received (may be normal for low activity)")
        
        # Cleanup
        await connector.unsubscribe('BTC/USDT', 'trades')
        await connector.close()
        return True
        
    except Exception as e:
        print(f"✗ Trades subscription test failed: {e}")
        print("  This may be expected if CCXT Pro not available or network issues")
        return False

def test_data_quality_calculation():
    """Test data quality calculation"""
    print("\n=== Data Quality Calculation Test ===")
    
    try:
        connector = CEXConnector('binance', sandbox=True)
        
        # Test with good orderbook data
        good_orderbook = {
            'bids': [[50000, 1.0], [49999, 0.5], [49998, 0.3], [49997, 0.2], [49996, 0.1]],
            'asks': [[50001, 1.0], [50002, 0.5], [50003, 0.3], [50004, 0.2], [50005, 0.1]],
            'timestamp': int(time.time() * 1000)
        }
        
        quality_score = connector._calculate_data_quality(good_orderbook)
        
        if quality_score > 0.8:
            print(f"✓ Data quality calculation working - score: {quality_score:.2f}")
        else:
            print(f"✗ Data quality calculation failed - score: {quality_score:.2f}")
            return False
        
        # Test with bad orderbook data
        bad_orderbook = {
            'bids': [],
            'asks': [],
            'timestamp': None
        }
        
        bad_quality_score = connector._calculate_data_quality(bad_orderbook)
        
        if bad_quality_score == 0.0:
            print(f"✓ Bad data detection working - score: {bad_quality_score:.2f}")
        else:
            print(f"✗ Bad data detection failed - score: {bad_quality_score:.2f}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Data quality calculation test failed: {e}")
        return False

def test_latency_recording():
    """Test latency recording functionality"""
    print("\n=== Latency Recording Test ===")
    
    try:
        connector = CEXConnector('binance', sandbox=True)
        
        # Record some test latencies
        connector._record_latency('BTC/USDT', 'orderbook', 50.0)
        connector._record_latency('BTC/USDT', 'orderbook', 75.0)
        connector._record_latency('BTC/USDT', 'orderbook', 60.0)
        
        # Get latency stats
        stats = connector.get_latency_stats('BTC/USDT')
        
        if stats and 'BTC/USDT_orderbook' in stats:
            orderbook_stats = stats['BTC/USDT_orderbook']
            avg_latency = orderbook_stats['avg_latency']
            min_latency = orderbook_stats['min_latency']
            max_latency = orderbook_stats['max_latency']
            
            print(f"✓ Latency recording working")
            print(f"  Average: {avg_latency:.2f}ms")
            print(f"  Min: {min_latency:.2f}ms")
            print(f"  Max: {max_latency:.2f}ms")
            
            # Verify calculations
            expected_avg = (50.0 + 75.0 + 60.0) / 3
            if abs(avg_latency - expected_avg) < 0.1:
                print("✓ Latency calculations correct")
                return True
            else:
                print(f"✗ Latency calculations incorrect - expected {expected_avg:.2f}, got {avg_latency:.2f}")
                return False
        else:
            print("✗ No latency stats found")
            return False
            
    except Exception as e:
        print(f"✗ Latency recording test failed: {e}")
        return False

async def main():
    """Run all CEX connector tests"""
    print("Starting CEX Connector Tests...\n")
    
    # Import time here to avoid issues if not available
    import time
    
    tests = [
        test_cex_connector_initialization,
        test_data_quality_calculation,
        test_latency_recording,
        test_connection,
        test_orderbook_subscription,
        test_trades_subscription
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
        print("🎉 All CEX connector tests passed!")
    else:
        print("⚠️  Some tests failed - this may be expected without internet or CCXT Pro")
        print("   Core functionality tests should pass even without network access")
    
    return all(results)

if __name__ == "__main__":
    asyncio.run(main())
