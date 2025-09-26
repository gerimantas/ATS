"""
Tests for Liquidity Event Detection Algorithm functionality
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import asyncio
import time
from datetime import datetime, timedelta
import numpy as np
from config.logging_config import setup_logging, get_logger
from src.algorithms.liquidity import LiquidityAnalyzer

# Initialize logging
setup_logging()
logger = get_logger("test.liquidity")

def test_liquidity_initialization():
    """Test liquidity analyzer initialization"""
    print("=== Liquidity Analyzer Initialization Test ===")

    try:
        analyzer = LiquidityAnalyzer(window_seconds=60)

        # Check initialization
        assert analyzer.window_seconds == 60
        assert analyzer.change_rate_threshold == 0.1
        assert analyzer.acceleration_threshold == 0.05
        assert analyzer.min_liquidity_threshold == 10000
        assert analyzer.cooldown_period == 120

        print("✓ Liquidity analyzer initialized successfully")
        print(f"  Window: {analyzer.window_seconds}s")
        print(f"  Change rate threshold: {analyzer.change_rate_threshold}")
        print(f"  Acceleration threshold: {analyzer.acceleration_threshold}")

        return True

    except Exception as e:
        print(f"✗ Liquidity analyzer initialization failed: {e}")
        return False

def test_liquidity_data_processing():
    """Test liquidity data processing"""
    print("\n=== Liquidity Data Processing Test ===")

    try:
        analyzer = LiquidityAnalyzer(window_seconds=60)

        # Add sample liquidity data points
        base_time = datetime.utcnow()
        liquidity_points = [
            {
                'total_liquidity': 1000000,
                'token0_liquidity': 500000,
                'token1_liquidity': 500000,
                'timestamp': base_time - timedelta(seconds=60)
            },
            {
                'total_liquidity': 1100000,  # 10% increase
                'token0_liquidity': 550000,
                'token1_liquidity': 550000,
                'timestamp': base_time - timedelta(seconds=30)
            },
            {
                'total_liquidity': 1300000,  # Accelerating increase
                'token0_liquidity': 650000,
                'token1_liquidity': 650000,
                'timestamp': base_time
            }
        ]

        for point in liquidity_points:
            analyzer.add_liquidity_data('SOL/USDT', point)

        # Check data was added
        assert 'SOL/USDT' in analyzer.liquidity_windows
        assert len(analyzer.liquidity_windows['SOL/USDT']) == 3

        print("✓ Liquidity data processing successful")
        print(f"  Data points stored: {len(analyzer.liquidity_windows['SOL/USDT'])}")

        return True

    except Exception as e:
        print(f"✗ Liquidity data processing test failed: {e}")
        return False

def test_liquidity_change_rate():
    """Test liquidity change rate calculation"""
    print("\n=== Liquidity Change Rate Test ===")

    try:
        analyzer = LiquidityAnalyzer(window_seconds=60)

        # Add liquidity data with known change rate
        base_time = datetime.utcnow()
        base_liquidity = 1000000

        # Add data points with increasing liquidity
        for i in range(5):
            liquidity = base_liquidity * (1 + i * 0.1)  # 10% increase each step
            analyzer.add_liquidity_data('SOL/USDT', {
                'total_liquidity': liquidity,
                'timestamp': base_time - timedelta(seconds=60-i*15)
            })

        change_rate = analyzer.calculate_liquidity_change_rate('SOL/USDT')

        print(f"✓ Liquidity change rate: {change_rate:.6f}/s")

        # Should be positive for increasing liquidity
        assert change_rate > 0, f"Expected positive change rate, got {change_rate:.6f}"

        return True

    except Exception as e:
        print(f"✗ Liquidity change rate test failed: {e}")
        return False

def test_liquidity_acceleration():
    """Test liquidity acceleration calculation"""
    print("\n=== Liquidity Acceleration Test ===")

    try:
        analyzer = LiquidityAnalyzer(window_seconds=120)

        # Add liquidity data with accelerating change
        base_time = datetime.utcnow()
        base_liquidity = 1000000

        # Create accelerating pattern
        for i in range(6):
            # Quadratic growth pattern (accelerating)
            multiplier = 1 + (i * 0.05) + (i * i * 0.01)
            liquidity = base_liquidity * multiplier
            analyzer.add_liquidity_data('SOL/USDT', {
                'total_liquidity': liquidity,
                'timestamp': base_time - timedelta(seconds=120-i*20)
            })

        acceleration = analyzer.calculate_liquidity_acceleration('SOL/USDT')

        print(f"✓ Liquidity acceleration: {acceleration:.8f}/s²")

        # Should be positive for accelerating increase
        assert acceleration > 0, f"Expected positive acceleration, got {acceleration:.8f}"

        return True

    except Exception as e:
        print(f"✗ Liquidity acceleration test failed: {e}")
        return False

def test_liquidity_signal_generation():
    """Test liquidity signal generation"""
    print("\n=== Liquidity Signal Generation Test ===")

    try:
        analyzer = LiquidityAnalyzer(window_seconds=60)

        # Add significant liquidity event
        base_time = datetime.utcnow()
        
        # Add normal liquidity
        analyzer.add_liquidity_data('SOL/USDT', {
            'total_liquidity': 1000000,
            'timestamp': base_time - timedelta(seconds=60)
        })

        # Add sudden liquidity increase (should trigger event)
        analyzer.add_liquidity_data('SOL/USDT', {
            'total_liquidity': 1500000,  # 50% increase
            'timestamp': base_time
        })

        signal_triggered, signal_type = analyzer.is_signal_triggered('SOL/USDT')

        if signal_triggered:
            print(f"✓ Liquidity event detected: {signal_type}")
            assert signal_type in ['LIQUIDITY_INCREASE', 'LIQUIDITY_DECREASE']
        else:
            print("✗ No liquidity event detected")
            return False

        # Test cooldown
        immediate_signal, _ = analyzer.is_signal_triggered('SOL/USDT')
        assert not immediate_signal, "Should be in cooldown"

        print("✓ Cooldown working correctly")

        return True

    except Exception as e:
        print(f"✗ Liquidity signal generation test failed: {e}")
        return False

def test_liquidity_threshold_filtering():
    """Test minimum liquidity threshold filtering"""
    print("\n=== Liquidity Threshold Filtering Test ===")

    try:
        analyzer = LiquidityAnalyzer(window_seconds=60)
        analyzer.min_liquidity_threshold = 50000  # Set threshold

        # Add low liquidity data
        base_time = datetime.utcnow()
        analyzer.add_liquidity_data('SOL/USDT', {
            'total_liquidity': 10000,  # Below threshold
            'timestamp': base_time - timedelta(seconds=30)
        })

        analyzer.add_liquidity_data('SOL/USDT', {
            'total_liquidity': 20000,  # Still below threshold
            'timestamp': base_time
        })

        # Should not trigger signal due to low liquidity
        signal_triggered, _ = analyzer.is_signal_triggered('SOL/USDT')
        assert not signal_triggered, "Should not trigger with low liquidity"

        print("✓ Low liquidity filtering working")

        # Add high liquidity data
        analyzer.add_liquidity_data('SOL/USDT', {
            'total_liquidity': 100000,  # Above threshold
            'timestamp': base_time
        })

        # Should now consider signals
        signal_triggered, signal_type = analyzer.is_signal_triggered('SOL/USDT')
        print(f"✓ High liquidity signal check: triggered={signal_triggered}")

        return True

    except Exception as e:
        print(f"✗ Liquidity threshold filtering test failed: {e}")
        return False

def test_parameter_updates():
    """Test parameter update functionality"""
    print("\n=== Parameter Update Test ===")

    try:
        analyzer = LiquidityAnalyzer(window_seconds=60)

        # Update parameters
        analyzer.update_parameters(
            change_rate_threshold=0.15,
            acceleration_threshold=0.08,
            min_liquidity_threshold=20000,
            cooldown_period=180
        )

        assert analyzer.change_rate_threshold == 0.15
        assert analyzer.acceleration_threshold == 0.08
        assert analyzer.min_liquidity_threshold == 20000
        assert analyzer.cooldown_period == 180

        print("✓ Parameter updates working")
        print(f"  New change rate threshold: {analyzer.change_rate_threshold}")
        print(f"  New acceleration threshold: {analyzer.acceleration_threshold}")

        return True

    except Exception as e:
        print(f"✗ Parameter update test failed: {e}")
        return False

def test_statistics():
    """Test statistics and reporting"""
    print("\n=== Statistics Test ===")

    try:
        analyzer = LiquidityAnalyzer(window_seconds=60)

        # Add some liquidity data
        base_time = datetime.utcnow()
        for i in range(3):
            analyzer.add_liquidity_data('SOL/USDT', {
                'total_liquidity': 1000000 + i * 100000,
                'timestamp': base_time - timedelta(seconds=60-i*20)
            })

        # Generate a signal
        analyzer.is_signal_triggered('SOL/USDT')

        # Check statistics
        stats = analyzer.get_signal_stats()

        assert stats['analyzed_symbols'] == 1
        assert stats['cooldown_period'] == 120

        print("✓ Statistics tracking working")
        print(f"  Total signals: {stats['total_signals']}")
        print(f"  Analyzed symbols: {stats['analyzed_symbols']}")

        # Check recent signals
        recent = analyzer.get_recent_signals()
        print(f"✓ Recent signals count: {len(recent)}")

        return True

    except Exception as e:
        print(f"✗ Statistics test failed: {e}")
        return False

def main():
    """Run all liquidity analyzer tests"""
    print("Starting Liquidity Event Detection Algorithm Tests...\n")

    tests = [
        test_liquidity_initialization,
        test_liquidity_data_processing,
        test_liquidity_change_rate,
        test_liquidity_acceleration,
        test_liquidity_signal_generation,
        test_liquidity_threshold_filtering,
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
        print("🎉 All liquidity analyzer tests passed!")
    else:
        print("⚠️  Some tests failed - check the output above for details")

    return all(results)

if __name__ == "__main__":
    main()
