"""
QuantForge AI Engine - OHLCV Model for TimescaleDB

Time-series market data model with hypertable support.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    BigInteger,
    String,
    Index,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from anchorgrid.db.session import Base


class OHLCV(Base):
    """
    OHLCV (Open, High, Low, Close, Volume) time-series data.
    
    This table is converted to a TimescaleDB hypertable for efficient
    time-series queries and automatic partitioning.
    
    Features:
    - Space-time partitioning by (ticker, timestamp)
    - Compression after 30 days
    - Continuous aggregates for common intervals
    """
    __tablename__ = "ohlcv"
    
    # Composite primary key (time + ticker)
    # TimescaleDB requires time column in PK for hypertables
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
    )
    ticker: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
    )
    
    # Interval for this candle (1m, 5m, 1h, 1d)
    interval: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
        default="1d",
    )
    
    # OHLCV data
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # Optional: adjusted close (for splits/dividends)
    adj_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Data source tracking
    source: Mapped[str] = mapped_column(
        String(50),
        default="unknown",
    )  # yfinance, binance, polygon, etc.
    
    # Indexes for common queries
    __table_args__ = (
        # Primary lookup: ticker + time range
        Index("idx_ohlcv_ticker_time", "ticker", "timestamp"),
        # Source filtering
        Index("idx_ohlcv_source", "source"),
        # Interval queries
        Index("idx_ohlcv_interval", "interval", "ticker", "timestamp"),
    )
    
    def __repr__(self) -> str:
        return f"<OHLCV {self.ticker} {self.timestamp} O={self.open} C={self.close}>"


# =============================================================================
# TimescaleDB SQL Commands (run after table creation)
# =============================================================================

TIMESCALE_SETUP_SQL = """
-- Convert to hypertable (7-day chunks)
SELECT create_hypertable(
    'ohlcv',
    'timestamp',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Add space partitioning by ticker (improves query performance)
SELECT add_dimension(
    'ohlcv',
    'ticker',
    number_partitions => 4,
    if_not_exists => TRUE
);

-- Enable compression (compress after 30 days)
ALTER TABLE ohlcv SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'ticker,interval',
    timescaledb.compress_orderby = 'timestamp DESC'
);

-- Add compression policy
SELECT add_compression_policy(
    'ohlcv',
    INTERVAL '30 days',
    if_not_exists => TRUE
);

-- Create continuous aggregate for daily OHLCV (from 1-minute data)
CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS bucket,
    ticker,
    first(open, timestamp) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, timestamp) AS close,
    sum(volume) AS volume,
    source
FROM ohlcv
WHERE interval = '1m'
GROUP BY bucket, ticker, source
WITH NO DATA;

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy(
    'ohlcv_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Create index on continuous aggregate
CREATE INDEX IF NOT EXISTS idx_ohlcv_daily_ticker 
ON ohlcv_daily (ticker, bucket DESC);
"""

# SQL to verify hypertable setup
VERIFY_HYPERTABLE_SQL = """
SELECT hypertable_name, num_chunks, compression_enabled
FROM timescaledb_information.hypertables
WHERE hypertable_name = 'ohlcv';
"""

