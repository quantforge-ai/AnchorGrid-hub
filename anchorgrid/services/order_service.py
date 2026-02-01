# backend/services/order_service.py
"""
Order Service - Trade Order Management

Handles order placement, execution, and cancellation.
MVP: Market orders only (instant execution).

Phase 2D: Paper Trading Implementation
"""

from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Dict
from anchorgrid.db.session import AsyncSessionLocal
from anchorgrid.db.models import Portfolio, TradeOrder, OrderSide, OrderType, OrderStatus
from anchorgrid.services.portfolio_service import get_or_create_portfolio
from anchorgrid.services.trade_service import record_trade
from anchorgrid.services.quote_service import get_realtime_quote, get_historical_data
from anchorgrid.core.logger import log
from sqlalchemy import select


async def place_order(
    user_id: int,
    symbol: str,
    side: OrderSide,
    quantity: float,
    order_type: OrderType = OrderType.MARKET,
    limit_price: float | None = None
) -> Dict:
    """
    Place new trade order
    
    Args:
        user_id: User ID
        symbol: Stock symbol
        side: BUY or SELL
        quantity: Number of shares
        order_type: MARKET or LIMIT (MVP: market only)
        limit_price: Price for limit orders
        
    Returns:
        Order details with execution status
    """
    symbol = symbol.upper()
    
    async with AsyncSessionLocal() as db:
        portfolio = await get_or_create_portfolio(user_id, db)
        
        # Refresh portfolio with session
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio.id)
        )
        portfolio = result.scalar_one()
        
        # Create order
        order = TradeOrder(
            portfolio_id=portfolio.id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            limit_price=limit_price,
            status=OrderStatus.PENDING
        )
        
        db.add(order)
        await db.commit()
        await db.refresh(order)
        
        log.info(f"📝 Order placed: {order.id} - {side.value} {quantity} {symbol}")
        
        # Execute immediately for market orders
        if order_type == OrderType.MARKET:
            await execute_market_order(order, db)
            await db.refresh(order)
        
        return {
            "order_id": order.id,
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": order.quantity,
            "order_type": order.order_type.value,
            "status": order.status.value,
            "filled_price": float(order.filled_price) if order.filled_price else None,
            "created_at": order.created_at.isoformat(),
            "filled_at": order.filled_at.isoformat() if order.filled_at else None
        }


async def execute_market_order(order: TradeOrder, db):
    """
    Execute market order at current price
    
    Args:
        order: TradeOrder instance
        db: Database session
    """
    try:
        # Get current market price
        quote = await get_realtime_quote(order.symbol)
        
        if not quote:
            order.status = OrderStatus.REJECTED
            log.error(f"❌ No quote available for {order.symbol}")
            await db.commit()
            return
        
        filled_price = float(quote["price"])
        
        # Record trade and update position
        await record_trade(order, filled_price, db)
        
        log.info(f"✅ Market order executed: {order.symbol} @ ${filled_price}")
        
    except Exception as e:
        order.status = OrderStatus.REJECTED
        log.error(f"❌ Order execution failed: {e}")
        await db.commit()


async def cancel_order(order_id: int, user_id: int) -> Dict:
    """
    Cancel pending order
    
    Args:
        order_id: Order ID
        user_id: User ID (for authorization)
        
    Returns:
        Cancellation confirmation
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TradeOrder).where(TradeOrder.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            return {"error": "Order not found"}
        
        if order.portfolio.user_id != user_id:
            return {"error": "Unauthorized"}
        
        if order.status != OrderStatus.PENDING:
            return {"error": f"Cannot cancel order with status: {order.status.value}"}
        
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.now(timezone.utc)
        await db.commit()
        
        log.info(f"🚫 Order cancelled: {order_id}")
        
        return {
            "message": "Order cancelled",
            "order_id": order_id,
            "symbol": order.symbol
        }


async def get_order_history(user_id: int) -> List[Dict]:
    """
    Get all orders for user
    
    Args:
        user_id: User ID
        
    Returns:
        List of order details
    """
    async with AsyncSessionLocal() as db:
        portfolio = await get_or_create_portfolio(user_id, db)
        
        result = await db.execute(
            select(TradeOrder)
            .where(TradeOrder.portfolio_id == portfolio.id)
            .order_by(TradeOrder.created_at.desc())
        )
        orders = result.scalars().all()
        
        return [
            {
                "order_id": order.id,
                "symbol": order.symbol,
                "side": order.side.value,
                "quantity": order.quantity,
                "order_type": order.order_type.value,
                "status": order.status.value,
                "filled_price": float(order.filled_price) if order.filled_price else None,
                "filled_quantity": order.filled_quantity,
                "total_value": float(order.total_value) if order.total_value else None,
                "created_at": order.created_at.isoformat(),
                "filled_at": order.filled_at.isoformat() if order.filled_at else None
            }
            for order in orders
        ]
