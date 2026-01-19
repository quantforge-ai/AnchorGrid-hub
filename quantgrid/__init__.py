"""
QuantGrid - Unified Financial Intelligence Platform

Shared infrastructure for both AI and Terminal projects.
"""

__version__ = "1.0.0"
__author__ = "QuantGrid Team"

# Core exports
from quantgrid.core.config import settings
from quantgrid.core.exceptions import (
    QuantGridException,
    AuthenticationError,
    ValidationError,
    NotFoundError,
)

# Database exports
from quantgrid.db.session import get_session, get_timescale_session

# Service exports
from quantgrid.services.quote_service import quote_service
from quantgrid.services.quant_service import quant_service
from quantgrid.services.redis_service import get_cache, set_cache

__all__ = [
    # Version
    "__version__",
    "__author__",
    # Core
    "settings",
    "QuantGridException",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    # Database
    "get_session",
    "get_timescale_session",
    # Services
    "quote_service",
    "quant_service",
    "get_cache",
    "set_cache",
]
