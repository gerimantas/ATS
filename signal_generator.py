from config import MIN_DEX_VOLUME_24H, SPREAD_THRESHOLD_FILTER
from datetime import datetime


def generate_signal(dex_data, cex_data):
    """Primary trigger is DEX volume, secondary is spread."""
    print(
        f"    Signal gen check: DEX volume {dex_data.get('volume_h24', 0)} >= {MIN_DEX_VOLUME_24H}? {dex_data.get('volume_h24', 0) >= MIN_DEX_VOLUME_24H}"
    )

    if dex_data["volume_h24"] < MIN_DEX_VOLUME_24H:
        return None  # Market not active enough

    spread = ((cex_data["price"] - dex_data["price"]) / dex_data["price"]) * 100
    print(
        f"    Signal gen check: spread {abs(spread):.2f}% >= {SPREAD_THRESHOLD_FILTER}? {abs(spread) >= SPREAD_THRESHOLD_FILTER}"
    )

    if abs(spread) < SPREAD_THRESHOLD_FILTER:
        return None  # Opportunity not significant enough

    return {
        "timestamp": datetime.now(),
        "dex_price": dex_data["price"],
        "cex_price": cex_data["price"],
        "spread": spread,
        "signal_type": "BUY" if spread > 0 else "SELL",
        # Pass latency through for logging
        "latency": dex_data.get("latency_ms", 0) + cex_data.get("latency_ms", 0),
    }
