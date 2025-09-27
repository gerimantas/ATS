
## **Tasks 2.3 & 2.4: Meta-Scanner Development and CEX Cross-Verification Integration**

**Objective:** To transform the system's core logic. We will implement the meta-scanner that dynamically loads and orchestrates all DEX scanners. Then, we will overhaul the main loop to consume the dynamic watchlist and perform a critical data consistency check for CEX data using verifier plugins.

### **Part 1: Development of the Meta-Scanner (Task 2.3)**

**File to Modify:** `scanner.py`

**📝 Instructions:**
You will completely replace the contents of `scanner.py`. It will no longer be a scanner itself, but an **orchestrator** that dynamically loads, runs, and aggregates results from all enabled plugins in the `scanners/` directory.

**Code for `scanner.py`:**

```python
import asyncio
import os
import importlib
from collections import defaultdict
from config import ENABLED_DEX_SCANNERS, WATCHLIST_SIZE

# --- Dynamic Plugin Loading ---
# This code finds and imports all enabled scanner modules from the 'scanners/' directory.
scanner_modules = []
for scanner_name in ENABLED_DEX_SCANNERS:
    try:
        module_path = f"scanners.{scanner_name}"
        module = importlib.import_module(module_path)
        if hasattr(module, 'scan'):
            scanner_modules.append(module)
            print(f"Successfully loaded DEX scanner: {scanner_name}")
        else:
            print(f"ERROR: {scanner_name} module does not have a 'scan' function.")
    except ImportError:
        print(f"ERROR: Could not import scanner module: {scanner_name}")


async def update_watchlist(session):
    """
    Runs all enabled DEX scanners concurrently, aggregates their results,
    applies a confirmation bonus, and returns the final watchlist.
    """
    if not scanner_modules:
        print("No DEX scanners enabled or loaded. Watchlist update skipped.")
        return []

    print(f"--- Running {len(scanner_modules)} DEX scanners concurrently ---")
    
    tasks = [module.scan(session) for module in scanner_modules]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # --- Result Aggregation & Scoring ---
    aggregated_scores = defaultdict(float)
    pair_confirmations = defaultdict(int)
    pair_data_map = {}

    for result in results:
        if isinstance(result, Exception) or not result:
            continue
        
        for pair in result:
            symbol = pair['cex_symbol']
            aggregated_scores[symbol] += pair.get('score', 0)
            pair_confirmations[symbol] += 1
            pair_data_map[symbol] = pair # Store the full data for the pair

    # --- Final Score Calculation with Confirmation Bonus ---
    final_candidates = []
    for symbol, total_score in aggregated_scores.items():
        confirmations = pair_confirmations[symbol]
        
        # Apply a significant bonus if a pair is found by more than one scanner
        confirmation_bonus = (confirmations - 1) * 150 # e.g., +150 score for each extra confirmation
        
        final_score = total_score + confirmation_bonus
        
        candidate = pair_data_map[symbol]
        candidate['final_score'] = final_score
        candidate['confirmations'] = confirmations
        final_candidates.append(candidate)
        
    # Sort by the final aggregated score to get the top candidates
    sorted_candidates = sorted(final_candidates, key=lambda x: x['final_score'], reverse=True)
    
    watchlist = sorted_candidates[:WATCHLIST_SIZE]
    
    print(f"Watchlist updated. Top {len(watchlist)} pairs:")
    for item in watchlist:
        print(f"  - {item['cex_symbol']} (Score: {item['final_score']:.2f}, Confirmations: {item['confirmations']})")
    
    return watchlist

```

### **Part 2: CEX Cross-Verification and Main Loop Integration (Task 2.4)**

**File to Modify:** `main.py`

**📝 Instructions:**
You will now overhaul `main.py` to use the new meta-scanner and to implement the CEX data verification logic. The main loop will fetch data from the primary CEX API and all verifier plugins, compare the results, and only proceed if the data is consistent.

**Code for `main.py`:**

