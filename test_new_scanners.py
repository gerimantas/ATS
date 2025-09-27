"""
Test new DEX scanners (CoinGecko DEX and DEXTools)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import asyncio
import aiohttp
from dotenv import load_dotenv
from config.logging_config import setup_logging, get_logger

# Load environment variables
load_dotenv()

# Initialize logging
setup_logging()
logger = get_logger("test.new_scanners")


async def test_coingecko_dex_scanner():
    """Test CoinGecko DEX scanner"""
    print("\n=== CoinGecko DEX Scanner Test ===")

    try:
        from scanners.coingecko_dex_scanner import (
            scan,
            test_api_connection,
            _get_coingecko_headers,
            _get_trending_pools,
        )

        # Test API key
        print("Testing API key...")
        headers = _get_coingecko_headers()
        if headers:
            print("✓ API Key found")
        else:
            print("✗ API Key missing")
            return False

        # Test API connection
        print("Testing API connection...")
        async with aiohttp.ClientSession() as session:
            connected = await test_api_connection()
            if connected:
                print("✓ API connection successful")
            else:
                print("✗ API connection failed")
                return False

        # Test trending pools for one network
        print("Testing trending pools...")
        async with aiohttp.ClientSession() as session:
            pools = await _get_trending_pools(session, "eth")
            print(f"✓ Found {len(pools)} trending pools on Ethereum")

        # Test full scanner
        print("Testing full scanner...")
        async with aiohttp.ClientSession() as session:
            results = await scan(session)
            print(f"✓ CoinGecko DEX scanner found {len(results)} candidates")

            # Show top 3 results
            for i, result in enumerate(results[:3], 1):
                print(
                    f"  {i}. {result.get('cex_symbol', 'N/A')} - Score: {result.get('score', 0)} - Network: {result.get('network', 'N/A')}"
                )

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


async def test_dextools_scanner():
    """Test DEXTools scanner"""
    print("\n=== DEXTools Scanner Test ===")

    try:
        from scanners.dextools_scanner import (
            scan,
            test_api_connection,
            _get_dextools_headers,
            _get_hot_pairs,
        )

        # Test API key
        print("Testing API key...")
        headers = _get_dextools_headers()
        if headers:
            print("✓ API Key found")
        else:
            print("✗ API Key missing")
            return False

        # Test API connection
        print("Testing API connection...")
        async with aiohttp.ClientSession() as session:
            connected = await test_api_connection()
            if connected:
                print("✓ API connection successful")
            else:
                print("✗ API connection failed")
                return False

        # Test hot pairs for one chain
        print("Testing hot pairs...")
        async with aiohttp.ClientSession() as session:
            pairs = await _get_hot_pairs(session, "ether")
            print(f"✓ Found {len(pairs)} hot pairs on Ethereum")

        # Test full scanner
        print("Testing full scanner...")
        async with aiohttp.ClientSession() as session:
            results = await scan(session)
            print(f"✓ DEXTools scanner found {len(results)} candidates")

            # Show top 3 results
            for i, result in enumerate(results[:3], 1):
                print(
                    f"  {i}. {result.get('cex_symbol', 'N/A')} - Score: {result.get('score', 0)} - Chain: {result.get('chain', 'N/A')}"
                )

        return True

    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


async def test_all_5_scanners():
    """Test all 5 scanners together"""
    print("\n" + "=" * 60)
    print("Testing All 5 DEX Scanners Integration")
    print("=" * 60)

    # Import all scanners
    try:
        from scanners.dexscreener_scanner import scan as dexscreener_scan
        from scanners.jupiter_scanner import scan as jupiter_scan
        from scanners.moralis_scanner import scan as moralis_scan
        from scanners.coingecko_dex_scanner import scan as coingecko_dex_scan
        from scanners.dextools_scanner import scan as dextools_scan
    except ImportError as e:
        print(f"✗ Failed to import scanners: {e}")
        return

    async with aiohttp.ClientSession() as session:
        all_results = []
        scanner_results = {}

        scanners = [
            ("DexScreener", dexscreener_scan),
            ("Jupiter", jupiter_scan),
            ("Moralis", moralis_scan),
            ("CoinGecko DEX", coingecko_dex_scan),
            ("DEXTools", dextools_scan),
        ]

        for name, scanner_func in scanners:
            print(f"\n--- {name} Scanner ---")
            try:
                results = await scanner_func(session)
                scanner_results[name] = results
                print(f"✓ {name} found {len(results)} candidates")

                # Show top 2 from each
                for i, result in enumerate(results[:2], 1):
                    symbol = result.get("cex_symbol", "N/A")
                    score = result.get("score", 0)
                    print(f"  {i}. {symbol} - Score: {score}")

                all_results.extend(results)

            except Exception as e:
                print(f"✗ {name} failed: {e}")

        # Summary analysis
        print(f"\n=== Integration Summary ===")
        print(f"Total candidates from all scanners: {len(all_results)}")

        # Find overlapping symbols
        symbol_sources = {}
        for result in all_results:
            symbol = result.get("cex_symbol", "N/A")
            source = result.get("scanner_source", "unknown")

            if symbol not in symbol_sources:
                symbol_sources[symbol] = []
            symbol_sources[symbol].append((source, result.get("score", 0)))

        # Show multi-scanner hits
        print(f"\n=== Multi-Scanner Opportunities ===")
        multi_hits = 0
        for symbol, sources in symbol_sources.items():
            if len(sources) > 1:
                avg_score = sum(score for _, score in sources) / len(sources)
                source_names = [source for source, _ in sources]
                print(
                    f"  {symbol}: Found by {len(sources)} scanners ({', '.join(source_names)}) - Avg Score: {avg_score:.1f}"
                )
                multi_hits += 1

        if multi_hits == 0:
            print("  No symbols found by multiple scanners this round")

        print(f"\nSymbols confirmed by multiple scanners: {multi_hits}")
        print(f"Scanners successfully tested: {len(scanner_results)}/5")

        # Success rate
        successful_scanners = sum(
            1 for results in scanner_results.values() if len(results) > 0
        )
        print(f"✅ {successful_scanners}/5 scanners returned results")


async def main():
    """Run all tests"""
    print("Testing New DEX Scanners...")

    try:
        # Test individual scanners
        coingecko_success = await test_coingecko_dex_scanner()
        dextools_success = await test_dextools_scanner()

        # Test all 5 scanners together
        await test_all_5_scanners()

        # Final summary
        print(f"\n" + "=" * 60)
        print("FINAL TEST SUMMARY")
        print("=" * 60)
        print(f"CoinGecko DEX Scanner: {'✅ PASS' if coingecko_success else '❌ FAIL'}")
        print(f"DEXTools Scanner: {'✅ PASS' if dextools_success else '❌ FAIL'}")
        print(f"\n🎯 All 5 DEX scanners integration completed!")

    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
