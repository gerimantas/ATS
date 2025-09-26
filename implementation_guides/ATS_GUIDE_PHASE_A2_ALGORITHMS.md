# ATS Implementation Guide - Phase A2: Algorithms & Risk Management

## Overview

**Phase A2** implements the core trading signal algorithms and risk management systems. This phase builds upon the infrastructure from Phase A1 to create the rule-based signal generation system.

**Duration**: 2-3 weeks  
**Prerequisites**: Completed Phase A1, understanding of trading algorithms  
**Tasks Covered**: 7-14

---

## Task 7: DEX Order Flow Algorithm
**Objective**: Implement DEX order flow imbalance detection algorithm (10-30 second intervals).

### Implementation Steps

#### 7.1 Create OrderFlowAnalyzer Class Structure
Create `src/algorithms/order_flow.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta
from loguru import logger
import numpy as np

class OrderFlowAnalyzer:
    def __init__(self, window_seconds: int = 30):
        self.window_seconds = window_seconds
        self.imbalance_threshold = 0.6  # 60% imbalance threshold
        self.min_volume_threshold = 1000  # Minimum volume for signal
        self.trade_windows = {}  # symbol -> deque of trades
        self.signal_cooldowns = {}  # symbol -> last signal time
        
    def add_trade(self, symbol: str, trade: Dict):
        # Add new trade to analysis window
        pass
        
    def calculate_imbalance(self, symbol: str) -> float:
        # Calculate order flow imbalance ratio (-1 to 1)
        pass
        
    def is_signal_triggered(self, symbol: str) -> Tuple[bool, Optional[str]]:
        # Check if signal should be triggered
        pass
```

#### 7.2 Implement Trade Classification
- **Aggressive vs Passive Trades**: Identify market orders vs limit orders
- **Buy vs Sell Classification**: Use price movement and trade direction
- **Volume Weighting**: Weight trades by volume and recency
- **Time Decay**: Apply exponential decay for older trades

#### 7.3 Add Imbalance Calculation
- **Buy/Sell Volume Ratios**: Calculate volume-weighted ratios
- **Rolling Window Analysis**: Use sliding window for real-time calculation
- **Statistical Significance**: Ensure minimum volume thresholds
- **Normalization**: Return values between -1 (sell pressure) and 1 (buy pressure)

#### 7.4 Create Signal Triggering Logic
- **Threshold-Based Triggers**: Signal when imbalance exceeds thresholds
- **Signal Strength Scoring**: Calculate confidence based on volume and duration
- **Cooldown Management**: Prevent signal spam for same symbol
- **Direction Detection**: Determine BUY or SELL signal type

### Key Implementation Details
- Use `deque` with `maxlen` for efficient rolling window
- Implement exponential time decay for trade weighting
- Add statistical significance testing for imbalances
- Consider market microstructure effects and tick size

### Testing Instructions

#### 1. Trade Processing Test
```python
# Create test file: test_order_flow.py
import asyncio
from datetime import datetime
from src.algorithms.order_flow import OrderFlowAnalyzer

def test_trade_processing():
    analyzer = OrderFlowAnalyzer(window_seconds=30)
    
    # Add sample trades
    test_trades = [
        {
            'side': 'buy', 'amount': 100, 'price': 150.0,
            'timestamp': datetime.utcnow(), 'is_aggressive': True
        },
        {
            'side': 'sell', 'amount': 50, 'price': 149.9,
            'timestamp': datetime.utcnow(), 'is_aggressive': True
        },
        {
            'side': 'buy', 'amount': 200, 'price': 150.1,
            'timestamp': datetime.utcnow(), 'is_aggressive': True
        }
    ]
    
    for trade in test_trades:
        analyzer.add_trade('SOL/USDT', trade)
    
    imbalance = analyzer.calculate_imbalance('SOL/USDT')
    print(f"✓ Order flow imbalance: {imbalance:.3f}")
    
    # Should be positive (more buy volume)
    assert imbalance > 0, "Expected positive imbalance"
```

#### 2. Signal Generation Test
```python
def test_signal_generation():
    analyzer = OrderFlowAnalyzer(window_seconds=30)
    
    # Add strong buy pressure
    for i in range(10):
        analyzer.add_trade('SOL/USDT', {
            'side': 'buy', 'amount': 100, 'price': 150.0 + i * 0.01,
            'timestamp': datetime.utcnow(), 'is_aggressive': True
        })
    
    signal_triggered, signal_type = analyzer.is_signal_triggered('SOL/USDT')
    
    if signal_triggered:
        print(f"✓ Signal generated: {signal_type}")
        assert signal_type == 'BUY', "Expected BUY signal"
    else:
        print("✗ No signal generated")
```

#### 3. Window Management Test
```python
def test_window_management():
    analyzer = OrderFlowAnalyzer(window_seconds=5)  # Short window for testing
    
    # Add old trade
    old_trade = {
        'side': 'buy', 'amount': 100, 'price': 150.0,
        'timestamp': datetime.utcnow() - timedelta(seconds=10),
        'is_aggressive': True
    }
    analyzer.add_trade('SOL/USDT', old_trade)
    
    # Add recent trade
    recent_trade = {
        'side': 'sell', 'amount': 100, 'price': 149.9,
        'timestamp': datetime.utcnow(), 'is_aggressive': True
    }
    analyzer.add_trade('SOL/USDT', recent_trade)
    
    # Old trade should be filtered out
    imbalance = analyzer.calculate_imbalance('SOL/USDT')
    print(f"✓ Imbalance with window filtering: {imbalance:.3f}")
```

### Expected Test Results
- Trade data should be processed and stored correctly
- Imbalance calculations should return values between -1 and 1
- Signals should trigger only when thresholds are exceeded
- Window management should filter old trades

### Post-Test Actions
```bash
git add src/algorithms/order_flow.py
git add tests/test_order_flow.py
git commit -m "feat: implement DEX order flow imbalance algorithm"
```

### Progress Update
Mark Task 7 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 8: DEX Liquidity Event Algorithm
**Objective**: Create liquidity event detection based on rate and acceleration of liquidity changes.

### Implementation Steps

