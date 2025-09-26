"""
Data Synchronization Manager
Manages data synchronization between CEX and DEX sources with latency compensation
"""
import asyncio
from typing import Dict, List, Callable, Optional, Any, Tuple
from loguru import logger
import time
from datetime import datetime, timedelta
from collections import deque
import statistics
from config.logging_config import get_logger
from src.data.cex_connector import CEXConnector
from src.data.dex_connector import DEXConnector

logger = get_logger("data.sync_manager")

class DataSyncManager:
    """
    Manages synchronization of data from multiple sources
    Handles latency compensation and data quality monitoring
    """
    
    def __init__(self):
        """Initialize sync manager"""
        self.sync_tasks = {}
        self.connectors = {}
        self.sync_intervals = {
            'orderbook': 1,      # 1 second for orderbook updates
            'trades': 5,         # 5 seconds for trades
            'liquidity': 30,     # 30 seconds for liquidity
            'price': 10          # 10 seconds for price updates
        }
        
        # Performance tracking
        self.latency_stats = {}
        self.data_quality_scores = {}
        self.sync_health = {}
        
        # Data storage with timestamps
        self.synchronized_data = {
            'orderbooks': {},
            'trades': {},
            'liquidity': {},
            'prices': {}
        }
        
        # Latency compensation
        self.latency_compensation = {
            'enabled': True,
            'max_compensation_ms': 1000,  # Max 1 second compensation
            'compensation_history': deque(maxlen=100)
        }
        
        # Data freshness tracking
        self.data_freshness = {}
        self.stale_data_threshold = 60  # 60 seconds
        
        logger.info("Data Sync Manager initialized")
    
    def add_connector(self, name: str, connector):
        """
        Add a data connector to the sync manager
        
        Args:
            name: Connector name (e.g., 'binance_cex', 'birdeye_dex')
            connector: Connector instance (CEXConnector or DEXConnector)
        """
        self.connectors[name] = connector
        self.sync_health[name] = {
            'status': 'inactive',
            'last_sync': None,
            'error_count': 0,
            'success_count': 0
        }
        logger.info(f"Added connector: {name}")
    
    async def start_sync(self, symbol: str, data_types: List[str] = None):
        """
        Start data synchronization for a symbol
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            data_types: List of data types to sync ['orderbook', 'trades', 'liquidity', 'price']
        """
        if data_types is None:
            data_types = ['orderbook', 'trades', 'price']
        
        logger.info(f"Starting sync for {symbol} - data types: {data_types}")
        
        # Create sync tasks for each data type
        for data_type in data_types:
            task_key = f"{symbol}_{data_type}"
            
            if task_key not in self.sync_tasks:
                self.sync_tasks[task_key] = asyncio.create_task(
                    self._sync_loop(symbol, data_type)
                )
                logger.info(f"Started sync task: {task_key}")
        
        # Initialize data storage
        if symbol not in self.synchronized_data['orderbooks']:
            self.synchronized_data['orderbooks'][symbol] = {}
            self.synchronized_data['trades'][symbol] = {}
            self.synchronized_data['liquidity'][symbol] = {}
            self.synchronized_data['prices'][symbol] = {}
    
    async def _sync_loop(self, symbol: str, data_type: str):
        """Main synchronization loop for a symbol and data type"""
        task_key = f"{symbol}_{data_type}"
        interval = self.sync_intervals.get(data_type, 10)
        
        logger.info(f"Starting sync loop: {task_key} (interval: {interval}s)")
        
        while task_key in self.sync_tasks:
            try:
                start_time = time.time()
                
                # Sync data from all connectors
                sync_results = await self._sync_data_type(symbol, data_type)
                
                # Calculate sync latency
                sync_latency = (time.time() - start_time) * 1000
                self._record_sync_latency(task_key, sync_latency)
                
                # Process and store synchronized data
                if sync_results:
                    await self._process_sync_results(symbol, data_type, sync_results)
                
                # Update sync health
                self._update_sync_health(task_key, True)
                
                logger.debug(f"Sync completed: {task_key} - {sync_latency:.2f}ms")
                
                # Wait for next sync
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in sync loop {task_key}: {e}")
                self._update_sync_health(task_key, False)
                await asyncio.sleep(interval)  # Continue despite errors
    
    async def _sync_data_type(self, symbol: str, data_type: str) -> Dict[str, Any]:
        """
        Synchronize specific data type from all connectors
        
        Args:
            symbol: Trading pair symbol
            data_type: Type of data to sync
            
        Returns:
            Dictionary of connector results
        """
        results = {}
        
        for connector_name, connector in self.connectors.items():
            try:
                start_time = time.time()
                
                # Get data based on type and connector
                if data_type == 'orderbook' and hasattr(connector, 'get_orderbook'):
                    data = connector.get_orderbook(symbol)
                elif data_type == 'trades':
                    if hasattr(connector, 'get_trades'):
                        data = connector.get_trades(symbol, limit=50)
                    elif hasattr(connector, 'get_stored_trades'):
                        data = connector.get_stored_trades(symbol, limit=50)
                    else:
                        data = None
                elif data_type == 'price':
                    if hasattr(connector, 'get_stored_price'):
                        data = connector.get_stored_price(symbol)
                    else:
                        data = None
                elif data_type == 'liquidity':
                    if hasattr(connector, 'get_stored_liquidity'):
                        data = connector.get_stored_liquidity(symbol)
                    else:
                        data = None
                else:
                    data = None
                
                # Record latency
                latency = (time.time() - start_time) * 1000
                
                if data:
                    results[connector_name] = {
                        'data': data,
                        'timestamp': datetime.utcnow(),
                        'latency_ms': latency,
                        'connector_type': type(connector).__name__
                    }
                    
                    logger.debug(f"Got {data_type} from {connector_name}: {latency:.2f}ms")
                
            except Exception as e:
                logger.error(f"Error getting {data_type} from {connector_name}: {e}")
                continue
        
        return results
    
    async def _process_sync_results(self, symbol: str, data_type: str, results: Dict[str, Any]):
        """
        Process and store synchronized data with latency compensation
        
        Args:
            symbol: Trading pair symbol
            data_type: Type of data
            results: Sync results from connectors
        """
        if not results:
            return
        
        # Apply latency compensation
        compensated_results = self._apply_latency_compensation(results)
        
        # Calculate data quality scores
        quality_scores = self._calculate_sync_quality(results)
        
        # Store synchronized data
        storage_key = f"{symbol}_{data_type}"
        
        self.synchronized_data[f"{data_type}s"][symbol] = {
            'data': compensated_results,
            'quality_scores': quality_scores,
            'sync_timestamp': datetime.utcnow(),
            'source_count': len(results)
        }
        
        # Update data freshness
        self.data_freshness[storage_key] = datetime.utcnow()
        
        # Store quality scores
        self.data_quality_scores[storage_key] = {
            'overall_quality': statistics.mean(quality_scores.values()) if quality_scores else 0.0,
            'source_qualities': quality_scores,
            'timestamp': datetime.utcnow()
        }
    
    def _apply_latency_compensation(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply latency compensation to synchronized data
        
        Args:
            results: Raw sync results
            
        Returns:
            Compensated results
        """
        if not self.latency_compensation['enabled']:
            return results
        
        compensated = {}
        
        for connector_name, result in results.items():
            latency_ms = result.get('latency_ms', 0)
            
            # Only compensate if latency is within reasonable bounds
            if latency_ms <= self.latency_compensation['max_compensation_ms']:
                # Calculate compensation offset
                compensation_offset = timedelta(milliseconds=latency_ms)
                
                # Apply compensation to timestamp
                compensated_timestamp = result['timestamp'] + compensation_offset
                
                compensated[connector_name] = {
                    **result,
                    'compensated_timestamp': compensated_timestamp,
                    'original_timestamp': result['timestamp'],
                    'compensation_ms': latency_ms
                }
                
                # Record compensation
                self.latency_compensation['compensation_history'].append(latency_ms)
            else:
                # Don't compensate excessive latency
                compensated[connector_name] = result
                logger.warning(f"Excessive latency {latency_ms}ms from {connector_name}, skipping compensation")
        
        return compensated
    
    def _calculate_sync_quality(self, results: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate data quality scores for sync results
        
        Args:
            results: Sync results
            
        Returns:
            Quality scores by connector
        """
        quality_scores = {}
        
        for connector_name, result in results.items():
            score = 1.0
            
            # Check data availability
            if not result.get('data'):
                score = 0.0
            else:
                # Check latency (lower is better)
                latency = result.get('latency_ms', 0)
                if latency > 1000:  # > 1 second
                    score -= 0.3
                elif latency > 500:  # > 500ms
                    score -= 0.1
                
                # Check timestamp freshness
                timestamp = result.get('timestamp')
                if timestamp:
                    age_seconds = (datetime.utcnow() - timestamp).total_seconds()
                    if age_seconds > 30:  # > 30 seconds old
                        score -= 0.4
                    elif age_seconds > 10:  # > 10 seconds old
                        score -= 0.2
            
            quality_scores[connector_name] = max(0.0, score)
        
        return quality_scores
    
    def _record_sync_latency(self, task_key: str, latency_ms: float):
        """Record synchronization latency"""
        if task_key not in self.latency_stats:
            self.latency_stats[task_key] = {
                'measurements': deque(maxlen=100),
                'avg_latency': 0,
                'min_latency': float('inf'),
                'max_latency': 0,
                'last_update': None
            }
        
        stats = self.latency_stats[task_key]
        stats['measurements'].append(latency_ms)
        stats['min_latency'] = min(stats['min_latency'], latency_ms)
        stats['max_latency'] = max(stats['max_latency'], latency_ms)
        stats['avg_latency'] = statistics.mean(stats['measurements'])
        stats['last_update'] = datetime.utcnow()
    
    def _update_sync_health(self, task_key: str, success: bool):
        """Update sync health status"""
        # Extract connector name from task key
        connector_name = task_key.split('_')[0] if '_' in task_key else task_key
        
        if connector_name in self.sync_health:
            health = self.sync_health[connector_name]
            health['last_sync'] = datetime.utcnow()
            
            if success:
                health['success_count'] += 1
                health['status'] = 'active'
            else:
                health['error_count'] += 1
                if health['error_count'] > 5:
                    health['status'] = 'error'
    
    def get_synchronized_data(self, symbol: str, data_type: str) -> Optional[Dict]:
        """
        Get synchronized data for a symbol and data type
        
        Args:
            symbol: Trading pair symbol
            data_type: Type of data ('orderbook', 'trades', 'liquidity', 'price')
            
        Returns:
            Synchronized data or None
        """
        storage_key = f"{data_type}s"
        if storage_key in self.synchronized_data and symbol in self.synchronized_data[storage_key]:
            return self.synchronized_data[storage_key][symbol]
        return None
    
    def get_data_quality(self, symbol: str = None) -> Dict:
        """
        Get data quality scores
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            Data quality information
        """
        if symbol:
            return {k: v for k, v in self.data_quality_scores.items() if symbol in k}
        return self.data_quality_scores
    
    def get_sync_health(self) -> Dict:
        """Get synchronization health status"""
        return self.sync_health
    
    def get_latency_stats(self) -> Dict:
        """Get synchronization latency statistics"""
        return self.latency_stats
    
    def get_data_freshness(self, symbol: str = None) -> Dict:
        """
        Get data freshness information
        
        Args:
            symbol: Optional symbol filter
            
        Returns:
            Data freshness timestamps
        """
        if symbol:
            return {k: v for k, v in self.data_freshness.items() if symbol in k}
        return self.data_freshness
    
    def is_data_stale(self, symbol: str, data_type: str) -> bool:
        """
        Check if data is stale
        
        Args:
            symbol: Trading pair symbol
            data_type: Type of data
            
        Returns:
            True if data is stale
        """
        key = f"{symbol}_{data_type}"
        if key not in self.data_freshness:
            return True
        
        age_seconds = (datetime.utcnow() - self.data_freshness[key]).total_seconds()
        return age_seconds > self.stale_data_threshold
    
    def get_compensation_stats(self) -> Dict:
        """Get latency compensation statistics"""
        history = list(self.latency_compensation['compensation_history'])
        
        if not history:
            return {
                'enabled': self.latency_compensation['enabled'],
                'compensations_applied': 0,
                'avg_compensation_ms': 0,
                'max_compensation_ms': 0
            }
        
        return {
            'enabled': self.latency_compensation['enabled'],
            'compensations_applied': len(history),
            'avg_compensation_ms': statistics.mean(history),
            'max_compensation_ms': max(history),
            'min_compensation_ms': min(history)
        }
    
    async def stop_sync(self, symbol: str = None, data_type: str = None):
        """
        Stop synchronization tasks
        
        Args:
            symbol: Optional symbol filter
            data_type: Optional data type filter
        """
        tasks_to_stop = []
        
        for task_key, task in self.sync_tasks.items():
            should_stop = True
            
            if symbol and symbol not in task_key:
                should_stop = False
            
            if data_type and data_type not in task_key:
                should_stop = False
            
            if should_stop:
                tasks_to_stop.append(task_key)
        
        for task_key in tasks_to_stop:
            task = self.sync_tasks.pop(task_key)
            task.cancel()
            logger.info(f"Stopped sync task: {task_key}")
        
        # Wait for tasks to complete
        if tasks_to_stop:
            await asyncio.sleep(0.1)
    
    async def stop_all_sync(self):
        """Stop all synchronization tasks"""
        logger.info("Stopping all sync tasks...")
        
        for task_key, task in self.sync_tasks.items():
            task.cancel()
        
        self.sync_tasks.clear()
        
        # Wait for cleanup
        await asyncio.sleep(0.1)
        
        logger.info("All sync tasks stopped")
    
    def get_sync_summary(self) -> Dict:
        """Get comprehensive sync status summary"""
        active_tasks = len(self.sync_tasks)
        total_connectors = len(self.connectors)
        
        # Calculate overall health
        healthy_connectors = sum(1 for health in self.sync_health.values() 
                               if health['status'] == 'active')
        
        # Calculate average quality
        if self.data_quality_scores:
            avg_quality = statistics.mean(
                score['overall_quality'] for score in self.data_quality_scores.values()
            )
        else:
            avg_quality = 0.0
        
        # Calculate average latency
        if self.latency_stats:
            avg_latency = statistics.mean(
                stats['avg_latency'] for stats in self.latency_stats.values()
            )
        else:
            avg_latency = 0.0
        
        return {
            'active_tasks': active_tasks,
            'total_connectors': total_connectors,
            'healthy_connectors': healthy_connectors,
            'health_percentage': (healthy_connectors / total_connectors * 100) if total_connectors > 0 else 0,
            'average_quality': avg_quality,
            'average_latency_ms': avg_latency,
            'compensation_enabled': self.latency_compensation['enabled'],
            'data_types_synced': len(set(key.split('_')[-1] for key in self.sync_tasks.keys())),
            'symbols_synced': len(set('_'.join(key.split('_')[:-1]) for key in self.sync_tasks.keys()))
        }
    
    def __repr__(self):
        summary = self.get_sync_summary()
        return f"DataSyncManager(tasks={summary['active_tasks']}, connectors={summary['total_connectors']}, health={summary['health_percentage']:.1f}%)"
