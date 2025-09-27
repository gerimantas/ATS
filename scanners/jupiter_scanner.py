"""
Jupiter DEX Scanner for Solana - Fixed Implementation
Uses Jupiter aggregator API for liquidity analysis only
Prices are obtained from external sources for accuracy
"""

import aiohttp
import asyncio
from typing import List, Dict, Optional
from config import MIN_DEX_LIQUIDITY
from config.logging_config import get_logger

logger = get_logger("scanners.jupiter_scanner")

# Jupiter API endpoints
JUPITER_TOKEN_LIST_URL = "https://token.jup.ag/all"
JUPITER_QUOTE_API_URL = "https://quote-api.jup.ag/v6/quote"

# Known token addresses for Solana
SOL_ADDRESS = "So11111111111111111111111111111111111111112"
USDC_ADDRESS = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT_ADDRESS = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"

# Common token decimals for Solana (simplified mapping)
TOKEN_DECIMALS = {
    SOL_ADDRESS: 9,
    USDC_ADDRESS: 6,
    USDT_ADDRESS: 6,
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


async def _get_token_list(session: aiohttp.ClientSession) -> Optional[List[Dict]]:
    """Get Jupiter token list"""
    try:
        async with session.get(JUPITER_TOKEN_LIST_URL, timeout=10) as response:
            if response.status == 200:
                tokens = await response.json()
                logger.debug(f"Retrieved {len(tokens)} tokens from Jupiter")
                return tokens
            else:
                logger.warning(f"Jupiter token list request failed: {response.status}")
                return None
    except Exception as e:
        logger.error(f"Error fetching Jupiter token list: {e}")
        return None

        return None


async def _get_price_from_dexscreener(
    session: aiohttp.ClientSession, token_address: str
) -> Optional[float]:
    """Get token price from DexScreener as backup"""
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
        async with session.get(url, timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                pairs = data.get("pairs", [])
                if pairs:
                    # Get the first pair with USD price
                    for pair in pairs:
                        if pair.get("quoteToken", {}).get("symbol") in ["USDC", "USDT"]:
                            price = pair.get("priceUsd")
                            if price:
                                return float(price)
        return None
    except Exception as e:
        logger.debug(f"Error getting price from DexScreener for {token_address}: {e}")
        return None


async def _get_quote(
    session: aiohttp.ClientSession, input_mint: str, output_mint: str, amount: int
) -> Optional[Dict]:
    """Get swap quote from Jupiter"""
    try:
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": 50,  # 0.5% slippage
        }

        async with session.get(
            JUPITER_QUOTE_API_URL, params=params, timeout=10
        ) as response:
            if response.status == 200:
                quote_data = await response.json()
                logger.debug(f"Retrieved quote for {input_mint} -> {output_mint}")
                return quote_data
            else:
                logger.debug(
                    f"Quote request failed: {response.status} for {input_mint}"
                )
                return None
    except Exception as e:
        logger.debug(f"Error getting quote for {input_mint}: {e}")
        return None


def _calculate_liquidity_score(quote_data: Dict) -> float:
    """Calculate liquidity score based on quote data"""
    try:
        in_amount = float(quote_data.get("inAmount", 0))
        out_amount = float(quote_data.get("outAmount", 0))

        if in_amount == 0 or out_amount == 0:
            return 0.0

        # Calculate price impact (lower is better)
        expected_rate = out_amount / in_amount

        # Routes count (more routes = better liquidity)
        routes_plan = quote_data.get("routePlan", [])
        routes_count = len(routes_plan)

        # Base score from route availability
        route_score = min(routes_count * 20, 100)  # Max 100 for 5+ routes

        # Liquidity depth estimation (simplified)
        liquidity_estimate = in_amount * expected_rate

        return min(route_score + (liquidity_estimate / 10000), 100)

    except Exception as e:
        logger.debug(f"Error calculating liquidity score: {e}")
        return 0.0


def _calculate_activity_score(
    token_data: Dict, price_data: Dict, liquidity_score: float
) -> float:
    """Calculate overall activity score for a token"""
    try:
        # Base score from token verification
        base_score = (
            10
            if token_data.get("tags", []) and "verified" in token_data.get("tags", [])
            else 5
        )

        # Price availability bonus
        price_bonus = 20 if price_data else 0

        # Liquidity score (0-100)
        liquidity_bonus = liquidity_score * 0.6  # Weight liquidity heavily

        # Symbol length penalty (shorter symbols often better established)
        symbol = token_data.get("symbol", "")
        symbol_bonus = max(10 - len(symbol), 0) if len(symbol) <= 10 else 0

        total_score = base_score + price_bonus + liquidity_bonus + symbol_bonus

        return min(total_score, 100)

    except Exception as e:
        logger.debug(f"Error calculating activity score: {e}")
        return 0.0


async def scan(session: aiohttp.ClientSession) -> List[Dict]:
    """
    Scans Jupiter for promising Solana tokens and calculates activity scores.
    Returns a list of candidate pairs in standardized format.
    """
    logger.info("Executing jupiter_scanner...")
    candidate_pairs = []

    try:
        # Step 1: Get token list
        tokens = await _get_token_list(session)
        if not tokens:
            logger.warning("No tokens received from Jupiter API")
            return []

        # Step 2: Filter tokens (verified, reasonable symbol length)
        filtered_tokens = []
        for token in tokens:
            symbol = token.get("symbol", "")
            tags = token.get("tags", [])

            # Basic filtering
            if (
                len(symbol) >= 2
                and len(symbol) <= 8
                and symbol.upper() not in ["SOL", "USDC", "USDT"]  # Skip base tokens
                and not symbol.startswith("$")
            ):  # Skip meme tokens with $

                filtered_tokens.append(token)

        logger.info(f"Filtered to {len(filtered_tokens)} potential tokens")

        # Step 3: Limit tokens for performance
        if len(filtered_tokens) > 20:
            filtered_tokens = filtered_tokens[:20]  # Conservative limit

        # Step 4: For each token, get liquidity data and price
        processed_count = 0
        for token in filtered_tokens:
            if processed_count >= 10:  # Very conservative limit
                break

            token_address = token["address"]
            symbol = token["symbol"]

            # Check if symbol exists on CEX first (faster check)
            if not await _check_cex_symbol_exists(session, symbol):
                continue

            # Get token price from DexScreener (more reliable)
            token_price = await _get_price_from_dexscreener(session, token_address)

            if not token_price or token_price <= 0:
                logger.debug(f"No valid price found for {symbol}")
                continue

            # Validate price range (avoid extreme values)
            if token_price > 1000000 or token_price < 0.000001:
                logger.debug(f"Price out of range for {symbol}: ${token_price}")
                continue

            # Get liquidity quote (test with $50 USDC)
            quote_data = await _get_quote(
                session, USDC_ADDRESS, token_address, 50000000
            )  # 50 USDC (6 decimals)

            if quote_data:
                liquidity_score = _calculate_liquidity_score(quote_data)

                # Skip tokens with very low liquidity
                if liquidity_score < 10:
                    continue

                # Create mock price data for activity score calculation
                mock_price_data = {"price": str(token_price)}
                activity_score = _calculate_activity_score(
                    token, mock_price_data, liquidity_score
                )

                if activity_score > 20:  # Minimum threshold
                    candidate_pairs.append(
                        {
                            "cex_symbol": symbol,
                            "dex_pair_address": token_address,
                            "dex_data": {
                                "price": token_price,
                                "liquidity": liquidity_score
                                * 1000,  # Estimate liquidity in USD
                                "volume_h24": 0,  # Jupiter doesn't provide volume directly
                                "token_name": token.get("name", symbol),
                                "verified": "verified" in token.get("tags", []),
                            },
                            "score": activity_score,
                        }
                    )
                    processed_count += 1

            # Rate limiting - small delay between requests
            await asyncio.sleep(0.5)

    except aiohttp.ClientError as e:
        logger.error(f"Network error in jupiter_scanner: {type(e).__name__}")
        return []
    except asyncio.TimeoutError:
        logger.error("Timeout error in jupiter_scanner")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in jupiter_scanner: {e}")
        return []

    logger.info(f"Jupiter scanner found {len(candidate_pairs)} potential candidates")
    return candidate_pairs
