"""
Pre-Trade Slippage Analysis System
Implements slippage calculation based on CEX order book depth analysis
"""
import asyncio
from typing import Dict, List, Optional, Tuple
import numpy as np
from datetime import datetime
from loguru import logger
from config.logging_config import get_logger

logger = get_logger("risk.slippage")

class SlippageAnalyzer:
    """
    Analyzes expected slippage for trades based on order book depth
    Provides trade size optimization and signal filtering
    """

    def __init__(self):
        """Initialize slippage analyzer"""
        self.orderbook_depth_percentages = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
        self.max_slippage_threshold = 0.02  # 2% maximum acceptable slippage
        self.min_profit_after_slippage = 0.001  # 0.1% minimum profit after costs
        self.transaction_fee_rate = 0.001  # 0.1% transaction fee
        
        # Performance tracking
        self.analysis_history = []
        self.stats = {
            'total_analyses': 0,
            'signals_canceled': 0,
            'avg_slippage': 0.0
        }

        logger.info("SlippageAnalyzer initialized")

    def calculate_slippage(self, orderbook: Dict, trade_size: float, 
                         trade_side: str) -> Dict[str, float]:
        """
        Calculate expected slippage for different order sizes

        Args:
            orderbook: Order book data with 'bids' and 'asks'
            trade_size: Size of trade in quote currency (USD)
            trade_side: 'BUY' or 'SELL'

        Returns:
            Dictionary with slippage analysis results
        """
        try:
            if not orderbook or trade_size <= 0:
                return {'estimated_slippage': 0.0, 'error': 'Invalid input'}

            # Select appropriate side of order book
            if trade_side.upper() == 'BUY':
                orders = orderbook.get('asks', [])
                side_name = 'asks'
            else:
                orders = orderbook.get('bids', [])
                side_name = 'bids'

            if not orders:
                return {'estimated_slippage': 1.0, 'error': f'No {side_name} in order book'}

            # Calculate VWAP and slippage
            vwap_result = self._calculate_vwap(orders, trade_size, trade_side)
            
            if vwap_result['error']:
                return {
                    'estimated_slippage': 1.0,
                    'error': vwap_result['error'],
                    'available_liquidity': vwap_result.get('available_liquidity', 0)
                }

            # Calculate slippage percentage
            market_price = orders[0][0]  # Best bid/ask price
            execution_price = vwap_result['vwap']
            
            if trade_side.upper() == 'BUY':
                slippage = (execution_price - market_price) / market_price
            else:
                slippage = (market_price - execution_price) / market_price

            # Ensure slippage is non-negative
            slippage = max(0.0, slippage)

            # Add transaction fees
            total_cost = slippage + self.transaction_fee_rate

            result = {
                'estimated_slippage': slippage,
                'total_cost': total_cost,
                'execution_price': execution_price,
                'market_price': market_price,
                'filled_amount': vwap_result['filled_amount'],
                'available_liquidity': vwap_result['available_liquidity'],
                'partial_fill': vwap_result['partial_fill'],
                'error': None
            }

            # Update stats
            self.stats['total_analyses'] += 1
            self.stats['avg_slippage'] = (
                (self.stats['avg_slippage'] * (self.stats['total_analyses'] - 1) + slippage) /
                self.stats['total_analyses']
            )

            # Record analysis
            self.analysis_history.append({
                'timestamp': datetime.utcnow(),
                'trade_size': trade_size,
                'trade_side': trade_side,
                'slippage': slippage,
                'total_cost': total_cost
            })

            # Keep only recent history
            if len(self.analysis_history) > 1000:
                self.analysis_history = self.analysis_history[-1000:]

            logger.debug(f"Slippage analysis: {trade_side} ${trade_size:.2f} -> "
                        f"{slippage:.4f} slippage, {total_cost:.4f} total cost")

            return result

        except Exception as e:
            logger.error(f"Error calculating slippage: {e}")
            return {'estimated_slippage': 1.0, 'error': str(e)}

    def _calculate_vwap(self, orders: List[List], trade_size: float, 
                       trade_side: str) -> Dict:
        """
        Calculate Volume Weighted Average Price for given trade size

        Args:
            orders: List of [price, size] orders
            trade_size: Trade size in quote currency
            trade_side: 'BUY' or 'SELL'

        Returns:
            Dictionary with VWAP calculation results
        """
        try:
            total_cost = 0.0
            total_quantity = 0.0
            remaining_size = trade_size
            available_liquidity = 0.0

            for price, quantity in orders:
                if remaining_size <= 0:
                    break

                # Calculate available liquidity
                order_value = price * quantity
                available_liquidity += order_value

                # Calculate how much we can fill from this order
                if trade_side.upper() == 'BUY':
                    # For buy orders, trade_size is in quote currency
                    max_fillable_value = min(remaining_size, order_value)
                    fillable_quantity = max_fillable_value / price
                else:
                    # For sell orders, trade_size is in base currency
                    fillable_quantity = min(remaining_size, quantity)
                    max_fillable_value = fillable_quantity * price

                # Add to totals
                total_cost += max_fillable_value
                total_quantity += fillable_quantity
                remaining_size -= max_fillable_value if trade_side.upper() == 'BUY' else fillable_quantity

            if total_quantity == 0:
                return {
                    'vwap': 0.0,
                    'filled_amount': 0.0,
                    'available_liquidity': available_liquidity,
                    'partial_fill': True,
                    'error': 'Insufficient liquidity'
                }

            vwap = total_cost / total_quantity
            filled_amount = total_cost if trade_side.upper() == 'BUY' else total_quantity
            partial_fill = remaining_size > 0.001  # Small tolerance for rounding

            return {
                'vwap': vwap,
                'filled_amount': filled_amount,
                'available_liquidity': available_liquidity,
                'partial_fill': partial_fill,
                'error': None
            }

        except Exception as e:
            logger.error(f"Error calculating VWAP: {e}")
            return {
                'vwap': 0.0,
                'filled_amount': 0.0,
                'available_liquidity': 0.0,
                'partial_fill': True,
                'error': str(e)
            }

    def should_cancel_signal(self, estimated_slippage: float, 
                           predicted_profit: float) -> bool:
        """
        Determine if signal should be canceled due to high slippage

        Args:
            estimated_slippage: Expected slippage percentage
            predicted_profit: Expected profit percentage

        Returns:
            True if signal should be canceled, False otherwise
        """
        try:
            # Calculate total cost including fees
            total_cost = estimated_slippage + self.transaction_fee_rate

            # Check if slippage exceeds maximum threshold
            if estimated_slippage > self.max_slippage_threshold:
                self.stats['signals_canceled'] += 1
                logger.info(f"Signal canceled: slippage {estimated_slippage:.4f} > threshold {self.max_slippage_threshold:.4f}")
                return True

            # Check if profit after costs is sufficient
            net_profit = predicted_profit - total_cost
            if net_profit < self.min_profit_after_slippage:
                self.stats['signals_canceled'] += 1
                logger.info(f"Signal canceled: net profit {net_profit:.4f} < minimum {self.min_profit_after_slippage:.4f}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking signal cancellation: {e}")
            return True  # Cancel on error to be safe

    def get_optimal_trade_size(self, orderbook: Dict, max_slippage: float,
                             trade_side: str) -> float:
        """
        Calculate optimal trade size for given slippage tolerance

        Args:
            orderbook: Order book data
            max_slippage: Maximum acceptable slippage
            trade_side: 'BUY' or 'SELL'

        Returns:
            Optimal trade size in quote currency
        """
        try:
            if not orderbook or max_slippage <= 0:
                return 0.0

            # Select appropriate side of order book
            if trade_side.upper() == 'BUY':
                orders = orderbook.get('asks', [])
            else:
                orders = orderbook.get('bids', [])

            if not orders:
                return 0.0

            # Binary search for optimal size
            min_size = 100.0  # Minimum trade size
            max_size = self._estimate_max_liquidity(orders) * 0.5  # Start with 50% of available liquidity
            
            if max_size < min_size:
                return 0.0

            optimal_size = min_size
            tolerance = 0.001  # 0.1% tolerance

            for _ in range(20):  # Maximum 20 iterations
                mid_size = (min_size + max_size) / 2
                
                slippage_result = self.calculate_slippage(orderbook, mid_size, trade_side)
                estimated_slippage = slippage_result.get('estimated_slippage', 1.0)

                if slippage_result.get('error'):
                    max_size = mid_size
                    continue

                if estimated_slippage <= max_slippage + tolerance:
                    optimal_size = mid_size
                    min_size = mid_size
                else:
                    max_size = mid_size

                # Check convergence
                if (max_size - min_size) / max_size < 0.01:  # 1% convergence
                    break

            logger.debug(f"Optimal trade size for {max_slippage:.2%} slippage: ${optimal_size:.2f}")

            return optimal_size

        except Exception as e:
            logger.error(f"Error calculating optimal trade size: {e}")
            return 0.0

    def _estimate_max_liquidity(self, orders: List[List]) -> float:
        """Estimate maximum available liquidity in quote currency"""
        try:
            total_liquidity = 0.0
            for price, quantity in orders[:20]:  # Consider top 20 orders
                total_liquidity += price * quantity
            return total_liquidity
        except Exception:
            return 0.0

    def analyze_market_impact(self, orderbook: Dict, trade_sizes: List[float],
                            trade_side: str) -> Dict[float, Dict]:
        """
        Analyze market impact for different trade sizes

        Args:
            orderbook: Order book data
            trade_sizes: List of trade sizes to analyze
            trade_side: 'BUY' or 'SELL'

        Returns:
            Dictionary mapping trade sizes to slippage analysis
        """
        try:
            impact_analysis = {}

            for size in trade_sizes:
                result = self.calculate_slippage(orderbook, size, trade_side)
                impact_analysis[size] = result

            logger.debug(f"Market impact analysis completed for {len(trade_sizes)} sizes")

            return impact_analysis

        except Exception as e:
            logger.error(f"Error analyzing market impact: {e}")
            return {}

    def get_slippage_stats(self) -> Dict:
        """Get slippage analysis statistics"""
        return {
            'total_analyses': self.stats['total_analyses'],
            'signals_canceled': self.stats['signals_canceled'],
            'cancellation_rate': (
                self.stats['signals_canceled'] / max(1, self.stats['total_analyses'])
            ),
            'avg_slippage': self.stats['avg_slippage'],
            'max_slippage_threshold': self.max_slippage_threshold,
            'min_profit_threshold': self.min_profit_after_slippage,
            'transaction_fee_rate': self.transaction_fee_rate
        }

    def get_recent_analyses(self, limit: int = 10) -> List[Dict]:
        """Get recent slippage analyses"""
        return self.analysis_history[-limit:] if self.analysis_history else []

    def update_parameters(self, **kwargs):
        """
        Update analyzer parameters

        Args:
            max_slippage_threshold: New maximum slippage threshold
            min_profit_after_slippage: New minimum profit threshold
            transaction_fee_rate: New transaction fee rate
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"Updated {key} to {value}")

    def clear_history(self):
        """Clear analysis history"""
        self.analysis_history.clear()
        logger.info("Cleared slippage analysis history")

    def __repr__(self):
        stats = self.get_slippage_stats()
        return (f"SlippageAnalyzer(analyses={stats['total_analyses']}, "
                f"canceled={stats['signals_canceled']}, "
                f"avg_slippage={stats['avg_slippage']:.4f})")
