"""
AnchorGrid AI Engine - API Dependencies
y Injection

Request context resolution happens HERE — once per request.
Business logic NEVER resolves tenants or users directly.

Phase 2: Structure in place
Phase 3: Wire up database lookups
"""
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from loguru import logger

from anchorgrid.core.security import (
    decode_access_token,
    hash_api_key,
    validate_api_key_format,
    TokenPayload,
)
from anchorgrid.core.exceptions import AuthenticationError, AuthorizationError


# =============================================================================
# Request Context
# =============================================================================

@dataclass
class RequestContext:
    """
    Resolved once per request — globally available via Depends().
    
    Contains all auth context needed by business logic.
    Set as PostgreSQL session variables for audit triggers.
    """
    tenant_id: UUID
    user_id: UUID
    email: str
    plan: str  # "free" | "pro" | "enterprise"
    permissions: list[str] = field(default_factory=lambda: ["read"])
    api_key_id: Optional[UUID] = None  # Set if authenticated via API key
    request_id: Optional[str] = None  # From middleware
    
    def has_permission(self, permission: str) -> bool:
        """Check if context has a specific permission"""
        return permission in self.permissions or "admin" in self.permissions
    
    def is_enterprise(self) -> bool:
        """Check if user is on enterprise plan"""
        return self.plan == "enterprise"


# =============================================================================
# Authentication Dependencies
# =============================================================================

async def get_optional_context(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Optional[RequestContext]:
    """
    Get request context if authenticated, None otherwise.
    
    Use for endpoints that work with or without auth.
    """
    try:
        return await get_request_context(request, authorization, x_api_key)
    except HTTPException:
        return None


async def get_request_context(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> RequestContext:
    """
    Single point of tenant/user resolution.
    
    Called by routes via Depends(get_request_context).
    Raises 401 if not authenticated.
    
    Priority:
    1. X-API-Key header
    2. Authorization: Bearer <token>
    """
    # Get request_id from middleware (Phase 1)
    request_id = getattr(request.state, "request_id", None)
    
    if x_api_key:
        ctx = await _resolve_from_api_key(x_api_key)
        ctx.request_id = request_id
        return ctx
    
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        ctx = await _resolve_from_jwt(token)
        ctx.request_id = request_id
        return ctx
    
    raise AuthenticationError(
        message="Authentication required. Provide X-API-Key or Authorization header.",
    )


async def _resolve_from_api_key(api_key: str) -> RequestContext:
    """
    Resolve tenant/user from API key.
    
    Phase 2: Validates format only
    Phase 3: Full database lookup
    """
    if not validate_api_key_format(api_key):
        raise AuthenticationError(message="Invalid API key format")
    
    # Hash the key for lookup
    hashed_key = hash_api_key(api_key)
    
    # TODO Phase 3: Database lookup
    # api_key_record = await api_key_repo.get_by_hash(hashed_key)
    # if not api_key_record or api_key_record.is_revoked:
    #     raise AuthenticationError(message="Invalid or revoked API key")
    
    # For now, raise not implemented
    logger.debug(f"API key lookup pending (hash: {hashed_key[:16]}...)")
    raise AuthenticationError(
        message="API key authentication not yet implemented. Use JWT token.",
    )


async def _resolve_from_jwt(token: str) -> RequestContext:
    """
    Resolve tenant/user from JWT token.
    
    Phase 2: Decodes and validates token
    Phase 3: Additional database validation (user exists, not disabled, etc.)
    """
    payload: Optional[TokenPayload] = decode_access_token(token)
    
    if payload is None:
        raise AuthenticationError(message="Invalid or expired token")
    
    if payload.is_expired:
        raise AuthenticationError(message="Token has expired")
    
    # TODO Phase 3: Verify user still exists and is active
    # user = await user_repo.get_by_id(payload.user_id)
    # if not user or user.disabled:
    #     raise AuthenticationError(message="User not found or disabled")
    
    return RequestContext(
        tenant_id=payload.tenant_id,
        user_id=payload.user_id,
        email=payload.email,
        plan=payload.plan,
        permissions=payload.permissions,
    )


# =============================================================================
# Permission Dependencies
# =============================================================================

def require_permission(permission: str):
    """
    Dependency factory to check specific permission.
    
    Usage:
        @router.get("/admin")
        async def admin_endpoint(ctx = Depends(require_permission("admin"))):
            pass
    """
    async def check_permission(
        ctx: RequestContext = Depends(get_request_context)
    ) -> RequestContext:
        if not ctx.has_permission(permission):
            raise AuthorizationError(
                message=f"Permission '{permission}' required",
            )
        return ctx
    return check_permission


def require_plan(min_plan: str):
    """
    Dependency factory to check subscription plan.
    
    Plan hierarchy: free < pro < enterprise
    
    Usage:
        @router.get("/premium")
        async def premium_endpoint(ctx = Depends(require_plan("pro"))):
            pass
    """
    plan_levels = {"free": 0, "pro": 1, "enterprise": 2}
    
    async def check_plan(
        ctx: RequestContext = Depends(get_request_context)
    ) -> RequestContext:
        user_level = plan_levels.get(ctx.plan, 0)
        required_level = plan_levels.get(min_plan, 0)
        
        if user_level < required_level:
            raise AuthorizationError(
                message=f"This feature requires '{min_plan}' plan or higher",
            )
        return ctx
    return check_plan


# =============================================================================
# Database Session Context (Phase 3)
# =============================================================================

async def set_db_context(ctx: RequestContext) -> None:
    """
    Set PostgreSQL session variables for audit triggers.
    
    Phase 3: Called after getting DB session
    
    Example SQL:
        SET LOCAL app.current_user_id = 'uuid';
        SET LOCAL app.current_tenant_id = 'uuid';
    """
    # TODO Phase 3: Implement with SQLAlchemy session
    # await session.execute(
    #     text("SET LOCAL app.current_user_id = :user_id"),
    #     {"user_id": str(ctx.user_id)}
    # )
    pass
