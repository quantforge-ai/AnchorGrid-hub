"""
Health Check Routes
System status and dependency verification
"""

from fastapi import APIRouter
from anchorgrid.core import settings
from anchorgrid.db import check_db_connection

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check
    Returns application status
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV
    }


@router.get("/readiness")
async def readiness_check():
    """
    Readiness check
    Verifies all dependencies are available
    """
    # Check database
    db_ok = await check_db_connection()
    
    # Check Redis (if configured)
    redis_ok = True  # TODO: Implement Redis check when added
    
    is_ready = db_ok and redis_ok
    
    return {
        "ready": is_ready,
        "checks": {
            "database": "ok" if db_ok else "down",
            "redis": "ok" if redis_ok else "not_configured"
        }
    }
