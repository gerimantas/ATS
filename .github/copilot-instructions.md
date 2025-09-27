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

### Plugin Architecture (Current Refactoring)
**Modular plugin system** for DEX scanners and CEX verifiers. Never modify core logic - extend via plugins:

```python
# scanners/dexscreener_scanner.py - Standardized interface
async def scan(session: aiohttp.ClientSession) -> List[Dict]:
    """Returns standardized format: [{'cex_symbol': str, 'dex_pair_address': str, 'score': float}]"""
    return []

# config.py - Plugin configuration
ENABLED_DEX_SCANNERS = ['dexscreener_scanner']
ENABLED_CEX_VERIFIERS = ['coingecko_verifier']
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
# Test structure pattern from tests/test_algorithms_integration.py:
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

### Task-Driven Development
- Follow sequential task numbering (Task 1 → Task 32)
- Each task has clear deliverables and acceptance criteria
- Update `implementation_guides/ATS_IMPLEMENTATION_PROGRESS.md` after completing tasks
- Reference specific implementation guides for detailed instructions

### 3-Phase Development Strategy
- **Phase A (Tasks 1-16.1)**: Infrastructure & Data Foundation (4-6 weeks)
  - A1: Setup & Infrastructure (Environment, Database, Data Integration)
  - A2: Algorithms & Risk Management (Signal algorithms, risk systems)
  - A3: Trading & Validation (Paper trading, notifications)
- **Phase B (Tasks 17-26)**: ML & Execution (8-12 weeks)
  - B1: Execution System (Order management, position tracking)
  - B2: ML Pipeline (Feature engineering, model training, backtesting)
- **Phase C (Tasks 27-32)**: Production & Maintenance (3-5 weeks)

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

## Development Workflows

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

### Task-Driven Development
- Follow sequential task numbering (Task 1 → Task 32)
- Each task has clear deliverables and acceptance criteria
- Update `ATS_IMPLEMENTATION_PROGRESS.md` after completing tasks
- Reference specific implementation guides for detailed instructions

### 3-Phase Development Strategy
- **Phase A (Tasks 1-16.1)**: Infrastructure & Data Foundation (4-6 weeks)
  - A1: Setup & Infrastructure (Environment, Database, Data Integration)
  - A2: Algorithms & Risk Management (Signal algorithms, risk systems)
  - A3: Trading & Validation (Paper trading, notifications)
- **Phase B (Tasks 17-26)**: ML & Execution (8-12 weeks)
  - B1: Execution System (Order management, position tracking)
  - B2: ML Pipeline (Feature engineering, model training, backtesting)
- **Phase C (Tasks 27-32)**: Production & Maintenance (3-5 weeks)

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

## Essential Development Patterns

### Windows 11 Environment Setup
**Always activate virtual environment before any Python operations:**
```powershell
# Required for all Python development:
ats_env\Scripts\activate

# Check database status:
docker ps

# Run database setup:
python src/database/setup.py
```

### Import Structure & Dependencies
**Key imports to understand the system:**
```python
# Core dependencies (from requirements.txt):
import ccxt.pro as ccxtpro          # CEX WebSocket connections
import aiohttp                      # Async HTTP client
from loguru import logger           # Structured logging
import pandas as pd                 # Data manipulation
import numpy as np                  # Numerical computations
from sqlalchemy import create_engine # Database operations
from datetime import datetime, timezone  # UTC timestamps only

# Internal modules:
from config.logging_config import get_logger, setup_logging
from src.database.models import Signal  # Always reference this model
from src.data.sync_manager import DataSyncManager
```

### Algorithm Base Class Pattern
**All algorithms follow this structure (from `src/algorithms/order_flow.py`):**
```python
class AlgorithmAnalyzer:
    def __init__(self, window_seconds: int = 30):
        self.window_seconds = window_seconds
        self.signal_cooldowns = {}  # symbol -> last signal time
        self.cooldown_period = 60   # seconds
        self.signal_history = deque(maxlen=1000)
        
    def add_data(self, symbol: str, data: Dict):
        """Add new data point to analysis window"""
        pass
        
    def is_signal_triggered(self, symbol: str) -> Tuple[bool, str]:
        """Check if signal conditions are met"""
        return False, ""
