"""
QuantForge AI Engine - Market Data Service

Database operations for OHLCV data in TimescaleDB.
Handles upsert, queries, and data retrieval.
"""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from anchorgrid.db.models.ohlcv import OHLCV
from anchorgrid.engine.ingestion.base import OHLCVData


class MarketDataService:
    """
    Service for OHLCV data operations in TimescaleDB.
    
    All methods are async and require a database session.
    """
    
    async def upsert_ohlcv(
        self,
        session: AsyncSession,
        data: list[OHLCVData],
    ) -> int:
        """
        Upsert (insert or update) OHLCV data.
        
        Uses PostgreSQL ON CONFLICT to handle duplicates.
        
        Args:
            session: TimescaleDB async session
            data: List of OHLCVData records
            
        Returns:
            Number of rows upserted
        """
        if not data:
            return 0
        
        # Convert to dicts for bulk insert
        records = [d.to_dict() for d in data]
        
        # Build INSERT ... ON CONFLICT DO UPDATE
        stmt = insert(OHLCV).values(records)
        
        # On conflict (timestamp, ticker, interval), update prices
        stmt = stmt.on_conflict_do_update(
            index_elements=["timestamp", "ticker", "interval"],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "volume": stmt.excluded.volume,
                "adj_close": stmt.excluded.adj_close,
                "source": stmt.excluded.source,
            }
        )
        
        try:
            await session.execute(stmt)
            await session.commit()
            logger.info(f"Upserted {len(records)} OHLCV records")
            return len(records)
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to upsert OHLCV: {e}")
            raise
    
    async def get_ohlcv(
        self,
        session: AsyncSession,
        ticker: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        interval: str = "1d",
        limit: int = 1000,
    ) -> list[OHLCV]:
        """
        Get OHLCV data for a ticker.
        
        Args:
            session: TimescaleDB async session
            ticker: Symbol to query
            start: Start datetime (default: 30 days ago)
            end: End datetime (default: now)
            interval: Candle interval
            limit: Maximum rows to return
            
        Returns:
            List of OHLCV model instances
        """
        if end is None:
            end = datetime.now()
        if start is None:
            start = end - timedelta(days=30)
        
        stmt = (
            select(OHLCV)
            .where(
                OHLCV.ticker == ticker.upper(),
                OHLCV.interval == interval,
                OHLCV.timestamp >= start,
                OHLCV.timestamp <= end,
            )
            .order_by(OHLCV.timestamp.desc())
            .limit(limit)
        )
        
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_latest_price(
        self,
        session: AsyncSession,
        ticker: str,
    ) -> Optional[OHLCV]:
        """Get the most recent OHLCV record for a ticker"""
        stmt = (
            select(OHLCV)
            .where(OHLCV.ticker == ticker.upper())
            .order_by(OHLCV.timestamp.desc())
            .limit(1)
        )
        
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_price_history(
        self,
        session: AsyncSession,
        ticker: str,
        days: int = 30,
        interval: str = "1d",
    ) -> list[float]:
        """
        Get close prices as a simple list (for quant analysis).
        
        Returns prices in chronological order (oldest first).
        """
        rows = await self.get_ohlcv(
            session,
            ticker=ticker,
            start=datetime.now() - timedelta(days=days),
            interval=interval,
            limit=days + 10,  # Buffer for weekends/holidays
        )
        
        # Reverse to get chronological order
        prices = [row.close for row in reversed(rows)]
        return prices
    
    async def ticker_exists(
        self,
        session: AsyncSession,
        ticker: str,
    ) -> bool:
        """Check if we have any data for a ticker"""
        stmt = (
            select(OHLCV.ticker)
            .where(OHLCV.ticker == ticker.upper())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def get_all_tickers(
        self,
        session: AsyncSession,
    ) -> list[str]:
        """Get list of all tickers in the database"""
        stmt = select(OHLCV.ticker).distinct()
        result = await session.execute(stmt)
        return [row[0] for row in result.fetchall()]
    
    async def delete_ticker_data(
        self,
        session: AsyncSession,
        ticker: str,
    ) -> int:
        """Delete all data for a ticker (use with caution!)"""
        stmt = text("DELETE FROM ohlcv WHERE ticker = :ticker")
        result = await session.execute(stmt, {"ticker": ticker.upper()})
        await session.commit()
        return result.rowcount or 0


# Singleton instance
market_data_service = MarketDataService()
