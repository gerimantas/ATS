import aiohttp
import asyncio
from config import MIN_DEX_LIQUIDITY

# This is the public API endpoint for searching pairs on the Solana chain that are traded against USD-based tokens.
DEXSCREENER_SEARCH_URL = "https://api.dexscreener.com/latest/dex/search?q=solana%20usd"

async def _check_cex_symbol_exists(session, symbol):
    """Quick check if a symbol exists on Binance"""
    try:
        symbols_to_try = [f"{symbol}USDT", f"{symbol}USD"]
        for symbol_pair in symbols_to_try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol_pair}"
            async with session.get(url, timeout=2) as response:
                if response.status == 200:
                    return True
        return False
    except:
        return False

async def scan(session: aiohttp.ClientSession):
    """
    Scans Dexscreener for promising pairs on the Solana network, filters them,
    and calculates an activity score. Returns a list of candidate pairs.
    """
    print("Executing dexscreener_scanner...")
    candidate_pairs = []

    try:
        async with session.get(DEXSCREENER_SEARCH_URL, timeout=10) as response:
            response.raise_for_status()
            data = await response.json()

            if not data or not data.get('pairs'):
                print("Dexscreener returned no pairs.")
                return []

            for pair in data['pairs']:
                # --- Step 1: Basic Data Filtering ---
                liquidity = pair.get('liquidity', {}).get('usd', 0)
                if liquidity < MIN_DEX_LIQUIDITY:
                    continue

                if not pair.get('baseToken') or not pair.get('quoteToken'):
                    continue

                # We only care about pairs traded against stablecoins for easier CEX comparison
                if pair['quoteToken']['symbol'].upper() not in ['USDC', 'USDT']:
                    continue

                symbol = pair['baseToken']['symbol']

                # --- Step 2: Check if symbol exists on CEX ---
                if not await _check_cex_symbol_exists(session, symbol):
                    continue  # Skip pairs that don't exist on CEX

                # --- Step 3: Activity Scoring ---
                price_change_h1 = pair.get('priceChange', {}).get('h1', 0)
                txns_h1 = pair.get('txns', {}).get('h1', {}).get('buys', 0) + pair.get('txns', {}).get('h1', {}).get('sells', 0)

                # Filter out extreme pumps/dumps which are often scams or erroneous data
                if abs(price_change_h1) > 300:
                    continue

                # A simple scoring model: value transactions more than price change
                score = (price_change_h1 * 0.3) + (txns_h1 * 0.7)

                if score > 0:
                    candidate_pairs.append({
                        'cex_symbol': symbol,
                        'dex_pair_address': pair['pairAddress'],
                        'dex_data': {
                            'price': float(pair.get('priceUsd', 0)),
                            'liquidity': float(pair.get('liquidity', {}).get('usd', 0)),
                            'volume_h24': float(pair.get('volume', {}).get('h24', 0)),
                        },
                        'score': score
                    })

    except aiohttp.ClientError as e:
        print(f"ERROR in dexscreener_scanner: Network error - {e}")
        return [] # Return empty list on error
    except asyncio.TimeoutError as e:
        print(f"ERROR in dexscreener_scanner: Timeout error - {e}")
        return [] # Return empty list on error
    except Exception as e:
        print(f"ERROR in dexscreener_scanner: Unexpected error - {e}")
        return [] # Return empty list on error

    print(f"Dexscreener scanner found {len(candidate_pairs)} potential candidates.")
    return candidate_pairs