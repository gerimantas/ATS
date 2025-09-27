
## **Task 2.2: Implementation of Individual Modules**

**Objective:** To implement the core logic for the individual DEX scanner and CEX verifier plugins. We will replace the placeholder functions from the previous task with code that fetches and processes real data.

### **Part 1: Development of the DEX Scanner**

**File to Modify:** `scanners/dexscreener_scanner.py`

**📝 Instructions:**
You will now implement the full logic for the Dexscreener scanner. This involves fetching data from their API, filtering out uninteresting pairs, and calculating an "Activity Score" to find the most promising candidates.

**Code for `scanners/dexscreener_scanner.py`:**

```python
import aiohttp
from config import SCAN_MIN_DEX_LIQUIDITY

# This is the public API endpoint for searching pairs on the Solana chain that are traded against USD-based tokens.
DEXSCREENER_SEARCH_URL = "https://api.dexscreener.com/latest/dex/search?q=solana%20usd"

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
                if liquidity < SCAN_MIN_DEX_LIQUIDITY:
                    continue

                if not pair.get('baseToken') or not pair.get('quoteToken'):
                    continue

                # We only care about pairs traded against stablecoins for easier CEX comparison
                if pair['quoteToken']['symbol'].upper() not in ['USDC', 'USDT']:
                    continue

                # --- Step 2: Activity Scoring ---
                price_change_h1 = pair.get('priceChange', {}).get('h1', 0)
                txns_h1 = pair.get('txns', {}).get('h1', {}).get('buys', 0) + pair.get('txns', {}).get('h1', {}).get('sells', 0)

                # Filter out extreme pumps/dumps which are often scams or erroneous data
                if abs(price_change_h1) > 300:
                    continue
                
                # A simple scoring model: value transactions more than price change
                score = (price_change_h1 * 0.3) + (txns_h1 * 0.7)

                if score > 0:
                    candidate_pairs.append({
                        'cex_symbol': pair['baseToken']['symbol'],
                        'dex_pair_address': pair['pairAddress'],
                        'score': score
                    })

    except Exception as e:
        print(f"ERROR in dexscreener_scanner: {e}")
        return [] # Return empty list on error

    print(f"Dexscreener scanner found {len(candidate_pairs)} potential candidates.")
    return candidate_pairs

```

### **Part 2: Development of the CEX Verifier**

**File to Modify:** `cex_verifiers/coingecko_verifier.py`

**📝 Instructions:**
Now, implement the CoinGecko verifier. Its purpose is to provide a secondary, independent data point for a CEX price, which will be used in later steps to detect data glitches from the primary exchange API.

**Code for `cex_verifiers/coingecko_verifier.py`:**

```python
import aiohttp

# CoinGecko API requires mapping common symbols to their unique IDs
# This list should be expanded over time.
SYMBOL_TO_CG_ID = {
    'SOL': 'solana',
    'BONK': 'bonk',
    'WIF': 'dogwifhat',
    'JUP': 'jupiter-exchange-solana',
}

async def verify(session: aiohttp.ClientSession, cex_symbol: str):
    """
    Fetches price data for a given symbol from CoinGecko API to serve as a secondary
    verification source for CEX data.
    """
    coin_id = SYMBOL_TO_CG_ID.get(cex_symbol.upper())
    if not coin_id:
        # We don't have this coin in our map, so we can't verify it.
        return {'source': 'coingecko', 'price': None, 'error': f'Symbol {cex_symbol} not found in CoinGecko map.'}

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    
    try:
        async with session.get(url, timeout=5) as response:
            response.raise_for_status()
            data = await response.json()
            
            price = data.get(coin_id, {}).get('usd')
            if price:
                return {'source': 'coingecko', 'price': float(price)}
            else:
                return {'source': 'coingecko', 'price': None, 'error': 'Price not found in CoinGecko response.'}

    except Exception as e:
        print(f"ERROR in coingecko_verifier for {cex_symbol}: {e}")
        return {'source': 'coingecko', 'price': None, 'error': str(e)}

```

### **✅ Testing and Committing**

The goal is to verify that both modules now fetch and process real data correctly.

1.  **Use the `test_structure.py` file** you created in the previous task. If you deleted it, create it again.

2.  **Update the code** in `test_structure.py` to the following. This will call the new, fully implemented functions.

    ```python
    import asyncio
    import aiohttp
    from scanners import dexscreener_scanner
    from cex_verifiers import coingecko_verifier

    async def run_tests():
        async with aiohttp.ClientSession() as session:
            print("\n--- Testing DEX Scanner ---")
            dex_result = await dexscreener_scanner.scan(session)
            print(f"DEX scanner returned {len(dex_result)} candidates.")
            if dex_result:
                print("First candidate:", dex_result[0])
            
            if isinstance(dex_result, list):
                print("SUCCESS: DEX scanner returned the correct data type (list).")
            else:
                print("ERROR: DEX scanner returned the wrong data type.")

            print("\n--- Testing CEX Verifier ---")
            # Test with a known symbol
            cex_symbol_to_test = "SOL"
            cex_result = await coingecko_verifier.verify(session, cex_symbol_to_test)
            print(f"CEX verifier for {cex_symbol_to_test} returned: {cex_result}")
            if isinstance(cex_result, dict) and 'price' in cex_result and cex_result['price'] is not None:
                print("SUCCESS: CEX verifier returned a valid price.")
            else:
                print("ERROR: CEX verifier failed to return a valid price.")

    if __name__ == "__main__":
        asyncio.run(run_tests())

    ```

3.  **Run the test file** from your terminal: `python test_structure.py`.

4.  **Verify the output:**

      * The DEX scanner should now print a number of candidates found and show the first one. It should no longer be an empty list.
      * The CEX verifier should print a dictionary containing the current price of SOL fetched from CoinGecko.

5.  If both tests pass, you can delete `test_structure.py`.

6.  **Commit and push your changes.**

    ```bash
    git add .
    git commit -m "feat: Implement logic for dexscreener scanner and coingecko verifier"
    git push
    ```