```python
import asyncio
import aiohttp
import time
import importlib
from config import POLLING_INTERVAL_SECONDS, SCANNER_INTERVAL_SECONDS, ENABLED_CEX_VERIFIERS
import data_fetcher
import signal_generator
import risk_manager
import database_manager
import scanner

# --- Global State for Watchlist ---
watchlist = []

# --- Dynamic Loading for CEX Verifiers ---
cex_verifier_modules = []
for verifier_name in ENABLED_CEX_VERIFIERS:
    try:
        module = importlib.import_module(f"cex_verifiers.{verifier_name}")
        if hasattr(module, 'verify'):
            cex_verifier_modules.append(module)
            print(f"Successfully loaded CEX verifier: {verifier_name}")
    except ImportError:
        print(f"ERROR: Could not import CEX verifier: {verifier_name}")


async def scanner_task(session):
    """Background task that periodically updates the watchlist."""
    global watchlist
    while True:
        watchlist = await scanner.update_watchlist(session)
        await asyncio.sleep(SCANNER_INTERVAL_SECONDS)


async def main():
    database_manager.setup_database()
    
    async with aiohttp.ClientSession() as session:
        # Start the scanner as a background task
        scanner_handle = asyncio.create_task(scanner_task(session))
        
        print("ATS Started. Waiting for the first watchlist update...")
        while not watchlist:
            await asyncio.sleep(1)

        # Main analysis loop
        while True:
            start_cycle_time = time.monotonic()
            
            if not watchlist:
                print("Watchlist is empty, waiting for scanner.")
                await asyncio.sleep(POLLING_INTERVAL_SECONDS)
                continue

            # --- Create concurrent tasks for all pairs in the watchlist ---
            analysis_tasks = []
            for pair_info in watchlist:
                analysis_tasks.append(analyze_pair(session, pair_info))
            
            await asyncio.gather(*analysis_tasks)

            cycle_duration = time.monotonic() - start_cycle_time
            print(f"--- Cycle finished in {cycle_duration:.2f} seconds ---")
            await asyncio.sleep(max(0, POLLING_INTERVAL_SECONDS - cycle_duration))


async def analyze_pair(session, pair_info):
    """Fetches all data for a single pair, performs checks, and generates signals."""
    cex_symbol = pair_info['cex_symbol']
    dex_pair_address = pair_info['dex_pair_address']
    
    # --- Step 1: Concurrently fetch all required data ---
    data_tasks = [
        data_fetcher.get_dex_data(session, dex_pair_address),
        data_fetcher.get_cex_data(session, cex_symbol)
    ]
    # Add tasks for all CEX verifiers
    for verifier in cex_verifier_modules:
        data_tasks.append(verifier.verify(session, cex_symbol))

    results = await asyncio.gather(*data_tasks, return_exceptions=True)

    dex_data = results[0]
    primary_cex_data = results[1]
    verifier_results = results[2:]

    # --- Step 2: Basic Data Validation ---
    if isinstance(dex_data, Exception) or not dex_data: return
    if isinstance(primary_cex_data, Exception) or not primary_cex_data: return
    
    # --- Step 3: CEX Data Cross-Verification ---
    is_data_consistent = True
    PRICE_DEVIATION_THRESHOLD = 0.02 # 2% deviation threshold
    
    for v_result in verifier_results:
        if isinstance(v_result, Exception) or not v_result.get('price'):
            continue # Verifier failed, but we can proceed with caution
        
        deviation = abs(primary_cex_data['price'] - v_result['price']) / primary_cex_data['price']
        if deviation > PRICE_DEVIATION_THRESHOLD:
            print(f"DATA GLITCH DETECTED for {cex_symbol}: Primary CEX price ({primary_cex_data['price']}) deviates from {v_result['source']} price ({v_result['price']}) by {deviation:.2%}. Skipping signal.")
            is_data_consistent = False
            break # One bad verifier is enough to distrust the data
    
    if not is_data_consistent:
        return

    # --- Step 4: Proceed with existing logic if data is consistent ---
    print(f"Analyzing {cex_symbol}... Data is consistent.")
    is_safe, notes = risk_manager.perform_risk_checks(dex_data, primary_cex_data)
    if is_safe:
        signal = signal_generator.generate_signal(dex_data, primary_cex_data)
        if signal:
            database_manager.create_signal(
                timestamp=signal['timestamp'],
                dex_price=signal['dex_price'],
                cex_price=signal['cex_price'],
                spread=signal['spread'],
                data_latency_ms=signal.get('latency', 0)
            )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopping ATS.")
```

### **✅ Testing and Committing**

The goal is to verify that the dynamic loading works and that the main loop correctly uses the new orchestrated logic.

1.  **Run the main application** from your terminal: `python main.py`.

2.  **Verify the Initial Output:**

      * You should see messages like:
          * `Successfully loaded DEX scanner: dexscreener_scanner`
          * `Successfully loaded CEX verifier: coingecko_verifier`
      * Then, you should see the `scanner.py` output: `Watchlist updated...` with a list of pairs.

3.  **Verify the Main Loop:**

      * The main loop should start printing `Analyzing [SYMBOL]... Data is consistent.` for the pairs from the watchlist.

4.  **Test the Glitch Detection (Optional but Recommended):**

      * Open `cex_verifiers/coingecko_verifier.py`.
      * Temporarily change the return line to `return {'source': 'coingecko', 'price': 0.01}` to simulate a glitch.
      * Restart `main.py`. Now, when the system analyzes a pair, you should see the `DATA GLITCH DETECTED` message, and the signal for that pair should be skipped.
      * **Remember to revert this change after testing.**

5.  If the tests pass and the logic flows as expected, **commit and push your changes.**

    ```bash
    git add .
    git commit -m "feat: Implement meta-scanner orchestrator and CEX cross-verification"
    git push
    ```