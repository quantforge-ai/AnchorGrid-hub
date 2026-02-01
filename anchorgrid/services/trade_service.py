# backend/services/trade_service.py
"""
Trade Service - Trade Recording and Position Updates

Handles trade execution, position updates, P&L calculation,
and Shadow Watch integration.

Phase 2D: Paper Trading Implementation
"""

from decimal import Decimal
from datetime import datetime, timezone
from typing import Dict
from anchorgrid.db.session import AsyncSessionLocal
from anchorgrid.db.models import Portfolio, Position, TradeOrder, OrderSide, OrderStatus
from anchorgrid.services.shadow_watch import track_activity
from anchorgrid.core.logger import log
from sqlalchemy import select


async def record_trade(order: TradeOrder, filled_price: float, db):
    """
    Record filled trade and update portfolio position
    
    Args:
        order: TradeOrder instance
        filled_price: Execution price
        db: Database session
    """
    filled_value = filled_price * order.quantity
    
    # Update order status
    order.status = OrderStatus.FILLED
    order.filled_quantity = order.quantity
    order.filled_price = filled_price
    order.total_value = filled_value
    order.filled_at = datetime.now(timezone.utc)
    
    # Get portfolio
    result = await db.execute(
        select(Portfolio).where(Portfolio.id == order.portfolio_id)
    )
    portfolio = result.scalar_one()
    
    # Update cash balance
    if order.side == OrderSide.BUY:
        # Check sufficient funds
        if portfolio.cash_balance < filled_value:
            order.status = OrderStatus.REJECTED
            log.error(f"❌ Insufficient funds: need ${filled_value}, have ${portfolio.cash_balance}")
            await db.commit()
            return
        
        portfolio.cash_balance -= filled_value
        log.info(f"💸 Deducted ${filled_value} from cash")
    else:  # SELL
        portfolio.cash_balance += filled_value
        log.info(f"💰 Added ${filled_value} to cash")
    
    # Update or create position
    result = await db.execute(
        select(Position).where(
            Position.portfolio_id == order.portfolio_id,
            Position.symbol == order.symbol
        )
    )
    position = result.scalar_one_or_none()
    
    if order.side == OrderSide.BUY:
        if not position:
            # Create new position
            position = Position(
                portfolio_id=order.portfolio_id,
                symbol=order.symbol,
                quantity=order.quantity,
                avg_cost_basis=filled_price,
                current_price=filled_price
            )
            db.add(position)
            log.info(f"📊 New position: {order.quantity} shares of {order.symbol} @ ${filled_price}")
        else:
            # Update existing position (average cost)
            total_cost = (position.avg_cost_basis * position.quantity) + filled_value
            new_quantity = position.quantity + order.quantity
            position.avg_cost_basis = total_cost / new_quantity
            position.quantity = new_quantity
            position.current_price = filled_price
            log.info(f"📈 Updated position: {position.quantity} shares of {order.symbol} (avg ${position.avg_cost_basis:.2f})")
    
    else:  # SELL
        if not position or position.quantity < order.quantity:
            order.status = OrderStatus.REJECTED
            log.error(f"❌ Insufficient shares: need {order.quantity}, have {position.quantity if position else 0}")
            await db.commit()
            return
        
        # Calculate realized P&L
        realized_pnl = (filled_price - position.avg_cost_basis) * order.quantity
        
        # Update position
        position.quantity -= order.quantity
        log.info(f"📉 Sold {order.quantity} shares of {order.symbol} @ ${filled_price} (realized P/L: ${realized_pnl:.2f})")
        
        # Delete position if quantity is zero
        if position.quantity == 0:
            await db.delete(position)
            log.info(f"🗑️ Closed position in {order.symbol}")
    
    position.updated_at = datetime.now(timezone.utc)
    portfolio.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    
    # Shadow Watch integration - Track trade activity
    await track_activity(
        user_id=portfolio.user_id,
        symbol=order.symbol,
        action="trade",
        event_metadata={
            "side": order.side.value,
            "quantity": order.quantity,
            "price": filled_price,
            "total_value": filled_value,
            "portfolio_value": float(portfolio.cash_balance)
        }
    )
    
    log.info(f"✅ Trade recorded: {order.side.value} {order.quantity} {order.symbol} @ ${filled_price}")


async def calculate_realized_pnl(user_id: int) -> float:
    """
    Calculate total realized P&L from all closed trades
    
    Args:
        user_id: User ID
        
    Returns:
        Total realized profit/loss
    """
    # TODO: Sum realized_pnl from all trades
    # For now, return 0 (unrealized P&L in positions is more important for MVP)
    return 0.0
