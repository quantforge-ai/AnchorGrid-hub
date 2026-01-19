# backend/services/security/device_fingerprint.py
"""
Device Fingerprinting Service

Trust Factor: 25% weight in ensemble

Features:
- Parse User-Agent strings
- Generate device fingerprints
- Track known vs. unknown devices
- Calculate device-based trust score
"""

import hashlib
from datetime import datetime, timezone
from typing import Optional
from user_agents import parse
from quantgrid.db.session import AsyncSessionLocal
from quantgrid.db.models import UserDevice
from quantgrid.core.logger import log
from sqlalchemy import select, and_


def generate_device_fingerprint(user_agent: str, additional_data: Optional[dict] = None) -> str:
    """
    Generate device fingerprint hash from User-Agent and optional data
    
    Args:
        user_agent: Browser User-Agent string
        additional_data: Optional dict with screen resolution, timezone, etc.
    
    Returns:
        SHA-256 hash of device characteristics
    """
    fingerprint_input = user_agent
    
    if additional_data:
        # Add screen resolution, timezone, etc. if provided
        fingerprint_input += str(additional_data.get("screen_resolution", ""))
        fingerprint_input += str(additional_data.get("timezone", ""))
        fingerprint_input += str(additional_data.get("language", ""))
    
    return hashlib.sha256(fingerprint_input.encode()).hexdigest()


async def track_device_login(user_id: int, user_agent: str, additional_data: Optional[dict] = None):
    """
    Track user login from a device
    
    - Parses User-Agent
    - Generates fingerprint
    - Creates or updates device record
    """
    # Parse User-Agent
    ua = parse(user_agent)
    
    # Generate fingerprint
    fingerprint = generate_device_fingerprint(user_agent, additional_data)
    
    async with AsyncSessionLocal() as db:
        # Check if device already tracked
        result = await db.execute(
            select(UserDevice).where(
                and_(
                    UserDevice.user_id == user_id,
                    UserDevice.fingerprint_hash == fingerprint
                )
            )
        )
        device_record = result.scalar_one_or_none()
        
        if device_record:
            # Update existing device
            device_record.last_login = datetime.now(timezone.utc)
            device_record.login_count += 1
            log.debug(f"📱 Known device login: {ua.browser.family} on {ua.os.family} (count: {device_record.login_count})")
        else:
            # New device
            device_type = "mobile" if ua.is_mobile else ("tablet" if ua.is_tablet else "desktop")
            
            device_record = UserDevice(
                user_id=user_id,
                fingerprint_hash=fingerprint,
                user_agent=user_agent,
                browser=ua.browser.family,
                browser_version=ua.browser.version_string,
                os=ua.os.family,
                os_version=ua.os.version_string,
                device_type=device_type,
                is_trusted=False,  # Not trusted until verified
                first_seen=datetime.now(timezone.utc),
                last_login=datetime.now(timezone.utc),
                login_count=1
            )
            db.add(device_record)
            log.info(f"📱 New device: {ua.browser.family} on {ua.os.family} ({device_type})")
        
        await db.commit()


async def verify_device_trust(user_id: int, user_agent: str, fingerprint: Optional[str] = None) -> float:
    """
    Calculate trust score for device (0.0-1.0)
    
    25% weight in ensemble trust score
    
    Trust levels:
    - 1.0: Known trusted device (manually trusted)
    - 0.9: Known device (30+ days)
    - 0.8: Known device (7-30 days)
    - 0.6: New device, same browser family
    - 0.4: New device, different browser
    - 0.5: Mobile when usually desktop (or vice versa)
    """
    # Generate fingerprint if not provided
    if not fingerprint:
        fingerprint = generate_device_fingerprint(user_agent)
    
    async with AsyncSessionLocal() as db:
        # Get user's device history
        result = await db.execute(
            select(UserDevice)
            .where(UserDevice.user_id == user_id)
            .order_by(UserDevice.last_login.desc())
        )
        devices = result.scalars().all()
        
        if not devices:
            # First device - neutral score
            log.info(f"📱 First device login for user {user_id}")
            return 0.6
        
        # Check if current device is known
        current_device = next((d for d in devices if d.fingerprint_hash == fingerprint), None)
        
        if current_device:
            # Known device
            if current_device.is_trusted:
                log.info(f"📱 Trusted device")
                return 1.0
            
            days_known = (datetime.now(timezone.utc) - current_device.first_seen).days
            
            if days_known >= 30:
                log.info(f"📱 Known device (established {days_known} days)")
                return 0.9
            elif days_known >= 7:
                log.info(f"📱 Known device ({days_known} days)")
                return 0.8
            else:
                log.info(f"📱 Recent device ({days_known} days)")
                return 0.7
        
        # New device - analyze similarity to known devices
        ua_current = parse(user_agent)
        
        # Check if same browser family as any known device
        same_browser = any(d.browser == ua_current.browser.family for d in devices)
        
        # Check device type consistency
        current_type = "mobile" if ua_current.is_mobile else ("tablet" if ua_current.is_tablet else "desktop")
        most_common_type = max(set(d.device_type for d in devices), key=lambda t: sum(1 for d in devices if d.device_type == t))
        
        if same_browser and current_type == most_common_type:
            log.info(f"📱 New device, same browser family and type")
            return 0.6
        elif same_browser:
            log.info(f"📱 New device, same browser but different type")
            return 0.5
        else:
            log.warning(f"📱 New device, different browser")
            return 0.4
