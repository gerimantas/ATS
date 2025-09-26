"""
DEX Liquidity Event Detection Algorithm
Implements liquidity event detection based on rate and acceleration of liquidity changes
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger
from config.logging_config import get_logger

logger = get_logger("algorithms.liquidity")

class LiquidityAnalyzer:
    """
    Analyzes liquidity events in DEX pools
    Detects significant liquidity additions/removals and their acceleration
    """

    def __init__(self, window_seconds: int = 60):
        """
        Initialize liquidity analyzer

        Args:
            window_seconds: Analysis window in seconds
        """
        self.window_seconds = window_seconds
        self.change_rate_threshold = 0.1  # 10% change rate
        self.acceleration_threshold = 0.05  # 5% acceleration
        self.min_liquidity_threshold = 10000  # Minimum liquidity to consider
        self.liquidity_windows = {}  # symbol -> deque of liquidity data
        self.signal_cooldowns = {}  # symbol -> last signal time
        self.cooldown_period = 120  # 2 minutes cooldown

        # Performance tracking
        self.signal_history = deque(maxlen=1000)
        self.accuracy_stats = {
            'total_signals': 0,
            'profitable_signals': 0,
            'avg_return': 0.0
        }

        logger.info(f"LiquidityAnalyzer initialized with {window_seconds}s window")

    def add_liquidity_data(self, symbol: str, liquidity_data: Dict):
        """
        Add new liquidity data point

        Args:
            symbol: Trading pair symbol
            liquidity_data: Dict with keys: total_liquidity, token0_liquidity, token1_liquidity, timestamp
        """
        try:
            # Initialize window if needed
            if symbol not in self.liquidity_windows:
                self.liquidity_windows[symbol] = deque(maxlen=500)  # Keep last 500 data points

            # Validate liquidity data
            required_keys = ['total_liquidity', 'timestamp']
            if not all(key in liquidity_data for key in required_keys):
                logger.warning(f"Invalid liquidity data for {symbol}: missing required keys")
                return

            # Add data to window
            self.liquidity_windows[symbol].append(liquidity_data)

            # Clean old data
            self._clean_old_data(symbol)

            logger.debug(f"Added liquidity data to {symbol}: {liquidity_data['total_liquidity']}")

        except Exception as e:
            logger.error(f"Error adding liquidity data for {symbol}: {e}")

    def _clean_old_data(self, symbol: str):
        """Remove data older than analysis window"""
        if symbol not in self.liquidity_windows:
            return

        cutoff_time = datetime.utcnow() - timedelta(seconds=self.window_seconds)
        window = self.liquidity_windows[symbol]

        # Remove old data from front of deque
        while window and isinstance(window[0]['timestamp'], datetime) and window[0]['timestamp'] < cutoff_time:
            window.popleft()

    def calculate_liquidity_change_rate(self, symbol: str) -> float:
        """
        Calculate rate of liquidity change (first derivative)

        Args:
            symbol: Trading pair symbol

        Returns:
            Rate of change as percentage per second
        """
        try:
            if symbol not in self.liquidity_windows:
                return 0.0

            window = self.liquidity_windows[symbol]
            if len(window) < 2:
                return 0.0

            # Convert to pandas for easier analysis
            data = []
            for point in window:
                data.append({
                    'timestamp': point['timestamp'],
                    'total_liquidity': point['total_liquidity']
                })

            df = pd.DataFrame(data)
            df = df.sort_values('timestamp')

            # Calculate time differences in seconds
            df['time_diff'] = df['timestamp'].diff().dt.total_seconds()
            df['liquidity_diff'] = df['total_liquidity'].diff()
            df['liquidity_pct_change'] = df['liquidity_diff'] / df['total_liquidity'].shift(1)

            # Calculate rate of change (percentage per second)
            df['change_rate'] = df['liquidity_pct_change'] / df['time_diff']

            # Apply exponential smoothing to reduce noise
            smoothed_rates = df['change_rate'].ewm(span=5).mean()

            # Return most recent smoothed rate
            latest_rate = smoothed_rates.iloc[-1] if not smoothed_rates.empty else 0.0

            # Handle NaN values
            if pd.isna(latest_rate):
                latest_rate = 0.0

            logger.debug(f"{symbol} liquidity change rate: {latest_rate:.6f}/s")

            return float(latest_rate)

        except Exception as e:
            logger.error(f"Error calculating liquidity change rate for {symbol}: {e}")
            return 0.0

    def calculate_liquidity_acceleration(self, symbol: str) -> float:
        """
        Calculate acceleration of liquidity change (second derivative)

        Args:
            symbol: Trading pair symbol

        Returns:
            Acceleration as percentage per second squared
        """
        try:
            if symbol not in self.liquidity_windows:
                return 0.0

            window = self.liquidity_windows[symbol]
            if len(window) < 3:
                return 0.0

            # Convert to pandas for easier analysis
            data = []
            for point in window:
                data.append({
                    'timestamp': point['timestamp'],
                    'total_liquidity': point['total_liquidity']
                })

            df = pd.DataFrame(data)
            df = df.sort_values('timestamp')

            # Calculate first derivative (change rate)
            df['time_diff'] = df['timestamp'].diff().dt.total_seconds()
            df['liquidity_diff'] = df['total_liquidity'].diff()
            df['liquidity_pct_change'] = df['liquidity_diff'] / df['total_liquidity'].shift(1)
            df['change_rate'] = df['liquidity_pct_change'] / df['time_diff']

            # Calculate second derivative (acceleration)
            df['rate_diff'] = df['change_rate'].diff()
            df['acceleration'] = df['rate_diff'] / df['time_diff']

            # Apply exponential smoothing
            smoothed_acceleration = df['acceleration'].ewm(span=3).mean()

            # Return most recent smoothed acceleration
            latest_acceleration = smoothed_acceleration.iloc[-1] if not smoothed_acceleration.empty else 0.0

            # Handle NaN values
            if pd.isna(latest_acceleration):
                latest_acceleration = 0.0

            logger.debug(f"{symbol} liquidity acceleration: {latest_acceleration:.8f}/s²")

            return float(latest_acceleration)

        except Exception as e:
            logger.error(f"Error calculating liquidity acceleration for {symbol}: {e}")
            return 0.0

    def is_signal_triggered(self, symbol: str) -> Tuple[bool, Optional[str]]:
        """
        Check if liquidity event signal should be triggered

        Args:
            symbol: Trading pair symbol

        Returns:
            Tuple of (should_trigger, signal_type)
        """
        try:
            # Check cooldown
            if self._is_in_cooldown(symbol):
                return False, None

            # Check minimum liquidity threshold
            if not self._meets_liquidity_threshold(symbol):
                return False, None

            change_rate = self.calculate_liquidity_change_rate(symbol)
            acceleration = self.calculate_liquidity_acceleration(symbol)

            # Check if either rate or acceleration exceeds threshold
            rate_significant = abs(change_rate) >= self.change_rate_threshold
            acceleration_significant = abs(acceleration) >= self.acceleration_threshold

            if rate_significant or acceleration_significant:
                # Determine signal type based on direction
                if change_rate > 0 or acceleration > 0:
                    signal_type = 'LIQUIDITY_INCREASE'
                else:
                    signal_type = 'LIQUIDITY_DECREASE'

                # Record signal
                self._record_signal(symbol, signal_type, change_rate, acceleration)
                self._set_cooldown(symbol)

                logger.info(f"Liquidity signal triggered for {symbol}: {signal_type} "
                          f"(rate: {change_rate:.6f}, accel: {acceleration:.8f})")
                return True, signal_type

            return False, None

        except Exception as e:
            logger.error(f"Error checking liquidity signal for {symbol}: {e}")
            return False, None

    def _meets_liquidity_threshold(self, symbol: str) -> bool:
        """Check if current liquidity meets minimum threshold"""
        if symbol not in self.liquidity_windows:
            return False

        window = self.liquidity_windows[symbol]
        if not window:
            return False

        latest_liquidity = window[-1]['total_liquidity']
        return latest_liquidity >= self.min_liquidity_threshold

    def _is_in_cooldown(self, symbol: str) -> bool:
        """Check if symbol is in cooldown period"""
        if symbol not in self.signal_cooldowns:
            return False

        return datetime.utcnow() < self.signal_cooldowns[symbol]

    def _set_cooldown(self, symbol: str):
        """Set cooldown period for symbol"""
        self.signal_cooldowns[symbol] = datetime.utcnow() + timedelta(seconds=self.cooldown_period)

    def _record_signal(self, symbol: str, signal_type: str, change_rate: float, acceleration: float):
        """Record signal for analysis"""
        signal_record = {
            'symbol': symbol,
            'signal_type': signal_type,
            'change_rate': change_rate,
            'acceleration': acceleration,
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
            'analyzed_symbols': len(self.liquidity_windows),
            'change_rate_threshold': self.change_rate_threshold,
            'acceleration_threshold': self.acceleration_threshold,
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
            change_rate_threshold: New change rate threshold
            acceleration_threshold: New acceleration threshold
            min_liquidity_threshold: New minimum liquidity threshold
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
            self.liquidity_windows.pop(symbol, None)
            self.signal_cooldowns.pop(symbol, None)
            logger.info(f"Cleared data for {symbol}")
        else:
            self.liquidity_windows.clear()
            self.signal_cooldowns.clear()
            logger.info("Cleared all data")

    def __repr__(self):
        stats = self.get_signal_stats()
        return f"LiquidityAnalyzer(symbols={stats['analyzed_symbols']}, signals={stats['total_signals']}, cooldowns={stats['active_cooldowns']})"
