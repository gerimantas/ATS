"""
Test all DEX scanners integration
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
logger = get_logger("test.all_scanners")

# Import scanners
from scanners.dexscreener_scanner import scan as dexscreener_scan
from scanners.jupiter_scanner import scan as jupiter_scan
from scanners.moralis_scanner import scan as moralis_scan
from scanners.coingecko_dex_scanner import scan as coingecko_dex_scan
from scanners.defillama_scanner import scan as defillama_scan


async def test_all_scanners():
    """Test all five DEX scanners together"""

    print("Testing All DEX Scanners Integration...")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        all_results = []

        # Test DexScreener Scanner
        print("\n=== DexScreener Scanner ===")
        try:
            dex_results = await dexscreener_scan(session)
            print(f"✓ DexScreener found {len(dex_results)} candidates")
            for i, result in enumerate(dex_results[:3], 1):  # Show top 3
                print(
                    f"  {i}. {result.get('cex_symbol', 'N/A')} - Score: {result.get('score', 0)}"
                )
            all_results.extend(dex_results)
        except Exception as e:
            print(f"✗ DexScreener failed: {e}")

        # Test Jupiter Scanner
        print("\n=== Jupiter Scanner ===")
        try:
            jupiter_results = await jupiter_scan(session)
            print(f"✓ Jupiter found {len(jupiter_results)} candidates")
            for i, result in enumerate(jupiter_results[:3], 1):  # Show top 3
                print(
                    f"  {i}. {result.get('cex_symbol', 'N/A')} - Score: {result.get('score', 0)}"
                )
            all_results.extend(jupiter_results)
        except Exception as e:
            print(f"✗ Jupiter failed: {e}")

        # Test Moralis Scanner
        print("\n=== Moralis Scanner ===")
        try:
            moralis_results = await moralis_scan(session)
            print(f"✓ Moralis found {len(moralis_results)} candidates")
            for i, result in enumerate(moralis_results[:3], 1):  # Show top 3
                print(
                    f"  {i}. {result.get('cex_symbol', 'N/A')} - Score: {result.get('score', 0)}"
                )
            all_results.extend(moralis_results)
        except Exception as e:
            print(f"✗ Moralis failed: {e}")

        # Test CoinGecko DEX Scanner
        print("\n=== CoinGecko DEX Scanner ===")
        try:
            coingecko_results = await coingecko_dex_scan(session)
            print(f"✓ CoinGecko DEX found {len(coingecko_results)} candidates")
            for i, result in enumerate(coingecko_results[:3], 1):  # Show top 3
                print(
                    f"  {i}. {result.get('cex_symbol', 'N/A')} - Score: {result.get('score', 0)}"
                )
            all_results.extend(coingecko_results)
        except Exception as e:
            print(f"✗ CoinGecko DEX failed: {e}")

        # Test DefiLlama Scanner
        print("\n=== DefiLlama Scanner ===")
        try:
            defillama_results = await defillama_scan(session)
            print(f"✓ DefiLlama found {len(defillama_results)} candidates")
            for i, result in enumerate(defillama_results[:3], 1):  # Show top 3
                print(
                    f"  {i}. {result.get('cex_symbol', 'N/A')} - Score: {result.get('score', 0)}"
                )
            all_results.extend(defillama_results)
        except Exception as e:
            print(f"✗ DefiLlama failed: {e}")

        # Summary
        print(f"\n=== Summary ===")
        print(f"Total candidates from all scanners: {len(all_results)}")

        # Aggregate by symbol
        symbol_scores = {}
        for result in all_results:
            symbol = result.get("cex_symbol", "N/A")
            score = result.get("score", 0)
            if symbol not in symbol_scores:
                symbol_scores[symbol] = []
            symbol_scores[symbol].append(score)

        # Calculate average scores for symbols found by multiple scanners
        print("\n=== Multi-Scanner Opportunities ===")
        multi_scanner_hits = 0
        for symbol, scores in symbol_scores.items():
            if len(scores) > 1:
                avg_score = sum(scores) / len(scores)
                max_score = max(scores)
                print(
                    f"  {symbol}: Found by {len(scores)} scanners, Avg Score: {avg_score:.1f}, Max: {max_score:.1f}"
                )
                multi_scanner_hits += 1

        if multi_scanner_hits == 0:
            print("  No symbols found by multiple scanners this round")

        print(f"\nSymbols found by multiple scanners: {multi_scanner_hits}")
        print("✅ Multi-scanner integration test completed!")


async def test_scanner_configuration():
    """Test scanner configuration integration"""

    print("\n" + "=" * 50)
    print("Testing Scanner Configuration...")

    try:
        # Test config integration
        from config import ENABLED_DEX_SCANNERS

        print(f"✓ Enabled scanners in config: {ENABLED_DEX_SCANNERS}")

        # Test scanner mapping
        SCANNER_MAP = {
            "dexscreener_scanner": dexscreener_scan,
            "jupiter_scanner": jupiter_scan,
            "moralis_scanner": moralis_scan,
            "coingecko_dex_scanner": coingecko_dex_scan,
            "defillama_scanner": defillama_scan,
        }

        print("✓ Scanner function mapping:")
        for name, func in SCANNER_MAP.items():
            enabled = name in ENABLED_DEX_SCANNERS
            status = "ENABLED" if enabled else "DISABLED"
            print(f"  {name}: {status}")

        # Test enabled scanners only
        print("\nTesting only enabled scanners...")
        async with aiohttp.ClientSession() as session:
            for scanner_name in ENABLED_DEX_SCANNERS:
                if scanner_name in SCANNER_MAP:
                    try:
                        results = await SCANNER_MAP[scanner_name](session)
                        print(f"✓ {scanner_name}: {len(results)} candidates")
                    except Exception as e:
                        print(f"✗ {scanner_name}: {e}")
                else:
                    print(f"⚠️  {scanner_name}: Function not found")

        print("✅ Scanner configuration test completed!")

    except ImportError as e:
        print(f"⚠️  Config import issue: {e}")
        print("Using default scanners...")


async def main():
    """Run all scanner tests"""
    try:
        await test_all_scanners()
        await test_scanner_configuration()
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
