"""
QuantForge AI Engine - Security Utilities

JWT tokens, API key hashing, password hashing, and security helpers.
All functions are stateless — database operations happen in services.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID
import hashlib
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext

from quantgrid.core.config import settings


# =============================================================================
# Password Hashing
# =============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored hash to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# API Key Generation & Hashing
# =============================================================================

API_KEY_PREFIX = "qf_"
API_KEY_LENGTH = 32


def generate_api_key() -> tuple[str, str]:
    """
    Generate a new API key.
    
    Returns:
        Tuple of (raw_key, hashed_key)
        - raw_key: Show to user ONCE, never store
        - hashed_key: Store in database for lookup
        
    Example:
        raw_key = "qf_abc123..."
        hashed_key = "sha256:..."
    """
    # Generate cryptographically secure random key
    random_part = secrets.token_urlsafe(API_KEY_LENGTH)
    raw_key = f"{API_KEY_PREFIX}{random_part}"
    
    # Hash for secure storage
    hashed_key = hash_api_key(raw_key)
    
    return raw_key, hashed_key


def hash_api_key(raw_key: str) -> str:
    """
    Hash an API key for storage/lookup.
    
    Args:
        raw_key: The raw API key (e.g., qf_abc123...)
        
    Returns:
        SHA256 hash of the key
    """
    return hashlib.sha256(raw_key.encode()).hexdigest()


def validate_api_key_format(key: str) -> bool:
    """
    Check if an API key has valid format.
    
    Args:
        key: API key to validate
        
    Returns:
        True if format is valid
    """
    return key.startswith(API_KEY_PREFIX) and len(key) > len(API_KEY_PREFIX) + 10


# =============================================================================
# JWT Token Management
# =============================================================================

class TokenPayload:
    """Decoded JWT token payload"""
    
    def __init__(
        self,
        user_id: UUID,
        tenant_id: UUID,
        email: str,
        plan: str,
        permissions: list[str],
        exp: datetime,
        iat: datetime,
    ):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.email = email
        self.plan = plan
        self.permissions = permissions
        self.exp = exp
        self.iat = iat
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.now(timezone.utc) > self.exp


def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    email: str,
    plan: str = "free",
    permissions: list[str] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User's UUID
        tenant_id: Tenant/Organization UUID
        email: User's email
        plan: Subscription plan (free, pro, enterprise)
        permissions: List of permission strings
        expires_delta: Custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    if permissions is None:
        permissions = ["read"]
        
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "email": email,
        "plan": plan,
        "permissions": permissions,
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[TokenPayload]:
    """
    Decode and validate a JWT access token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenPayload if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        
        return TokenPayload(
            user_id=UUID(payload["sub"]),
            tenant_id=UUID(payload["tenant_id"]),
            email=payload.get("email", ""),
            plan=payload.get("plan", "free"),
            permissions=payload.get("permissions", ["read"]),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
        )
    except (JWTError, KeyError, ValueError):
        return None


def create_refresh_token(
    user_id: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a refresh token (longer-lived, limited claims).
    
    Args:
        user_id: User's UUID
        expires_delta: Custom expiration (default: 7 days)
        
    Returns:
        Encoded JWT refresh token
    """
    if expires_delta is None:
        expires_delta = timedelta(days=7)
    
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "refresh",
    }
    
    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_refresh_token(token: str) -> Optional[UUID]:
    """
    Decode a refresh token.
    
    Args:
        token: JWT refresh token
        
    Returns:
        User UUID if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        
        if payload.get("type") != "refresh":
            return None
            
        return UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None


# =============================================================================
# Security Headers
# =============================================================================

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Cache-Control": "no-store",
}
