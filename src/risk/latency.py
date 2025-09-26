"""
Latency Compensation System
Implements dynamic threshold adjustment based on data acquisition latency
"""
import asyncio
from typing import Dict, List, Optional
from collections import deque
from datetime import datetime, timedelta
import numpy as np
from loguru import logger
from config.logging_config import get_logger

logger = get_logger("risk.latency")

class LatencyCompensationManager:
    """
    Manages latency compensation with dynamic threshold adjustment
    Monitors system performance and adjusts trading thresholds accordingly
    """

    def __init__(self, base_thresholds: Dict[str, float]):
        """
        Initialize latency compensation manager

        Args:
            base_thresholds: Base threshold values for different components
        """
        self.base_thresholds = base_thresholds.copy()
        self.latency_history = {}  # component -> deque of latency measurements
        self.current_thresholds = base_thresholds.copy()
        self.latency_window = 100  # Keep last 100 measurements
        
        # Adjustment factors based on latency levels
        self.adjustment_factors = {
            'low': 1.0,      # < 50ms
            'medium': 1.2,   # 50-100ms
            'high': 1.5,     # 100-200ms
            'critical': 2.0  # > 200ms
        }

        # Latency thresholds in milliseconds
        self.latency_thresholds = {
            'low': 50,
            'medium': 100,
            'high': 200
        }

        # Performance tracking
        self.stats = {
            'total_measurements': 0,
            'avg_latency_by_component': {},
            'threshold_adjustments': 0,
            'bottlenecks_detected': []
        }

        # Component weights (how much each component affects overall adjustment)
        self.component_weights = {
            'data_acquisition': 1.0,
            'signal_processing': 0.8,
            'database_write': 0.6,
            'api_calls': 0.7,
            'network': 0.9
        }

        logger.info(f"LatencyCompensationManager initialized with base thresholds: {base_thresholds}")

    def record_latency(self, component: str, latency_ms: float):
        """
        Record latency measurement for a component

        Args:
            component: Component name (e.g., 'data_acquisition', 'signal_processing')
            latency_ms: Latency measurement in milliseconds
        """
        try:
            # Initialize history if needed
            if component not in self.latency_history:
                self.latency_history[component] = deque(maxlen=self.latency_window)

            # Add measurement with timestamp
            measurement = {
                'latency': latency_ms,
                'timestamp': datetime.utcnow()
            }
            
            self.latency_history[component].append(measurement)

            # Update stats
            self.stats['total_measurements'] += 1
            self._update_component_stats(component)

            # Check if thresholds need adjustment
            self._check_threshold_adjustment()

            logger.debug(f"Recorded latency for {component}: {latency_ms:.2f}ms")

        except Exception as e:
            logger.error(f"Error recording latency for {component}: {e}")

    def _update_component_stats(self, component: str):
        """Update average latency statistics for a component"""
        try:
            if component not in self.latency_history:
                return

            latencies = [m['latency'] for m in self.latency_history[component]]
            if latencies:
                self.stats['avg_latency_by_component'][component] = np.mean(latencies)

        except Exception as e:
            logger.error(f"Error updating stats for {component}: {e}")

    def get_current_threshold(self, threshold_type: str) -> float:
        """
        Get current threshold value adjusted for latency

        Args:
            threshold_type: Type of threshold (e.g., 'order_flow', 'liquidity')

        Returns:
            Adjusted threshold value
        """
        try:
            base_threshold = self.base_thresholds.get(threshold_type, 1.0)
            return self.current_thresholds.get(threshold_type, base_threshold)

        except Exception as e:
            logger.error(f"Error getting threshold for {threshold_type}: {e}")
            return self.base_thresholds.get(threshold_type, 1.0)

    def _calculate_latency_adjustment(self, component: str) -> float:
        """
        Calculate adjustment factor based on recent latency

        Args:
            component: Component name

        Returns:
            Adjustment factor (1.0 = no adjustment)
        """
        try:
            if component not in self.latency_history:
                return 1.0

            # Get recent latency measurements
            recent_measurements = list(self.latency_history[component])[-20:]  # Last 20 measurements
            if not recent_measurements:
                return 1.0

            # Calculate statistics
            latencies = [m['latency'] for m in recent_measurements]
            avg_latency = np.mean(latencies)
            p95_latency = np.percentile(latencies, 95)

            # Use P95 for adjustment to account for spikes
            effective_latency = p95_latency

            # Determine adjustment level
            if effective_latency >= self.latency_thresholds['high']:
                adjustment = self.adjustment_factors['critical']
            elif effective_latency >= self.latency_thresholds['medium']:
                adjustment = self.adjustment_factors['high']
            elif effective_latency >= self.latency_thresholds['low']:
                adjustment = self.adjustment_factors['medium']
            else:
                adjustment = self.adjustment_factors['low']

            # Apply trend analysis
            if len(latencies) >= 10:
                # Check if latency is trending upward
                recent_half = latencies[-5:]
                earlier_half = latencies[-10:-5]
                
                if np.mean(recent_half) > np.mean(earlier_half) * 1.2:  # 20% increase
                    adjustment *= 1.1  # Additional 10% adjustment for trend

            logger.debug(f"Latency adjustment for {component}: {adjustment:.3f} "
                        f"(avg: {avg_latency:.2f}ms, p95: {p95_latency:.2f}ms)")

            return adjustment

        except Exception as e:
            logger.error(f"Error calculating latency adjustment for {component}: {e}")
            return 1.0

    def _check_threshold_adjustment(self):
        """Check if thresholds need to be adjusted based on current latency"""
        try:
            # Calculate overall adjustment factor
            total_weighted_adjustment = 0.0
            total_weight = 0.0

            for component, weight in self.component_weights.items():
                if component in self.latency_history:
                    adjustment = self._calculate_latency_adjustment(component)
                    total_weighted_adjustment += adjustment * weight
                    total_weight += weight

            if total_weight == 0:
                return

            overall_adjustment = total_weighted_adjustment / total_weight

            # Only adjust if change is significant (> 5%)
            if abs(overall_adjustment - 1.0) > 0.05:
                self._apply_threshold_adjustments(overall_adjustment)

        except Exception as e:
            logger.error(f"Error checking threshold adjustment: {e}")

    def _apply_threshold_adjustments(self, adjustment_factor: float):
        """Apply adjustment factor to all thresholds"""
        try:
            old_thresholds = self.current_thresholds.copy()

            for threshold_type, base_value in self.base_thresholds.items():
                # Adjust threshold (higher latency = higher thresholds for more lenient filtering)
                adjusted_value = base_value * adjustment_factor
                self.current_thresholds[threshold_type] = adjusted_value

            self.stats['threshold_adjustments'] += 1

            logger.info(f"Applied threshold adjustment: factor={adjustment_factor:.3f}")
            logger.debug(f"Threshold changes: {old_thresholds} -> {self.current_thresholds}")

        except Exception as e:
            logger.error(f"Error applying threshold adjustments: {e}")

    def get_latency_stats(self, component: str) -> Dict:
        """
        Get latency statistics for a component

        Args:
            component: Component name

        Returns:
            Dictionary with latency statistics
        """
        try:
            if component not in self.latency_history:
                return {'error': f'No data for component {component}'}

            latencies = [m['latency'] for m in self.latency_history[component]]
            if not latencies:
                return {'error': f'No latency data for {component}'}

            stats = {
                'count': len(latencies),
                'avg': np.mean(latencies),
                'median': np.median(latencies),
                'p95': np.percentile(latencies, 95),
                'p99': np.percentile(latencies, 99),
                'min': np.min(latencies),
                'max': np.max(latencies),
                'std': np.std(latencies)
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting latency stats for {component}: {e}")
            return {'error': str(e)}

    def identify_bottlenecks(self, threshold_ms: float = 100) -> List[str]:
        """
        Identify performance bottlenecks

        Args:
            threshold_ms: Latency threshold for identifying bottlenecks

        Returns:
            List of component names that are bottlenecks
        """
        try:
            bottlenecks = []

            for component in self.latency_history:
                stats = self.get_latency_stats(component)
                if 'error' not in stats and stats['p95'] > threshold_ms:
                    bottlenecks.append(f"{component} (P95: {stats['p95']:.2f}ms)")

            # Update bottlenecks in stats
            self.stats['bottlenecks_detected'] = bottlenecks

            logger.debug(f"Identified {len(bottlenecks)} bottlenecks: {bottlenecks}")

            return bottlenecks

        except Exception as e:
            logger.error(f"Error identifying bottlenecks: {e}")
            return []

    def get_performance_report(self) -> Dict:
        """Get comprehensive performance report"""
        try:
            report = {
                'total_measurements': self.stats['total_measurements'],
                'threshold_adjustments': self.stats['threshold_adjustments'],
                'components': {},
                'bottlenecks': self.identify_bottlenecks(),
                'current_thresholds': self.current_thresholds.copy(),
                'base_thresholds': self.base_thresholds.copy()
            }

            # Add component-specific stats
            for component in self.latency_history:
                report['components'][component] = self.get_latency_stats(component)

            return report

        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {'error': str(e)}

    def reset_thresholds(self):
        """Reset thresholds to base values"""
        try:
            self.current_thresholds = self.base_thresholds.copy()
            logger.info("Reset thresholds to base values")

        except Exception as e:
            logger.error(f"Error resetting thresholds: {e}")

    def update_base_thresholds(self, new_thresholds: Dict[str, float]):
        """
        Update base threshold values

        Args:
            new_thresholds: Dictionary of new base threshold values
        """
        try:
            self.base_thresholds.update(new_thresholds)
            # Also update current thresholds if they haven't been adjusted
            for key, value in new_thresholds.items():
                if key not in self.current_thresholds or self.current_thresholds[key] == self.base_thresholds.get(key, value):
                    self.current_thresholds[key] = value

            logger.info(f"Updated base thresholds: {new_thresholds}")

        except Exception as e:
            logger.error(f"Error updating base thresholds: {e}")

    def clear_history(self, component: Optional[str] = None):
        """
        Clear latency history

        Args:
            component: Specific component to clear, or None for all
        """
        try:
            if component:
                self.latency_history.pop(component, None)
                self.stats['avg_latency_by_component'].pop(component, None)
                logger.info(f"Cleared latency history for {component}")
            else:
                self.latency_history.clear()
                self.stats['avg_latency_by_component'].clear()
                self.stats['total_measurements'] = 0
                self.stats['threshold_adjustments'] = 0
                self.stats['bottlenecks_detected'] = []
                logger.info("Cleared all latency history")

        except Exception as e:
            logger.error(f"Error clearing history: {e}")

    def __repr__(self):
        return (f"LatencyCompensationManager(components={len(self.latency_history)}, "
                f"measurements={self.stats['total_measurements']}, "
                f"adjustments={self.stats['threshold_adjustments']})")