#### 8.1 Create LiquidityAnalyzer Class Structure
Create `src/algorithms/liquidity.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger

class LiquidityAnalyzer:
    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self.change_rate_threshold = 0.1  # 10% change rate
        self.acceleration_threshold = 0.05  # 5% acceleration
        self.min_liquidity_threshold = 10000  # Minimum liquidity to consider
        self.liquidity_windows = {}  # symbol -> deque of liquidity data
        
    def add_liquidity_data(self, symbol: str, liquidity_data: Dict):
        # Add new liquidity data point
        pass
        
    def calculate_liquidity_change_rate(self, symbol: str) -> float:
        # Calculate rate of liquidity change (first derivative)
        pass
        
    def calculate_liquidity_acceleration(self, symbol: str) -> float:
        # Calculate acceleration of liquidity change (second derivative)
        pass
```

#### 8.2 Implement Liquidity Metrics
- **Total Liquidity Tracking**: Monitor combined token0 + token1 liquidity
- **Rate of Change**: Calculate first derivative using time series analysis
- **Acceleration**: Calculate second derivative for momentum detection
- **Smoothing**: Apply exponential smoothing to reduce noise

#### 8.3 Add Event Classification
- **Gradual vs Sudden Changes**: Distinguish between normal and anomalous changes
- **Liquidity Additions vs Removals**: Identify direction of liquidity change
- **Event Significance**: Classify events by magnitude and duration
- **Pool Size Consideration**: Weight events by relative pool size

#### 8.4 Create Signal Generation Logic
- **Combined Thresholds**: Use both rate and acceleration for signal confirmation
- **Directional Bias**: Determine if liquidity change suggests price movement
- **Event Duration**: Consider sustained vs momentary changes
- **Cross-Pool Analysis**: Compare events across different pools

### Key Implementation Details
- Use pandas for efficient time series calculations
- Implement exponential smoothing for noise reduction
- Add minimum liquidity thresholds to filter small pools
- Consider relative changes vs absolute amounts

### Testing Instructions

#### 1. Liquidity Data Processing Test
```python
# Create test file: test_liquidity.py
from datetime import datetime, timedelta
from src.algorithms.liquidity import LiquidityAnalyzer

def test_liquidity_data_processing():
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
    
    change_rate = analyzer.calculate_liquidity_change_rate('SOL/USDT')
    acceleration = analyzer.calculate_liquidity_acceleration('SOL/USDT')
    
    print(f"✓ Liquidity change rate: {change_rate:.3f}")
    print(f"✓ Liquidity acceleration: {acceleration:.3f}")
    
    assert change_rate > 0, "Expected positive change rate"
    assert acceleration > 0, "Expected positive acceleration"
```

#### 2. Event Detection Test
```python
def test_event_detection():
    analyzer = LiquidityAnalyzer(window_seconds=60)
    
    # Simulate significant liquidity event
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
    else:
        print("✗ No liquidity event detected")
```

#### 3. Smoothing and Noise Reduction Test
```python
def test_smoothing():
    analyzer = LiquidityAnalyzer(window_seconds=120)
    
    # Add noisy data
    base_time = datetime.utcnow()
    base_liquidity = 1000000
    
    for i in range(10):
        # Add random noise
        noise = np.random.normal(0, 0.02)  # 2% noise
        liquidity = base_liquidity * (1 + noise)
        
        analyzer.add_liquidity_data('SOL/USDT', {
            'total_liquidity': liquidity,
            'timestamp': base_time - timedelta(seconds=120-i*12)
        })
    
    # Should handle noise gracefully
    change_rate = analyzer.calculate_liquidity_change_rate('SOL/USDT')
    print(f"✓ Change rate with noise: {change_rate:.3f}")
    
    # Should be close to zero for random noise
    assert abs(change_rate) < 0.05, "Change rate should be small for random noise"
```

### Expected Test Results
- Liquidity data should be processed and stored correctly
- Change rate calculations should reflect actual liquidity movements
- Events should trigger only for significant liquidity changes
- Smoothing should reduce impact of random noise

### Post-Test Actions
```bash
git add src/algorithms/liquidity.py
git add tests/test_liquidity.py
git commit -m "feat: implement DEX liquidity event detection algorithm"
```

### Progress Update
Mark Task 8 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 9: Volume-Price Correlation Algorithm
**Objective**: Implement volume-price correlation analysis for position formation detection.

### Implementation Steps

#### 9.1 Create VolumePriceAnalyzer Class Structure
Create `src/algorithms/volume_price.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from loguru import logger

class VolumePriceAnalyzer:
    def __init__(self, window_seconds: int = 120):
        self.window_seconds = window_seconds
        self.correlation_threshold = 0.3  # Minimum correlation for signal
        self.volume_multiplier_threshold = 2.0  # Volume spike threshold
        self.price_stability_threshold = 0.005  # 0.5% price stability
        self.price_windows = {}  # symbol -> deque of price data
        self.volume_windows = {}  # symbol -> deque of volume data
        
    def add_price_data(self, symbol: str, price_data: Dict):
        # Add new price data point
        pass
        
    def add_volume_data(self, symbol: str, volume_data: Dict):
        # Add new volume data point
        pass
        
    def calculate_correlation(self, symbol: str) -> float:
        # Calculate Pearson correlation between volume and price
        pass
        
    def calculate_volume_increase(self, symbol: str) -> float:
        # Calculate volume increase over analysis window
        pass
```

#### 9.2 Implement Correlation Analysis
- **Pearson Correlation**: Calculate correlation between volume and price changes
- **Rolling Correlation**: Use sliding window for real-time analysis
- **Volume-Weighted Analysis**: Weight correlation by volume magnitude
- **Time-Based Weighting**: Apply time decay for older data points

#### 9.3 Add Position Formation Detection
- **Accumulation Patterns**: Identify high volume with stable/rising prices
- **Distribution Patterns**: Detect high volume with stable/falling prices
- **Volume Spikes**: Identify unusual volume increases
- **Price Stability**: Measure price movement during volume events

#### 9.4 Create Signal Generation Logic
- **Divergence Detection**: Trigger signals on volume-price divergence
- **Pattern Recognition**: Identify accumulation vs distribution patterns
- **Signal Strength**: Weight signals by volume magnitude and duration
- **Directional Bias**: Determine likely price direction from pattern

