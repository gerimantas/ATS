import asyncio
import aiohttp
import time
import importlib
from config import (
    POLLING_INTERVAL_SECONDS,
    SCANNER_INTERVAL_SECONDS,
    ENABLED_CEX_VERIFIERS,
)
from src.data.data_fetcher import get_dex_data, get_cex_data
import signal_generator
import risk_manager
import database_manager
import scanner
import post_signal_analyzer

# --- Global State for Watchlist ---
watchlist = []

# --- Dynamic Loading for CEX Verifiers ---
cex_verifier_modules = []
for verifier_name in ENABLED_CEX_VERIFIERS:
    try:
        module = importlib.import_module(f"cex_verifiers.{verifier_name}")
        if hasattr(module, "verify"):
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
    cex_symbol = pair_info["cex_symbol"]
    dex_pair_address = pair_info["dex_pair_address"]

    # --- Step 1: Concurrently fetch all required data ---
    data_tasks = [
        get_dex_data(session, pair_info),  # Pass full pair_info which includes dex_data
        get_cex_data(session, cex_symbol),
    ]
    # Add tasks for all CEX verifiers
    for verifier in cex_verifier_modules:
        data_tasks.append(verifier.verify(session, cex_symbol))

    results = await asyncio.gather(*data_tasks, return_exceptions=True)

    dex_data = results[0]
    primary_cex_data = results[1]
    verifier_results = results[2:]

    # --- Step 2: Basic Data Validation ---
    if isinstance(dex_data, Exception) or not dex_data:
        return
    if isinstance(primary_cex_data, Exception) or not primary_cex_data:
        return

    # --- Step 3: CEX Data Cross-Verification ---
    is_data_consistent = True
    PRICE_DEVIATION_THRESHOLD = 0.02  # 2% deviation threshold

    for v_result in verifier_results:
        if isinstance(v_result, Exception) or not v_result.get("price"):
            continue  # Verifier failed, but we can proceed with caution

        deviation = (
            abs(primary_cex_data["price"] - v_result["price"])
            / primary_cex_data["price"]
        )
        if deviation > PRICE_DEVIATION_THRESHOLD:
            print(
                f"DATA GLITCH DETECTED for {cex_symbol}: Primary CEX price ({primary_cex_data['price']}) deviates from {v_result['source']} price ({v_result['price']}) by {deviation:.2%}. Skipping signal."
            )
            is_data_consistent = False
            break  # One bad verifier is enough to distrust the data

    if not is_data_consistent:
        return

    # --- Step 4: Proceed with existing logic if data is consistent ---
    print(f"Analyzing {cex_symbol}... Data is consistent.")
    print(
        f"  DEX data: price={dex_data.get('price', 'N/A')}, volume_24h={dex_data.get('volume_h24', 'N/A')}, liquidity={dex_data.get('liquidity', 'N/A')}"
    )
    print(
        f"  CEX data: price={primary_cex_data.get('price', 'N/A')}, volume_24h={primary_cex_data.get('volume_h24', 'N/A')}"
    )
    is_safe, notes = risk_manager.perform_risk_checks(dex_data, primary_cex_data)
    print(f"  Risk check result: {is_safe} - {notes}")
    if is_safe:
        signal = signal_generator.generate_signal(dex_data, primary_cex_data)
        if signal:
            print(
                f"  Signal generated: {signal['signal_type']} at spread {signal['spread']:.2f}%"
            )
            signal_id = database_manager.create_signal(
                timestamp=signal["timestamp"],
                dex_price=signal["dex_price"],
                cex_price=signal["cex_price"],
                spread=signal["spread"],
                data_latency_ms=signal.get("latency", 0),
                pair_symbol=f"{cex_symbol}/USDT",
                cex_symbol=cex_symbol,
                signal_type=signal["signal_type"],
            )
            # Schedule reward calculation as a background task
            asyncio.create_task(
                post_signal_analyzer.calculate_and_store_reward(
                    session,
                    signal_id,
                    cex_symbol,
                    signal["cex_price"],
                    signal["signal_type"],
                    signal["timestamp"],
                )
            )
        else:
            print("  No signal generated (spread or volume too low)")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopping ATS.")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopping ATS.")
