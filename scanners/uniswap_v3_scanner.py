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


logger = get_logger("scanners.uniswap_v3_scanner")

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


def _get_subgraph_url() -> str:
    """Get Uniswap V3 subgraph URL from environment or use default"""
    return os.getenv("UNISWAP_V3_SUBGRAPH_URL", DEFAULT_SUBGRAPH_URL)


async def _execute_graphql_query(
    session: aiohttp.ClientSession, url: str, query: str
) -> Optional[Dict]:
    """Execute a GraphQL query against Uniswap V3 subgraph"""

    payload = {"query": query}

    try:
        await asyncio.sleep(RATE_LIMIT_DELAY)  # Rate limiting

        async with session.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=DEFAULT_TIMEOUT,
        ) as response:
            if response.status == 200:
                data = await response.json()
                if "errors" in data:
                    logger.warning(f"GraphQL errors: {data['errors']}")
                    return None
                return data.get("data", {})
            else:
                logger.warning(f"Subgraph request failed: {response.status}")
                return None

    except asyncio.TimeoutError:
        logger.warning(f"Timeout executing query on {url}")
        return None
    except Exception as e:
        logger.error(f"Error executing GraphQL query: {e}")
        return None


async def _get_top_pools(session: aiohttp.ClientSession, network: str) -> List[Dict]:
    """Get top Uniswap V3 pools by TVL for a specific network"""

    url = UNISWAP_V3_ENDPOINTS.get(network, DEFAULT_SUBGRAPH_URL)

    # GraphQL query to get top pools by total value locked
    query = """
    {
        pools(
            first: 20
            orderBy: totalValueLockedUSD
            orderDirection: desc
            where: {
                totalValueLockedUSD_gt: "50000"
                volumeUSD_gt: "10000"
            }
        ) {
            id
            token0 {
                id
                symbol
                name
                decimals
            }
            token1 {
                id
                symbol
                name
                decimals
            }
            totalValueLockedUSD
            volumeUSD
            feeTier
            txCount
            createdAtTimestamp
            token0Price
            token1Price
        }
    }
    """

    data = await _execute_graphql_query(session, url, query)
    if not data:
        return []

    pools = data.get("pools", [])
    logger.debug(f"Found {len(pools)} top pools on {network}")
    return pools


async def _get_trending_pools(
    session: aiohttp.ClientSession, network: str
) -> List[Dict]:
    """Get trending Uniswap V3 pools by recent volume for a specific network"""

    url = UNISWAP_V3_ENDPOINTS.get(network, DEFAULT_SUBGRAPH_URL)

    # GraphQL query for trending pools by recent activity
    query = """
    {
        pools(
            first: 15
            orderBy: volumeUSD
            orderDirection: desc
            where: {
                totalValueLockedUSD_gt: "25000"
                volumeUSD_gt: "5000"
                txCount_gt: "10"
            }
        ) {
            id
            token0 {
                id
                symbol
                name
            }
            token1 {
                id
                symbol
                name
            }
            totalValueLockedUSD
            volumeUSD
            feeTier
            txCount
            tick
            liquidity
        }
    }
    """

    data = await _execute_graphql_query(session, url, query)
    if not data:
        return []

    pools = data.get("pools", [])
    logger.debug(f"Found {len(pools)} trending pools on {network}")
    return pools


async def _calculate_pool_score(pool: Dict, network: str) -> float:
    """Calculate opportunity score for a Uniswap V3 pool"""

    try:
        # Base metrics
        tvl_usd = float(pool.get("totalValueLockedUSD", 0))
        volume_usd = float(pool.get("volumeUSD", 0))
        tx_count = int(pool.get("txCount", 0))
        fee_tier = int(pool.get("feeTier", 3000))  # basis points (e.g., 3000 = 0.3%)

        # Skip low quality pools
        if tvl_usd < MIN_DEX_LIQUIDITY or volume_usd < 5000:
            return 0.0

        # Scoring components
        tvl_score = min(tvl_usd / 1000000, 100) * 0.3  # TVL score (max 30 points)
        volume_score = (
            min(volume_usd / 100000, 100) * 0.4
        )  # Volume score (max 40 points)
        activity_score = min(tx_count / 100, 50) * 0.2  # Activity score (max 10 points)

        # Fee tier bonus (lower fees = more activity potential)
        fee_bonus = 0
        if fee_tier <= 500:  # 0.05%
            fee_bonus = 15
        elif fee_tier <= 3000:  # 0.3%
            fee_bonus = 10
        elif fee_tier <= 10000:  # 1%
            fee_bonus = 5

        # Network bonus
        network_bonus = 0
        if network == "ethereum":
            network_bonus = 5  # Highest liquidity
        elif network in ["polygon", "arbitrum"]:
            network_bonus = 3  # Good L2 options

        total_score = (
            tvl_score + volume_score + activity_score + fee_bonus + network_bonus
        )
        return round(total_score, 1)

    except (ValueError, TypeError) as e:
        logger.warning(f"Error calculating pool score: {e}")
        return 0.0


