# backend/services/portfolio_service.py
"""
Portfolio Service - Paper Trading Portfolio Management

Handles portfolio creation, position tracking, and P&L calculations.

Phase 2D: Paper Trading Implementation
"""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict, List
from quantgrid.db.session import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from quantgrid.db.models import Portfolio, Position
from quantgrid.services.quote_service import get_realtime_quote, get_historical_data
from quantgrid.core.logger import log
from sqlalchemy import select


async def get_or_create_portfolio(user_id: int, db: AsyncSession) -> Portfolio:
    """
    Get user's portfolio or create with $100k starting balance
    
    Args:
        user_id: User ID
        db: Database session (passed in to avoid nested sessions)
        
    Returns:
        Portfolio instance
    """
    # Session passed in from caller - no nested session creation
    result = await db.execute(
        select(Portfolio).where(Portfolio.user_id == user_id)
    )
    portfolio = result.scalar_one_or_none()
        
    if not portfolio:
        portfolio = Portfolio(
            user_id=user_id,
            cash_balance=100000.0,
            starting_balance=100000.0
        )
        db.add(portfolio)
        await db.commit()
        await db.refresh(portfolio)
        log.info(f"💰 Created portfolio for user {user_id} with $100k")
        
    return portfolio


async def update_position_prices(portfolio: Portfolio, db):
    """
    Refresh current prices for all positions and calculate unrealized P&L
    
    Args:
        portfolio: Portfolio instance
        db: Database session
    """
    for position in portfolio.positions:
        try:
            quote = await get_realtime_quote(position.symbol)
            if quote:
                position.current_price = float(quote["price"])
                position.unrealized_pnl = (
                    position.current_price - position.avg_cost_basis
                ) * position.quantity
                position.updated_at = datetime.now(timezone.utc)
        except Exception as e:
            log.warning(f"Failed to update price for {position.symbol}: {e}")
    
    # Calculate total portfolio value
    positions_value = sum(
        (pos.current_price or 0) * pos.quantity for pos in portfolio.positions
    )
    portfolio.total_value = portfolio.cash_balance + positions_value
    portfolio.updated_at = datetime.now(timezone.utc)
    
    await db.commit()


async def get_portfolio_summary(user_id: int) -> Dict:
    """
    Get complete portfolio summary with current prices and P&L
    
    Args:
        user_id: User ID
        
    Returns:
        {
            "cash_balance": float,
            "total_value": float,
            "positions": [position dicts],
            "unrealized_pnl": float,
            "realized_pnl": float  # TODO: Sum from trades
        }
    """
    async with AsyncSessionLocal() as db:
        portfolio = await get_or_create_portfolio(user_id, db)  # Pass session
        
        # Refresh with session AND eagerly load positions to avoid lazy loading greenlet error
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Portfolio)
            .where(Portfolio.id == portfolio.id)
            .options(selectinload(Portfolio.positions))  # Eager load positions!
        )
        portfolio = result.scalar_one()
        
        # Update prices
        await update_position_prices(portfolio, db)
        
        positions = [
            {
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "avg_cost_basis": float(pos.avg_cost_basis),
                "current_price": float(pos.current_price) if pos.current_price else 0.0,
                "market_value": float(pos.current_price or 0) * pos.quantity,
                "unrealized_pnl": float(pos.unrealized_pnl),
                "percent_gain": (
                    ((pos.current_price - pos.avg_cost_basis) / pos.avg_cost_basis * 100)
                    if pos.avg_cost_basis > 0 else 0.0
                )
            }
            for pos in portfolio.positions
        ]
        
        
        total_unrealized_pnl = sum(pos["unrealized_pnl"] for pos in positions)
        total_positions_value = sum(pos["market_value"] for pos in positions)
        total_portfolio_value = float(portfolio.cash_balance) + total_positions_value
        
        return {
            "cash_balance": float(portfolio.cash_balance),
            "total_value": total_portfolio_value,  # Computed: cash + positions
            "starting_balance": float(portfolio.starting_balance),
            "positions_count": len(positions),
            "positions": positions,
            "unrealized_pnl": total_unrealized_pnl,
            "total_gain_percent": (
                ((total_portfolio_value - portfolio.starting_balance) / portfolio.starting_balance * 100)
                if portfolio.starting_balance > 0 else 0.0
            )
        }


async def reset_portfolio(user_id: int) -> Dict:
    """
    Reset portfolio to $100k (for testing)
    
    Deletes all positions and orders, resets cash balance
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Portfolio).where(Portfolio.user_id == user_id)
        )
        portfolio = result.scalar_one_or_none()
        
        if portfolio:
            # Delete all positions and orders (cascade)
            for position in portfolio.positions:
                await db.delete(position)
            for order in portfolio.orders:
                await db.delete(order)
            
            portfolio.cash_balance = 100000.0
            portfolio.total_value = 100000.0
            portfolio.updated_at = datetime.now(timezone.utc)
            
            await db.commit()
            log.info(f"♻️ Reset portfolio for user {user_id}")
            
            return {"message": "Portfolio reset to $100,000", "cash_balance": 100000.0}
        
        return {"message": "No portfolio found"}
