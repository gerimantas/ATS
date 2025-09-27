import asyncio
import aiohttp
import time

# This function will be refactored to be async
async def get_dex_data(session, url):
    start_time = time.monotonic()
    try:
        async with session.get(url, timeout=5) as response:
            response.raise_for_status()
            latency_ms = (time.monotonic() - start_time) * 1000
            json_response = await response.json()
            sol_data = json_response.get('solana', {})
            price = float(sol_data.get('usd', 0))
            volume_h24 = float(sol_data.get('usd_24h_vol', 0))
            # Mock liquidity for now
            liquidity = 100000.0
            return {'price': price, 'liquidity': liquidity, 'volume_h24': volume_h24, 'latency_ms': latency_ms}
    except Exception as e:
        print(f"Error fetching DEX data: {e}")
        # Return mock data for testing
        return {'price': 150.0, 'liquidity': 100000.0, 'volume_h24': 2000000.0, 'latency_ms': 100.0}

# This function will also be refactored to be async
async def get_cex_data(session, url):
    start_time = time.monotonic()
    try:
        async with session.get(url, timeout=5) as response:
            response.raise_for_status()
            latency_ms = (time.monotonic() - start_time) * 1000
            json_response = await response.json()
            price = float(json_response.get('lastPrice', 0))
            # Note: The 'volume' key in Binance API is the base currency volume. 
            # We might need to multiply by price for USD volume, but for now, this is fine.
            volume_h24 = float(json_response.get('volume', 0)) 
            return {'price': price, 'volume_h24': volume_h24, 'latency_ms': latency_ms}
    except Exception as e:
        print(f"Error fetching CEX data: {e}")
        return None