async def _convert_to_standard_format(pool: Dict, network: str) -> Dict:
    """Convert Uniswap V3 pool data to standard scanner format"""

    try:
        token0 = pool.get("token0", {})
        token1 = pool.get("token1", {})

        # Create pair symbol (prefer token/USDC, token/USDT, token/WETH format)
        symbol0 = token0.get("symbol", "UNK")
        symbol1 = token1.get("symbol", "UNK")

        # Determine base/quote ordering
        stablecoins = {"USDC", "USDT", "DAI", "BUSD"}
        major_tokens = {"WETH", "ETH", "WBTC", "BTC"}

        if symbol1 in stablecoins or (
            symbol1 in major_tokens and symbol0 not in stablecoins
        ):
            cex_symbol = f"{symbol0}/{symbol1}"
        else:
            cex_symbol = f"{symbol1}/{symbol0}"

        # Calculate score
        score = await _calculate_pool_score(pool, network)

        return {
            "cex_symbol": cex_symbol,
            "dex_pair_address": pool.get("id", ""),
            "score": score,
            "source": "sushiswap_v3",
            "network": network,
            "metadata": {
                "tvl_usd": float(pool.get("totalValueLockedUSD", 0)),
                "volume_usd": float(pool.get("volumeUSD", 0)),
                "fee_tier": int(pool.get("feeTier", 3000)),
                "tx_count": int(pool.get("txCount", 0)),
                "token0_address": token0.get("id", ""),
                "token1_address": token1.get("id", ""),
            },
        }

    except Exception as e:
        logger.error(f"Error converting pool to standard format: {e}")
        return None


async def scan(session: aiohttp.ClientSession) -> List[Dict]:
    """
    Scan Uniswap V3 pools for trading opportunities across multiple networks

    Returns:
        List[Dict]: List of potential trading opportunities with standardized format
    """

    logger.info("Executing uniswap_v3_scanner...")

    all_candidates = []

    # Scan multiple networks
    for network in ["ethereum", "polygon", "arbitrum"]:
        logger.info(f"Scanning {network} Uniswap V3 pools...")

        try:
            # Get top pools by TVL
            top_pools = await _get_top_pools(session, network)

            # Get trending pools by volume
            trending_pools = await _get_trending_pools(session, network)

            # Combine and deduplicate pools
            all_pools = {pool["id"]: pool for pool in top_pools + trending_pools}
            unique_pools = list(all_pools.values())

            # Convert to standard format and filter
            for pool in unique_pools:
                candidate = await _convert_to_standard_format(pool, network)
                if candidate and candidate["score"] > 20:  # Minimum score threshold
                    all_candidates.append(candidate)

        except Exception as e:
            logger.error(f"Error scanning {network}: {e}")
            continue

    # Sort by score descending and take top candidates
    all_candidates.sort(key=lambda x: x["score"], reverse=True)
    top_candidates = all_candidates[:10]  # Top 10

    logger.info(f"Uniswap V3 scanner found {len(top_candidates)} potential candidates")

    return top_candidates


# Test function for standalone execution
async def test_api_connection():
    """Test Uniswap V3 Subgraph API connectivity"""

    async with aiohttp.ClientSession() as session:
        # Test basic query
        query = """
        {
            pools(first: 1) {
                id
                totalValueLockedUSD
            }
        }
        """

        url = _get_subgraph_url()
        result = await _execute_graphql_query(session, url, query)

        if result and "pools" in result:
            print(f"✓ Uniswap V3 Subgraph API connection successful")
            print(f"  URL: {url}")
            print(f"  Sample pool: {result['pools'][0] if result['pools'] else 'None'}")
            return True
        else:
            print(f"✗ Uniswap V3 Subgraph API connection failed")
            return False


if __name__ == "__main__":
    # Standalone test
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path.cwd().parent))

    from config import MIN_DEX_LIQUIDITY
    from config.logging_config import setup_logging

    setup_logging()

    async def main():
        print("Testing Uniswap V3 Scanner...")

        # Test API connection
        await test_api_connection()

        # Test full scan
        async with aiohttp.ClientSession() as session:
            results = await scan(session)
            print(f"\nFound {len(results)} candidates:")
            for i, candidate in enumerate(results[:5], 1):
                print(
                    f"  {i}. {candidate['cex_symbol']} on {candidate['network']} - Score: {candidate['score']}"
                )

    asyncio.run(main())
