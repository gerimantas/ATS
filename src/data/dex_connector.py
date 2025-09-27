"""
DEX (Decentralized Exchange) data connector using Birdeye API
Implements real-time DEX trading data and liquidity information
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from loguru import logger
import time
from datetime import datetime, timedelta
import json
from collections import deque
import os
from config.logging_config import get_logger
from config.birdeye_config import get_birdeye_config

logger = get_logger("data.dex_connector")


class DEXConnector:
    """
    Decentralized Exchange connector for real-time market data
    Uses Birdeye API for DEX data aggregation
    """

    def __init__(self, api_key: str, base_url: str = "https://public-api.birdeye.so"):
        """
        Initialize DEX connector

        Args:
            api_key: Birdeye API key
            base_url: Birdeye API base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self.connection_status = {}

        # Get configuration from config file
        config = get_birdeye_config()

        # Rate limiting based on configuration
        self.rate_limiter = {
            "requests_made": 0,
            "daily_limit": config["daily_limit"],
            "last_reset": datetime.utcnow().date(),
            "request_times": deque(maxlen=100),  # Track request timing
            "test_mode": config.get("enabled", True),
            "delay_between_requests": config["delay_between_requests"],
            "warning_threshold": config["warning_threshold"],
            "critical_threshold": config["critical_threshold"],
        }

        # Data storage
        self.trades_data = {}
        self.liquidity_data = {}
        self.token_info = {}
        self.price_data = {}

        # Performance tracking
        self.latency_stats = {}
        self.data_quality_scores = {}

        # Supported chains
        self.supported_chains = ["solana", "ethereum", "bsc", "polygon"]

    async def connect(self):
        """Initialize HTTP session and test API connection"""
        try:
            logger.info("Connecting to Birdeye API...")

            # Create HTTP session with proper headers
            headers = {
                "X-API-KEY": self.api_key,
                "Accept": "application/json",
                "User-Agent": "ATS-DEX-Connector/1.0",
            }

            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout,
                connector=aiohttp.TCPConnector(limit=10),
            )

            # Test connection with a simple API call
            test_response = await self._make_request("/defi/networks")

            if test_response and "data" in test_response:
                networks = test_response["data"]
                logger.info(
                    f"Connection successful - {len(networks)} networks available"
                )

                self.connection_status["birdeye"] = {
                    "connected": True,
                    "last_ping": datetime.utcnow(),
                    "networks_count": len(networks),
                    "daily_requests_used": self.rate_limiter["requests_made"],
                }
                return True
            else:
                logger.error("Connection test failed - invalid response")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to Birdeye API: {e}")
            self.connection_status["birdeye"] = {
                "connected": False,
                "error": str(e),
                "last_attempt": datetime.utcnow(),
            }
            return False

    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make HTTP request with rate limiting and error handling

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Response data or None if failed
        """
        try:
            # Check rate limits
            if not self._check_rate_limit():
                logger.warning("Rate limit exceeded, skipping request")
                return None

            start_time = time.time()

            # Make request
            url = f"{self.base_url}{endpoint}"
            async with self.session.get(url, params=params) as response:

                # Calculate latency
                latency_ms = (time.time() - start_time) * 1000
                self._record_latency(endpoint, latency_ms)

                # Update rate limiter
                self._update_rate_limiter()

                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Request successful: {endpoint} - {latency_ms:.2f}ms")
                    return data
                elif response.status == 429:
                    logger.warning(f"Rate limit hit: {endpoint}")
                    return None
                else:
                    logger.error(
                        f"Request failed: {endpoint} - Status {response.status}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Request error for {endpoint}: {e}")
            return None

    def _check_rate_limit(self) -> bool:
        """Check if we can make another request"""
        current_date = datetime.utcnow().date()

        # Reset daily counter if new day
        if current_date > self.rate_limiter["last_reset"]:
            self.rate_limiter["requests_made"] = 0
            self.rate_limiter["last_reset"] = current_date
            logger.info("Daily rate limit counter reset")

        # Check daily limit
        if self.rate_limiter["requests_made"] >= self.rate_limiter["daily_limit"]:
            return False

        # Check per-request delay based on configuration
        now = time.time()
        delay = self.rate_limiter["delay_between_requests"]

        if delay > 0:
            delay_ago = now - delay
            recent_requests = [
                t for t in self.rate_limiter["request_times"] if t > delay_ago
            ]
            if len(recent_requests) >= 1:
                logger.debug(f"Rate limit: waiting {delay} seconds between requests")
                return False

        return True

    def _update_rate_limiter(self):
        """Update rate limiter counters with safety warnings"""
        self.rate_limiter["requests_made"] += 1
        self.rate_limiter["request_times"].append(time.time())

        # Safety warnings based on configuration thresholds
        daily_used = self.rate_limiter["requests_made"]
        daily_limit = self.rate_limiter["daily_limit"]
        warning_threshold = self.rate_limiter["warning_threshold"]
        critical_threshold = self.rate_limiter["critical_threshold"]

        usage_ratio = daily_used / daily_limit

        if usage_ratio >= warning_threshold and usage_ratio < critical_threshold:
            logger.warning(
                f"⚠️  API usage warning: {daily_used}/{daily_limit} requests used ({usage_ratio*100:.1f}%)"
            )
        elif usage_ratio >= critical_threshold:
            logger.error(
                f"🚨 API usage critical: {daily_used}/{daily_limit} requests used - approaching limit!"
            )

        if daily_used >= daily_limit:
            logger.error(
                "🛑 Daily API limit reached! No more requests will be made today."
            )

    def _record_latency(self, endpoint: str, latency_ms: float):
        """Record API latency for monitoring"""
        if endpoint not in self.latency_stats:
            self.latency_stats[endpoint] = {
                "measurements": deque(maxlen=100),
                "avg_latency": 0,
                "min_latency": float("inf"),
                "max_latency": 0,
                "last_update": None,
            }

        stats = self.latency_stats[endpoint]
        stats["measurements"].append(latency_ms)
        stats["min_latency"] = min(stats["min_latency"], latency_ms)
        stats["max_latency"] = max(stats["max_latency"], latency_ms)
        stats["avg_latency"] = sum(stats["measurements"]) / len(stats["measurements"])
        stats["last_update"] = datetime.utcnow()

    async def get_token_trades(
        self, token_address: str, chain: str = "solana", limit: int = 100
    ) -> List[Dict]:
        """
        Get recent trades for a token

        Args:
            token_address: Token contract address
            chain: Blockchain network
            limit: Number of trades to retrieve

        Returns:
            List of trade data
        """
        try:
            logger.info(f"Getting trades for {token_address} on {chain}")

            params = {
                "address": token_address,
                "limit": min(limit, 100),  # API limit
                "sort_type": "desc",
            }

            endpoint = f"/defi/txs/token"
            response = await self._make_request(endpoint, params)

            if response and "data" in response:
                trades = response["data"]["items"]

                # Store trades data
                key = f"{chain}:{token_address}"
                if key not in self.trades_data:
                    self.trades_data[key] = deque(maxlen=1000)

                # Add new trades
                for trade in trades:
                    self.trades_data[key].append(trade)

                # Calculate data quality
                quality_score = self._calculate_trades_quality(trades)
                self.data_quality_scores[f"{key}_trades"] = quality_score

                logger.info(f"Retrieved {len(trades)} trades for {token_address}")
                return trades
            else:
                logger.warning(f"No trades data received for {token_address}")
                return []

        except Exception as e:
            logger.error(f"Error getting trades for {token_address}: {e}")
            return []

    async def get_token_liquidity(
        self, token_address: str, chain: str = "solana"
    ) -> Dict:
        """
        Get liquidity information for a token

        Args:
            token_address: Token contract address
            chain: Blockchain network

        Returns:
            Liquidity data
        """
        try:
            logger.info(f"Getting liquidity for {token_address} on {chain}")

            params = {"address": token_address}

            endpoint = f"/defi/token_overview"
            response = await self._make_request(endpoint, params)

            if response and "data" in response:
                liquidity_info = response["data"]

                # Store liquidity data
                key = f"{chain}:{token_address}"
                self.liquidity_data[key] = {
                    "data": liquidity_info,
                    "timestamp": datetime.utcnow(),
                    "chain": chain,
                }

                # Calculate data quality
                quality_score = self._calculate_liquidity_quality(liquidity_info)
                self.data_quality_scores[f"{key}_liquidity"] = quality_score

                logger.info(f"Retrieved liquidity info for {token_address}")
                return liquidity_info
            else:
                logger.warning(f"No liquidity data received for {token_address}")
                return {}

        except Exception as e:
            logger.error(f"Error getting liquidity for {token_address}: {e}")
            return {}

    async def get_token_price(self, token_address: str, chain: str = "solana") -> Dict:
        """
        Get current price information for a token

        Args:
            token_address: Token contract address
            chain: Blockchain network

        Returns:
            Price data
        """
        try:
            logger.info(f"Getting price for {token_address} on {chain}")

            params = {"address": token_address}

            endpoint = f"/defi/price"
            response = await self._make_request(endpoint, params)

            if response and "data" in response:
                price_info = response["data"]

                # Store price data
                key = f"{chain}:{token_address}"
                self.price_data[key] = {
                    "data": price_info,
                    "timestamp": datetime.utcnow(),
                    "chain": chain,
                }

                logger.info(
                    f"Retrieved price info for {token_address}: ${price_info.get('value', 'N/A')}"
                )
                return price_info
            else:
                logger.warning(f"No price data received for {token_address}")
                return {}

        except Exception as e:
            logger.error(f"Error getting price for {token_address}: {e}")
            return {}

    async def get_trending_tokens(
        self, chain: str = "solana", limit: int = 50
    ) -> List[Dict]:
        """
        Get trending tokens on a chain

        Args:
            chain: Blockchain network
            limit: Number of tokens to retrieve

        Returns:
            List of trending tokens
        """
        try:
            logger.info(f"Getting trending tokens on {chain}")

            params = {
                "sort_by": "volume24hUSD",
                "sort_type": "desc",
                "limit": min(limit, 50),
            }

            endpoint = f"/defi/tokenlist"
            response = await self._make_request(endpoint, params)

            if response and "data" in response:
                tokens = response["data"]["tokens"]
                logger.info(f"Retrieved {len(tokens)} trending tokens")
                return tokens
            else:
                logger.warning("No trending tokens data received")
                return []

        except Exception as e:
            logger.error(f"Error getting trending tokens: {e}")
            return []

    def _calculate_trades_quality(self, trades: List[Dict]) -> float:
        """Calculate data quality score for trades data"""
        try:
            if not trades:
                return 0.0

            score = 1.0

            # Check if trades have required fields
            required_fields = ["blockUnixTime", "txHash", "source", "tokenAmount"]
            for trade in trades[:10]:  # Check first 10 trades
                missing_fields = [
                    field for field in required_fields if field not in trade
                ]
                if missing_fields:
                    score -= 0.1

            # Check timestamp freshness
            if trades:
                latest_trade = trades[0]
                if "blockUnixTime" in latest_trade:
                    trade_time = datetime.fromtimestamp(latest_trade["blockUnixTime"])
                    age_hours = (datetime.utcnow() - trade_time).total_seconds() / 3600
                    if age_hours > 24:  # Trades older than 24 hours
                        score -= 0.3

            return max(0.0, score)

        except Exception as e:
            logger.error(f"Error calculating trades quality: {e}")
            return 0.0

    def _calculate_liquidity_quality(self, liquidity_info: Dict) -> float:
        """Calculate data quality score for liquidity data"""
        try:
            if not liquidity_info:
                return 0.0

            score = 1.0

            # Check if liquidity info has required fields
            required_fields = ["liquidity", "volume24h", "priceChange24h"]
            missing_fields = [
                field for field in required_fields if field not in liquidity_info
            ]

            if missing_fields:
                score -= 0.3 * len(missing_fields)

            # Check if liquidity value is reasonable
            if "liquidity" in liquidity_info:
                liquidity = liquidity_info["liquidity"]
                if liquidity <= 0:
                    score -= 0.5

            return max(0.0, score)

        except Exception as e:
            logger.error(f"Error calculating liquidity quality: {e}")
            return 0.0

    def get_stored_trades(
        self, token_address: str, chain: str = "solana", limit: int = 100
    ) -> List[Dict]:
        """Get stored trades data"""
        key = f"{chain}:{token_address}"
        if key not in self.trades_data:
            return []

        trades_list = list(self.trades_data[key])
        return trades_list[-limit:] if limit else trades_list

    def get_stored_liquidity(self, token_address: str, chain: str = "solana") -> Dict:
        """Get stored liquidity data"""
        key = f"{chain}:{token_address}"
        return self.liquidity_data.get(key, {})

    def get_stored_price(self, token_address: str, chain: str = "solana") -> Dict:
        """Get stored price data"""
        key = f"{chain}:{token_address}"
        return self.price_data.get(key, {})

    def get_latency_stats(self) -> Dict:
        """Get API latency statistics"""
        return self.latency_stats

    def get_connection_status(self) -> Dict:
        """Get connection status"""
        return self.connection_status

    def get_data_quality_scores(self) -> Dict:
        """Get data quality scores"""
        return self.data_quality_scores

    def get_rate_limit_status(self) -> Dict:
        """Get rate limiting status"""
        return {
            "requests_made": self.rate_limiter["requests_made"],
            "daily_limit": self.rate_limiter["daily_limit"],
            "remaining": self.rate_limiter["daily_limit"]
            - self.rate_limiter["requests_made"],
            "reset_date": self.rate_limiter["last_reset"].isoformat(),
        }

    async def close(self):
        """Close HTTP session and cleanup"""
        try:
            if self.session:
                await self.session.close()

            logger.info("Closed DEX connector")

        except Exception as e:
            logger.error(f"Error closing DEX connector: {e}")

    def __repr__(self):
        connected = self.connection_status.get("birdeye", {}).get("connected", False)
        requests_used = self.rate_limiter["requests_made"]
        return f"DEXConnector(connected={connected}, requests_used={requests_used}/{self.rate_limiter['daily_limit']})"
