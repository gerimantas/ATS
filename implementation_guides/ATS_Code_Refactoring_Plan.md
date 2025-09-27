
# ATS Code Refactoring Plan

This plan is based on a fresh analysis of the code in `github.com/gerimantas/ATS` as of today. It provides a step-by-step guide for modifications and new features.

## Phase 1: Analysis and Signal Generation

### 🚀 Milestone 1: Foundational Refactoring

**Objective:** To fix the critical latency issue by migrating the existing synchronous code to an asynchronous architecture.

-----

#### 🎯 Task 1.1: Migrate to Asynchronous Operations

  * **Files:** `main.py`, `data_fetcher.py`, `requirements.txt`

  * **📝 Instructions:**

    1.  **Update `requirements.txt`:** The file already exists. Add the `aiohttp` and `streamlit` libraries needed for this and future steps.

        ```diff
        sqlalchemy
        requests
        + aiohttp
        + streamlit
        ```

        Run `pip install -r requirements.txt` to install the new packages.

    2.  **Refactor `data_fetcher.py`:** Convert the existing functions to be asynchronous.

        **Code Example (`data_fetcher.py`):**

        ```python
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
                    pair_data = json_response.get('pairs')[0]
                    price = float(pair_data.get('priceUsd'))
                    liquidity = float(pair_data.get('liquidity', {}).get('usd'))
                    volume_h24 = float(pair_data.get('volume', {}).get('h24'))
                    return {'price': price, 'liquidity': liquidity, 'volume_h24': volume_h24, 'latency_ms': latency_ms}
            except Exception as e:
                print(f"Error fetching DEX data: {e}")
                return None

        # This function will also be refactored to be async
        async def get_cex_data(session, url):
            start_time = time.monotonic()
            try:
                async with session.get(url, timeout=5) as response:
                    response.raise_for_status()
                    latency_ms = (time.monotonic() - start_time) * 1000
                    json_response = await response.json()
                    price = float(json_response.get('price'))
                    # Note: The 'volume' key in MEXC API is the base currency volume. 
                    # We might need to multiply by price for USD volume, but for now, this is fine.
                    volume_h24 = float(json_response.get('volume')) 
                    return {'price': price, 'volume_h24': volume_h24, 'latency_ms': latency_ms}
            except Exception as e:
                print(f"Error fetching CEX data: {e}")
                return None
        ```

    3.  **Refactor `main.py`:** Modify the main loop to be asynchronous, creating a single `aiohttp.ClientSession` and gathering data concurrently.

        **Code Example (`main.py`):**

        ```python
        import asyncio
        import aiohttp
        import time
        from config import DEX_URL, CEX_URL, POLLING_INTERVAL_SECONDS
        import data_fetcher
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
                        data_fetcher.get_dex_data(session, DEX_URL),
                        data_fetcher.get_cex_data(session, CEX_URL)
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    dex_data, cex_data = results[0], results[1]

                    if isinstance(dex_data, Exception) or isinstance(cex_data, Exception):
                        print(f"An error occurred during data fetching: DEX-{dex_data}, CEX-{cex_data}")
                        await asyncio.sleep(POLLING_INTERVAL_SECONDS)
                        continue

                    if dex_data and cex_data:
                        signal = signal_generator.generate_signal(dex_data, cex_data)
                        if signal:
                            if risk_manager.manage_risk(dex_data, cex_data):
                                database_manager.create_signal(
                                    timestamp=signal['timestamp'], 
                                    dex_price=signal['dex_price'], 
                                    cex_price=signal['cex_price'],
                                    spread=signal['spread']
                                )
                    
                    cycle_duration = time.monotonic() - start_cycle_time
                    await asyncio.sleep(max(0, POLLING_INTERVAL_SECONDS - cycle_duration))

        if __name__ == "__main__":
            try:
                asyncio.run(main())
            except KeyboardInterrupt:
                print("Stopping ATS.")
        ```

  * **✅ Test & Commit:**

    1.  Run `python main.py` from your terminal.
    2.  Confirm that the application runs without errors, fetching and printing data every few seconds.
    3.  If successful, commit your changes.
        ```bash
        git add requirements.txt data_fetcher.py main.py
        git commit -m "refactor: Migrate core components to asyncio for non-blocking I/O"
        ```

-----

### 🧠 Milestone 2: Strategy Logic Upgrade

**Objective:** To evolve the strategy from being purely spread-based and enhance the database for richer analysis.

-----

#### 🎯 Task 2.1: Enhance the Database Schema

  * **File:** `database_manager.py`

  * **📝 Instructions:**
    Your current `Signal` model is a good start. Let's add the new columns needed for deeper analysis. The `create_signal` function will also need to be updated.

    **Code Example (`database_manager.py`):**

    ```python
    # Find this class definition and add the new columns
    class Signal(Base):
        __tablename__ = 'signals'
        id = Column(Integer, primary_key=True)
        timestamp = Column(DateTime)
        dex_price = Column(Float)
        cex_price = Column(Float)
        spread = Column(Float)
        # --- ADD THESE NEW COLUMNS ---
        data_latency_ms = Column(Integer, nullable=True)
        market_regime = Column(String, nullable=True)
        notes = Column(Text, nullable=True)
        actual_reward = Column(Float, nullable=True)

    # Update the create_signal function signature and body
    def create_signal(timestamp, dex_price, cex_price, spread, data_latency_ms=None, notes=None):
        session = Session()
        new_signal = Signal(
            timestamp=timestamp,
            dex_price=dex_price,
            cex_price=cex_price,
            spread=spread,
            data_latency_ms=data_latency_ms,
            notes=notes
        )
        session.add(new_signal)
        session.commit()
        print(f"SUCCESS: Signal successfully logged to the database.")
        session.close()
    ```

  * **✅ Test & Commit:**

    1.  Delete the existing `ats.db` file to allow the new schema to be created cleanly.
    2.  Run `python main.py`. It will likely fail because you are not passing the new arguments yet, but it should create the new `ats.db` file.
    3.  Use an SQLite browser to verify that the `signals` table now contains the new columns (`data_latency_ms`, `market_regime`, etc.).
    4.  If the schema is correct, commit the changes.
        ```bash
        git add database_manager.py
        git commit -m "feat: Enhance database schema for advanced analysis"
        ```

