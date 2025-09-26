# ATS Implementation Guide - Phase B2: ML Pipeline

## Overview

**Phase B2** implements the machine learning pipeline for advanced signal prediction. This phase transforms the rule-based system into an ML-enhanced trading system with predictive capabilities.

**Duration**: 5-8 weeks  
**Prerequisites**: Completed Phase A & B1, ML knowledge, historical data access, minimum 1,000 labeled signals  
**Tasks Covered**: 20-26

---

## Task 20: Feature Engineering Module
**Objective**: Create comprehensive feature engineering system for ML model training.

### Implementation Steps

#### 20.1 Create FeatureEngineer Class Structure
Create `src/ml/feature_engineer.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from loguru import logger

class FeatureEngineer:
    def __init__(self, lookback_periods: List[int] = [5, 15, 30, 60]):
        self.lookback_periods = lookback_periods
        self.scalers = {}
        self.feature_importance = {}
        self.feature_definitions = {
            'price_features': ['price_change', 'volatility', 'momentum'],
            'volume_features': ['volume_change', 'volume_ma', 'volume_spike'],
            'orderbook_features': ['spread', 'depth_imbalance', 'order_flow'],
            'technical_features': ['rsi', 'macd', 'bollinger_bands'],
            'market_features': ['market_regime', 'correlation', 'beta']
        }
        
    def engineer_features(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        # Create comprehensive feature set from raw market data
        pass
        
    def create_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        # Create price-based features
        pass
        
    def create_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        # Create volume-based features
        pass
        
    def create_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Create technical analysis indicators
        pass
```

#### 20.2 Implement Price-Based Features
- **Price Changes**: Returns over multiple timeframes (1min, 5min, 15min, 1h)
- **Volatility Measures**: Rolling standard deviation, GARCH volatility
- **Momentum Indicators**: Price momentum, acceleration, trend strength
- **Price Patterns**: Support/resistance levels, breakout indicators

#### 20.3 Add Volume-Based Features
- **Volume Patterns**: Volume moving averages, volume spikes
- **Volume-Price Relationship**: VWAP, volume-weighted returns
- **Liquidity Metrics**: Bid-ask spread, market depth
- **Flow Indicators**: Money flow index, accumulation/distribution

#### 20.4 Create Technical Indicators
- **Trend Indicators**: Moving averages, MACD, ADX
- **Oscillators**: RSI, Stochastic, Williams %R
- **Volatility Indicators**: Bollinger Bands, ATR
- **Custom Indicators**: Proprietary technical signals

### Key Implementation Details
- Use vectorized operations for performance
- Implement proper handling of missing data
- Add feature scaling and normalization
- Consider look-ahead bias prevention

### Testing Instructions

#### 1. Basic Feature Engineering Test
```python
# Create test file: test_feature_engineer.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.ml.feature_engineer import FeatureEngineer

def test_basic_feature_engineering():
    engineer = FeatureEngineer()
    
    # Create sample market data
    dates = pd.date_range(start='2023-01-01', periods=1000, freq='1min')
    np.random.seed(42)
    
    raw_data = pd.DataFrame({
        'timestamp': dates,
        'open': 50000 + np.cumsum(np.random.randn(1000) * 10),
        'high': lambda x: x['open'] + np.abs(np.random.randn(1000) * 5),
        'low': lambda x: x['open'] - np.abs(np.random.randn(1000) * 5),
        'close': lambda x: x['open'] + np.random.randn(1000) * 8,
        'volume': np.random.exponential(1000, 1000)
    })
    
    # Apply lambda functions
    raw_data['high'] = raw_data['open'] + np.abs(np.random.randn(1000) * 5)
    raw_data['low'] = raw_data['open'] - np.abs(np.random.randn(1000) * 5)
    raw_data['close'] = raw_data['open'] + np.random.randn(1000) * 8
    
    # Engineer features
    features = engineer.engineer_features(raw_data)
    print(f"✓ Feature engineering completed: {features.shape}")
    
    # Check feature categories
    expected_categories = ['price_features', 'volume_features', 'technical_features']
    for category in expected_categories:
        category_features = [col for col in features.columns if category.split('_')[0] in col]
        assert len(category_features) > 0, f"Should have {category} features"
        print(f"✓ {category}: {len(category_features)} features")
    
    # Check for NaN handling
    nan_count = features.isnull().sum().sum()
    print(f"✓ NaN values handled: {nan_count} remaining")
    assert nan_count < len(features) * 0.1, "Should have minimal NaN values"
```

#### 2. Price Features Test
```python
def test_price_features():
    engineer = FeatureEngineer()
    
    # Create price data with known patterns
    dates = pd.date_range(start='2023-01-01', periods=100, freq='1min')
    
    # Create trending price data
    trend = np.linspace(50000, 51000, 100)  # 2% uptrend
    noise = np.random.randn(100) * 10
    
    df = pd.DataFrame({
        'timestamp': dates,
        'close': trend + noise,
        'high': trend + noise + np.abs(np.random.randn(100) * 5),
        'low': trend + noise - np.abs(np.random.randn(100) * 5),
        'volume': np.random.exponential(1000, 100)
    })
    
    price_features = engineer.create_price_features(df)
    print(f"✓ Price features created: {price_features.columns.tolist()}")
    
    # Check for expected features
    expected_features = ['price_change_1', 'price_change_5', 'volatility_15', 'momentum_30']
    for feature in expected_features:
        matching_features = [col for col in price_features.columns if feature.split('_')[0] in col]
        assert len(matching_features) > 0, f"Should have {feature} type features"
    
    # Check trend detection
    if 'momentum_5' in price_features.columns:
        avg_momentum = price_features['momentum_5'].mean()
        print(f"✓ Average momentum: {avg_momentum:.4f}")
        assert avg_momentum > 0, "Should detect upward trend"
```

#### 3. Technical Indicators Test
```python
def test_technical_indicators():
    engineer = FeatureEngineer()
    
    # Create data suitable for technical analysis
    dates = pd.date_range(start='2023-01-01', periods=200, freq='1min')
    
    # Create oscillating price pattern
    base_price = 50000
    oscillation = 1000 * np.sin(np.linspace(0, 4*np.pi, 200))
    trend = np.linspace(0, 500, 200)
    noise = np.random.randn(200) * 20
    
    df = pd.DataFrame({
        'timestamp': dates,
        'close': base_price + oscillation + trend + noise,
        'high': base_price + oscillation + trend + noise + np.abs(np.random.randn(200) * 10),
        'low': base_price + oscillation + trend + noise - np.abs(np.random.randn(200) * 10),
        'volume': np.random.exponential(1000, 200)
    })
    
    technical_features = engineer.create_technical_indicators(df)
    print(f"✓ Technical indicators created: {technical_features.columns.tolist()}")
    
    # Check for standard indicators
    expected_indicators = ['rsi', 'macd', 'bollinger', 'sma', 'ema']
    for indicator in expected_indicators:
        matching_indicators = [col for col in technical_features.columns if indicator in col.lower()]
        assert len(matching_indicators) > 0, f"Should have {indicator} indicators"
        print(f"✓ {indicator} indicators: {len(matching_indicators)}")
    
    # Check RSI bounds
    if 'rsi_14' in technical_features.columns:
        rsi_values = technical_features['rsi_14'].dropna()
        assert rsi_values.min() >= 0 and rsi_values.max() <= 100, "RSI should be between 0 and 100"
        print(f"✓ RSI range: {rsi_values.min():.1f} - {rsi_values.max():.1f}")
```

