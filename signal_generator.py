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