### Key Implementation Details
- Use rolling correlation calculations for efficiency
- Implement volume-weighted average price (VWAP) analysis
- Add outlier detection for volume spikes
- Consider different timeframes for correlation analysis

### Testing Instructions

#### 1. Volume-Price Data Test
```python
# Create test file: test_volume_price.py
from datetime import datetime, timedelta
from src.algorithms.volume_price import VolumePriceAnalyzer

def test_volume_price_data():
    analyzer = VolumePriceAnalyzer(window_seconds=120)
    
    # Add sample price and volume data
    base_time = datetime.utcnow()
    
    # Simulate accumulation pattern (high volume, stable price)
    for i in range(10):
        analyzer.add_price_data('SOL/USDT', {
            'price': 150.0 + np.random.normal(0, 0.1),  # Stable price with small noise
            'high': 150.2, 'low': 149.8,
            'timestamp': base_time - timedelta(seconds=120-i*12)
        })
        
        analyzer.add_volume_data('SOL/USDT', {
            'volume': 10000 + i * 1000,  # Increasing volume
            'trade_count': 50 + i * 5,
            'timestamp': base_time - timedelta(seconds=120-i*12)
        })
    
    correlation = analyzer.calculate_correlation('SOL/USDT')
    volume_increase = analyzer.calculate_volume_increase('SOL/USDT')
    
    print(f"✓ Volume-price correlation: {correlation:.3f}")
    print(f"✓ Volume increase: {volume_increase:.3f}")
    
    assert volume_increase > 1.0, "Expected volume increase"
```

#### 2. Position Formation Test
```python
def test_position_formation():
    analyzer = VolumePriceAnalyzer(window_seconds=120)
    
    # Simulate strong accumulation pattern
    base_time = datetime.utcnow()
    
    for i in range(15):
        # High volume with minimal price movement
        analyzer.add_volume_data('SOL/USDT', {
            'volume': 20000,  # Consistently high volume
            'timestamp': base_time - timedelta(seconds=120-i*8)
        })
        
        analyzer.add_price_data('SOL/USDT', {
            'price': 150.0 + np.random.normal(0, 0.05),  # Very stable price
            'timestamp': base_time - timedelta(seconds=120-i*8)
        })
    
    signal_triggered, signal_type = analyzer.is_signal_triggered('SOL/USDT')
    
    if signal_triggered:
        print(f"✓ Position formation detected: {signal_type}")
        assert signal_type in ['ACCUMULATION', 'BUY'], "Expected accumulation signal"
    else:
        print("✗ No position formation detected")
```

#### 3. Correlation Calculation Test
```python
def test_correlation_calculation():
    analyzer = VolumePriceAnalyzer(window_seconds=60)
    
    # Add perfectly correlated data
    base_time = datetime.utcnow()
    
    for i in range(10):
        price = 150.0 + i * 0.5  # Increasing price
        volume = 10000 + i * 1000  # Increasing volume
        
        analyzer.add_price_data('SOL/USDT', {
            'price': price,
            'timestamp': base_time - timedelta(seconds=60-i*6)
        })
        
        analyzer.add_volume_data('SOL/USDT', {
            'volume': volume,
            'timestamp': base_time - timedelta(seconds=60-i*6)
        })
    
    correlation = analyzer.calculate_correlation('SOL/USDT')
    print(f"✓ Perfect correlation test: {correlation:.3f}")
    
    # Should be close to 1.0 for perfectly correlated data
    assert correlation > 0.8, "Expected high positive correlation"
```

### Expected Test Results
- Volume and price data should be processed correctly
- Correlation calculations should return meaningful values (-1 to 1)
- Position formation signals should trigger appropriately
- Volume increases should be calculated accurately

### Post-Test Actions
```bash
git add src/algorithms/volume_price.py
git add tests/test_volume_price.py
git commit -m "feat: implement volume-price correlation algorithm"
```

### Progress Update
Mark Task 9 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 10: Signal Combination Logic
**Objective**: Create multi-algorithm confirmation system for strong signal generation.

### Implementation Steps

#### 10.1 Create SignalAggregator Class Structure
Create `src/algorithms/signal_aggregator.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger

class SignalAggregator:
    def __init__(self, confirmation_threshold: int = 2):
        self.confirmation_threshold = confirmation_threshold
        self.recent_signals = defaultdict(list)  # symbol -> list of recent signals
        self.signal_window_seconds = 30  # Time window for signal confirmation
        self.algorithm_weights = {
            'order_flow': 1.0,
            'liquidity': 1.0,
            'volume_price': 0.8
        }
        
    def add_algorithm_signal(self, symbol: str, signal_type: str, 
                           algorithm_name: str, confidence: float) -> bool:
        # Add signal from individual algorithm
        pass
        
    def _check_confirmation(self, symbol: str, signal_type: str) -> Tuple[bool, float]:
        # Check if multiple algorithms confirm the same signal
        pass
        
    def get_combined_signal_strength(self, symbol: str, signal_type: str) -> float:
        # Calculate combined signal strength from multiple algorithms
        pass
```

#### 10.2 Implement Signal Confirmation Logic
- **Multi-Algorithm Agreement**: Require minimum number of algorithms to agree
- **Temporal Alignment**: Check signals occur within time window
- **Weighted Voting**: Weight signals by algorithm reliability and confidence
- **Signal Persistence**: Consider duration of signal agreement

#### 10.3 Add Signal Strength Calculation
- **Confidence Aggregation**: Combine confidence scores from multiple algorithms
- **Time Decay**: Apply decay for older signals within window
- **Algorithm Weighting**: Weight different algorithms based on historical performance
- **Normalization**: Return final signal strength between 0 and 1

#### 10.4 Create Cooldown Management
- **Symbol-Specific Cooldowns**: Prevent signal spam for same trading pair
- **Dynamic Cooldown Periods**: Adjust based on signal success rate
- **Algorithm-Specific Tracking**: Track performance by algorithm type
- **Cleanup Mechanisms**: Remove expired signals and cooldowns

### Key Implementation Details
- Use time-based signal windows for confirmation
- Implement weighted voting system for signal strength
- Add signal metadata preservation for analysis
- Consider algorithm reliability in weighting decisions

### Testing Instructions

