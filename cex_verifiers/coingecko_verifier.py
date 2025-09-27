import aiohttp
import asyncio
import time

# CoinGecko API requires mapping common symbols to their unique IDs
# This list should be expanded over time.
SYMBOL_TO_CG_ID = {
    "SOL": "solana",
    "BONK": "bonk",
    "WIF": "dogwifhat",
    "JUP": "jupiter-exchange-solana",
}

# Simple rate limiting cache
_price_cache = {}
_CACHE_DURATION = 30  # Cache prices for 30 seconds


async def verify(session: aiohttp.ClientSession, cex_symbol: str):
    """
    Fetches price data for a given symbol from CoinGecko API to serve as a secondary
    verification source for CEX data.
    """
    # Check cache first
    cache_key = cex_symbol.upper()
    current_time = time.time()

    if cache_key in _price_cache:
        cached_price, cache_time = _price_cache[cache_key]
        if current_time - cache_time < _CACHE_DURATION:
            return {"source": "coingecko", "price": cached_price}

    coin_id = SYMBOL_TO_CG_ID.get(cex_symbol.upper())
    if not coin_id:
        # We don't have this coin in our map, so we can't verify it.
        return {
            "source": "coingecko",
            "price": None,
            "error": f"Symbol {cex_symbol} not found in CoinGecko map.",
        }

    url = (
        f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    )

    try:
        async with session.get(url, timeout=5) as response:
            if response.status == 429:
                # Rate limited - return cached data if available
                if cache_key in _price_cache:
                    cached_price, _ = _price_cache[cache_key]
                    print(
                        f"Rate limited by CoinGecko for {cex_symbol}, using cached price"
                    )
                    return {"source": "coingecko", "price": cached_price}
                else:
                    return {
                        "source": "coingecko",
                        "price": None,
                        "error": "Rate limited by CoinGecko",
                    }

            response.raise_for_status()
            data = await response.json()

            price = data.get(coin_id, {}).get("usd")
            if price:
                # Cache the successful result
                _price_cache[cache_key] = (float(price), current_time)
                return {"source": "coingecko", "price": float(price)}
            else:
                return {
                    "source": "coingecko",
                    "price": None,
                    "error": "Price not found in CoinGecko response.",
                }

    except aiohttp.ClientError as e:
        print(
            f"Network/API Error in coingecko_verifier for {cex_symbol}: {type(e).__name__}"
        )
        return {"source": "coingecko", "price": None, "error": str(e)}
    except Exception as e:
        # This block will now catch only data processing errors (JSON, key errors, etc.)
        print(
            f"Data Processing Error in coingecko_verifier for {cex_symbol}: {type(e).__name__} - {e}"
        )
        return {"source": "coingecko", "price": None, "error": str(e)}
