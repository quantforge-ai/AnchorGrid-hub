# backend/services/security/__init__.py
"""
Security Services Package

Trust Score Ensemble Components:
- IP Tracking (30% weight)
- Device Fingerprinting (25% weight)
- Time Pattern Analysis (15% weight)
- API Behavior Monitoring (10% weight)
- Shadow Watch (20% weight) - in parent services/

Total: 100% trust score
"""

from quantgrid.services.security.ip_tracker import verify_ip_trust, track_ip_login
from quantgrid.services.security.device_fingerprint import verify_device_trust, track_device_login
from quantgrid.services.security.time_analyzer import verify_time_pattern, update_time_pattern
from quantgrid.services.security.api_monitor import get_api_behavior_score, track_api_request

__all__ = [
    "verify_ip_trust",
    "track_ip_login",
    "verify_device_trust",
    "track_device_login",
    "verify_time_pattern",
    "update_time_pattern",
    "get_api_behavior_score",
    "track_api_request"
]
