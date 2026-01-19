"""
QuantForge AI Engine - Auth Service

Business logic for authentication, users, and API keys.
Wires the security utilities with database models.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from quantgrid.db.models import User, Tenant, APIKey
from quantgrid.core.security import (
    hash_password,
    verify_password,
    generate_api_key,
    hash_api_key,
    create_access_token,
    create_refresh_token,
)
from quantgrid.core.exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
)


class AuthService:
    """
    Authentication service.
    
    Handles user authentication, registration, and API key management.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # =========================================================================
    # User Authentication
    # =========================================================================
    
    async def authenticate_user(self, email: str, password: str) -> tuple[User, str, str]:
        """
        Authenticate user with email and password.
        
        Returns:
            Tuple of (user, access_token, refresh_token)
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Find user by email
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            raise AuthenticationError(message="Invalid email or password")
        
        if not user.is_active:
            raise AuthenticationError(message="Account is disabled")
        
        if not verify_password(password, user.password_hash):
            raise AuthenticationError(message="Invalid email or password")
        
        # Update login tracking
        user.last_login_at = datetime.now(timezone.utc)
        user.login_count += 1
        await self.session.flush()
        
        # Generate tokens
        access_token = create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            plan=await self._get_user_plan(user),
            permissions=user.permission_list,
        )
        refresh_token = create_refresh_token(user_id=user.id)
        
        return user, access_token, refresh_token
    
    async def _get_user_plan(self, user: User) -> str:
        """Get user's tenant plan"""
        result = await self.session.execute(
            select(Tenant.plan).where(Tenant.id == user.tenant_id)
        )
        plan = result.scalar_one_or_none()
        return plan or "free"
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    # =========================================================================
    # User Registration
    # =========================================================================
    
    async def register_user(
        self,
        email: str,
        password: str,
        name: str,
        organization_name: Optional[str] = None,
    ) -> tuple[User, Tenant]:
        """
        Register a new user.
        
        If organization_name is provided, creates a new tenant.
        Otherwise, creates user without tenant (pending invitation).
        
        Returns:
            Tuple of (user, tenant)
            
        Raises:
            ValidationError: If email already exists
        """
        # Check if email exists
        existing = await self.get_user_by_email(email)
        if existing:
            raise ValidationError(message="Email already registered")
        
        # Create tenant if organization provided
        tenant = None
        if organization_name:
            tenant = Tenant(
                name=organization_name,
                slug=organization_name.lower().replace(" ", "-"),
                plan="free",
            )
            self.session.add(tenant)
            await self.session.flush()
        
        if tenant is None:
            raise ValidationError(message="Organization name required")
        
        # Create user
        user = User(
            tenant_id=tenant.id,
            email=email,
            password_hash=hash_password(password),
            name=name,
            role="owner",  # First user is owner
            permissions=json.dumps(["read", "write", "admin"]),
        )
        self.session.add(user)
        await self.session.flush()
        
        return user, tenant
    
    # =========================================================================
    # API Key Management
    # =========================================================================
    
    async def create_api_key(
        self,
        user_id: UUID,
        tenant_id: UUID,
        name: str,
        permissions: list[str],
        expires_in_days: Optional[int] = None,
    ) -> tuple[APIKey, str]:
        """
        Create a new API key.
        
        Returns:
            Tuple of (api_key_model, raw_key)
            The raw_key is only returned once - cannot be retrieved later.
        """
        # Generate key
        raw_key, hashed_key = generate_api_key()
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            from datetime import timedelta
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        
        # Create model
        api_key = APIKey(
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            key_hash=hashed_key,
            key_prefix=raw_key[:12],  # "qf_xxxx" for display
            permissions=json.dumps(permissions),
            expires_at=expires_at,
        )
        self.session.add(api_key)
        await self.session.flush()
        
        return api_key, raw_key
    
    async def get_api_key_by_hash(self, key_hash: str) -> Optional[APIKey]:
        """Get API key by hash (for authentication)"""
        result = await self.session.execute(
            select(APIKey).where(APIKey.key_hash == key_hash)
        )
        return result.scalar_one_or_none()
    
    async def list_user_api_keys(self, user_id: UUID) -> list[APIKey]:
        """List all API keys for a user"""
        result = await self.session.execute(
            select(APIKey)
            .where(APIKey.user_id == user_id)
            .where(APIKey.revoked_at.is_(None))
            .order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def revoke_api_key(self, key_id: UUID, user_id: UUID) -> bool:
        """
        Revoke an API key.
        
        Returns:
            True if revoked, False if not found
        """
        result = await self.session.execute(
            select(APIKey)
            .where(APIKey.id == key_id)
            .where(APIKey.user_id == user_id)
        )
        api_key = result.scalar_one_or_none()
        
        if api_key is None:
            return False
        
        api_key.revoked_at = datetime.now(timezone.utc)
        api_key.is_active = False
        await self.session.flush()
        
        return True
    
    async def record_api_key_usage(self, api_key: APIKey) -> None:
        """Record API key usage"""
        api_key.last_used_at = datetime.now(timezone.utc)
        api_key.usage_count += 1
        await self.session.flush()