#### 1. Signal Aggregation Test
```python
# Create test file: test_signal_aggregator.py
from datetime import datetime
from src.algorithms.signal_aggregator import SignalAggregator

def test_signal_aggregation():
    aggregator = SignalAggregator(confirmation_threshold=2)
    
    # Add signals from different algorithms
    signal1 = aggregator.add_algorithm_signal(
        'SOL/USDT', 'BUY', 'order_flow', 0.8
    )
    
    signal2 = aggregator.add_algorithm_signal(
        'SOL/USDT', 'BUY', 'liquidity', 0.7
    )
    
    # Should generate combined signal when threshold met
    if signal1 or signal2:
        print("✓ Combined signal generated")
        
        # Check signal strength
        strength = aggregator.get_combined_signal_strength('SOL/USDT', 'BUY')
        print(f"✓ Combined signal strength: {strength:.3f}")
        
        assert strength > 0.5, "Expected strong combined signal"
    else:
        print("✗ No combined signal generated")
```

#### 2. Confirmation Logic Test
```python
def test_confirmation_logic():
    aggregator = SignalAggregator(confirmation_threshold=3)
    
    # Add insufficient signals (below threshold)
    aggregator.add_algorithm_signal('SOL/USDT', 'BUY', 'order_flow', 0.6)
    aggregator.add_algorithm_signal('SOL/USDT', 'BUY', 'liquidity', 0.5)
    
    confirmed, strength = aggregator._check_confirmation('SOL/USDT', 'BUY')
    assert not confirmed, "Should not confirm with insufficient signals"
    
    # Add third signal to meet threshold
    aggregator.add_algorithm_signal('SOL/USDT', 'BUY', 'volume_price', 0.7)
    
    confirmed, strength = aggregator._check_confirmation('SOL/USDT', 'BUY')
    assert confirmed, "Should confirm with sufficient signals"
    print(f"✓ Signal confirmed with strength: {strength:.3f}")
```

#### 3. Cooldown Test
```python
def test_cooldown_functionality():
    aggregator = SignalAggregator(confirmation_threshold=2)
    
    # Generate initial signal
    aggregator.add_algorithm_signal('SOL/USDT', 'BUY', 'order_flow', 0.8)
    aggregator.add_algorithm_signal('SOL/USDT', 'BUY', 'liquidity', 0.7)
    
    # Check cooldown status
    is_cooldown = aggregator.is_in_cooldown('SOL/USDT')
    print(f"✓ Symbol in cooldown: {is_cooldown}")
    
    # Should prevent immediate duplicate signals
    if is_cooldown:
        duplicate_signal = aggregator.add_algorithm_signal('SOL/USDT', 'BUY', 'order_flow', 0.9)
        assert not duplicate_signal, "Should block duplicate signals during cooldown"
```

#### 4. Time Window Test
```python
def test_time_window():
    aggregator = SignalAggregator(confirmation_threshold=2)
    aggregator.signal_window_seconds = 5  # Short window for testing
    
    # Add first signal
    aggregator.add_algorithm_signal('SOL/USDT', 'BUY', 'order_flow', 0.8)
    
    # Wait beyond time window
    import time
    time.sleep(6)
    
    # Add second signal (should not combine due to time window)
    signal_generated = aggregator.add_algorithm_signal('SOL/USDT', 'BUY', 'liquidity', 0.7)
    
    # Should not generate combined signal due to time window expiry
    assert not signal_generated, "Should not combine signals outside time window"
```

### Expected Test Results
- Signal combination should work correctly with multiple algorithms
- Confirmation logic should require minimum threshold
- Cooldown periods should prevent signal spam
- Time windows should limit signal combination timeframe

### Post-Test Actions
```bash
git add src/algorithms/signal_aggregator.py
git add tests/test_signal_aggregator.py
git commit -m "feat: implement multi-algorithm signal confirmation system"
```

### Progress Update
Mark Task 10 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 11: Pre-Trade Slippage Analysis
**Objective**: Implement slippage calculation based on CEX order book depth analysis.

### Implementation Steps

#### 11.1 Create SlippageAnalyzer Class Structure
Create `src/risk/slippage.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional, Tuple
import numpy as np
from loguru import logger

class SlippageAnalyzer:
    def __init__(self):
        self.orderbook_depth_percentages = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
        self.max_slippage_threshold = 0.02  # 2% maximum acceptable slippage
        self.min_profit_after_slippage = 0.001  # 0.1% minimum profit after costs
        
    def calculate_slippage(self, orderbook: Dict, trade_size: float, 
                         trade_side: str) -> Dict[str, float]:
        # Calculate expected slippage for different order sizes
        pass
        
    def should_cancel_signal(self, estimated_slippage: float, 
                           predicted_profit: float) -> bool:
        # Determine if signal should be canceled due to high slippage
        pass
        
    def get_optimal_trade_size(self, orderbook: Dict, max_slippage: float,
                             trade_side: str) -> float:
        # Calculate optimal trade size for given slippage tolerance
        pass
```

#### 11.2 Implement Order Book Analysis
- **VWAP Calculation**: Calculate volume-weighted average price at different depths
- **Market Impact Modeling**: Model price impact for various trade sizes
- **Bid-Ask Spread Analysis**: Account for spread in slippage calculations
- **Liquidity Assessment**: Evaluate available liquidity at different price levels

#### 11.3 Add Dynamic Trade Sizing
- **Size Optimization**: Adjust trade size based on available liquidity
- **Slippage Tolerance**: Implement maximum acceptable slippage thresholds
- **Partial Fill Scenarios**: Consider scenarios where orders may not fill completely
- **Market Condition Adjustment**: Adjust sizing based on market volatility

#### 11.4 Create Signal Filtering Logic
- **Cost-Benefit Analysis**: Cancel signals where slippage exceeds predicted profit
- **Risk-Adjusted Returns**: Calculate returns after accounting for execution costs
- **Dynamic Thresholds**: Adjust filtering based on market conditions
- **Alternative Execution**: Consider different execution strategies

### Key Implementation Details
- Use real-time order book data for accurate calculations
- Implement different slippage models for various market conditions
- Add safety margins for slippage estimates
- Consider transaction fees in total cost calculation

### Testing Instructions

