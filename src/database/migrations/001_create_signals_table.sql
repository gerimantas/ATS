-- Migration 001: Create signals table with TimescaleDB hypertable
-- This script creates the signals table with all required fields and converts it to a hypertable

-- Create signals table with all required fields
CREATE TABLE IF NOT EXISTS signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL,
    pair_symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(10) NOT NULL,
    
    -- ML and prediction fields
    predicted_reward FLOAT,
    actual_reward FLOAT,
    
    -- Price data
    dex_price DECIMAL(20,8),
    cex_price DECIMAL(20,8),
    
    -- Algorithm-specific fields
    dex_orderflow_imbalance FLOAT,
    cex_orderbook_depth_5pct DECIMAL(20,8),
    
    -- Volume and correlation analysis fields
    dex_volume_spike FLOAT,
    volume_price_correlation FLOAT,
    liquidity_change_velocity FLOAT,
    
    -- DEX-CEX spread analysis
    dex_cex_spread_pct FLOAT,
    spread_moving_avg FLOAT,
    spread_volatility FLOAT,
    
    -- Market microstructure fields
    bid_ask_spread_dex FLOAT,
    bid_ask_spread_cex FLOAT,
    order_book_imbalance_cex FLOAT,
    
    -- System and performance fields
    market_regime VARCHAR(20),
    btc_volatility FLOAT,
    eth_volatility FLOAT,
    data_latency_ms INTEGER,
    execution_latency_ms INTEGER,
    processing_latency_ms INTEGER,
    
    -- Risk management fields
    estimated_slippage_pct FLOAT,
    actual_slippage_pct FLOAT,
    position_size_usd DECIMAL(20,2),
    risk_score FLOAT,
    
    -- Signal quality and validation
    signal_strength FLOAT,
    data_quality_score FLOAT,
    algorithm_confidence FLOAT,
    
    -- Execution and results
    executed BOOLEAN DEFAULT FALSE,
    execution_price DECIMAL(20,8),
    execution_timestamp TIMESTAMPTZ,
    pnl_usd DECIMAL(20,2),
    
    -- Additional metadata
    exchange_cex VARCHAR(20),
    exchange_dex VARCHAR(20),
    blockchain VARCHAR(20),
    
    -- Algorithm identification
    algorithm_version VARCHAR(10),
    signal_source VARCHAR(50),
    
    -- Notes and debugging
    notes TEXT,
    debug_info TEXT
);

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_pair_symbol ON signals (pair_symbol);
CREATE INDEX IF NOT EXISTS idx_signals_type_timestamp ON signals (signal_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_market_regime ON signals (market_regime);
CREATE INDEX IF NOT EXISTS idx_signals_executed ON signals (executed);
CREATE INDEX IF NOT EXISTS idx_signals_exchange_cex ON signals (exchange_cex);
CREATE INDEX IF NOT EXISTS idx_signals_signal_source ON signals (signal_source);

-- Convert signals table to hypertable for time-series optimization
-- This will partition the table by timestamp for better performance
SELECT create_hypertable('signals', 'timestamp', if_not_exists => TRUE);

-- Create additional indexes optimized for time-series queries
CREATE INDEX IF NOT EXISTS idx_signals_timestamp_pair ON signals (timestamp DESC, pair_symbol);
CREATE INDEX IF NOT EXISTS idx_signals_predicted_reward ON signals (predicted_reward) WHERE predicted_reward IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_signals_actual_reward ON signals (actual_reward) WHERE actual_reward IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_signals_pnl ON signals (pnl_usd) WHERE pnl_usd IS NOT NULL;

-- Create composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_signals_pair_type_time ON signals (pair_symbol, signal_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_executed_time ON signals (executed, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_regime_time ON signals (market_regime, timestamp DESC) WHERE market_regime IS NOT NULL;

-- Add table comment
COMMENT ON TABLE signals IS 'Trading signals with comprehensive metadata for ATS system';

-- Add column comments for important fields
COMMENT ON COLUMN signals.predicted_reward IS 'ML model predicted reward score';
COMMENT ON COLUMN signals.actual_reward IS 'Actual reward calculated after analysis window';
COMMENT ON COLUMN signals.signal_strength IS 'Overall signal strength score (0-1)';
COMMENT ON COLUMN signals.data_quality_score IS 'Quality score of input data (0-1)';
COMMENT ON COLUMN signals.market_regime IS 'Market regime classification (CALM, BTC_VOLATILE, etc.)';
