# backend/routes/paper_trading.py
"""
Paper Trading API Routes
Endpoints for virtual portfolio management and order execution
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from anchorgrid.core.dependencies import get_current_user
from anchorgrid.db.models import User, OrderSide, OrderType
from anchorgrid.services.portfolio_service import (
    get_portfolio_summary,
    reset_portfolio
)
from anchorgrid.services.order_service import (
    place_order,
    cancel_order,
    get_order_history
)
from anchorgrid.core.logger import log

router = APIRouter()


# Request models
class OrderRequest(BaseModel):
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    order_type: str = "market"  # "market" or "limit"
    limit_price: Optional[float] = None


@router.get("/portfolio")
async def get_portfolio(
    current_user: User = Depends(get_current_user)
):
    """
    Get portfolio summary with positions and P&L
    
    Returns:
        - cash_balance: Available cash
        - total_value: Cash + positions value
        - positions: List of holdings
        - unrealized_pnl: Total unrealized profit/loss
    """
    try:
        summary = await get_portfolio_summary(current_user.id)
        log.info(f"📊 Portfolio viewed by user {current_user.id}")
        return summary
    except Exception as e:
        log.error(f"Error getting portfolio: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch portfolio")


@router.post("/portfolio/reset")
async def reset_user_portfolio(
    current_user: User = Depends(get_current_user)
):
    """
    Reset portfolio to $100k (for testing)
    
    ⚠️ WARNING: Deletes all positions and orders!
    """
    try:
        result = await reset_portfolio(current_user.id)
        log.info(f"♻️ Portfolio reset by user {current_user.id}")
        return result
    except Exception as e:
        log.error(f"Error resetting portfolio: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset portfolio")


@router.post("/orders")
async def create_order(
    order: OrderRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Place new trade order
    
    Request body:
        {
            "symbol": "AAPL",
            "side": "buy",  // or "sell"
            "quantity": 10,
            "order_type": "market",  // MVP: market only
            "limit_price": null  // For limit orders (future)
        }
    
    Returns:
        Order details with execution status
    """
    try:
        # Validate side
        try:
            side_enum = OrderSide(order.side.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid side (must be 'buy' or 'sell')")
        
        # Validate order type
        try:
            type_enum = OrderType(order.order_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid order_type (must be 'market' or 'limit')")
        
        # Validate quantity
        if order.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
        
        # Place order
        result = await place_order(
            user_id=current_user.id,
            symbol=order.symbol,
            side=side_enum,
            quantity=order.quantity,
            order_type=type_enum,
            limit_price=order.limit_price
        )
        
        log.info(f"📝 Order placed by user {current_user.id}: {order.side} {order.quantity} {order.symbol}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error placing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def list_orders(
    current_user: User = Depends(get_current_user)
):
    """
    Get order history for current user
    
    Returns list of all orders (pending, filled, cancelled)
    """
    try:
        orders = await get_order_history(current_user.id)
        log.info(f"📋 Order history viewed by user {current_user.id}")
        return {"orders": orders}
    except Exception as e:
        log.error(f"Error getting order history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch orders")


@router.delete("/orders/{order_id}")
async def cancel_pending_order(
    order_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel pending order
    
    Only works for orders with status='pending'
    """
    try:
        result = await cancel_order(order_id, current_user.id)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        log.info(f"🚫 Order {order_id} cancelled by user {current_user.id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error cancelling order: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel order")