#### 1. Slippage Calculation Test
```python
# Create test file: test_slippage.py
from src.risk.slippage import SlippageAnalyzer

def test_slippage_calculation():
    analyzer = SlippageAnalyzer()
    
    # Mock orderbook data
    mock_orderbook = {
        'bids': [
            [50000, 100], [49999, 200], [49998, 300],
            [49997, 400], [49996, 500]
        ],
        'asks': [
            [50001, 100], [50002, 200], [50003, 300],
            [50004, 400], [50005, 500]
        ],
        'timestamp': datetime.utcnow()
    }
    
    # Test buy order slippage
    slippage_buy = analyzer.calculate_slippage(mock_orderbook, 1000, 'BUY')
    print(f"✓ Buy slippage for $1000: {slippage_buy}")
    
    # Test sell order slippage
    slippage_sell = analyzer.calculate_slippage(mock_orderbook, 1000, 'SELL')
    print(f"✓ Sell slippage for $1000: {slippage_sell}")
    
    assert 'estimated_slippage' in slippage_buy, "Should return slippage estimate"
    assert slippage_buy['estimated_slippage'] >= 0, "Slippage should be non-negative"
```

#### 2. Signal Filtering Test
```python
def test_signal_filtering():
    analyzer = SlippageAnalyzer()
    
    # Test profitable signal (should not cancel)
    should_cancel_1 = analyzer.should_cancel_signal(0.003, 0.010)  # 0.3% slippage, 1% profit
    assert not should_cancel_1, "Should not cancel profitable signal"
    print("✓ Profitable signal not canceled")
    
    # Test unprofitable signal (should cancel)
    should_cancel_2 = analyzer.should_cancel_signal(0.015, 0.005)  # 1.5% slippage, 0.5% profit
    assert should_cancel_2, "Should cancel unprofitable signal"
    print("✓ Unprofitable signal canceled")
```

#### 3. Optimal Trade Size Test
```python
def test_optimal_trade_size():
    analyzer = SlippageAnalyzer()
    
    mock_orderbook = {
        'asks': [
            [50001, 100], [50002, 200], [50003, 500],
            [50005, 1000], [50010, 2000]
        ]
    }
    
    # Find optimal size for 1% max slippage
    optimal_size = analyzer.get_optimal_trade_size(mock_orderbook, 0.01, 'BUY')
    print(f"✓ Optimal trade size for 1% slippage: ${optimal_size}")
    
    assert optimal_size > 0, "Should return positive trade size"
    
    # Verify slippage is within tolerance
    slippage = analyzer.calculate_slippage(mock_orderbook, optimal_size, 'BUY')
    assert slippage['estimated_slippage'] <= 0.01, "Slippage should be within tolerance"
```

#### 4. Market Impact Test
```python
def test_market_impact():
    analyzer = SlippageAnalyzer()
    
    # Thin orderbook (high impact)
    thin_orderbook = {
        'asks': [[50001, 10], [50010, 20], [50020, 30]]
    }
    
    # Deep orderbook (low impact)
    deep_orderbook = {
        'asks': [[50001, 1000], [50002, 2000], [50003, 3000]]
    }
    
    thin_slippage = analyzer.calculate_slippage(thin_orderbook, 500, 'BUY')
    deep_slippage = analyzer.calculate_slippage(deep_orderbook, 500, 'BUY')
    
    print(f"✓ Thin orderbook slippage: {thin_slippage['estimated_slippage']:.4f}")
    print(f"✓ Deep orderbook slippage: {deep_slippage['estimated_slippage']:.4f}")
    
    # Thin orderbook should have higher slippage
    assert thin_slippage['estimated_slippage'] > deep_slippage['estimated_slippage'], \
           "Thin orderbook should have higher slippage"
```

### Expected Test Results
- Slippage calculations should return reasonable estimates
- Signal filtering should work based on profit/slippage ratios
- Trade sizing should adjust based on available liquidity
- Market impact should be higher for thin orderbooks

### Post-Test Actions
```bash
git add src/risk/slippage.py
git add tests/test_slippage.py
git commit -m "feat: implement pre-trade slippage analysis system"
```

### Progress Update
Mark Task 11 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 12: Market Regime Filter
**Objective**: Create BTC/ETH volatility monitoring and altcoin signal filtering system.

### Implementation Steps

#### 12.1 Create MarketRegimeFilter Class Structure
Create `src/risk/market_regime.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta
import numpy as np
from loguru import logger

class MarketRegimeFilter:
    def __init__(self, volatility_window: int = 300):  # 5 minutes
        self.volatility_window = volatility_window
        self.volatility_thresholds = {
            'CALM': 0.02,           # 2% volatility
            'NORMAL': 0.05,         # 5% volatility
            'VOLATILE': 0.10,       # 10% volatility
            'HIGHLY_VOLATILE': 0.20 # 20% volatility
        }
        self.price_windows = {}  # symbol -> deque of prices
        self.current_regime = 'NORMAL'
        self.regime_persistence = 3  # Require 3 confirmations for regime change
        
    def add_price_data(self, symbol: str, price: float, timestamp: float):
        # Add new price data point
        pass
        
    def calculate_volatility(self, symbol: str) -> float:
        # Calculate current volatility for a symbol
        pass
        
    def get_market_regime(self, btc_volatility: float, eth_volatility: float) -> str:
        # Determine current market regime
        pass
        
    def should_filter_signal(self, symbol: str, regime: str, is_altcoin: bool = True) -> Tuple[bool, str]:
        # Determine if signal should be filtered based on market regime
        pass
```

#### 12.2 Implement Volatility Calculation
- **Rolling Standard Deviation**: Use log returns for volatility calculation
- **Realized Volatility**: Calculate over different timeframes (1min, 5min, 15min)
- **Exponential Weighting**: Apply higher weight to recent price movements
- **Annualized Volatility**: Convert to annualized figures for comparison

#### 12.3 Add Regime Classification
- **Threshold-Based Classification**: Define volatility ranges for each regime
- **Multi-Asset Assessment**: Combine BTC and ETH volatility for overall market view
- **Regime Persistence**: Avoid frequent regime switching with confirmation requirements
- **Transition Smoothing**: Implement gradual transitions between regimes

