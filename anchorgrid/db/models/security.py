# backend/db/models/security.py
"""
Security Models - Trust Score System Components

Database models for tracking:
- IP history and geolocation
- Device fingerprints
- Login time patterns
- API behavior metrics
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from anchorgrid.db.session import Base


class UserIPHistory(Base):
    """
    Track user login IPs and geographic locations
    
    Used for IP/Location trust factor (30% weight)
    """
    __tablename__ = "user_ip_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)  # IPv4 or IPv6
    country = Column(String(2), nullable=True)  # ISO country code
    country_name = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_vpn = Column(Boolean, default=False)
    is_proxy = Column(Boolean, default=False)
    first_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    login_count = Column(Integer, default=1)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'ip_address', name='uq_user_ip'),
    )
    
    # Relationships
    user = relationship("User", back_populates="ip_history")


class UserDevice(Base):
    """
    Track user devices via browser fingerprints
    
    Used for Device Fingerprint trust factor (25% weight)
    """
    __tablename__ = "user_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    fingerprint_hash = Column(String(64), unique=True, nullable=False, index=True)
    user_agent = Column(String(500), nullable=True)
    browser = Column(String(50), nullable=True)  # Chrome, Firefox, Safari, etc.
    browser_version = Column(String(20), nullable=True)
    os = Column(String(50), nullable=True)  # Windows, macOS, Linux, etc.
    os_version = Column(String(20), nullable=True)
    device_type = Column(String(20), default="desktop")  # desktop, mobile, tablet
    is_trusted = Column(Boolean, default=False)  # Manual trust flag
    first_seen = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    login_count = Column(Integer, default=1)
    
    # Relationships
    user = relationship("User", back_populates="devices")


class UserLoginPattern(Base):
    """
    Track user's typical login behavior patterns
    
    Used for Time Pattern trust factor (15% weight)
    """
    __tablename__ = "user_login_patterns"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # Hour-of-day histogram (0-23): {0: 5, 1: 0, ..., 23: 12}
    hour_histogram = Column(JSON, default=dict)
    
    # Day-of-week histogram (0-6, Monday=0): {0: 20, 1: 25, ..., 6: 5}
    weekday_histogram = Column(JSON, default=dict)
    
    # User's typical timezone (e.g., "America/New_York")
    typical_timezone = Column(String(50), nullable=True)
    
    # Peak login hours (list of hours with >10 logins)
    peak_hours = Column(JSON, default=list)
    
    # Total logins recorded
    total_logins = Column(Integer, default=0)
    
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="login_pattern")


class UserAPIActivity(Base):
    """
    Track API request rates and behavior metrics
    
    Used for API Behavior trust factor (10% weight)
    """
    __tablename__ = "user_api_activity"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # Request counters
    requests_last_minute = Column(Integer, default=0)
    requests_last_hour = Column(Integer, default=0)
    requests_last_day = Column(Integer, default=0)
    
    # Failed login tracking
    failed_logins_last_hour = Column(Integer, default=0)
    failed_logins_last_day = Column(Integer, default=0)
    last_failed_login = Column(DateTime(timezone=True), nullable=True)
    
    # Unusual activity flags
    suspicious_endpoints = Column(JSON, default=list)  # List of unusual endpoints accessed
    rapid_requests_detected = Column(Boolean, default=False)
    
    # Timestamps for rate calculation
    last_request = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_activity_reset = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    user = relationship("User", back_populates="api_activity")
