# backend/services/redis_service.py
"""
Redis caching service for QuantTerminal
Handles session storage, rate limiting, and quote caching
"""
from redis.asyncio import Redis
from quantgrid.core.config import get_settings
from quantgrid.core.logger import log
import json
from typing import Any

settings = get_settings()

redis_client: Redis | None = None


async def get_redis_client() -> Redis | None:
    """Get or create Redis client"""
    global redis_client
    if redis_client is None:
        try:
            redis_client = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5
            )
            await redis_client.ping()
            log.info("✅ Redis client initialized")
        except Exception as e:
            log.error(f"❌ Redis connection failed: {e}")
            redis_client = None
    return redis_client


async def close_redis():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        log.info("Redis connection closed")


# === CACHE OPERATIONS - READY TO USE ===

async def set_cache(key: str, value: Any, ttl: int = 3600) -> bool:
    """
    Cache value with TTL
    
    Args:
        key: Cache key
        value: Any JSON-serializable value
        ttl: Time to live in seconds (default 1 hour)
    """
    client = await get_redis_client()
    if client is None:
        log.warning("Redis unavailable - cache skip")
        return False
    
    try:
        serialized = json.dumps(value)
        await client.set(key, serialized, ex=ttl)
        log.debug(f"Cached: {key} (TTL: {ttl}s)")
        return True
    except Exception as e:
        log.error(f"Redis set failed for {key}: {e}")
        return False


async def get_cache(key: str) -> Any | None:
    """
    Retrieve from cache
    
    Returns:
        Cached value or None if not found/expired
    """
    client = await get_redis_client()
    if client is None:
        return None
    
    try:
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        log.error(f"Redis get failed for {key}: {e}")
        return None


async def delete_cache(key: str) -> bool:
    """Delete cache key"""
    client = await get_redis_client()
    if client is None:
        return False
    
    try:
        await client.delete(key)
        return True
    except Exception as e:
        log.error(f"Redis delete failed for {key}: {e}")
        return False


async def increment_counter(key: str, ttl: int = 3600) -> int:
    """
    Increment counter (for rate limiting)
    
    Returns:
        Current count after increment
    """
    client = await get_redis_client()
    if client is None:
        return 0
    
    try:
        count = await client.incr(key)
        if count == 1:  # First increment, set expiry
            await client.expire(key, ttl)
        return count
    except Exception as e:
        log.error(f"Redis incr failed for {key}: {e}")
        return 0


# === PLACEHOLDERS FOR FUTURE ===

async def publish_event(channel: str, message: dict) -> bool:
    """
    Publish to Redis pub/sub (for WebSocket fan-out)
    TODO: Implement in Phase 3
    """
    raise NotImplementedError("Redis pub/sub placeholder")


async def subscribe_to_events(channel: str):
    """
    Subscribe to Redis pub/sub
    TODO: Implement in Phase 3
    """
    raise NotImplementedError("Redis subscribe placeholder")