#### 4. Feature Scaling Test
```python
def test_feature_scaling():
    engineer = FeatureEngineer()
    
    # Create features with different scales
    dates = pd.date_range(start='2023-01-01', periods=100, freq='1min')
    
    features = pd.DataFrame({
        'timestamp': dates,
        'price_change': np.random.randn(100) * 0.01,  # Small values (percentages)
        'volume': np.random.exponential(10000, 100),   # Large values
        'rsi': np.random.uniform(20, 80, 100),         # Bounded values
        'volatility': np.random.exponential(0.02, 100) # Small positive values
    })
    
    # Apply scaling
    scaled_features = engineer.scale_features(features)
    print(f"✓ Features scaled: {scaled_features.shape}")
    
    # Check scaling results
    for col in ['price_change', 'volume', 'rsi', 'volatility']:
        if col in scaled_features.columns:
            col_mean = scaled_features[col].mean()
            col_std = scaled_features[col].std()
            print(f"✓ {col}: mean={col_mean:.3f}, std={col_std:.3f}")
            
            # Should be approximately standardized
            assert abs(col_mean) < 0.1, f"{col} should have mean near 0"
            assert abs(col_std - 1.0) < 0.2, f"{col} should have std near 1"
```

### Expected Test Results
- Feature engineering should create comprehensive feature sets
- Price features should capture market dynamics correctly
- Technical indicators should be calculated accurately
- Feature scaling should normalize different value ranges

### Post-Test Actions
```bash
git add src/ml/feature_engineer.py
git add tests/test_feature_engineer.py
git commit -m "feat: implement comprehensive feature engineering for ML pipeline"
```

### Progress Update
Mark Task 20 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 21: Data Labeling System
**Objective**: Create system for labeling historical data with forward-looking returns and signal outcomes.

### Implementation Steps

#### 21.1 Create DataLabeler Class Structure
Create `src/ml/data_labeler.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

class DataLabeler:
    def __init__(self, forward_windows: List[int] = [5, 15, 30, 60]):
        self.forward_windows = forward_windows  # minutes
        self.labeling_methods = {
            'return_based': self._label_by_returns,
            'volatility_adjusted': self._label_by_vol_adjusted_returns,
            'quantile_based': self._label_by_quantiles,
            'signal_outcome': self._label_by_signal_outcome
        }
        self.label_thresholds = {
            'strong_buy': 0.02,    # 2% return threshold
            'buy': 0.005,          # 0.5% return threshold
            'hold': 0.002,         # 0.2% return threshold
            'sell': -0.005,        # -0.5% return threshold
            'strong_sell': -0.02   # -2% return threshold
        }
        
    def label_data(self, df: pd.DataFrame, method: str = 'return_based') -> pd.DataFrame:
        # Label data using specified method
        pass
        
    def _label_by_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        # Label based on forward-looking returns
        pass
        
    def _label_by_signal_outcome(self, df: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
        # Label based on actual signal performance
        pass
        
    def calculate_label_distribution(self, labels: pd.Series) -> Dict:
        # Calculate distribution of labels for analysis
        pass
```

#### 21.2 Implement Return-Based Labeling
- **Forward Returns**: Calculate returns over multiple future timeframes
- **Risk-Adjusted Returns**: Adjust returns for volatility and market conditions
- **Threshold-Based Classification**: Convert returns to discrete labels
- **Multi-Timeframe Labels**: Create labels for different prediction horizons

#### 21.3 Add Signal Outcome Labeling
- **Historical Signal Tracking**: Match historical signals with outcomes
- **Performance Attribution**: Label based on actual trading performance
- **Slippage Adjustment**: Account for execution costs in labeling
- **Risk-Adjusted Outcomes**: Consider risk in outcome evaluation

#### 21.4 Create Quality Control
- **Label Consistency**: Ensure consistent labeling across timeframes
- **Outlier Detection**: Identify and handle extreme market events
- **Data Leakage Prevention**: Ensure no future information in features
- **Balance Analysis**: Monitor label distribution for model training

### Key Implementation Details
- Prevent look-ahead bias in labeling process
- Handle market gaps and trading halts properly
- Consider transaction costs in return calculations
- Implement proper data alignment for features and labels

### Testing Instructions

#### 1. Return-Based Labeling Test
```python
# Create test file: test_data_labeler.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.ml.data_labeler import DataLabeler

def test_return_based_labeling():
    labeler = DataLabeler(forward_windows=[5, 15, 30])
    
    # Create price data with known patterns
    dates = pd.date_range(start='2023-01-01', periods=200, freq='1min')
    
    # Create data with clear up/down movements
    prices = []
    base_price = 50000
    
    for i in range(200):
        if i < 50:
            price = base_price + i * 10  # Uptrend
        elif i < 100:
            price = base_price + 500 - (i-50) * 5  # Downtrend
        elif i < 150:
            price = base_price + 250 + (i-100) * 8  # Strong uptrend
        else:
            price = base_price + 650 + np.random.randn() * 5  # Sideways
        
        prices.append(price)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'close': prices
    })
    
    # Apply labeling
    labeled_data = labeler.label_data(df, method='return_based')
    print(f"✓ Data labeled: {labeled_data.shape}")
    
    # Check label columns
    expected_columns = ['label_5min', 'label_15min', 'label_30min']
    for col in expected_columns:
        assert col in labeled_data.columns, f"Should have {col} column"
    
    # Check label distribution
    label_dist = labeler.calculate_label_distribution(labeled_data['label_5min'])
    print(f"✓ Label distribution: {label_dist}")
    
    # Should have different label types
    assert len(label_dist) > 1, "Should have multiple label types"
    
    # Check uptrend period labels (first 50 points)
    uptrend_labels = labeled_data['label_5min'].iloc[:45]  # Avoid edge effects
    buy_labels = sum(1 for label in uptrend_labels if label in ['buy', 'strong_buy'])
    print(f"✓ Buy labels in uptrend: {buy_labels}/{len(uptrend_labels)}")
    
    # Should have more buy labels in uptrend
    assert buy_labels > len(uptrend_labels) * 0.3, "Should have buy labels in uptrend period"
```

#### 2. Signal Outcome Labeling Test
```python
def test_signal_outcome_labeling():
    labeler = DataLabeler()
    
    # Create market data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='1min')
    df = pd.DataFrame({
        'timestamp': dates,
        'close': 50000 + np.cumsum(np.random.randn(100) * 10)
    })
    
    # Create sample signals with known outcomes
    signals = pd.DataFrame({
        'timestamp': dates[::20],  # Every 20 minutes
        'signal_type': ['BUY', 'SELL', 'BUY', 'SELL', 'BUY'],
        'entry_price': [50000, 50100, 49900, 50200, 50050],
        'exit_price': [50150, 50050, 50000, 50100, 50200],  # Mix of wins/losses
        'realized_pnl': [150, 50, 100, 100, 150]
    })
    
    # Apply signal outcome labeling
    labeled_data = labeler._label_by_signal_outcome(df, signals)
    print(f"✓ Signal outcome labeling completed: {labeled_data.shape}")
    
    # Check for signal outcome labels
    signal_labels = labeled_data['signal_outcome'].dropna()
    print(f"✓ Signal outcome labels: {len(signal_labels)}")
    
    assert len(signal_labels) > 0, "Should have signal outcome labels"
    
    # Check label types
    unique_labels = signal_labels.unique()
    print(f"✓ Unique signal outcome labels: {unique_labels}")
    
    # Should have both positive and negative outcomes
    assert len(unique_labels) > 1, "Should have different outcome types"
```

#### 3. Label Quality Control Test
```python
def test_label_quality_control():
    labeler = DataLabeler()
    
    # Create data with extreme events
    dates = pd.date_range(start='2023-01-01', periods=100, freq='1min')
    
    prices = np.random.randn(100).cumsum() * 10 + 50000
    # Add extreme event
    prices[50] = prices[49] * 1.1  # 10% jump
    prices[75] = prices[74] * 0.9  # 10% drop
    
    df = pd.DataFrame({
        'timestamp': dates,
        'close': prices
    })
    
    # Apply labeling
    labeled_data = labeler.label_data(df, method='return_based')
    
    # Check for outlier handling
    returns_5min = labeled_data['return_5min'].dropna()
    extreme_returns = returns_5min[abs(returns_5min) > 0.05]  # >5% returns
    
    print(f"✓ Extreme returns detected: {len(extreme_returns)}")
    print(f"✓ Extreme return values: {extreme_returns.values}")
    
    # Should detect extreme events
    assert len(extreme_returns) >= 2, "Should detect extreme price movements"
    
    # Check label distribution balance
    label_dist = labeler.calculate_label_distribution(labeled_data['label_5min'])
    print(f"✓ Label distribution: {label_dist}")
    
    # Check for reasonable balance (no single label > 80%)
    max_label_pct = max(label_dist.values()) / sum(label_dist.values())
    print(f"✓ Maximum label percentage: {max_label_pct:.2%}")
    
    assert max_label_pct < 0.8, "Labels should be reasonably balanced"
```

