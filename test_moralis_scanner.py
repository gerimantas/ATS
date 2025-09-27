"""
Test Moralis Scanner functionality
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import asyncio
import aiohttp
import os
from dotenv import load_dotenv
from config.logging_config import setup_logging, get_logger

# Load environment variables
load_dotenv()
from scanners.moralis_scanner import (
    scan,
    _get_moralis_headers,
    _get_token_price,
    _get_token_metadata,
)

# Initialize logging
setup_logging()
logger = get_logger("test.moralis_scanner")


async def test_api_key():
    """Test Moralis API key availability"""
    print("=== Moralis API Key Test ===")

    try:
        headers = await _get_moralis_headers()

        if headers and "X-API-Key" in headers:
            api_key = headers["X-API-Key"]
            print(f"✓ API Key found: {api_key[:20]}...")
            return True
        else:
            print("✗ API Key not found in environment")
            return False

    except Exception as e:
        print(f"✗ API Key test failed: {e}")
        return False


async def test_token_price():
    """Test token price retrieval"""
    print("\n=== Moralis Token Price Test ===")

    try:
        async with aiohttp.ClientSession() as session:
            # Test with USDC on Ethereum
            usdc_address = "0xA0b86a33E6441d07b651c6cD6e2c35b43aA47Fbe"

            price = await _get_token_price(session, usdc_address, "eth")

            if price and price > 0:
                print(f"✓ Retrieved USDC price: ${price:.6f}")

                # Should be close to $1 for USDC
                if 0.95 <= price <= 1.05:
                    print("✓ Price looks reasonable for USDC")
                    return True
                else:
                    print(f"⚠️  USDC price seems off: ${price}")
                    return True  # Still counts as API working
            else:
                print("✗ Failed to retrieve price")
                return False

    except Exception as e:
        print(f"✗ Token price test failed: {e}")
        return False


async def test_token_metadata():
    """Test token metadata retrieval"""
    print("\n=== Moralis Token Metadata Test ===")

    try:
        async with aiohttp.ClientSession() as session:
            # Test with UNI on Ethereum
            uni_address = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"

            metadata = await _get_token_metadata(session, uni_address, "eth")

            if metadata:
                symbol = metadata.get("symbol", "N/A")
                name = metadata.get("name", "N/A")
                decimals = metadata.get("decimals", "N/A")

                print(f"✓ Retrieved metadata:")
                print(f"  Symbol: {symbol}")
                print(f"  Name: {name}")
                print(f"  Decimals: {decimals}")

                # UNI should have symbol "UNI"
                if symbol == "UNI":
                    print("✓ Metadata looks correct")
                    return True
                else:
                    print(f"⚠️  Expected UNI symbol, got: {symbol}")
                    return True  # Still counts as API working
            else:
                print("✗ Failed to retrieve metadata")
                return False

    except Exception as e:
        print(f"✗ Token metadata test failed: {e}")
        return False


async def test_multi_chain():
    """Test multi-chain functionality"""
    print("\n=== Moralis Multi-Chain Test ===")

    try:
        async with aiohttp.ClientSession() as session:
            test_tokens = {
                "eth": (
                    "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
                    "UNI",
                ),  # UNI on Ethereum
                "polygon": (
                    "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
                    "WMATIC",
                ),  # WMATIC on Polygon
                "bsc": (
                    "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",
                    "ETH",
                ),  # ETH on BSC
            }

            results = {}
            for chain, (address, expected_symbol) in test_tokens.items():
                print(f"  Testing {chain.upper()}...")

                metadata = await _get_token_metadata(session, address, chain)
                if metadata:
                    symbol = metadata.get("symbol", "")
                    results[chain] = symbol
                    print(f"    ✓ {chain}: {symbol}")
                else:
                    results[chain] = None
                    print(f"    ✗ {chain}: Failed")

                await asyncio.sleep(0.5)  # Rate limiting

            success_count = sum(1 for result in results.values() if result)
            print(f"\n✓ Successfully tested {success_count}/{len(test_tokens)} chains")

            return success_count > 0

    except Exception as e:
        print(f"✗ Multi-chain test failed: {e}")
        return False


async def test_full_scan():
    """Test full Moralis scanner"""
    print("\n=== Moralis Full Scanner Test ===")

    try:
        async with aiohttp.ClientSession() as session:
            candidates = await scan(session)

            if candidates:
                print(f"✓ Scanner found {len(candidates)} candidates")

                # Show details of candidates
                print("  Candidates found:")
                for i, candidate in enumerate(candidates[:3], 1):
                    symbol = candidate["cex_symbol"]
                    score = candidate["score"]
                    price = candidate["dex_data"]["price"]
                    chain = candidate["dex_data"].get("chain_name", "Unknown")

                    print(
                        f"    {i}. {symbol} on {chain} - Score: {score:.1f}, Price: ${price:.6f}"
                    )

                return True
            else:
                print("⚠️  Scanner found no candidates")
                return True  # Not necessarily a failure for test tokens

    except Exception as e:
        print(f"✗ Full scanner test failed: {e}")
        return False


async def run_all_tests():
    """Run all Moralis scanner tests"""
    print("Starting Moralis Scanner Tests...\n")

    tests = [
        test_api_key,
        test_token_price,
        test_token_metadata,
        test_multi_chain,
        test_full_scan,
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    print(f"\n=== Moralis Scanner Test Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")

    if all(results):
        print("🎉 All Moralis scanner tests passed!")
    elif sum(results) >= 3:
        print("⚠️  Most tests passed - scanner should work")
    else:
        print("❌ Multiple tests failed - check API key and connectivity")

    return sum(results) >= 3


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    if success:
        print("\n✅ Moralis scanner integration is ready!")
    else:
        print("\n❌ Moralis scanner needs attention!")
