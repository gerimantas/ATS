"""
Paper Trading System
Implements paper trading mode for safe testing and signal validation without real money
"""
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import uuid
import numpy as np
from config.logging_config import get_logger

logger = get_logger("trading.paper_trading")

class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

@dataclass
class PaperOrder:
    id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    amount: float
    price: float
    order_type: str  # 'MARKET' or 'LIMIT'
    status: OrderStatus
    created_at: datetime
    filled_at: Optional[datetime] = None
    fill_price: Optional[float] = None
    fill_amount: Optional[float] = None

class PaperTradingEngine:
    """
    Paper trading engine for safe testing without real money
    Simulates realistic order execution with slippage and market conditions
    """

    def __init__(self, initial_balance: float = 10000.0):
        """
        Initialize paper trading engine

        Args:
            initial_balance: Starting balance in USD
        """
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.positions = {}  # symbol -> position_size (positive = long, negative = short)
        self.position_costs = {}  # symbol -> average_cost_basis
        self.orders = {}  # order_id -> PaperOrder
        self.trade_history = []
        self.performance_metrics = {}
        self.market_prices = {}  # symbol -> current_price
        
        # Trading parameters
        self.default_slippage = 0.001  # 0.1% default slippage
        self.transaction_fee = 0.001  # 0.1% transaction fee
        self.max_position_size = 0.1  # 10% of portfolio per position
        
        # Performance tracking
        self.daily_pnl = []
        self.equity_curve = [initial_balance]
        self.max_equity = initial_balance
        self.max_drawdown = 0.0
        
        logger.info(f"PaperTradingEngine initialized with ${initial_balance:,.2f}")

    def execute_signal(self, signal: Dict) -> Dict:
        """
        Execute trading signal in paper mode

        Args:
            signal: Signal dictionary with required fields

        Returns:
            Dictionary with execution result
        """
        try:
            # Validate signal
            required_fields = ['pair_symbol', 'signal_type', 'current_price']
            if not all(field in signal for field in required_fields):
                return {'status': 'rejected', 'reason': 'Missing required fields'}

            symbol = signal['pair_symbol']
            signal_type = signal['signal_type'].upper()
            current_price = signal['current_price']
            
            # Update market price
            self.market_prices[symbol] = current_price
            
            # Determine order details
            if signal_type == 'BUY':
                side = 'BUY'
                # Calculate position size based on predicted reward and confidence
                predicted_reward = signal.get('predicted_reward', 0.02)
                confidence = signal.get('confidence', 0.5)
                position_value = self._calculate_position_size(predicted_reward, confidence)
                amount = position_value / current_price
                
            elif signal_type == 'SELL':
                side = 'SELL'
                # Sell existing position or skip if no position
                if symbol not in self.positions or self.positions[symbol] <= 0:
                    return {'status': 'rejected', 'reason': 'No position to sell'}
                amount = abs(self.positions[symbol])
                
            else:
                return {'status': 'rejected', 'reason': f'Invalid signal type: {signal_type}'}

            # Create and execute order
            order = self._create_order(symbol, side, amount, current_price, 'MARKET')
            execution_result = self._execute_order(order)
            
            if execution_result['status'] == 'filled':
                # Record trade
                self._record_trade(order, signal)
                
                # Update performance metrics
                self._update_performance_metrics()
                
                logger.info(f"Executed {side} order for {symbol}: {amount:.6f} @ ${order.fill_price:.2f}")
                
                return {
                    'status': 'executed',
                    'order_id': order.id,
                    'symbol': symbol,
                    'side': side,
                    'amount': order.fill_amount,
                    'price': order.fill_price,
                    'timestamp': order.filled_at
                }
            else:
                return execution_result

        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return {'status': 'error', 'reason': str(e)}

    def _create_order(self, symbol: str, side: str, amount: float, 
                     price: float, order_type: str) -> PaperOrder:
        """Create a new paper order"""
        order_id = str(uuid.uuid4())[:8]
        
        order = PaperOrder(
            id=order_id,
            symbol=symbol,
            side=side,
            amount=amount,
            price=price,
            order_type=order_type,
            status=OrderStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        self.orders[order_id] = order
        return order

    def _execute_order(self, order: PaperOrder) -> Dict:
        """Execute a paper order with realistic simulation"""
        try:
            # Check if we have enough balance/position
            if order.side == 'BUY':
                required_balance = order.amount * order.price * (1 + self.transaction_fee)
                if required_balance > self.current_balance:
                    order.status = OrderStatus.REJECTED
                    return {'status': 'rejected', 'reason': 'Insufficient balance'}
            
            elif order.side == 'SELL':
                if order.symbol not in self.positions or self.positions[order.symbol] < order.amount:
                    order.status = OrderStatus.REJECTED
                    return {'status': 'rejected', 'reason': 'Insufficient position'}

            # Simulate market order execution with slippage
            if order.order_type == 'MARKET':
                # Apply slippage
                slippage_factor = np.random.normal(0, self.default_slippage)
                if order.side == 'BUY':
                    fill_price = order.price * (1 + abs(slippage_factor))
                else:
                    fill_price = order.price * (1 - abs(slippage_factor))
                
                # Execute immediately
                order.fill_price = fill_price
                order.fill_amount = order.amount
                order.filled_at = datetime.utcnow()
                order.status = OrderStatus.FILLED
                
                # Update positions and balance
                self._update_portfolio(order)
                
                return {'status': 'filled', 'fill_price': fill_price, 'fill_amount': order.amount}
            
            else:  # LIMIT order
                # For now, assume limit orders fill immediately if price is favorable
                # In a real implementation, this would check market conditions
                order.fill_price = order.price
                order.fill_amount = order.amount
                order.filled_at = datetime.utcnow()
                order.status = OrderStatus.FILLED
                
                self._update_portfolio(order)
                
                return {'status': 'filled', 'fill_price': order.price, 'fill_amount': order.amount}

        except Exception as e:
            logger.error(f"Error executing order {order.id}: {e}")
            order.status = OrderStatus.REJECTED
            return {'status': 'error', 'reason': str(e)}

    def _update_portfolio(self, order: PaperOrder):
        """Update portfolio positions and balance after order execution"""
        symbol = order.symbol
        
        if order.side == 'BUY':
            # Add to position
            cost = order.fill_amount * order.fill_price * (1 + self.transaction_fee)
            
            if symbol in self.positions:
                # Update average cost basis
                old_position = self.positions[symbol]
                old_cost = self.position_costs.get(symbol, 0) * old_position
                new_position = old_position + order.fill_amount
                new_cost = (old_cost + cost) / new_position if new_position > 0 else 0
                
                self.positions[symbol] = new_position
                self.position_costs[symbol] = new_cost
            else:
                self.positions[symbol] = order.fill_amount
                self.position_costs[symbol] = order.fill_price * (1 + self.transaction_fee)
            
            self.current_balance -= cost
            
        elif order.side == 'SELL':
            # Remove from position
            proceeds = order.fill_amount * order.fill_price * (1 - self.transaction_fee)
            
            if symbol in self.positions:
                self.positions[symbol] -= order.fill_amount
                if abs(self.positions[symbol]) < 1e-8:  # Close to zero
                    del self.positions[symbol]
                    if symbol in self.position_costs:
                        del self.position_costs[symbol]
            
            self.current_balance += proceeds

    def _calculate_position_size(self, predicted_reward: float, confidence: float) -> float:
        """Calculate position size based on Kelly criterion and risk management"""
        try:
            # Simple position sizing: base on confidence and predicted reward
            # Kelly fraction = (bp - q) / b, where b = odds, p = win prob, q = loss prob
            
            # Assume win probability based on confidence
            win_prob = confidence
            loss_prob = 1 - confidence
            
            # Assume average loss is half the predicted reward
            avg_win = predicted_reward
            avg_loss = predicted_reward * 0.5
            
            # Kelly fraction
            if avg_loss > 0:
                kelly_fraction = (win_prob * avg_win - loss_prob * avg_loss) / avg_win
            else:
                kelly_fraction = 0.1  # Default to 10%
            
            # Apply conservative scaling (25% of Kelly)
            kelly_fraction *= 0.25
            
            # Apply maximum position size limit
            kelly_fraction = min(kelly_fraction, self.max_position_size)
            kelly_fraction = max(kelly_fraction, 0.01)  # Minimum 1%
            
            # Calculate position value
            total_portfolio_value = self._calculate_total_portfolio_value()
            position_value = total_portfolio_value * kelly_fraction
            
            return position_value

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return self.current_balance * 0.05  # Default to 5%

    def _calculate_total_portfolio_value(self) -> float:
        """Calculate total portfolio value including positions"""
        total_value = self.current_balance
        
        for symbol, position_size in self.positions.items():
            if symbol in self.market_prices:
                position_value = position_size * self.market_prices[symbol]
                total_value += position_value
        
        return total_value

    def calculate_pnl(self) -> Dict:
        """Calculate current profit and loss"""
        try:
            total_value = self._calculate_total_portfolio_value()
            
            # Calculate unrealized P&L
            unrealized_pnl = 0.0
            for symbol, position_size in self.positions.items():
                if symbol in self.market_prices and symbol in self.position_costs:
                    current_price = self.market_prices[symbol]
                    cost_basis = self.position_costs[symbol]
                    position_pnl = position_size * (current_price - cost_basis)
                    unrealized_pnl += position_pnl

            # Calculate realized P&L from trade history
            realized_pnl = sum(trade.get('pnl', 0) for trade in self.trade_history)
            
            # Calculate total return
            total_pnl = realized_pnl + unrealized_pnl
            total_return_pct = total_pnl / self.initial_balance if self.initial_balance > 0 else 0
            
            return {
                'total_value': total_value,
                'unrealized_pnl': unrealized_pnl,
                'realized_pnl': realized_pnl,
                'total_pnl': total_pnl,
                'total_return_pct': total_return_pct,
                'current_balance': self.current_balance,
                'positions_value': total_value - self.current_balance
            }

        except Exception as e:
            logger.error(f"Error calculating P&L: {e}")
            return {'error': str(e)}

    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        try:
            pnl = self.calculate_pnl()
            
            # Position details
            position_details = {}
            for symbol, position_size in self.positions.items():
                if symbol in self.market_prices and symbol in self.position_costs:
                    current_price = self.market_prices[symbol]
                    cost_basis = self.position_costs[symbol]
                    position_value = position_size * current_price
                    position_pnl = position_size * (current_price - cost_basis)
                    position_pnl_pct = (current_price - cost_basis) / cost_basis if cost_basis > 0 else 0
                    
                    position_details[symbol] = {
                        'size': position_size,
                        'current_price': current_price,
                        'cost_basis': cost_basis,
                        'market_value': position_value,
                        'pnl': position_pnl,
                        'pnl_pct': position_pnl_pct
                    }

            return {
                'total_value': pnl.get('total_value', 0),
                'cash_balance': self.current_balance,
                'positions': position_details,
                'pnl': pnl,
                'performance_metrics': self.get_performance_metrics(),
                'total_trades': len(self.trade_history),
                'active_positions': len(self.positions)
            }

        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {'error': str(e)}

    def _record_trade(self, order: PaperOrder, signal: Dict):
        """Record executed trade with metadata"""
        try:
            # Calculate P&L for sell orders
            pnl = 0.0
            if order.side == 'SELL' and order.symbol in self.position_costs:
                cost_basis = self.position_costs[order.symbol]
                pnl = order.fill_amount * (order.fill_price - cost_basis)

            trade_record = {
                'trade_id': order.id,
                'symbol': order.symbol,
                'side': order.side,
                'amount': order.fill_amount,
                'price': order.fill_price,
                'timestamp': order.filled_at,
                'pnl': pnl,
                'signal_type': signal.get('signal_type'),
                'predicted_reward': signal.get('predicted_reward'),
                'confidence': signal.get('confidence'),
                'algorithms': signal.get('algorithms', [])
            }
            
            self.trade_history.append(trade_record)
            
        except Exception as e:
            logger.error(f"Error recording trade: {e}")

    def _update_performance_metrics(self):
        """Update performance metrics after each trade"""
        try:
            current_value = self._calculate_total_portfolio_value()
            self.equity_curve.append(current_value)
            
            # Update max equity and drawdown
            if current_value > self.max_equity:
                self.max_equity = current_value
            
            current_drawdown = (self.max_equity - current_value) / self.max_equity
            if current_drawdown > self.max_drawdown:
                self.max_drawdown = current_drawdown
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")

    def get_performance_metrics(self) -> Dict:
        """Calculate comprehensive performance metrics"""
        try:
            if len(self.trade_history) == 0:
                return {
                    'total_trades': 0,
                    'win_rate': 0.0,
                    'avg_return': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'profit_factor': 0.0
                }

            # Calculate basic metrics
            total_trades = len(self.trade_history)
            winning_trades = [t for t in self.trade_history if t.get('pnl', 0) > 0]
            losing_trades = [t for t in self.trade_history if t.get('pnl', 0) < 0]
            
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            
            # Calculate returns
            total_pnl = sum(t.get('pnl', 0) for t in self.trade_history)
            avg_return = total_pnl / self.initial_balance if self.initial_balance > 0 else 0
            
            # Calculate Sharpe ratio (simplified)
            if len(self.equity_curve) > 1:
                returns = np.diff(self.equity_curve) / self.equity_curve[:-1]
                if np.std(returns) > 0:
                    sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)  # Annualized
                else:
                    sharpe_ratio = 0.0
            else:
                sharpe_ratio = 0.0
            
            # Calculate profit factor
            gross_profit = sum(t.get('pnl', 0) for t in winning_trades)
            gross_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            return {
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'avg_return': avg_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': self.max_drawdown,
                'profit_factor': profit_factor,
                'gross_profit': gross_profit,
                'gross_loss': gross_loss,
                'current_equity': self._calculate_total_portfolio_value()
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {'error': str(e)}

    def _update_market_price(self, symbol: str, price: float):
        """Update market price for a symbol (for testing)"""
        self.market_prices[symbol] = price

    def reset_portfolio(self):
        """Reset portfolio to initial state"""
        self.current_balance = self.initial_balance
        self.positions.clear()
        self.position_costs.clear()
        self.orders.clear()
        self.trade_history.clear()
        self.market_prices.clear()
        self.equity_curve = [self.initial_balance]
        self.max_equity = self.initial_balance
        self.max_drawdown = 0.0
        
        logger.info("Portfolio reset to initial state")

    def get_trade_history(self, limit: int = None) -> List[Dict]:
        """Get trade history with optional limit"""
        if limit:
            return self.trade_history[-limit:]
        return self.trade_history.copy()

    def get_open_orders(self) -> List[PaperOrder]:
        """Get list of open (pending) orders"""
        return [order for order in self.orders.values() if order.status == OrderStatus.PENDING]

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order"""
        try:
            if order_id in self.orders:
                order = self.orders[order_id]
                if order.status == OrderStatus.PENDING:
                    order.status = OrderStatus.CANCELLED
                    logger.info(f"Cancelled order {order_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    def __repr__(self):
        pnl = self.calculate_pnl()
        return (f"PaperTradingEngine(balance=${self.current_balance:.2f}, "
                f"positions={len(self.positions)}, "
                f"total_value=${pnl.get('total_value', 0):.2f}, "
                f"pnl={pnl.get('total_return_pct', 0):.2%})")