#### 4. Data Leakage Prevention Test
```python
def test_data_leakage_prevention():
    labeler = DataLabeler(forward_windows=[5, 15])
    
    # Create sequential data
    dates = pd.date_range(start='2023-01-01', periods=50, freq='1min')
    df = pd.DataFrame({
        'timestamp': dates,
        'close': range(50000, 50050),  # Strictly increasing
        'feature_1': range(100, 150),   # Feature that increases with price
    })
    
    # Apply labeling
    labeled_data = labeler.label_data(df, method='return_based')
    
    # Check that labels are based on future data only
    for i in range(10, 40):  # Check middle section
        current_price = labeled_data.iloc[i]['close']
        future_price_5min = labeled_data.iloc[min(i+5, len(labeled_data)-1)]['close']
        
        expected_return = (future_price_5min - current_price) / current_price
        
        # Label should reflect future return direction
        label = labeled_data.iloc[i]['label_5min']
        
        if expected_return > 0.001:  # Positive return
            assert label in ['buy', 'strong_buy', 'hold'], f"Positive return should have buy/hold label, got {label}"
        elif expected_return < -0.001:  # Negative return
            assert label in ['sell', 'strong_sell', 'hold'], f"Negative return should have sell/hold label, got {label}"
    
    print("✓ Data leakage prevention test passed")
    
    # Ensure no future information in current row
    for i in range(len(labeled_data) - 15):
        current_features = labeled_data.iloc[i][['close', 'feature_1']]
        # Features should only use current and past information
        assert not pd.isna(current_features['close']), "Current features should be available"
```

### Expected Test Results
- Return-based labeling should create meaningful labels
- Signal outcome labeling should match historical performance
- Quality control should detect and handle extreme events
- Data leakage prevention should ensure proper temporal alignment

### Post-Test Actions
```bash
git add src/ml/data_labeler.py
git add tests/test_data_labeler.py
git commit -m "feat: implement data labeling system with outcome tracking"
```

### Progress Update
Mark Task 21 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 22: Free Historical Data Integration
**Objective**: Integrate free historical data sources (CryptoCompare, Binance, CoinGecko) for model training.

### Implementation Steps

#### 22.1 Create HistoricalDataManager Class Structure
Create `src/data/historical_data.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import aiohttp
import ccxt
from loguru import logger
import time

class HistoricalDataManager:
    def __init__(self):
        self.data_sources = {
            'cryptocompare': {
                'base_url': 'https://min-api.cryptocompare.com/data',
                'rate_limit': 100,  # requests per second
                'api_key': None     # Optional API key for higher limits
            },
            'binance': {
                'base_url': 'https://api.binance.com/api/v3',
                'rate_limit': 1200,  # requests per minute
                'weight_limits': True
            },
            'coingecko': {
                'base_url': 'https://api.coingecko.com/api/v3',
                'rate_limit': 50,   # requests per minute (free tier)
                'demo_plan': True
            }
        }
        self.rate_limiters = {}
        self.data_cache = {}
        
    async def fetch_historical_data(self, symbol: str, timeframe: str, 
                                  start_date: datetime, end_date: datetime,
                                  source: str = 'binance') -> pd.DataFrame:
        # Fetch historical OHLCV data from specified source
        pass
        
    async def fetch_cryptocompare_data(self, symbol: str, timeframe: str,
                                     start_date: datetime, end_date: datetime) -> pd.DataFrame:
        # Fetch data from CryptoCompare API
        pass
        
    async def fetch_binance_data(self, symbol: str, timeframe: str,
                               start_date: datetime, end_date: datetime) -> pd.DataFrame:
        # Fetch data from Binance public API
        pass
        
    def merge_multiple_sources(self, data_sources: List[pd.DataFrame]) -> pd.DataFrame:
        # Merge and validate data from multiple sources
        pass
```

#### 22.2 Implement CryptoCompare Integration
- **OHLCV Data**: Fetch historical price and volume data
- **Rate Limiting**: Respect free tier limits (100 req/sec)
- **Data Validation**: Validate data quality and completeness
- **Error Handling**: Handle API errors and timeouts gracefully

#### 22.3 Add Binance Public API Integration
- **Kline Data**: Fetch candlestick data from public endpoints
- **Weight Management**: Track API weight usage
- **Batch Requests**: Optimize requests for large date ranges
- **Data Formatting**: Convert to standard format

#### 22.4 Create CoinGecko Integration
- **Market Data**: Fetch historical market data
- **Free Tier Management**: Respect 50 requests/minute limit
- **Data Enrichment**: Add market cap and other metrics
- **Fallback Source**: Use as backup when other sources fail

### Key Implementation Details
- Implement proper rate limiting for each API
- Add data validation and quality checks
- Cache data locally to reduce API calls
- Handle different data formats and time zones

### Testing Instructions

#### 1. CryptoCompare Integration Test
```python
# Create test file: test_historical_data.py
import asyncio
from datetime import datetime, timedelta
from src.data.historical_data import HistoricalDataManager

async def test_cryptocompare_integration():
    manager = HistoricalDataManager()
    
    # Test fetching recent data (small request)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=24)  # 24 hours of data
    
    try:
        data = await manager.fetch_cryptocompare_data(
            symbol='BTC/USDT',
            timeframe='1h',
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"✓ CryptoCompare data fetched: {data.shape}")
        print(f"✓ Data columns: {data.columns.tolist()}")
        
        # Check data structure
        expected_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in expected_columns:
            assert col in data.columns, f"Should have {col} column"
        
        # Check data quality
        assert len(data) > 0, "Should have data points"
        assert not data['close'].isnull().all(), "Should have valid close prices"
        assert (data['high'] >= data['low']).all(), "High should be >= Low"
        assert (data['high'] >= data['close']).all(), "High should be >= Close"
        assert (data['low'] <= data['close']).all(), "Low should be <= Close"
        
        print("✓ CryptoCompare data validation passed")
        
    except Exception as e:
        print(f"⚠️ CryptoCompare test failed (may be rate limited): {e}")

# Run test
asyncio.run(test_cryptocompare_integration())
```

#### 2. Binance Public API Test
```python
async def test_binance_integration():
    manager = HistoricalDataManager()
    
    # Test fetching recent data
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=12)  # 12 hours of data
    
    try:
        data = await manager.fetch_binance_data(
            symbol='BTCUSDT',  # Binance format
            timeframe='1h',
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"✓ Binance data fetched: {data.shape}")
        
        # Check data structure
        expected_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        for col in expected_columns:
            assert col in data.columns, f"Should have {col} column"
        
        # Check data ordering
        assert data['timestamp'].is_monotonic_increasing, "Timestamps should be ordered"
        
        # Check for reasonable values
        assert (data['volume'] >= 0).all(), "Volume should be non-negative"
        assert (data['close'] > 0).all(), "Prices should be positive"
        
        print("✓ Binance data validation passed")
        
    except Exception as e:
        print(f"⚠️ Binance test failed: {e}")
```

