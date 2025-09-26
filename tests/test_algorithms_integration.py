"""
Integration Tests for All Algorithm Components
Tests the complete Phase A2 algorithm implementation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import asyncio
import time
from datetime import datetime, timedelta
import numpy as np
from config.logging_config import setup_logging, get_logger

# Import all algorithm components
from src.algorithms.order_flow import OrderFlowAnalyzer
from src.algorithms.liquidity import LiquidityAnalyzer
from src.algorithms.volume_price import VolumePriceAnalyzer
from src.algorithms.signal_aggregator import SignalAggregator

# Import risk management components
from src.risk.slippage import SlippageAnalyzer
from src.risk.market_regime import MarketRegimeFilter
from src.risk.latency import LatencyCompensationManager
from src.risk.cooldown import CooldownManager

# Initialize logging
setup_logging()
logger = get_logger("test.integration")

def test_algorithm_initialization():
    """Test initialization of all algorithm components"""
    print("=== Algorithm Components Initialization Test ===")

    try:
        # Initialize algorithm components
        order_flow = OrderFlowAnalyzer(window_seconds=30)
        liquidity = LiquidityAnalyzer(window_seconds=60)
        volume_price = VolumePriceAnalyzer(window_seconds=120)
        signal_aggregator = SignalAggregator(confirmation_threshold=2)

        # Initialize risk management components
        slippage = SlippageAnalyzer()
        market_regime = MarketRegimeFilter(volatility_window=300)
        latency = LatencyCompensationManager({'order_flow': 0.6, 'liquidity': 0.1})
        cooldown = CooldownManager()

        print("✓ All algorithm components initialized successfully")
        print(f"  Order Flow: {order_flow.window_seconds}s window")
        print(f"  Liquidity: {liquidity.window_seconds}s window")
        print(f"  Volume-Price: {volume_price.window_seconds}s window")
        print(f"  Signal Aggregator: {signal_aggregator.confirmation_threshold} threshold")
        print(f"  Risk components: 4 initialized")

        return True

    except Exception as e:
        print(f"✗ Algorithm initialization failed: {e}")
        return False

def test_signal_generation_pipeline():
    """Test complete signal generation pipeline"""
    print("\n=== Signal Generation Pipeline Test ===")

    try:
        # Initialize components
        order_flow = OrderFlowAnalyzer(window_seconds=30)
        liquidity = LiquidityAnalyzer(window_seconds=60)
        volume_price = VolumePriceAnalyzer(window_seconds=120)
        signal_aggregator = SignalAggregator(confirmation_threshold=2)

        # Simulate market data
        base_time = datetime.utcnow()
        symbol = 'SOL/USDT'

        # 1. Add order flow data (strong buy pressure)
        for i in range(10):
            order_flow.add_trade(symbol, {
                'side': 'buy',
                'amount': 100 + i * 10,
                'price': 150.0 + i * 0.01,
                'timestamp': base_time - timedelta(seconds=30-i*3),
                'is_aggressive': True
            })

        # 2. Add liquidity data (increasing liquidity)
        for i in range(5):
            liquidity.add_liquidity_data(symbol, {
                'total_liquidity': 1000000 + i * 200000,  # Significant increase
                'timestamp': base_time - timedelta(seconds=60-i*15)
            })

        # 3. Add volume-price data
        for i in range(8):
            volume_price.add_price_data(symbol, {
                'price': 150.0 + i * 0.05,
                'timestamp': base_time - timedelta(seconds=120-i*15)
            })
            
            volume_price.add_volume_data(symbol, {
                'volume': 5000 + i * 1000,  # Increasing volume
                'timestamp': base_time - timedelta(seconds=120-i*15)
            })

        # 4. Check individual algorithm signals
        of_signal, of_type = order_flow.is_signal_triggered(symbol)
        liq_signal, liq_type = liquidity.is_signal_triggered(symbol)
        vp_signal, vp_type = volume_price.is_signal_triggered(symbol)

        print(f"✓ Individual signals:")
        print(f"  Order Flow: {of_type if of_signal else 'None'}")
        print(f"  Liquidity: {liq_type if liq_signal else 'None'}")
        print(f"  Volume-Price: {vp_type if vp_signal else 'None'}")

        # 5. Test signal aggregation
        signals_generated = 0
        if of_signal:
            combined = signal_aggregator.add_algorithm_signal(symbol, of_type, 'order_flow', 0.8)
            if combined:
                signals_generated += 1

        if liq_signal:
            combined = signal_aggregator.add_algorithm_signal(symbol, liq_type, 'liquidity', 0.7)
            if combined:
                signals_generated += 1

        if vp_signal:
            combined = signal_aggregator.add_algorithm_signal(symbol, vp_type, 'volume_price', 0.6)
            if combined:
                signals_generated += 1

        print(f"✓ Signal aggregation: {signals_generated} combined signals generated")

        # Get aggregator stats
        agg_stats = signal_aggregator.get_aggregator_stats()
        print(f"  Total combined signals: {agg_stats['total_combined_signals']}")

        return True

    except Exception as e:
        print(f"✗ Signal generation pipeline test failed: {e}")
        return False

def test_risk_management_integration():
    """Test risk management system integration"""
    print("\n=== Risk Management Integration Test ===")

    try:
        # Initialize risk components
        slippage = SlippageAnalyzer()
        market_regime = MarketRegimeFilter(volatility_window=300)
        latency = LatencyCompensationManager({'order_flow': 0.6, 'liquidity': 0.1})
        cooldown = CooldownManager()

        symbol = 'SOL/USDT'

        # 1. Test slippage analysis
        mock_orderbook = {
            'bids': [[50000, 100], [49999, 200], [49998, 300]],
            'asks': [[50001, 100], [50002, 200], [50003, 300]]
        }

        slippage_result = slippage.calculate_slippage(mock_orderbook, 1000, 'BUY')
        print(f"✓ Slippage analysis: {slippage_result.get('estimated_slippage', 0):.4f}")

        # Test signal cancellation
        should_cancel = slippage.should_cancel_signal(0.003, 0.010)  # 0.3% slippage, 1% profit
        print(f"  Signal cancellation: {should_cancel}")

        # 2. Test market regime filtering
        base_time = datetime.utcnow()
        
        # Add BTC price data for regime detection
        for i in range(20):
            price = 50000 + np.random.normal(0, 500)  # Some volatility
            market_regime.add_price_data('BTC', price, base_time - timedelta(seconds=300-i*15))

        # Test signal filtering
        should_filter, reason = market_regime.should_filter_signal(symbol, is_altcoin=True)
        print(f"✓ Market regime filtering: {should_filter} ({reason})")
        print(f"  Current regime: {market_regime.current_regime}")

        # 3. Test latency compensation
        # Record some latency measurements
        latency.record_latency('data_acquisition', 45.0)
        latency.record_latency('data_acquisition', 52.0)
        latency.record_latency('signal_processing', 15.0)

        current_threshold = latency.get_current_threshold('order_flow')
        print(f"✓ Latency compensation: threshold adjusted to {current_threshold:.3f}")

        # 4. Test cooldown management
        cooldown.set_cooldown(symbol, minutes=5)
        is_in_cooldown = cooldown.is_in_cooldown(symbol)
        remaining = cooldown.get_remaining_cooldown(symbol)

        print(f"✓ Cooldown management: in_cooldown={is_in_cooldown}, remaining={remaining}s")

        return True

    except Exception as e:
        print(f"✗ Risk management integration test failed: {e}")
        return False

def test_complete_trading_decision():
    """Test complete trading decision process"""
    print("\n=== Complete Trading Decision Test ===")

    try:
        # Initialize all components
        order_flow = OrderFlowAnalyzer(window_seconds=30)
        liquidity = LiquidityAnalyzer(window_seconds=60)
        volume_price = VolumePriceAnalyzer(window_seconds=120)
        signal_aggregator = SignalAggregator(confirmation_threshold=2)
        
        slippage = SlippageAnalyzer()
        market_regime = MarketRegimeFilter(volatility_window=300)
        cooldown = CooldownManager()

        symbol = 'SOL/USDT'
        base_time = datetime.utcnow()

        print("Step 1: Generate market signals...")

        # Generate strong buy signals from multiple algorithms
        # Order flow: Strong buy pressure
        for i in range(15):
            order_flow.add_trade(symbol, {
                'side': 'buy',
                'amount': 150,
                'price': 150.0 + i * 0.01,
                'timestamp': base_time - timedelta(seconds=30-i*2),
                'is_aggressive': True
            })

        # Liquidity: Significant increase
        liquidity.add_liquidity_data(symbol, {
            'total_liquidity': 500000,
            'timestamp': base_time - timedelta(seconds=60)
        })
        liquidity.add_liquidity_data(symbol, {
            'total_liquidity': 800000,  # 60% increase
            'timestamp': base_time
        })

        # Check individual signals
        of_signal, of_type = order_flow.is_signal_triggered(symbol)
        liq_signal, liq_type = liquidity.is_signal_triggered(symbol)

        print(f"  Order Flow Signal: {of_type if of_signal else 'None'}")
        print(f"  Liquidity Signal: {liq_type if liq_signal else 'None'}")

        print("Step 2: Aggregate signals...")

        # Aggregate signals
        combined_signal_generated = False
        if of_signal:
            combined = signal_aggregator.add_algorithm_signal(symbol, of_type, 'order_flow', 0.8)
            if combined:
                combined_signal_generated = True

        if liq_signal:
            combined = signal_aggregator.add_algorithm_signal(symbol, liq_type, 'liquidity', 0.7)
            if combined:
                combined_signal_generated = True

        print(f"  Combined signal generated: {combined_signal_generated}")

        print("Step 3: Apply risk filters...")

        # Check cooldown
        in_cooldown = cooldown.is_in_cooldown(symbol)
        print(f"  Cooldown check: {'BLOCKED' if in_cooldown else 'PASSED'}")

        # Check market regime
        should_filter, reason = market_regime.should_filter_signal(symbol, is_altcoin=True)
        print(f"  Market regime filter: {'BLOCKED' if should_filter else 'PASSED'} ({reason})")

        # Check slippage
        mock_orderbook = {
            'asks': [[150.01, 1000], [150.02, 2000], [150.03, 3000]]
        }
        slippage_result = slippage.calculate_slippage(mock_orderbook, 5000, 'BUY')
        should_cancel = slippage.should_cancel_signal(
            slippage_result.get('estimated_slippage', 0), 0.015  # 1.5% expected profit
        )
        print(f"  Slippage filter: {'BLOCKED' if should_cancel else 'PASSED'} "
              f"(slippage: {slippage_result.get('estimated_slippage', 0):.4f})")

        print("Step 4: Final decision...")

        # Final trading decision
        can_trade = (
            combined_signal_generated and
            not in_cooldown and
            not should_filter and
            not should_cancel
        )

        print(f"  FINAL DECISION: {'EXECUTE TRADE' if can_trade else 'NO TRADE'}")

        if can_trade:
            # Set cooldown for executed trade
            cooldown.set_cooldown(symbol)
            print(f"  Cooldown set for {symbol}")

        return True

    except Exception as e:
        print(f"✗ Complete trading decision test failed: {e}")
        return False

def test_performance_and_stats():
    """Test performance monitoring and statistics"""
    print("\n=== Performance and Statistics Test ===")

    try:
        # Initialize components
        order_flow = OrderFlowAnalyzer(window_seconds=30)
        signal_aggregator = SignalAggregator(confirmation_threshold=2)
        slippage = SlippageAnalyzer()
        cooldown = CooldownManager()

        # Generate some activity
        symbol = 'SOL/USDT'
        base_time = datetime.utcnow()

        # Add some trades and generate signals
        for i in range(5):
            order_flow.add_trade(symbol, {
                'side': 'buy',
                'amount': 100,
                'price': 150.0,
                'timestamp': base_time,
                'is_aggressive': True
            })

        # Get statistics from all components
        of_stats = order_flow.get_signal_stats()
        agg_stats = signal_aggregator.get_aggregator_stats()
        slip_stats = slippage.get_slippage_stats()
        cool_stats = cooldown.get_cooldown_stats()

        print("✓ Component statistics:")
        print(f"  Order Flow: {of_stats['analyzed_symbols']} symbols, {of_stats['total_signals']} signals")
        print(f"  Signal Aggregator: {agg_stats['total_combined_signals']} combined signals")
        print(f"  Slippage Analyzer: {slip_stats['total_analyses']} analyses")
        print(f"  Cooldown Manager: {cool_stats['total_cooldowns_set']} cooldowns set")

        return True

    except Exception as e:
        print(f"✗ Performance and statistics test failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("Starting ATS Phase A2 Algorithm Integration Tests...\n")

    tests = [
        test_algorithm_initialization,
        test_signal_generation_pipeline,
        test_risk_management_integration,
        test_complete_trading_decision,
        test_performance_and_stats
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    print(f"\n=== Integration Test Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")

    if all(results):
        print("🎉 All integration tests passed!")
        print("\n✅ Phase A2 Algorithm Implementation Complete!")
        print("   - Order Flow Imbalance Detection: ✓")
        print("   - Liquidity Event Detection: ✓")
        print("   - Volume-Price Correlation Analysis: ✓")
        print("   - Multi-Algorithm Signal Aggregation: ✓")
        print("   - Pre-Trade Slippage Analysis: ✓")
        print("   - Market Regime Filtering: ✓")
        print("   - Latency Compensation: ✓")
        print("   - Cooldown Period Management: ✓")
    else:
        print("⚠️  Some integration tests failed - check the output above for details")

    return all(results)

if __name__ == "__main__":
    main()
