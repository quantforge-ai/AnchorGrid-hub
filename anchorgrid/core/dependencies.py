"""
Authentication Dependencies
JWT middleware and user authentication helpers for protected routes
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
# Import directly from modules to avoid circular import through backend.core
from anchorgrid.core.security import decode_access_token, create_access_token
from anchorgrid.core.config import settings
from anchorgrid.services import UserService
from anchorgrid.db.models import User


# HTTP Bearer token security scheme
security = HTTPBearer()




def _get_db_dependency():
    """Helper to lazily import get_db to avoid circular import"""
    from anchorgrid.db import get_db
    return get_db


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(_get_db_dependency())
) -> User:
    """
    Dependency to get current authenticated user from JWT token
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: User = Depends(get_current_user)):
            return {"user_id": user.id}
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session
        
    Returns:
        Authenticated user instance
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # ⚠️ TEMPORARY DEV BYPASS - REMOVE IN PRODUCTION
    if token == "dev-bypass-token-user-1":
        # Return test user (user_id=1, the one viewing quotes)
        user = await UserService.get_user_by_id(db, user_id=1)
        if user:
            return user
        # Fallback: raise error if user doesn't exist
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Test user not found - register first",
        )
    
    # Decode JWT token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user_id from token payload
    user_id: int | None = payload.get("sub")  # "sub" is standard JWT claim for user ID
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = await UserService.get_user_by_id(db, user_id=int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is active
    (Alias for get_current_user for clarity)
    """
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure user is a superuser (admin)
    
    Usage:
        @app.delete("/admin/users/{user_id}")
        async def delete_user(
            user_id: int,
            admin: User = Depends(get_current_superuser)
        ):
            ...
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Superuser instance
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Superuser access required."
        )
    return current_user


def create_user_token(user: User) -> dict:
    """
    Create JWT token for user
    
    Args:
        user: User instance
        
    Returns:
        Dictionary with access_token, token_type, and expires_in
    """
    token_data = {
        "sub": str(user.id),  # Subject (user ID)
        "email": user.email,
        "username": user.username
    }
    
    access_token = create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # convert to seconds
    }
