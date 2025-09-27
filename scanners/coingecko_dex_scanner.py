"""
CoinGecko DEX Scanner for Multi-Chain DEX Analysis
Uses CoinGecko's GeckoTerminal API to find promising DEX tokens and pools
"""

import aiohttp
import asyncio
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from config import MIN_DEX_LIQUIDITY
from config.logging_config import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("scanners.coingecko_dex_scanner")

# CoinGecko DEX API configuration
COINGECKO_BASE_URL = "https://api.geckoterminal.com/api/v2"
DEFAULT_TIMEOUT = 30
RATE_LIMIT_DELAY = 0.5  # 500ms between requests for free tier

# Supported networks for scanning
SUPPORTED_NETWORKS = [
    "eth",  # Ethereum
    "bsc",  # Binance Smart Chain
    "polygon",  # Polygon
    "solana",  # Solana
    "avalanche",  # Avalanche
    "arbitrum",  # Arbitrum
]


def _get_coingecko_headers() -> Dict[str, str]:
    """Get headers for CoinGecko API requests"""
    api_key = os.getenv("COINGECKO_API_KEY")
    if not api_key:
        logger.error("COINGECKO_API_KEY not found in environment variables")
        return {}

    return {"accept": "application/json", "x-cg-demo-api-key": api_key}


async def _get_trending_pools(
    session: aiohttp.ClientSession, network: str
) -> List[Dict]:
    """Get trending pools for a specific network"""
    headers = _get_coingecko_headers()
    if not headers:
        return []

    url = f"{COINGECKO_BASE_URL}/networks/{network}/trending_pools"

    try:
        await asyncio.sleep(RATE_LIMIT_DELAY)  # Rate limiting

        async with session.get(
            url, headers=headers, timeout=DEFAULT_TIMEOUT
        ) as response:
            if response.status == 200:
                data = await response.json()
                pools = data.get("data", [])
                logger.debug(f"Found {len(pools)} trending pools on {network}")
                return pools
            elif response.status == 429:
                logger.warning(f"Rate limited on {network} trending pools")
                await asyncio.sleep(2)
                return []
            else:
                logger.warning(
                    f"CoinGecko trending pools request failed for {network}: {response.status}"
                )
                return []

    except asyncio.TimeoutError:
        logger.warning(f"Timeout getting trending pools for {network}")
        return []
    except Exception as e:
        logger.error(f"Error getting trending pools for {network}: {e}")
        return []


async def _get_pool_details(
    session: aiohttp.ClientSession, network: str, pool_address: str
) -> Optional[Dict]:
    """Get detailed information about a specific pool"""
    headers = _get_coingecko_headers()
    if not headers:
        return None

    url = f"{COINGECKO_BASE_URL}/networks/{network}/pools/{pool_address}"

    try:
        await asyncio.sleep(RATE_LIMIT_DELAY)  # Rate limiting

        async with session.get(
            url, headers=headers, timeout=DEFAULT_TIMEOUT
        ) as response:
            if response.status == 200:
                data = await response.json()
                pool_data = data.get("data", {})
                return pool_data
            elif response.status == 429:
                logger.warning(f"Rate limited on pool details for {pool_address}")
                await asyncio.sleep(2)
                return None
            else:
                logger.warning(
                    f"Pool details request failed for {pool_address}: {response.status}"
                )
                return None

    except asyncio.TimeoutError:
        logger.warning(f"Timeout getting pool details for {pool_address}")
        return None
    except Exception as e:
        logger.error(f"Error getting pool details for {pool_address}: {e}")
        return None


def _calculate_opportunity_score(
    pool: Dict, pool_details: Optional[Dict] = None
) -> float:
    """Calculate opportunity score based on pool metrics"""
    try:
        attributes = pool.get("attributes", {})

        # Base metrics from pool
        volume_24h = float(attributes.get("volume_usd", {}).get("h24", 0))
        price_change_24h = abs(
            float(attributes.get("price_change_percentage", {}).get("h24", 0))
        )
        reserve_usd = float(attributes.get("reserve_in_usd", 0))

        # Additional metrics from detailed pool info
        if pool_details:
            detail_attrs = pool_details.get("attributes", {})
            volume_7d = float(
                detail_attrs.get("volume_usd", {}).get("h168", volume_24h)
            )
            transactions_24h = int(
                detail_attrs.get("transactions", {}).get("h24", {}).get("buys", 0)
                + detail_attrs.get("transactions", {}).get("h24", {}).get("sells", 0)
            )
        else:
            volume_7d = volume_24h
            transactions_24h = 10  # Default estimate

        # Scoring algorithm
        score = 0.0

        # Volume score (30% weight)
        if volume_24h > 100000:  # > $100k daily volume
            volume_score = min(volume_24h / 1000000, 10) * 3  # Max 30 points
        else:
            volume_score = (volume_24h / 100000) * 1.5
        score += volume_score

        # Volatility score (25% weight) - moderate volatility preferred
        if 2 <= price_change_24h <= 15:  # 2-15% change is ideal
            volatility_score = 25
        elif price_change_24h < 2:
            volatility_score = price_change_24h * 10
        else:  # > 15% change
            volatility_score = max(0, 25 - (price_change_24h - 15))
        score += volatility_score

        # Liquidity score (25% weight)
        if reserve_usd >= MIN_DEX_LIQUIDITY:
            liquidity_score = (
                min(reserve_usd / MIN_DEX_LIQUIDITY, 5) * 5
            )  # Max 25 points
            score += liquidity_score

        # Activity score (20% weight)
        if transactions_24h > 50:
            activity_score = min(transactions_24h / 50, 4) * 5  # Max 20 points
            score += activity_score

        # Volume trend bonus
        if (
            volume_7d > 0 and volume_24h > volume_7d / 7 * 1.2
        ):  # 20% above 7-day average
            score += 10

        return min(score, 100.0)  # Cap at 100

    except (ValueError, TypeError, KeyError) as e:
        logger.warning(f"Error calculating score for pool: {e}")
        return 0.0


