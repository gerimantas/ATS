from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()


class Signal(Base):
    __tablename__ = "signals"
    id = Column(Integer, primary_key=True)
    timestamp = Column(
        DateTime, index=True
    )  # Add index=True for performance optimization
    pair_symbol = Column(String(20), nullable=False)
    cex_symbol = Column(
        String(20), nullable=False, index=True
    )  # Add the new column with an index
    signal_type = Column(String(10), nullable=False)
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
def create_signal(
    timestamp,
    dex_price,
    cex_price,
    spread,
    data_latency_ms=None,
    notes=None,
    pair_symbol="UNKNOWN",
    cex_symbol="UNKNOWN",
    signal_type="UNKNOWN",
):
    session = Session()
    signal_id = None
    try:
        new_signal = Signal(
            timestamp=timestamp,
            pair_symbol=pair_symbol,
            cex_symbol=cex_symbol,
            signal_type=signal_type,
            dex_price=dex_price,
            cex_price=cex_price,
            spread=spread,
            data_latency_ms=data_latency_ms,
            notes=notes,
        )
        session.add(new_signal)
        session.commit()
        signal_id = new_signal.id  # Get the ID of the new signal
        print(f"SUCCESS: Signal {signal_id} logged to the database.")
    except Exception as e:
        print(f"ERROR: Failed to create signal in DB. Error: {e}")
        session.rollback()
    finally:
        session.close()

    return signal_id  # Return the ID, or None if an error occurred


def update_signal_reward(signal_id: int, reward_score: float):
    """Finds a signal by its ID and updates its actual_reward field."""
    session = Session()
    try:
        signal_to_update = session.query(Signal).filter(Signal.id == signal_id).first()
        if signal_to_update:
            signal_to_update.actual_reward = reward_score
            session.commit()
            print(
                f"SUCCESS: Updated reward for signal ID {signal_id} to {reward_score:.5f}"
            )
        else:
            print(f"ERROR: Could not find signal with ID {signal_id} to update reward.")
    finally:
        session.close()
