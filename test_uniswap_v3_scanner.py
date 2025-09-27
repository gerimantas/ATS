"""
Test Uniswap V3 Scanner
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import asyncio
import aiohttp
from dotenv import load_dotenv
from config.logging_config import setup_logging, get_logger
from scanners.uniswap_v3_scanner import scan, test_api_connection

# Load environment variables
load_dotenv()

# Initialize logging
setup_logging()
logger = get_logger("test.uniswap_v3_scanner")


async def main():
    """Test Uniswap V3 scanner"""

    print("Testing Uniswap V3 Scanner...")
    print("=" * 40)

    # Test API connection
    print("\n=== API Connection Test ===")
    connection_ok = await test_api_connection()

    if connection_ok:
        print("\n=== Full Scanner Test ===")
        async with aiohttp.ClientSession() as session:
            try:
                results = await scan(session)
                print(f"✓ Scanner found {len(results)} candidates")

                if results:
                    print("\nTop candidates:")
                    for i, candidate in enumerate(results[:5], 1):
                        score = candidate.get("score", 0)
                        symbol = candidate.get("cex_symbol", "N/A")
                        network = candidate.get("network", "unknown")
                        tvl = candidate.get("metadata", {}).get("tvl_usd", 0)

                        print(f"  {i}. {symbol} on {network}")
                        print(f"     Score: {score}, TVL: ${tvl:,.0f}")
                else:
                    print("No candidates found")

                print("✅ Uniswap V3 scanner test completed!")

            except Exception as e:
                print(f"✗ Scanner test failed: {e}")
                import traceback

                traceback.print_exc()
    else:
        print("❌ Cannot test scanner - API connection failed")


if __name__ == "__main__":
    asyncio.run(main())
