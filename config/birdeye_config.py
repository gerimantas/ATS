"""
Birdeye API configuration for different usage modes
"""

# API Configuration
BIRDEYE_CONFIG = {
    # Test mode - very conservative for development
    "test_mode": {
        "daily_limit": 100,  # Very low limit for testing
        "requests_per_hour": 20,  # 20 requests per hour max
        "delay_between_requests": 3,  # 3 seconds between requests
        "warning_threshold": 0.7,  # Warn at 70% usage
        "critical_threshold": 0.9,  # Critical at 90% usage
        "enabled": True,
        "description": "Conservative mode for development and testing",
    },
    # Development mode - moderate usage
    "development": {
        "daily_limit": 500,  # Moderate daily limit
        "requests_per_hour": 100,  # 100 requests per hour
        "delay_between_requests": 2,  # 2 seconds between requests
        "warning_threshold": 0.8,  # Warn at 80% usage
        "critical_threshold": 0.9,  # Critical at 90% usage
        "enabled": False,
        "description": "Development mode with moderate limits",
    },
    # Production mode - full Standard tier usage
    "production": {
        "daily_limit": 1000,  # Higher daily limit (still conservative vs 30k CU)
        "requests_per_hour": 200,  # 200 requests per hour
        "delay_between_requests": 1,  # 1 second between requests
        "warning_threshold": 0.8,  # Warn at 80% usage
        "critical_threshold": 0.95,  # Critical at 95% usage
        "enabled": False,
        "description": "Production mode using more of Standard tier",
    },
}


class BirdeyeConfigManager:
    """Manager for Birdeye API configuration"""

    def __init__(self):
        self.active_mode = "test_mode"

    def get_config(self):
        """Get current Birdeye configuration"""
        return BIRDEYE_CONFIG[self.active_mode]

    def get_all_modes(self):
        """Get all available configuration modes"""
        return list(BIRDEYE_CONFIG.keys())

    def set_active_mode(self, mode: str):
        """Set active configuration mode"""
        if mode in BIRDEYE_CONFIG:
            self.active_mode = mode
            return True
        return False

    def get_active_mode(self):
        """Get current active mode"""
        return self.active_mode


# Global instance
_config_manager = BirdeyeConfigManager()


def get_birdeye_config():
    """Get current Birdeye configuration"""
    return _config_manager.get_config()


def get_all_modes():
    """Get all available configuration modes"""
    return _config_manager.get_all_modes()


def set_active_mode(mode: str):
    """Set active configuration mode"""
    return _config_manager.set_active_mode(mode)


# API endpoint costs (in Compute Units) - for reference
BIRDEYE_ENDPOINT_COSTS = {
    "/defi/networks": 1,  # Very cheap - list networks
    "/defi/price": 1,  # Single token price
    "/defi/multi_price": 2,  # Multiple token prices
    "/defi/tokenlist": 5,  # Token list (trending)
    "/defi/trades_token": 10,  # Token trades
    "/defi/trades_pair": 10,  # Pair trades
    "/defi/liquidity": 15,  # Liquidity data
    "/defi/ohlcv": 20,  # OHLCV candles
}


# Safety calculations
def calculate_daily_cu_usage(requests_per_endpoint):
    """
    Calculate estimated daily CU usage

    Args:
        requests_per_endpoint: Dict with endpoint -> daily_request_count

    Returns:
        Estimated total CU usage for the day
    """
    total_cu = 0
    for endpoint, count in requests_per_endpoint.items():
        cost_per_request = BIRDEYE_ENDPOINT_COSTS.get(endpoint, 5)  # Default 5 CU
        total_cu += cost_per_request * count

    return total_cu
