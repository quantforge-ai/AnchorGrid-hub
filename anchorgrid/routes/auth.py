"""
Authentication Routes
User registration, login, and token management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from anchorgrid.db import get_db
from anchorgrid.schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    UserWithToken,
    PasswordChange,
    UserUpdate
)
from anchorgrid.services import UserService
from anchorgrid.core.dependencies import get_current_user, create_user_token
from anchorgrid.core import log
from anchorgrid.db.models import User


router = APIRouter()


@router.post("/register", response_model=UserWithToken, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account
    
    - **username**: 3-50 characters, alphanumeric with underscores/hyphens
    - **email**: Valid email address
    - **password**: Minimum 8 characters
    
    Returns user data with access token
    """
    try:
        # Create user
        user = await UserService.create_user(db, user_data)
        
        # Generate token
        token_data = create_user_token(user)
        
        log.info(f"New user registered: {user.username} ({user.email})")
        
        return {
            "user": UserResponse.model_validate(user),
            **token_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=UserWithToken)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password
    
    Returns user data with access token
    """
    # Authenticate user
    user = await UserService.authenticate_user(db, credentials)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate token
    token_data = create_user_token(user)
    
    log.info(f"User logged in: {user.username}")
    
    return {
        "user": UserResponse.model_validate(user),
        **token_data
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile (protected route)
    
    Requires valid JWT token in Authorization header:
    `Authorization: Bearer <token>`
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_profile(
    updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user profile (protected route)
    
    Can update username and/or email
    """
    try:
        updated_user = await UserService.update_user(
            db,
            current_user,
            username=updates.username,
            email=updates.email
        )
        
        log.info(f"User profile updated: {updated_user.username}")
        
        return UserResponse.model_validate(updated_user)
    
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password (protected route)
    
    Requires current password for verification
    """
    try:
        await UserService.change_password(
            db,
            current_user,
            password_data.current_password,
            password_data.new_password
        )
        
        log.info(f"Password changed for user: {current_user.username}")
        
        return {"message": "Password changed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout (protected route)
    
    Note: In stateless JWT auth, logout is typically handled client-side by
    removing the token. This endpoint exists for logging purposes and
    potential future token blacklisting.
    """
    log.info(f"User logged out: {current_user.username}")
    
    return {"message": "Logged out successfully"}