#### 3. Multi-Source Data Merging Test
```python
async def test_multi_source_merging():
    manager = HistoricalDataManager()
    
    # Fetch same data from multiple sources
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=6)
    
    data_sources = []
    
    # Try to fetch from multiple sources
    for source in ['binance', 'cryptocompare']:
        try:
            data = await manager.fetch_historical_data(
                symbol='BTC/USDT',
                timeframe='1h',
                start_date=start_date,
                end_date=end_date,
                source=source
            )
            data['source'] = source
            data_sources.append(data)
            print(f"✓ Data from {source}: {data.shape}")
        except Exception as e:
            print(f"⚠️ Failed to fetch from {source}: {e}")
    
    if len(data_sources) >= 2:
        # Test merging
        merged_data = manager.merge_multiple_sources(data_sources)
        print(f"✓ Merged data: {merged_data.shape}")
        
        # Check merge quality
        assert len(merged_data) > 0, "Merged data should not be empty"
        
        # Check for data consistency
        price_diff = merged_data['close'].std() / merged_data['close'].mean()
        print(f"✓ Price consistency (CV): {price_diff:.4f}")
        
        # Should have reasonable consistency between sources
        assert price_diff < 0.1, "Price data should be consistent between sources"
    else:
        print("⚠️ Could not test merging - insufficient data sources")
```

#### 4. Rate Limiting Test
```python
async def test_rate_limiting():
    manager = HistoricalDataManager()
    
    # Test rate limiting with multiple rapid requests
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(hours=1)
    
    start_time = time.time()
    
    # Make multiple requests to test rate limiting
    for i in range(3):
        try:
            data = await manager.fetch_binance_data(
                symbol='BTCUSDT',
                timeframe='1h',
                start_date=start_date,
                end_date=end_date
            )
            print(f"✓ Request {i+1} completed: {data.shape}")
        except Exception as e:
            print(f"⚠️ Request {i+1} failed: {e}")
        
        # Small delay between requests
        await asyncio.sleep(0.5)
    
    total_time = time.time() - start_time
    print(f"✓ Rate limiting test completed in {total_time:.2f}s")
    
    # Should complete without hitting rate limits
    assert total_time < 10, "Should complete quickly with proper rate limiting"
```

### Expected Test Results
- Historical data should be fetched from multiple sources
- Data validation should ensure quality and consistency
- Rate limiting should prevent API violations
- Multi-source merging should provide robust data

### Post-Test Actions
```bash
git add src/data/historical_data.py
git add tests/test_historical_data.py
git commit -m "feat: implement free historical data integration with multiple sources"
```

### Progress Update
Mark Task 22 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 23: ML Model Development
**Objective**: Develop and train machine learning models (LightGBM, XGBoost, Neural Networks) for signal prediction.

### Implementation Steps

#### 23.1 Create MLModelManager Class Structure
Create `src/ml/model_manager.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from datetime import datetime
import joblib
import json
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import lightgbm as lgb
import xgboost as xgb
from loguru import logger

class MLModelManager:
    def __init__(self):
        self.models = {}
        self.model_configs = {
            'lightgbm': {
                'objective': 'multiclass',
                'num_class': 5,  # strong_sell, sell, hold, buy, strong_buy
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.9,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': 0
            },
            'xgboost': {
                'objective': 'multi:softprob',
                'num_class': 5,
                'max_depth': 6,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': 42
            }
        }
        self.feature_importance = {}
        self.model_performance = {}
        
    def train_model(self, X_train: pd.DataFrame, y_train: pd.Series, 
                   model_type: str = 'lightgbm') -> Dict:
        # Train ML model with given data
        pass
        
    def evaluate_model(self, model: Any, X_test: pd.DataFrame, 
                      y_test: pd.Series) -> Dict:
        # Evaluate model performance
        pass
        
    def predict_signals(self, model: Any, features: pd.DataFrame) -> np.ndarray:
        # Generate predictions from trained model
        pass
        
    def save_model(self, model: Any, model_name: str, metadata: Dict):
        # Save trained model with metadata
        pass
```

#### 23.2 Implement LightGBM Integration
- **Gradient Boosting**: Use LightGBM for fast training
- **Feature Importance**: Track feature importance for analysis
- **Hyperparameter Tuning**: Optimize model parameters
- **Cross-Validation**: Use time series cross-validation

#### 23.3 Add XGBoost Support
- **Alternative Algorithm**: Provide XGBoost as alternative
- **Ensemble Methods**: Combine multiple models
- **Regularization**: Prevent overfitting with proper regularization
- **Early Stopping**: Implement early stopping for training

#### 23.4 Create Neural Network Models
- **Deep Learning**: Implement neural networks for complex patterns
- **LSTM Networks**: Use for time series pattern recognition
- **Attention Mechanisms**: Add attention for important features
- **Ensemble Integration**: Combine with tree-based models

### Key Implementation Details
- Use time series cross-validation to prevent data leakage
- Implement proper feature scaling for neural networks
- Add model versioning and metadata tracking
- Consider class imbalance in model training

### Testing Instructions

#### 1. LightGBM Training Test
```python
# Create test file: test_model_manager.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.ml.model_manager import MLModelManager
from sklearn.datasets import make_classification

def test_lightgbm_training():
    manager = MLModelManager()
    
    # Create synthetic training data
    X, y = make_classification(
        n_samples=1000,
        n_features=20,
        n_informative=15,
        n_redundant=5,
        n_classes=5,
        random_state=42
    )
    
    # Convert to DataFrame
    feature_names = [f'feature_{i}' for i in range(20)]
    X_train = pd.DataFrame(X, columns=feature_names)
    y_train = pd.Series(y)
    
    print(f"✓ Training data prepared: {X_train.shape}")
    
    # Train LightGBM model
    training_result = manager.train_model(X_train, y_train, model_type='lightgbm')
    print(f"✓ LightGBM training completed: {training_result}")
    
    # Check training results
    assert 'model' in training_result, "Should return trained model"
    assert 'training_score' in training_result, "Should return training score"
    assert 'feature_importance' in training_result, "Should return feature importance"
    
    # Check model can make predictions
    model = training_result['model']
    predictions = manager.predict_signals(model, X_train.iloc[:10])
    print(f"✓ Predictions shape: {predictions.shape}")
    
    assert predictions.shape[0] == 10, "Should predict for all samples"
    assert predictions.shape[1] == 5, "Should predict 5 classes"
    
    # Check feature importance
    feature_importance = training_result['feature_importance']
    assert len(feature_importance) == 20, "Should have importance for all features"
    print(f"✓ Top 5 important features: {sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]}")
```

#### 2. Model Evaluation Test
```python
def test_model_evaluation():
    manager = MLModelManager()
    
    # Create train/test split
    X, y = make_classification(
        n_samples=1000,
        n_features=15,
        n_informative=10,
        n_classes=5,
        random_state=42
    )
    
    # Split data
    split_idx = 800
    X_train = pd.DataFrame(X[:split_idx], columns=[f'feature_{i}' for i in range(15)])
    y_train = pd.Series(y[:split_idx])
    X_test = pd.DataFrame(X[split_idx:], columns=[f'feature_{i}' for i in range(15)])
    y_test = pd.Series(y[split_idx:])
    
    # Train model
    training_result = manager.train_model(X_train, y_train, model_type='lightgbm')
    model = training_result['model']
    
    # Evaluate model
    evaluation_result = manager.evaluate_model(model, X_test, y_test)
    print(f"✓ Model evaluation: {evaluation_result}")
    
    # Check evaluation metrics
    expected_metrics = ['accuracy', 'precision', 'recall', 'f1_score']
    for metric in expected_metrics:
        assert metric in evaluation_result, f"Should have {metric} metric"
        assert 0 <= evaluation_result[metric] <= 1, f"{metric} should be between 0 and 1"
    
    # Should have reasonable performance on synthetic data
    assert evaluation_result['accuracy'] > 0.3, "Should have better than random accuracy"
    print(f"✓ Model accuracy: {evaluation_result['accuracy']:.3f}")
```

