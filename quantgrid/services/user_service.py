"""
User Service - Business Logic Layer
Handles all user-related operations
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from quantgrid.db.models import User
from quantgrid.core import hash_password, verify_password, create_access_token
from quantgrid.schemas import UserRegister, UserLogin
from fastapi import HTTPException, status


class UserService:
    """Service class for user operations"""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserRegister) -> User:
        """
        Create a new user account
        
        Args:
            db: Database session
            user_data: User registration data
            
        Returns:
            Created user instance
            
        Raises:
            HTTPException: If username or email already exists
        """
        # Check if username exists
        stmt = select(User).where(User.username == user_data.username)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email exists
        stmt = select(User).where(User.email == user_data.email)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        hashed_password = hash_password(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, user_data: UserLogin) -> User | None:
        """
        Authenticate user with email and password
        
        Args:
            db: Database session
            user_data: Login credentials
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        # Get user by email
        stmt = select(User).where(User.email == user_data.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Verify password
        if not verify_password(user_data.password, user.hashed_password):
            return None
        
        # Check if user is active
        if not user.is_active:
            return None
        
        return user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        """
        Get user by ID
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User instance or None
        """
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
        """
        Get user by email
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            User instance or None
        """
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_user(
        db: AsyncSession, 
        user: User, 
        username: str | None = None,
        email: str | None = None
    ) -> User:
        """
        Update user profile
        
        Args:
            db: Database session
            user: User instance to update
            username: New username (optional)
            email: New email (optional)
            
        Returns:
            Updated user instance
            
        Raises:
            HTTPException: If username/email already exists
        """
        if username and username != user.username:
            # Check if username is available
            stmt = select(User).where(User.username == username)
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            user.username = username
        
        if email and email != user.email:
            # Check if email is available
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            user.email = email
        
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def change_password(
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password
        
        Args:
            db: Database session
            user: User instance
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            True if password changed successfully
            
        Raises:
            HTTPException: If current password is incorrect
        """
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        user.hashed_password = hash_password(new_password)
        await db.commit()
        
        return True
