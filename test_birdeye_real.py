"""
Real Birdeye API test with actual token data
"""

import asyncio
import os
from src.data.dex_connector import DEXConnector
from config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger("test.birdeye_real")


async def test_birdeye_real_data():
    """Test Birdeye API with real token data"""
    print("=== Birdeye Real Data Test ===")

    # Get API key from .env
    api_key = os.getenv("BIRDEYE_API_KEY", "b2806ccd55d548d999f149fbf7b79104")

    if not api_key or api_key == "your_birdeye_api_key_here":
        print("❌ No valid API key found")
        return False

    connector = DEXConnector(api_key)

    try:
        # Connect to API
        print("\n1. Connecting to Birdeye API...")
        connected = await connector.connect()

        if not connected:
            print("❌ Failed to connect to API")
            return False

        print("✅ Successfully connected to Birdeye API")

        # Test getting token price for SOL
        print("\n2. Getting SOL token price...")
        sol_address = "So11111111111111111111111111111111111111112"  # SOL token address

        price_data = await connector.get_token_price(sol_address)

        if price_data:
            print("✅ SOL price data received:")
            print(f"   Price: ${price_data.get('value', 'N/A')}")
            print(f"   Update Unix: {price_data.get('updateUnixTime', 'N/A')}")
        else:
            print("❌ Failed to get SOL price data")

        # Test getting trending tokens
        print("\n3. Getting trending tokens...")
        trending = await connector.get_trending_tokens(limit=5)

        if trending:
            print("✅ Trending tokens received:")
            for i, token in enumerate(trending[:3], 1):
                symbol = token.get("symbol", "Unknown")
                address = token.get("address", "N/A")[:12] + "..."
                volume_24h = token.get("volume24h", 0)
                print(f"   {i}. {symbol} ({address}) - Vol: ${volume_24h:,.0f}")
        else:
            print("❌ Failed to get trending tokens")

        # Test connection status
        print("\n4. Connection status:")
        status = connector.get_connection_status()
        for service, info in status.items():
            print(
                f"   {service}: {'✅ Connected' if info.get('connected') else '❌ Disconnected'}"
            )
            if "networks_count" in info:
                print(f"      Networks: {info['networks_count']}")
            if "daily_requests_used" in info:
                print(f"      Requests used: {info['daily_requests_used']}")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

    finally:
        await connector.close()


if __name__ == "__main__":
    success = asyncio.run(test_birdeye_real_data())
    if success:
        print("\n🎉 Birdeye integration test completed successfully!")
    else:
        print("\n💥 Birdeye integration test failed!")