```

### Signal Processing Pipeline
**Complete signal flow (from integration tests):**
```python
# 1. Initialize components
order_flow = OrderFlowAnalyzer(window_seconds=30)
liquidity = LiquidityAnalyzer(window_seconds=60)
aggregator = SignalAggregator(confirmation_threshold=2)

# 2. Add market data
order_flow.add_trade('SOL/USDT', trade_data)
liquidity.add_liquidity_data('SOL/USDT', liquidity_data)

# 3. Check individual signals
signal_triggered, signal_type = order_flow.is_signal_triggered('SOL/USDT')

# 4. Aggregate for confirmation
if signal_triggered:
    combined = aggregator.add_algorithm_signal('SOL/USDT', signal_type, 'order_flow', 0.8)
```

### Database Operations Pattern
**Always use SQLAlchemy ORM (from `src/database/models.py`):**
```python
from sqlalchemy.orm import sessionmaker
from src.database.models import Signal

# Create session
Session = sessionmaker(bind=engine)
session = Session()

# Create signal with all required fields
signal = Signal(
    timestamp=datetime.now(timezone.utc),
    pair_symbol="SOL/USDT",
    signal_type="BUY",
    predicted_reward=0.0023,
    dex_price=Decimal('123.45'),
    cex_price=Decimal('123.50'),
    signal_strength=0.85,
    algorithm_version="1.0",
    signal_source="dex_orderflow"
)

session.add(signal)
session.commit()
```

### Testing Execution Pattern
**Run tests individually after changes:**
```bash
# Algorithm tests (most critical):
python tests/test_order_flow.py
python tests/test_liquidity.py
python tests/test_algorithms_integration.py

# Data integration tests:
python tests/test_cex_connector.py
python tests/test_dex_connector.py
python tests/test_sync_manager.py
```

### Configuration File Structure
**Environment-specific configs:**
- `.env` - API keys and secrets (not in version control)
- `config/logging_config.py` - Logging setup
- `config/` - Other configuration modules

## File Structure & Navigation

### Core Architecture Directories
```
src/
├── algorithms/          # Trading algorithms (order_flow.py, liquidity.py, etc.)
├── data/               # Data connectors (cex_connector.py, dex_connector.py, sync_manager.py)
├── database/           # Database models and setup (models.py, setup.py)
├── risk/               # Risk management (slippage.py, market_regime.py, etc.)
├── trading/            # Trading execution (Phase B)
└── monitoring/         # System monitoring (Phase C)

config/                 # Configuration files (logging_config.py, etc.)
tests/                  # Test files (test_*.py)
scanners/              # DEX scanner plugins
cex_verifiers/         # CEX verification plugins
implementation_guides/ # Phase-specific guides
logs/                  # Log files (auto-generated)
```

### Key Files to Reference
- **`src/database/models.py`**: Complete Signal model definition (40+ fields)
- **`config/logging_config.py`**: Logging setup and get_logger() function
- **`tests/test_algorithms_integration.py`**: Integration testing patterns
- **`main.py`**: System startup and main loop
- **`requirements.txt`**: All dependencies with versions

### Development Workflow Files
- **`implementation_guides/ATS_IMPLEMENTATION_PROGRESS.md`**: Task completion tracking
- **`implementation_guides/ATS_GUIDE_PHASE_*.md`**: Phase-specific instructions
- **`run_dashboard.bat`**: Dashboard startup script

## Quick Reference Commands

### Environment Setup
```powershell
# Always run first:
ats_env\Scripts\activate

# Check system status:
docker ps
python src/database/setup.py
```

### Testing Commands
```powershell
# Core algorithm tests:
python tests/test_algorithms_integration.py
python tests/test_order_flow.py
python tests/test_liquidity.py

# Data integration tests:
python tests/test_cex_connector.py
python tests/test_dex_connector.py
python tests/test_sync_manager.py
```

### System Startup
```powershell
# Main system:
python main.py

# Dashboard:
./run_dashboard.bat
```

## AI Agent Priorities

1. **Read the Signal model** (`src/database/models.py`) before implementing any signal-related code
2. **Use hierarchical logging** with `get_logger("module.submodule")` for all logging
3. **Follow async patterns** - all I/O operations should be async
4. **Reference existing algorithms** for implementation patterns
5. **Run relevant tests** after any changes to algorithms or data connectors
6. **Update progress tracking** when completing tasks