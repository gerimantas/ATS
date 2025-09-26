# ATS Implementation Guide - Phase A1: Setup & Infrastructure

## Overview

**Phase A1** establishes the foundational infrastructure for the ATS system. This phase focuses on setting up the development environment, database, and core data integration components.

**Duration**: 1-2 weeks  
**Prerequisites**: Windows 11, basic Python knowledge  
**Tasks Covered**: 1-6

---

## Task 1: Environment Setup
**Objective**: Set up Python development environment with all required dependencies on Windows 11.

### Implementation Steps

#### 1.1 Install Python 3.9+ on Windows 11
- Download Python from [python.org](https://python.org) (ensure "Add to PATH" is checked during installation)
- Verify installation: Open Command Prompt and run `python --version`
- Install pip if not included: `python -m ensurepip --upgrade`

#### 1.2 Create Project Structure
Create the following directory structure:
```
ats_project/
├── src/
│   ├── data/          # Data connectors and managers
│   ├── algorithms/    # Trading signal algorithms
│   ├── risk/          # Risk management systems
│   ├── ml/            # Machine learning components
│   ├── database/      # Database models and connections
│   ├── trading/       # Paper trading and execution
│   └── monitoring/    # Monitoring and notifications
├── config/            # Configuration files
├── tests/             # Test suites
├── logs/              # Log files
└── data/              # Local data storage
```

#### 1.3 Create Virtual Environment
```bash
# Navigate to project directory
cd ats_project

# Create virtual environment
python -m venv ats_env

# Activate environment (Windows)
ats_env\Scripts\activate

# Verify activation
where python  # Should point to venv python
```

#### 1.4 Install Dependencies
Create `requirements.txt` with the following content:
```
ccxt-pro>=4.0.0
pandas>=2.0.0
numpy>=1.24.0
asyncio
websockets>=11.0.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
scikit-learn>=1.3.0
lightgbm>=4.0.0
xgboost>=1.7.0
optuna>=3.0.0
fastapi>=0.100.0
uvicorn>=0.23.0
aiohttp>=3.8.0
python-dotenv>=1.0.0
pydantic>=2.0.0
loguru>=0.7.0
python-telegram-bot>=20.0.0
```

Install dependencies:
```bash
pip install -r requirements.txt
```

#### 1.5 Configure Windows 11 Specific Settings
- **Windows Defender**: Add Python processes to exclusions
  - Open Windows Security → Virus & threat protection → Exclusions
  - Add folder: `C:\path\to\ats_project\ats_env\`
- **Windows Firewall**: Configure for API access (ports 8000-9000)
  - Open Windows Defender Firewall → Advanced settings
  - Create inbound rules for ports 8000-9000

#### 1.6 Set Up Logging System
Create `config/logging_config.py`:
```python
# Example logging configuration structure
from loguru import logger
import sys

def setup_logging():
    # Remove default handler
    logger.remove()
    
    # Add console handler
    logger.add(sys.stdout, level="INFO")
    
    # Add file handlers
    logger.add("logs/ats_{time}.log", rotation="1 day", retention="30 days")
    logger.add("logs/errors_{time}.log", level="ERROR", rotation="1 week")
```

### Key Implementation Details
- Use `.env` file for sensitive configuration (never commit to git)
- Implement proper error handling for environment setup
- Create activation scripts for easy environment management
- Set up IDE integration (VS Code recommended with Python extension)

### Testing Instructions

#### 1. Environment Verification Test
```bash
# Test virtual environment activation
where python  # Should point to venv python
python --version  # Verify version 3.9+

# Test core imports
python -c "import ccxt, pandas, numpy; print('Core dependencies OK')"
python -c "import sklearn, lightgbm, xgboost; print('ML dependencies OK')"
python -c "import fastapi, uvicorn; print('Web dependencies OK')"
```

#### 2. Project Structure Test
```bash
# Verify all directories created
dir src config tests logs data

# Test Python path setup
python -c "import sys; print('\n'.join(sys.path))"
```

#### 3. Logging System Test
```python
# Create test file: test_logging.py
from config.logging_config import setup_logging
from loguru import logger

setup_logging()
logger.info("Environment setup test")
logger.error("Error logging test")
# Check logs directory for output files
```

### Expected Test Results
- All Python imports should succeed without errors
- Project structure should match specified layout
- Logging should create appropriate log files in logs/ directory
- Virtual environment should be properly activated

### Post-Test Actions
```bash
# Initialize git repository
git init

# Create .gitignore
echo "ats_env/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore
echo ".env" >> .gitignore
echo "logs/*.log" >> .gitignore

# Add and commit
git add .
git commit -m "feat: initial environment setup for Windows 11"
```

### Progress Update
Mark Task 1 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 2: Database Setup (Docker-based)
**Objective**: Set up TimescaleDB using Docker for time-series data on Windows 11.

### Implementation Steps

#### 2.1 Install Docker Desktop on Windows 11
- Download Docker Desktop from [docker.com/get-started/get-docker/](https://docs.docker.com/get-started/get-docker/)
- Run the installer and follow the installation wizard
- Restart your computer if prompted
- Verify Docker installation: Open Command Prompt and run `docker --version`
- Ensure Docker Desktop is running (check system tray)

#### 2.2 Deploy TimescaleDB Container
```bash
# Pull TimescaleDB-HA image with PostgreSQL 17
docker pull timescale/timescaledb-ha:pg17

# Run TimescaleDB container
docker run -d --name timescaledb -p 5432:5432 -e POSTGRES_PASSWORD=your_secure_password_here timescale/timescaledb-ha:pg17
```

**Important Notes:**
- Replace `your_secure_password_here` with a strong password
- No volume mapping (`-v`) to avoid Windows permission issues
- Data stored inside container (for development use)
- For production, consider Docker named volumes

#### 2.3 Create ATS Database and User
Connect to the TimescaleDB container:
```bash
docker exec -it timescaledb psql -U postgres
```

Execute these SQL commands:
```sql
-- Create dedicated user for ATS
CREATE USER ats_user WITH PASSWORD 'your_secure_password_here';

-- Create database
CREATE DATABASE ats_db OWNER ats_user;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE ats_db TO ats_user;

-- Connect to ats_db
\c ats_db

-- Enable TimescaleDB extension (pre-installed in container)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Grant schema permissions
GRANT USAGE ON SCHEMA public TO ats_user;
GRANT CREATE ON SCHEMA public TO ats_user;

-- Exit psql
\q
```

#### 2.4 Configure Connection Settings
Create `.env` file in project root:
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ats_db
DB_USER=ats_user
DB_PASSWORD=your_secure_password_here

# API Keys (add as needed)
BINANCE_API_KEY=
BINANCE_API_SECRET=
BIRDEYE_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

The database connection module is already implemented in `src/database/connection.py` with:
- Environment variable configuration
- Connection pooling and error handling
- TimescaleDB extension verification
- Session management with context managers

#### 2.5 Verify Database Setup
Run the database setup script:
```bash
# Activate virtual environment
ats_env\Scripts\activate

# Run setup verification
python src/database/setup.py
```

### Key Implementation Details
- **Docker-based**: No manual PostgreSQL installation required
- **TimescaleDB-HA**: Includes PostgreSQL 17 + TimescaleDB + extensions
- **Windows 11 Optimized**: Avoids common permission issues
- **Development Ready**: Container includes all database tools (psql, etc.)
- **Port Mapping**: Database accessible on localhost:5432
- **Existing Integration**: Works with implemented connection modules

### Testing Instructions

#### 1. Container Status Test
```bash
# Check if container is running
docker ps

# View container logs
docker logs timescaledb

# Expected: Container should be running and healthy
```

#### 2. Database Connection Test
```python
# Create test file: test_docker_database.py
import psycopg2
from src.database.connection import get_database_url, test_database_connection

# Test direct connection
try:
    conn = psycopg2.connect(
        host="localhost",
        database="ats_db", 
        user="ats_user",
        password="your_secure_password_here"
    )
    print("✓ Direct connection successful")
    conn.close()
except Exception as e:
    print(f"✗ Direct connection failed: {e}")

# Test connection module
if test_database_connection():
    print("✓ Database connection module working")
else:
    print("✗ Database connection module failed")
```

#### 3. TimescaleDB Extension Test
```bash
# Connect to container and check extensions
docker exec -it timescaledb psql -U postgres -d ats_db -c "\dx"

# Expected output should include:
# - timescaledb
# - timescaledb_toolkit (optional)
```

#### 4. Python Integration Test
```bash
# Run comprehensive database tests
python tests/test_database.py

# Expected: All tests should pass
```

#### 5. Performance Test
```python
# Test basic database operations with Docker setup
from sqlalchemy import create_engine, text
from src.database.connection import get_database_url

engine = create_engine(get_database_url())

with engine.connect() as conn:
    # Test table creation
    conn.execute(text("CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, created_at TIMESTAMPTZ DEFAULT NOW());"))
    
    # Test data insertion
    conn.execute(text("INSERT INTO test_table DEFAULT VALUES;"))
    
    # Test data retrieval
    result = conn.execute(text("SELECT COUNT(*) FROM test_table;"))
    count = result.fetchone()[0]
    print(f"✓ Test table has {count} records")
    
    # Cleanup
    conn.execute(text("DROP TABLE test_table;"))
    conn.commit()
```

### Expected Test Results
- Docker container should be running without errors
- Database connection should succeed from Python
- TimescaleDB extension should be available and active
- All database tests should pass
- Basic CRUD operations should work correctly

### Troubleshooting

#### Common Docker Issues
1. **Container not running**
   - Check Docker Desktop status
   - Restart container: `docker restart timescaledb`
   - View logs: `docker logs timescaledb`

2. **Connection refused**
   - Ensure container is running: `docker ps`
   - Check port mapping: `docker port timescaledb`
   - Verify Windows Firewall settings

3. **Permission errors**
   - Avoid volume mapping on Windows
   - Use Docker named volumes for persistence
   - Check container logs for permission issues

4. **TimescaleDB extension missing**
   - Verify correct image: `timescale/timescaledb-ha:pg17`
   - Recreate container if needed
   - Check extensions: `docker exec -it timescaledb psql -U postgres -c "\dx"`

For detailed troubleshooting, refer to [DATABASE_SETUP_INSTRUCTIONS.md](../DATABASE_SETUP_INSTRUCTIONS.md)

### Post-Test Actions
```bash
# Add database configuration (without passwords)
git add .env.example  # Create example without real passwords
git add src/database/connection.py
git add src/database/setup.py
git commit -m "feat: Docker-based TimescaleDB setup for Windows 11"
```

### Progress Update
Mark Task 2 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 3: CEX Data Integration
**Objective**: Implement CCXT Pro integration for real-time L2 order book data from centralized exchanges.

### Implementation Steps

#### 3.1 Create CEX Connector Class Structure
Create `src/data/cex_connector.py`:

```python
# Example class structure - implement full functionality
import ccxt.pro as ccxt
import asyncio
from typing import Dict, List, Optional
from loguru import logger
import time

class CEXConnector:
    def __init__(self, exchange_id: str, api_key: str, api_secret: str):
        # Initialize exchange with proper configuration
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'rateLimit': 100,  # Adjust based on exchange
            'timeout': 30000,
        })
        self.orderbooks = {}
        self.latency_stats = {}
        
    async def connect(self):
        # Establish connection and load markets
        pass
        
    async def subscribe_orderbook(self, symbol: str):
        # Subscribe to real-time L2 orderbook updates
        pass
        
    def _record_latency(self, symbol: str, data_type: str, latency_ms: float):
        # Track latency for performance monitoring
        pass
