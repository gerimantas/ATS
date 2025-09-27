import asyncio
from src.data import data_fetcher
import database_manager
from config import REWARD_CALCULATION_DELAY_SECONDS, REWARD_TIME_WINDOW_MINUTES

async def calculate_and_store_reward(session, signal_id: int, cex_symbol: str, entry_price: float, signal_type: str):
    """
    Waits for a period, fetches historical price data, calculates the reward score,
    and updates the database.
    """
    print(f"Analyzer scheduled for signal {signal_id}. Waiting for {REWARD_CALCULATION_DELAY_SECONDS} seconds...")
    await asyncio.sleep(REWARD_CALCULATION_DELAY_SECONDS)

    print(f"Analyzer started for signal {signal_id}. Fetching historical data...")
    klines = await data_fetcher.get_cex_historical_klines(
        session, cex_symbol, limit=REWARD_TIME_WINDOW_MINUTES
    )

    if not klines:
        print(f"Could not calculate reward for signal {signal_id}: No historical data.")
        return

    # --- Reward Calculation Logic ---
    # Kline format: [open_time, open, high, low, close, ...]
    high_prices = [float(k[2]) for k in klines]
    low_prices = [float(k[3]) for k in klines]

    if signal_type == 'BUY':
        # For a BUY signal, the reward is based on the highest price reached
        max_favorable_price = max(high_prices)
        reward = (max_favorable_price - entry_price) / entry_price
    else:  # SELL
        # For a SELL signal, the reward is based on the lowest price reached
        min_favorable_price = min(low_prices)
        reward = (entry_price - min_favorable_price) / entry_price

    database_manager.update_signal_reward(signal_id, reward)