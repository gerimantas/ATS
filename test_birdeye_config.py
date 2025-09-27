"""
Test configuration manager for Birdeye API
"""

import asyncio
from config.birdeye_config import get_birdeye_config, set_active_mode, get_all_modes
from src.data.dex_connector import DEXConnector
from config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger("test.config_manager")


async def test_all_modes():
    """Test all configuration modes"""
    print("=== Birdeye Configuration Test ===\n")

    api_key = "b2806ccd55d548d999f149fbf7b79104"

    for mode in get_all_modes():
        print(f"Testing mode: {mode}")
        print("-" * 40)

        # Set mode
        success = set_active_mode(mode)
        if not success:
            print(f"❌ Failed to set mode: {mode}")
            continue

        # Get config
        config = get_birdeye_config()
        print(f"📊 Configuration:")
        print(f"   Daily limit: {config['daily_limit']}")
        print(f"   Delay between requests: {config['delay_between_requests']}s")
        print(f"   Warning threshold: {config['warning_threshold']*100}%")
        print(f"   Critical threshold: {config['critical_threshold']*100}%")
        print(f"   Description: {config['description']}")

        # Test connector creation
        connector = DEXConnector(api_key)
        print(f"\n🔧 DEXConnector settings:")
        print(f"   Daily limit: {connector.rate_limiter['daily_limit']}")
        print(f"   Delay: {connector.rate_limiter['delay_between_requests']}s")
        print(f"   Warning at: {connector.rate_limiter['warning_threshold']*100}%")

        # Quick connection test (no actual requests)
        rate_status = connector.get_rate_limit_status()
        print(f"   Requests made: {rate_status['requests_made']}")
        print(f"   Remaining: {rate_status['remaining']}")

        print()

    print("🎯 Current active mode recommendations:")
    print("   - test_mode: For development/testing (100 requests/day)")
    print("   - development: For active development (500 requests/day)")
    print("   - production: For production usage (1000 requests/day)")

    return True


def show_safe_usage_guidelines():
    """Show safe usage guidelines"""
    print("\n📋 Safe Usage Guidelines:")
    print("=" * 50)

    print("\n🛡️  To avoid exceeding Birdeye Standard (30,000 CU) limits:")
    print("   1. Use test_mode during development (100 req/day)")
    print("   2. Monitor usage with get_rate_limit_status()")
    print("   3. Check logs for warning/critical messages")
    print("   4. Each request costs 1-20 CU depending on endpoint")
    print("   5. Price checks = 1 CU, Trades = 10 CU, OHLCV = 20 CU")

    print("\n⚙️  Configuration controls:")
    print("   - Daily limits: test_mode=100, development=500, production=1000")
    print("   - Request delays: test_mode=3s, development=2s, production=1s")
    print("   - Warnings at 70-80% usage, critical at 90-95%")

    print("\n🔄 To change modes:")
    print("   from config.birdeye_config import set_active_mode")
    print("   set_active_mode('development')  # Switch to development mode")

    print("\n📊 To monitor usage:")
    print("   connector.get_rate_limit_status()  # Check current usage")
    print("   Watch for ⚠️ warnings and 🚨 critical alerts in logs")


if __name__ == "__main__":
    asyncio.run(test_all_modes())
    show_safe_usage_guidelines()