```

#### 3.2 Implement WebSocket Connection Management
- Handle connection drops and automatic reconnections
- Implement exponential backoff for failed connections
- Add heartbeat mechanism for connection health monitoring
- Create connection pool for multiple symbols

#### 3.3 Add Data Validation Functions
- Validate orderbook structure and data types
- Check for missing or invalid price/volume data
- Implement data quality scoring system
- Add timestamp validation and synchronization

#### 3.4 Configure Windows 11 Specific Settings
- Add firewall rules for exchange API endpoints
- Configure Windows Defender exclusions for network processes
- Set up network monitoring for connection issues

### Key Implementation Details
- Use asyncio for concurrent operations
- Implement proper rate limiting to avoid API bans
- Store API credentials securely in environment variables
- Add comprehensive logging for debugging

### Testing Instructions

#### 1. Connection Test
```python
# Create test file: test_cex_connector.py
import asyncio
from src.data.cex_connector import CEXConnector
import os

async def test_connection():
    # Test basic connection (use sandbox/testnet keys)
    connector = CEXConnector('binance', 
                           os.getenv('BINANCE_API_KEY'), 
                           os.getenv('BINANCE_API_SECRET'))
    
    try:
        await connector.connect()
        print("✓ Exchange connection successful")
        
        # Test market data loading
        markets = await connector.exchange.load_markets()
        print(f"✓ Loaded {len(markets)} markets")
    except Exception as e:
        print(f"✗ Connection failed: {e}")

