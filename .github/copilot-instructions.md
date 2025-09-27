# Copilot Instructions for Automated Trading System (ATS)

## Project Overview
This is an **early-stage** Automated Trading System that uses DEX data as leading indicators for CEX trading signals. The system follows a structured 3-phase implementation with 32 tasks, designed for Windows 11 local development.

**Key Principle:** This is NOT arbitrage - we predict CEX price movements using DEX market microstructure anomalies.

## Project Structure & Navigation
- **Root Documentation**: `README.md`, `ATS_IMPLEMENTATION_GUIDE.md` (master navigation)
- **Implementation Guides**: `implementation_guides/ATS_GUIDE_PHASE_*.md` (A1-A3, B1-B2, C)
- **Progress Tracking**: `implementation_guides/ATS_IMPLEMENTATION_PROGRESS.md`
- **Architecture**: `implementation_guides/ATS_strategic_concept.txt`

## Critical Implementation Patterns

### Database Schema (Signal Model)
All trading events stored in central `signals` table with 40+ fields. **Always reference `src/database/models.py`** for the complete Signal model:

```python
# Key fields every signal must populate:
signal = Signal(
    timestamp=datetime.now(timezone.utc),  # Always UTC with timezone
    pair_symbol="SOL/USDT",                 # Format: BASE/QUOTE
    signal_type="BUY",                      # "BUY" or "SELL" only
    predicted_reward=0.0023,                # Float between -1.0 and 1.0
    dex_price=Decimal('123.45'),           # DECIMAL(20,8) for precision
    cex_price=Decimal('123.50'),           # DECIMAL(20,8) for precision
    market_regime="normal",                 # "normal", "high_volatility", "bear"
    estimated_slippage_pct=0.001,          # Risk calculation input
    signal_strength=0.85,                  # 0.0 to 1.0 confidence score
    algorithm_version="1.0",               # Track algorithm versions
    signal_source="dex_orderflow"          # Algorithm identifier
)
```

### Data Connectors Architecture
**Three-tier data architecture** - never access exchanges directly:

1. **CEXConnector** (`src/data/cex_connector.py`): CCXT Pro for centralized exchanges
2. **DEXConnector** (`src/data/dex_connector.py`): Birdeye API for decentralized exchanges
3. **DataSyncManager** (`src/data/sync_manager.py`): Latency-compensated synchronization

```python
# Always use sync manager, never direct connector access:
sync_manager = DataSyncManager()
await sync_manager.add_connector('binance_cex', cex_connector)
await sync_manager.add_connector('raydium_dex', dex_connector)
await sync_manager.start_sync(['SOL/USDT'])
```

### Logging & Error Handling
**Loguru-based logging** with structured format. **Always use `config/logging_config.py`**:

```python
from config.logging_config import get_logger
logger = get_logger("module.submodule")  # Hierarchical naming

# Critical logging patterns:
logger.info("Starting {task} for {pair}", task="signal_generation", pair="SOL/USDT")
logger.error("Failed {operation}: {error}", operation="api_call", error=str(e))
logger.debug("Latency: {latency_ms}ms, Quality: {score}", latency_ms=45, quality_score=0.95)
```

### Testing Patterns
**Async-first testing** with real API validation. Reference `tests/test_*.py` files:

```python
# Test structure pattern:
async def test_feature():
    """Test docstring describing what validates"""
    print("=== Test Name ===")
    try:
        # Test implementation
        result = await some_async_operation()
        assert result is not None, "Result should not be None"
        print("✓ Test passed")
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

# Run all tests:
if __name__ == "__main__":
    asyncio.run(run_all_tests())
```

## Development Workflows

### 3-Phase Development Strategy
- **Phase A (Tasks 1-16.1)**: Infrastructure & Data Foundation (4-6 weeks)
  - A1: Setup & Infrastructure (Environment, Database, Data Integration)
  - A2: Algorithms & Risk Management (Signal algorithms, risk systems)
  - A3: Trading & Validation (Paper trading, notifications)
