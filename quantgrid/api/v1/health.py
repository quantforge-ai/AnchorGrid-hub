"""
QuantForge AI Engine - Health Check Routes
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns status of all dependent services.
    """
    # TODO: Check actual service health
    return {
        "status": "healthy",
        "version": "0.1.0",
        "services": {
            "postgres": "ok",
            "timescale": "ok",
            "redis": "ok",
            "weaviate": "ok",
            "minio": "ok",
            "ollama": "ok",
        }
    }


@router.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe"""
    return {"status": "ready"}


@router.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe"""
    return {"status": "alive"}