# Run test
asyncio.run(test_connection())
```

#### 2. Orderbook Subscription Test
```python
async def test_orderbook():
    connector = CEXConnector('binance', api_key, api_secret)
    
    try:
        # Test orderbook subscription
        await connector.subscribe_orderbook('BTC/USDT')
        
        # Wait for data and verify structure
        await asyncio.sleep(5)
        orderbook = connector.orderbooks.get('BTC/USDT')
        
        if orderbook and 'bids' in orderbook and 'asks' in orderbook:
            print("✓ Orderbook data received and validated")
            print(f"  Bids: {len(orderbook['bids'])}, Asks: {len(orderbook['asks'])}")
        else:
            print("✗ Invalid orderbook structure")
    except Exception as e:
        print(f"✗ Orderbook test failed: {e}")
```

#### 3. Latency Measurement Test
```python
async def test_latency():
    connector = CEXConnector('binance', api_key, api_secret)
    
    # Run for 30 seconds to collect latency data
    await asyncio.sleep(30)
    
    latency_stats = connector.get_latency_stats('BTC/USDT')
    if latency_stats:
        print(f"✓ Average latency: {latency_stats.avg_latency}ms")
        print(f"  Min: {latency_stats.min_latency}ms, Max: {latency_stats.max_latency}ms")
    else:
        print("✗ No latency data collected")