#### 3. XGBoost Comparison Test
```python
def test_xgboost_comparison():
    manager = MLModelManager()
    
    # Create training data
    X, y = make_classification(
        n_samples=800,
        n_features=12,
        n_informative=8,
        n_classes=5,
        random_state=42
    )
    
    X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(12)])
    y_series = pd.Series(y)
    
    # Train both models
    lgb_result = manager.train_model(X_df, y_series, model_type='lightgbm')
    xgb_result = manager.train_model(X_df, y_series, model_type='xgboost')
    
    print(f"✓ LightGBM training score: {lgb_result['training_score']:.3f}")
    print(f"✓ XGBoost training score: {xgb_result['training_score']:.3f}")
    
    # Both should train successfully
    assert 'model' in lgb_result, "LightGBM should train successfully"
    assert 'model' in xgb_result, "XGBoost should train successfully"
    
    # Compare predictions
    test_data = X_df.iloc[:10]
    lgb_predictions = manager.predict_signals(lgb_result['model'], test_data)
    xgb_predictions = manager.predict_signals(xgb_result['model'], test_data)
    
    print(f"✓ LightGBM predictions shape: {lgb_predictions.shape}")
    print(f"✓ XGBoost predictions shape: {xgb_predictions.shape}")
    
    # Both should produce valid predictions
    assert lgb_predictions.shape == xgb_predictions.shape, "Predictions should have same shape"
    assert np.all(lgb_predictions >= 0) and np.all(lgb_predictions <= 1), "LightGBM predictions should be probabilities"
    assert np.all(xgb_predictions >= 0) and np.all(xgb_predictions <= 1), "XGBoost predictions should be probabilities"
```

#### 4. Model Persistence Test
```python
def test_model_persistence():
    manager = MLModelManager()
    
    # Train a model
    X, y = make_classification(
        n_samples=500,
        n_features=10,
        n_classes=5,
        random_state=42
    )
    
    X_df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(10)])
    y_series = pd.Series(y)
    
    training_result = manager.train_model(X_df, y_series, model_type='lightgbm')
    model = training_result['model']
    
    # Save model
    model_metadata = {
        'model_type': 'lightgbm',
        'training_date': datetime.utcnow().isoformat(),
        'feature_count': 10,
        'training_samples': 500,
        'training_score': training_result['training_score']
    }
    
    model_name = 'test_model_v1'
    manager.save_model(model, model_name, model_metadata)
    print(f"✓ Model saved: {model_name}")
    
    # Load model
    loaded_model, loaded_metadata = manager.load_model(model_name)
    print(f"✓ Model loaded: {loaded_metadata}")
    
    # Test loaded model
    original_predictions = manager.predict_signals(model, X_df.iloc[:5])
    loaded_predictions = manager.predict_signals(loaded_model, X_df.iloc[:5])
    
    # Predictions should be identical
    np.testing.assert_array_almost_equal(
        original_predictions, loaded_predictions, decimal=6,
        err_msg="Loaded model should produce identical predictions"
    )
    
    print("✓ Model persistence test passed")
```

### Expected Test Results
- Models should train successfully with reasonable performance
- Evaluation metrics should be calculated correctly
- Different model types should be comparable
- Model persistence should maintain prediction accuracy

### Post-Test Actions
```bash
git add src/ml/model_manager.py
git add tests/test_model_manager.py
git commit -m "feat: implement ML model development with LightGBM and XGBoost"
```

### Progress Update
Mark Task 23 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 24: Model Training Pipeline
**Objective**: Create automated training pipeline with hyperparameter optimization and cross-validation.

### Implementation Steps

#### 24.1 Create TrainingPipeline Class Structure
Create `src/ml/training_pipeline.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import optuna
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, log_loss
from loguru import logger
import json

class TrainingPipeline:
    def __init__(self, model_manager):
        self.model_manager = model_manager
        self.hyperparameter_spaces = {
            'lightgbm': {
                'num_leaves': (10, 100),
                'learning_rate': (0.01, 0.3),
                'feature_fraction': (0.5, 1.0),
                'bagging_fraction': (0.5, 1.0),
                'min_child_samples': (5, 50)
            },
            'xgboost': {
                'max_depth': (3, 10),
                'learning_rate': (0.01, 0.3),
                'subsample': (0.5, 1.0),
                'colsample_bytree': (0.5, 1.0),
                'min_child_weight': (1, 10)
            }
        }
        self.cv_folds = 5
        self.optimization_trials = 100
        
    def run_training_pipeline(self, features: pd.DataFrame, labels: pd.Series,
                            model_type: str = 'lightgbm') -> Dict:
        # Run complete training pipeline
        pass
        
    def optimize_hyperparameters(self, features: pd.DataFrame, labels: pd.Series,
                                model_type: str) -> Dict:
        # Optimize hyperparameters using Optuna
        pass
        
    def cross_validate_model(self, features: pd.DataFrame, labels: pd.Series,
                           model_config: Dict, model_type: str) -> Dict:
        # Perform time series cross-validation
        pass
        
    def _objective_function(self, trial, features: pd.DataFrame, 
                          labels: pd.Series, model_type: str) -> float:
        # Objective function for hyperparameter optimization
        pass
```

#### 24.2 Implement Hyperparameter Optimization
- **Optuna Integration**: Use Optuna for efficient hyperparameter search
- **Bayesian Optimization**: Intelligent parameter space exploration
- **Early Stopping**: Stop unpromising trials early
- **Multi-Objective Optimization**: Balance accuracy and training time

#### 24.3 Add Cross-Validation Framework
- **Time Series CV**: Use TimeSeriesSplit for temporal data
- **Walk-Forward Validation**: Implement walk-forward testing
- **Performance Metrics**: Track multiple evaluation metrics
- **Overfitting Detection**: Monitor train/validation performance gap

#### 24.4 Create Training Automation
- **Automated Retraining**: Schedule regular model retraining
- **Data Drift Detection**: Monitor for data distribution changes
- **Model Comparison**: Compare new models with existing ones
- **Production Deployment**: Automated model deployment pipeline

### Key Implementation Details
- Use time-aware cross-validation to prevent data leakage
- Implement proper hyperparameter search spaces
- Add comprehensive logging and monitoring
- Consider computational resources in optimization

### Testing Instructions

#### 1. Hyperparameter Optimization Test
```python
# Create test file: test_training_pipeline.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.ml.training_pipeline import TrainingPipeline
from src.ml.model_manager import MLModelManager
from sklearn.datasets import make_classification

def test_hyperparameter_optimization():
    model_manager = MLModelManager()
    pipeline = TrainingPipeline(model_manager)
    
    # Create synthetic time series data
    X, y = make_classification(
        n_samples=1000,
        n_features=15,
        n_informative=10,
        n_classes=5,
        random_state=42
    )
    
    # Add time index
    dates = pd.date_range(start='2023-01-01', periods=1000, freq='1min')
    features = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(15)], index=dates)
    labels = pd.Series(y, index=dates)
    
    print(f"✓ Training data prepared: {features.shape}")
    
    # Run hyperparameter optimization (limited trials for testing)
    pipeline.optimization_trials = 10  # Reduce for testing
    
    optimization_result = pipeline.optimize_hyperparameters(
        features, labels, model_type='lightgbm'
    )
    
    print(f"✓ Hyperparameter optimization completed: {optimization_result}")
    
    # Check optimization results
    assert 'best_params' in optimization_result, "Should return best parameters"
    assert 'best_score' in optimization_result, "Should return best score"
    assert 'optimization_history' in optimization_result, "Should return optimization history"
    
    # Check parameter validity
    best_params = optimization_result['best_params']
    expected_params = ['num_leaves', 'learning_rate', 'feature_fraction']
    
    for param in expected_params:
        assert param in best_params, f"Should optimize {param}"
    
    # Check score improvement
    best_score = optimization_result['best_score']
    assert 0 <= best_score <= 1, "Score should be between 0 and 1"
    print(f"✓ Best optimization score: {best_score:.3f}")
```

