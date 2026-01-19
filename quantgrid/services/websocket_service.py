# backend/services/websocket_service.py
"""
WebSocket Connection Manager

Real-time streaming for:
- Live price updates
- Technical indicator updates
- Portfolio P&L changes
- Trading alerts

Phase 3: Advanced Features
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
from datetime import datetime
from quantgrid.services.quote_service import get_realtime_quote
from quantgrid.services.indicators_service import get_indicators, calculate_streaming_indicator
from quantgrid.services.portfolio_service import get_portfolio_summary
from quantgrid.core.logger import log
import asyncio
import json


class ConnectionManager:
    """
    Manages WebSocket connections and subscriptions
    """
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.user_subscriptions: Dict[int, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """
        Accept new WebSocket connection
        
        Args:
            websocket: WebSocket instance
            user_id: Authenticated user ID
        """
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
            self.user_subscriptions[user_id] = set()
        
        self.active_connections[user_id].append(websocket)
        log.info(f"🔌 WebSocket connected: user {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """
        Remove WebSocket connection
        """
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # Clean up if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                if user_id in self.user_subscriptions:
                    del self.user_subscriptions[user_id]
        
        log.info(f"🔌 WebSocket disconnected: user {user_id}")
    
    async def subscribe(self, user_id: int, symbol: str):
        """
        Subscribe user to symbol updates
        
        Args:
            user_id: User ID
            symbol: Stock/crypto symbol
        """
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].add(symbol.upper())
            log.info(f"📡 User {user_id} subscribed to {symbol}")
    
    async def unsubscribe(self, user_id: int, symbol: str):
        """Unsubscribe from symbol"""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(symbol.upper())
            log.info(f"📡 User {user_id} unsubscribed from {symbol}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send message to specific WebSocket
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            log.error(f"Failed to send WebSocket message: {e}")
    
    async def broadcast_to_user(self, user_id: int, message: dict):
        """
        Broadcast message to all connections for a user
        
        Args:
            user_id: User ID
            message: Message dict
        """
        if user_id in self.active_connections:
            dead_connections = []
            
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    log.warning(f"Dead connection for user {user_id}: {e}")
                    dead_connections.append(connection)
            
            # Clean up dead connections
            for conn in dead_connections:
                self.disconnect(conn, user_id)
    
    async def broadcast_to_subscribers(self, symbol: str, message: dict):
        """
        Broadcast message to all users subscribed to a symbol
        
        Args:
            symbol: Stock symbol
            message: Message dict
        """
        symbol = symbol.upper()
        
        for user_id, subscriptions in self.user_subscriptions.items():
            if symbol in subscriptions:
                await self.broadcast_to_user(user_id, message)
    
    def get_all_subscriptions(self) -> Set[str]:
        """Get set of all currently subscribed symbols"""
        all_subs = set()
        for subs in self.user_subscriptions.values():
            all_subs.update(subs)
        return all_subs


# Global connection manager instance
manager = ConnectionManager()


async def start_price_streaming():
    """
    Background task: Stream real-time price updates
    
    Runs every 5 seconds, updates all subscribed symbols
    """
    log.info("📡 Starting price streaming background task")
    
    while True:
        try:
            # Get all symbols with active subscriptions
            symbols = manager.get_all_subscriptions()
            
            if symbols:
                log.debug(f"📡 Streaming {len(symbols)} symbols: {symbols}")
                
                for symbol in symbols:
                    try:
                        # Fetch latest quote
                        quote = await get_realtime_quote(symbol)
                        
                        if quote:
                            message = {
                                "type": "price_update",
                                "symbol": symbol,
                                "price": quote["price"],
                                "change": quote["change"],
                                "percent_change": quote["change_percent"],
                                "high": quote["high"],
                                "low": quote["low"],
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            
                            # Broadcast to subscribers
                            await manager.broadcast_to_subscribers(symbol, message)
                            
                    except Exception as e:
                        log.error(f"Error streaming {symbol}: {e}")
            
            # Wait 5 seconds before next update
            await asyncio.sleep(5)
            
        except Exception as e:
            log.error(f"Price streaming error: {e}")
            await asyncio.sleep(5)


async def start_portfolio_streaming():
    """
    Background task: Stream live portfolio P&L updates
    
    Runs every 10 seconds for users with active connections
    """
    log.info("📊 Starting portfolio streaming background task")
    
    while True:
        try:
            # Get all connected users
            connected_users = list(manager.active_connections.keys())
            
            for user_id in connected_users:
                try:
                    # Get latest portfolio summary
                    summary = await get_portfolio_summary(user_id)
                    
                    message = {
                        "type": "portfolio_update",
                        "cash_balance": summary["cash_balance"],
                        "total_value": summary["total_value"],
                        "unrealized_pnl": summary["unrealized_pnl"],
                        "total_gain_percent": summary["total_gain_percent"],
                        "positions_count": summary["positions_count"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    await manager.broadcast_to_user(user_id, message)
                    
                except Exception as e:
                    log.error(f"Portfolio streaming error for user {user_id}: {e}")
            
            # Wait 10 seconds
            await asyncio.sleep(10)
            
        except Exception as e:
            log.error(f"Portfolio streaming error: {e}")
            await asyncio.sleep(10)


def get_manager() -> ConnectionManager:
    """Get global connection manager instance"""
    return manager
