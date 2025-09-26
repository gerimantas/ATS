"""
Test Paper Trading System
Tests for the paper trading engine and virtual order execution
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import asyncio
import time
from datetime import datetime, timedelta
import numpy as np
from config.logging_config import setup_logging, get_logger

# Import paper trading components
from src.trading.paper_trading import PaperTradingEngine, OrderStatus

# Initialize logging
setup_logging()
logger = get_logger("test.paper_trading")

def test_basic_paper_trading():
    """Test basic paper trading functionality"""
    print("=== Basic Paper Trading Test ===")
    
    try:
        engine = PaperTradingEngine(initial_balance=10000.0)
        
        # Execute a sample signal
        signal = {
            'pair_symbol': 'SOL/USDT',
            'signal_type': 'BUY',
            'predicted_reward': 0.025,
            'confidence': 0.8,
            'timestamp': datetime.utcnow(),
            'current_price': 150.0
        }
        
        result = engine.execute_signal(signal)
        print(f"✓ Trade result: {result}")
        
        assert result['status'] == 'executed', "Trade should be executed"
        assert result['order_id'] is not None, "Should return order ID"
        
        # Check portfolio state
        portfolio = engine.get_portfolio_summary()
        print(f"✓ Portfolio after trade: {portfolio}")
        
        assert portfolio['total_value'] > 0, "Portfolio should have value"
        assert 'SOL/USDT' in engine.positions, "Should have SOL position"
        
        print("✓ Basic paper trading test passed")
        return True
        
    except Exception as e:
        print(f"✗ Basic paper trading test failed: {e}")
        return False

def test_pnl_calculation():
    """Test P&L calculation functionality"""
    print("\n=== P&L Calculation Test ===")
    
    try:
        engine = PaperTradingEngine(initial_balance=10000.0)
        
        # Execute buy order
        buy_signal = {
            'pair_symbol': 'SOL/USDT',
            'signal_type': 'BUY',
            'predicted_reward': 0.025,
            'timestamp': datetime.utcnow(),
            'current_price': 150.0
        }
        
        engine.execute_signal(buy_signal)
        
        # Simulate price increase
        engine._update_market_price('SOL/USDT', 160.0)  # 6.67% increase
        
        # Calculate P&L
        pnl = engine.calculate_pnl()
        print(f"✓ Current P&L: {pnl}")
        
        assert pnl['unrealized_pnl'] > 0, "Should have positive unrealized P&L"
        assert pnl['total_return_pct'] > 0, "Should have positive return percentage"
        
        # Execute sell order to realize profit
        sell_signal = {
            'pair_symbol': 'SOL/USDT',
            'signal_type': 'SELL',
            'timestamp': datetime.utcnow(),
            'current_price': 160.0
        }
        
        engine.execute_signal(sell_signal)
        
        final_pnl = engine.calculate_pnl()
        print(f"✓ Final P&L: {final_pnl}")
        
        assert final_pnl['realized_pnl'] > 0, "Should have positive realized P&L"
        
        print("✓ P&L calculation test passed")
        return True
        
    except Exception as e:
        print(f"✗ P&L calculation test failed: {e}")
        return False

def test_order_management():
    """Test order management functionality"""
    print("\n=== Order Management Test ===")
    
    try:
        engine = PaperTradingEngine(initial_balance=10000.0)
        
        # Test market order
        market_signal = {
            'pair_symbol': 'BTC/USDT',
            'signal_type': 'BUY',
            'order_type': 'MARKET',
            'amount': 0.1,
            'current_price': 50000.0,
            'timestamp': datetime.utcnow()
        }
        
        result = engine.execute_signal(market_signal)
        order_id = result['order_id']
        
        # Check order status
        order = engine.orders[order_id]
        print(f"✓ Market order status: {order.status}")
        assert order.status == OrderStatus.FILLED, "Market order should be filled immediately"
        
        # Test insufficient balance scenario
        large_signal = {
            'pair_symbol': 'BTC/USDT',
            'signal_type': 'BUY',
            'current_price': 50000.0,
            'predicted_reward': 0.02,
            'confidence': 0.9,  # This should try to buy a lot
            'timestamp': datetime.utcnow()
        }
        
        # Try to execute with remaining balance
        result2 = engine.execute_signal(large_signal)
        print(f"✓ Large order result: {result2['status']}")
        
        # Test selling without position
        sell_signal = {
            'pair_symbol': 'ETH/USDT',  # Different symbol, no position
            'signal_type': 'SELL',
            'current_price': 3000.0,
            'timestamp': datetime.utcnow()
        }
        
        result3 = engine.execute_signal(sell_signal)
        print(f"✓ Sell without position: {result3['status']}")
        assert result3['status'] == 'rejected', "Should reject sell without position"
        
        print("✓ Order management test passed")
        return True
        
    except Exception as e:
        print(f"✗ Order management test failed: {e}")
        return False

def test_performance_analytics():
    """Test performance analytics functionality"""
    print("\n=== Performance Analytics Test ===")
    
    try:
        engine = PaperTradingEngine(initial_balance=10000.0)
        
        # Execute multiple trades to generate performance data
        trades = [
            {'symbol': 'SOL/USDT', 'side': 'BUY', 'price': 150.0, 'exit_price': 160.0},  # +6.67%
            {'symbol': 'BTC/USDT', 'side': 'BUY', 'price': 50000.0, 'exit_price': 49000.0},  # -2%
            {'symbol': 'ETH/USDT', 'side': 'BUY', 'price': 3000.0, 'exit_price': 3150.0},  # +5%
        ]
        
        for trade in trades:
            # Execute buy
            buy_signal = {
                'pair_symbol': trade['symbol'],
                'signal_type': 'BUY',
                'current_price': trade['price'],
                'predicted_reward': 0.05,
                'confidence': 0.7,
                'timestamp': datetime.utcnow()
            }
            engine.execute_signal(buy_signal)
            
            # Update price and sell
            engine._update_market_price(trade['symbol'], trade['exit_price'])
            sell_signal = {
                'pair_symbol': trade['symbol'],
                'signal_type': 'SELL',
                'current_price': trade['exit_price'],
                'timestamp': datetime.utcnow()
            }
            engine.execute_signal(sell_signal)
        
        # Calculate performance metrics
        metrics = engine.get_performance_metrics()
        print(f"✓ Performance metrics: {metrics}")
        
        assert 'win_rate' in metrics, "Should calculate win rate"
        assert 'sharpe_ratio' in metrics, "Should calculate Sharpe ratio"
        assert 'max_drawdown' in metrics, "Should calculate max drawdown"
        assert metrics['total_trades'] == len(trades), "Should track all trades"
        
        # Check win rate calculation
        expected_winners = 2  # SOL and ETH trades should be profitable
        expected_win_rate = expected_winners / len(trades)
        actual_win_rate = metrics['win_rate']
        
        print(f"✓ Win rate: {actual_win_rate:.2%} (expected ~{expected_win_rate:.2%})")
        
        print("✓ Performance analytics test passed")
        return True
        
    except Exception as e:
        print(f"✗ Performance analytics test failed: {e}")
        return False

def test_position_sizing():
    """Test position sizing logic"""
    print("\n=== Position Sizing Test ===")
    
    try:
        engine = PaperTradingEngine(initial_balance=10000.0)
        
        # Test different confidence levels
        confidence_levels = [0.3, 0.5, 0.8, 0.95]
        
        for confidence in confidence_levels:
            signal = {
                'pair_symbol': f'TEST{confidence}/USDT',
                'signal_type': 'BUY',
                'predicted_reward': 0.03,
                'confidence': confidence,
                'current_price': 100.0,
                'timestamp': datetime.utcnow()
            }
            
            result = engine.execute_signal(signal)
            if result['status'] == 'executed':
                position_value = result['amount'] * result['price']
                portfolio_pct = position_value / engine.initial_balance
                print(f"✓ Confidence {confidence:.1%}: Position {portfolio_pct:.2%} of portfolio")
        
        # Test maximum position size limit
        high_confidence_signal = {
            'pair_symbol': 'MAXTEST/USDT',
            'signal_type': 'BUY',
            'predicted_reward': 0.50,  # Very high predicted reward
            'confidence': 0.99,  # Very high confidence
            'current_price': 100.0,
            'timestamp': datetime.utcnow()
        }
        
        result = engine.execute_signal(high_confidence_signal)
        if result['status'] == 'executed':
            position_value = result['amount'] * result['price']
            portfolio_pct = position_value / engine.initial_balance
            print(f"✓ Max position test: {portfolio_pct:.2%} of portfolio")
            assert portfolio_pct <= engine.max_position_size + 0.01, "Should respect max position size"
        
        print("✓ Position sizing test passed")
        return True
        
    except Exception as e:
        print(f"✗ Position sizing test failed: {e}")
        return False

def test_portfolio_reset():
    """Test portfolio reset functionality"""
    print("\n=== Portfolio Reset Test ===")
    
    try:
        engine = PaperTradingEngine(initial_balance=10000.0)
        
        # Execute some trades
        signal = {
            'pair_symbol': 'SOL/USDT',
            'signal_type': 'BUY',
            'predicted_reward': 0.025,
            'confidence': 0.8,
            'current_price': 150.0,
            'timestamp': datetime.utcnow()
        }
        
        engine.execute_signal(signal)
        
        # Verify portfolio has changed
        assert len(engine.positions) > 0, "Should have positions"
        assert len(engine.trade_history) > 0, "Should have trade history"
        assert engine.current_balance < engine.initial_balance, "Balance should have decreased"
        
        # Reset portfolio
        engine.reset_portfolio()
        
        # Verify reset
        assert len(engine.positions) == 0, "Positions should be cleared"
        assert len(engine.trade_history) == 0, "Trade history should be cleared"
        assert engine.current_balance == engine.initial_balance, "Balance should be reset"
        assert len(engine.orders) == 0, "Orders should be cleared"
        
        print("✓ Portfolio reset test passed")
        return True
        
    except Exception as e:
        print(f"✗ Portfolio reset test failed: {e}")
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n=== Edge Cases Test ===")
    
    try:
        engine = PaperTradingEngine(initial_balance=10000.0)
        
        # Test invalid signal
        invalid_signal = {
            'pair_symbol': 'SOL/USDT',
            # Missing signal_type and current_price
        }
        
        result = engine.execute_signal(invalid_signal)
        print(f"✓ Invalid signal result: {result['status']}")
        assert result['status'] == 'rejected', "Should reject invalid signal"
        
        # Test zero/negative prices
        zero_price_signal = {
            'pair_symbol': 'SOL/USDT',
            'signal_type': 'BUY',
            'current_price': 0.0,
            'timestamp': datetime.utcnow()
        }
        
        result = engine.execute_signal(zero_price_signal)
        print(f"✓ Zero price signal result: {result['status']}")
        
        # Test very small amounts
        small_signal = {
            'pair_symbol': 'SOL/USDT',
            'signal_type': 'BUY',
            'predicted_reward': 0.001,  # Very small reward
            'confidence': 0.1,  # Low confidence
            'current_price': 150.0,
            'timestamp': datetime.utcnow()
        }
        
        result = engine.execute_signal(small_signal)
        print(f"✓ Small position signal result: {result['status']}")
        
        print("✓ Edge cases test passed")
        return True
        
    except Exception as e:
        print(f"✗ Edge cases test failed: {e}")
        return False

def main():
    """Run all paper trading tests"""
    print("Starting Paper Trading System Tests...\n")

    tests = [
        test_basic_paper_trading,
        test_pnl_calculation,
        test_order_management,
        test_performance_analytics,
        test_position_sizing,
        test_portfolio_reset,
        test_edge_cases
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    print(f"\n=== Paper Trading Test Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")

    if all(results):
        print("🎉 All paper trading tests passed!")
    else:
        print("⚠️  Some paper trading tests failed - check the output above for details")

    return all(results)

if __name__ == "__main__":
    main()
