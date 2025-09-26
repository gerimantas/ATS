# Copilot Instructions for Automated Trading System (ATS)

## Project Overview
This is an **early-stage** Automated Trading System that uses DEX data as leading indicators for CEX trading signals. The system follows a structured 3-phase implementation with 32 tasks, designed for Windows 11 local development.

**Key Principle:** This is NOT arbitrage - we predict CEX price movements using DEX market microstructure anomalies.

## Project Structure & Navigation
- **Root Documentation**: `README.md`, `ATS_IMPLEMENTATION_GUIDE.md` (master navigation)
- **Implementation Guides**: `implementation_guides/ATS_GUIDE_PHASE_*.md` (A1-A3, B1-B2, C)
- **Progress Tracking**: `implementation_guides/ATS_IMPLEMENTATION_PROGRESS.md` 
- **Architecture**: `implementation_guides/ATS_strategic_concept.txt`

## Implementation Workflow & Patterns

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

### Required Directory Structure
```
ats_project/
├── src/
│   ├── data/          # Data connectors (CCXT Pro, Birdeye API)
│   ├── algorithms/    # Signal generation algorithms
│   ├── risk/          # Risk management systems  
│   ├── ml/            # Machine learning pipeline
│   ├── database/      # PostgreSQL/TimescaleDB models
│   ├── trading/       # Paper/live trading execution
│   └── monitoring/    # System monitoring & alerts
├── config/            # Environment configurations
├── tests/             # Test suites per module
├── logs/              # System logs
└── data/              # Local data cache/storage
```

## Key Implementation Patterns

### Database Schema (signals table)
All events stored in central `signals` table with these critical fields:
- Time-series: `timestamp`, `pair_symbol`, `signal_type` 
- ML features: `predicted_reward`, `actual_reward`, latency metrics
- Risk data: `estimated_slippage_pct`, `actual_slippage_pct`, `market_regime`

### Signal Generation Algorithms
Implement these three core detectors:
1. **DEX Order Flow Imbalance** - 10-30 second aggressive trade volume analysis
2. **DEX Liquidity Event Detection** - Rate of change, not absolute amounts
3. **Volume-Price Correlation** - High volume + minimal price movement patterns

### Risk Management Rules
- **Pre-trade validation:** Cancel if `(predicted_profit - estimated_slippage) < 0`
- **Market regime filtering:** Halt altcoin signals during high BTC/ETH volatility
- **Cool-down periods:** 15-minute blocks per trading pair after signals
- **Latency compensation:** Tighten thresholds during high-latency periods

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

## Development Workflows

### Windows 11 Development Environment  
- **Python**: Use virtual environment `ats_env\Scripts\activate`
- **Database**: PostgreSQL + TimescaleDB for time-series data
- **Dependencies**: Install via `pip install -r requirements.txt` (defined in Phase A1)
- **Monitoring**: Windows Event Logs + custom monitoring dashboard
- **Firewall**: Configure ports 8000-9000 for API access

### Testing & Validation Approach
- **Backtesting Requirements**: Simulate network latency, realistic slippage, trading fees
- **Data Quality Standards**: Use professional tick-by-tick providers, not free APIs  
- **Paper Trading**: Validate all algorithms before live execution
- **Performance Metrics**: Track `predicted_reward` vs `actual_reward` deviation

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