- **Phase B (Tasks 17-26)**: ML & Execution (8-12 weeks)
  - B1: Execution System (Order management, position tracking)
  - B2: ML Pipeline (Feature engineering, model training, backtesting)
- **Phase C (Tasks 27-32)**: Production & Maintenance (3-5 weeks)

### Task-Driven Development
- Follow sequential task numbering (Task 1 → Task 32)
- Each task has clear deliverables and acceptance criteria
- Update `ATS_IMPLEMENTATION_PROGRESS.md` after completing tasks
- Reference specific implementation guides for detailed instructions

### Windows 11 Development Environment
```powershell
# Activate environment (required for all Python operations):
ats_env\Scripts\activate

# Database operations:
docker ps  # Check TimescaleDB container
python src/database/setup.py  # Database verification

# Testing (run after any changes):
python tests/test_cex_connector.py
python tests/test_dex_connector.py
python tests/test_sync_manager.py
```

## Key Implementation Patterns

### Signal Generation Algorithms
Implement these three core detectors in `src/algorithms/`:
1. **DEX Order Flow Imbalance** - 10-30 second aggressive trade volume analysis
2. **DEX Liquidity Event Detection** - Rate of change, not absolute amounts
3. **Volume-Price Correlation** - High volume + minimal price movement patterns

### Risk Management Rules
- **Pre-trade validation:** `if (predicted_profit - estimated_slippage) < 0: cancel_trade()`
- **Market regime filtering:** Halt altcoin signals during high BTC/ETH volatility
- **Cool-down periods:** 15-minute blocks per trading pair after signals
- **Latency compensation:** Tighten thresholds during high-latency periods (>200ms)

### Algorithm Implementation Pattern
```python
class AlgorithmAnalyzer:
    def __init__(self, window_seconds: int = 30):
        self.window_seconds = window_seconds
        self.signal_cooldowns = {}  # symbol -> last signal time
        self.cooldown_period = 60   # seconds
        self.signal_history = deque(maxlen=1000)

    def add_data(self, symbol: str, data: Dict):
        """Add new data point to analysis window"""
        # Implementation here
        pass
```

## Technology Stack Expectations

### Data Sources
- **DEX data:** Birdeye API for real-time streams
- **CEX data:** CCXT Pro for WebSocket connections
- **Historical:** Kaiko/Amberdata for backtesting (tick-by-tick + L2 required)

### Storage & Infrastructure
- **Operational DB:** PostgreSQL/TimescaleDB for real-time data
- **Analytics:** AWS S3/Google BigQuery for long-term storage
- **Deployment:** VPS with geographic proximity to exchanges (latency critical)

### ML Pipeline (Phase B)
- **Model type:** Gradient Boosting (LightGBM/XGBoost) for regression
- **Target:** `reward_score` with exponential time decay formula
- **Retraining:** Automated weekly with maintenance agent monitoring

## Code Quality Standards

### Type Hints & Documentation
```python
from typing import Dict, List, Optional, Callable
from loguru import logger

async def process_signal(data: Dict[str, Any]) -> Optional[Signal]:
    """
    Process raw market data into trading signal.

    Args:
        data: Raw market data dictionary

    Returns:
        Signal object if valid signal generated, None otherwise
    """
```

### Error Handling Pattern
```python
try:
    result = await risky_operation()
except ccxt.NetworkError as e:
    logger.error("Network error in {operation}: {error}", operation="api_call", error=str(e))
    await handle_retry()
except Exception as e:
    logger.error("Unexpected error: {error}", error=str(e))
    raise  # Re-raise for higher level handling
```

### Configuration Management
- Use `.env` files for API keys and sensitive configuration
- Separate config files for different environments (dev/test/prod)
- All exchange API credentials stored securely outside version control

## Critical Success Factors
- **Latency is everything** - Use co-located infrastructure and measure every operation
- **Data quality over quantity** - Better to have fewer, high-quality signals than noisy data
- **Risk management is non-negotiable** - Never skip pre-trade validation
- **Multi-algorithm confirmation** - Single algorithm signals are typically false positives

When implementing, prioritize the real-time data pipeline and risk management over ML sophistication initially.