"""
Tests for Order Flow Algorithm functionality
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import asyncio
import time
from datetime import datetime, timedelta
from config.logging_config import setup_logging, get_logger
from src.algorithms.order_flow import OrderFlowAnalyzer

# Initialize logging
setup_logging()
logger = get_logger("test.order_flow")

def test_order_flow_initialization():
    """Test order flow analyzer initialization"""
    print("=== Order Flow Analyzer Initialization Test ===")

    try:
        analyzer = OrderFlowAnalyzer(window_seconds=30)

        # Check initialization
        assert analyzer.window_seconds == 30
        assert analyzer.imbalance_threshold == 0.6
        assert analyzer.min_volume_threshold == 1000
        assert analyzer.cooldown_period == 60

        print("✓ Order flow analyzer initialized successfully")
        print(f"  Window: {analyzer.window_seconds}s")
        print(f"  Threshold: {analyzer.imbalance_threshold}")
        print(f"  Min volume: {analyzer.min_volume_threshold}")

        return True

    except Exception as e:
        print(f"✗ Order flow analyzer initialization failed: {e}")
        return False

def test_trade_processing():
    """Test trade data processing"""
    print("\n=== Trade Processing Test ===")

    try:
        analyzer = OrderFlowAnalyzer(window_seconds=30)

        # Add sample trades
        base_time = datetime.utcnow()
        test_trades = [
            {
                'side': 'buy', 'amount': 100, 'price': 150.0,
                'timestamp': base_time, 'is_aggressive': True
            },
            {
                'side': 'sell', 'amount': 50, 'price': 149.9,
                'timestamp': base_time, 'is_aggressive': True
            },
            {
                'side': 'buy', 'amount': 200, 'price': 150.1,
                'timestamp': base_time, 'is_aggressive': True
            }
        ]

        for trade in test_trades:
            analyzer.add_trade('SOL/USDT', trade)

        # Check trades were added
        assert 'SOL/USDT' in analyzer.trade_windows
        assert len(analyzer.trade_windows['SOL/USDT']) == 3

        print("✓ Trade processing successful")
        print(f"  Trades stored: {len(analyzer.trade_windows['SOL/USDT'])}")

        return True

    except Exception as e:
        print(f"✗ Trade processing test failed: {e}")
        return False

def test_imbalance_calculation():
    """Test order flow imbalance calculation"""
    print("\n=== Imbalance Calculation Test ===")

    try:
        analyzer = OrderFlowAnalyzer(window_seconds=30)

        # Add trades with strong buy pressure
        base_time = datetime.utcnow()
        buy_trades = [
            {'side': 'buy', 'amount': 100, 'price': 150.0, 'timestamp': base_time},
            {'side': 'buy', 'amount': 200, 'price': 150.1, 'timestamp': base_time},
            {'side': 'buy', 'amount': 150, 'price': 150.2, 'timestamp': base_time},
        ]

        for trade in buy_trades:
            analyzer.add_trade('SOL/USDT', trade)

        imbalance = analyzer.calculate_imbalance('SOL/USDT')

        print(f"✓ Imbalance calculation: {imbalance:.3f}")

        # Should be positive (buy pressure)
        assert imbalance > 0.5, f"Expected high positive imbalance, got {imbalance:.3f}"

        # Test with sell pressure
        analyzer.clear_data('SOL/USDT')
        sell_trades = [
            {'side': 'sell', 'amount': 100, 'price': 150.0, 'timestamp': base_time},
            {'side': 'sell', 'amount': 200, 'price': 149.9, 'timestamp': base_time},
            {'side': 'sell', 'amount': 150, 'price': 149.8, 'timestamp': base_time},
        ]

        for trade in sell_trades:
            analyzer.add_trade('SOL/USDT', trade)

        sell_imbalance = analyzer.calculate_imbalance('SOL/USDT')

        print(f"✓ Sell imbalance: {sell_imbalance:.3f}")

        # Should be negative (sell pressure)
        assert sell_imbalance < -0.5, f"Expected high negative imbalance, got {sell_imbalance:.3f}"

        return True

    except Exception as e:
        print(f"✗ Imbalance calculation test failed: {e}")
        return False

def test_signal_generation():
    """Test signal generation"""
    print("\n=== Signal Generation Test ===")

    try:
        analyzer = OrderFlowAnalyzer(window_seconds=30)

        # Add strong buy pressure
        base_time = datetime.utcnow()
        for i in range(10):
            analyzer.add_trade('SOL/USDT', {
                'side': 'buy', 'amount': 100, 'price': 150.0 + i * 0.01,
                'timestamp': base_time, 'is_aggressive': True
            })

        signal_triggered, signal_type = analyzer.is_signal_triggered('SOL/USDT')

        if signal_triggered:
            print(f"✓ Signal generated: {signal_type}")
            assert signal_type == 'BUY', f"Expected BUY signal, got {signal_type}"
        else:
            print("✗ No signal generated")
            return False

        # Test cooldown
        immediate_signal, _ = analyzer.is_signal_triggered('SOL/USDT')
        assert not immediate_signal, "Should be in cooldown"

        print("✓ Cooldown working correctly")

        return True

    except Exception as e:
        print(f"✗ Signal generation test failed: {e}")
        return False

def test_window_management():
    """Test time window management"""
    print("\n=== Window Management Test ===")

    try:
        analyzer = OrderFlowAnalyzer(window_seconds=5)  # Short window for testing

        base_time = datetime.utcnow()

        # Add old trade (outside window)
        old_trade = {
            'side': 'buy', 'amount': 100, 'price': 150.0,
            'timestamp': base_time - timedelta(seconds=10),
            'is_aggressive': True
        }
        analyzer.add_trade('SOL/USDT', old_trade)

        # Add recent trade
        recent_trade = {
            'side': 'sell', 'amount': 100, 'price': 149.9,
            'timestamp': base_time, 'is_aggressive': True
        }
        analyzer.add_trade('SOL/USDT', recent_trade)

        # Check that old trade was cleaned up
        imbalance = analyzer.calculate_imbalance('SOL/USDT')

        print(f"✓ Window management: imbalance {imbalance:.3f}")

        # Should be negative (only recent sell trade)
        assert imbalance < -0.5, f"Expected negative imbalance after cleanup, got {imbalance:.3f}"

        return True

    except Exception as e:
        print(f"✗ Window management test failed: {e}")
        return False

def test_volume_threshold():
    """Test volume threshold filtering"""
    print("\n=== Volume Threshold Test ===")

    try:
        analyzer = OrderFlowAnalyzer(window_seconds=30)
        analyzer.min_volume_threshold = 1000  # Set threshold manually

        # Add low volume trades
        base_time = datetime.utcnow()
        low_volume_trades = [
            {'side': 'buy', 'amount': 10, 'price': 150.0, 'timestamp': base_time},
            {'side': 'buy', 'amount': 20, 'price': 150.1, 'timestamp': base_time},
        ]

        for trade in low_volume_trades:
            analyzer.add_trade('SOL/USDT', trade)

        # Should not trigger signal due to low volume
        signal_triggered, _ = analyzer.is_signal_triggered('SOL/USDT')
        assert not signal_triggered, "Should not trigger with low volume"

        print("✓ Volume threshold filtering working")

        # Add high volume trades
        high_volume_trades = [
            {'side': 'buy', 'amount': 500, 'price': 150.0, 'timestamp': base_time},
            {'side': 'buy', 'amount': 600, 'price': 150.1, 'timestamp': base_time},
        ]

        for trade in high_volume_trades:
            analyzer.add_trade('SOL/USDT', trade)

        # Should trigger signal with sufficient volume
        signal_triggered, signal_type = analyzer.is_signal_triggered('SOL/USDT')

        if signal_triggered:
            print(f"✓ High volume signal: {signal_type}")
            assert signal_type == 'BUY'
        else:
            print("✗ High volume should trigger signal")
            return False

        return True

    except Exception as e:
        print(f"✗ Volume threshold test failed: {e}")
        return False

def test_parameter_updates():
    """Test parameter update functionality"""
    print("\n=== Parameter Update Test ===")

    try:
        analyzer = OrderFlowAnalyzer(window_seconds=30)

        # Update parameters
        analyzer.update_parameters(
            imbalance_threshold=0.7,
            min_volume_threshold=2000,
            cooldown_period=120
        )

        assert analyzer.imbalance_threshold == 0.7
        assert analyzer.min_volume_threshold == 2000
        assert analyzer.cooldown_period == 120

        print("✓ Parameter updates working")
        print(f"  New threshold: {analyzer.imbalance_threshold}")
        print(f"  New volume threshold: {analyzer.min_volume_threshold}")

        return True

    except Exception as e:
        print(f"✗ Parameter update test failed: {e}")
        return False

def test_statistics():
    """Test statistics and reporting"""
    print("\n=== Statistics Test ===")

    try:
        analyzer = OrderFlowAnalyzer(window_seconds=30)

        # Add some trades
        base_time = datetime.utcnow()
        for i in range(5):
            analyzer.add_trade('SOL/USDT', {
                'side': 'buy', 'amount': 100, 'price': 150.0,
                'timestamp': base_time, 'is_aggressive': True
            })

        # Generate a signal
        analyzer.is_signal_triggered('SOL/USDT')

        # Check statistics
        stats = analyzer.get_signal_stats()

        assert stats['total_signals'] == 1
        assert stats['analyzed_symbols'] == 1
        assert stats['cooldown_period'] == 60

        print("✓ Statistics tracking working")
        print(f"  Total signals: {stats['total_signals']}")
        print(f"  Analyzed symbols: {stats['analyzed_symbols']}")

        # Check recent signals
        recent = analyzer.get_recent_signals()
        assert len(recent) == 1

        print("✓ Recent signals tracking working")

        return True

    except Exception as e:
        print(f"✗ Statistics test failed: {e}")
        return False

def main():
    """Run all order flow tests"""
    print("Starting Order Flow Algorithm Tests...\n")

    tests = [
        test_order_flow_initialization,
        test_trade_processing,
        test_imbalance_calculation,
        test_signal_generation,
        test_window_management,
        test_volume_threshold,
        test_parameter_updates,
        test_statistics
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    print(f"\n=== Test Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")

    if all(results):
        print("🎉 All order flow tests passed!")
    else:
        print("⚠️  Some tests failed - check the output above for details")

    return all(results)

if __name__ == "__main__":
    main()
