# backend/services/security/api_monitor.py
"""
API Behavior Monitoring Service

Trust Factor: 10% weight in ensemble

Features:
- Track API request rates using Redis
- Monitor failed login attempts
- Detect automated attacks
- Calculate behavior-based trust score
"""

from datetime import datetime, timezone, timedelta
from quantgrid.db.session import AsyncSessionLocal
from quantgrid.db.models import UserAPIActivity
from quantgrid.services.redis_service import get_redis_client
from quantgrid.core.logger import log
from sqlalchemy import select


async def track_api_request(user_id: int, endpoint: str):
    """
    Track API request for rate monitoring
    
    - Increments request counters
    - Uses Redis for real-time rate limiting
    - Updates database for historical tracking
    """
    redis_client = await get_redis_client()
    
    if redis_client:
        # Use Redis for real-time rate tracking
        try:
            # Increment minute counter
            minute_key = f"api_rate:{user_id}:minute"
            await redis_client.incr(minute_key)
            await redis_client.expire(minute_key, 60)  # Expire after 1 minute
            
            # Increment hour counter
            hour_key = f"api_rate:{user_id}:hour"
            await redis_client.incr(hour_key)
            await redis_client.expire(hour_key, 3600)  # Expire after 1 hour
            
            # Increment day counter
            day_key = f"api_rate:{user_id}:day"
            await redis_client.incr(day_key)
            await redis_client.expire(day_key, 86400)  # Expire after 1 day
            
        except Exception as e:
            log.warning(f"Redis API tracking failed: {e}")
    
    # Update database (less frequently)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserAPIActivity).where(UserAPIActivity.user_id == user_id)
        )
        activity = result.scalar_one_or_none()
        
        if not activity:
            activity = UserAPIActivity(
                user_id=user_id,
                requests_last_minute=1,
                requests_last_hour=1,
                requests_last_day=1,
                failed_logins_last_hour=0,
                failed_logins_last_day=0,
                suspicious_endpoints=[],
                rapid_requests_detected=False,
                last_request=datetime.now(timezone.utc),
                last_activity_reset=datetime.now(timezone.utc)
            )
            db.add(activity)
        else:
            activity.last_request = datetime.now(timezone.utc)
            
            # Reset counters if 24 hours passed
            if (datetime.now(timezone.utc) - activity.last_activity_reset).total_seconds() > 86400:
                activity.requests_last_minute = 0
                activity.requests_last_hour = 0
                activity.requests_last_day = 0
                activity.last_activity_reset = datetime.now(timezone.utc)
        
        await db.commit()


async def track_failed_login(user_id: int):
    """
    Track failed login attempt
    
    Used to detect brute-force attacks
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserAPIActivity).where(UserAPIActivity.user_id == user_id)
        )
        activity = result.scalar_one_or_none()
        
        if not activity:
            activity = UserAPIActivity(
                user_id=user_id,
                failed_logins_last_hour=1,
                failed_logins_last_day=1,
                last_failed_login=datetime.now(timezone.utc)
            )
            db.add(activity)
        else:
            # Reset counters if hour passed
            if activity.last_failed_login:
                hours_since_last = (datetime.now(timezone.utc) - activity.last_failed_login).total_seconds() / 3600
                
                if hours_since_last > 1:
                    activity.failed_logins_last_hour = 0
                if hours_since_last > 24:
                    activity.failed_logins_last_day = 0
            
            activity.failed_logins_last_hour += 1
            activity.failed_logins_last_day += 1
            activity.last_failed_login = datetime.now(timezone.utc)
        
        await db.commit()
        
        if activity.failed_logins_last_hour >= 3:
            log.warning(f"⚠️ Multiple failed logins for user {user_id}: {activity.failed_logins_last_hour} in last hour")


async def get_api_behavior_score(user_id: int) -> float:
    """
    Calculate trust score for API behavior (0.0-1.0)
    
    10% weight in ensemble trust score
    
    Trust levels:
    - 1.0: Normal request rate (<100/hour)
    - 0.9: Elevated rate (100-500/hour)
    - 0.6: High rate (500-1000/hour)
    - 0.3: Suspicious rate (>1000/hour)
    - 0.2: Multiple failed logins (>3/hour)
    - 0.1: Rapid automated requests detected
    """
    redis_client = await get_redis_client()
    
    # Try to get real-time rate from Redis first
    if redis_client:
        try:
            minute_key = f"api_rate:{user_id}:minute"
            hour_key = f"api_rate:{user_id}:hour"
            
            requests_per_minute = await redis_client.get(minute_key)
            requests_per_hour = await redis_client.get(hour_key)
            
            req_per_min = int(requests_per_minute) if requests_per_minute else 0
            req_per_hour = int(requests_per_hour) if requests_per_hour else 0
            
            # Check for rapid burst (>30 requests in 1 minute)
            if req_per_min > 30:
                log.warning(f"🚨 RAPID BURST: {req_per_min} requests/minute for user {user_id}")
                return 0.1
            
            # Check hourly rate
            if req_per_hour > 1000:
                log.warning(f"🚨 High rate: {req_per_hour} requests/hour for user {user_id}")
                return 0.3
            elif req_per_hour > 500:
                log.info(f"⚠️ Elevated rate: {req_per_hour} requests/hour")
                return 0.6
            elif req_per_hour > 100:
                log.info(f"Moderate rate: {req_per_hour} requests/hour")
                return 0.9
            else:
                log.debug(f"Normal rate: {req_per_hour} requests/hour")
                return 1.0
                
        except Exception as e:
            log.error(f"Redis rate check failed: {e}")
    
    # Fallback to database
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserAPIActivity).where(UserAPIActivity.user_id == user_id)
        )
        activity = result.scalar_one_or_none()
        
        if not activity:
            # No activity data - neutral score
            return 1.0
        
        # Check failed logins
        if activity.failed_logins_last_hour >= 5:
            log.warning(f"🚨 Brute force attack suspected: {activity.failed_logins_last_hour} failed logins")
            return 0.2
        elif activity.failed_logins_last_hour >= 3:
            log.warning(f"⚠️ Multiple failed logins: {activity.failed_logins_last_hour}")
            return 0.4
        
        # Check rapid requests flag
        if activity.rapid_requests_detected:
            log.warning(f"🚨 Automated requests detected")
            return 0.1
        
        # Default to high trust if no suspicious activity
        return 1.0