async def _find_cex_symbol(
    session: aiohttp.ClientSession, token_address: str, network: str
) -> Optional[str]:
    """Find corresponding CEX symbol for a DEX token"""
    try:
        # Use CoinGecko token info endpoint
        headers = _get_coingecko_headers()
        if not headers:
            return None

        # Map network names
        network_map = {
            "eth": "ethereum",
            "bsc": "binance-smart-chain",
            "polygon": "polygon-pos",
            "solana": "solana",
            "avalanche": "avalanche",
            "arbitrum": "arbitrum-one",
        }

        platform = network_map.get(network, network)

        # Try to get token info from CoinGecko
        url = f"https://api.coingecko.com/api/v3/coins/{platform}/contract/{token_address}"

        await asyncio.sleep(RATE_LIMIT_DELAY)

        async with session.get(url, headers=headers, timeout=15) as response:
            if response.status == 200:
                data = await response.json()
                symbol = data.get("symbol", "").upper()
                if symbol:
                    # Common CEX symbol mappings
                    if symbol == "WETH":
                        return "ETH"
                    elif symbol == "WBTC":
                        return "BTC"
                    elif symbol.startswith("W") and len(symbol) <= 5:
                        return symbol[1:]  # Remove "W" prefix
                    return symbol

    except Exception as e:
        logger.debug(f"Could not find CEX symbol for {token_address}: {e}")

    return None


async def scan(session: aiohttp.ClientSession) -> List[Dict]:
    """
    Main scanning function for CoinGecko DEX scanner
    Returns list of promising DEX opportunities
    """
    logger.info("Executing coingecko_dex_scanner...")

    # Check API key
    if not os.getenv("COINGECKO_API_KEY"):
        logger.error("CoinGecko API key not available")
        return []

    all_candidates = []

    try:
        for network in SUPPORTED_NETWORKS:
            logger.info(f"Scanning {network} network...")

            # Get trending pools for this network
            trending_pools = await _get_trending_pools(session, network)

            if not trending_pools:
                continue

            # Process each trending pool
            for pool in trending_pools[:5]:  # Limit to top 5 per network
                try:
                    attributes = pool.get("attributes", {})
                    pool_address = attributes.get("address")

                    if not pool_address:
                        continue

                    # Get detailed pool information
                    pool_details = await _get_pool_details(
                        session, network, pool_address
                    )

                    # Calculate opportunity score
                    score = _calculate_opportunity_score(pool, pool_details)

                    if score < 30:  # Minimum score threshold
                        continue

                    # Extract token information
                    base_token = attributes.get("base_token", {})
                    quote_token = attributes.get("quote_token", {})

                    base_symbol = base_token.get("symbol", "").upper()
                    base_address = base_token.get("address", "")

                    # Skip common stablecoins and wrapped tokens as base
                    skip_tokens = {
                        "USDT",
                        "USDC",
                        "DAI",
                        "BUSD",
                        "WETH",
                        "WBNB",
                        "WMATIC",
                    }
                    if base_symbol in skip_tokens:
                        continue

                    # Try to find CEX equivalent
                    cex_symbol = await _find_cex_symbol(session, base_address, network)
                    if not cex_symbol:
                        cex_symbol = base_symbol

                    # Create candidate entry
                    candidate = {
                        "cex_symbol": f"{cex_symbol}/USDT",
                        "dex_pair_address": pool_address,
                        "score": round(score, 1),
                        "network": network,
                        "base_token": base_symbol,
                        "quote_token": quote_token.get("symbol", "").upper(),
                        "volume_24h": attributes.get("volume_usd", {}).get("h24", 0),
                        "price_change_24h": attributes.get(
                            "price_change_percentage", {}
                        ).get("h24", 0),
                        "reserve_usd": attributes.get("reserve_in_usd", 0),
                        "scanner_source": "coingecko_dex",
                    }

                    all_candidates.append(candidate)

                except Exception as e:
                    logger.warning(f"Error processing pool on {network}: {e}")
                    continue

        # Sort by score and return top candidates
        all_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = all_candidates[:10]  # Return top 10

        logger.info(
            f"CoinGecko DEX scanner found {len(top_candidates)} potential candidates"
        )
        return top_candidates

    except Exception as e:
        logger.error(f"CoinGecko DEX scanner error: {e}")
        return []


# Test functions for development
async def test_api_connection():
    """Test CoinGecko DEX API connection"""
    async with aiohttp.ClientSession() as session:
        # Test getting trending pools for Ethereum
        pools = await _get_trending_pools(session, "eth")
        return len(pools) > 0


async def test_scanner():
    """Test the full scanner functionality"""
    async with aiohttp.ClientSession() as session:
        results = await scan(session)
        return results


if __name__ == "__main__":
    # Simple test when run directly
    async def main():
        print("Testing CoinGecko DEX Scanner...")

        # Test API connection
        print("Testing API connection...")
        connected = await test_api_connection()
        print(f"API Connection: {'✓' if connected else '✗'}")

        # Test full scanner
        print("Testing full scanner...")
        results = await test_scanner()
        print(f"Found {len(results)} candidates")

        for i, result in enumerate(results[:3], 1):
            print(f"  {i}. {result['cex_symbol']} - Score: {result['score']}")

    asyncio.run(main())