#### 2. Cross-Validation Test
```python
def test_cross_validation():
    model_manager = MLModelManager()
    pipeline = TrainingPipeline(model_manager)
    
    # Create time series data
    X, y = make_classification(
        n_samples=500,
        n_features=10,
        n_classes=5,
        random_state=42
    )
    
    dates = pd.date_range(start='2023-01-01', periods=500, freq='1min')
    features = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(10)], index=dates)
    labels = pd.Series(y, index=dates)
    
    # Test cross-validation
    model_config = {
        'num_leaves': 31,
        'learning_rate': 0.1,
        'feature_fraction': 0.9
    }
    
    cv_result = pipeline.cross_validate_model(
        features, labels, model_config, model_type='lightgbm'
    )
    
    print(f"✓ Cross-validation completed: {cv_result}")
    
    # Check CV results
    assert 'cv_scores' in cv_result, "Should return CV scores"
    assert 'mean_score' in cv_result, "Should return mean score"
    assert 'std_score' in cv_result, "Should return score standard deviation"
    
    cv_scores = cv_result['cv_scores']
    assert len(cv_scores) == pipeline.cv_folds, f"Should have {pipeline.cv_folds} CV scores"
    
    # All scores should be reasonable
    for score in cv_scores:
        assert 0 <= score <= 1, "CV scores should be between 0 and 1"
    
    mean_score = cv_result['mean_score']
    std_score = cv_result['std_score']
    
    print(f"✓ CV Score: {mean_score:.3f} ± {std_score:.3f}")
    
    # Should have reasonable performance
    assert mean_score > 0.2, "Should have better than random performance"
```

#### 3. Full Training Pipeline Test
```python
def test_full_training_pipeline():
    model_manager = MLModelManager()
    pipeline = TrainingPipeline(model_manager)
    
    # Create comprehensive training data
    X, y = make_classification(
        n_samples=800,
        n_features=12,
        n_informative=8,
        n_classes=5,
        random_state=42
    )
    
    dates = pd.date_range(start='2023-01-01', periods=800, freq='1min')
    features = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(12)], index=dates)
    labels = pd.Series(y, index=dates)
    
    # Run full pipeline (reduced trials for testing)
    pipeline.optimization_trials = 5
    pipeline.cv_folds = 3
    
    pipeline_result = pipeline.run_training_pipeline(
        features, labels, model_type='lightgbm'
    )
    
    print(f"✓ Training pipeline completed: {list(pipeline_result.keys())}")
    
    # Check pipeline results
    expected_keys = [
        'trained_model', 'best_params', 'cv_results', 
        'feature_importance', 'training_metadata'
    ]
    
    for key in expected_keys:
        assert key in pipeline_result, f"Should have {key} in results"
    
    # Check trained model
    trained_model = pipeline_result['trained_model']
    test_predictions = model_manager.predict_signals(trained_model, features.iloc[:10])
    
    assert test_predictions.shape[0] == 10, "Should predict for all test samples"
    print(f"✓ Model predictions shape: {test_predictions.shape}")
    
    # Check metadata
    metadata = pipeline_result['training_metadata']
    assert 'training_date' in metadata, "Should have training date"
    assert 'model_type' in metadata, "Should have model type"
    assert 'feature_count' in metadata, "Should have feature count"
    
    print(f"✓ Training metadata: {metadata}")
```

#### 4. Model Comparison Test
```python
def test_model_comparison():
    model_manager = MLModelManager()
    pipeline = TrainingPipeline(model_manager)
    
    # Create training data
    X, y = make_classification(
        n_samples=600,
        n_features=8,
        n_classes=5,
        random_state=42
    )
    
    dates = pd.date_range(start='2023-01-01', periods=600, freq='1min')
    features = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(8)], index=dates)
    labels = pd.Series(y, index=dates)
    
    # Train multiple models
    pipeline.optimization_trials = 3  # Minimal for testing
    pipeline.cv_folds = 2
    
    models_to_compare = ['lightgbm', 'xgboost']
    comparison_results = {}
    
    for model_type in models_to_compare:
        try:
            result = pipeline.run_training_pipeline(features, labels, model_type=model_type)
            comparison_results[model_type] = result
            print(f"✓ {model_type} training completed")
        except Exception as e:
            print(f"⚠️ {model_type} training failed: {e}")
    
    # Compare models if both trained successfully
    if len(comparison_results) >= 2:
        print("\n✓ Model Comparison:")
        for model_type, result in comparison_results.items():
            cv_score = result['cv_results']['mean_score']
            print(f"  {model_type}: CV Score = {cv_score:.3f}")
        
        # Should have reasonable scores
        for model_type, result in comparison_results.items():
            cv_score = result['cv_results']['mean_score']
            assert cv_score > 0.15, f"{model_type} should have reasonable performance"
    
    print("✓ Model comparison test completed")
```

### Expected Test Results
- Hyperparameter optimization should improve model performance
- Cross-validation should provide reliable performance estimates
- Full pipeline should integrate all components successfully
- Model comparison should enable selection of best approach

### Post-Test Actions
```bash
git add src/ml/training_pipeline.py
git add tests/test_training_pipeline.py
git commit -m "feat: implement automated training pipeline with hyperparameter optimization"
```

### Progress Update
Mark Task 24 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 25: Backtesting Engine
**Objective**: Create comprehensive backtesting system with realistic execution simulation.

### Implementation Steps

#### 25.1 Create BacktestEngine Class Structure
Create `src/ml/backtest_engine.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from loguru import logger

@dataclass
class BacktestConfig:
    initial_capital: float = 10000.0
    transaction_cost: float = 0.001  # 0.1% per trade
    slippage_model: str = 'linear'   # 'linear', 'sqrt', 'fixed'
    max_position_size: float = 0.1   # 10% of capital
    rebalance_frequency: str = 'signal'  # 'signal', 'daily', 'weekly'

class BacktestEngine:
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.portfolio_history = []
        self.trade_history = []
        self.performance_metrics = {}
        self.current_positions = {}
        self.current_capital = config.initial_capital
        
    def run_backtest(self, predictions: pd.DataFrame, 
                    market_data: pd.DataFrame) -> Dict:
        # Run complete backtest simulation
        pass
        
    def simulate_trade_execution(self, signal: Dict, market_data: pd.Series) -> Dict:
        # Simulate realistic trade execution with slippage
        pass
        
    def calculate_performance_metrics(self) -> Dict:
        # Calculate comprehensive performance metrics
        pass
        
    def _calculate_slippage(self, trade_size: float, market_data: pd.Series) -> float:
        # Calculate realistic slippage based on trade size
        pass
```

#### 25.2 Implement Realistic Execution Simulation
- **Slippage Modeling**: Model market impact based on trade size
- **Transaction Costs**: Include realistic trading fees
- **Partial Fills**: Simulate scenarios where orders don't fill completely
- **Market Hours**: Consider trading hours and market closures

#### 25.3 Add Performance Analytics
- **Return Metrics**: Calculate total return, CAGR, volatility
- **Risk Metrics**: Sharpe ratio, Sortino ratio, maximum drawdown
- **Trade Analytics**: Win rate, average trade duration, profit factor
- **Benchmark Comparison**: Compare against buy-and-hold strategy

#### 25.4 Create Visualization and Reporting
- **Equity Curves**: Plot portfolio value over time
- **Drawdown Analysis**: Visualize drawdown periods
- **Trade Distribution**: Analyze trade outcomes
- **Performance Attribution**: Break down returns by strategy component

### Key Implementation Details
- Use realistic market microstructure assumptions
- Implement proper position sizing and risk management
- Add comprehensive performance attribution
- Consider survivorship bias and other common pitfalls

### Testing Instructions

