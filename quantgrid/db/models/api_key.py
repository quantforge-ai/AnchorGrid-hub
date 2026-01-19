"""
QuantForge AI Engine - API Key Model

API key storage and management.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quantgrid.db.session import Base

if TYPE_CHECKING:
    from quantgrid.db.models.tenant import Tenant
    from quantgrid.db.models.user import User


class APIKey(Base):
    """
    API Key model.
    
    Stores hashed API keys for programmatic access.
    Keys are hashed with SHA256 - only the first 8 chars are stored for display.
    """
    __tablename__ = "api_keys"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Foreign keys
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Key info
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    key_hash: Mapped[str] = mapped_column(
        String(64),  # SHA256 hex = 64 chars
        unique=True,
        nullable=False,
        index=True,
    )
    key_prefix: Mapped[str] = mapped_column(
        String(12),  # "qf_xxxx" for display
        nullable=False,
    )
    
    # Permissions
    permissions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # JSON array of permissions
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Usage tracking
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    usage_count: Mapped[int] = mapped_column(default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="api_keys",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="api_keys",
    )
    
    def __repr__(self) -> str:
        return f"<APIKey {self.key_prefix}... ({self.name})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if key is expired"""
        if self.expires_at is None:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at
    
    @property
    def is_revoked(self) -> bool:
        """Check if key is revoked"""
        return self.revoked_at is not None
    
    @property
    def is_valid(self) -> bool:
        """Check if key can be used"""
        return self.is_active and not self.is_expired and not self.is_revoked
    
    @property
    def permission_list(self) -> list[str]:
        """Parse permissions JSON to list"""
        import json
        if not self.permissions:
            return ["read"]
        try:
            return json.loads(self.permissions)
        except json.JSONDecodeError:
            return ["read"]
