"""
Test DEX scanners
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import asyncio
import aiohttp
from config.logging_config import setup_logging, get_logger

# Initialize logging
setup_logging()
logger = get_logger("test.scanners")


async def test_coingecko_dex_scanner():
    """Test CoinGecko DEX scanner"""
    print("\n=== CoinGecko DEX Scanner Test ===")

    try:
        from scanners.coingecko_dex_scanner import (
            scan,
            _get_dex_terminal_data,
        )

        # Test DEX terminal data retrieval
        async with aiohttp.ClientSession() as session:
            try:
                data = await _get_dex_terminal_data(session)
                print(f"✓ Retrieved {len(data)} DEX terminal entries")

                if data:
                    # Show example data
                    example = data[0]
                    print(
                        f"  Example: {example.get('name', 'Unknown')} - {example.get('symbol', 'Unknown')}"
                    )
                    print(f"  Volume 24h: ${example.get('total_volume', 0):,.0f}")
                else:
                    print("⚠ No DEX terminal data available")
                    return False

            except Exception as e:
                print(f"✗ DEX terminal data error: {e}")
                return False

            # Test full scanner
            results = await scan(session)
            print(f"✓ CoinGecko DEX scanner found {len(results)} candidates")

            for i, result in enumerate(results[:3], 1):
                print(
                    f"  {i}. {result.get('cex_symbol', 'Unknown')} - Score: {result.get('score', 0)}"
                )

            return len(results) > 0

    except ImportError as e:
        print(f"✗ CoinGecko DEX scanner import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ CoinGecko DEX scanner error: {e}")
        return False


async def test_individual_scanners():
    """Test each scanner individually"""
    print("\n" + "=" * 60)
    print("INDIVIDUAL SCANNER TESTS")
    print("=" * 60)

    # Test CoinGecko DEX
    coingecko_success = await test_coingecko_dex_scanner()

    return {"coingecko_dex": coingecko_success}


async def test_all_scanners_parallel():
    """Test all scanners in parallel"""
    print("\n" + "=" * 60)
    print("PARALLEL SCANNER TESTS")
    print("=" * 60)

    try:
        from scanners.coingecko_dex_scanner import scan as coingecko_dex_scan

        # Available scanners
        scanners = [
            ("CoinGecko DEX", coingecko_dex_scan),
        ]

        async with aiohttp.ClientSession() as session:
            # Run all scanners in parallel
            tasks = []
            for name, scanner in scanners:

                async def run_scanner(scanner_name, scan_func):
                    try:
                        start_time = asyncio.get_event_loop().time()
                        results = await scan_func(session)
                        end_time = asyncio.get_event_loop().time()

                        return {
                            "name": scanner_name,
                            "success": True,
                            "results": len(results),
                            "time": end_time - start_time,
                            "data": results[:2],  # Sample data
                        }
                    except Exception as e:
                        return {
                            "name": scanner_name,
                            "success": False,
                            "error": str(e),
                            "results": 0,
                            "time": 0,
                        }

                tasks.append(run_scanner(name, scanner))

            # Wait for all scanners to complete
            scanner_results = await asyncio.gather(*tasks)

            # Display results
            print("\nParallel Scanner Results:")
            print("-" * 40)

            total_results = 0
            successful_scanners = 0

            for result in scanner_results:
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                print(f"{result['name']}: {status}")
                print(f"  Results: {result['results']} candidates")
                print(f"  Time: {result['time']:.2f}s")

                if result["success"]:
                    successful_scanners += 1
                    total_results += result["results"]

                    # Show sample data
                    if result.get("data"):
                        for i, sample in enumerate(result["data"], 1):
                            symbol = sample.get("cex_symbol", "Unknown")
                            score = sample.get("score", 0)
                            print(f"    {i}. {symbol} (Score: {score})")
                else:
                    print(f"  Error: {result.get('error', 'Unknown')}")
                print()

            print(f"Summary: {successful_scanners}/{len(scanners)} scanners successful")
            print(f"Total candidates found: {total_results}")

            return successful_scanners > 0

    except Exception as e:
        print(f"Parallel test error: {e}")
        return False


async def run_all_tests():
    """Run all scanner tests"""
    print("=" * 60)
    print("DEX SCANNER TESTING SUITE")
    print("=" * 60)

    # Individual tests
    individual_results = await test_individual_scanners()

    # Parallel tests
    parallel_success = await test_all_scanners_parallel()

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL TEST SUMMARY")
    print("=" * 60)

    print("Individual Scanner Results:")
    for scanner, success in individual_results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {scanner.replace('_', ' ').title()}: {status}")

    parallel_status = "✅ PASS" if parallel_success else "❌ FAIL"
    print(f"\nParallel Test: {parallel_status}")

    # Overall status
    successful_individual = sum(individual_results.values())
    total_individual = len(individual_results)

    print(f"\nOverall: {successful_individual}/{total_individual} scanners working")

    if successful_individual > 0:
        print("✅ Scanner system is functional!")
    else:
        print("❌ No scanners are working - check configuration")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
