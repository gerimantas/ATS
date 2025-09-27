"""
Test Jupiter Scanner functionality
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import asyncio
import aiohttp
from config.logging_config import setup_logging, get_logger
from scanners.jupiter_scanner import (
    scan,
    _get_token_list,
    _get_price_from_dexscreener,
    _get_quote,
)

# Initialize logging
setup_logging()
logger = get_logger("test.jupiter_scanner")


async def test_token_list():
    """Test Jupiter token list retrieval"""
    print("=== Jupiter Token List Test ===")

    try:
        async with aiohttp.ClientSession() as session:
            tokens = await _get_token_list(session)

            if tokens and len(tokens) > 0:
                print(f"✓ Retrieved {len(tokens)} tokens from Jupiter")

                # Show some examples
                verified_tokens = [
                    t for t in tokens[:10] if "verified" in t.get("tags", [])
                ]
                if verified_tokens:
                    print(f"  Example verified tokens:")
                    for token in verified_tokens[:3]:
                        print(f"    {token['symbol']} - {token['name']}")

                return True
            else:
                print("✗ Failed to retrieve tokens")
                return False

    except Exception as e:
        print(f"✗ Token list test failed: {e}")
        return False


async def test_price_api():
    """Test DexScreener price API integration"""
    print("\n=== DexScreener Price API Test ===")

    try:
        async with aiohttp.ClientSession() as session:
            # Test with SOL
            sol_address = "So11111111111111111111111111111111111111112"

            price = await _get_price_from_dexscreener(session, sol_address)

            if price and price > 0:
                print(f"✓ Retrieved SOL price: ${price:.2f}")
                return True
            else:
                print("✗ Failed to retrieve price")
                return False

    except Exception as e:
        print(f"✗ Price API test failed: {e}")
        return False


async def test_quote_api():
    """Test Jupiter quote API"""
    print("\n=== Jupiter Quote API Test ===")

    try:
        async with aiohttp.ClientSession() as session:
            # Test quote: 1000 USDC -> SOL
            usdc_address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            sol_address = "So11111111111111111111111111111111111111112"

            quote = await _get_quote(
                session, usdc_address, sol_address, 1000000000
            )  # 1000 USDC

            if quote:
                in_amount = float(quote.get("inAmount", 0)) / 1000000  # Convert to USDC
                out_amount = (
                    float(quote.get("outAmount", 0)) / 1000000000
                )  # Convert to SOL
                routes = len(quote.get("routePlan", []))

                print(f"✓ Quote received: {in_amount:.2f} USDC -> {out_amount:.6f} SOL")
                print(f"  Routes available: {routes}")

                if routes > 0:
                    print(f"  Price per SOL: ${in_amount/out_amount:.2f}")

                return True
            else:
                print("✗ Failed to get quote")
                return False

    except Exception as e:
        print(f"✗ Quote API test failed: {e}")
        return False


async def test_full_scan():
    """Test full Jupiter scanner"""
    print("\n=== Jupiter Full Scanner Test ===")

    try:
        async with aiohttp.ClientSession() as session:
            candidates = await scan(session)

            if candidates:
                print(f"✓ Scanner found {len(candidates)} candidates")

                # Show top 3 candidates
                sorted_candidates = sorted(
                    candidates, key=lambda x: x["score"], reverse=True
                )

                print("  Top candidates:")
                for i, candidate in enumerate(sorted_candidates[:3], 1):
                    symbol = candidate["cex_symbol"]
                    score = candidate["score"]
                    price = candidate["dex_data"]["price"]
                    verified = candidate["dex_data"].get("verified", False)

                    print(
                        f"    {i}. {symbol} - Score: {score:.1f}, Price: ${price:.6f}, Verified: {'✓' if verified else '✗'}"
                    )

                return True
            else:
                print("⚠️  Scanner found no candidates (this may be normal)")
                return True  # Not necessarily a failure

    except Exception as e:
        print(f"✗ Full scanner test failed: {e}")
        return False


async def run_all_tests():
    """Run all Jupiter scanner tests"""
    print("Starting Jupiter Scanner Tests...\n")

    tests = [test_token_list, test_price_api, test_quote_api, test_full_scan]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    print(f"\n=== Jupiter Scanner Test Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")

    if all(results):
        print("🎉 All Jupiter scanner tests passed!")
    else:
        print("⚠️  Some tests failed - check network connectivity")

    return all(results)


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    if success:
        print("\n✅ Jupiter scanner integration is ready!")
    else:
        print("\n❌ Jupiter scanner needs attention!")
