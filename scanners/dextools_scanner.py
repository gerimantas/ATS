"""
DEXTools Scanner for Advanced DEX Analytics
Uses DEXTools API for sophisticated token screening and social sentiment analysis
"""

import aiohttp
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import MIN_DEX_LIQUIDITY
from config.logging_config import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("scanners.dextools_scanner")

# DEXTools API configuration
DEXTOOLS_BASE_URL = "https://www.dextools.io/shared/data/pair"
DEXTOOLS_API_URL = "https://api.dextools.io/v1"  # Alternative endpoint
DEFAULT_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.0  # 1 second between requests for free tier

# Supported chains for scanning
SUPPORTED_CHAINS = [
    "ether",  # Ethereum
    "bsc",  # Binance Smart Chain
    "polygon",  # Polygon
    "solana",  # Solana
    "avalanche",  # Avalanche
    "arbitrum",  # Arbitrum
]


def _get_dextools_headers() -> Dict[str, str]:
    """Get headers for DEXTools API requests"""
    api_key = os.getenv("DEXTOOLS_API_KEY")
    if not api_key:
        logger.error("DEXTOOLS_API_KEY not found in environment variables")
        return {}

    return {"accept": "application/json", "X-API-KEY": api_key}


async def _get_hot_pairs(session: aiohttp.ClientSession, chain: str) -> List[Dict]:
    """Get hot trading pairs for a specific chain using DexScreener as fallback"""

    # Use DexScreener free API since DEXTools API has connectivity issues
    chain_map = {
        "ether": "ethereum",
        "bsc": "bsc",
        "polygon": "polygon",
        "solana": "solana",
        "avalanche": "avalanche",
        "arbitrum": "arbitrum",
    }

    chain_name = chain_map.get(chain, "ethereum")
    # Use DexScreener search endpoint with chain filter
    url = f"https://api.dexscreener.com/latest/dex/tokens/trending"

    try:
        await asyncio.sleep(RATE_LIMIT_DELAY)  # Rate limiting

        # Use DexScreener free API as fallback
        async with session.get(url, timeout=DEFAULT_TIMEOUT) as response:
            if response.status == 200:
                data = await response.json()
                # Token trending endpoint returns tokens array, not pairs
                tokens = data.get("tokens", [])

                # Convert tokens to pairs format
                hot_pairs = []
                for token in tokens[:20]:  # Take first 20
                    # Get the best pair for this token
                    pairs = token.get("pairs", [])
                    if not pairs:
                        continue

                    best_pair = max(
                        pairs, key=lambda p: p.get("volume", {}).get("h24", 0)
                    )

                    # Filter by chain name
                    if (
                        best_pair.get("chainId") != chain_name
                        and chain_name != "ethereum"
                    ):
                        continue

                    if (
                        best_pair.get("volume", {}).get("h24", 0)
                        > 10000  # $10k+ volume
                        and best_pair.get("txns", {}).get("h24", {}).get("buys", 0) > 5
                    ):  # 5+ buy txns                        # Convert to DEXTools-like format
                        converted_pair = {
                            "pairAddress": best_pair.get("pairAddress"),
                            "volume": best_pair.get("volume", {}).get("h24", 0),
                            "variation": best_pair.get("priceChange", {}).get("h24", 0),
                            "liquidity": best_pair.get("liquidity", {}).get("usd", 0),
                            "transactions": (
                                best_pair.get("txns", {}).get("h24", {}).get("buys", 0)
                                + best_pair.get("txns", {})
                                .get("h24", {})
                                .get("sells", 0)
                            ),
                            "token0": {
                                "symbol": best_pair.get("baseToken", {}).get(
                                    "symbol", ""
                                ),
                                "address": best_pair.get("baseToken", {}).get(
                                    "address", ""
                                ),
                            },
                            "token1": {
                                "symbol": best_pair.get("quoteToken", {}).get(
                                    "symbol", ""
                                ),
                                "address": best_pair.get("quoteToken", {}).get(
                                    "address", ""
                                ),
                            },
                        }
                        hot_pairs.append(converted_pair)

                logger.debug(
                    f"Found {len(hot_pairs)} hot pairs on {chain} (via DexScreener)"
                )
                return hot_pairs

            else:
                logger.warning(
                    f"DexScreener request failed for {chain}: {response.status}"
                )
                return []

    except asyncio.TimeoutError:
        logger.warning(f"Timeout getting hot pairs for {chain}")
        return []
    except Exception as e:
        logger.error(f"Error getting hot pairs for {chain}: {e}")
        return []


