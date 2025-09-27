import asyncio
import aiohttp
import time
import config
from src.data.data_fetcher import get_dex_data, get_cex_data
import signal_generator
import risk_manager
import database_manager

async def main():
    # DB setup is synchronous and should be done once
    database_manager.setup_database()
    
    async with aiohttp.ClientSession() as session:
        while True:
            print("--- New Cycle ---")
            start_cycle_time = time.monotonic()

            tasks = [
                get_dex_data(session, config.DEX_URL),
                get_cex_data(session, config.CEX_URL)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            dex_data, cex_data = results[0], results[1]

            if isinstance(dex_data, Exception) or isinstance(cex_data, Exception):
                print(f"An error occurred during data fetching: DEX-{dex_data}, CEX-{cex_data}")
                await asyncio.sleep(config.POLLING_INTERVAL_SECONDS)
                continue

            if dex_data and cex_data:
                is_safe, notes = risk_manager.perform_risk_checks(dex_data, cex_data)
                if is_safe:
                    signal = signal_generator.generate_signal(dex_data, cex_data)
                    if signal:
                        database_manager.create_signal(
                            timestamp=signal['timestamp'], 
                            dex_price=signal['dex_price'], 
                            cex_price=signal['cex_price'],
                            spread=signal['spread'],
                            data_latency_ms=signal['latency'], # Logging latency
                            notes=notes # Logging risk check result
                        )
            
            cycle_duration = time.monotonic() - start_cycle_time
            await asyncio.sleep(max(0, config.POLLING_INTERVAL_SECONDS - cycle_duration))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopping ATS.")