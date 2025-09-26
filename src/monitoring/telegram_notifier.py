"""
Telegram Notifications System
Implements basic Telegram notifications for signals, errors, and system status
"""
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import os
from loguru import logger
import json
from config.logging_config import get_logger

logger = get_logger("monitoring.telegram_notifier")

# Try to import telegram library, handle if not installed
try:
    import telegram
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot not installed. Telegram notifications disabled.")

class TelegramNotifier:
    """
    Telegram notification system for ATS alerts and status updates
    """

    def __init__(self, bot_token: str = None, chat_ids: List[str] = None):
        """
        Initialize Telegram notifier

        Args:
            bot_token: Telegram bot token (from BotFather)
            chat_ids: List of chat IDs to send notifications to
        """
        # Get credentials from environment if not provided
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_ids = chat_ids or [os.getenv('TELEGRAM_CHAT_ID')] if os.getenv('TELEGRAM_CHAT_ID') else []
        
        # Remove None values from chat_ids
        self.chat_ids = [chat_id for chat_id in self.chat_ids if chat_id]
        
        self.bot = None
        self.enabled = False
        
        # Rate limiting
        self.last_message_time = {}
        self.min_interval_seconds = 1  # Minimum 1 second between messages
        
        # Message templates with rich formatting
        self.message_templates = {
            'signal': '🚨 *ATS Signal Alert*\n\n'
                     '📊 Pair: `{symbol}`\n'
                     '📈 Type: *{signal_type}*\n'
                     '💰 Predicted Reward: {predicted_reward:.2%}\n'
                     '🎯 Confidence: {confidence:.1%}\n'
                     '⏰ Time: {timestamp}\n'
                     '🔗 Algorithms: {algorithms}',
            
            'error': '❌ *ATS Error Alert*\n\n'
                    '🚫 Error: `{error_type}`\n'
                    '📝 Message: {message}\n'
                    '⏰ Time: {timestamp}\n'
                    '🔧 Severity: *{severity}*',
            
            'status': '📊 *ATS Status Update*\n\n'
                     '💼 Portfolio Value: ${total_value:,.2f}\n'
                     '📈 P&L: {pnl:+.2%}\n'
                     '📊 Active Positions: {active_positions}\n'
                     '🎯 Signals Today: {signals_today}\n'
                     '⏰ Uptime: {uptime}',
            
            'trade': '💹 *Trade Executed*\n\n'
                    '📊 Symbol: `{symbol}`\n'
                    '📈 Side: *{side}*\n'
                    '💰 Amount: {amount:.6f}\n'
                    '💵 Price: ${price:.4f}\n'
                    '💸 Value: ${value:.2f}\n'
                    '⏰ Time: {timestamp}',
            
            'system': '⚙️ *System Notification*\n\n'
                     '📢 Event: *{event}*\n'
                     '📝 Details: {details}\n'
                     '⏰ Time: {timestamp}'
        }
        
        # Initialize bot if credentials are available
        self._initialize_bot()
        
        logger.info(f"TelegramNotifier initialized: enabled={self.enabled}, chats={len(self.chat_ids)}")

    def _initialize_bot(self):
        """Initialize Telegram bot connection"""
        try:
            if not TELEGRAM_AVAILABLE:
                logger.warning("Telegram library not available")
                return
                
            if not self.bot_token:
                logger.warning("No Telegram bot token provided")
                return
                
            if not self.chat_ids:
                logger.warning("No Telegram chat IDs provided")
                return
            
            self.bot = Bot(token=self.bot_token)
            self.enabled = True
            logger.info("Telegram bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            self.enabled = False

    async def send_signal_notification(self, signal: Dict):
        """
        Send trading signal notification

        Args:
            signal: Signal dictionary with signal details
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled, skipping signal notification")
            return

        try:
            # Format algorithms list
            algorithms = signal.get('algorithms', [])
            if isinstance(algorithms, list):
                algorithms_str = ', '.join(algorithms)
            else:
                algorithms_str = str(algorithms)

            # Prepare message data
            message_data = {
                'symbol': signal.get('pair_symbol', signal.get('symbol', 'Unknown')),
                'signal_type': signal.get('signal_type', 'Unknown'),
                'predicted_reward': signal.get('predicted_reward', 0.0),
                'confidence': signal.get('confidence', 0.0),
                'timestamp': signal.get('timestamp', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')),
                'algorithms': algorithms_str
            }

            # Format message
            message = self.message_templates['signal'].format(**message_data)
            
            # Send to all chat IDs
            await self._send_message_to_all(message)
            
            logger.info(f"Signal notification sent: {signal.get('pair_symbol')} {signal.get('signal_type')}")

        except Exception as e:
            logger.error(f"Error sending signal notification: {e}")

    async def send_error_notification(self, error: str, severity: str = "ERROR", 
                                    error_type: str = "System Error"):
        """
        Send error notification

        Args:
            error: Error message
            severity: Error severity level
            error_type: Type of error
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled, skipping error notification")
            return

        try:
            # Prepare message data
            message_data = {
                'error_type': error_type,
                'message': error,
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'severity': severity
            }

            # Format message
            message = self.message_templates['error'].format(**message_data)
            
            # Send to all chat IDs
            await self._send_message_to_all(message)
            
            logger.info(f"Error notification sent: {error_type} - {severity}")

        except Exception as e:
            logger.error(f"Error sending error notification: {e}")

    async def send_status_update(self, status_data: Dict):
        """
        Send system status update

        Args:
            status_data: Dictionary with status information
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled, skipping status update")
            return

        try:
            # Prepare message data with defaults
            message_data = {
                'total_value': status_data.get('total_value', 0.0),
                'pnl': status_data.get('pnl', 0.0),
                'active_positions': status_data.get('active_positions', 0),
                'signals_today': status_data.get('signals_today', 0),
                'uptime': status_data.get('uptime', 'Unknown')
            }

            # Format message
            message = self.message_templates['status'].format(**message_data)
            
            # Send to all chat IDs
            await self._send_message_to_all(message)
            
            logger.info("Status update notification sent")

        except Exception as e:
            logger.error(f"Error sending status update: {e}")

    async def send_trade_notification(self, trade: Dict):
        """
        Send trade execution notification

        Args:
            trade: Trade dictionary with execution details
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled, skipping trade notification")
            return

        try:
            # Calculate trade value
            amount = trade.get('amount', 0.0)
            price = trade.get('price', 0.0)
            value = amount * price

            # Prepare message data
            message_data = {
                'symbol': trade.get('symbol', 'Unknown'),
                'side': trade.get('side', 'Unknown'),
                'amount': amount,
                'price': price,
                'value': value,
                'timestamp': trade.get('timestamp', datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S UTC')
            }

            # Format message
            message = self.message_templates['trade'].format(**message_data)
            
            # Send to all chat IDs
            await self._send_message_to_all(message)
            
            logger.info(f"Trade notification sent: {trade.get('symbol')} {trade.get('side')}")

        except Exception as e:
            logger.error(f"Error sending trade notification: {e}")

    async def send_system_notification(self, event: str, details: str = ""):
        """
        Send system notification

        Args:
            event: System event name
            details: Additional details about the event
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled, skipping system notification")
            return

        try:
            # Prepare message data
            message_data = {
                'event': event,
                'details': details,
                'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            }

            # Format message
            message = self.message_templates['system'].format(**message_data)
            
            # Send to all chat IDs
            await self._send_message_to_all(message)
            
            logger.info(f"System notification sent: {event}")

        except Exception as e:
            logger.error(f"Error sending system notification: {e}")

    async def send_custom_message(self, message: str, parse_mode: str = 'Markdown'):
        """
        Send custom formatted message

        Args:
            message: Custom message text
            parse_mode: Telegram parse mode (Markdown or HTML)
        """
        if not self.enabled:
            logger.debug("Telegram notifications disabled, skipping custom message")
            return

        try:
            # Send to all chat IDs
            await self._send_message_to_all(message, parse_mode)
            
            logger.info("Custom message sent")

        except Exception as e:
            logger.error(f"Error sending custom message: {e}")

    async def _send_message_to_all(self, message: str, parse_mode: str = 'Markdown'):
        """
        Send message to all configured chat IDs with rate limiting

        Args:
            message: Message text to send
            parse_mode: Telegram parse mode
        """
        if not self.enabled or not self.bot:
            return

        for chat_id in self.chat_ids:
            try:
                # Rate limiting check
                now = datetime.utcnow()
                if chat_id in self.last_message_time:
                    time_since_last = (now - self.last_message_time[chat_id]).total_seconds()
                    if time_since_last < self.min_interval_seconds:
                        await asyncio.sleep(self.min_interval_seconds - time_since_last)

                # Send message
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True
                )
                
                # Update rate limiting timestamp
                self.last_message_time[chat_id] = datetime.utcnow()
                
                logger.debug(f"Message sent to chat {chat_id}")

            except TelegramError as e:
                logger.error(f"Telegram error sending to {chat_id}: {e}")
            except Exception as e:
                logger.error(f"Error sending message to {chat_id}: {e}")

    def is_enabled(self) -> bool:
        """Check if Telegram notifications are enabled"""
        return self.enabled

    def get_chat_count(self) -> int:
        """Get number of configured chat IDs"""
        return len(self.chat_ids)

    def add_chat_id(self, chat_id: str):
        """Add a new chat ID for notifications"""
        if chat_id not in self.chat_ids:
            self.chat_ids.append(chat_id)
            logger.info(f"Added chat ID: {chat_id}")

    def remove_chat_id(self, chat_id: str):
        """Remove a chat ID from notifications"""
        if chat_id in self.chat_ids:
            self.chat_ids.remove(chat_id)
            logger.info(f"Removed chat ID: {chat_id}")

    def set_rate_limit(self, seconds: float):
        """Set minimum interval between messages"""
        self.min_interval_seconds = seconds
        logger.info(f"Rate limit set to {seconds} seconds")

    async def test_connection(self) -> bool:
        """
        Test Telegram bot connection

        Returns:
            True if connection successful, False otherwise
        """
        if not self.enabled or not self.bot:
            return False

        try:
            # Get bot info to test connection
            bot_info = await self.bot.get_me()
            logger.info(f"Bot connection test successful: @{bot_info.username}")
            
            # Send test message to first chat
            if self.chat_ids:
                test_message = "🧪 *ATS Connection Test*\n\nTelegram notifications are working correctly!"
                await self.bot.send_message(
                    chat_id=self.chat_ids[0],
                    text=test_message,
                    parse_mode='Markdown'
                )
                logger.info("Test message sent successfully")
            
            return True

        except Exception as e:
            logger.error(f"Bot connection test failed: {e}")
            return False

    def get_status(self) -> Dict:
        """Get notifier status information"""
        return {
            'enabled': self.enabled,
            'telegram_available': TELEGRAM_AVAILABLE,
            'bot_token_configured': bool(self.bot_token),
            'chat_ids_count': len(self.chat_ids),
            'chat_ids': self.chat_ids,
            'rate_limit_seconds': self.min_interval_seconds
        }

    def __repr__(self):
        return (f"TelegramNotifier(enabled={self.enabled}, "
                f"chats={len(self.chat_ids)}, "
                f"rate_limit={self.min_interval_seconds}s)")
