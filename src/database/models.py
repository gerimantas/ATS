"""
SQLAlchemy models for ATS database schema
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, DECIMAL, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class Signal(Base):
    """
    Signal model representing trading signals with all required fields
    from the strategic concept document
    """
    __tablename__ = 'signals'
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    pair_symbol = Column(String(20), nullable=False, index=True)
    cex_symbol = Column(String(20), nullable=False, index=True)  # e.g., 'SOL' for SOL/USDT
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
    
    # Volume and correlation analysis fields
    dex_volume_spike = Column(Float, nullable=True)
    volume_price_correlation = Column(Float, nullable=True)
    liquidity_change_velocity = Column(Float, nullable=True)
    
    # DEX-CEX spread analysis
    dex_cex_spread_pct = Column(Float, nullable=True)
    spread_moving_avg = Column(Float, nullable=True)
    spread_volatility = Column(Float, nullable=True)
    
    # Market microstructure fields
    bid_ask_spread_dex = Column(Float, nullable=True)
    bid_ask_spread_cex = Column(Float, nullable=True)
    order_book_imbalance_cex = Column(Float, nullable=True)
    
    # System and performance fields
    market_regime = Column(String(20), nullable=True)
    btc_volatility = Column(Float, nullable=True)
    eth_volatility = Column(Float, nullable=True)
    data_latency_ms = Column(Integer, nullable=True)
    execution_latency_ms = Column(Integer, nullable=True)
    processing_latency_ms = Column(Integer, nullable=True)
    
    # Risk management fields
    estimated_slippage_pct = Column(Float, nullable=True)
    actual_slippage_pct = Column(Float, nullable=True)
    position_size_usd = Column(DECIMAL(precision=20, scale=2), nullable=True)
    risk_score = Column(Float, nullable=True)
    
    # Signal quality and validation
    signal_strength = Column(Float, nullable=True)
    data_quality_score = Column(Float, nullable=True)
    algorithm_confidence = Column(Float, nullable=True)
    
    # Execution and results
    executed = Column(Boolean, default=False)
    execution_price = Column(DECIMAL(precision=20, scale=8), nullable=True)
    execution_timestamp = Column(DateTime(timezone=True), nullable=True)
    pnl_usd = Column(DECIMAL(precision=20, scale=2), nullable=True)
    
    # Additional metadata
    exchange_cex = Column(String(20), nullable=True)  # e.g., 'binance'
    exchange_dex = Column(String(20), nullable=True)  # e.g., 'raydium'
    blockchain = Column(String(20), nullable=True)    # e.g., 'solana', 'ethereum'
    
    # Algorithm identification
    algorithm_version = Column(String(10), nullable=True)
    signal_source = Column(String(50), nullable=True)  # Which algorithm generated this
    
    # Notes and debugging
    notes = Column(Text, nullable=True)
    debug_info = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Signal(id={self.id}, timestamp={self.timestamp}, pair={self.pair_symbol}, type={self.signal_type}, predicted_reward={self.predicted_reward})>"
    
    def to_dict(self):
        """Convert signal to dictionary for JSON serialization"""
        return {
            'id': str(self.id),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'pair_symbol': self.pair_symbol,
            'signal_type': self.signal_type,
            'predicted_reward': float(self.predicted_reward) if self.predicted_reward else None,
            'actual_reward': float(self.actual_reward) if self.actual_reward else None,
            'dex_price': float(self.dex_price) if self.dex_price else None,
            'cex_price': float(self.cex_price) if self.cex_price else None,
            'market_regime': self.market_regime,
            'executed': self.executed,
            'signal_strength': float(self.signal_strength) if self.signal_strength else None
        }