#### 1. Basic Backtesting Test
```python
# Create test file: test_backtest_engine.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.ml.backtest_engine import BacktestEngine, BacktestConfig

def test_basic_backtesting():
    config = BacktestConfig(
        initial_capital=10000.0,
        transaction_cost=0.001,
        max_position_size=0.1
    )
    
    engine = BacktestEngine(config)
    
    # Create sample market data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
    
    # Create trending market data
    base_price = 50000
    price_changes = np.random.randn(100) * 0.01  # 1% hourly volatility
    prices = base_price * np.exp(np.cumsum(price_changes))
    
    market_data = pd.DataFrame({
        'timestamp': dates,
        'close': prices,
        'volume': np.random.exponential(1000, 100),
        'high': prices * (1 + np.abs(np.random.randn(100) * 0.005)),
        'low': prices * (1 - np.abs(np.random.randn(100) * 0.005))
    }).set_index('timestamp')
    
    # Create sample predictions (simple trend following)
    predictions = pd.DataFrame({
        'timestamp': dates,
        'predicted_signal': np.where(
            market_data['close'].pct_change() > 0.005, 'BUY',
            np.where(market_data['close'].pct_change() < -0.005, 'SELL', 'HOLD')
        ),
        'confidence': np.random.uniform(0.6, 0.9, 100)
    }).set_index('timestamp')
    
    print(f"✓ Test data prepared: {len(market_data)} periods")
    
    # Run backtest
    backtest_result = engine.run_backtest(predictions, market_data)
    print(f"✓ Backtest completed: {list(backtest_result.keys())}")
    
    # Check backtest results
    expected_keys = ['portfolio_history', 'trade_history', 'performance_metrics']
    for key in expected_keys:
        assert key in backtest_result, f"Should have {key} in results"
    
    # Check portfolio history
    portfolio_history = backtest_result['portfolio_history']
    assert len(portfolio_history) > 0, "Should have portfolio history"
    
    # Check performance metrics
    performance = backtest_result['performance_metrics']
    assert 'total_return' in performance, "Should calculate total return"
    assert 'sharpe_ratio' in performance, "Should calculate Sharpe ratio"
    assert 'max_drawdown' in performance, "Should calculate max drawdown"
    
    print(f"✓ Total return: {performance['total_return']:.2%}")
    print(f"✓ Sharpe ratio: {performance['sharpe_ratio']:.3f}")
    print(f"✓ Max drawdown: {performance['max_drawdown']:.2%}")
```

### Expected Test Results
- Backtesting should simulate realistic trading scenarios
- Performance metrics should be calculated accurately
- Trade execution should include slippage and costs
- Results should provide actionable insights

### Post-Test Actions
```bash
git add src/ml/backtest_engine.py
git add tests/test_backtest_engine.py
git commit -m "feat: implement comprehensive backtesting engine with realistic simulation"
```

### Progress Update
Mark Task 25 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 26: Model Performance Monitoring
**Objective**: Create system for monitoring ML model performance in production and detecting model drift.

### Implementation Steps

#### 26.1 Create ModelMonitor Class Structure
Create `src/ml/model_monitor.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from scipy import stats
from loguru import logger
import json

@dataclass
class ModelPerformanceMetrics:
    timestamp: datetime
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    prediction_confidence: float
    feature_drift_score: float
    label_drift_score: float

class ModelMonitor:
    def __init__(self, baseline_window_days: int = 30):
        self.baseline_window_days = baseline_window_days
        self.performance_history = []
        self.drift_thresholds = {
            'feature_drift': 0.1,      # 10% drift threshold
            'label_drift': 0.15,       # 15% label drift threshold
            'accuracy_drop': 0.05,     # 5% accuracy drop threshold
            'confidence_drop': 0.1     # 10% confidence drop threshold
        }
        self.baseline_metrics = {}
        self.alerts = []
        
    def record_prediction_batch(self, predictions: pd.DataFrame, 
                              actuals: pd.DataFrame, features: pd.DataFrame,
                              model_name: str):
        # Record batch of predictions for monitoring
        pass
        
    def calculate_feature_drift(self, current_features: pd.DataFrame,
                              baseline_features: pd.DataFrame) -> float:
        # Calculate feature distribution drift using statistical tests
        pass
        
    def calculate_label_drift(self, current_labels: pd.Series,
                            baseline_labels: pd.Series) -> float:
        # Calculate label distribution drift
        pass
        
    def detect_performance_degradation(self, model_name: str) -> List[Dict]:
        # Detect if model performance has degraded significantly
        pass
        
    def generate_monitoring_report(self, model_name: str, 
                                 days_back: int = 7) -> Dict:
        # Generate comprehensive monitoring report
        pass
```

#### 26.2 Implement Drift Detection
- **Feature Drift**: Use statistical tests (KS test, PSI) to detect feature distribution changes
- **Label Drift**: Monitor changes in target variable distribution
- **Concept Drift**: Detect changes in feature-target relationships
- **Covariate Shift**: Identify shifts in input data distribution

#### 26.3 Add Performance Tracking
- **Real-Time Metrics**: Track accuracy, precision, recall in production
- **Confidence Monitoring**: Monitor prediction confidence levels
- **Temporal Analysis**: Analyze performance trends over time
- **Segment Analysis**: Break down performance by market conditions

#### 26.4 Create Alerting System
- **Threshold-Based Alerts**: Alert when metrics cross predefined thresholds
- **Trend-Based Alerts**: Detect gradual performance degradation
- **Anomaly Detection**: Identify unusual patterns in model behavior
- **Automated Retraining**: Trigger retraining when drift is detected

### Key Implementation Details
- Use statistical significance tests for drift detection
- Implement sliding window analysis for trend detection
- Add configurable alerting thresholds
- Consider different drift types and their implications

### Testing Instructions

#### 1. Feature Drift Detection Test
```python
# Create test file: test_model_monitor.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.ml.model_monitor import ModelMonitor

def test_feature_drift_detection():
    monitor = ModelMonitor(baseline_window_days=30)
    
    # Create baseline features (normal distribution)
    np.random.seed(42)
    baseline_features = pd.DataFrame({
        'feature_1': np.random.normal(0, 1, 1000),
        'feature_2': np.random.normal(5, 2, 1000),
        'feature_3': np.random.exponential(1, 1000)
    })
    
    # Create current features with drift (shifted distribution)
    current_features = pd.DataFrame({
        'feature_1': np.random.normal(0.5, 1, 1000),  # Mean shift
        'feature_2': np.random.normal(5, 3, 1000),    # Variance increase
        'feature_3': np.random.exponential(1.5, 1000) # Scale change
    })
    
    # Calculate drift
    drift_score = monitor.calculate_feature_drift(current_features, baseline_features)
    print(f"✓ Feature drift score: {drift_score:.4f}")
    
    # Should detect drift
    assert drift_score > monitor.drift_thresholds['feature_drift'], \
           "Should detect feature drift in shifted distributions"
    
    # Test with no drift
    no_drift_features = pd.DataFrame({
        'feature_1': np.random.normal(0, 1, 1000),
        'feature_2': np.random.normal(5, 2, 1000),
        'feature_3': np.random.exponential(1, 1000)
    })
    
    no_drift_score = monitor.calculate_feature_drift(no_drift_features, baseline_features)
    print(f"✓ No drift score: {no_drift_score:.4f}")
    
    # Should not detect drift
    assert no_drift_score <= monitor.drift_thresholds['feature_drift'], \
           "Should not detect drift in similar distributions"
```