#### 12.4 Create Signal Filtering Logic
- **Altcoin Filtering**: Filter altcoin signals during high volatility periods
- **Position Sizing Adjustment**: Reduce position sizes in volatile regimes
- **Risk Multipliers**: Apply regime-specific risk adjustments
- **Correlation Consideration**: Account for increased correlation during stress periods

### Key Implementation Details
- Use high-frequency price data for accurate volatility calculation
- Implement regime persistence to avoid frequent switching
- Add correlation analysis between major cryptocurrencies
- Consider volume-adjusted volatility measures

### Testing Instructions

#### 1. Volatility Calculation Test
```python
# Create test file: test_market_regime.py
from datetime import datetime, timedelta
import numpy as np
from src.risk.market_regime import MarketRegimeFilter

def test_volatility_calculation():
    filter = MarketRegimeFilter(volatility_window=300)
    
    # Add sample price data with known volatility
    base_time = datetime.utcnow().timestamp()
    base_price = 50000
    
    # Generate price series with 5% volatility
    np.random.seed(42)  # For reproducible results
    for i in range(100):
        # Generate log-normal price movement
        return_pct = np.random.normal(0, 0.05)  # 5% daily volatility
        price = base_price * (1 + return_pct)
        
        filter.add_price_data('BTC', price, base_time + i * 60)  # 1-minute intervals
    
    btc_vol = filter.calculate_volatility('BTC')
    print(f"✓ BTC volatility: {btc_vol:.4f}")
    
    # Should be close to 5% (0.05)
    assert 0.03 < btc_vol < 0.07, f"Expected ~5% volatility, got {btc_vol:.4f}"
```

#### 2. Market Regime Test
```python
def test_market_regime():
    filter = MarketRegimeFilter(volatility_window=300)
    
    # Test different volatility scenarios
    test_cases = [
        (0.01, 0.015, 'CALM'),      # Low volatility
        (0.03, 0.04, 'NORMAL'),     # Normal volatility
        (0.08, 0.12, 'VOLATILE'),   # High volatility
        (0.25, 0.30, 'HIGHLY_VOLATILE')  # Very high volatility
    ]
    
    for btc_vol, eth_vol, expected_regime in test_cases:
        regime = filter.get_market_regime(btc_vol, eth_vol)
        print(f"✓ BTC: {btc_vol:.1%}, ETH: {eth_vol:.1%} → {regime}")
        assert regime == expected_regime, f"Expected {expected_regime}, got {regime}"
```

#### 3. Signal Filtering Test
```python
def test_signal_filtering():
    filter = MarketRegimeFilter(volatility_window=300)
    
    # Test signal filtering in different regimes
    test_cases = [
        ('CALM', False, "Should not filter in calm market"),
        ('NORMAL', False, "Should not filter in normal market"),
        ('VOLATILE', True, "Should filter altcoins in volatile market"),
        ('HIGHLY_VOLATILE', True, "Should filter altcoins in highly volatile market")
    ]
    
    for regime, should_filter, message in test_cases:
        filter_signal, reason = filter.should_filter_signal('SOL/USDT', regime, is_altcoin=True)
        print(f"✓ {regime}: Filter={filter_signal}, Reason={reason}")
        assert filter_signal == should_filter, message
```

#### 4. Regime Persistence Test
```python
def test_regime_persistence():
    filter = MarketRegimeFilter(volatility_window=60)
    filter.regime_persistence = 2  # Require 2 confirmations
    
    # Start in NORMAL regime
    assert filter.current_regime == 'NORMAL'
    
    # Single high volatility reading (should not change regime immediately)
    regime1 = filter.get_market_regime(0.15, 0.18)  # VOLATILE levels
    # Should still be NORMAL due to persistence requirement
    
    # Second high volatility reading (should change regime)
    regime2 = filter.get_market_regime(0.16, 0.19)
    
    print(f"✓ Regime persistence test: {filter.current_regime}")
    # Should now be VOLATILE after persistence requirement met
```

### Expected Test Results
- Volatility calculations should reflect actual market conditions
- Market regime classification should be stable and meaningful
- Signal filtering should work appropriately for different regimes
- Regime persistence should prevent frequent switching

### Post-Test Actions
```bash
git add src/risk/market_regime.py
git add tests/test_market_regime.py
git commit -m "feat: implement market regime filter with volatility monitoring"
```

### Progress Update
Mark Task 12 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 13: Latency Compensation System
**Objective**: Implement dynamic threshold adjustment based on data acquisition latency.

### Implementation Steps

#### 13.1 Create LatencyCompensationManager Class Structure
Create `src/risk/latency.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional
from collections import deque
from datetime import datetime, timedelta
import numpy as np
from loguru import logger

class LatencyCompensationManager:
    def __init__(self, base_thresholds: Dict[str, float]):
        self.base_thresholds = base_thresholds
        self.latency_history = {}  # component -> deque of latency measurements
        self.current_thresholds = base_thresholds.copy()
        self.latency_window = 100  # Keep last 100 measurements
        self.adjustment_factors = {
            'low': 1.0,      # < 50ms
            'medium': 1.2,   # 50-100ms
            'high': 1.5,     # 100-200ms
            'critical': 2.0  # > 200ms
        }
        
    def record_latency(self, component: str, latency_ms: float):
        # Record latency measurement for a component
        pass
        
    def get_current_threshold(self, threshold_type: str) -> float:
        # Get current threshold value adjusted for latency
        pass
        
    def _calculate_latency_adjustment(self, component: str) -> float:
        # Calculate adjustment factor based on recent latency
        pass
```

#### 13.2 Implement Latency Measurement
- **Component-Specific Tracking**: Track latency for different system components
- **Statistical Analysis**: Calculate mean, median, and percentiles
- **Trend Detection**: Identify increasing or decreasing latency trends
- **Outlier Handling**: Filter out anomalous latency measurements

#### 13.3 Add Threshold Adjustment Algorithms
- **Dynamic Scaling**: Increase thresholds during high latency periods
- **Adaptive Algorithms**: Learn optimal adjustments from historical data
- **Component Weighting**: Weight adjustments by component importance
- **Predictive Compensation**: Anticipate latency based on patterns

#### 13.4 Create Performance Optimization
- **Bottleneck Identification**: Identify system components causing delays
- **Caching Strategies**: Implement caching for frequently accessed data
- **Connection Pooling**: Optimize database and API connections
- **Resource Monitoring**: Monitor CPU, memory, and network usage

