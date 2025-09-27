"""
DefiLlama DEX Scanner
Uses DefiLlama API to find trending DEX protocols and pools with high activity
Real-time TVL and volume data across all chains and DEX protocols
"""

import aiohttp
import asyncio
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after path setup for standalone execution
try:
    from config import MIN_DEX_LIQUIDITY
    from config.logging_config import get_logger
except ImportError:
    # For standalone execution
    MIN_DEX_LIQUIDITY = 50000
    import logging

    def get_logger(name):
        return logging.getLogger(name)


logger = get_logger("scanners.defillama_scanner")

# DefiLlama API configuration
DEFILLAMA_API_BASE = "https://api.llama.fi"
RATE_LIMIT_DELAY = 1.0  # 1 second delay between requests
DEFAULT_TIMEOUT = 30

# DefiLlama endpoints for different data types
DEFILLAMA_ENDPOINTS = {
    "protocols": f"{DEFILLAMA_API_BASE}/protocols",
    "pools": f"{DEFILLAMA_API_BASE}/pools",
    "yields": f"{DEFILLAMA_API_BASE}/pools",
    "tvl": f"{DEFILLAMA_API_BASE}/tvl",
}


async def _make_api_request(session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
    """Make API request to DefiLlama"""

    try:
        await asyncio.sleep(RATE_LIMIT_DELAY)  # Rate limiting

        async with session.get(url, timeout=DEFAULT_TIMEOUT) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.warning(f"DefiLlama request failed: {response.status} for {url}")
                return None

    except asyncio.TimeoutError:
        logger.warning(f"Timeout making request to {url}")
        return None
    except Exception as e:
        logger.error(f"Error making API request: {e}")
        return None


async def _get_dex_protocols(session: aiohttp.ClientSession) -> List[Dict]:
    """Get top DEX protocols by TVL"""

    data = await _make_api_request(session, DEFILLAMA_ENDPOINTS["protocols"])
    if not data:
        return []

    # Filter for DEX protocols
    dex_protocols = []
    for protocol in data:
        if not protocol:
            continue

        category = protocol.get("category", "").lower()
        if "dex" in category:
            tvl = protocol.get("tvl")
            if tvl and tvl > MIN_DEX_LIQUIDITY:
                dex_protocols.append(protocol)

    # Sort by TVL descending
    dex_protocols.sort(key=lambda x: x.get("tvl", 0), reverse=True)

    logger.debug(f"Found {len(dex_protocols)} DEX protocols")
    return dex_protocols[:20]  # Top 20


async def _get_yield_pools(session: aiohttp.ClientSession) -> List[Dict]:
    """Get high-yield pools from DefiLlama"""

    data = await _make_api_request(session, DEFILLAMA_ENDPOINTS["pools"])
    if not data or "data" not in data:
        return []

    pools = data["data"]

    # Filter for high-yield, high-TVL DEX pools
    good_pools = []
    for pool in pools:
        if not pool:
            continue

        # Pool filtering criteria
        tvl = pool.get("tvlUsd", 0)
        apy = pool.get("apy", 0)
        project = pool.get("project", "").lower()

        # Focus on DEX-related projects
        dex_keywords = [
            "uniswap",
            "sushiswap",
            "pancakeswap",
            "curve",
            "balancer",
            "trader joe",
            "quickswap",
        ]
        is_dex = any(keyword in project for keyword in dex_keywords)

        if (
            is_dex
            and tvl > MIN_DEX_LIQUIDITY
            and apy > 5  # At least 5% APY
            and apy < 1000
        ):  # Exclude suspicious high APY

            good_pools.append(pool)

    # Sort by TVL * APY score
    good_pools.sort(key=lambda x: (x.get("tvlUsd", 0) * x.get("apy", 0)), reverse=True)

    logger.debug(f"Found {len(good_pools)} good DEX pools")
    return good_pools[:15]  # Top 15


async def _calculate_opportunity_score(item: Dict, item_type: str) -> float:
    """Calculate opportunity score for DEX protocol or pool"""

    try:
        if item_type == "protocol":
            # Protocol scoring
            tvl = item.get("tvl", 0)
            change_1d = item.get("change_1d", 0)
            change_7d = item.get("change_7d", 0)

            # TVL score (max 40 points)
            tvl_score = min(tvl / 10000000, 40)  # $10M = max score

            # Growth score (max 30 points)
            growth_score = 0
            if change_1d > 0:
                growth_score += min(change_1d, 15)
            if change_7d > 0:
                growth_score += min(change_7d / 7, 15)

            # Name bonus for established DEXs
            name = item.get("name", "").lower()
            name_bonus = 0
            if any(dex in name for dex in ["uniswap", "sushiswap", "pancakeswap"]):
                name_bonus = 15
            elif any(dex in name for dex in ["curve", "balancer", "1inch"]):
                name_bonus = 10

            return tvl_score + growth_score + name_bonus

        elif item_type == "pool":
            # Pool scoring
            tvl = item.get("tvlUsd", 0)
            apy = item.get("apy", 0)

            # TVL score (max 30 points)
            tvl_score = min(tvl / 5000000, 30)  # $5M = max score

            # APY score (max 40 points, sweet spot 10-50% APY)
            apy_score = 0
            if 5 <= apy <= 50:
                apy_score = min(apy, 40)
            elif apy > 50:
                apy_score = max(0, 40 - (apy - 50) * 0.5)  # Penalty for too high APY

            # Stability bonus
            stability_bonus = 10 if 10 <= apy <= 30 else 0

            return tvl_score + apy_score + stability_bonus

        return 0.0

    except Exception as e:
        logger.warning(f"Error calculating score: {e}")
        return 0.0


async def _convert_to_standard_format(item: Dict, item_type: str) -> Optional[Dict]:
    """Convert DefiLlama data to standard scanner format"""

    try:
        score = await _calculate_opportunity_score(item, item_type)

        if item_type == "protocol":
            name = item.get("name", "Unknown")
            symbol = item.get("symbol", name.upper()[:4])

            return {
                "cex_symbol": f"{symbol}/USDT",  # Generic pair format
                "dex_pair_address": f"defillama_protocol_{item.get('id', 'unknown')}",
                "score": round(score, 1),
                "source": "defillama_protocol",
                "network": "multi-chain",
                "metadata": {
                    "protocol_name": name,
                    "tvl_usd": item.get("tvl", 0),
                    "change_1d": item.get("change_1d", 0),
                    "change_7d": item.get("change_7d", 0),
                    "category": item.get("category", ""),
                    "chains": item.get("chains", []),
                },
            }

        elif item_type == "pool":
            project = item.get("project", "Unknown")
            symbol = (
                item.get("symbol", "").split("-")[0] or "POOL"
            )  # Get first token symbol
            chain = item.get("chain", "ethereum")

            return {
                "cex_symbol": f"{symbol}/USDT",
                "dex_pair_address": item.get("pool", f"defillama_pool_{project}"),
                "score": round(score, 1),
                "source": "defillama_pool",
                "network": chain.lower(),
                "metadata": {
                    "project": project,
                    "pool_symbol": item.get("symbol", ""),
                    "tvl_usd": item.get("tvlUsd", 0),
                    "apy": item.get("apy", 0),
                    "chain": chain,
                    "exposure": item.get("exposure", ""),
                },
            }

        return None

    except Exception as e:
        logger.error(f"Error converting item to standard format: {e}")
        return None


async def scan(session: aiohttp.ClientSession) -> List[Dict]:
    """
    Scan DefiLlama for DEX trading opportunities

    Returns:
        List[Dict]: List of potential trading opportunities with standardized format
    """

    logger.info("Executing defillama_scanner...")

    all_candidates = []

    try:
        # Get top DEX protocols
        dex_protocols = await _get_dex_protocols(session)
        logger.info(f"Found {len(dex_protocols)} DEX protocols")

        for protocol in dex_protocols[:10]:  # Top 10 protocols
            candidate = await _convert_to_standard_format(protocol, "protocol")
            if candidate and candidate["score"] > 20:
                all_candidates.append(candidate)

        # Get high-yield pools
        yield_pools = await _get_yield_pools(session)
        logger.info(f"Found {len(yield_pools)} yield pools")

        for pool in yield_pools[:10]:  # Top 10 pools
            candidate = await _convert_to_standard_format(pool, "pool")
            if candidate and candidate["score"] > 15:
                all_candidates.append(candidate)

    except Exception as e:
        logger.error(f"Error in DefiLlama scan: {e}")

    # Sort by score and remove duplicates by symbol
    all_candidates.sort(key=lambda x: x["score"], reverse=True)

    # Deduplicate by symbol
    seen_symbols = set()
    unique_candidates = []
    for candidate in all_candidates:
        symbol = candidate["cex_symbol"]
        if symbol not in seen_symbols:
            seen_symbols.add(symbol)
            unique_candidates.append(candidate)

    top_candidates = unique_candidates[:8]  # Top 8 unique

    logger.info(f"DefiLlama scanner found {len(top_candidates)} potential candidates")

    return top_candidates


async def test_api_connection():
    """Test DefiLlama API connectivity"""

    async with aiohttp.ClientSession() as session:
        # Test protocols endpoint
        data = await _make_api_request(session, DEFILLAMA_ENDPOINTS["protocols"])

        if data and len(data) > 0:
            print(f"✓ DefiLlama API connection successful")
            print(f"  Found {len(data)} protocols")

            # Find DEX protocols
            dex_count = sum(
                1 for p in data if p and "dex" in p.get("category", "").lower()
            )
            print(f"  DEX protocols: {dex_count}")
            return True
        else:
            print(f"✗ DefiLlama API connection failed")
            return False


if __name__ == "__main__":
    # Standalone test
    import sys
    from pathlib import Path

    # Add parent directory to path to import config
    sys.path.insert(0, str(Path.cwd().parent))

    async def main():
        print("Testing DefiLlama Scanner...")

        # Test API connection
        await test_api_connection()

        # Test full scan
        async with aiohttp.ClientSession() as session:
            results = await scan(session)
            print(f"\nFound {len(results)} candidates:")
            for i, candidate in enumerate(results, 1):
                print(
                    f"  {i}. {candidate['cex_symbol']} ({candidate['source']}) - Score: {candidate['score']}"
                )

    asyncio.run(main())
