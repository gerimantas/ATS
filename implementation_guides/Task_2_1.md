
## **Task 2.1: Architectural Refactoring for a 'Plugin' System**

**Objective:** To restructure the project to support a modular "plugin" architecture. This will allow for the dynamic loading of multiple DEX scanners and CEX data verifiers without changing the core logic.

### **Step 1: Create New Directories**

You need to create a standardized location for your new modules.

  * In the root directory of your `ATS` project, create two new folders:

    1.  `scanners/`
    2.  `cex_verifiers/`

  * Inside each of these new folders, create an empty file named `__init__.py`.

      * **Purpose:** This tells Python to treat these directories as packages, which will allow you to import modules from them later.

Your project structure should now look something like this:

```
ATS/
├── scanners/
│   └── __init__.py
├── cex_verifiers/
│   └── __init__.py
├── main.py
├── data_fetcher.py
├── config.py
└── ... (other files)
```

### **Step 2: Update the Configuration File**

Modify `config.py` to manage which scanners and verifiers are active. This allows you to enable or disable modules easily.

  * **File to Modify:** `config.py`

  * **Instructions:** Add the following lists to your configuration file. These lists will control which plugins the system attempts to load and run.

    **Code to Add (`config.py`):**

    ```python
    # ... (keep your existing settings)

    # --- NEW PLUGIN CONFIGURATION ---
    # A list of DEX scanner modules (filenames without .py) to load from the 'scanners/' directory.
    ENABLED_DEX_SCANNERS = [
        'dexscreener_scanner',
        # 'birdeye_scanner', # Example of another scanner that can be added later
    ]

    # A list of CEX verifier modules to load from the 'cex_verifiers/' directory.
    ENABLED_CEX_VERIFIERS = [
        'coingecko_verifier',
    ]
    ```

### **Step 3: Define the Standard Interface (Create Example Plugins)**

To ensure all plugins work the same way, we need to define a standard "contract" or interface. We'll do this by creating the first example of a scanner and a verifier.

1.  **Create an Example DEX Scanner:**

      * **New File:** `scanners/dexscreener_scanner.py`

      * **Content:** This module must contain an `async def scan(session)` function that returns a list of dictionaries.

        **Code for `scanners/dexscreener_scanner.py`:**

        ```python
        import aiohttp

        # This is a placeholder URL. The full implementation will come in Task 2.2
        DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex/search?q=solana%20usd"

        async def scan(session: aiohttp.ClientSession):
            """
            This is the standardized function for all DEX scanners.
            It scans for potential opportunities and returns them in a standardized format.
            """
            print("Executing dexscreener_scanner...")
            # The full logic for fetching, filtering, and scoring will be implemented in the next phase.
            # For now, we return an empty list to confirm the structure works.
            
            # Example of the standardized format it WILL return:
            # return [
            #     {
            #         'cex_symbol': 'SOL',
            #         'dex_pair_address': '4pUQS4nSjQXy3iF8b6y3o1qA1sK1e2f3g4h5j6',
            #         'score': 150.75
            #     }
            # ]
            return []
        ```

2.  **Create an Example CEX Verifier:**

      * **New File:** `cex_verifiers/coingecko_verifier.py`

      * **Content:** This module must contain a standardized function, for example, `async def verify(session, cex_symbol)`.

        **Code for `cex_verifiers/coingecko_verifier.py`:**

        ```python
        import aiohttp

        async def verify(session: aiohttp.ClientSession, cex_symbol: str):
            """
            This is the standardized function for all CEX verifiers.
            It fetches data for a specific symbol from a third-party source to verify the primary CEX API data.
            """
            print(f"Executing coingecko_verifier for {cex_symbol}...")
            # The full logic will be implemented later.
            # For now, we return a placeholder dictionary.
            return {'source': 'coingecko', 'price': None, 'volume': None}
        ```

### **✅ Testing and Committing**

The goal of this test is to ensure the new project structure is sound and the new modules can be imported correctly.

1.  **Create a temporary test file** in your root directory named `test_structure.py`.

2.  **Add the following code** to `test_structure.py`. This code attempts to import and call the example plugin functions.

    ```python
    import asyncio
    import aiohttp

    # Try to import the new modules
    try:
        from scanners import dexscreener_scanner
        from cex_verifiers import coingecko_verifier
        print("SUCCESS: Modules imported correctly.")
    except ImportError as e:
        print(f"ERROR: Failed to import modules. Check your __init__.py files. Details: {e}")

    async def run_tests():
        async with aiohttp.ClientSession() as session:
            print("\n--- Testing DEX Scanner ---")
            dex_result = await dexscreener_scanner.scan(session)
            print(f"DEX scanner returned: {dex_result}")
            if isinstance(dex_result, list):
                print("SUCCESS: DEX scanner returned the correct data type (list).")
            else:
                print("ERROR: DEX scanner returned the wrong data type.")

            print("\n--- Testing CEX Verifier ---")
            cex_result = await coingecko_verifier.verify(session, "SOL")
            print(f"CEX verifier returned: {cex_result}")
            if isinstance(cex_result, dict):
                print("SUCCESS: CEX verifier returned the correct data type (dict).")
            else:
                print("ERROR: CEX verifier returned the wrong data type.")

    if __name__ == "__main__":
        asyncio.run(run_tests())
    ```

3.  **Run the test file** from your terminal: `python test_structure.py`.

4.  **Verify the output.** You should see "SUCCESS" messages confirming that the modules were imported and that the functions returned the correct data types.

5.  If the tests pass, you can delete the `test_structure.py` file.

6.  **Commit and push your changes.** The new architecture is now in place.

    ```bash
    git add .
    git commit -m "refactor: Establish plugin architecture for scanners and verifiers"
    git push
    ```