import asyncio
import aiohttp
import time

# This function fetches DEX data for a specific pair address
async def get_dex_data(session, pair_address_or_data):
    """
    Fetches DEX data. If pair_address_or_data is a dict, it's already fetched data.
    If it's a string, it's a pair address that needs to be fetched.
    """
    start_time = time.monotonic()

    # If it's already a dict with data, return it directly
    if isinstance(pair_address_or_data, dict) and 'dex_data' in pair_address_or_data:
        data = pair_address_or_data['dex_data'].copy()
        data['latency_ms'] = (time.monotonic() - start_time) * 1000
        return data

    # Otherwise, try to fetch from API (fallback for compatibility)
    try:
        # Use Dexscreener API to get pair-specific data
        url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{pair_address_or_data}"
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            latency_ms = (time.monotonic() - start_time) * 1000
            json_response = await response.json()

            pair_data = json_response.get('pair', {})
            if not pair_data:
                raise ValueError(f"No pair data found for {pair_address_or_data}")

            price = float(pair_data.get('priceUsd', 0))
            liquidity = float(pair_data.get('liquidity', {}).get('usd', 0))
            volume_h24 = float(pair_data.get('volume', {}).get('h24', 0))

            return {
                'price': price,
                'liquidity': liquidity,
                'volume_h24': volume_h24,
                'latency_ms': latency_ms
            }
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
        print(f"Error fetching DEX data: {pair_address_or_data} - {e}")
        return None

# This function fetches CEX data for a specific symbol
async def get_cex_data(session, symbol):
    start_time = time.monotonic()
    try:
        # Use Binance API for ticker data - try both SYMBOLUSDT and SYMBOLUSD
        symbols_to_try = [f"{symbol}USDT", f"{symbol}USD"]

        for symbol_pair in symbols_to_try:
            try:
                url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol_pair}"
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        latency_ms = (time.monotonic() - start_time) * 1000
                        json_response = await response.json()

                        price = float(json_response.get('lastPrice', 0))
                        volume_h24 = float(json_response.get('quoteVolume', 0))  # USD volume

                        return {
                            'price': price,
                            'volume_h24': volume_h24,
                            'latency_ms': latency_ms,
                            'symbol_used': symbol_pair
                        }
            except (aiohttp.ClientError, asyncio.TimeoutError):
                continue  # Try next symbol

        # If we get here, none of the symbols worked
        print(f"Error fetching CEX data: {symbol} (tried {symbols_to_try})")
        return None

    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        print(f"Error fetching CEX data: {symbol} - {e}")
        return None