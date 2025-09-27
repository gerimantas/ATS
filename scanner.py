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

    print(f"Watchlist updated with {len(watchlist)} pairs at {asyncio.get_event_loop().time()}")
    for item in watchlist:
        print(f"  - {item['cex_symbol']} (Score: {item['final_score']:.2f}, Confirmations: {item['confirmations']})")

    return watchlist