async def _get_token_info(
    session: aiohttp.ClientSession, chain: str, token_address: str
) -> Optional[Dict]:
    """Get detailed token information"""
    headers = _get_dextools_headers()
    if not headers:
        return None

    url = f"{DEXTOOLS_BASE_URL}/token/{chain}/{token_address}/info"

    try:
        await asyncio.sleep(RATE_LIMIT_DELAY)  # Rate limiting

        async with session.get(
            url, headers=headers, timeout=DEFAULT_TIMEOUT
        ) as response:
            if response.status == 200:
                data = await response.json()
                token_info = data.get("data", {})
                return token_info
            elif response.status == 429:
                logger.warning(f"Rate limited on token info for {token_address}")
                await asyncio.sleep(3)
                return None
            else:
                logger.debug(
                    f"Token info request failed for {token_address}: {response.status}"
                )
                return None

    except asyncio.TimeoutError:
        logger.warning(f"Timeout getting token info for {token_address}")
        return None
    except Exception as e:
        logger.debug(f"Error getting token info for {token_address}: {e}")
        return None


async def _get_pair_info(
    session: aiohttp.ClientSession, chain: str, pair_address: str
) -> Optional[Dict]:
    """Get detailed pair information including metrics"""
    headers = _get_dextools_headers()
    if not headers:
        return None

    url = f"{DEXTOOLS_BASE_URL}/pair/{chain}/{pair_address}"

    try:
        await asyncio.sleep(RATE_LIMIT_DELAY)  # Rate limiting

        async with session.get(
            url, headers=headers, timeout=DEFAULT_TIMEOUT
        ) as response:
            if response.status == 200:
                data = await response.json()
                pair_info = data.get("data", {})
                return pair_info
            elif response.status == 429:
                logger.warning(f"Rate limited on pair info for {pair_address}")
                await asyncio.sleep(3)
                return None
            else:
                logger.debug(
                    f"Pair info request failed for {pair_address}: {response.status}"
                )
                return None

    except asyncio.TimeoutError:
        logger.warning(f"Timeout getting pair info for {pair_address}")
        return None
    except Exception as e:
        logger.debug(f"Error getting pair info for {pair_address}: {e}")
        return None


def _calculate_dextools_score(
    pair: Dict, token_info: Optional[Dict] = None, pair_info: Optional[Dict] = None
) -> float:
    """Calculate opportunity score based on DEXTools metrics"""
    try:
        score = 0.0

        # Basic pair metrics
        volume_24h = float(pair.get("volume", 0))
        price_change = abs(float(pair.get("variation", 0)))
        liquidity = float(pair.get("liquidity", 0))

        # Volume score (25% weight)
        if volume_24h > 50000:  # > $50k daily volume
            volume_score = min(volume_24h / 500000, 5) * 5  # Max 25 points
        else:
            volume_score = (volume_24h / 50000) * 5
        score += volume_score

        # Price change score (20% weight) - moderate movement preferred
        if 1 <= price_change <= 20:  # 1-20% change is ideal
            change_score = 20
        elif price_change < 1:
            change_score = price_change * 15
        else:  # > 20% change
            change_score = max(0, 20 - (price_change - 20) * 0.5)
        score += change_score

        # Liquidity score (25% weight)
        if liquidity >= MIN_DEX_LIQUIDITY:
            liquidity_score = (
                min(liquidity / MIN_DEX_LIQUIDITY, 4) * 6.25
            )  # Max 25 points
            score += liquidity_score

        # Token-specific scoring if available
        if token_info:
            # Token reputation score (15% weight)
            reputation = token_info.get("reputation", 0)
            if reputation:
                reputation_score = min(int(reputation), 5) * 3  # Max 15 points
                score += reputation_score

            # Token metrics (audit, social, etc.)
            metrics = token_info.get("metrics", {})
            if metrics:
                # Social metrics bonus
                if metrics.get("socialScore", 0) > 50:
                    score += 5

                # Audit bonus
                if metrics.get("auditScore", 0) > 70:
                    score += 5

        # Pair-specific bonuses
        if pair_info:
            pair_data = pair_info.get("pair", {})

            # DEX bonus - prefer established DEXes
            dex_name = pair_data.get("dex", {}).get("name", "").lower()
            if dex_name in ["uniswap", "pancakeswap", "quickswap", "sushiswap"]:
                score += 10

            # Creation time bonus - avoid very new pairs
            created_at = pair_data.get("creationTime")
            if created_at:
                # Prefer pairs older than 7 days but younger than 90 days
                import time

                age_days = (time.time() - int(created_at)) / 86400
                if 7 <= age_days <= 90:
                    score += 5

        # Transaction count bonus
        transactions = int(pair.get("transactions", 0))
        if transactions > 100:
            tx_score = min(transactions / 100, 3) * 5  # Max 15 points
            score += tx_score

        return min(score, 100.0)  # Cap at 100

    except (ValueError, TypeError, KeyError) as e:
        logger.warning(f"Error calculating DEXTools score: {e}")
        return 0.0