```

### Expected Test Results
- Connection should establish without errors
- Orderbook data should be received and properly structured
- Latency measurements should be recorded and accessible
- No API rate limit violations

### Post-Test Actions
```bash
git add src/data/cex_connector.py
git add tests/test_cex_connector.py
git commit -m "feat: implement CEX data integration with CCXT Pro"
```

### Progress Update
Mark Task 3 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 4: DEX Data Integration
**Objective**: Integrate Birdeye API for real-time DEX trading data and liquidity information.

### Implementation Steps

#### 4.1 Create DEX Connector Class Structure
Create `src/data/dex_connector.py`:

```python
# Example class structure - implement full functionality
import aiohttp
import asyncio
from typing import Dict, List, Optional
from loguru import logger
import time

class DEXConnector:
    def __init__(self, api_key: str, base_url: str = "https://public-api.birdeye.so"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        self.rate_limiter = {}  # Track API usage
        self.max_requests_per_day = 1000  # Free tier limit
        
    async def connect(self):
        # Initialize HTTP session with proper headers
        pass
        
    async def get_trades_stream(self, symbol: str):
        # Get real-time trades for a symbol
        pass
        
    async def get_liquidity_info(self, symbol: str):
        # Get liquidity pool information
        pass
```

#### 4.2 Implement Free Tier API Management
- Track API call counts and daily limits
- Implement request batching to optimize usage
- Add fallback mechanisms for rate limit exceeded
- Cache frequently requested data

#### 4.3 Add Data Transformation Functions
- Normalize DEX data to match internal format
- Convert between different token address formats
- Handle missing or incomplete data gracefully
- Implement data quality checks

#### 4.4 Configure Windows 11 Networking
- Ensure HTTPS connections work properly
- Configure proxy settings if needed
- Add network timeout handling

### Key Implementation Details
- Respect free tier API limits (typically 100-1000 requests/day)
- Implement intelligent caching to reduce API calls
- Use aiohttp for async HTTP requests
- Add comprehensive error handling for network issues

### Testing Instructions

#### 1. API Connection Test
```python
# Create test file: test_dex_connector.py
import asyncio
from src.data.dex_connector import DEXConnector
import os

async def test_api_connection():
    connector = DEXConnector(os.getenv('BIRDEYE_API_KEY'))
    
    try:
        await connector.connect()
        print("✓ Birdeye API connection successful")
    except Exception as e:
        print(f"✗ API connection failed: {e}")
```

#### 2. Trades Data Test
```python
async def test_trades_data():
    connector = DEXConnector(os.getenv('BIRDEYE_API_KEY'))
    
    try:
        trades = await connector.get_trades_stream('SOL/USDT')
        
        if isinstance(trades, list):
            print(f"✓ Retrieved {len(trades)} trades")
            if trades:
                print(f"  Sample trade: {trades[0]}")
        else:
            print("✗ Invalid trades data format")
    except Exception as e:
        print(f"✗ Trades test failed: {e}")
```

#### 3. Liquidity Data Test
```python
async def test_liquidity_data():
    connector = DEXConnector(os.getenv('BIRDEYE_API_KEY'))
    
    try:
        liquidity = await connector.get_liquidity_info('SOL/USDT')
        
        if isinstance(liquidity, dict):
            print(f"✓ Liquidity info retrieved: {liquidity}")
        else:
            print("✗ Invalid liquidity data format")
    except Exception as e:
        print(f"✗ Liquidity test failed: {e}")
```

#### 4. Rate Limiting Test
```python
async def test_rate_limiting():
    connector = DEXConnector(os.getenv('BIRDEYE_API_KEY'))
    
    try:
        # Test multiple requests
        for i in range(10):
            await connector.get_trades_stream('SOL/USDT')
            print(f"✓ Request {i+1} completed")
            await asyncio.sleep(1)  # Respect rate limits
    except Exception as e:
        print(f"✗ Rate limiting test failed: {e}")
```

### Expected Test Results
- API connection should succeed
- Trades and liquidity data should be retrieved successfully
- Rate limiting should prevent API limit exceeded errors
- Data should be properly formatted and validated

### Post-Test Actions
```bash
git add src/data/dex_connector.py
git add tests/test_dex_connector.py
git commit -m "feat: implement DEX data integration with Birdeye API"
```

### Progress Update
Mark Task 4 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 5: Data Synchronization Module
**Objective**: Create data synchronization system with latency measurement and compensation.

### Implementation Steps

#### 5.1 Create Synchronization Manager Class
Create `src/data/sync_manager.py`:

```python
# Example class structure - implement full functionality
import asyncio
from typing import Dict, List, Callable, Optional
from loguru import logger
import time
from collections import deque

class DataSyncManager:
    def __init__(self):
        self.sync_tasks = {}
        self.latency_stats = {}
        self.data_quality_scores = {}
        self.sync_intervals = {'orderbook': 1, 'trades': 5, 'liquidity': 30}
        
    async def start_sync(self, symbol: str, sync_function: Callable):
        # Start data synchronization for a symbol
        pass
        
    def _update_latency_stats(self, symbol: str, latency: float):
        # Update latency statistics for compensation
        pass
        
    def get_data_quality(self, symbol: str) -> float:
        # Calculate data quality score
        pass
```

#### 5.2 Implement Latency Measurement
- Measure data acquisition latency from each source
- Track processing latency for internal operations
- Calculate network latency to exchanges
- Store latency statistics for analysis

#### 5.3 Add Data Quality Monitoring
- Detect missing or delayed data
- Identify data inconsistencies between sources
- Implement data freshness checks
- Calculate quality scores

#### 5.4 Create Compensation Algorithms
- Adjust timestamps for known latencies
- Interpolate missing data points
- Synchronize data streams with different update frequencies
- Implement predictive latency compensation

### Key Implementation Details
- Use high-precision timestamps for accurate synchronization
- Implement sliding window for latency statistics
- Add configurable sync intervals for different data types
- Use asyncio queues for data buffering

### Testing Instructions

#### 1. Synchronization Test
```python
# Create test file: test_sync_manager.py
import asyncio
from src.data.sync_manager import DataSyncManager

async def mock_sync_function(symbol):
    # Mock synchronization function
    await asyncio.sleep(0.1)
    return f"Synced data for {symbol}"

async def test_synchronization():
    sync_manager = DataSyncManager()
    
    try:
        await sync_manager.start_sync('BTC/USDT', mock_sync_function)
        
        # Wait for sync to run
        await asyncio.sleep(5)
        
        # Verify latency tracking
        stats = sync_manager.get_latency_stats('BTC/USDT')
        if stats:
            print(f"✓ Sync latency: {stats.avg_latency}ms")
        else:
            print("✗ No latency stats available")
    except Exception as e:
        print(f"✗ Synchronization test failed: {e}")
```

#### 2. Data Quality Test
```python
async def test_data_quality():
    sync_manager = DataSyncManager()
    
    # Simulate data quality monitoring
    quality_score = sync_manager.get_data_quality('BTC/USDT')
    
    if quality_score > 0.8:  # 80% quality threshold
        print(f"✓ Data quality: {quality_score:.2f}")
    else:
        print(f"✗ Poor data quality: {quality_score:.2f}")
```

#### 3. Latency Compensation Test
```python
async def test_latency_compensation():
    sync_manager = DataSyncManager()
    
    # Test latency recording
    sync_manager._update_latency_stats('BTC/USDT', 50.0)
    sync_manager._update_latency_stats('BTC/USDT', 75.0)
    sync_manager._update_latency_stats('BTC/USDT', 60.0)
    
    stats = sync_manager.get_latency_stats('BTC/USDT')
    if stats and stats.avg_latency > 0:
        print(f"✓ Latency compensation working: {stats.avg_latency}ms avg")
    else:
        print("✗ Latency compensation failed")
```

### Expected Test Results
- Data synchronization should maintain consistent timestamps
- Latency compensation should reduce timing discrepancies
- Data quality scores should be above acceptable thresholds
- Sync tasks should run without errors

### Post-Test Actions
```bash
git add src/data/sync_manager.py
git add tests/test_sync_manager.py
git commit -m "feat: implement data synchronization with latency compensation"
```

### Progress Update
Mark Task 5 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Task 6: Database Schema Implementation
**Objective**: Implement the signals table structure with all required fields and indexes.

### Implementation Steps

#### 6.1 Create SQLAlchemy Models
Create `src/database/models.py`:

```python
# Example model structure - implement all fields from strategic concept
from sqlalchemy import Column, Integer, String, Float, DateTime, DECIMAL, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class Signal(Base):
    __tablename__ = 'signals'
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    pair_symbol = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(10), nullable=False)  # 'BUY' or 'SELL'
    
    # ML and prediction fields
    predicted_reward = Column(Float, nullable=True)
    actual_reward = Column(Float, nullable=True)
    
    # Price data
    dex_price = Column(DECIMAL(precision=20, scale=8), nullable=True)
    cex_price = Column(DECIMAL(precision=20, scale=8), nullable=True)
    
    # Algorithm-specific fields
    dex_orderflow_imbalance = Column(Float, nullable=True)
    cex_orderbook_depth_5pct = Column(DECIMAL(precision=20, scale=8), nullable=True)
    
    # System fields
    market_regime = Column(String(20), nullable=True)
    data_latency_ms = Column(Integer, nullable=True)
    execution_latency_ms = Column(Integer, nullable=True)
    estimated_slippage_pct = Column(Float, nullable=True)
    actual_slippage_pct = Column(Float, nullable=True)
    
    # Add all other fields from strategic concept
