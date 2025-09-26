"""
Multi-Algorithm Signal Confirmation System
Implements signal combination logic for strong signal generation
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger
from config.logging_config import get_logger

logger = get_logger("algorithms.signal_aggregator")

class SignalAggregator:
    """
    Aggregates signals from multiple algorithms for confirmation
    Implements weighted voting and temporal alignment
    """

    def __init__(self, confirmation_threshold: int = 2):
        """
        Initialize signal aggregator

        Args:
            confirmation_threshold: Minimum number of algorithms required for confirmation
        """
        self.confirmation_threshold = confirmation_threshold
        self.recent_signals = defaultdict(list)  # symbol -> list of recent signals
        self.signal_window_seconds = 30  # Time window for signal confirmation
        self.algorithm_weights = {
            'order_flow': 1.0,
            'liquidity': 1.0,
            'volume_price': 0.8
        }
        self.combined_signals = []  # History of combined signals
        self.symbol_cooldowns = {}  # symbol -> cooldown expiry time
        self.cooldown_period = 300  # 5 minutes cooldown for combined signals

        # Performance tracking
        self.stats = {
            'total_combined_signals': 0,
            'algorithm_contributions': defaultdict(int),
            'signal_type_counts': defaultdict(int)
        }

        logger.info(f"SignalAggregator initialized with threshold={confirmation_threshold}")

    def add_algorithm_signal(self, symbol: str, signal_type: str, 
                           algorithm_name: str, confidence: float) -> bool:
        """
        Add signal from individual algorithm

        Args:
            symbol: Trading pair symbol
            signal_type: Type of signal (BUY, SELL, etc.)
            algorithm_name: Name of the algorithm generating the signal
            confidence: Confidence score (0.0 to 1.0)

        Returns:
            True if combined signal was generated, False otherwise
        """
        try:
            # Check if symbol is in cooldown
            if self._is_in_cooldown(symbol):
                logger.debug(f"Symbol {symbol} is in cooldown, ignoring signal")
                return False

            # Create signal record
            signal_record = {
                'symbol': symbol,
                'signal_type': signal_type,
                'algorithm': algorithm_name,
                'confidence': confidence,
                'timestamp': datetime.utcnow(),
                'weight': self.algorithm_weights.get(algorithm_name, 1.0)
            }

            # Add to recent signals
            self.recent_signals[symbol].append(signal_record)

            # Clean old signals
            self._clean_old_signals(symbol)

            # Update stats
            self.stats['algorithm_contributions'][algorithm_name] += 1

            logger.debug(f"Added signal from {algorithm_name} for {symbol}: {signal_type} (confidence: {confidence:.3f})")

            # Check for confirmation
            confirmed, combined_strength = self._check_confirmation(symbol, signal_type)

            if confirmed:
                # Generate combined signal
                self._generate_combined_signal(symbol, signal_type, combined_strength)
                self._set_cooldown(symbol)
                return True

            return False

        except Exception as e:
            logger.error(f"Error adding algorithm signal: {e}")
            return False

    def _clean_old_signals(self, symbol: str):
        """Remove signals older than the confirmation window"""
        if symbol not in self.recent_signals:
            return

        cutoff_time = datetime.utcnow() - timedelta(seconds=self.signal_window_seconds)
        
        # Filter out old signals
        self.recent_signals[symbol] = [
            signal for signal in self.recent_signals[symbol]
            if signal['timestamp'] > cutoff_time
        ]

        # Remove empty entries
        if not self.recent_signals[symbol]:
            del self.recent_signals[symbol]

    def _check_confirmation(self, symbol: str, signal_type: str) -> Tuple[bool, float]:
        """
        Check if multiple algorithms confirm the same signal

        Args:
            symbol: Trading pair symbol
            signal_type: Signal type to check for confirmation

        Returns:
            Tuple of (is_confirmed, combined_strength)
        """
        try:
            if symbol not in self.recent_signals:
                return False, 0.0

            # Get signals of the same type within the time window
            matching_signals = [
                signal for signal in self.recent_signals[symbol]
                if signal['signal_type'] == signal_type
            ]

            if len(matching_signals) < self.confirmation_threshold:
                return False, 0.0

            # Check for algorithm diversity (no duplicate algorithms)
            algorithms_used = set(signal['algorithm'] for signal in matching_signals)
            
            if len(algorithms_used) < self.confirmation_threshold:
                return False, 0.0

            # Calculate combined strength
            combined_strength = self._calculate_combined_strength(matching_signals)

            logger.debug(f"Signal confirmation for {symbol} {signal_type}: "
                        f"{len(matching_signals)} signals from {len(algorithms_used)} algorithms, "
                        f"strength: {combined_strength:.3f}")

            return True, combined_strength

        except Exception as e:
            logger.error(f"Error checking confirmation for {symbol}: {e}")
            return False, 0.0

    def _calculate_combined_strength(self, signals: List[Dict]) -> float:
        """
        Calculate combined signal strength from multiple algorithms

        Args:
            signals: List of signal records

        Returns:
            Combined strength score (0.0 to 1.0)
        """
        try:
            if not signals:
                return 0.0

            total_weighted_confidence = 0.0
            total_weight = 0.0

            for signal in signals:
                confidence = signal['confidence']
                weight = signal['weight']
                
                # Apply time decay (more recent signals have higher weight)
                age_seconds = (datetime.utcnow() - signal['timestamp']).total_seconds()
                time_decay = max(0.5, 1.0 - (age_seconds / self.signal_window_seconds))
                
                effective_weight = weight * time_decay
                total_weighted_confidence += confidence * effective_weight
                total_weight += effective_weight

            if total_weight == 0:
                return 0.0

            # Calculate weighted average
            combined_strength = total_weighted_confidence / total_weight

            # Apply bonus for algorithm diversity
            unique_algorithms = len(set(signal['algorithm'] for signal in signals))
            diversity_bonus = min(0.2, (unique_algorithms - 1) * 0.1)
            combined_strength = min(1.0, combined_strength + diversity_bonus)

            return combined_strength

        except Exception as e:
            logger.error(f"Error calculating combined strength: {e}")
            return 0.0

    def _generate_combined_signal(self, symbol: str, signal_type: str, strength: float):
        """Generate and record combined signal"""
        try:
            combined_signal = {
                'symbol': symbol,
                'signal_type': signal_type,
                'strength': strength,
                'timestamp': datetime.utcnow(),
                'contributing_algorithms': [
                    signal['algorithm'] for signal in self.recent_signals[symbol]
                    if signal['signal_type'] == signal_type
                ],
                'algorithm_count': len(set(
                    signal['algorithm'] for signal in self.recent_signals[symbol]
                    if signal['signal_type'] == signal_type
                ))
            }

            self.combined_signals.append(combined_signal)

            # Update stats
            self.stats['total_combined_signals'] += 1
            self.stats['signal_type_counts'][signal_type] += 1

            logger.info(f"Combined signal generated for {symbol}: {signal_type} "
                       f"(strength: {strength:.3f}, algorithms: {combined_signal['algorithm_count']})")

        except Exception as e:
            logger.error(f"Error generating combined signal: {e}")

    def get_combined_signal_strength(self, symbol: str, signal_type: str) -> float:
        """
        Get combined signal strength for a specific symbol and type

        Args:
            symbol: Trading pair symbol
            signal_type: Signal type

        Returns:
            Combined signal strength (0.0 to 1.0)
        """
        try:
            if symbol not in self.recent_signals:
                return 0.0

            matching_signals = [
                signal for signal in self.recent_signals[symbol]
                if signal['signal_type'] == signal_type
            ]

            if not matching_signals:
                return 0.0

            return self._calculate_combined_strength(matching_signals)

        except Exception as e:
            logger.error(f"Error getting combined signal strength: {e}")
            return 0.0

    def is_in_cooldown(self, symbol: str) -> bool:
        """
        Check if symbol is in cooldown period

        Args:
            symbol: Trading pair symbol

        Returns:
            True if in cooldown, False otherwise
        """
        return self._is_in_cooldown(symbol)

    def _is_in_cooldown(self, symbol: str) -> bool:
        """Internal cooldown check"""
        if symbol not in self.symbol_cooldowns:
            return False

        return datetime.utcnow() < self.symbol_cooldowns[symbol]

    def _set_cooldown(self, symbol: str):
        """Set cooldown period for symbol"""
        self.symbol_cooldowns[symbol] = datetime.utcnow() + timedelta(seconds=self.cooldown_period)

    def get_recent_combined_signals(self, limit: int = 10) -> List[Dict]:
        """
        Get recent combined signals

        Args:
            limit: Maximum number of signals to return

        Returns:
            List of recent combined signals
        """
        return self.combined_signals[-limit:] if self.combined_signals else []

    def get_aggregator_stats(self) -> Dict:
        """Get aggregator statistics"""
        return {
            'total_combined_signals': self.stats['total_combined_signals'],
            'active_symbols': len(self.recent_signals),
            'active_cooldowns': len(self.symbol_cooldowns),
            'confirmation_threshold': self.confirmation_threshold,
            'signal_window_seconds': self.signal_window_seconds,
            'algorithm_contributions': dict(self.stats['algorithm_contributions']),
            'signal_type_counts': dict(self.stats['signal_type_counts'])
        }

    def update_algorithm_weights(self, weights: Dict[str, float]):
        """
        Update algorithm weights

        Args:
            weights: Dictionary of algorithm names to weights
        """
        self.algorithm_weights.update(weights)
        logger.info(f"Updated algorithm weights: {self.algorithm_weights}")

    def update_parameters(self, **kwargs):
        """
        Update aggregator parameters

        Args:
            confirmation_threshold: New confirmation threshold
            signal_window_seconds: New signal window
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
            self.recent_signals.pop(symbol, None)
            self.symbol_cooldowns.pop(symbol, None)
            logger.info(f"Cleared data for {symbol}")
        else:
            self.recent_signals.clear()
            self.symbol_cooldowns.clear()
            self.combined_signals.clear()
            logger.info("Cleared all data")

    def cleanup_expired_data(self):
        """Clean up expired signals and cooldowns"""
        try:
            # Clean expired signals
            for symbol in list(self.recent_signals.keys()):
                self._clean_old_signals(symbol)

            # Clean expired cooldowns
            current_time = datetime.utcnow()
            expired_cooldowns = [
                symbol for symbol, expiry_time in self.symbol_cooldowns.items()
                if current_time >= expiry_time
            ]

            for symbol in expired_cooldowns:
                del self.symbol_cooldowns[symbol]

            if expired_cooldowns:
                logger.debug(f"Cleaned up {len(expired_cooldowns)} expired cooldowns")

        except Exception as e:
            logger.error(f"Error cleaning up expired data: {e}")

    def __repr__(self):
        stats = self.get_aggregator_stats()
        return (f"SignalAggregator(threshold={self.confirmation_threshold}, "
                f"active_symbols={stats['active_symbols']}, "
                f"combined_signals={stats['total_combined_signals']})")
