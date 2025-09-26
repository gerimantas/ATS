"""
Cool-Down Period Management System
Implements signal blocking mechanism for specific trading pairs after recent signals
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from config.logging_config import get_logger

logger = get_logger("risk.cooldown")

class CooldownManager:
    """
    Manages cooldown periods for trading signals
    Prevents signal spam and implements dynamic cooldown adjustment
    """

    def __init__(self):
        """Initialize cooldown manager"""
        self.cooldown_periods = {}  # symbol -> expiry_time
        self.default_cooldown_minutes = 15
        self.symbol_specific_cooldowns = {}  # symbol -> custom_minutes
        self.success_rates = {}  # symbol -> success_rate_data
        self.dynamic_adjustment = True
        
        # Performance tracking
        self.stats = {
            'total_cooldowns_set': 0,
            'active_cooldowns': 0,
            'signals_blocked': 0,
            'cooldown_violations': 0
        }

        # Success rate tracking for dynamic adjustment
        self.signal_history = {}  # symbol -> list of signal results

        # Cooldown adjustment parameters
        self.min_cooldown_minutes = 5
        self.max_cooldown_minutes = 60
        self.success_rate_window = 10  # Number of recent signals to consider

        logger.info("CooldownManager initialized")

    def set_cooldown(self, symbol: str, minutes: Optional[int] = None):
        """
        Set cooldown period for a symbol

        Args:
            symbol: Trading pair symbol
            minutes: Cooldown duration in minutes (uses default if None)
        """
        try:
            # Determine cooldown duration
            if minutes is None:
                if self.dynamic_adjustment:
                    minutes = self._calculate_dynamic_cooldown(symbol)
                else:
                    minutes = self.symbol_specific_cooldowns.get(symbol, self.default_cooldown_minutes)

            # Set expiry time
            expiry_time = datetime.utcnow() + timedelta(minutes=minutes)
            self.cooldown_periods[symbol] = expiry_time

            # Update stats
            self.stats['total_cooldowns_set'] += 1
            self.stats['active_cooldowns'] = len(self.cooldown_periods)

            logger.info(f"Set cooldown for {symbol}: {minutes} minutes (expires at {expiry_time.strftime('%H:%M:%S')})")

        except Exception as e:
            logger.error(f"Error setting cooldown for {symbol}: {e}")

    def _calculate_dynamic_cooldown(self, symbol: str) -> int:
        """
        Calculate dynamic cooldown based on success rate

        Args:
            symbol: Trading pair symbol

        Returns:
            Cooldown duration in minutes
        """
        try:
            # Get symbol-specific base cooldown
            base_cooldown = self.symbol_specific_cooldowns.get(symbol, self.default_cooldown_minutes)

            # If no history, use base cooldown
            if symbol not in self.signal_history or not self.signal_history[symbol]:
                return base_cooldown

            # Calculate recent success rate
            recent_signals = self.signal_history[symbol][-self.success_rate_window:]
            if not recent_signals:
                return base_cooldown

            successful_signals = sum(1 for signal in recent_signals if signal['success'])
            success_rate = successful_signals / len(recent_signals)

            # Adjust cooldown based on success rate
            if success_rate >= 0.8:  # High success rate
                adjustment_factor = 0.7  # Shorter cooldown
            elif success_rate >= 0.6:  # Good success rate
                adjustment_factor = 0.85
            elif success_rate >= 0.4:  # Average success rate
                adjustment_factor = 1.0  # No adjustment
            elif success_rate >= 0.2:  # Poor success rate
                adjustment_factor = 1.5  # Longer cooldown
            else:  # Very poor success rate
                adjustment_factor = 2.0  # Much longer cooldown

            # Calculate adjusted cooldown
            adjusted_cooldown = int(base_cooldown * adjustment_factor)

            # Apply bounds
            adjusted_cooldown = max(self.min_cooldown_minutes, 
                                  min(self.max_cooldown_minutes, adjusted_cooldown))

            logger.debug(f"Dynamic cooldown for {symbol}: {adjusted_cooldown}min "
                        f"(success_rate: {success_rate:.2f}, factor: {adjustment_factor:.2f})")

            return adjusted_cooldown

        except Exception as e:
            logger.error(f"Error calculating dynamic cooldown for {symbol}: {e}")
            return self.default_cooldown_minutes

    def is_in_cooldown(self, symbol: str) -> bool:
        """
        Check if symbol is currently in cooldown period

        Args:
            symbol: Trading pair symbol

        Returns:
            True if in cooldown, False otherwise
        """
        try:
            if symbol not in self.cooldown_periods:
                return False

            current_time = datetime.utcnow()
            expiry_time = self.cooldown_periods[symbol]

            # Check if cooldown has expired
            if current_time >= expiry_time:
                # Remove expired cooldown
                del self.cooldown_periods[symbol]
                self.stats['active_cooldowns'] = len(self.cooldown_periods)
                return False

            # Still in cooldown
            if current_time < expiry_time:
                self.stats['signals_blocked'] += 1
                logger.debug(f"{symbol} is in cooldown until {expiry_time.strftime('%H:%M:%S')}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking cooldown for {symbol}: {e}")
            return True  # Default to cooldown on error for safety

    def get_remaining_cooldown(self, symbol: str) -> Optional[int]:
        """
        Get remaining cooldown time in seconds

        Args:
            symbol: Trading pair symbol

        Returns:
            Remaining seconds, or None if not in cooldown
        """
        try:
            if symbol not in self.cooldown_periods:
                return None

            current_time = datetime.utcnow()
            expiry_time = self.cooldown_periods[symbol]

            if current_time >= expiry_time:
                # Cooldown expired
                del self.cooldown_periods[symbol]
                self.stats['active_cooldowns'] = len(self.cooldown_periods)
                return None

            remaining_seconds = int((expiry_time - current_time).total_seconds())
            return max(0, remaining_seconds)

        except Exception as e:
            logger.error(f"Error getting remaining cooldown for {symbol}: {e}")
            return None

    def record_signal_result(self, symbol: str, success: bool, profit: float = 0.0):
        """
        Record the result of a signal for dynamic cooldown adjustment

        Args:
            symbol: Trading pair symbol
            success: Whether the signal was successful
            profit: Profit/loss percentage (optional)
        """
        try:
            # Initialize history if needed
            if symbol not in self.signal_history:
                self.signal_history[symbol] = []

            # Add signal result
            signal_result = {
                'timestamp': datetime.utcnow(),
                'success': success,
                'profit': profit
            }

            self.signal_history[symbol].append(signal_result)

            # Keep only recent history
            max_history = self.success_rate_window * 3  # Keep 3x window size
            if len(self.signal_history[symbol]) > max_history:
                self.signal_history[symbol] = self.signal_history[symbol][-max_history:]

            # Update success rate
            self._update_success_rate(symbol)

            logger.debug(f"Recorded signal result for {symbol}: success={success}, profit={profit:.4f}")

        except Exception as e:
            logger.error(f"Error recording signal result for {symbol}: {e}")

    def _update_success_rate(self, symbol: str):
        """Update success rate statistics for a symbol"""
        try:
            if symbol not in self.signal_history or not self.signal_history[symbol]:
                return

            recent_signals = self.signal_history[symbol][-self.success_rate_window:]
            if not recent_signals:
                return

            successful_signals = sum(1 for signal in recent_signals if signal['success'])
            success_rate = successful_signals / len(recent_signals)

            # Calculate average profit
            profits = [signal['profit'] for signal in recent_signals if signal['profit'] != 0.0]
            avg_profit = sum(profits) / len(profits) if profits else 0.0

            self.success_rates[symbol] = {
                'success_rate': success_rate,
                'avg_profit': avg_profit,
                'total_signals': len(recent_signals),
                'last_updated': datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Error updating success rate for {symbol}: {e}")

    def cleanup_expired_cooldowns(self):
        """Remove expired cooldowns from memory"""
        try:
            current_time = datetime.utcnow()
            expired_symbols = []

            for symbol, expiry_time in self.cooldown_periods.items():
                if current_time >= expiry_time:
                    expired_symbols.append(symbol)

            # Remove expired cooldowns
            for symbol in expired_symbols:
                del self.cooldown_periods[symbol]

            if expired_symbols:
                self.stats['active_cooldowns'] = len(self.cooldown_periods)
                logger.debug(f"Cleaned up {len(expired_symbols)} expired cooldowns")

        except Exception as e:
            logger.error(f"Error cleaning up expired cooldowns: {e}")

    def get_cooldown_stats(self) -> Dict:
        """Get cooldown statistics"""
        return {
            'total_cooldowns_set': self.stats['total_cooldowns_set'],
            'active_cooldowns': len(self.cooldown_periods),
            'signals_blocked': self.stats['signals_blocked'],
            'cooldown_violations': self.stats['cooldown_violations'],
            'default_cooldown_minutes': self.default_cooldown_minutes,
            'dynamic_adjustment': self.dynamic_adjustment,
            'symbols_with_custom_cooldowns': len(self.symbol_specific_cooldowns),
            'symbols_with_history': len(self.signal_history)
        }

    def get_active_cooldowns(self) -> Dict[str, Dict]:
        """Get information about active cooldowns"""
        try:
            active_cooldowns = {}
            current_time = datetime.utcnow()

            for symbol, expiry_time in self.cooldown_periods.items():
                if current_time < expiry_time:
                    remaining_seconds = int((expiry_time - current_time).total_seconds())
                    active_cooldowns[symbol] = {
                        'expires_at': expiry_time.isoformat(),
                        'remaining_seconds': remaining_seconds,
                        'remaining_minutes': remaining_seconds // 60
                    }

            return active_cooldowns

        except Exception as e:
            logger.error(f"Error getting active cooldowns: {e}")
            return {}

    def get_success_rates(self) -> Dict[str, Dict]:
        """Get success rate information for all symbols"""
        return self.success_rates.copy()

    def set_symbol_cooldown(self, symbol: str, minutes: int):
        """
        Set custom cooldown duration for a specific symbol

        Args:
            symbol: Trading pair symbol
            minutes: Cooldown duration in minutes
        """
        try:
            minutes = max(self.min_cooldown_minutes, min(self.max_cooldown_minutes, minutes))
            self.symbol_specific_cooldowns[symbol] = minutes
            logger.info(f"Set custom cooldown for {symbol}: {minutes} minutes")

        except Exception as e:
            logger.error(f"Error setting symbol cooldown for {symbol}: {e}")

    def remove_symbol_cooldown(self, symbol: str):
        """
        Remove custom cooldown for a symbol (will use default)

        Args:
            symbol: Trading pair symbol
        """
        try:
            self.symbol_specific_cooldowns.pop(symbol, None)
            logger.info(f"Removed custom cooldown for {symbol}")

        except Exception as e:
            logger.error(f"Error removing symbol cooldown for {symbol}: {e}")

    def force_remove_cooldown(self, symbol: str):
        """
        Force remove cooldown for a symbol (emergency use)

        Args:
            symbol: Trading pair symbol
        """
        try:
            if symbol in self.cooldown_periods:
                del self.cooldown_periods[symbol]
                self.stats['active_cooldowns'] = len(self.cooldown_periods)
                self.stats['cooldown_violations'] += 1
                logger.warning(f"Force removed cooldown for {symbol}")

        except Exception as e:
            logger.error(f"Error force removing cooldown for {symbol}: {e}")

    def update_parameters(self, **kwargs):
        """
        Update cooldown manager parameters

        Args:
            default_cooldown_minutes: New default cooldown duration
            dynamic_adjustment: Enable/disable dynamic adjustment
            min_cooldown_minutes: Minimum cooldown duration
            max_cooldown_minutes: Maximum cooldown duration
            success_rate_window: Window size for success rate calculation
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"Updated {key} to {value}")

    def clear_all_cooldowns(self):
        """Clear all active cooldowns (emergency use)"""
        try:
            cleared_count = len(self.cooldown_periods)
            self.cooldown_periods.clear()
            self.stats['active_cooldowns'] = 0
            self.stats['cooldown_violations'] += cleared_count
            logger.warning(f"Cleared all {cleared_count} active cooldowns")

        except Exception as e:
            logger.error(f"Error clearing all cooldowns: {e}")

    def clear_history(self, symbol: Optional[str] = None):
        """
        Clear signal history

        Args:
            symbol: Specific symbol to clear, or None for all
        """
        try:
            if symbol:
                self.signal_history.pop(symbol, None)
                self.success_rates.pop(symbol, None)
                logger.info(f"Cleared history for {symbol}")
            else:
                self.signal_history.clear()
                self.success_rates.clear()
                logger.info("Cleared all signal history")

        except Exception as e:
            logger.error(f"Error clearing history: {e}")

    def __repr__(self):
        stats = self.get_cooldown_stats()
        return (f"CooldownManager(active={stats['active_cooldowns']}, "
                f"total_set={stats['total_cooldowns_set']}, "
                f"blocked={stats['signals_blocked']})")