### Key Implementation Details
- Use high-precision timing for accurate latency measurement
- Implement statistical analysis of latency patterns
- Add predictive latency modeling based on historical data
- Consider different latency sources and their impacts

### Testing Instructions

#### 1. Latency Recording Test
```python
# Create test file: test_latency.py
from src.risk.latency import LatencyCompensationManager

def test_latency_recording():
    base_thresholds = {'order_flow': 0.6, 'liquidity': 0.1}
    manager = LatencyCompensationManager(base_thresholds)
    
    # Record sample latencies
    latencies = [45, 52, 48, 67, 51, 49, 55, 62, 46, 53]
    
    for latency in latencies:
        manager.record_latency('data_acquisition', latency)
    
    # Check latency statistics
    stats = manager.get_latency_stats('data_acquisition')
    print(f"✓ Latency stats: avg={stats['avg']:.1f}ms, p95={stats['p95']:.1f}ms")
    
    assert 45 <= stats['avg'] <= 65, "Average latency should be reasonable"
    assert stats['count'] == len(latencies), "Should record all measurements"
```

#### 2. Threshold Adjustment Test
```python
def test_threshold_adjustment():
    base_thresholds = {'order_flow': 0.6}
    manager = LatencyCompensationManager(base_thresholds)
    
    # Record low latency (should not adjust threshold much)
    for _ in range(10):
        manager.record_latency('data_acquisition', 30)  # Low latency
    
    low_latency_threshold = manager.get_current_threshold('order_flow')
    print(f"✓ Low latency threshold: {low_latency_threshold:.3f}")
    
    # Record high latency (should increase threshold)
    for _ in range(10):
        manager.record_latency('data_acquisition', 150)  # High latency
    
    high_latency_threshold = manager.get_current_threshold('order_flow')
    print(f"✓ High latency threshold: {high_latency_threshold:.3f}")
    
    # High latency should result in higher threshold
    assert high_latency_threshold > low_latency_threshold, \
           "High latency should increase thresholds"
```

#### 3. Performance Analysis Test
```python
def test_performance_analysis():
    base_thresholds = {'order_flow': 0.6}
    manager = LatencyCompensationManager(base_thresholds)
    
    # Simulate different components with different latencies
    components = {
        'data_acquisition': [45, 50, 48, 52, 49],  # Good performance
        'signal_processing': [15, 18, 16, 20, 17], # Excellent performance
        'database_write': [85, 92, 88, 95, 90]     # Poor performance
    }
    
    for component, latencies in components.items():
        for latency in latencies:
            manager.record_latency(component, latency)
    
    # Identify bottlenecks
    bottlenecks = manager.identify_bottlenecks()
    print(f"✓ Performance bottlenecks: {bottlenecks}")
    
    # Database should be identified as bottleneck
    assert any('database' in bottleneck for bottleneck in bottlenecks), \
           "Should identify database as bottleneck"
```

#### 4. Predictive Compensation Test
```python
def test_predictive_compensation():
    base_thresholds = {'order_flow': 0.6}
    manager = LatencyCompensationManager(base_thresholds)
    
    # Simulate increasing latency trend
    for i in range(20):
        latency = 50 + i * 2  # Increasing from 50ms to 88ms
        manager.record_latency('data_acquisition', latency)
    
    # Should predict continued increase and adjust accordingly
    predicted_adjustment = manager._calculate_latency_adjustment('data_acquisition')
    print(f"✓ Predicted adjustment factor: {predicted_adjustment:.3f}")
    
    assert predicted_adjustment > 1.0, "Should predict need for adjustment"
```

### Expected Test Results
- Latency measurements should be recorded accurately
- Threshold adjustments should reflect current latency conditions
- Performance analysis should identify bottlenecks correctly
- Predictive compensation should anticipate latency trends

### Post-Test Actions
```bash
git add src/risk/latency.py
git add tests/test_latency.py
git commit -m "feat: implement latency compensation with dynamic thresholds"
```

### Progress Update
Mark Task 13 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 14: Cool-Down Period Management
**Objective**: Create signal blocking mechanism for specific trading pairs after recent signals.

### Implementation Steps

#### 14.1 Create CooldownManager Class Structure
Create `src/risk/cooldown.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

class CooldownManager:
    def __init__(self):
        self.cooldown_periods = {}  # symbol -> expiry_time
        self.default_cooldown_minutes = 15
        self.symbol_specific_cooldowns = {}  # symbol -> custom_minutes
        self.success_rates = {}  # symbol -> success_rate
        self.dynamic_adjustment = True
        
    def set_cooldown(self, symbol: str, minutes: Optional[int] = None):
        # Set cooldown period for a symbol
        pass
        
    def is_in_cooldown(self, symbol: str) -> bool:
        # Check if symbol is currently in cooldown period
        pass
        
    def get_remaining_cooldown(self, symbol: str) -> Optional[int]:
        # Get remaining cooldown time in seconds
        pass
        
    def cleanup_expired_cooldowns(self):
        # Remove expired cooldowns from memory
        pass
```

#### 14.2 Implement Cooldown Logic
- **Time-Based Cooldowns**: Set cooldown periods after signal generation
- **Symbol-Specific Durations**: Allow different cooldown periods per trading pair
- **Expiration Tracking**: Track when cooldowns expire
- **Memory Management**: Clean up expired cooldowns automatically

#### 14.3 Add Dynamic Cooldown Adjustment
- **Success Rate Tracking**: Monitor signal success rates by symbol
- **Adaptive Periods**: Longer cooldowns for unsuccessful signals
- **Market Condition Adjustment**: Modify cooldowns based on volatility
- **Algorithm-Specific Cooldowns**: Different cooldowns for different algorithms

#### 14.4 Create Monitoring and Reporting
- **Cooldown Status Reporting**: Provide current cooldown status
- **Effectiveness Metrics**: Track cooldown impact on performance
- **Configuration Management**: Allow runtime cooldown adjustments
- **Persistence**: Optionally persist cooldowns across restarts

### Key Implementation Details
- Use efficient data structures for cooldown tracking
- Implement thread-safe cooldown operations
- Add persistence for cooldown periods across system restarts
- Consider different cooldown strategies for different market conditions

