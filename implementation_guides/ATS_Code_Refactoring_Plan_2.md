

# **Overall ATS Project Development Plan (Revised Version)**

### **1.0 Phase: Technological Foundation & MVP (Status: Completed)**
* **1.1** The system operates asynchronously (`asyncio`, `aiohttp`).
* **1.2** Base risk and signal generation modules are implemented.
* **1.3** Data is collected in a structured database.
* **1.4** A real-time monitoring user interface (`Streamlit`) is functional.

***

### **2.0 Phase: Dynamic Multi-Source Market Scanning & Data Verification**
**Objective:** To evolve the system into a modular "plugin" architecture, allowing it to dynamically use multiple independent data sources for both DEX opportunity discovery and CEX data reliability verification.

* **2.1 Architectural Refactoring for a 'Plugin' System**
    * **2.1.1** Create a `scanners/` directory for individual DEX scanner modules.
    * **2.1.2** Create a `cex_verifiers/` directory for CEX data verifier modules.
    * **2.1.3** Define standardized interfaces (function names and returned data structures) that all scanners and verifiers must adhere to.
    * **2.1.4** Update `config.py` to include configurable lists: `ENABLED_DEX_SCANNERS` and `ENABLED_CEX_VERIFIERS`.

* **2.2 Implementation of Individual Modules**
    * **2.2.1 Development of DEX Scanners (for Opportunity Discovery)**
        * *Comment:* Implement `scanners/dexscreener_scanner.py` and `scanners/birdeye_scanner.py`. Both modules will search for promising pairs based on activity metrics and return a standardized result.
    * **2.2.2 Development of CEX Verifiers (for Data Reliability)**
        * *Comment:* Implement `cex_verifiers/coingecko_verifier.py`. This module will fetch data for a specific pair on a CEX from the CoinGecko API. The primary CEX data source will remain the direct exchange API via `data_fetcher.py`.

* **2.3 Development of the Meta-Scanner (Orchestrator)**
    * **2.3.1** Modify the main `scanner.py` to dynamically load and run all enabled DEX scanners from the `scanners/` directory.
    * **2.3.2** Implement the logic to aggregate the results from all DEX scanners and apply a "confirmation bonus" to pairs found by multiple sources, thus forming the final `Watchlist`.

* **2.4 Integration of CEX Data Cross-Verification**
    * **2.4.1** Modify the main analysis loop in `main.py`. For each pair in the `Watchlist`, it will concurrently fetch data from:
        * The primary CEX API (via `data_fetcher.py`).
        * All enabled CEX verifiers (from `cex_verifiers/`).
    * **2.4.2** Implement a "data consistency check".
        * *Comment:* Before generating a signal, compare the price and volume data received from the different sources. In case of a significant discrepancy, discard the signal and log it as a potential data glitch.

***

### **3.0 Phase: Signal Quality Assessment & Optimization**
**Objective:** To implement an automated mechanism that evaluates the profitability of each generated signal, allowing for data-driven strategy optimization.

* **3.1 Creation of the `actual_reward` Calculator**
* **3.2 Integration into the Main Loop as a Background Task**
* **3.3 Dashboard Enhancement for Profitability Analysis**

***

### **4.0 Phase: System Robustness Enhancement**
**Objective:** To increase system reliability and prepare it for long-term, autonomous operation.

* **4.1 Implementation of Advanced Error Handling**
* **4.2 Database Performance Optimization (Indexing)**