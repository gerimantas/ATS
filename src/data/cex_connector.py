"""
CEX (Centralized Exchange) data connector using CCXT Pro
Implements real-time L2 orderbook data integration from centralized exchanges
"""
import ccxt.pro as ccxt
import asyncio
from typing import Dict, List, Optional, Callable
from loguru import logger
import time
from datetime import datetime
import json
from collections import deque
import os
from config.logging_config import get_logger

logger = get_logger("data.cex_connector")

class CEXConnector:
    """
    Centralized Exchange connector for real-time market data
    Supports multiple exchanges via CCXT Pro
    """
    
    def __init__(self, exchange_id: str, api_key: str = None, api_secret: str = None, sandbox: bool = True):
        """
        Initialize CEX connector
        
        Args:
            exchange_id: Exchange identifier (e.g., 'binance', 'okx')
            api_key: API key (optional for public data)
            api_secret: API secret (optional for public data)
            sandbox: Use sandbox/testnet environment
        """
        self.exchange_id = exchange_id
        self.sandbox = sandbox
        self.exchange = None
        self.orderbooks = {}
        self.trades = {}
        self.latency_stats = {}
        self.connection_status = {}
        self.subscriptions = set()
        
        # Performance tracking
        self.latency_window = deque(maxlen=100)  # Last 100 latency measurements
        self.data_quality_scores = {}
        
        # Rate limiting
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.last_request_time = 0
        
        # Initialize exchange
        self._initialize_exchange(api_key, api_secret)
        
    def _initialize_exchange(self, api_key: str = None, api_secret: str = None):
        """Initialize CCXT Pro exchange instance"""
        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            
            config = {
                'enableRateLimit': True,
                'rateLimit': 100,  # 100ms between requests
                'timeout': 30000,  # 30 second timeout
                'verbose': False,
            }
            
            # Add API credentials if provided
            if api_key and api_secret:
                config.update({
                    'apiKey': api_key,
                    'secret': api_secret,
                })
            
            # Enable sandbox mode
            if self.sandbox:
                config['sandbox'] = True
                
            self.exchange = exchange_class(config)
            logger.info(f"Initialized {self.exchange_id} exchange connector (sandbox: {self.sandbox})")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.exchange_id} exchange: {e}")
            raise
    
    async def connect(self):
        """Establish connection and load markets"""
        try:
            logger.info(f"Connecting to {self.exchange_id}...")
            
            # Load markets
            markets = await self.exchange.load_markets()
            logger.info(f"Loaded {len(markets)} markets from {self.exchange_id}")
            
            # Test connection with a simple API call
            ticker = await self.exchange.fetch_ticker('BTC/USDT')
            logger.info(f"Connection test successful - BTC/USDT: ${ticker['last']}")
            
            self.connection_status[self.exchange_id] = {
                'connected': True,
                'last_ping': datetime.utcnow(),
                'markets_count': len(markets)
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.exchange_id}: {e}")
            self.connection_status[self.exchange_id] = {
                'connected': False,
                'error': str(e),
                'last_attempt': datetime.utcnow()
            }
            return False
    
    async def subscribe_orderbook(self, symbol: str, limit: int = 20):
        """
        Subscribe to real-time L2 orderbook updates
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            limit: Number of price levels to retrieve
        """
        try:
            logger.info(f"Subscribing to {symbol} orderbook on {self.exchange_id}")
            
            # Add to subscriptions
            self.subscriptions.add(f"orderbook:{symbol}")
            
            # Initialize orderbook storage
            if symbol not in self.orderbooks:
                self.orderbooks[symbol] = {
                    'bids': [],
                    'asks': [],
                    'timestamp': None,
                    'datetime': None,
                    'nonce': None
                }
            
            # Start orderbook monitoring loop
            asyncio.create_task(self._orderbook_loop(symbol, limit))
            
            logger.info(f"Successfully subscribed to {symbol} orderbook")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to {symbol} orderbook: {e}")
            raise
    
    async def _orderbook_loop(self, symbol: str, limit: int):
        """Continuous orderbook update loop"""
        while f"orderbook:{symbol}" in self.subscriptions:
            try:
                start_time = time.time()
                
                # Fetch orderbook
                orderbook = await self.exchange.watch_order_book(symbol, limit)
                
                # Calculate latency
                latency_ms = (time.time() - start_time) * 1000
                self._record_latency(symbol, 'orderbook', latency_ms)
                
                # Update stored orderbook
                self.orderbooks[symbol] = orderbook
                
                # Validate data quality
                quality_score = self._calculate_data_quality(orderbook)
                self.data_quality_scores[f"{symbol}_orderbook"] = quality_score
                
                logger.debug(f"{symbol} orderbook updated - latency: {latency_ms:.2f}ms, quality: {quality_score:.2f}")
                
            except Exception as e:
                logger.error(f"Error in orderbook loop for {symbol}: {e}")
                await asyncio.sleep(1)  # Wait before retry
    
    async def subscribe_trades(self, symbol: str):
        """
        Subscribe to real-time trades
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
        """
        try:
            logger.info(f"Subscribing to {symbol} trades on {self.exchange_id}")
            
            # Add to subscriptions
            self.subscriptions.add(f"trades:{symbol}")
            
            # Initialize trades storage
            if symbol not in self.trades:
                self.trades[symbol] = deque(maxlen=1000)  # Keep last 1000 trades
            
            # Start trades monitoring loop
            asyncio.create_task(self._trades_loop(symbol))
            
            logger.info(f"Successfully subscribed to {symbol} trades")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to {symbol} trades: {e}")
            raise
    
    async def _trades_loop(self, symbol: str):
        """Continuous trades update loop"""
        while f"trades:{symbol}" in self.subscriptions:
            try:
                start_time = time.time()
                
                # Fetch trades
                trades = await self.exchange.watch_trades(symbol)
                
                # Calculate latency
                latency_ms = (time.time() - start_time) * 1000
                self._record_latency(symbol, 'trades', latency_ms)
                
                # Store new trades
                for trade in trades:
                    self.trades[symbol].append(trade)
                
                logger.debug(f"{symbol} trades updated - {len(trades)} new trades, latency: {latency_ms:.2f}ms")
                
            except Exception as e:
                logger.error(f"Error in trades loop for {symbol}: {e}")
                await asyncio.sleep(1)  # Wait before retry
    
    def _record_latency(self, symbol: str, data_type: str, latency_ms: float):
        """Record latency for performance monitoring"""
        key = f"{symbol}_{data_type}"
        
        if key not in self.latency_stats:
            self.latency_stats[key] = {
                'measurements': deque(maxlen=100),
                'avg_latency': 0,
                'min_latency': float('inf'),
                'max_latency': 0,
                'last_update': None
            }
        
        stats = self.latency_stats[key]
        stats['measurements'].append(latency_ms)
        stats['min_latency'] = min(stats['min_latency'], latency_ms)
        stats['max_latency'] = max(stats['max_latency'], latency_ms)
        stats['avg_latency'] = sum(stats['measurements']) / len(stats['measurements'])
        stats['last_update'] = datetime.utcnow()
        
        # Add to global latency window
        self.latency_window.append(latency_ms)
    
    def _calculate_data_quality(self, orderbook: dict) -> float:
        """
        Calculate data quality score for orderbook
        
        Returns:
            Quality score between 0 and 1
        """
        try:
            score = 1.0
            
            # Check if orderbook has data
            if not orderbook.get('bids') or not orderbook.get('asks'):
                return 0.0
            
            # Check bid-ask spread reasonableness
            best_bid = orderbook['bids'][0][0] if orderbook['bids'] else 0
            best_ask = orderbook['asks'][0][0] if orderbook['asks'] else 0
            
            if best_bid <= 0 or best_ask <= 0 or best_bid >= best_ask:
                score -= 0.5
            
            # Check depth (number of levels)
            bid_levels = len(orderbook['bids'])
            ask_levels = len(orderbook['asks'])
            
            if bid_levels < 5 or ask_levels < 5:
                score -= 0.2
            
            # Check timestamp freshness
            if orderbook.get('timestamp'):
                age_seconds = (time.time() * 1000 - orderbook['timestamp']) / 1000
                if age_seconds > 5:  # Data older than 5 seconds
                    score -= 0.3
            
            return max(0.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating data quality: {e}")
            return 0.0
    
    def get_orderbook(self, symbol: str) -> Optional[dict]:
        """Get latest orderbook for symbol"""
        return self.orderbooks.get(symbol)
    
    def get_trades(self, symbol: str, limit: int = 100) -> List[dict]:
        """Get recent trades for symbol"""
        if symbol not in self.trades:
            return []
        
        trades_list = list(self.trades[symbol])
        return trades_list[-limit:] if limit else trades_list
    
    def get_latency_stats(self, symbol: str = None) -> dict:
        """Get latency statistics"""
        if symbol:
            return {k: v for k, v in self.latency_stats.items() if symbol in k}
        return self.latency_stats
    
    def get_connection_status(self) -> dict:
        """Get connection status"""
        return self.connection_status
    
    def get_data_quality_scores(self) -> dict:
        """Get data quality scores"""
        return self.data_quality_scores
    
    async def unsubscribe(self, symbol: str, data_type: str = None):
        """
        Unsubscribe from symbol data
        
        Args:
            symbol: Trading pair symbol
            data_type: 'orderbook', 'trades', or None for all
        """
        if data_type:
            subscription = f"{data_type}:{symbol}"
            if subscription in self.subscriptions:
                self.subscriptions.remove(subscription)
                logger.info(f"Unsubscribed from {symbol} {data_type}")
        else:
            # Unsubscribe from all data types for this symbol
            to_remove = [sub for sub in self.subscriptions if symbol in sub]
            for sub in to_remove:
                self.subscriptions.remove(sub)
            logger.info(f"Unsubscribed from all {symbol} data")
    
    async def close(self):
        """Close exchange connection and cleanup"""
        try:
            # Clear all subscriptions
            self.subscriptions.clear()
            
            # Close exchange connection
            if self.exchange:
                await self.exchange.close()
            
            logger.info(f"Closed {self.exchange_id} connector")
            
        except Exception as e:
            logger.error(f"Error closing {self.exchange_id} connector: {e}")
    
    def __repr__(self):
        return f"CEXConnector(exchange={self.exchange_id}, subscriptions={len(self.subscriptions)}, connected={self.connection_status.get(self.exchange_id, {}).get('connected', False)})"
