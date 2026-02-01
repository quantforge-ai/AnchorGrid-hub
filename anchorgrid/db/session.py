"""
QuantForge AI Engine - Database Session & Base

SQLAlchemy async engine and session management.
"""
from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from anchorgrid.core.config import settings


# =============================================================================
# Naming Convention for Constraints
# =============================================================================

# This ensures consistent constraint names for Alembic migrations
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# =============================================================================
# Base Model Class
# =============================================================================

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""
    metadata = MetaData(naming_convention=convention)


# =============================================================================
# Database Engine & Session
# =============================================================================

def _get_database_url() -> str:
    """Get database URL, converting to async driver if needed"""
    url = settings.DATABASE_URL
    if not url:
        # Fallback to SQLite for development
        return "sqlite+aiosqlite:///./quantforge.db"
    
    # Convert sync drivers to async drivers
    # NeonDB uses: postgresql+psycopg2://
    # We need: postgresql+asyncpg://
    if "psycopg2" in url:
        url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Remove channel_binding parameter (not supported by asyncpg)
    if "channel_binding=" in url:
        # Remove the parameter
        import re
        url = re.sub(r"[&?]channel_binding=[^&]*", "", url)
    
    return url


# Create async engine
engine = create_async_engine(
    _get_database_url(),
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.
    
    Usage:
        @app.get("/users")
        async def get_users(session: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# =============================================================================
# TimescaleDB Engine (for time-series data)
# =============================================================================

def _get_timescale_url() -> str:
    """Get TimescaleDB URL for async driver"""
    url = settings.timescale_url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


timescale_engine = create_async_engine(
    _get_timescale_url(),
    echo=settings.ENVIRONMENT == "development",
    pool_pre_ping=True,
    pool_size=10,  # More connections for time-series queries
    max_overflow=20,
)

timescale_session_maker = async_sessionmaker(
    timescale_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_timescale_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting TimescaleDB session"""
    async with timescale_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
