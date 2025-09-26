"""
Test Data Validation Module
Tests for the comprehensive data validation system
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import asyncio
import time
from datetime import datetime, timedelta
import numpy as np
from config.logging_config import setup_logging, get_logger

# Import validation components
from src.data.validator import DataValidator, ValidationSeverity

# Initialize logging
setup_logging()
logger = get_logger("test.validator")

def test_orderbook_validation():
    """Test orderbook validation functionality"""
    print("=== Orderbook Validation Test ===")
    
    try:
        validator = DataValidator()
        
        # Test valid orderbook
        valid_orderbook = {
            'bids': [[50000, 100], [49999, 200], [49998, 300]],
            'asks': [[50001, 100], [50002, 200], [50003, 300]],
            'timestamp': datetime.utcnow(),
            'symbol': 'BTC/USDT'
        }
        
        results = validator.validate_orderbook(valid_orderbook)
        print(f"✓ Valid orderbook validation: {len(results)} issues")
        
        # Should have no critical errors
        critical_errors = [r for r in results if r.severity == ValidationSeverity.CRITICAL]
        assert len(critical_errors) == 0, "Valid orderbook should have no critical errors"
        
        # Test invalid orderbook
        invalid_orderbook = {
            'bids': [[50000, -100]],  # Negative volume
            'asks': [[49999, 200]],   # Ask price lower than bid
            'timestamp': datetime.utcnow() - timedelta(minutes=5),  # Stale data
            'symbol': 'BTC/USDT'
        }
        
        results = validator.validate_orderbook(invalid_orderbook)
        print(f"✓ Invalid orderbook validation: {len(results)} issues")
        
        # Should have multiple errors
        assert len(results) > 0, "Invalid orderbook should have validation errors"
        
        # Check for specific error types
        error_messages = [r.message for r in results]
        assert any('negative volume' in msg.lower() for msg in error_messages), \
               "Should detect negative volume"
        assert any('crossed spread' in msg.lower() for msg in error_messages), \
               "Should detect crossed spread"
        
        print("✓ Orderbook validation test passed")
        return True
        
    except Exception as e:
        print(f"✗ Orderbook validation test failed: {e}")
        return False

def test_trade_validation():
    """Test trade data validation functionality"""
    print("\n=== Trade Data Validation Test ===")
    
    try:
        validator = DataValidator()
        
        # Test valid trade
        valid_trade = {
            'symbol': 'SOL/USDT',
            'side': 'buy',
            'amount': 100.0,
            'price': 150.0,
            'timestamp': datetime.utcnow(),
            'trade_id': 'trade_123'
        }
        
        results = validator.validate_trade_data(valid_trade)
        print(f"✓ Valid trade validation: {len(results)} issues")
        
        # Should have minimal issues
        critical_errors = [r for r in results if r.severity == ValidationSeverity.CRITICAL]
        assert len(critical_errors) == 0, "Valid trade should have no critical errors"
        
        # Test invalid trade
        invalid_trade = {
            'symbol': '',  # Empty symbol
            'side': 'invalid_side',  # Invalid side
            'amount': 0,  # Zero amount
            'price': -150.0,  # Negative price
            'timestamp': None,  # Missing timestamp
        }
        
        results = validator.validate_trade_data(invalid_trade)
        print(f"✓ Invalid trade validation: {len(results)} issues")
        
        assert len(results) >= 4, "Should detect multiple validation errors"
        
        # Check for specific validations
        severities = [r.severity for r in results]
        assert ValidationSeverity.ERROR in severities, "Should have error-level issues"
        
        # Test missing required fields
        incomplete_trade = {
            'symbol': 'SOL/USDT'
            # Missing other required fields
        }
        
        results = validator.validate_trade_data(incomplete_trade)
        print(f"✓ Incomplete trade validation: {len(results)} issues")
        assert len(results) >= 3, "Should detect missing required fields"
        
        print("✓ Trade validation test passed")
        return True
        
    except Exception as e:
        print(f"✗ Trade validation test failed: {e}")
        return False

def test_anomaly_detection():
    """Test price anomaly detection functionality"""
    print("\n=== Anomaly Detection Test ===")
    
    try:
        validator = DataValidator()
        
        # Normal price history
        normal_prices = [150.0, 150.5, 149.8, 150.2, 149.9, 150.1]
        
        # Test normal price (should not trigger anomaly)
        normal_price = 150.3
        results = validator.detect_price_anomalies('SOL/USDT', normal_price, normal_prices)
        print(f"✓ Normal price anomaly check: {len(results)} anomalies")
        
        anomalies = [r for r in results if r.severity in [ValidationSeverity.WARNING, ValidationSeverity.ERROR]]
        assert len(anomalies) == 0, "Normal price should not trigger anomalies"
        
        # Test anomalous price (should trigger anomaly)
        anomalous_price = 200.0  # 33% jump
        results = validator.detect_price_anomalies('SOL/USDT', anomalous_price, normal_prices)
        print(f"✓ Anomalous price check: {len(results)} anomalies")
        
        anomalies = [r for r in results if r.severity in [ValidationSeverity.WARNING, ValidationSeverity.ERROR]]
        assert len(anomalies) > 0, "Anomalous price should trigger alerts"
        
        # Check anomaly details
        price_anomalies = [r for r in results if 'price' in r.message.lower()]
        assert len(price_anomalies) > 0, "Should detect price anomaly specifically"
        
        # Test statistical outlier detection
        extended_prices = normal_prices + [149.5, 150.8, 149.2, 150.6, 149.7]
        outlier_price = 180.0  # Statistical outlier
        
        results = validator.detect_price_anomalies('SOL/USDT', outlier_price, extended_prices)
        print(f"✓ Statistical outlier check: {len(results)} anomalies")
        
        outlier_anomalies = [r for r in results if 'outlier' in r.message.lower()]
        assert len(outlier_anomalies) > 0, "Should detect statistical outliers"
        
        print("✓ Anomaly detection test passed")
        return True
        
    except Exception as e:
        print(f"✗ Anomaly detection test failed: {e}")
        return False

def test_data_quality_scoring():
    """Test data quality scoring functionality"""
    print("\n=== Data Quality Scoring Test ===")
    
    try:
        validator = DataValidator()
        
        # Simulate high-quality data
        high_quality_data = [
            {
                'symbol': 'BTC/USDT',
                'timestamp': datetime.utcnow(),
                'price': 50000.0,
                'volume': 1000.0,
                'quality_issues': []
            }
            for _ in range(10)
        ]
        
        # Add data to validator
        for data in high_quality_data:
            validator._record_data_quality('BTC/USDT', data)
        
        high_quality_score = validator.calculate_data_quality_score('BTC/USDT')
        print(f"✓ High quality data score: {high_quality_score:.3f}")
        
        assert high_quality_score > 0.9, "High quality data should score > 0.9"
        
        # Simulate low-quality data
        low_quality_data = [
            {
                'symbol': 'ETH/USDT',
                'timestamp': datetime.utcnow() - timedelta(minutes=2),  # Stale
                'price': None,  # Missing price
                'volume': -100.0,  # Invalid volume
                'quality_issues': ['missing_price', 'invalid_volume', 'stale_data']
            }
            for _ in range(10)
        ]
        
        for data in low_quality_data:
            validator._record_data_quality('ETH/USDT', data)
        
        low_quality_score = validator.calculate_data_quality_score('ETH/USDT')
        print(f"✓ Low quality data score: {low_quality_score:.3f}")
        
        assert low_quality_score < 0.5, "Low quality data should score < 0.5"
        
        # Test unknown symbol
        unknown_score = validator.calculate_data_quality_score('UNKNOWN/USDT')
        print(f"✓ Unknown symbol score: {unknown_score:.3f}")
        assert unknown_score == 0.5, "Unknown symbol should have neutral score"
        
        print("✓ Data quality scoring test passed")
        return True
        
    except Exception as e:
        print(f"✗ Data quality scoring test failed: {e}")
        return False

def test_threshold_management():
    """Test threshold management functionality"""
    print("\n=== Threshold Management Test ===")
    
    try:
        validator = DataValidator()
        
        # Get initial thresholds
        initial_thresholds = validator.get_thresholds()
        print(f"✓ Initial thresholds: {initial_thresholds}")
        
        # Update a threshold
        old_price_threshold = initial_thresholds['price_change_1min']
        new_price_threshold = 0.08  # 8%
        
        validator.set_threshold('price_change_1min', new_price_threshold)
        
        # Verify threshold was updated
        updated_thresholds = validator.get_thresholds()
        assert updated_thresholds['price_change_1min'] == new_price_threshold, \
               "Threshold should be updated"
        
        print(f"✓ Updated price change threshold: {old_price_threshold} -> {new_price_threshold}")
        
        # Test invalid threshold name
        validator.set_threshold('invalid_threshold', 0.1)  # Should log warning
        
        # Test threshold effect on anomaly detection
        normal_prices = [100.0, 101.0, 99.0, 100.5]
        moderate_change_price = 107.0  # 7% change
        
        # Should not trigger with 8% threshold
        results = validator.detect_price_anomalies('TEST/USDT', moderate_change_price, normal_prices)
        price_change_anomalies = [r for r in results if 'price movement' in r.message.lower()]
        
        print(f"✓ Moderate change with high threshold: {len(price_change_anomalies)} anomalies")
        
        # Lower threshold and test again
        validator.set_threshold('price_change_1min', 0.05)  # 5%
        results = validator.detect_price_anomalies('TEST/USDT', moderate_change_price, normal_prices)
        price_change_anomalies = [r for r in results if 'price movement' in r.message.lower()]
        
        print(f"✓ Moderate change with low threshold: {len(price_change_anomalies)} anomalies")
        assert len(price_change_anomalies) > 0, "Should trigger anomaly with lower threshold"
        
        print("✓ Threshold management test passed")
        return True
        
    except Exception as e:
        print(f"✗ Threshold management test failed: {e}")
        return False

def test_validation_summary():
    """Test validation summary functionality"""
    print("\n=== Validation Summary Test ===")
    
    try:
        validator = DataValidator()
        
        # Generate some validation results
        test_orderbook = {
            'bids': [[50000, -100]],  # Invalid
            'asks': [[49999, 200]],   # Invalid (crossed spread)
            'timestamp': datetime.utcnow(),
            'symbol': 'BTC/USDT'
        }
        
        results = validator.validate_orderbook(test_orderbook)
        validator.validation_history.extend(results)
        
        # Add some trade validation results
        invalid_trade = {
            'symbol': '',
            'side': 'invalid',
            'amount': -100,
            'price': 0,
            'timestamp': None
        }
        
        trade_results = validator.validate_trade_data(invalid_trade)
        validator.validation_history.extend(trade_results)
        
        # Get validation summary
        summary = validator.get_validation_summary(hours=1)
        print(f"✓ Validation summary: {summary}")
        
        assert 'total_validations' in summary, "Should include total validations"
        assert 'severity_breakdown' in summary, "Should include severity breakdown"
        assert 'health_score' in summary, "Should include health score"
        
        assert summary['total_validations'] > 0, "Should have recorded validations"
        assert summary['health_score'] <= 1.0, "Health score should be <= 1.0"
        
        # Test with different time periods
        summary_24h = validator.get_validation_summary(hours=24)
        print(f"✓ 24h summary: {summary_24h['total_validations']} validations")
        
        print("✓ Validation summary test passed")
        return True
        
    except Exception as e:
        print(f"✗ Validation summary test failed: {e}")
        return False

def test_symbol_statistics():
    """Test symbol statistics tracking"""
    print("\n=== Symbol Statistics Test ===")
    
    try:
        validator = DataValidator()
        
        # Update statistics for a symbol
        symbol = 'SOL/USDT'
        prices = [150.0, 151.0, 149.5, 150.8, 149.2, 151.5, 150.3]
        volumes = [1000, 1200, 800, 1500, 900, 1300, 1100]
        
        for price, volume in zip(prices, volumes):
            validator.update_symbol_statistics(symbol, price, volume)
        
        # Check that statistics were recorded
        assert symbol in validator.symbol_stats, "Symbol should be in statistics"
        
        stats = validator.symbol_stats[symbol]
        assert len(stats['prices']) == len(prices), "Should record all prices"
        assert len(stats['volumes']) == len(volumes), "Should record all volumes"
        assert stats['avg_volatility'] > 0, "Should calculate volatility"
        
        print(f"✓ Symbol statistics: {len(stats['prices'])} prices, volatility={stats['avg_volatility']:.4f}")
        
        # Test volatility calculation in anomaly detection
        current_price = 155.0  # Higher volatility
        results = validator.detect_price_anomalies(symbol, current_price, prices)
        
        volatility_anomalies = [r for r in results if 'volatility' in r.message.lower()]
        print(f"✓ Volatility anomaly check: {len(volatility_anomalies)} anomalies")
        
        print("✓ Symbol statistics test passed")
        return True
        
    except Exception as e:
        print(f"✗ Symbol statistics test failed: {e}")
        return False

def test_history_management():
    """Test validation history management"""
    print("\n=== History Management Test ===")
    
    try:
        validator = DataValidator()
        
        # Add some old validation results
        old_result = validator.validate_trade_data({
            'symbol': 'TEST/USDT',
            'side': 'invalid',
            'amount': -1,
            'price': 0,
            'timestamp': datetime.utcnow() - timedelta(hours=25)  # Old
        })
        
        # Manually set old timestamp
        for result in old_result:
            result.timestamp = datetime.utcnow() - timedelta(hours=25)
        
        validator.validation_history.extend(old_result)
        
        # Add some recent validation results
        recent_result = validator.validate_trade_data({
            'symbol': 'TEST/USDT',
            'side': 'buy',
            'amount': 100,
            'price': 150,
            'timestamp': datetime.utcnow()
        })
        
        validator.validation_history.extend(recent_result)
        
        initial_count = len(validator.validation_history)
        print(f"✓ Initial validation history: {initial_count} items")
        
        # Clear old history
        validator.clear_history(older_than_hours=24)
        
        final_count = len(validator.validation_history)
        print(f"✓ After cleanup: {final_count} items")
        
        assert final_count < initial_count, "Should have removed old items"
        
        # Verify recent items are still there
        recent_items = [v for v in validator.validation_history 
                       if v.timestamp >= datetime.utcnow() - timedelta(hours=1)]
        assert len(recent_items) > 0, "Should keep recent items"
        
        print("✓ History management test passed")
        return True
        
    except Exception as e:
        print(f"✗ History management test failed: {e}")
        return False

def main():
    """Run all data validation tests"""
    print("Starting Data Validation System Tests...\n")

    tests = [
        test_orderbook_validation,
        test_trade_validation,
        test_anomaly_detection,
        test_data_quality_scoring,
        test_threshold_management,
        test_validation_summary,
        test_symbol_statistics,
        test_history_management
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    print(f"\n=== Data Validation Test Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")

    if all(results):
        print("🎉 All data validation tests passed!")
    else:
        print("⚠️  Some data validation tests failed - check the output above for details")

    return all(results)

if __name__ == "__main__":
    main()