def _extract_token_symbol(pair: Dict) -> tuple:
    """Extract base and quote token symbols from pair"""
    try:
        token0 = pair.get("token0", {})
        token1 = pair.get("token1", {})

        base_symbol = token0.get("symbol", "").upper()
        quote_symbol = token1.get("symbol", "").upper()

        # Determine which is base and which is quote
        stable_coins = {"USDT", "USDC", "DAI", "BUSD", "UST"}
        wrapped_natives = {"WETH", "WBNB", "WMATIC", "WAVAX"}

        if quote_symbol in stable_coins:
            return base_symbol, quote_symbol, token0.get("address")
        elif base_symbol in stable_coins:
            return quote_symbol, base_symbol, token1.get("address")
        elif quote_symbol in wrapped_natives:
            return base_symbol, quote_symbol, token0.get("address")
        elif base_symbol in wrapped_natives:
            return quote_symbol, base_symbol, token1.get("address")
        else:
            # Default to token0 as base
            return base_symbol, quote_symbol, token0.get("address")

    except Exception as e:
        logger.warning(f"Error extracting token symbols: {e}")
        return "", "", ""


async def scan(session: aiohttp.ClientSession) -> List[Dict]:
    """
    Main scanning function for DEXTools scanner
    Returns list of promising DEX opportunities based on advanced analytics
    """
    logger.info("Executing dextools_scanner...")

    # Check API key
    if not os.getenv("DEXTOOLS_API_KEY"):
        logger.error("DEXTools API key not available")
        return []

    all_candidates = []

    try:
        for chain in SUPPORTED_CHAINS:
            logger.info(f"Scanning {chain} chain...")

            # Get hot pairs for this chain
            hot_pairs = await _get_hot_pairs(session, chain)

            if not hot_pairs:
                continue

            # Process each hot pair
            for pair in hot_pairs[:8]:  # Limit to top 8 per chain for free tier
                try:
                    pair_address = pair.get("pairAddress")
                    if not pair_address:
                        continue

                    # Extract token information
                    base_symbol, quote_symbol, token_address = _extract_token_symbol(
                        pair
                    )

                    if not base_symbol or base_symbol in {"WETH", "WBNB", "WMATIC"}:
                        continue

                    # Get additional token and pair information
                    token_info = None
                    pair_info = None

                    if token_address:
                        token_info = await _get_token_info(
                            session, chain, token_address
                        )
                        pair_info = await _get_pair_info(session, chain, pair_address)

                    # Calculate opportunity score
                    score = _calculate_dextools_score(pair, token_info, pair_info)

                    if score < 25:  # Minimum score threshold
                        continue

                    # Create candidate entry
                    candidate = {
                        "cex_symbol": f"{base_symbol}/USDT",
                        "dex_pair_address": pair_address,
                        "score": round(score, 1),
                        "chain": chain,
                        "base_token": base_symbol,
                        "quote_token": quote_symbol,
                        "volume_24h": pair.get("volume", 0),
                        "price_change_24h": pair.get("variation", 0),
                        "liquidity": pair.get("liquidity", 0),
                        "transactions_24h": pair.get("transactions", 0),
                        "scanner_source": "dextools",
                    }

                    # Add token-specific data if available
                    if token_info:
                        candidate["token_reputation"] = token_info.get("reputation", 0)
                        metrics = token_info.get("metrics", {})
                        if metrics:
                            candidate["social_score"] = metrics.get("socialScore", 0)
                            candidate["audit_score"] = metrics.get("auditScore", 0)

                    all_candidates.append(candidate)

                except Exception as e:
                    logger.warning(f"Error processing hot pair on {chain}: {e}")
                    continue

        # Sort by score and return top candidates
        all_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = all_candidates[:12]  # Return top 12

        logger.info(
            f"DEXTools scanner found {len(top_candidates)} potential candidates"
        )
        return top_candidates

    except Exception as e:
        logger.error(f"DEXTools scanner error: {e}")
        return []


# Test functions for development
async def test_api_connection():
    """Test DEXTools API connection"""
    async with aiohttp.ClientSession() as session:
        # Test getting hot pairs for Ethereum
        pairs = await _get_hot_pairs(session, "ether")
        return len(pairs) > 0


async def test_scanner():
    """Test the full scanner functionality"""
    async with aiohttp.ClientSession() as session:
        results = await scan(session)
        return results


if __name__ == "__main__":
    # Simple test when run directly
    async def main():
        print("Testing DEXTools Scanner...")

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
