
## **Phase 3.0: Signal Quality Assessment & Optimization**

**Objective:** To implement a crucial feedback loop by automatically calculating the performance of each generated signal. This transforms the ATS from a simple signal generator into a system that can learn and be optimized.

### **🎯 Task 3.1: Create the `actual_reward` Calculator**

**Instructions:**
You will create a new module responsible for post-signal analysis. This involves creating a new data fetching function for historical data and a new function in the database manager to update a signal with its calculated reward.

1.  **Add a New Function to `data_fetcher.py`:**

      * **File to Modify:** `data_fetcher.py`
      * **Logic:** Add a function to fetch recent candlestick (Kline) data from the CEX. This is needed to find out what the price did *after* the signal was generated.

    <!-- end list -->

    ```python
    # Add this new async function to data_fetcher.py
    async def get_cex_historical_klines(session, cex_symbol: str, interval: str = '1m', limit: int = 30):
        """Fetches historical Kline (candlestick) data from MEXC."""
        symbol_formatted = f"{cex_symbol.upper()}USDT"
        # This endpoint provides [open_time, open, high, low, close, volume, close_time, ...]
        url = f"https://api.mexc.com/api/v3/klines?symbol={symbol_formatted}&interval={interval}&limit={limit}"
        try:
            async with session.get(url, timeout=10) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            print(f"Error fetching historical klines for {cex_symbol}: {e}")
            return None
    ```

2.  **Add an Update Function to `database_manager.py`:**

      * **File to Modify:** `database_manager.py`
      * **Logic:** Add a function specifically for updating a signal with its reward score.

    <!-- end list -->

    ```python
    # Add this new function to database_manager.py
    def update_signal_reward(signal_id: int, reward_score: float):
        """Finds a signal by its ID and updates its actual_reward field."""
        session = Session()
        try:
            signal_to_update = session.query(Signal).filter(Signal.id == signal_id).first()
            if signal_to_update:
                signal_to_update.actual_reward = reward_score
                session.commit()
                print(f"SUCCESS: Updated reward for signal ID {signal_id} to {reward_score:.5f}")
            else:
                print(f"ERROR: Could not find signal with ID {signal_id} to update reward.")
        finally:
            session.close()

    # Also, modify the create_signal function to return the new signal's ID
    def create_signal(timestamp, dex_price, cex_price, spread, data_latency_ms=None, notes=None):
        session = Session()
        new_signal = Signal(...) # your existing code
        session.add(new_signal)
        session.commit()
        signal_id = new_signal.id # Get the ID of the new signal
        print(f"SUCCESS: Signal {signal_id} logged to the database.")
        session.close()
        return signal_id # Return the ID
    ```

3.  **Create the New Analyzer Module:**

      * **New File:** `post_signal_analyzer.py`
      * **Logic:** This module will contain the core logic for waiting, fetching historical data, calculating the reward, and storing it.

    <!-- end list -->

    ```python
    # New file: post_signal_analyzer.py
    import asyncio
    import data_fetcher
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
        else: # SELL
            # For a SELL signal, the reward is based on the lowest price reached
            min_favorable_price = min(low_prices)
            reward = (entry_price - min_favorable_price) / entry_price
        
        database_manager.update_signal_reward(signal_id, reward)
    ```

4.  **Update `config.py`:**

      * **File to Modify:** `config.py`
      * **Logic:** Add the new configuration parameters needed by the analyzer.

    <!-- end list -->

    ```python
    # Add these at the end of config.py
    REWARD_CALCULATION_DELAY_SECONDS = 60 * 16 # Wait 16 minutes before calculating
    REWARD_TIME_WINDOW_MINUTES = 15           # Analyze the 15 minutes after the signal
    ```

### **🎯 Task 3.2 & 3.3: Integration and Dashboard Enhancement**