-----

#### 🎯 Task 2.2: Refactor Signal Trigger and Risk Management

  * **Files:** `signal_generator.py`, `risk_manager.py`, `main.py`

  * **📝 Instructions:**
    Let's refactor the logic. The **risk check should happen first**, and the **signal should be generated based on volume**, with spread as a secondary filter.

    1.  **Modify `risk_manager.py`:** Combine the checks into one function that returns a status and notes.

        ```python
        # In risk_manager.py
        from config import MIN_DEX_LIQUIDITY, MIN_CEX_VOLUME_24H

        def perform_risk_checks(dex_data, cex_data):
            """Performs all risk checks and returns a boolean and notes."""
            if dex_data['liquidity'] < MIN_DEX_LIQUIDITY:
                return False, f"Risk FAILED: DEX liquidity {dex_data['liquidity']} < {MIN_DEX_LIQUIDITY}"
            
            if cex_data['volume_h24'] < MIN_CEX_VOLUME_24H:
                return False, f"Risk FAILED: CEX 24h volume {cex_data['volume_h24']} < {MIN_CEX_VOLUME_24H}"
            
            # Future: Add Market Regime filter here
            
            return True, "All risk checks passed."
        ```

    2.  **Modify `signal_generator.py`:** Update the logic as planned.

        ```python
        # In signal_generator.py
        from config import MIN_DEX_VOLUME_24H, SPREAD_THRESHOLD_FILTER
        from datetime import datetime

        def generate_signal(dex_data, cex_data):
            """Primary trigger is DEX volume, secondary is spread."""
            if dex_data['volume_h24'] < MIN_DEX_VOLUME_24H:
                return None # Market not active enough

            spread = ((cex_data['price'] - dex_data['price']) / dex_data['price']) * 100
            if abs(spread) < SPREAD_THRESHOLD_FILTER:
                return None # Opportunity not significant enough

            return {
                'timestamp': datetime.now(),
                'dex_price': dex_data['price'],
                'cex_price': cex_data['price'],
                'spread': spread,
                'signal_type': 'BUY' if spread > 0 else 'SELL',
                # Pass latency through for logging
                'latency': dex_data.get('latency_ms', 0) + cex_data.get('latency_ms', 0)
            }
        ```

    3.  **Update `main.py`** to use the new flow.

        ```python
        # In the main() function's while loop in main.py
        # ... after fetching data
        is_safe, notes = risk_manager.perform_risk_checks(dex_data, cex_data)
        if not is_safe:
            print(notes)
        else:
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
        ```

  * **✅ Test & Commit:**

    1.  Run `python main.py`.
    2.  Adjust thresholds in `config.py` to test different scenarios (e.g., risk check fails, spread is too low, etc.).
    3.  Verify that signals are logged to the database only when all conditions are met, and that the `notes` and `data_latency_ms` fields are populated.
    4.  If the new logic works, commit the changes.
        ```bash
        git add main.py signal_generator.py risk_manager.py
        git commit -m "refactor: Invert logic to check risk first and use volume as primary signal trigger"
        ```

-----

### 📊 Milestone 3: User Interface for Analysis

**Objective:** Create a dashboard to monitor the live system.

-----

#### 🎯 Task 3.1: Create the Analysis Dashboard

  * **New File:** `dashboard.py`

  * **📝 Instructions:**
    Create a `Streamlit` app to display data from the `ats.db` database.

    **Code Example (`dashboard.py`):**

    ```python
    import streamlit as st
    import pandas as pd
    from sqlalchemy import create_engine
    import time

    DB_URL = "sqlite:///ats.db"
    engine = create_engine(DB_URL)

    st.set_page_config(layout="wide")

    @st.cache_data(ttl=10) # Cache data for 10 seconds
    def load_data():
        try:
            query = "SELECT * FROM signals ORDER BY timestamp DESC LIMIT 100"
            df = pd.read_sql(query, engine)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            st.error(f"Error connecting to database: {e}")
            return pd.DataFrame()

    st.title("📈 ATS Signal Monitoring Dashboard")

    df = load_data()

    if not df.empty:
        st.subheader("Key Performance Indicators")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Signals Logged (Last 100)", len(df))
        avg_spread = df['spread'].mean()
        col2.metric("Average Spread", f"{avg_spread:.4f}%")
        avg_latency = df['data_latency_ms'].mean()
        col3.metric("Average Latency (ms)", f"{avg_latency:.2f}")
        
        st.subheader("Latest Generated Signals")
        st.dataframe(df)
    else:
        st.warning("No signals found in the database yet.")

    # Refresh the page automatically
    time.sleep(15)
    st.rerun()
    ```

  * **✅ Test & Commit:**

    1.  Ensure `main.py` is running and has logged some signals.
    2.  In a new terminal, run the dashboard: `streamlit run dashboard.py`.
    3.  A browser tab should open. Verify that it displays the signals, KPIs, and automatically refreshes.
    4.  If the dashboard works, commit the new file.
        ```bash
        git add dashboard.py
        git commit -m "feat: Create Streamlit dashboard for real-time monitoring"
        ```