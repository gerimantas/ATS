"""
Volume-Price Correlation Algorithm
Implements volume-price correlation analysis for position formation detection
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from loguru import logger
from config.logging_config import get_logger

logger = get_logger("algorithms.volume_price")

class VolumePriceAnalyzer:
    """
    Analyzes volume-price correlation for position formation detection
    Identifies accumulation and distribution patterns
    """

    def __init__(self, window_seconds: int = 120):
        """
        Initialize volume-price analyzer

        Args:
            window_seconds: Analysis window in seconds
        """
        self.window_seconds = window_seconds
        self.correlation_threshold = 0.3  # Minimum correlation for signal
        self.volume_multiplier_threshold = 2.0  # Volume spike threshold
        self.price_stability_threshold = 0.005  # 0.5% price stability
        self.price_windows = {}  # symbol -> deque of price data
        self.volume_windows = {}  # symbol -> deque of volume data
        self.signal_cooldowns = {}  # symbol -> last signal time
        self.cooldown_period = 180  # 3 minutes cooldown

        # Performance tracking
        self.signal_history = deque(maxlen=1000)
        self.accuracy_stats = {
            'total_signals': 0,
            'profitable_signals': 0,
            'avg_return': 0.0
        }

        logger.info(f"VolumePriceAnalyzer initialized with {window_seconds}s window")

    def add_price_data(self, symbol: str, price_data: Dict):
        """
        Add new price data point

        Args:
            symbol: Trading pair symbol
            price_data: Dict with keys: price, high, low, timestamp
        """
        try:
            # Initialize window if needed
            if symbol not in self.price_windows:
                self.price_windows[symbol] = deque(maxlen=500)  # Keep last 500 data points

            # Validate price data
            required_keys = ['price', 'timestamp']
            if not all(key in price_data for key in required_keys):
                logger.warning(f"Invalid price data for {symbol}: missing required keys")
                return

            # Add data to window
            self.price_windows[symbol].append(price_data)

            # Clean old data
            self._clean_old_price_data(symbol)

            logger.debug(f"Added price data to {symbol}: {price_data['price']}")

        except Exception as e:
            logger.error(f"Error adding price data for {symbol}: {e}")

    def add_volume_data(self, symbol: str, volume_data: Dict):
        """
        Add new volume data point

        Args:
            symbol: Trading pair symbol
            volume_data: Dict with keys: volume, trade_count, timestamp
        """
        try:
            # Initialize window if needed
            if symbol not in self.volume_windows:
                self.volume_windows[symbol] = deque(maxlen=500)  # Keep last 500 data points

            # Validate volume data
            required_keys = ['volume', 'timestamp']
            if not all(key in volume_data for key in required_keys):
                logger.warning(f"Invalid volume data for {symbol}: missing required keys")
                return

            # Add data to window
            self.volume_windows[symbol].append(volume_data)

            # Clean old data
            self._clean_old_volume_data(symbol)

            logger.debug(f"Added volume data to {symbol}: {volume_data['volume']}")

        except Exception as e:
            logger.error(f"Error adding volume data for {symbol}: {e}")

    def _clean_old_price_data(self, symbol: str):
        """Remove price data older than analysis window"""
        if symbol not in self.price_windows:
            return

        cutoff_time = datetime.utcnow() - timedelta(seconds=self.window_seconds)
        window = self.price_windows[symbol]

        # Remove old data from front of deque
        while window and isinstance(window[0]['timestamp'], datetime) and window[0]['timestamp'] < cutoff_time:
            window.popleft()

    def _clean_old_volume_data(self, symbol: str):
        """Remove volume data older than analysis window"""
        if symbol not in self.volume_windows:
            return

        cutoff_time = datetime.utcnow() - timedelta(seconds=self.window_seconds)
        window = self.volume_windows[symbol]

        # Remove old data from front of deque
        while window and isinstance(window[0]['timestamp'], datetime) and window[0]['timestamp'] < cutoff_time:
            window.popleft()

    def calculate_correlation(self, symbol: str) -> float:
        """
        Calculate Pearson correlation between volume and price changes

        Args:
            symbol: Trading pair symbol

        Returns:
            Correlation coefficient between -1 and 1
        """
        try:
            if symbol not in self.price_windows or symbol not in self.volume_windows:
                return 0.0

            price_window = self.price_windows[symbol]
            volume_window = self.volume_windows[symbol]

            if len(price_window) < 5 or len(volume_window) < 5:
                return 0.0

            # Convert to pandas for easier analysis
            price_data = []
            for point in price_window:
                price_data.append({
                    'timestamp': point['timestamp'],
                    'price': point['price']
                })

            volume_data = []
            for point in volume_window:
                volume_data.append({
                    'timestamp': point['timestamp'],
                    'volume': point['volume']
                })

            price_df = pd.DataFrame(price_data).sort_values('timestamp')
            volume_df = pd.DataFrame(volume_data).sort_values('timestamp')

            # Align timestamps (use nearest neighbor approach)
            merged_df = pd.merge_asof(
                price_df.sort_values('timestamp'),
                volume_df.sort_values('timestamp'),
                on='timestamp',
                direction='nearest',
                tolerance=pd.Timedelta(seconds=30)
            )

            if len(merged_df) < 5:
                return 0.0

            # Calculate price changes
            merged_df['price_change'] = merged_df['price'].pct_change()

            # Calculate volume changes (use log to handle large variations)
            merged_df['log_volume'] = np.log(merged_df['volume'] + 1)
            merged_df['volume_change'] = merged_df['log_volume'].diff()

            # Remove NaN values
            clean_df = merged_df.dropna()

            if len(clean_df) < 5:
                return 0.0

            # Calculate Pearson correlation
            correlation, p_value = pearsonr(clean_df['price_change'], clean_df['volume_change'])

            # Handle NaN correlation
            if pd.isna(correlation):
                correlation = 0.0

            # Apply time weighting (more recent data has higher weight)
            if len(clean_df) > 10:
                # Calculate weighted correlation for recent data
                recent_data = clean_df.tail(10)
                if len(recent_data) >= 5:
                    recent_corr, _ = pearsonr(recent_data['price_change'], recent_data['volume_change'])
                    if not pd.isna(recent_corr):
                        # Weight recent correlation more heavily
                        correlation = 0.7 * recent_corr + 0.3 * correlation

            logger.debug(f"{symbol} volume-price correlation: {correlation:.3f}")

            return float(correlation)

        except Exception as e:
            logger.error(f"Error calculating correlation for {symbol}: {e}")
            return 0.0

    def calculate_volume_increase(self, symbol: str) -> float:
        """
        Calculate volume increase over analysis window

        Args:
            symbol: Trading pair symbol

        Returns:
            Volume increase multiplier (e.g., 2.0 = 100% increase)
        """
        try:
            if symbol not in self.volume_windows:
                return 1.0

            window = self.volume_windows[symbol]
            if len(window) < 10:
                return 1.0

            # Calculate average volume for first half vs second half of window
            mid_point = len(window) // 2
            early_volumes = [point['volume'] for point in list(window)[:mid_point]]
            recent_volumes = [point['volume'] for point in list(window)[mid_point:]]

            if not early_volumes or not recent_volumes:
                return 1.0

            early_avg = np.mean(early_volumes)
            recent_avg = np.mean(recent_volumes)

            if early_avg == 0:
                return 1.0

            volume_multiplier = recent_avg / early_avg

            logger.debug(f"{symbol} volume increase: {volume_multiplier:.2f}x")

            return float(volume_multiplier)

        except Exception as e:
            logger.error(f"Error calculating volume increase for {symbol}: {e}")
            return 1.0

    def calculate_price_stability(self, symbol: str) -> float:
        """
        Calculate price stability (lower values = more stable)

        Args:
            symbol: Trading pair symbol

        Returns:
            Price volatility as standard deviation of returns
        """
        try:
            if symbol not in self.price_windows:
                return 1.0

            window = self.price_windows[symbol]
            if len(window) < 5:
                return 1.0

            prices = [point['price'] for point in window]
            price_changes = np.diff(prices) / prices[:-1]  # Calculate returns

            if len(price_changes) == 0:
                return 1.0

            stability = np.std(price_changes)

            logger.debug(f"{symbol} price stability (volatility): {stability:.4f}")

            return float(stability)

        except Exception as e:
            logger.error(f"Error calculating price stability for {symbol}: {e}")
            return 1.0

    def is_signal_triggered(self, symbol: str) -> Tuple[bool, Optional[str]]:
        """
        Check if volume-price signal should be triggered

        Args:
            symbol: Trading pair symbol

        Returns:
            Tuple of (should_trigger, signal_type)
        """
        try:
            # Check cooldown
            if self._is_in_cooldown(symbol):
                return False, None

            correlation = self.calculate_correlation(symbol)
            volume_increase = self.calculate_volume_increase(symbol)
            price_stability = self.calculate_price_stability(symbol)

            # Check for accumulation pattern (high volume, stable price, low correlation)
            is_accumulation = (
                volume_increase >= self.volume_multiplier_threshold and
                price_stability <= self.price_stability_threshold and
                abs(correlation) <= self.correlation_threshold
            )

            # Check for distribution pattern (high volume, stable price, negative correlation)
            is_distribution = (
                volume_increase >= self.volume_multiplier_threshold and
                price_stability <= self.price_stability_threshold and
                correlation < -self.correlation_threshold
            )

            # Check for breakout pattern (high volume, positive correlation)
            is_breakout = (
                volume_increase >= self.volume_multiplier_threshold and
                correlation > self.correlation_threshold
            )

            signal_type = None
            if is_accumulation:
                signal_type = 'ACCUMULATION'
            elif is_distribution:
                signal_type = 'DISTRIBUTION'
            elif is_breakout:
                signal_type = 'BREAKOUT'

            if signal_type:
                # Record signal
                self._record_signal(symbol, signal_type, correlation, volume_increase, price_stability)
                self._set_cooldown(symbol)

                logger.info(f"Volume-price signal triggered for {symbol}: {signal_type} "
                          f"(corr: {correlation:.3f}, vol: {volume_increase:.2f}x, stability: {price_stability:.4f})")
                return True, signal_type

            return False, None

        except Exception as e:
            logger.error(f"Error checking volume-price signal for {symbol}: {e}")
            return False, None

    def _is_in_cooldown(self, symbol: str) -> bool:
        """Check if symbol is in cooldown period"""
        if symbol not in self.signal_cooldowns:
            return False

        return datetime.utcnow() < self.signal_cooldowns[symbol]

    def _set_cooldown(self, symbol: str):
        """Set cooldown period for symbol"""
        self.signal_cooldowns[symbol] = datetime.utcnow() + timedelta(seconds=self.cooldown_period)

    def _record_signal(self, symbol: str, signal_type: str, correlation: float, 
                      volume_increase: float, price_stability: float):
        """Record signal for analysis"""
        signal_record = {
            'symbol': symbol,
            'signal_type': signal_type,
            'correlation': correlation,
            'volume_increase': volume_increase,
            'price_stability': price_stability,
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
            'analyzed_symbols': len(set(list(self.price_windows.keys()) + list(self.volume_windows.keys()))),
            'correlation_threshold': self.correlation_threshold,
            'volume_multiplier_threshold': self.volume_multiplier_threshold,
            'price_stability_threshold': self.price_stability_threshold,
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
            correlation_threshold: New correlation threshold
            volume_multiplier_threshold: New volume multiplier threshold
            price_stability_threshold: New price stability threshold
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
            self.price_windows.pop(symbol, None)
            self.volume_windows.pop(symbol, None)
            self.signal_cooldowns.pop(symbol, None)
            logger.info(f"Cleared data for {symbol}")
        else:
            self.price_windows.clear()
            self.volume_windows.clear()
            self.signal_cooldowns.clear()
            logger.info("Cleared all data")

    def __repr__(self):
        stats = self.get_signal_stats()
        return f"VolumePriceAnalyzer(symbols={stats['analyzed_symbols']}, signals={stats['total_signals']}, cooldowns={stats['active_cooldowns']})"
