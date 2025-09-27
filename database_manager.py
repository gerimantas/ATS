from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()

class Signal(Base):
    __tablename__ = 'signals'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    dex_price = Column(Float)
    cex_price = Column(Float)
    spread = Column(Float)
    # --- ADD THESE NEW COLUMNS ---
    data_latency_ms = Column(Integer, nullable=True)
    market_regime = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    actual_reward = Column(Float, nullable=True)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ats.db")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def setup_database():
    Base.metadata.create_all(engine)

# Update the create_signal function signature and body
def create_signal(timestamp, dex_price, cex_price, spread, data_latency_ms=None, notes=None):
    session = Session()
    new_signal = Signal(
        timestamp=timestamp,
        dex_price=dex_price,
        cex_price=cex_price,
        spread=spread,
        data_latency_ms=data_latency_ms,
        notes=notes
    )
    session.add(new_signal)
    session.commit()
    print(f"SUCCESS: Signal successfully logged to the database.")
    session.close()