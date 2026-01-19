# backend/db/models/portfolio.py
"""
Portfolio Models - Paper Trading System

Database models for virtual portfolio management, positions tracking,
and trade order execution.

Phase 2D: Paper Trading Implementation
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from quantgrid.db.session import Base
import enum


class OrderSide(enum.Enum):
    """Order side enum"""
    BUY = "buy"
    SELL = "sell"


class OrderType(enum.Enum):
    """Order type enum"""
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(enum.Enum):
    """Order status enum"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Portfolio(Base):
    """
    User's paper trading portfolio
    
    Tracks virtual cash balance and overall portfolio value.
    Each user gets one portfolio with $100k starting balance.
    """
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    cash_balance = Column(Float, default=100000.0, nullable=False)  # Virtual cash
    starting_balance = Column(Float, default=100000.0, nullable=False)  # For reset
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="portfolio")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    orders = relationship("TradeOrder", back_populates="portfolio", cascade="all, delete-orphan")


class Position(Base):
    """
    Portfolio position (holding) for a specific symbol
    
    Tracks quantity owned, average cost basis, and unrealized P&L.
    """
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), index=True, nullable=False)
    quantity = Column(Float, default=0.0, nullable=False)  # Shares owned
    avg_cost_basis = Column(Float, default=0.0, nullable=False)  # Average price paid per share
    current_price = Column(Float, nullable=True)  # Latest market price (cached)
    unrealized_pnl = Column(Float, default=0.0)  # (current_price - avg_cost) * quantity
    opened_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint('portfolio_id', 'symbol', name='uq_portfolio_symbol'),
    )

    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")


class TradeOrder(Base):
    """
    Trade order (buy/sell request)
    
    Tracks order placement, execution, and fill details.
    Market orders fill instantly, limit orders remain pending.
    """
    __tablename__ = "trade_orders"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), index=True, nullable=False)
    side = Column(SQLEnum(OrderSide), nullable=False)  # buy or sell
    order_type = Column(SQLEnum(OrderType), nullable=False)  # market or limit
    quantity = Column(Float, nullable=False)  # Requested quantity
    limit_price = Column(Float, nullable=True)  # For limit orders only
    filled_quantity = Column(Float, default=0.0)  # Actual filled quantity
    filled_price = Column(Float, nullable=True)  # Execution price
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    total_value = Column(Float, nullable=True)  # filled_quantity * filled_price
    commission = Column(Float, default=0.0)  # Always 0 for paper trading
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    filled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="orders")
