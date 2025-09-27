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