```

#### 6.2 Create Database Migration Scripts
Create `src/database/migrations/001_create_signals_table.sql`:

```sql
-- Create signals table with all required fields
CREATE TABLE IF NOT EXISTS signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL,
    pair_symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(10) NOT NULL,
    predicted_reward FLOAT,
    actual_reward FLOAT,
    dex_price DECIMAL(20,8),
    cex_price DECIMAL(20,8),
    dex_orderflow_imbalance FLOAT,
    cex_orderbook_depth_5pct DECIMAL(20,8),
    market_regime VARCHAR(20),
    data_latency_ms INTEGER,
    execution_latency_ms INTEGER,
    estimated_slippage_pct FLOAT,
    actual_slippage_pct FLOAT
);

-- Create performance indexes
CREATE INDEX idx_signals_timestamp ON signals (timestamp DESC);
CREATE INDEX idx_signals_pair_symbol ON signals (pair_symbol);
CREATE INDEX idx_signals_type_timestamp ON signals (signal_type, timestamp DESC);
CREATE INDEX idx_signals_market_regime ON signals (market_regime);
```

#### 6.3 Convert to TimescaleDB Hypertable
```sql
-- Convert signals table to hypertable for time-series optimization
SELECT create_hypertable('signals', 'timestamp', if_not_exists => TRUE);

