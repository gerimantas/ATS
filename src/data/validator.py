"""
Data Validation Module
Comprehensive data validation system for DEX/CEX data quality checks
"""
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
from loguru import logger
from config.logging_config import get_logger

logger = get_logger("data.validator")

class ValidationSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    field: str
    severity: ValidationSeverity
    message: str
    value: Any
    timestamp: datetime

class DataValidator:
    """
    Comprehensive data validation system for market data quality checks
    """

    def __init__(self):
        """Initialize data validator with default thresholds"""
        self.validation_rules = {}
        self.anomaly_thresholds = {
            'price_change_1min': 0.05,  # 5% max price change per minute
            'volume_spike': 10.0,       # 10x volume spike threshold
            'spread_threshold': 0.02,   # 2% max bid-ask spread
            'stale_data_seconds': 30    # Data older than 30s is stale
        }
        self.data_quality_scores = {}
        self.validation_history = []
        self.symbol_stats = {}  # Track statistics per symbol
        
        logger.info("DataValidator initialized with default thresholds")

    def validate_orderbook(self, orderbook: Dict) -> List[ValidationResult]:
        """
        Validate orderbook data structure and values

        Args:
            orderbook: Orderbook dictionary with bids, asks, timestamp, symbol

        Returns:
            List of validation results
        """
        results = []
        timestamp = datetime.utcnow()

        try:
            # Structure validation
            required_fields = ['bids', 'asks', 'timestamp', 'symbol']
            for field in required_fields:
                if field not in orderbook:
                    results.append(ValidationResult(
                        field=field,
                        severity=ValidationSeverity.CRITICAL,
                        message=f"Missing required field: {field}",
                        value=None,
                        timestamp=timestamp
                    ))

            if not results:  # Only continue if structure is valid
                symbol = orderbook['symbol']
                bids = orderbook['bids']
                asks = orderbook['asks']
                data_timestamp = orderbook['timestamp']

                # Validate bids and asks structure
                if not isinstance(bids, list) or not isinstance(asks, list):
                    results.append(ValidationResult(
                        field='structure',
                        severity=ValidationSeverity.CRITICAL,
                        message="Bids and asks must be lists",
                        value={'bids_type': type(bids), 'asks_type': type(asks)},
                        timestamp=timestamp
                    ))
                    return results

                # Validate bid/ask entries
                for i, bid in enumerate(bids[:5]):  # Check top 5 levels
                    if not isinstance(bid, list) or len(bid) != 2:
                        results.append(ValidationResult(
                            field=f'bids[{i}]',
                            severity=ValidationSeverity.ERROR,
                            message=f"Invalid bid format at level {i}",
                            value=bid,
                            timestamp=timestamp
                        ))
                    else:
                        price, volume = bid
                        if price <= 0:
                            results.append(ValidationResult(
                                field=f'bids[{i}].price',
                                severity=ValidationSeverity.ERROR,
                                message=f"Invalid bid price: {price}",
                                value=price,
                                timestamp=timestamp
                            ))
                        if volume < 0:
                            results.append(ValidationResult(
                                field=f'bids[{i}].volume',
                                severity=ValidationSeverity.ERROR,
                                message=f"Negative volume in bid: {volume}",
                                value=volume,
                                timestamp=timestamp
                            ))

                for i, ask in enumerate(asks[:5]):  # Check top 5 levels
                    if not isinstance(ask, list) or len(ask) != 2:
                        results.append(ValidationResult(
                            field=f'asks[{i}]',
                            severity=ValidationSeverity.ERROR,
                            message=f"Invalid ask format at level {i}",
                            value=ask,
                            timestamp=timestamp
                        ))
                    else:
                        price, volume = ask
                        if price <= 0:
                            results.append(ValidationResult(
                                field=f'asks[{i}].price',
                                severity=ValidationSeverity.ERROR,
                                message=f"Invalid ask price: {price}",
                                value=price,
                                timestamp=timestamp
                            ))
                        if volume < 0:
                            results.append(ValidationResult(
                                field=f'asks[{i}].volume',
                                severity=ValidationSeverity.ERROR,
                                message=f"Negative volume in ask: {volume}",
                                value=volume,
                                timestamp=timestamp
                            ))

                # Check for crossed spread
                if bids and asks:
                    best_bid = max(bid[0] for bid in bids if len(bid) >= 2)
                    best_ask = min(ask[0] for ask in asks if len(ask) >= 2)
                    
                    if best_bid >= best_ask:
                        results.append(ValidationResult(
                            field='spread',
                            severity=ValidationSeverity.ERROR,
                            message=f"Crossed spread detected: bid={best_bid}, ask={best_ask}",
                            value={'bid': best_bid, 'ask': best_ask},
                            timestamp=timestamp
                        ))
                    else:
                        # Check spread width
                        spread_pct = (best_ask - best_bid) / best_bid
                        if spread_pct > self.anomaly_thresholds['spread_threshold']:
                            results.append(ValidationResult(
                                field='spread',
                                severity=ValidationSeverity.WARNING,
                                message=f"Wide spread detected: {spread_pct:.4f}",
                                value=spread_pct,
                                timestamp=timestamp
                            ))

                # Check data freshness
                if isinstance(data_timestamp, datetime):
                    age_seconds = (timestamp - data_timestamp).total_seconds()
                    if age_seconds > self.anomaly_thresholds['stale_data_seconds']:
                        results.append(ValidationResult(
                            field='timestamp',
                            severity=ValidationSeverity.WARNING,
                            message=f"Stale data: {age_seconds:.1f}s old",
                            value=age_seconds,
                            timestamp=timestamp
                        ))

        except Exception as e:
            results.append(ValidationResult(
                field='validation',
                severity=ValidationSeverity.CRITICAL,
                message=f"Validation error: {str(e)}",
                value=str(e),
                timestamp=timestamp
            ))

        return results

    def validate_trade_data(self, trade: Dict) -> List[ValidationResult]:
        """
        Validate individual trade data

        Args:
            trade: Trade dictionary with required fields

        Returns:
            List of validation results
        """
        results = []
        timestamp = datetime.utcnow()

        try:
            # Required fields validation
            required_fields = ['symbol', 'side', 'amount', 'price', 'timestamp']
            for field in required_fields:
                if field not in trade or trade[field] is None:
                    results.append(ValidationResult(
                        field=field,
                        severity=ValidationSeverity.ERROR,
                        message=f"Missing or null required field: {field}",
                        value=trade.get(field),
                        timestamp=timestamp
                    ))

            if not results:  # Continue only if required fields exist
                # Validate symbol
                symbol = trade['symbol']
                if not isinstance(symbol, str) or len(symbol.strip()) == 0:
                    results.append(ValidationResult(
                        field='symbol',
                        severity=ValidationSeverity.ERROR,
                        message="Invalid symbol format",
                        value=symbol,
                        timestamp=timestamp
                    ))

                # Validate side
                side = trade['side']
                if side.lower() not in ['buy', 'sell', 'bid', 'ask']:
                    results.append(ValidationResult(
                        field='side',
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid trade side: {side}",
                        value=side,
                        timestamp=timestamp
                    ))

                # Validate amount
                amount = trade['amount']
                if not isinstance(amount, (int, float)) or amount <= 0:
                    results.append(ValidationResult(
                        field='amount',
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid trade amount: {amount}",
                        value=amount,
                        timestamp=timestamp
                    ))

                # Validate price
                price = trade['price']
                if not isinstance(price, (int, float)) or price <= 0:
                    results.append(ValidationResult(
                        field='price',
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid trade price: {price}",
                        value=price,
                        timestamp=timestamp
                    ))

                # Validate timestamp
                trade_timestamp = trade['timestamp']
                if isinstance(trade_timestamp, datetime):
                    age_seconds = (timestamp - trade_timestamp).total_seconds()
                    if age_seconds > self.anomaly_thresholds['stale_data_seconds']:
                        results.append(ValidationResult(
                            field='timestamp',
                            severity=ValidationSeverity.WARNING,
                            message=f"Old trade data: {age_seconds:.1f}s",
                            value=age_seconds,
                            timestamp=timestamp
                        ))
                elif trade_timestamp is not None:
                    results.append(ValidationResult(
                        field='timestamp',
                        severity=ValidationSeverity.WARNING,
                        message="Invalid timestamp format",
                        value=trade_timestamp,
                        timestamp=timestamp
                    ))

        except Exception as e:
            results.append(ValidationResult(
                field='validation',
                severity=ValidationSeverity.CRITICAL,
                message=f"Trade validation error: {str(e)}",
                value=str(e),
                timestamp=timestamp
            ))

        return results

    def detect_price_anomalies(self, symbol: str, price: float, 
                             historical_prices: List[float]) -> List[ValidationResult]:
        """
        Detect unusual price movements

        Args:
            symbol: Trading symbol
            price: Current price
            historical_prices: List of recent historical prices

        Returns:
            List of validation results for anomalies
        """
        results = []
        timestamp = datetime.utcnow()

        try:
            if not historical_prices or len(historical_prices) < 2:
                return results

            # Calculate price change from most recent price
            last_price = historical_prices[-1]
            if last_price > 0:
                price_change = abs(price - last_price) / last_price
                
                if price_change > self.anomaly_thresholds['price_change_1min']:
                    severity = ValidationSeverity.ERROR if price_change > 0.1 else ValidationSeverity.WARNING
                    results.append(ValidationResult(
                        field='price_change',
                        severity=severity,
                        message=f"Large price movement: {price_change:.4f} ({price_change*100:.2f}%)",
                        value=price_change,
                        timestamp=timestamp
                    ))

            # Statistical outlier detection
            if len(historical_prices) >= 10:
                prices_array = np.array(historical_prices)
                mean_price = np.mean(prices_array)
                std_price = np.std(prices_array)
                
                if std_price > 0:
                    z_score = abs(price - mean_price) / std_price
                    
                    if z_score > 3:  # 3 standard deviations
                        results.append(ValidationResult(
                            field='price_outlier',
                            severity=ValidationSeverity.WARNING,
                            message=f"Price outlier detected: z-score={z_score:.2f}",
                            value=z_score,
                            timestamp=timestamp
                        ))

            # Volatility spike detection
            if len(historical_prices) >= 5:
                recent_prices = historical_prices[-5:]
                returns = np.diff(recent_prices) / recent_prices[:-1]
                volatility = np.std(returns)
                
                # Compare to historical volatility if available
                if symbol in self.symbol_stats and 'avg_volatility' in self.symbol_stats[symbol]:
                    avg_vol = self.symbol_stats[symbol]['avg_volatility']
                    if volatility > avg_vol * 3:  # 3x normal volatility
                        results.append(ValidationResult(
                            field='volatility_spike',
                            severity=ValidationSeverity.WARNING,
                            message=f"Volatility spike: {volatility:.4f} vs avg {avg_vol:.4f}",
                            value=volatility,
                            timestamp=timestamp
                        ))

        except Exception as e:
            results.append(ValidationResult(
                field='anomaly_detection',
                severity=ValidationSeverity.ERROR,
                message=f"Anomaly detection error: {str(e)}",
                value=str(e),
                timestamp=timestamp
            ))

        return results

    def calculate_data_quality_score(self, symbol: str) -> float:
        """
        Calculate overall data quality score (0-1)

        Args:
            symbol: Trading symbol

        Returns:
            Quality score between 0 and 1
        """
        try:
            if symbol not in self.data_quality_scores:
                return 0.5  # Default neutral score

            scores = self.data_quality_scores[symbol]
            
            # Weight recent scores more heavily
            if len(scores) == 0:
                return 0.5

            # Calculate weighted average with exponential decay
            weights = np.exp(-np.arange(len(scores)) * 0.1)  # Decay factor
            weighted_score = np.average(scores, weights=weights[::-1])  # Reverse for recent first
            
            return max(0.0, min(1.0, weighted_score))

        except Exception as e:
            logger.error(f"Error calculating quality score for {symbol}: {e}")
            return 0.0

    def _record_data_quality(self, symbol: str, data: Dict):
        """Record data quality metrics for a symbol"""
        try:
            # Calculate quality score based on validation results
            quality_issues = data.get('quality_issues', [])
            
            # Base score starts at 1.0
            score = 1.0
            
            # Deduct points for each issue type
            for issue in quality_issues:
                if 'missing' in issue.lower() or 'null' in issue.lower():
                    score -= 0.3
                elif 'invalid' in issue.lower():
                    score -= 0.2
                elif 'stale' in issue.lower():
                    score -= 0.1
                elif 'anomaly' in issue.lower():
                    score -= 0.15

            score = max(0.0, score)

            # Store score
            if symbol not in self.data_quality_scores:
                self.data_quality_scores[symbol] = []
            
            self.data_quality_scores[symbol].append(score)
            
            # Keep only recent scores (last 100)
            if len(self.data_quality_scores[symbol]) > 100:
                self.data_quality_scores[symbol] = self.data_quality_scores[symbol][-100:]

        except Exception as e:
            logger.error(f"Error recording data quality for {symbol}: {e}")

    def update_symbol_statistics(self, symbol: str, price: float, volume: float = None):
        """Update statistical tracking for a symbol"""
        try:
            if symbol not in self.symbol_stats:
                self.symbol_stats[symbol] = {
                    'prices': [],
                    'volumes': [],
                    'avg_volatility': 0.0,
                    'last_updated': datetime.utcnow()
                }

            stats = self.symbol_stats[symbol]
            stats['prices'].append(price)
            if volume is not None:
                stats['volumes'].append(volume)
            
            # Keep only recent data (last 100 points)
            if len(stats['prices']) > 100:
                stats['prices'] = stats['prices'][-100:]
            if len(stats['volumes']) > 100:
                stats['volumes'] = stats['volumes'][-100:]

            # Update volatility
            if len(stats['prices']) >= 10:
                prices = np.array(stats['prices'])
                returns = np.diff(prices) / prices[:-1]
                stats['avg_volatility'] = np.std(returns)

            stats['last_updated'] = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error updating statistics for {symbol}: {e}")

    def get_validation_summary(self, hours: int = 24) -> Dict:
        """Get validation summary for the last N hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_validations = [
                v for v in self.validation_history 
                if v.timestamp >= cutoff_time
            ]

            # Count by severity
            severity_counts = {
                ValidationSeverity.INFO: 0,
                ValidationSeverity.WARNING: 0,
                ValidationSeverity.ERROR: 0,
                ValidationSeverity.CRITICAL: 0
            }

            for validation in recent_validations:
                severity_counts[validation.severity] += 1

            # Calculate overall health score
            total_issues = len(recent_validations)
            if total_issues == 0:
                health_score = 1.0
            else:
                # Weight different severities
                weighted_issues = (
                    severity_counts[ValidationSeverity.CRITICAL] * 4 +
                    severity_counts[ValidationSeverity.ERROR] * 2 +
                    severity_counts[ValidationSeverity.WARNING] * 1 +
                    severity_counts[ValidationSeverity.INFO] * 0.1
                )
                health_score = max(0.0, 1.0 - (weighted_issues / (total_issues * 4)))

            return {
                'period_hours': hours,
                'total_validations': total_issues,
                'severity_breakdown': {
                    'critical': severity_counts[ValidationSeverity.CRITICAL],
                    'error': severity_counts[ValidationSeverity.ERROR],
                    'warning': severity_counts[ValidationSeverity.WARNING],
                    'info': severity_counts[ValidationSeverity.INFO]
                },
                'health_score': health_score,
                'symbols_tracked': len(self.data_quality_scores),
                'avg_quality_score': np.mean([
                    self.calculate_data_quality_score(symbol) 
                    for symbol in self.data_quality_scores.keys()
                ]) if self.data_quality_scores else 0.0
            }

        except Exception as e:
            logger.error(f"Error generating validation summary: {e}")
            return {'error': str(e)}

    def set_threshold(self, threshold_name: str, value: float):
        """Update anomaly detection threshold"""
        if threshold_name in self.anomaly_thresholds:
            old_value = self.anomaly_thresholds[threshold_name]
            self.anomaly_thresholds[threshold_name] = value
            logger.info(f"Updated threshold {threshold_name}: {old_value} -> {value}")
        else:
            logger.warning(f"Unknown threshold: {threshold_name}")

    def get_thresholds(self) -> Dict:
        """Get current anomaly detection thresholds"""
        return self.anomaly_thresholds.copy()

    def clear_history(self, older_than_hours: int = 24):
        """Clear old validation history"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            initial_count = len(self.validation_history)
            
            self.validation_history = [
                v for v in self.validation_history 
                if v.timestamp >= cutoff_time
            ]
            
            cleared_count = initial_count - len(self.validation_history)
            if cleared_count > 0:
                logger.info(f"Cleared {cleared_count} old validation records")

        except Exception as e:
            logger.error(f"Error clearing validation history: {e}")