1.  **Integrate into `main.py`:**

      * **File to Modify:** `main.py`
      * **Logic:** After a signal is created, launch the analyzer as a background task.

    <!-- end list -->

    ```python
    # Add the new import at the top of main.py
    import post_signal_analyzer

    # Inside the analyze_pair function in main.py
    # ... after the signal is generated
    if signal:
        signal_id = database_manager.create_signal(
            # ... arguments
        )
        if signal_id:
            # Launch the reward calculator as a non-blocking background task
            asyncio.create_task(
                post_signal_analyzer.calculate_and_store_reward(
                    session,
                    signal_id,
                    cex_symbol, # You need to pass the symbol to this function
                    signal['cex_price'],
                    signal['signal_type']
                )
            )
    ```

2.  **Enhance `dashboard.py`:**

      * **File to Modify:** `dashboard.py`
      * **Logic:** Update the dashboard to display the new performance metrics.

    <!-- end list -->

    ```python
    # Inside dashboard.py
    # ... inside the "if not df.empty:" block

    st.subheader("Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)

    # Filter for signals that have been analyzed
    analyzed_df = df.dropna(subset=['actual_reward'])

    col1.metric("Total Signals Logged (Last 100)", len(df))
    col2.metric("Analyzed Signals", len(analyzed_df))

    if not analyzed_df.empty:
        avg_reward = analyzed_df['actual_reward'].mean()
        win_rate = (analyzed_df['actual_reward'] > 0).mean()
        col3.metric("Average Reward", f"{avg_reward:.2%}")
        col4.metric("Win Rate", f"{win_rate:.2%}")

        st.subheader("Actual Reward Distribution")
        st.bar_chart(analyzed_df['actual_reward'])

    st.subheader("Latest Generated Signals")
    st.dataframe(df)
    ```

-----

## **Phase 4.0: System Robustness Enhancement**

**Objective:** To increase the system's reliability for long-term operation.

### **🎯 Task 4.1: Advanced Error Handling**

  * **File(s) to Modify:** `data_fetcher.py` and all files in `scanners/` and `cex_verifiers/`.

  * **Logic:** Replace broad `except Exception:` blocks with specific ones to make logs more informative.

    **Example Refactor (for any fetching function):**

    ```python
    # Instead of this:
    # except Exception as e:
    #     print(f"Error fetching data: {e}")

    # Use this more specific structure:
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        print(f"Network/API Error fetching data: {type(e).__name__} - {e}")
        return None
    except Exception as e:
        # This will now catch other errors like JSON parsing, key errors, etc.
        print(f"Data Processing Error: {type(e).__name__} - {e}")
        return None
    ```

### **🎯 Task 4.2: Database Performance Optimization**

  * **File to Modify:** `database_manager.py`

  * **Logic:** Add database indexes to columns that are frequently used for sorting or filtering to speed up queries.

    ```python
    # In the Signal class in database_manager.py
    class Signal(Base):
        __tablename__ = 'signals'
        id = Column(Integer, primary_key=True)
        # Add index=True to the timestamp column because we always sort by it
        timestamp = Column(DateTime, index=True)
        # It's also useful to add a symbol column to filter by
        cex_symbol = Column(String, index=True)
        # ... rest of your columns
    ```

      * **Note:** You will need to update the `create_signal` function and the call in `main.py` to also save the `cex_symbol`. After making this schema change, you must delete your old `ats.db` file for the new, indexed database to be created.

-----

### **✅ Testing and Committing**

1.  **Test Phase 3:**

      * Run `main.py`. Let the system generate a signal. Note its ID from the console log.
      * Wait for the duration of `REWARD_CALCULATION_DELAY_SECONDS`.
      * Check the console for the `SUCCESS: Updated reward for signal ID...` message.
      * Launch the dashboard with `streamlit run dashboard.py`.
      * Verify that the signal's `actual_reward` column is now filled. Check if the new KPIs (Average Reward, Win Rate) and the bar chart are displayed correctly.

2.  **Test Phase 4:**

      * After adding `index=True` and the `cex_symbol` column, delete the old `ats.db` and restart `main.py`. Use an SQLite browser to confirm the new database schema is correct.
      * To test error handling, temporarily put a typo in an API URL in `data_fetcher.py`. Run `main.py` and confirm that the console now logs a more specific `Network/API Error` instead of a generic one. Revert the typo after the test.

3.  **Commit and push your changes.**

    ```bash
    git add .
    git commit -m "feat: Implement signal quality assessment and robustness enhancements"
    git push
    ```