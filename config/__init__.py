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
MIN_DEX_VOLUME_24H = (
    1000  # Minimum DEX 24h volume in USD (temporarily lowered for testing)
)
SPREAD_THRESHOLD_FILTER = (
    0.05  # Minimum spread percentage for signal (temporarily lowered for testing)
)

# Risk management thresholds
MIN_DEX_LIQUIDITY = 50000  # Minimum DEX liquidity in USD
MIN_CEX_VOLUME_24H = 1000000  # Minimum CEX 24h volume in USD

# --- NEW PLUGIN CONFIGURATION ---
# A list of DEX scanner modules (filenames without .py) to load from the 'scanners/' directory.
ENABLED_DEX_SCANNERS = [
    "dexscreener_scanner",
    "jupiter_scanner",  # Jupiter DEX aggregator scanner
    "moralis_scanner",  # Moralis multi-chain scanner
    "coingecko_dex_scanner",  # CoinGecko DEX terminal scanner
    "defillama_scanner",  # DefiLlama DEX protocols scanner
    # 'birdeye_scanner',       # Example of another scanner that can be added later
]

# A list of CEX verifier modules to load from the 'cex_verifiers/' directory.
ENABLED_CEX_VERIFIERS = [
    "coingecko_verifier",
]

# --- REWARD CALCULATION CONFIGURATION ---
# How long to wait after a signal before calculating reward (in seconds)
REWARD_CALCULATION_DELAY_SECONDS = 30  # Temporarily set to 30 seconds for testing

# How many minutes of historical data to analyze for reward calculation
REWARD_TIME_WINDOW_MINUTES = 15  # And analyze the 15-minute period
