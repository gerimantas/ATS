"""
Test Telegram Notifications System
Tests for the Telegram notification functionality
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import asyncio
import os
from datetime import datetime, timedelta
from config.logging_config import setup_logging, get_logger

# Import Telegram notifier
from src.monitoring.telegram_notifier import TelegramNotifier

# Initialize logging
setup_logging()
logger = get_logger("test.telegram_notifier")

def test_notifier_initialization():
    """Test Telegram notifier initialization"""
    print("=== Notifier Initialization Test ===")
    
    try:
        # Test initialization without credentials
        notifier = TelegramNotifier()
        print(f"✓ Notifier without credentials: enabled={notifier.is_enabled()}")
        
        # Test initialization with mock credentials
        mock_notifier = TelegramNotifier(
            bot_token="mock_token_123",
            chat_ids=["mock_chat_123", "mock_chat_456"]
        )
        
        print(f"✓ Mock notifier: chats={mock_notifier.get_chat_count()}")
        assert mock_notifier.get_chat_count() == 2, "Should have 2 chat IDs"
        
        # Test status information
        status = mock_notifier.get_status()
        print(f"✓ Notifier status: {status}")
        
        assert 'enabled' in status, "Status should include enabled flag"
        assert 'telegram_available' in status, "Status should include library availability"
        assert 'chat_ids_count' in status, "Status should include chat count"
        
        print("✓ Notifier initialization test passed")
        return True
        
    except Exception as e:
        print(f"✗ Notifier initialization test failed: {e}")
        return False

def test_message_formatting():
    """Test message template formatting"""
    print("\n=== Message Formatting Test ===")
    
    try:
        notifier = TelegramNotifier(
            bot_token="mock_token",
            chat_ids=["mock_chat"]
        )
        
        # Test signal message formatting
        signal = {
            'pair_symbol': 'SOL/USDT',
            'signal_type': 'BUY',
            'predicted_reward': 0.025,
            'confidence': 0.8,
            'timestamp': '2024-01-01 12:00:00 UTC',
            'algorithms': ['order_flow', 'liquidity']
        }
        
        # Format signal message manually to test template
        template = notifier.message_templates['signal']
        message_data = {
            'symbol': signal['pair_symbol'],
            'signal_type': signal['signal_type'],
            'predicted_reward': signal['predicted_reward'],
            'confidence': signal['confidence'],
            'timestamp': signal['timestamp'],
            'algorithms': ', '.join(signal['algorithms'])
        }
        
        formatted_message = template.format(**message_data)
        print(f"✓ Signal message formatted: {len(formatted_message)} chars")
        
        # Check that message contains expected elements
        assert 'SOL/USDT' in formatted_message, "Should contain symbol"
        assert 'BUY' in formatted_message, "Should contain signal type"
        assert '2.50%' in formatted_message, "Should contain formatted reward"
        assert '80.0%' in formatted_message, "Should contain formatted confidence"
        
        # Test error message formatting
        error_template = notifier.message_templates['error']
        error_data = {
            'error_type': 'Database Error',
            'message': 'Connection timeout',
            'timestamp': '2024-01-01 12:00:00 UTC',
            'severity': 'HIGH'
        }
        
        error_message = error_template.format(**error_data)
        print(f"✓ Error message formatted: {len(error_message)} chars")
        
        assert 'Database Error' in error_message, "Should contain error type"
        assert 'Connection timeout' in error_message, "Should contain error message"
        assert 'HIGH' in error_message, "Should contain severity"
        
        print("✓ Message formatting test passed")
        return True
        
    except Exception as e:
        print(f"✗ Message formatting test failed: {e}")
        return False

def test_chat_management():
    """Test chat ID management functionality"""
    print("\n=== Chat Management Test ===")
    
    try:
        notifier = TelegramNotifier(
            bot_token="mock_token",
            chat_ids=["chat1", "chat2"]
        )
        
        initial_count = notifier.get_chat_count()
        print(f"✓ Initial chat count: {initial_count}")
        assert initial_count == 2, "Should start with 2 chats"
        
        # Add new chat ID
        notifier.add_chat_id("chat3")
        assert notifier.get_chat_count() == 3, "Should have 3 chats after adding"
        print(f"✓ After adding chat: {notifier.get_chat_count()} chats")
        
        # Try to add duplicate
        notifier.add_chat_id("chat3")  # Should not add duplicate
        assert notifier.get_chat_count() == 3, "Should still have 3 chats (no duplicate)"
        
        # Remove chat ID
        notifier.remove_chat_id("chat2")
        assert notifier.get_chat_count() == 2, "Should have 2 chats after removing"
        print(f"✓ After removing chat: {notifier.get_chat_count()} chats")
        
        # Try to remove non-existent chat
        notifier.remove_chat_id("nonexistent")  # Should not cause error
        assert notifier.get_chat_count() == 2, "Should still have 2 chats"
        
        print("✓ Chat management test passed")
        return True
        
    except Exception as e:
        print(f"✗ Chat management test failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n=== Rate Limiting Test ===")
    
    try:
        notifier = TelegramNotifier(
            bot_token="mock_token",
            chat_ids=["chat1"]
        )
        
        # Test rate limit setting
        initial_limit = notifier.min_interval_seconds
        print(f"✓ Initial rate limit: {initial_limit}s")
        
        notifier.set_rate_limit(2.0)
        assert notifier.min_interval_seconds == 2.0, "Should update rate limit"
        print(f"✓ Updated rate limit: {notifier.min_interval_seconds}s")
        
        # Test rate limiting logic (without actually sending messages)
        chat_id = "test_chat"
        now = datetime.utcnow()
        
        # Simulate first message
        notifier.last_message_time[chat_id] = now
        
        # Check if second message would be rate limited
        time_since_last = (now - notifier.last_message_time[chat_id]).total_seconds()
        should_wait = time_since_last < notifier.min_interval_seconds
        
        print(f"✓ Rate limiting check: should_wait={should_wait}")
        assert should_wait, "Should be rate limited immediately after first message"
        
        # Simulate time passing
        future_time = now + timedelta(seconds=3)
        time_since_last = (future_time - notifier.last_message_time[chat_id]).total_seconds()
        should_wait = time_since_last < notifier.min_interval_seconds
        
        print(f"✓ After waiting: should_wait={should_wait}")
        assert not should_wait, "Should not be rate limited after waiting"
        
        print("✓ Rate limiting test passed")
        return True
        
    except Exception as e:
        print(f"✗ Rate limiting test failed: {e}")
        return False

async def test_notification_methods():
    """Test different notification methods (without actual sending)"""
    print("\n=== Notification Methods Test ===")
    
    try:
        # Create notifier without real credentials (won't actually send)
        notifier = TelegramNotifier()
        
        # Test signal notification
        signal = {
            'pair_symbol': 'SOL/USDT',
            'signal_type': 'BUY',
            'predicted_reward': 0.025,
            'confidence': 0.8,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'algorithms': ['order_flow', 'liquidity']
        }
        
        await notifier.send_signal_notification(signal)
        print("✓ Signal notification method executed")
        
        # Test error notification
        await notifier.send_error_notification(
            error="Test error message",
            severity="HIGH",
            error_type="Test Error"
        )
        print("✓ Error notification method executed")
        
        # Test status update
        status_data = {
            'total_value': 10250.75,
            'pnl': 0.025,
            'active_positions': 3,
            'signals_today': 12,
            'uptime': '2 days, 14 hours'
        }
        
        await notifier.send_status_update(status_data)
        print("✓ Status update method executed")
        
        # Test trade notification
        trade = {
            'symbol': 'SOL/USDT',
            'side': 'BUY',
            'amount': 100.0,
            'price': 150.0,
            'timestamp': datetime.utcnow()
        }
        
        await notifier.send_trade_notification(trade)
        print("✓ Trade notification method executed")
        
        # Test system notification
        await notifier.send_system_notification(
            event="System Started",
            details="ATS system has been initialized successfully"
        )
        print("✓ System notification method executed")
        
        # Test custom message
        await notifier.send_custom_message("🧪 Test custom message")
        print("✓ Custom message method executed")
        
        print("✓ Notification methods test passed")
        return True
        
    except Exception as e:
        print(f"✗ Notification methods test failed: {e}")
        return False

async def test_real_telegram_connection():
    """Test real Telegram connection if credentials are available"""
    print("\n=== Real Telegram Connection Test ===")
    
    try:
        # Check if real credentials are available
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            print("⚠️ Skipping real Telegram test - credentials not configured")
            print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables to test")
            return True  # Skip test but don't fail
        
        print("✓ Found Telegram credentials, testing real connection...")
        
        notifier = TelegramNotifier(bot_token, [chat_id])
        
        if not notifier.is_enabled():
            print("⚠️ Telegram notifier not enabled (library not available)")
            return True
        
        # Test connection
        connection_ok = await notifier.test_connection()
        print(f"✓ Connection test result: {connection_ok}")
        
        if connection_ok:
            # Send test notifications
            await notifier.send_custom_message("🧪 *ATS Test Suite*\n\nTesting Telegram notifications...")
            
            # Test signal notification
            test_signal = {
                'pair_symbol': 'TEST/USDT',
                'signal_type': 'BUY',
                'predicted_reward': 0.025,
                'confidence': 0.8,
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'algorithms': ['test_algorithm']
            }
            
            await notifier.send_signal_notification(test_signal)
            
            # Test error notification
            await notifier.send_error_notification(
                error="Test error from ATS test suite",
                severity="INFO",
                error_type="Test Error"
            )
            
            print("✓ Real Telegram notifications sent successfully")
        
        print("✓ Real Telegram connection test passed")
        return True
        
    except Exception as e:
        print(f"✗ Real Telegram connection test failed: {e}")
        return False

def test_environment_configuration():
    """Test environment variable configuration"""
    print("\n=== Environment Configuration Test ===")
    
    try:
        # Test with environment variables
        original_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        original_chat = os.environ.get('TELEGRAM_CHAT_ID')
        
        # Set test environment variables
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_123'
        os.environ['TELEGRAM_CHAT_ID'] = 'test_chat_123'
        
        # Create notifier without explicit parameters
        notifier = TelegramNotifier()
        
        status = notifier.get_status()
        print(f"✓ Environment config status: {status}")
        
        assert status['bot_token_configured'], "Should detect bot token from environment"
        assert status['chat_ids_count'] == 1, "Should have 1 chat ID from environment"
        
        # Restore original environment
        if original_token:
            os.environ['TELEGRAM_BOT_TOKEN'] = original_token
        else:
            os.environ.pop('TELEGRAM_BOT_TOKEN', None)
            
        if original_chat:
            os.environ['TELEGRAM_CHAT_ID'] = original_chat
        else:
            os.environ.pop('TELEGRAM_CHAT_ID', None)
        
        print("✓ Environment configuration test passed")
        return True
        
    except Exception as e:
        print(f"✗ Environment configuration test failed: {e}")
        return False

def test_error_handling():
    """Test error handling in various scenarios"""
    print("\n=== Error Handling Test ===")
    
    try:
        # Test with invalid data
        notifier = TelegramNotifier(
            bot_token="mock_token",
            chat_ids=["mock_chat"]
        )
        
        # Test with missing signal data
        incomplete_signal = {
            'pair_symbol': 'SOL/USDT'
            # Missing other required fields
        }
        
        # Should not crash
        asyncio.run(notifier.send_signal_notification(incomplete_signal))
        print("✓ Handled incomplete signal data")
        
        # Test with None values
        none_signal = {
            'pair_symbol': None,
            'signal_type': None,
            'predicted_reward': None,
            'confidence': None,
            'timestamp': None,
            'algorithms': None
        }
        
        asyncio.run(notifier.send_signal_notification(none_signal))
        print("✓ Handled None values in signal")
        
        # Test with empty status data
        empty_status = {}
        asyncio.run(notifier.send_status_update(empty_status))
        print("✓ Handled empty status data")
        
        # Test with invalid trade data
        invalid_trade = {
            'symbol': None,
            'side': None,
            'amount': 'invalid',
            'price': 'invalid',
            'timestamp': 'invalid'
        }
        
        asyncio.run(notifier.send_trade_notification(invalid_trade))
        print("✓ Handled invalid trade data")
        
        print("✓ Error handling test passed")
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

def main():
    """Run all Telegram notifier tests"""
    print("Starting Telegram Notifications System Tests...\n")

    tests = [
        test_notifier_initialization,
        test_message_formatting,
        test_chat_management,
        test_rate_limiting,
        lambda: asyncio.run(test_notification_methods()),
        lambda: asyncio.run(test_real_telegram_connection()),
        test_environment_configuration,
        test_error_handling
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__ if hasattr(test, '__name__') else 'async_test'} failed with exception: {e}")
            results.append(False)

    print(f"\n=== Telegram Notifications Test Summary ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")

    if all(results):
        print("🎉 All Telegram notification tests passed!")
        print("\n📱 To test with real Telegram:")
        print("   1. Create a bot via @BotFather on Telegram")
        print("   2. Set TELEGRAM_BOT_TOKEN environment variable")
        print("   3. Set TELEGRAM_CHAT_ID environment variable")
        print("   4. Install python-telegram-bot: pip install python-telegram-bot")
    else:
        print("⚠️  Some Telegram notification tests failed - check the output above for details")

    return all(results)

if __name__ == "__main__":
    main()
