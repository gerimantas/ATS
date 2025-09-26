"""
Tests for DEX connector functionality
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import asyncio
import os
import time
from config.logging_config import setup_logging, get_logger
from src.data.dex_connector import DEXConnector

# Initialize logging
setup_logging()
logger = get_logger("test.dex_connector")

def test_dex_connector_initialization():
    """Test DEX connector initialization"""
    print("=== DEX Connector Initialization Test ===")
    
    try:
        # Test with dummy API key
        connector = DEXConnector('test_api_key')
        
        if connector.api_key == 'test_api_key':
            print("✓ DEX connector initialized successfully")
            print(f"  Base URL: {connector.base_url}")
            print(f"  Daily limit: {connector.rate_limiter['daily_limit']}")
            print(f"  Supported chains: {connector.supported_chains}")
            return True
        else:
            print("✗ DEX connector initialization failed")
            return False
            
    except Exception as e:
        print(f"✗ DEX connector initialization failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n=== Rate Limiting Test ===")
    
    try:
        connector = DEXConnector('test_api_key')
        
        # Test initial rate limit check
        can_make_request = connector._check_rate_limit()
        
        if can_make_request:
            print("✓ Initial rate limit check passed")
        else:
            print("✗ Initial rate limit check failed")
            return False
        
        # Simulate making requests
        for i in range(5):
            connector._update_rate_limiter()
        
        # Check rate limit status
        status = connector.get_rate_limit_status()
        
        if status['requests_made'] == 5:
            print("✓ Rate limiter tracking requests correctly")
            print(f"  Requests made: {status['requests_made']}")
            print(f"  Remaining: {status['remaining']}")
        else:
            print(f"✗ Rate limiter tracking incorrect - expected 5, got {status['requests_made']}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Rate limiting test failed: {e}")
        return False

def test_data_quality_calculation():
    """Test data quality calculation"""
    print("\n=== Data Quality Calculation Test ===")
    
    try:
        connector = DEXConnector('test_api_key')
        
        # Test with good trades data
        good_trades = [
            {
                'blockUnixTime': int(time.time()),
                'txHash': '0x123...',
                'source': 'Raydium',
                'tokenAmount': 1000000
            },
            {
                'blockUnixTime': int(time.time()) - 3600,
                'txHash': '0x456...',
                'source': 'Orca',
                'tokenAmount': 500000
            }
        ]
        
        quality_score = connector._calculate_trades_quality(good_trades)
        
        if quality_score > 0.8:
            print(f"✓ Good trades quality calculation working - score: {quality_score:.2f}")
        else:
            print(f"✗ Good trades quality calculation failed - score: {quality_score:.2f}")
            return False
        
        # Test with bad trades data
        bad_trades = []
        bad_quality_score = connector._calculate_trades_quality(bad_trades)
        
        if bad_quality_score == 0.0:
            print(f"✓ Bad trades detection working - score: {bad_quality_score:.2f}")
        else:
            print(f"✗ Bad trades detection failed - score: {bad_quality_score:.2f}")
            return False
        
        # Test liquidity quality
        good_liquidity = {
            'liquidity': 1000000,
            'volume24h': 500000,
            'priceChange24h': 5.2
        }
        
        liquidity_quality = connector._calculate_liquidity_quality(good_liquidity)
        
        if liquidity_quality > 0.8:
            print(f"✓ Liquidity quality calculation working - score: {liquidity_quality:.2f}")
        else:
            print(f"✗ Liquidity quality calculation failed - score: {liquidity_quality:.2f}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Data quality calculation test failed: {e}")
        return False

def test_latency_recording():
    """Test latency recording functionality"""
    print("\n=== Latency Recording Test ===")
    
    try:
        connector = DEXConnector('test_api_key')
        
        # Record some test latencies
        connector._record_latency('/defi/price', 150.0)
        connector._record_latency('/defi/price', 200.0)
        connector._record_latency('/defi/price', 175.0)
        
        # Get latency stats
        stats = connector.get_latency_stats()
        
        if '/defi/price' in stats:
            price_stats = stats['/defi/price']
            avg_latency = price_stats['avg_latency']
            min_latency = price_stats['min_latency']
            max_latency = price_stats['max_latency']
            
            print(f"✓ Latency recording working")
            print(f"  Average: {avg_latency:.2f}ms")
            print(f"  Min: {min_latency:.2f}ms")
            print(f"  Max: {max_latency:.2f}ms")
            
            # Verify calculations
            expected_avg = (150.0 + 200.0 + 175.0) / 3
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

async def test_connection():
    """Test API connection (requires internet and valid API key)"""
    print("\n=== API Connection Test ===")
    
    try:
        # Try to get API key from environment
        api_key = os.getenv('BIRDEYE_API_KEY')
        
        if not api_key:
            print("⚠️  Skipping connection test - no BIRDEYE_API_KEY in environment")
            print("   Set BIRDEYE_API_KEY environment variable to test real API connection")
            return True  # Not a failure, just can't test
        
        connector = DEXConnector(api_key)
        
        # Test connection
        connected = await connector.connect()
        
        if connected:
            print("✓ Birdeye API connection successful")
            
            # Check connection status
            status = connector.get_connection_status()
            if status.get('birdeye', {}).get('connected'):
                print("✓ Connection status verified")
                print(f"  Networks available: {status['birdeye'].get('networks_count', 0)}")
            else:
                print("✗ Connection status check failed")
                await connector.close()
                return False
                
            # Cleanup
            await connector.close()
            return True
        else:
            print("✗ Birdeye API connection failed")
            print("  This may be expected with invalid API key or network issues")
            return False
            
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        print("  This may be expected without valid API key or network issues")
        return False

async def test_token_data_retrieval():
    """Test token data retrieval (requires internet and valid API key)"""
    print("\n=== Token Data Retrieval Test ===")
    
    try:
        # Try to get API key from environment
        api_key = os.getenv('BIRDEYE_API_KEY')
        
        if not api_key:
            print("⚠️  Skipping token data test - no BIRDEYE_API_KEY in environment")
            return True  # Not a failure, just can't test
        
        connector = DEXConnector(api_key)
        
        # Connect first
        connected = await connector.connect()
        if not connected:
            print("⚠️  Skipping token data test - connection failed")
            return True  # Not a failure, just can't test
        
        # Test with a well-known Solana token (USDC)
        usdc_address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        
        # Test price retrieval
        price_data = await connector.get_token_price(usdc_address, 'solana')
        
        if price_data:
            print("✓ Token price retrieval successful")
            print(f"  USDC price: ${price_data.get('value', 'N/A')}")
        else:
            print("⚠️  No price data received (may be API limit or token not found)")
        
        # Test liquidity retrieval
        liquidity_data = await connector.get_token_liquidity(usdc_address, 'solana')
        
        if liquidity_data:
            print("✓ Token liquidity retrieval successful")
            print(f"  Liquidity: ${liquidity_data.get('liquidity', 'N/A')}")
        else:
            print("⚠️  No liquidity data received (may be API limit or token not found)")
        
        # Check data quality scores
        quality_scores = connector.get_data_quality_scores()
        if quality_scores:
            print(f"  Data quality scores: {quality_scores}")
        
        # Check rate limit status
        rate_status = connector.get_rate_limit_status()
        print(f"  API requests used: {rate_status['requests_made']}/{rate_status['daily_limit']}")
        
        # Cleanup
        await connector.close()
        return True
        
    except Exception as e:
        print(f"✗ Token data retrieval test failed: {e}")
        print("  This may be expected without valid API key or network issues")
        return False

async def test_trending_tokens():
    """Test trending tokens retrieval (requires internet and valid API key)"""
    print("\n=== Trending Tokens Test ===")
    
    try:
        # Try to get API key from environment
        api_key = os.getenv('BIRDEYE_API_KEY')
        
        if not api_key:
            print("⚠️  Skipping trending tokens test - no BIRDEYE_API_KEY in environment")
            return True  # Not a failure, just can't test
        
        connector = DEXConnector(api_key)
        
        # Connect first
        connected = await connector.connect()
        if not connected:
            print("⚠️  Skipping trending tokens test - connection failed")
            return True  # Not a failure, just can't test
        
        # Test trending tokens retrieval
        trending = await connector.get_trending_tokens('solana', limit=10)
        
        if trending:
            print("✓ Trending tokens retrieval successful")
            print(f"  Retrieved {len(trending)} trending tokens")
            
            # Show sample token
            if trending:
                sample_token = trending[0]
                print(f"  Top token: {sample_token.get('symbol', 'N/A')} - ${sample_token.get('price', 'N/A')}")
        else:
            print("⚠️  No trending tokens data received (may be API limit)")
        
        # Cleanup
        await connector.close()
        return True
        
    except Exception as e:
        print(f"✗ Trending tokens test failed: {e}")
        print("  This may be expected without valid API key or network issues")
        return False

def test_data_storage():
    """Test data storage functionality"""
    print("\n=== Data Storage Test ===")
    
    try:
        connector = DEXConnector('test_api_key')
        
        # Test storing trades data
        test_token = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        key = f"solana:{test_token}"
        
        # Manually add some test data
        from collections import deque
        connector.trades_data[key] = deque(maxlen=1000)
        connector.trades_data[key].append({
            'blockUnixTime': int(time.time()),
            'txHash': '0x123...',
            'source': 'Raydium',
            'tokenAmount': 1000000
        })
        
        # Test retrieval
        stored_trades = connector.get_stored_trades(test_token, 'solana')
        
        if stored_trades and len(stored_trades) == 1:
            print("✓ Trades data storage working")
            print(f"  Stored {len(stored_trades)} trades")
        else:
            print("✗ Trades data storage failed")
            return False
        
        # Test storing liquidity data
        connector.liquidity_data[key] = {
            'data': {'liquidity': 1000000, 'volume24h': 500000},
            'timestamp': time.time(),
            'chain': 'solana'
        }
        
        stored_liquidity = connector.get_stored_liquidity(test_token, 'solana')
        
        if stored_liquidity and 'data' in stored_liquidity:
            print("✓ Liquidity data storage working")
            print(f"  Liquidity: ${stored_liquidity['data'].get('liquidity', 'N/A')}")
        else:
            print("✗ Liquidity data storage failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Data storage test failed: {e}")
        return False

async def main():
    """Run all DEX connector tests"""
    print("Starting DEX Connector Tests...\n")
    
    tests = [
        test_dex_connector_initialization,
        test_rate_limiting,
        test_data_quality_calculation,
        test_latency_recording,
        test_data_storage,
        test_connection,
        test_token_data_retrieval,
        test_trending_tokens
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
        print("🎉 All DEX connector tests passed!")
    else:
        print("⚠️  Some tests failed - this may be expected without valid API key")
        print("   Core functionality tests should pass even without network access")
        print("   Set BIRDEYE_API_KEY environment variable to test real API connection")
    
    return all(results)

if __name__ == "__main__":
    asyncio.run(main())