#### 2. Performance Monitoring Test
```python
def test_performance_monitoring():
    monitor = ModelMonitor()
    
    # Create sample prediction data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='1H')
    
    # Simulate model performance over time
    for i, date in enumerate(dates):
        # Simulate gradual performance degradation
        base_accuracy = 0.8
        degradation = min(i * 0.001, 0.1)  # Up to 10% degradation
        current_accuracy = base_accuracy - degradation
        
        predictions = pd.DataFrame({
            'timestamp': [date] * 50,
            'predicted_class': np.random.choice([0, 1, 2, 3, 4], 50),
            'confidence': np.random.uniform(0.6, 0.95, 50)
        })
        
        # Generate actuals with decreasing accuracy
        actuals = pd.DataFrame({
            'timestamp': [date] * 50,
            'actual_class': np.where(
                np.random.random(50) < current_accuracy,
                predictions['predicted_class'],  # Correct predictions
                np.random.choice([0, 1, 2, 3, 4], 50)  # Random incorrect
            )
        })
        
        features = pd.DataFrame({
            'feature_1': np.random.normal(0, 1, 50),
            'feature_2': np.random.normal(0, 1, 50)
        })
        
        monitor.record_prediction_batch(predictions, actuals, features, 'test_model')
    
    # Check performance degradation detection
    degradation_alerts = monitor.detect_performance_degradation('test_model')
    print(f"✓ Performance degradation alerts: {len(degradation_alerts)}")
    
    # Should detect degradation
    assert len(degradation_alerts) > 0, "Should detect performance degradation"
    
    # Check alert details
    for alert in degradation_alerts:
        print(f"✓ Alert: {alert['type']} - {alert['message']}")
        assert 'accuracy' in alert['message'].lower(), "Should mention accuracy degradation"
```

#### 3. Label Drift Detection Test
```python
def test_label_drift_detection():
    monitor = ModelMonitor()
    
    # Create baseline labels (balanced distribution)
    baseline_labels = pd.Series(np.random.choice([0, 1, 2, 3, 4], 1000, 
                                                p=[0.2, 0.2, 0.2, 0.2, 0.2]))
    
    # Create current labels with drift (imbalanced distribution)
    current_labels = pd.Series(np.random.choice([0, 1, 2, 3, 4], 1000,
                                               p=[0.5, 0.1, 0.1, 0.1, 0.2]))
    
    # Calculate label drift
    label_drift = monitor.calculate_label_drift(current_labels, baseline_labels)
    print(f"✓ Label drift score: {label_drift:.4f}")
    
    # Should detect drift
    assert label_drift > monitor.drift_thresholds['label_drift'], \
           "Should detect label distribution drift"
    
    # Test with no drift
    no_drift_labels = pd.Series(np.random.choice([0, 1, 2, 3, 4], 1000,
                                                p=[0.2, 0.2, 0.2, 0.2, 0.2]))
    
    no_label_drift = monitor.calculate_label_drift(no_drift_labels, baseline_labels)
    print(f"✓ No label drift score: {no_label_drift:.4f}")
    
    # Should not detect drift
    assert no_label_drift <= monitor.drift_thresholds['label_drift'], \
           "Should not detect drift in similar label distributions"
```

#### 4. Monitoring Report Test
```python
def test_monitoring_report():
    monitor = ModelMonitor()
    
    # Add sample performance data
    dates = pd.date_range(start='2023-01-01', periods=30, freq='1D')
    
    for i, date in enumerate(dates):
        # Create sample batch data
        predictions = pd.DataFrame({
            'timestamp': [date] * 100,
            'predicted_class': np.random.choice([0, 1, 2, 3, 4], 100),
            'confidence': np.random.uniform(0.7, 0.9, 100)
        })
        
        actuals = pd.DataFrame({
            'timestamp': [date] * 100,
            'actual_class': np.where(
                np.random.random(100) < 0.75,  # 75% accuracy
                predictions['predicted_class'],
                np.random.choice([0, 1, 2, 3, 4], 100)
            )
        })
        
        features = pd.DataFrame({
            'feature_1': np.random.normal(0, 1, 100),
            'feature_2': np.random.normal(0, 1, 100),
            'feature_3': np.random.normal(0, 1, 100)
        })
        
        monitor.record_prediction_batch(predictions, actuals, features, 'production_model')
    
    # Generate monitoring report
    report = monitor.generate_monitoring_report('production_model', days_back=7)
    print(f"✓ Monitoring report generated: {list(report.keys())}")
    
    # Check report contents
    expected_sections = [
        'model_performance', 'drift_analysis', 'alerts', 
        'recommendations', 'data_quality'
    ]
    
    for section in expected_sections:
        assert section in report, f"Report should have {section} section"
    
    # Check performance metrics
    performance = report['model_performance']
    assert 'accuracy' in performance, "Should report accuracy"
    assert 'confidence_trend' in performance, "Should report confidence trends"
    
    # Check drift analysis
    drift = report['drift_analysis']
    assert 'feature_drift_score' in drift, "Should report feature drift"
    assert 'label_drift_score' in drift, "Should report label drift"
    
    print(f"✓ Model accuracy: {performance['accuracy']:.3f}")
    print(f"✓ Feature drift: {drift['feature_drift_score']:.4f}")
    print(f"✓ Alerts generated: {len(report['alerts'])}")
```

### Expected Test Results
- Drift detection should identify distribution changes accurately
- Performance monitoring should track model degradation
- Alerting system should trigger appropriate warnings
- Monitoring reports should provide actionable insights

### Post-Test Actions
```bash
git add src/ml/model_monitor.py
git add tests/test_model_monitor.py
git commit -m "feat: implement model performance monitoring with drift detection"
```

### Progress Update
Mark Task 26 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Phase B2 Summary

### Completed Tasks:
- ✅ Task 20: Feature Engineering Module
- ✅ Task 21: Data Labeling System
- ✅ Task 22: Free Historical Data Integration
- ✅ Task 23: ML Model Development
- ✅ Task 24: Model Training Pipeline
- ✅ Task 25: Backtesting Engine
- ✅ Task 26: Model Performance Monitoring

### Milestone 4 Checkpoint:
**ML-Enhanced Signal System Operational**

Verify all Phase B2 components are working:
1. **Feature Engineering**: Comprehensive feature creation from market data
2. **Data Labeling**: Forward-looking returns and signal outcome labeling
3. **Historical Data**: Multi-source data integration for training
4. **ML Models**: LightGBM, XGBoost models trained and validated
5. **Training Pipeline**: Automated hyperparameter optimization
6. **Backtesting**: Realistic performance simulation
7. **Monitoring**: Production model performance tracking

### Phase B2 Integration Testing:
Run comprehensive integration tests to verify:

#### 1. End-to-End ML Pipeline
```python
# Test complete ML workflow
async def test_ml_pipeline_integration():
    # 1. Historical data fetching
    # 2. Feature engineering
    # 3. Data labeling
    # 4. Model training with optimization
    # 5. Backtesting validation
    # 6. Performance monitoring setup
    pass
```

#### 2. Model Deployment Pipeline
```python
# Test model deployment workflow
async def test_model_deployment():
    # 1. Model training and validation
    # 2. Performance benchmarking
    # 3. Production deployment
    # 4. Monitoring activation
    # 5. Drift detection setup
    pass
```

### Success Criteria Verification:
- ✅ ML models achieving better performance than rule-based system
- ✅ Feature engineering creating meaningful predictive features
- ✅ Backtesting showing positive risk-adjusted returns
- ✅ Model monitoring detecting drift and performance issues
- ✅ Training pipeline enabling automated model updates

### Next Steps:
Proceed to **[Phase C: Production & Maintenance](ATS_GUIDE_PHASE_C_PRODUCTION.md)** (Tasks 27-32)

### Production Readiness Checklist:
Before moving to Phase C, ensure:
- **Model Performance**: ML models outperforming baseline consistently
- **Data Pipeline**: Robust historical data integration working
- **Feature Quality**: Feature engineering producing stable features
- **Monitoring**: Comprehensive model monitoring in place
- **Backtesting**: Validated strategy performance across market conditions

### Troubleshooting:
- **Model overfitting**: Review cross-validation and regularization
- **Feature drift**: Check data sources and feature stability
- **Poor backtesting results**: Validate assumptions and execution simulation
- **Training pipeline failures**: Check hyperparameter spaces and data quality

---

**Phase B2 Complete!** Continue with [ATS_GUIDE_PHASE_C_PRODUCTION.md](ATS_GUIDE_PHASE_C_PRODUCTION.md)
