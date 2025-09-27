# Config package initialization

# DEX API URL (CoinGecko example for testing)
DEX_URL = "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd&include_24hr_vol=true&include_24hr_change=true"

# CEX API URL (Binance example)
CEX_URL = "https://api.binance.com/api/v3/ticker/24hr?symbol=SOLUSDT"

# Polling interval in seconds
POLLING_INTERVAL_SECONDS = 5

# Scanner configuration
SCANNER_INTERVAL_SECONDS = 60  # How often to update the watchlist (60 seconds)
WATCHLIST_SIZE = 10  # Maximum number of pairs to track in watchlist

# Thresholds for signal generation
MIN_DEX_VOLUME_24H = 1000000  # Minimum DEX 24h volume in USD
SPREAD_THRESHOLD_FILTER = 0.5  # Minimum spread percentage for signal

# Risk management thresholds
MIN_DEX_LIQUIDITY = 50000  # Minimum DEX liquidity in USD
MIN_CEX_VOLUME_24H = 1000000  # Minimum CEX 24h volume in USD

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