-- Create additional indexes for time-series queries
CREATE INDEX idx_signals_timestamp_pair ON signals (timestamp DESC, pair_symbol);
CREATE INDEX idx_signals_predicted_reward ON signals (predicted_reward) WHERE predicted_reward IS NOT NULL;
```

#### 6.4 Implement Database Connection Management
Create `src/database/session.py`:

```python
# Example session management structure
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from .connection import get_database_url
from .models import Base

engine = create_engine(get_database_url(), pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db_session() -> Session:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

### Key Implementation Details
- Use UUID for primary keys to avoid conflicts
- Add proper timezone handling for timestamps
- Implement data validation at database level
- Consider partitioning for large datasets

### Testing Instructions

#### 1. Schema Creation Test
```python
# Create test file: test_database_schema.py
from src.database.models import Base, Signal
from src.database.session import create_tables, get_db_session
from sqlalchemy import create_engine
from src.database.connection import get_database_url

def test_schema_creation():
    try:
        # Test table creation
        create_tables()
        print("✓ Database schema created successfully")
        
        # Verify table exists
        engine = create_engine(get_database_url())
        with engine.connect() as conn:
            result = conn.execute("SELECT tablename FROM pg_tables WHERE tablename = 'signals';")
            if result.fetchone():
                print("✓ Signals table exists")
            else:
                print("✗ Signals table not found")
    except Exception as e:
        print(f"✗ Schema creation failed: {e}")
```

#### 2. Data Insertion Test
```python
def test_data_insertion():
    from datetime import datetime
    
    try:
        with get_db_session() as session:
            # Test signal insertion
            signal = Signal(
                timestamp=datetime.utcnow(),
                pair_symbol='BTC/USDT',
                signal_type='BUY',
                predicted_reward=0.025,
                dex_price=50000.0,
                cex_price=50010.0
            )
            
            session.add(signal)
            session.commit()
            print("✓ Signal inserted successfully")
            
            # Verify insertion
            count = session.query(Signal).count()
            print(f"✓ Total signals in database: {count}")
    except Exception as e:
        print(f"✗ Data insertion failed: {e}")
```

#### 3. Query Performance Test
```python
def test_query_performance():
    import time
    from datetime import datetime, timedelta
    
    try:
        with get_db_session() as session:
            start_time = time.time()
            
            # Test index performance
            recent_signals = session.query(Signal).filter(
                Signal.timestamp >= datetime.utcnow() - timedelta(hours=1)
            ).all()
            
            query_time = time.time() - start_time
            print(f"✓ Query completed in {query_time:.3f}s, found {len(recent_signals)} signals")
    except Exception as e:
        print(f"✗ Query performance test failed: {e}")
```

### Expected Test Results
- Database schema should be created without errors
- Data insertion should work with proper validation
- Queries should execute quickly with proper indexes
- TimescaleDB hypertable should be created successfully

### Post-Test Actions
```bash
git add src/database/models.py
git add src/database/session.py
git add src/database/migrations/
git add tests/test_database_schema.py
git commit -m "feat: implement signals database schema with TimescaleDB"
```

### Progress Update
Mark Task 6 as completed in [ATS_IMPLEMENTATION_PROGRESS.md](ATS_IMPLEMENTATION_PROGRESS.md)

---

## Phase A1 Summary

### Completed Tasks:
- ✅ Task 1: Environment Setup
- ✅ Task 2: Database Setup  
- ✅ Task 3: CEX Data Integration
- ✅ Task 4: DEX Data Integration
- ✅ Task 5: Data Synchronization Module
- ✅ Task 6: Database Schema Implementation

### Milestone 1 Checkpoint:
**Local Development Environment Complete**

Verify all components are working:
1. Python environment with all dependencies
2. PostgreSQL + TimescaleDB operational
3. CEX data connector receiving orderbook data
4. DEX data connector retrieving trades/liquidity
5. Data synchronization managing latency
6. Database schema ready for signal storage

### Next Steps:
Proceed to **[Phase A2: Algorithms & Risk Management](ATS_GUIDE_PHASE_A2_ALGORITHMS.md)** (Tasks 7-14)

### Troubleshooting:
- **Database connection issues**: Check PostgreSQL service status
- **API connection failures**: Verify API keys and network connectivity
- **Import errors**: Ensure virtual environment is activated
- **Permission errors**: Check Windows Defender exclusions

---

**Phase A1 Complete!** Continue with [ATS_GUIDE_PHASE_A2_ALGORITHMS.md](ATS_GUIDE_PHASE_A2_ALGORITHMS.md)
