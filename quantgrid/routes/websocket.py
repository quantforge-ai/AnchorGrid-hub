# backend/routes/websocket.py
"""
WebSocket API Routes
Real-time streaming endpoints
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from quantgrid.core.dependencies import get_current_user
from quantgrid.services.websocket_service import get_manager
from quantgrid.core.logger import log
import json

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time streaming
    
    Connection requires authentication token in query params:
        ws://localhost:8000/ws?token=<jwt_token>
    
    Message Protocol:
        Client → Server:
            {"action": "subscribe", "symbol": "AAPL"}
            {"action": "unsubscribe", "symbol": "AAPL"}
            {"action": "ping"}
        
        Server → Client:
            {"type": "price_update", "symbol": "AAPL", "price": 195.50, ...}
            {"type": "portfolio_update", "total_value": 105000.00, ...}
            {"type": "pong"}
    """
    manager = get_manager()
    user_id = None
    
    try:
        # TODO: Extract token from query params and validate
        # For now, accept connection (add auth in Phase 4)
        user_id = 1  # Placeholder - will be extracted from JWT
        
        await manager.connect(websocket, user_id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket connection established",
            "user_id": user_id
        })
        
        # Message loop
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                action = message.get("action")
                
                if action == "subscribe":
                    symbol = message.get("symbol", "").upper()
                    if symbol:
                        await manager.subscribe(user_id, symbol)
                        await websocket.send_json({
                            "type": "subscribed",
                            "symbol": symbol
                        })
                
                elif action == "unsubscribe":
                    symbol = message.get("symbol", "").upper()
                    if symbol:
                        await manager.unsubscribe(user_id, symbol)
                        await websocket.send_json({
                            "type": "unsubscribed",
                            "symbol": symbol
                        })
                
                elif action == "ping":
                    await websocket.send_json({"type": "pong"})
                
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown action: {action}"
                    })
            
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON"
                })
    
    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(websocket, user_id)
        log.info(f"🔌 WebSocket disconnected: user {user_id}")
    
    except Exception as e:
        log.error(f"WebSocket error: {e}")
        if user_id:
            manager.disconnect(websocket, user_id)
