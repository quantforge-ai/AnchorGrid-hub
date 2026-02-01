"""
QuantForge AI Engine - Sentry Error Tracking

Initialize Sentry for error capture and performance monitoring.
"""
from typing import Optional
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from loguru import logger

from anchorgrid.core.config import settings


def init_sentry() -> bool:
    """
    Initialize Sentry SDK.
    
    Returns:
        True if Sentry was initialized, False if skipped (no DSN)
    """
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured, error tracking disabled")
        return False
    
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        release=f"quantforge@{settings.APP_VERSION}",
        
        # Integrations
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
            LoggingIntegration(level=None, event_level="ERROR"),
            RedisIntegration(),
        ],
        
        # Performance monitoring
        traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
        profiles_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 0.5,
        
        # Data scrubbing
        send_default_pii=False,
        
        # Before send hooks
        before_send=before_send,
        before_send_transaction=before_send_transaction,
    )
    
    logger.info(f"Sentry initialized for environment: {settings.SENTRY_ENVIRONMENT}")
    return True


def before_send(event: dict, hint: dict) -> Optional[dict]:
    """
    Process event before sending to Sentry.
    
    Use this to:
    - Filter out certain errors
    - Scrub sensitive data
    - Add custom context
    """
    # Don't send 4xx client errors
    if "exception" in event:
        for exception in event.get("exception", {}).get("values", []):
            exc_type = exception.get("type", "")
            if exc_type in ["ValidationError", "AuthenticationError", "NotFoundError"]:
                return None
    
    return event


def before_send_transaction(event: dict, hint: dict) -> Optional[dict]:
    """
    Process transaction before sending to Sentry.
    
    Use this to filter out noisy endpoints.
    """
    # Don't trace health checks
    transaction = event.get("transaction", "")
    if transaction in ["/health", "/metrics"]:
        return None
    
    return event


def set_user_context(user_id: str, tenant_id: str, email: str = "", plan: str = ""):
    """
    Set user context for Sentry.
    
    Call this after authentication to associate errors with users.
    """
    sentry_sdk.set_user({
        "id": user_id,
        "email": email,
    })
    sentry_sdk.set_tag("tenant_id", tenant_id)
    sentry_sdk.set_tag("plan", plan)


def clear_user_context():
    """Clear user context (e.g., on logout)"""
    sentry_sdk.set_user(None)


def capture_message(message: str, level: str = "info", extra: dict = None):
    """
    Send a message to Sentry.
    
    Args:
        message: Message text
        level: debug, info, warning, error, fatal
        extra: Additional context
    """
    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_message(message, level=level)


def capture_exception(exception: Exception, extra: dict = None):
    """
    Capture an exception and send to Sentry.
    
    Args:
        exception: The exception to capture
        extra: Additional context
    """
    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_exception(exception)


def add_breadcrumb(
    message: str,
    category: str = "custom",
    level: str = "info",
    data: dict = None,
):
    """
    Add a breadcrumb for debugging.
    
    Breadcrumbs are shown in the event timeline.
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
    )
