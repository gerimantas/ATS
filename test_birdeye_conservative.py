"""
Conservative Birdeye API test to check rate limiting safety
"""

import asyncio
import os
from src.data.dex_connector import DEXConnector
from config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger("test.birdeye_conservative")


async def test_conservative_mode():
    """Test conservative API usage"""
    print("=== Birdeye Conservative Test ===")

    api_key = os.getenv("BIRDEYE_API_KEY", "b2806ccd55d548d999f149fbf7b79104")
    connector = DEXConnector(api_key)

    try:
        # Connect to API
        print("\n1. Connecting to Birdeye API...")
        connected = await connector.connect()

        if not connected:
            print("❌ Failed to connect to API")
            return False

        print("✅ Successfully connected to Birdeye API")

        # Check initial rate limit status
        rate_status = connector.get_rate_limit_status()
        print(f"\n📊 Initial API usage:")
        print(f"   Requests made today: {rate_status['requests_made']}")
        print(f"   Daily limit: {rate_status['daily_limit']}")
        print(f"   Remaining: {rate_status['remaining']}")
        print(
            f"   Test mode: {'✅ ON' if connector.rate_limiter.get('test_mode') else '❌ OFF'}"
        )

        # Test multiple requests with safety
        print(f"\n2. Testing conservative request pattern (2 sec delays)...")

        for i in range(3):
            print(f"\n   Request {i+1}/3:")

            # Check if we can make request
            can_request = connector._check_rate_limit()
            print(f"   Can make request: {'✅' if can_request else '❌'}")

            if can_request:
                # Make a simple request
                response = await connector._make_request("/defi/networks")
                if response and response.get("success"):
                    networks = response.get("data", [])
                    print(f"   ✅ Response received: {len(networks)} networks")
                else:
                    print(f"   ❌ Request failed")

                # Show updated stats
                rate_status = connector.get_rate_limit_status()
                print(
                    f"   Usage: {rate_status['requests_made']}/{rate_status['daily_limit']}"
                )
            else:
                print("   ⏳ Rate limited - waiting...")

            # Wait before next request (test mode enforces 2 sec)
            print("   Waiting 3 seconds...")
            await asyncio.sleep(3)

        # Final status
        print(f"\n📊 Final API usage:")
        final_status = connector.get_rate_limit_status()
        print(f"   Total requests: {final_status['requests_made']}")
        print(f"   Remaining today: {final_status['remaining']}")

        usage_percent = (
            final_status["requests_made"] / final_status["daily_limit"]
        ) * 100
        print(f"   Usage percentage: {usage_percent:.2f}%")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

    finally:
        await connector.close()


if __name__ == "__main__":
    success = asyncio.run(test_conservative_mode())
    if success:
        print("\n🛡️ Conservative mode test completed successfully!")
    else:
        print("\n💥 Conservative mode test failed!")
