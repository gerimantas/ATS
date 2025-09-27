import asyncio
import aiohttp
import time
from typing import Optional, Dict, Any
from config.logging_config import get_logger

logger = get_logger("data_fetcher")

# Circuit breaker state
circuit_breaker_state = {
    'dex_api': {'failures': 0, 'last_failure': 0, 'open': False},
    'cex_api': {'failures': 0, 'last_failure': 0, 'open': False},
    'mexc_api': {'failures': 0, 'last_failure': 0, 'open': False}
}

CIRCUIT_BREAKER_THRESHOLD = 5  # Open circuit after 5 failures
CIRCUIT_BREAKER_TIMEOUT = 60  # Reset after 60 seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

async def _check_circuit_breaker(api_name: str) -> bool:
    """Check if circuit breaker is open for this API."""
    state = circuit_breaker_state[api_name]
    if state['open']:
        if time.time() - state['last_failure'] > CIRCUIT_BREAKER_TIMEOUT:
            # Reset circuit breaker
            state['open'] = False
            state['failures'] = 0
            logger.info(f"Circuit breaker reset for {api_name}")
            return False
        else:
            logger.warning(f"Circuit breaker open for {api_name}, skipping request")
            return True
    return False

def _record_failure(api_name: str):
    """Record a failure for circuit breaker."""
    state = circuit_breaker_state[api_name]
    state['failures'] += 1
    state['last_failure'] = time.time()
    if state['failures'] >= CIRCUIT_BREAKER_THRESHOLD:
        state['open'] = True
        logger.error(f"Circuit breaker opened for {api_name} after {state['failures']} failures")

def _record_success(api_name: str):
    """Record a success to reset failure count."""
    state = circuit_breaker_state[api_name]
    state['failures'] = 0

async def _retry_request(session, url: str, timeout: int = 10, max_retries: int = MAX_RETRIES) -> Optional[Dict]:
    """Retry HTTP request with exponential backoff."""
    for attempt in range(max_retries):
        try:
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt < max_retries - 1:
                delay = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Request failed after {max_retries} attempts: {e}")
                raise e
    return None

# This function fetches DEX data for a specific pair address
async def get_dex_data(session, pair_address_or_data) -> Optional[Dict[str, Any]]:
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

    # Check circuit breaker
    if await _check_circuit_breaker('dex_api'):
        return None

    # Otherwise, try to fetch from API (fallback for compatibility)
    try:
        # Use Dexscreener API to get pair-specific data
        url = f"https://api.dexscreener.com/latest/dex/pairs/solana/{pair_address_or_data}"
        json_response = await _retry_request(session, url, timeout=10)

        if not json_response:
            raise aiohttp.ClientError("No response from API")

        latency_ms = (time.monotonic() - start_time) * 1000
        pair_data = json_response.get('pair', {})

        if not pair_data:
            raise ValueError(f"No pair data found for {pair_address_or_data}")

        price = float(pair_data.get('priceUsd', 0))
        if price <= 0:
            raise ValueError(f"Invalid price data: {price}")

        liquidity = float(pair_data.get('liquidity', {}).get('usd', 0))
        volume_h24 = float(pair_data.get('volume', {}).get('h24', 0))

        result = {
            'price': price,
            'liquidity': liquidity,
            'volume_h24': volume_h24,
            'latency_ms': latency_ms
        }

        _record_success('dex_api')
        logger.debug(f"Successfully fetched DEX data for {pair_address_or_data}: price={price}, latency={latency_ms:.2f}ms")
        return result

    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
        _record_failure('dex_api')
        logger.error(f"Error fetching DEX data: {pair_address_or_data} - {e}")
        return None

# This function fetches CEX data for a specific symbol
async def get_cex_data(session, symbol) -> Optional[Dict[str, Any]]:
    start_time = time.monotonic()

    # Check circuit breaker
    if await _check_circuit_breaker('cex_api'):
        return None

    try:
        # Use Binance API for ticker data - try both SYMBOLUSDT and SYMBOLUSD
        symbols_to_try = [f"{symbol}USDT", f"{symbol}USD"]

        for symbol_pair in symbols_to_try:
            try:
                url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol_pair}"
                json_response = await _retry_request(session, url, timeout=5)

                if json_response:
                    latency_ms = (time.monotonic() - start_time) * 1000
                    price = float(json_response.get('lastPrice', 0))
                    volume_h24 = float(json_response.get('quoteVolume', 0))  # USD volume

                    if price <= 0:
                        continue  # Try next symbol

                    result = {
                        'price': price,
                        'volume_h24': volume_h24,
                        'latency_ms': latency_ms,
                        'symbol_used': symbol_pair
                    }

                    _record_success('cex_api')
                    logger.debug(f"Successfully fetched CEX data for {symbol} using {symbol_pair}: price={price}, latency={latency_ms:.2f}ms")
                    return result

            except (aiohttp.ClientError, asyncio.TimeoutError):
                continue  # Try next symbol

        # If we get here, none of the symbols worked
        logger.error(f"Error fetching CEX data: {symbol} (tried {symbols_to_try})")
        _record_failure('cex_api')
        return None

    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        _record_failure('cex_api')
        logger.error(f"Error fetching CEX data: {symbol} - {e}")
        return None

# This function fetches historical Kline (candlestick) data from MEXC
async def get_cex_historical_klines(session, cex_symbol: str, interval: str = '1m', limit: int = 30) -> Optional[list]:
    """Fetches historical Kline (candlestick) data from MEXC."""
    # Check circuit breaker
    if await _check_circuit_breaker('mexc_api'):
        return None

    symbol_formatted = f"{cex_symbol.upper()}USDT"
    # This endpoint provides [open_time, open, high, low, close, volume, close_time, ...]
    url = f"https://api.mexc.com/api/v3/klines?symbol={symbol_formatted}&interval={interval}&limit={limit}"

    try:
        klines_data = await _retry_request(session, url, timeout=10)

        if not klines_data:
            raise aiohttp.ClientError("No response from MEXC API")

        # Validate that we got proper kline data
        if not isinstance(klines_data, list) or len(klines_data) == 0:
            raise ValueError(f"Invalid kline data format for {cex_symbol}")

        # Validate first kline has expected structure
        if len(klines_data[0]) < 6:
            raise ValueError(f"Incomplete kline data for {cex_symbol}")

        _record_success('mexc_api')
        logger.debug(f"Successfully fetched {len(klines_data)} klines for {cex_symbol}")
        return klines_data

    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
        _record_failure('mexc_api')
        logger.error(f"Error fetching historical klines for {cex_symbol}: {e}")
        return None