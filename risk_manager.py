# In risk_manager.py
from config import MIN_DEX_LIQUIDITY, MIN_CEX_VOLUME_24H


def perform_risk_checks(dex_data, cex_data):
    """Performs all risk checks and returns a boolean and notes."""
    try:
        # Check DEX liquidity
        if dex_data["liquidity"] < MIN_DEX_LIQUIDITY:
            note = f"Risk FAILED: DEX liquidity {dex_data.get('liquidity')} is below threshold {MIN_DEX_LIQUIDITY}"
            print(note)
            return False, note

        # Check CEX volume
        if cex_data["volume_h24"] < MIN_CEX_VOLUME_24H:
            note = f"Risk FAILED: CEX 24h volume {cex_data.get('volume_h24')} is below threshold {MIN_CEX_VOLUME_24H}"
            print(note)
            return False, note

        # Future: Add Market Regime filter here

        return True, "All risk checks passed."

    except (KeyError, TypeError) as e:
        # This will catch errors if 'liquidity' or 'volume_h24' keys are missing,
        # or if their values are not numbers.
        note = f"RISK CHECK ERROR: Invalid data structure provided. Error: {type(e).__name__} - {e}"
        print(note)
        return False, note
