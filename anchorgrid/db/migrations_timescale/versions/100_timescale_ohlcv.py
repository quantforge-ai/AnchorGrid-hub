"""OHLCV hypertable for TimescaleDB

Revision ID: 100_timescale_ohlcv
Revises: 001_initial
Create Date: 2024-12-17

This migration:
1. Creates the OHLCV table
2. Converts it to a TimescaleDB hypertable with 7-day chunks
3. Adds space partitioning by ticker
4. Enables compression (30 days)
5. Creates continuous aggregates for daily rollups
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "100_timescale_ohlcv"
down_revision: Union[str, None] = None  # First migration in TimescaleDB
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create OHLCV hypertable with TimescaleDB features"""
    
    # ===================
    # OHLCV TABLE
    # ===================
    op.create_table(
        "ohlcv",
        sa.Column("timestamp", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("ticker", sa.String(20), primary_key=True),
        sa.Column("interval", sa.String(10), primary_key=True, server_default="1d"),
        sa.Column("open", sa.Float, nullable=False),
        sa.Column("high", sa.Float, nullable=False),
        sa.Column("low", sa.Float, nullable=False),
        sa.Column("close", sa.Float, nullable=False),
        sa.Column("volume", sa.BigInteger, nullable=False),
        sa.Column("adj_close", sa.Float, nullable=True),
        sa.Column("source", sa.String(50), server_default="unknown"),
    )
    
    # Create indexes
    op.create_index("idx_ohlcv_ticker_time", "ohlcv", ["ticker", "timestamp"])
    op.create_index("idx_ohlcv_source", "ohlcv", ["source"])
    op.create_index("idx_ohlcv_interval", "ohlcv", ["interval", "ticker", "timestamp"])
    
    # ===================
    # TIMESCALEDB SETUP
    # ===================
    # Note: These commands are idempotent (use if_not_exists)
    
    # Convert to hypertable with 7-day chunks
    op.execute("""
        SELECT create_hypertable(
            'ohlcv',
            'timestamp',
            chunk_time_interval => INTERVAL '7 days',
            if_not_exists => TRUE
        );
    """)
    
    # Add space partitioning by ticker
    op.execute("""
        SELECT add_dimension(
            'ohlcv',
            'ticker',
            number_partitions => 4,
            if_not_exists => TRUE
        );
    """)
    
    # Enable compression
    op.execute("""
        ALTER TABLE ohlcv SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'ticker,interval',
            timescaledb.compress_orderby = 'timestamp DESC'
        );
    """)
    
    # Add compression policy (compress chunks older than 30 days)
    op.execute("""
        SELECT add_compression_policy(
            'ohlcv',
            INTERVAL '30 days',
            if_not_exists => TRUE
        );
    """)
    
    # ===================
    # CONTINUOUS AGGREGATE
    # ===================
    # Create daily rollup from minute data
    op.execute("""
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
    """)
    
    # Refresh policy for continuous aggregate
    op.execute("""
        SELECT add_continuous_aggregate_policy(
            'ohlcv_daily',
            start_offset => INTERVAL '3 days',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour',
            if_not_exists => TRUE
        );
    """)
    
    # Index on continuous aggregate
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_ohlcv_daily_ticker 
        ON ohlcv_daily (ticker, bucket DESC);
    """)


def downgrade() -> None:
    """Drop OHLCV hypertable and related objects"""
    # Drop continuous aggregate first
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ohlcv_daily CASCADE;")
    
    # Drop compression policy (will error if not exists, that's ok)
    op.execute("""
        SELECT remove_compression_policy('ohlcv', if_exists => TRUE);
    """)
    
    # Drop indexes
    op.drop_index("idx_ohlcv_interval", table_name="ohlcv")
    op.drop_index("idx_ohlcv_source", table_name="ohlcv")
    op.drop_index("idx_ohlcv_ticker_time", table_name="ohlcv")
    
    # Drop table (hypertable drops automatically)
    op.drop_table("ohlcv")
