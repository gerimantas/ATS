"""
Moralis DEX Scanner for Multi-Chain Analysis
Uses Moralis Web3 API to find promising tokens across multiple chains
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

logger = get_logger("scanners.moralis_scanner")

# Moralis API configuration
MORALIS_BASE_URL = "https://deep-index.moralis.io/api/v2"

# Supported chains and their configurations
SUPPORTED_CHAINS = {
    "eth": {
        "name": "Ethereum",
        "native_token": "0x0000000000000000000000000000000000000000",
        "stable_tokens": [
            "0xA0b86a33E6441d07b651c6cD6e2c35b43aA47Fbe",  # USDC
            "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
        ],
    },
    "polygon": {
        "name": "Polygon",
        "native_token": "0x0000000000000000000000000000000000000000",
        "stable_tokens": [
            "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC.e
            "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",  # USDT
        ],
    },
    "bsc": {
        "name": "BSC",
        "native_token": "0x0000000000000000000000000000000000000000",
        "stable_tokens": [
            "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",  # USDC
            "0x55d398326f99059fF775485246999027B3197955",  # USDT
        ],
    },
}


async def _check_cex_symbol_exists(session, symbol):
    """Quick check if a symbol exists on Binance"""
    try:
        symbols_to_try = [f"{symbol}USDT", f"{symbol}USD", f"{symbol}BUSD"]
        for symbol_pair in symbols_to_try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_pair}"
            async with session.get(url, timeout=2) as response:
                if response.status == 200:
                    return True
        return False
    except:
        return False


async def _get_moralis_headers():
    """Get Moralis API headers"""
    api_key = os.getenv("MORALIS_API_KEY")
    if not api_key:
        logger.error("MORALIS_API_KEY not found in environment variables")
        return None

    return {"X-API-Key": api_key, "Accept": "application/json"}


async def _get_token_price(
    session: aiohttp.ClientSession, token_address: str, chain: str
) -> Optional[float]:
    """Get token price from Moralis"""
    try:
        headers = await _get_moralis_headers()
        if not headers:
            return None

        url = f"{MORALIS_BASE_URL}/erc20/{token_address}/price"
        params = {"chain": chain}

        async with session.get(
            url, headers=headers, params=params, timeout=10
        ) as response:
            if response.status == 200:
                data = await response.json()
                price = data.get("usdPrice")
                if price:
                    return float(price)
            elif response.status == 400:
                logger.debug(f"Token {token_address} not found on {chain}")
            else:
                logger.warning(f"Moralis price request failed: {response.status}")

        return None
    except Exception as e:
        logger.debug(f"Error getting price for {token_address} on {chain}: {e}")
        return None


async def _get_top_tokens_by_market_cap(
    session: aiohttp.ClientSession, chain: str, limit: int = 50
) -> List[Dict]:
    """Get top tokens by market cap from Moralis (if available)"""
    try:
        headers = await _get_moralis_headers()
        if not headers:
            return []

        # Note: This endpoint might require higher tier - using as example
        url = f"{MORALIS_BASE_URL}/market-data/erc20s/top-tokens"
        params = {"chain": chain, "limit": limit}

        async with session.get(
            url, headers=headers, params=params, timeout=15
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("result", [])
            else:
                logger.debug(f"Top tokens endpoint failed: {response.status}")
                return []

    except Exception as e:
        logger.debug(f"Error getting top tokens for {chain}: {e}")
        return []


async def _get_token_metadata(
    session: aiohttp.ClientSession, token_address: str, chain: str
) -> Optional[Dict]:
    """Get token metadata from Moralis"""
    try:
        headers = await _get_moralis_headers()
        if not headers:
            return None

        url = f"{MORALIS_BASE_URL}/erc20/metadata"
        params = {"chain": chain, "addresses[]": token_address}

        async with session.get(
            url, headers=headers, params=params, timeout=10
        ) as response:
            if response.status == 200:
                data = await response.json()
                if data and len(data) > 0:
                    return data[0]
            else:
                logger.debug(
                    f"Metadata request failed for {token_address}: {response.status}"
                )

        return None
    except Exception as e:
        logger.debug(f"Error getting metadata for {token_address}: {e}")
        return None


def _calculate_activity_score(token_data: Dict, price: float, chain: str) -> float:
    """Calculate activity score for a token"""
    try:
        base_score = 10

        # Price availability bonus
        price_bonus = 20 if price and price > 0 else 0

        # Chain preference (Ethereum gets higher score)
        chain_bonus = {"eth": 30, "polygon": 20, "bsc": 15}.get(chain, 10)

        # Symbol quality (shorter = better)
        symbol = token_data.get("symbol", "")
        symbol_bonus = max(15 - len(symbol), 0) if len(symbol) <= 8 else 0

        # Decimals standard (18 is common, gets bonus)
        decimals = token_data.get("decimals", 0)
        decimals_bonus = 10 if decimals == 18 else 5

        total_score = (
            base_score + price_bonus + chain_bonus + symbol_bonus + decimals_bonus
        )

        # Price range filter
        if price and (price > 10000 or price < 0.000001):
            total_score *= 0.5  # Penalty for extreme prices

        return min(total_score, 100)

    except Exception as e:
        logger.debug(f"Error calculating activity score: {e}")
        return 0.0


async def scan(session: aiohttp.ClientSession) -> List[Dict]:
    """
    Scans Moralis for promising tokens across multiple chains.
    Returns a list of candidate pairs in standardized format.
    """
    logger.info("Executing moralis_scanner...")
    candidate_pairs = []

    try:
        # Check API key availability
        headers = await _get_moralis_headers()
        if not headers:
            logger.error("Moralis API key not available")
            return []

        # Test tokens (well-known addresses for testing)
        test_tokens = {
            "eth": [
                "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",  # UNI
                "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0",  # MATIC
                "0xA0b86a33E6441d07b651c6cD6e2c35b43aA47Fbe",  # USDC (test)
            ],
            "polygon": [
                "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",  # WMATIC
                "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC.e (test)
            ],
            "bsc": [
                "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",  # ETH
                "0x1D2F0da169ceB9fC7B3144628dB156f3F6c60dBE",  # XRP
            ],
        }

        processed_count = 0
        for chain, token_addresses in test_tokens.items():
            if processed_count >= 10:  # Conservative limit across all chains
                break

            logger.info(f"Scanning {SUPPORTED_CHAINS[chain]['name']} chain...")

            for token_address in token_addresses:
                if processed_count >= 10:
                    break

                # Get token metadata
                metadata = await _get_token_metadata(session, token_address, chain)
                if not metadata:
                    continue

                symbol = metadata.get("symbol", "")
                if len(symbol) < 2 or len(symbol) > 8:
                    continue

                # Skip stablecoins and common base tokens
                if symbol.upper() in [
                    "USDC",
                    "USDT",
                    "DAI",
                    "BUSD",
                    "ETH",
                    "BNB",
                    "MATIC",
                ]:
                    continue

                # Check if symbol exists on CEX
                if not await _check_cex_symbol_exists(session, symbol):
                    continue

                # Get token price
                price = await _get_token_price(session, token_address, chain)
                if not price or price <= 0:
                    continue

                # Calculate activity score
                activity_score = _calculate_activity_score(metadata, price, chain)

                if activity_score > 25:  # Minimum threshold
                    candidate_pairs.append(
                        {
                            "cex_symbol": symbol,
                            "dex_pair_address": token_address,
                            "dex_data": {
                                "price": price,
                                "liquidity": 100000,  # Placeholder - Moralis doesn't provide direct liquidity
                                "volume_h24": 0,  # Placeholder - would need additional calls
                                "token_name": metadata.get("name", symbol),
                                "chain": chain,
                                "decimals": metadata.get("decimals", 18),
                                "chain_name": SUPPORTED_CHAINS[chain]["name"],
                            },
                            "score": activity_score,
                        }
                    )
                    processed_count += 1

                # Rate limiting
                await asyncio.sleep(0.2)  # 5 requests per second max

    except aiohttp.ClientError as e:
        logger.error(f"Network error in moralis_scanner: {type(e).__name__}")
        return []
    except asyncio.TimeoutError:
        logger.error("Timeout error in moralis_scanner")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in moralis_scanner: {e}")
        return []

    logger.info(f"Moralis scanner found {len(candidate_pairs)} potential candidates")
    return candidate_pairs
