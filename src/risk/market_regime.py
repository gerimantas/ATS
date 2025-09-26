"""
Market Regime Filter System
Implements BTC/ETH volatility monitoring and altcoin signal filtering
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta
import numpy as np
from loguru import logger
from config.logging_config import get_logger

logger = get_logger("risk.market_regime")

class MarketRegimeFilter:
    """
    Monitors market volatility and filters signals based on market regime
    Uses BTC/ETH volatility to determine overall market conditions
    """

    def __init__(self, volatility_window: int = 300):  # 5 minutes
        """
        Initialize market regime filter

        Args:
            volatility_window: Window for volatility calculation in seconds
        """
        self.volatility_window = volatility_window
        self.volatility_thresholds = {
            'CALM': 0.02,           # 2% volatility
            'NORMAL': 0.05,         # 5% volatility
            'VOLATILE': 0.10,       # 10% volatility
            'HIGHLY_VOLATILE': 0.20 # 20% volatility
        }
        self.price_windows = {}  # symbol -> deque of prices
        self.current_regime = 'NORMAL'
        self.regime_persistence = 3  # Require 3 confirmations for regime change
        self.regime_confirmations = 0
        self.pending_regime = None

        # Risk multipliers for different regimes
        self.risk_multipliers = {
            'CALM': 1.0,
            'NORMAL': 1.0,
            'VOLATILE': 1.5,
            'HIGHLY_VOLATILE': 2.0
        }

        # Signal filtering rules
        self.filtering_rules = {
            'CALM': {'filter_altcoins': False, 'position_size_multiplier': 1.0},
            'NORMAL': {'filter_altcoins': False, 'position_size_multiplier': 1.0},
            'VOLATILE': {'filter_altcoins': True, 'position_size_multiplier': 0.7},
            'HIGHLY_VOLATILE': {'filter_altcoins': True, 'position_size_multiplier': 0.5}
        }

        # Performance tracking
        self.regime_history = []
        self.filtered_signals = 0
        self.total_signals_checked = 0

        logger.info(f"MarketRegimeFilter initialized with {volatility_window}s window")

    def add_price_data(self, symbol: str, price: float, timestamp: datetime):
        """
        Add new price data point

        Args:
            symbol: Symbol (BTC, ETH, etc.)
            price: Current price
            timestamp: Timestamp of the price data
        """
        try:
            # Initialize window if needed
            if symbol not in self.price_windows:
                self.price_windows[symbol] = deque(maxlen=1000)  # Keep last 1000 prices

            # Add price data
            self.price_windows[symbol].append({
                'price': price,
                'timestamp': timestamp
            })

            # Clean old data
            self._clean_old_data(symbol)

            logger.debug(f"Added price data for {symbol}: {price}")

            # Update market regime if this is BTC or ETH
            if symbol in ['BTC', 'BTCUSDT', 'ETH', 'ETHUSDT']:
                self._update_market_regime()

        except Exception as e:
            logger.error(f"Error adding price data for {symbol}: {e}")

    def _clean_old_data(self, symbol: str):
        """Remove price data older than volatility window"""
        if symbol not in self.price_windows:
            return

        cutoff_time = datetime.utcnow() - timedelta(seconds=self.volatility_window)
        window = self.price_windows[symbol]

        # Remove old data from front of deque
        while window and window[0]['timestamp'] < cutoff_time:
            window.popleft()

    def calculate_volatility(self, symbol: str) -> float:
        """
        Calculate current volatility for a symbol

        Args:
            symbol: Symbol to calculate volatility for

        Returns:
            Annualized volatility as a decimal (e.g., 0.05 = 5%)
        """
        try:
            if symbol not in self.price_windows:
                return 0.0

            window = self.price_windows[symbol]
            if len(window) < 10:  # Need at least 10 data points
                return 0.0

            # Extract prices and calculate log returns
            prices = [point['price'] for point in window]
            log_returns = []

            for i in range(1, len(prices)):
                if prices[i-1] > 0 and prices[i] > 0:
                    log_return = np.log(prices[i] / prices[i-1])
                    log_returns.append(log_return)

            if len(log_returns) < 5:
                return 0.0

            # Calculate standard deviation of returns
            volatility = np.std(log_returns)

            # Annualize volatility (assuming data points are roughly 1 minute apart)
            # Convert to annual volatility: sqrt(525600) for minutes in a year
            annual_volatility = volatility * np.sqrt(525600)

            logger.debug(f"{symbol} volatility: {annual_volatility:.4f}")

            return float(annual_volatility)

        except Exception as e:
            logger.error(f"Error calculating volatility for {symbol}: {e}")
            return 0.0

    def get_market_regime(self, btc_volatility: float, eth_volatility: float) -> str:
        """
        Determine current market regime based on BTC and ETH volatility

        Args:
            btc_volatility: BTC volatility
            eth_volatility: ETH volatility

        Returns:
            Market regime string
        """
        try:
            # Use the higher of the two volatilities for regime determination
            max_volatility = max(btc_volatility, eth_volatility)

            # Determine regime based on thresholds
            if max_volatility >= self.volatility_thresholds['HIGHLY_VOLATILE']:
                return 'HIGHLY_VOLATILE'
            elif max_volatility >= self.volatility_thresholds['VOLATILE']:
                return 'VOLATILE'
            elif max_volatility >= self.volatility_thresholds['NORMAL']:
                return 'NORMAL'
            else:
                return 'CALM'

        except Exception as e:
            logger.error(f"Error determining market regime: {e}")
            return 'NORMAL'

    def _update_market_regime(self):
        """Update market regime based on current BTC and ETH volatility"""
        try:
            # Calculate volatilities for BTC and ETH
            btc_symbols = ['BTC', 'BTCUSDT']
            eth_symbols = ['ETH', 'ETHUSDT']

            btc_volatility = 0.0
            eth_volatility = 0.0

            # Get BTC volatility
            for symbol in btc_symbols:
                if symbol in self.price_windows:
                    btc_volatility = max(btc_volatility, self.calculate_volatility(symbol))

            # Get ETH volatility
            for symbol in eth_symbols:
                if symbol in self.price_windows:
                    eth_volatility = max(eth_volatility, self.calculate_volatility(symbol))

            # Determine new regime
            new_regime = self.get_market_regime(btc_volatility, eth_volatility)

            # Handle regime persistence
            if new_regime != self.current_regime:
                if self.pending_regime == new_regime:
                    self.regime_confirmations += 1
                else:
                    self.pending_regime = new_regime
                    self.regime_confirmations = 1

                # Change regime if we have enough confirmations
                if self.regime_confirmations >= self.regime_persistence:
                    old_regime = self.current_regime
                    self.current_regime = new_regime
                    self.pending_regime = None
                    self.regime_confirmations = 0

                    # Record regime change
                    self.regime_history.append({
                        'timestamp': datetime.utcnow(),
                        'old_regime': old_regime,
                        'new_regime': new_regime,
                        'btc_volatility': btc_volatility,
                        'eth_volatility': eth_volatility
                    })

                    # Keep only recent history
                    if len(self.regime_history) > 100:
                        self.regime_history = self.regime_history[-100:]

                    logger.info(f"Market regime changed: {old_regime} -> {new_regime} "
                              f"(BTC: {btc_volatility:.4f}, ETH: {eth_volatility:.4f})")
            else:
                # Reset pending regime if current regime is confirmed
                self.pending_regime = None
                self.regime_confirmations = 0

        except Exception as e:
            logger.error(f"Error updating market regime: {e}")

    def should_filter_signal(self, symbol: str, regime: str = None, 
                           is_altcoin: bool = True) -> Tuple[bool, str]:
        """
        Determine if signal should be filtered based on market regime

        Args:
            symbol: Trading pair symbol
            regime: Market regime (uses current if None)
            is_altcoin: Whether the symbol is an altcoin

        Returns:
            Tuple of (should_filter, reason)
        """
        try:
            self.total_signals_checked += 1

            if regime is None:
                regime = self.current_regime

            filtering_rule = self.filtering_rules.get(regime, self.filtering_rules['NORMAL'])

            # Check if altcoins should be filtered in this regime
            if is_altcoin and filtering_rule['filter_altcoins']:
                self.filtered_signals += 1
                reason = f"Altcoin signals filtered in {regime} market"
                logger.debug(f"Filtered signal for {symbol}: {reason}")
                return True, reason

            # Additional filtering based on correlation during stress periods
            if regime in ['VOLATILE', 'HIGHLY_VOLATILE']:
                # In volatile markets, be more selective
                if is_altcoin and self._is_high_correlation_period():
                    self.filtered_signals += 1
                    reason = f"High correlation period in {regime} market"
                    logger.debug(f"Filtered signal for {symbol}: {reason}")
                    return True, reason

            return False, "Signal passed regime filter"

        except Exception as e:
            logger.error(f"Error checking signal filter for {symbol}: {e}")
            return True, "Error in regime filter - filtered for safety"

    def _is_high_correlation_period(self) -> bool:
        """Check if we're in a high correlation period (simplified heuristic)"""
        try:
            # During volatile periods, assume higher correlation
            # This is a simplified implementation - in practice, you'd calculate actual correlations
            return self.current_regime in ['VOLATILE', 'HIGHLY_VOLATILE']
        except Exception:
            return True  # Default to high correlation for safety

    def get_position_size_multiplier(self, regime: str = None) -> float:
        """
        Get position size multiplier for current regime

        Args:
            regime: Market regime (uses current if None)

        Returns:
            Position size multiplier
        """
        if regime is None:
            regime = self.current_regime

        return self.filtering_rules.get(regime, self.filtering_rules['NORMAL'])['position_size_multiplier']

    def get_risk_multiplier(self, regime: str = None) -> float:
        """
        Get risk multiplier for current regime

        Args:
            regime: Market regime (uses current if None)

        Returns:
            Risk multiplier
        """
        if regime is None:
            regime = self.current_regime

        return self.risk_multipliers.get(regime, 1.0)

    def get_regime_stats(self) -> Dict:
        """Get market regime statistics"""
        return {
            'current_regime': self.current_regime,
            'pending_regime': self.pending_regime,
            'regime_confirmations': self.regime_confirmations,
            'total_signals_checked': self.total_signals_checked,
            'filtered_signals': self.filtered_signals,
            'filter_rate': (
                self.filtered_signals / max(1, self.total_signals_checked)
            ),
            'volatility_thresholds': self.volatility_thresholds,
            'risk_multipliers': self.risk_multipliers,
            'position_size_multiplier': self.get_position_size_multiplier()
        }

    def get_recent_regime_changes(self, limit: int = 10) -> List[Dict]:
        """Get recent regime changes"""
        return self.regime_history[-limit:] if self.regime_history else []

    def update_thresholds(self, thresholds: Dict[str, float]):
        """
        Update volatility thresholds

        Args:
            thresholds: Dictionary of regime names to volatility thresholds
        """
        self.volatility_thresholds.update(thresholds)
        logger.info(f"Updated volatility thresholds: {self.volatility_thresholds}")

    def update_filtering_rules(self, rules: Dict[str, Dict]):
        """
        Update filtering rules

        Args:
            rules: Dictionary of regime names to filtering rules
        """
        self.filtering_rules.update(rules)
        logger.info(f"Updated filtering rules: {self.filtering_rules}")

    def update_parameters(self, **kwargs):
        """
        Update filter parameters

        Args:
            volatility_window: New volatility window
            regime_persistence: New regime persistence requirement
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
            logger.info(f"Cleared data for {symbol}")
        else:
            self.price_windows.clear()
            self.regime_history.clear()
            self.current_regime = 'NORMAL'
            self.pending_regime = None
            self.regime_confirmations = 0
            logger.info("Cleared all data")

    def __repr__(self):
        stats = self.get_regime_stats()
        return (f"MarketRegimeFilter(regime={stats['current_regime']}, "
                f"filtered={stats['filtered_signals']}/{stats['total_signals_checked']})")
