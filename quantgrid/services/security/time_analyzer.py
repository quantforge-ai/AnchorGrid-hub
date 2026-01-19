# backend/services/security/time_analyzer.py
"""
Time Pattern Analysis Service

Trust Factor: 15% weight in ensemble

Features:
- Track user's typical login hours
- Build hour-of-day and day-of-week histograms
- Detect unusual login times
- Calculate time-based trust score
"""

from datetime import datetime, timezone
from typing import Optional
from quantgrid.db.session import AsyncSessionLocal
from quantgrid.db.models import UserLoginPattern
from quantgrid.core.logger import log
from sqlalchemy import select


async def update_time_pattern(user_id: int, login_time: datetime):
    """
    Update user's login time pattern histogram
    
    - Increments hour-of-day counter
    - Increments day-of-week counter
    - Updates peak hours list
    """
    async with AsyncSessionLocal() as db:
        # Get or create login pattern
        result = await db.execute(
            select(UserLoginPattern).where(UserLoginPattern.user_id == user_id)
        )
        pattern = result.scalar_one_or_none()
        
        if not pattern:
            pattern = UserLoginPattern(
                user_id=user_id,
                hour_histogram={},
                weekday_histogram={},
                peak_hours=[],
                total_logins=0
            )
            db.add(pattern)
        
        # Update hour histogram (0-23)
        hour = login_time.hour
        hour_hist = pattern.hour_histogram or {}
        hour_hist[str(hour)] = hour_hist.get(str(hour), 0) + 1
        pattern.hour_histogram = hour_hist
        
        # Update weekday histogram (0-6, Monday=0)
        weekday = login_time.weekday()
        weekday_hist = pattern.weekday_histogram or {}
        weekday_hist[str(weekday)] = weekday_hist.get(str(weekday), 0) + 1
        pattern.weekday_histogram = weekday_hist
        
        # Update total logins
        pattern.total_logins += 1
        
        # Calculate peak hours (hours with >10 logins)
        peak_hours = [int(h) for h, count in hour_hist.items() if count >= 10]
        pattern.peak_hours = peak_hours
        
        # Update timezone if not set (use current timezone)
        if not pattern.typical_timezone:
            pattern.typical_timezone = str(login_time.tzinfo) if login_time.tzinfo else "UTC"
        
        pattern.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        log.debug(f"🕐 Updated time pattern: hour={hour}, weekday={weekday}, total_logins={pattern.total_logins}")


async def verify_time_pattern(user_id: int, login_time: datetime) -> float:
    """
    Calculate trust score for login time (0.0-1.0)
    
    15% weight in ensemble trust score
    
    Trust levels:
    - 1.0: Login during peak hours (>10 previous logins)
    - 0.9: Login during moderate hours (5-10 logins)
    - 0.7: Login during rare hours (1-5 logins)
    - 0.5: Login during never-seen hours
    - 0.3: Login at unusual time (e.g., 3AM when usually 9AM-5PM)
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserLoginPattern).where(UserLoginPattern.user_id == user_id)
        )
        pattern = result.scalar_one_or_none()
        
        if not pattern or pattern.total_logins < 5:
            # Not enough data - neutral score
            log.info(f"🕐 Insufficient login history for time pattern analysis")
            return 0.7
        
        hour = login_time.hour
        hour_hist = pattern.hour_histogram or {}
        hour_count = hour_hist.get(str(hour), 0)
        
        # Calculate trust based on historical frequency
        if hour_count >= 10:
            log.info(f"🕐 Peak hour login (hour {hour}, {hour_count} previous logins)")
            return 1.0
        elif hour_count >= 5:
            log.info(f"🕐 Moderate hour login (hour {hour}, {hour_count} previous logins)")
            return 0.9
        elif hour_count >= 1:
            log.info(f"🕐 Rare hour login (hour {hour}, {hour_count} previous logins)")
            return 0.7
        else:
            # Never seen this hour before
            
            # Check if this is drastically different from peak hours
            peak_hours = pattern.peak_hours or []
            
            if peak_hours:
                # Calculate distance from nearest peak hour
                min_distance = min(abs(hour - peak) for peak in peak_hours)
                
                # If more than 6 hours from any peak, it's suspicious
                if min_distance > 6:
                    log.warning(f"🕐 SUSPICIOUS: Login at hour {hour}, far from peaks {peak_hours}")
                    return 0.3
                else:
                    log.info(f"🕐 New hour, but close to peak hours")
                    return 0.5
            else:
                log.info(f"🕐 First login at hour {hour}")
                return 0.5


async def get_login_pattern_summary(user_id: int) -> dict:
    """
    Get user's login pattern summary for debugging/display
    
    Returns:
        {
            "peak_hours": [9, 10, 14, 15, 16],
            "total_logins": 127,
            "most_common_hour": 14,
            "most_common_day": "Monday"
        }
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(UserLoginPattern).where(UserLoginPattern.user_id == user_id)
        )
        pattern = result.scalar_one_or_none()
        
        if not pattern:
            return {
                "peak_hours": [],
                "total_logins": 0,
                "most_common_hour": None,
                "most_common_day": None
            }
        
        hour_hist = pattern.hour_histogram or {}
        weekday_hist = pattern.weekday_histogram or {}
        
        # Find most common hour
        most_common_hour = max(hour_hist.items(), key=lambda x: x[1])[0] if hour_hist else None
        
        # Find most common day
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        most_common_day_idx = max(weekday_hist.items(), key=lambda x: x[1])[0] if weekday_hist else None
        most_common_day = day_names[int(most_common_day_idx)] if most_common_day_idx else None
        
        return {
            "peak_hours": pattern.peak_hours or [],
            "total_logins": pattern.total_logins,
            "most_common_hour": int(most_common_hour) if most_common_hour else None,
            "most_common_day": most_common_day
        }
