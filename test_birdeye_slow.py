"""
Slow Birdeye API test with delays between requests
"""

import asyncio
import os
from src.data.dex_connector import DEXConnector
from config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger("test.birdeye_slow")


async def test_birdeye_slow():
    """Test Birdeye API with delays"""
    print("=== Birdeye Slow Test (with delays) ===")

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
        print("   Waiting 2 seconds before next request...")
        await asyncio.sleep(2)

        # Test getting supported networks
        print("\n2. Getting supported networks...")
        response = await connector._make_request("/defi/networks")

        if response and response.get("success"):
            networks = response.get("data", [])
            print(f"✅ Networks received: {len(networks)} networks")
            for i, network in enumerate(networks[:5], 1):
                print(f"   {i}. {network}")
        else:
            print("❌ Failed to get networks")

        print("   Waiting 2 seconds before next request...")
        await asyncio.sleep(2)

        # Test getting SOL price
        print("\n3. Getting SOL price...")
        sol_address = "So11111111111111111111111111111111111111112"
        params = {"address": sol_address}

        response = await connector._make_request("/defi/price", params)

        if response and response.get("success"):
            data = response.get("data", {})
            price = data.get("value", "N/A")
            update_time = data.get("updateUnixTime", "N/A")
            print(f"✅ SOL price: ${price}")
            print(f"   Last update: {update_time}")
        else:
            print("❌ Failed to get SOL price")
            if response:
                print(f"   Response: {response}")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

    finally:
        await connector.close()


if __name__ == "__main__":
    success = asyncio.run(test_birdeye_slow())
    if success:
        print("\n🎉 Birdeye slow test completed!")
    else:
        print("\n💥 Birdeye slow test failed!")
