"""
DEX Order Flow Imbalance Algorithm
Implements real-time order flow imbalance detection for DEX trading
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta
from loguru import logger
import numpy as np
from config.logging_config import get_logger

logger = get_logger("algorithms.order_flow")

class OrderFlowAnalyzer:
    """
    Analyzes order flow imbalance in DEX trades
    Detects aggressive buying vs selling pressure
    """

    def __init__(self, window_seconds: int = 30):
        """
        Initialize order flow analyzer

        Args:
            window_seconds: Analysis window in seconds
        """
        self.window_seconds = window_seconds
        self.imbalance_threshold = 0.6  # 60% imbalance threshold
        self.min_volume_threshold = 1000  # Minimum volume for signal
        self.trade_windows = {}  # symbol -> deque of trades
        self.signal_cooldowns = {}  # symbol -> last signal time
        self.cooldown_period = 60  # 60 seconds cooldown

        # Performance tracking
        self.signal_history = deque(maxlen=1000)
        self.accuracy_stats = {
            'total_signals': 0,
            'profitable_signals': 0,
            'avg_return': 0.0
        }

        logger.info(f"OrderFlowAnalyzer initialized with {window_seconds}s window")

    def add_trade(self, symbol: str, trade: Dict):
        """
        Add new trade to analysis window

        Args:
            symbol: Trading pair symbol
            trade: Trade data with keys: side, amount, price, timestamp, is_aggressive
        """
        try:
            # Initialize window if needed
            if symbol not in self.trade_windows:
                self.trade_windows[symbol] = deque(maxlen=1000)  # Keep last 1000 trades

            # Validate trade data
            required_keys = ['side', 'amount', 'price', 'timestamp']
            if not all(key in trade for key in required_keys):
                logger.warning(f"Invalid trade data for {symbol}: missing required keys")
                return

            # Add trade to window
            self.trade_windows[symbol].append(trade)

            # Clean old trades
            self._clean_old_trades(symbol)

            logger.debug(f"Added trade to {symbol}: {trade['side']} {trade['amount']} @ {trade['price']}")

        except Exception as e:
            logger.error(f"Error adding trade for {symbol}: {e}")

    def _clean_old_trades(self, symbol: str):
        """Remove trades older than analysis window"""
        if symbol not in self.trade_windows:
            return

        cutoff_time = datetime.utcnow() - timedelta(seconds=self.window_seconds)
        window = self.trade_windows[symbol]

        # Remove old trades from front of deque
        while window and isinstance(window[0]['timestamp'], datetime) and window[0]['timestamp'] < cutoff_time:
            window.popleft()

    def calculate_imbalance(self, symbol: str) -> float:
        """
        Calculate order flow imbalance ratio

        Args:
            symbol: Trading pair symbol

        Returns:
            Imbalance ratio between -1 (sell pressure) and 1 (buy pressure)
        """
        try:
            if symbol not in self.trade_windows:
                return 0.0

            window = self.trade_windows[symbol]
            if not window:
                return 0.0

            # Calculate buy and sell volumes
            buy_volume = 0.0
            sell_volume = 0.0

            for trade in window:
                amount = trade.get('amount', 0)
                side = trade.get('side', '').lower()

                # Apply time decay (more recent trades have higher weight)
                age_seconds = (datetime.utcnow() - trade['timestamp']).total_seconds()
                decay_factor = max(0.1, 1.0 - (age_seconds / self.window_seconds))

                weighted_amount = amount * decay_factor

                if side == 'buy':
                    buy_volume += weighted_amount
                elif side == 'sell':
                    sell_volume += weighted_amount

            total_volume = buy_volume + sell_volume

            if total_volume == 0:
                return 0.0

            # Calculate imbalance: positive = buy pressure, negative = sell pressure
            imbalance = (buy_volume - sell_volume) / total_volume

            # Ensure within bounds
            imbalance = max(-1.0, min(1.0, imbalance))

            logger.debug(f"{symbol} imbalance: {imbalance:.3f} (buy: {buy_volume:.2f}, sell: {sell_volume:.2f})")

            return imbalance

        except Exception as e:
            logger.error(f"Error calculating imbalance for {symbol}: {e}")
            return 0.0

    def is_signal_triggered(self, symbol: str) -> Tuple[bool, Optional[str]]:
        """
        Check if signal should be triggered based on imbalance

        Args:
            symbol: Trading pair symbol

        Returns:
            Tuple of (should_trigger, signal_type)
        """
        try:
            # Check cooldown
            if self._is_in_cooldown(symbol):
                return False, None

            imbalance = self.calculate_imbalance(symbol)

            # Check volume threshold
            total_volume = self._get_window_volume(symbol)
            if total_volume < self.min_volume_threshold:
                return False, None

            # Check imbalance threshold
            if abs(imbalance) >= self.imbalance_threshold:
                signal_type = 'BUY' if imbalance > 0 else 'SELL'

                # Record signal
                self._record_signal(symbol, signal_type, imbalance, total_volume)
                self._set_cooldown(symbol)

                logger.info(f"Signal triggered for {symbol}: {signal_type} (imbalance: {imbalance:.3f})")
                return True, signal_type

            return False, None

        except Exception as e:
            logger.error(f"Error checking signal for {symbol}: {e}")
            return False, None

    def _get_window_volume(self, symbol: str) -> float:
        """Get total volume in current analysis window"""
        if symbol not in self.trade_windows:
            return 0.0

        return sum(trade.get('amount', 0) for trade in self.trade_windows[symbol])

    def _is_in_cooldown(self, symbol: str) -> bool:
        """Check if symbol is in cooldown period"""
        if symbol not in self.signal_cooldowns:
            return False

        return datetime.utcnow() < self.signal_cooldowns[symbol]

    def _set_cooldown(self, symbol: str):
        """Set cooldown period for symbol"""
        self.signal_cooldowns[symbol] = datetime.utcnow() + timedelta(seconds=self.cooldown_period)

    def _record_signal(self, symbol: str, signal_type: str, imbalance: float, volume: float):
        """Record signal for analysis"""
        signal_record = {
            'symbol': symbol,
            'signal_type': signal_type,
            'imbalance': imbalance,
            'volume': volume,
            'timestamp': datetime.utcnow(),
            'window_seconds': self.window_seconds
        }

        self.signal_history.append(signal_record)
        self.accuracy_stats['total_signals'] += 1

    def get_signal_stats(self) -> Dict:
        """Get signal generation statistics"""
        return {
            'total_signals': self.accuracy_stats['total_signals'],
            'active_cooldowns': len(self.signal_cooldowns),
            'analyzed_symbols': len(self.trade_windows),
            'avg_imbalance_threshold': self.imbalance_threshold,
            'cooldown_period': self.cooldown_period
        }

    def get_recent_signals(self, limit: int = 10) -> List[Dict]:
        """Get recent signals"""
        return list(self.signal_history)[-limit:]

    def update_parameters(self, **kwargs):
        """
        Update analyzer parameters

        Args:
            window_seconds: New analysis window
            imbalance_threshold: New imbalance threshold
            min_volume_threshold: New volume threshold
            cooldown_period: New cooldown period
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"Updated {key} to {value}")

    def clear_data(self, symbol: Optional[str] = None):
        """
        Clear stored data

        Args:
            symbol: Specific symbol to clear, or None for all
        """
        if symbol:
            self.trade_windows.pop(symbol, None)
            self.signal_cooldowns.pop(symbol, None)
            logger.info(f"Cleared data for {symbol}")
        else:
            self.trade_windows.clear()
            self.signal_cooldowns.clear()
            logger.info("Cleared all data")

    def __repr__(self):
        stats = self.get_signal_stats()
        return f"OrderFlowAnalyzer(symbols={stats['analyzed_symbols']}, signals={stats['total_signals']}, cooldowns={stats['active_cooldowns']})"
