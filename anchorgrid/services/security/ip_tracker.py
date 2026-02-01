# backend/services/security/ip_tracker.py
"""
IP Tracking & Geolocation Service

Trust Factor: 30% weight in ensemble

Features:
- Track user login IPs
- Geolocate IPs using free ip-api.com
- Detect VPNs and proxies
- Calculate trust score based on IP history
- Detect suspicious geographic jumps
"""

import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional
from anchorgrid.db.session import AsyncSessionLocal
from anchorgrid.db.models import UserIPHistory
from anchorgrid.core.logger import log
from sqlalchemy import select, and_
import math


async def get_ip_geolocation(ip_address: str) -> dict:
    """
    Get geolocation data for an IP address using ip-api.com (free tier)
    
    Free tier limits: 45 requests/minute
    
    Returns:
        {
            "country": "US",
            "countryCode": "US", 
            "city": "New York",
            "lat": 40.7128,
            "lon": -74.0060,
            "proxy": false
        }
    """
    try:
        url = f"http://ip-api.com/json/{ip_address}"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "success":
                    return {
                        "country": data.get("country"),
                        "country_code": data.get("countryCode"),
                        "city": data.get("city"),
                        "latitude": data.get("lat"),
                        "longitude": data.get("lon"),
                        "is_proxy": data.get("proxy", False)
                    }
        
        log.warning(f"IP geolocation failed for {ip_address}")
        return {}
        
    except Exception as e:
        log.error(f"IP geolocation error for {ip_address}: {e}")
        return {}


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (
        math.sin(delta_lat / 2) ** 2 +
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


async def track_ip_login(user_id: int, ip_address: str):
    """
    Track user login from IP address
    
    - Creates or updates IP history record
    - Fetches geolocation if new IP
    - Updates last_seen timestamp
    """
    async with AsyncSessionLocal() as db:
        # Check if IP already tracked for this user
        result = await db.execute(
            select(UserIPHistory).where(
                and_(
                    UserIPHistory.user_id == user_id,
                    UserIPHistory.ip_address == ip_address
                )
            )
        )
        ip_record = result.scalar_one_or_none()
        
        if ip_record:
            # Update existing record
            ip_record.last_seen = datetime.now(timezone.utc)
            ip_record.login_count += 1
            log.debug(f"🌍 Known IP login: {ip_address} (count: {ip_record.login_count})")
        else:
            # New IP - geolocate it
            geo_data = await get_ip_geolocation(ip_address)
            
            ip_record = UserIPHistory(
                user_id=user_id,
                ip_address=ip_address,
                country=geo_data.get("country_code"),
                country_name=geo_data.get("country"),
                city=geo_data.get("city"),
                latitude=geo_data.get("latitude"),
                longitude=geo_data.get("longitude"),
                is_proxy=geo_data.get("is_proxy", False),
                is_vpn=False,  # TODO: VPN detection
                first_seen=datetime.now(timezone.utc),
                last_seen=datetime.now(timezone.utc),
                login_count=1
            )
            db.add(ip_record)
            log.info(f"🌍 New IP login: {ip_address} from {geo_data.get('city', 'Unknown')}, {geo_data.get('country', 'Unknown')}")
        
        await db.commit()


async def verify_ip_trust(user_id: int, ip_address: str, current_country: Optional[str] = None) -> float:
    """
    Calculate trust score for IP address (0.0-1.0)
    
    30% weight in ensemble trust score
    
    Trust levels:
    - 1.0: Known IP (90+ days)
    - 0.9: Recent IP (30-90 days)
    - 0.7: New IP, same country
    - 0.5: New IP, different country
    - 0.3: VPN detected
    - 0.2: Geographic jump (>1000km in <1 hour)
    """
    async with AsyncSessionLocal() as db:
        # Get user's IP history
        result = await db.execute(
            select(UserIPHistory)
            .where(UserIPHistory.user_id == user_id)
            .order_by(UserIPHistory.last_seen.desc())
        )
        ip_history = result.scalars().all()
        
        if not ip_history:
            # First-time login - neutral score
            log.info(f"🌍 First IP login for user {user_id}")
            return 0.6
        
        # Check if current IP is known
        current_ip_record = next((ip for ip in ip_history if ip.ip_address == ip_address), None)
        
        if current_ip_record:
            # Known IP - calculate trust based on age
            days_known = (datetime.now(timezone.utc) - current_ip_record.first_seen).days
            
            if current_ip_record.is_vpn or current_ip_record.is_proxy:
                log.warning(f"🌍 VPN/Proxy detected for user {user_id}")
                return 0.3
            
            if days_known >= 90:
                log.info(f"🌍 Trusted IP (known {days_known} days)")
                return 1.0
            elif days_known >= 30:
                log.info(f"🌍 Recent known IP (known {days_known} days)")
                return 0.9
            else:
                log.info(f"🌍 New known IP (known {days_known} days)")
                return 0.8
        
        # New IP - check for suspicious patterns
        most_recent = ip_history[0]
        
        # Check for geographic jump (impossible travel)
        if (current_ip_record is None and most_recent.latitude and most_recent.longitude):
            
            # Get geolocation for new IP
            geo_data = await get_ip_geolocation(ip_address)
            
            if geo_data.get("latitude") and geo_data.get("longitude"):
                distance = calculate_distance_km(
                    most_recent.latitude, most_recent.longitude,
                    geo_data["latitude"], geo_data["longitude"]
                )
                
                time_diff = (datetime.now(timezone.utc) - most_recent.last_seen).total_seconds() / 3600
                
                # Impossible travel: >1000km in <1 hour
                if distance > 1000 and time_diff < 1:
                    log.warning(f"🌍 SUSPICIOUS: Geographic jump {distance:.0f}km in {time_diff:.1f}h")
                    return 0.2
                
                # Same country
                if geo_data.get("country_code") == most_recent.country:
                    log.info(f"🌍 New IP, same country ({most_recent.country})")
                    return 0.7
                else:
                    log.warning(f"🌍 New IP, different country ({most_recent.country} → {geo_data.get('country_code')})")
                    return 0.5
        
        # Default for new IP
        return 0.6
