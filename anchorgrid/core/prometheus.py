"""
QuantForge AI Engine - Prometheus Metrics

Exposes /metrics endpoint for Prometheus scraping.
Tracks request latency, error rates, and business metrics.
"""
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response

from anchorgrid.core.config import settings


router = APIRouter()


# =============================================================================
# Application Info
# =============================================================================

APP_INFO = Info(
    "quantforge",
    "QuantForge AI Engine information",
)
APP_INFO.info({
    "version": settings.APP_VERSION,
    "environment": settings.ENVIRONMENT,
})


# =============================================================================
# Request Metrics
# =============================================================================

REQUEST_COUNT = Counter(
    "quantforge_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "quantforge_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

REQUEST_IN_PROGRESS = Gauge(
    "quantforge_requests_in_progress",
    "Number of requests currently being processed",
    ["method"],
)


# =============================================================================
# Auth Metrics
# =============================================================================

AUTH_ATTEMPTS = Counter(
    "quantforge_auth_attempts_total",
    "Authentication attempts",
    ["method", "status"],  # method: jwt/api_key, status: success/failure
)

TOKEN_GENERATIONS = Counter(
    "quantforge_token_generations_total",
    "JWT tokens generated",
    ["type"],  # access/refresh
)


# =============================================================================
# Business Metrics
# =============================================================================

AI_ANALYSIS_COUNT = Counter(
    "quantforge_ai_analysis_total",
    "AI analysis requests",
    ["status", "plan"],
)

AI_ANALYSIS_LATENCY = Histogram(
    "quantforge_ai_analysis_duration_seconds",
    "AI analysis latency",
    ["plan"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

VECTOR_OPERATIONS = Counter(
    "quantforge_vector_ops_total",
    "Vector store operations",
    ["operation"],  # ingest/search/delete
)

LLM_REQUESTS = Counter(
    "quantforge_llm_requests_total",
    "LLM inference requests",
    ["provider", "status"],  # provider: ollama/openai/anthropic
)

LLM_LATENCY = Histogram(
    "quantforge_llm_duration_seconds",
    "LLM inference latency",
    ["provider"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

EMBEDDING_REQUESTS = Counter(
    "quantforge_embedding_requests_total",
    "Embedding requests",
    ["provider", "status"],  # provider: ollama/huggingface
)


# =============================================================================
# System Metrics
# =============================================================================

ACTIVE_CONNECTIONS = Gauge(
    "quantforge_active_connections",
    "Active database connections",
    ["database"],  # postgres/timescale/redis/weaviate
)

CACHE_OPERATIONS = Counter(
    "quantforge_cache_ops_total",
    "Cache operations",
    ["operation", "status"],  # operation: get/set, status: hit/miss
)


# =============================================================================
# Rate Limiting Metrics
# =============================================================================

RATE_LIMIT_HITS = Counter(
    "quantforge_rate_limit_hits_total",
    "Rate limit violations",
    ["plan", "endpoint"],
)


# =============================================================================
# Metrics Endpoint
# =============================================================================

@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format.
    Should be scraped by Prometheus at regular intervals.
    
    Note: This endpoint bypasses authentication — 
    protect it via network policy in production.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# =============================================================================
# Helper Functions
# =============================================================================

def track_request(method: str, endpoint: str, status: int, duration: float):
    """Track request metrics"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)


def track_auth(method: str, success: bool):
    """Track authentication attempt"""
    status = "success" if success else "failure"
    AUTH_ATTEMPTS.labels(method=method, status=status).inc()


def track_ai_analysis(success: bool, plan: str, duration: float):
    """Track AI analysis request"""
    status = "success" if success else "failure"
    AI_ANALYSIS_COUNT.labels(status=status, plan=plan).inc()
    AI_ANALYSIS_LATENCY.labels(plan=plan).observe(duration)


def track_llm_request(provider: str, success: bool, duration: float):
    """Track LLM inference request"""
    status = "success" if success else "failure"
    LLM_REQUESTS.labels(provider=provider, status=status).inc()
    LLM_LATENCY.labels(provider=provider).observe(duration)


def track_embedding_request(provider: str, success: bool):
    """Track embedding request"""
    status = "success" if success else "failure"
    EMBEDDING_REQUESTS.labels(provider=provider, status=status).inc()


def track_vector_operation(operation: str):
    """Track vector store operation"""
    VECTOR_OPERATIONS.labels(operation=operation).inc()


def track_rate_limit(plan: str, endpoint: str):
    """Track rate limit violation"""
    RATE_LIMIT_HITS.labels(plan=plan, endpoint=endpoint).inc()