### Testing Instructions

#### 1. Basic Cooldown Test
```python
# Create test file: test_cooldown.py
from datetime import datetime, timedelta
from src.risk.cooldown import CooldownManager
import time

def test_basic_cooldown():
    manager = CooldownManager()
    
    # Set cooldown for a symbol
    manager.set_cooldown('SOL/USDT', minutes=1)  # Short cooldown for testing
    
    # Check cooldown status
    is_cooldown = manager.is_in_cooldown('SOL/USDT')
    remaining = manager.get_remaining_cooldown('SOL/USDT')
    
    print(f"✓ In cooldown: {is_cooldown}")
    print(f"✓ Remaining time: {remaining}s")
    
    assert is_cooldown, "Should be in cooldown immediately after setting"
    assert remaining > 0, "Should have remaining time"
    
    # Wait for cooldown to expire
    time.sleep(65)  # Wait slightly more than 1 minute
    
    is_cooldown_after = manager.is_in_cooldown('SOL/USDT')
    assert not is_cooldown_after, "Should not be in cooldown after expiry"
```

#### 2. Dynamic Adjustment Test
```python
def test_dynamic_adjustment():
    manager = CooldownManager()
    manager.dynamic_adjustment = True
    
    # Simulate unsuccessful signals (should increase cooldown)
    for _ in range(5):
        manager.record_signal_result('SOL/USDT', success=False)
    
    # Set cooldown (should be longer due to poor success rate)
    manager.set_cooldown('SOL/USDT')
    
    # Check if cooldown was adjusted
    remaining = manager.get_remaining_cooldown('SOL/USDT')
    default_cooldown_seconds = manager.default_cooldown_minutes * 60
    
    print(f"✓ Adjusted cooldown: {remaining}s vs default {default_cooldown_seconds}s")
    
    # Should be longer than default due to poor performance
    assert remaining > default_cooldown_seconds, \
           "Poor performance should result in longer cooldown"
```

#### 3. Cleanup Test
```python
def test_cleanup():
    manager = CooldownManager()
    
    # Set multiple cooldowns with very short duration
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    
    for symbol in symbols:
        manager.cooldown_periods[symbol] = datetime.utcnow() + timedelta(seconds=1)
    
    # Verify all are in cooldown
    active_before = sum(1 for symbol in symbols if manager.is_in_cooldown(symbol))
    print(f"✓ Active cooldowns before cleanup: {active_before}")
    assert active_before == len(symbols), "All symbols should be in cooldown"
    
    # Wait for expiry
    time.sleep(2)
    
    # Run cleanup
    manager.cleanup_expired_cooldowns()
    
    # Verify cleanup worked
    active_after = sum(1 for symbol in symbols if manager.is_in_cooldown(symbol))
    print(f"✓ Active cooldowns after cleanup: {active_after}")
    assert active_after == 0, "No symbols should be in cooldown after cleanup"
```

#### 4. Symbol-Specific Cooldown Test
```python
def test_symbol_specific_cooldowns():
    manager = CooldownManager()
    
    # Set different cooldowns for different symbols
    manager.symbol_specific_cooldowns['BTC/USDT'] = 30  # 30 minutes
    manager.symbol_specific_cooldowns['SOL/USDT'] = 5   # 5 minutes
    
    # Set cooldowns
    manager.set_cooldown('BTC/USDT')
    manager.set_cooldown('SOL/USDT')
    
    btc_remaining = manager.get_remaining_cooldown('BTC/USDT')
    sol_remaining = manager.get_remaining_cooldown('SOL/USDT')
    
    print(f"✓ BTC cooldown: {btc_remaining}s")
    print(f"✓ SOL cooldown: {sol_remaining}s")
    
    # BTC should have longer cooldown
    assert btc_remaining > sol_remaining, \
           "BTC should have longer cooldown than SOL"
```

### Expected Test Results
- Cooldown periods should be set and tracked correctly
- Cooldown status checks should return accurate results
- Cleanup should remove only expired cooldowns
- Dynamic adjustments should work based on success rates

### Post-Test Actions
```bash
git add src/risk/cooldown.py
git add tests/test_cooldown.py
git commit -m "feat: implement cooldown period management system"
```

### Progress Update
Mark Task 14 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Phase A2 Summary

### Completed Tasks:
- ✅ Task 7: DEX Order Flow Algorithm
- ✅ Task 8: DEX Liquidity Event Algorithm
- ✅ Task 9: Volume-Price Correlation Algorithm
- ✅ Task 10: Signal Combination Logic
- ✅ Task 11: Pre-Trade Slippage Analysis
- ✅ Task 12: Market Regime Filter
- ✅ Task 13: Latency Compensation System
- ✅ Task 14: Cool-Down Period Management

### Milestone 2 Checkpoint:
**Rule-Based Signal System Operational**

Verify all algorithm components are working:
1. Order flow imbalance detection generating signals
2. Liquidity event detection identifying significant changes
3. Volume-price correlation detecting position formation
4. Signal aggregation combining multiple algorithms
5. Risk management systems filtering signals appropriately
6. All components integrated and tested

### Risk Management Systems Verification:
1. Slippage analysis preventing unprofitable trades
2. Market regime filter adapting to volatility conditions
3. Latency compensation adjusting thresholds dynamically
4. Cooldown management preventing signal spam

### Integration Testing:
Run comprehensive integration tests to verify:
- Data flows correctly between all components
- Signal generation pipeline works end-to-end
- Risk management systems properly filter signals
- All algorithms can work together without conflicts

### Next Steps:
Proceed to **[Phase A3: Trading & Validation](ATS_GUIDE_PHASE_A3_TRADING.md)** (Tasks 15-16.1)

### Troubleshooting:
- **Algorithm not triggering**: Check threshold configurations and input data quality
- **Signal conflicts**: Verify signal aggregation logic and algorithm weights
- **Performance issues**: Review latency compensation and optimize bottlenecks
- **Risk filter too aggressive**: Adjust market regime and slippage thresholds

---

**Phase A2 Complete!** Continue with [ATS_GUIDE_PHASE_A3_TRADING.md](ATS_GUIDE_PHASE_A3_TRADING.md)
