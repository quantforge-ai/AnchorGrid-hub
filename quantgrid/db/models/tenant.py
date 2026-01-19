"""
QuantForge AI Engine - Tenant Model

Multi-tenancy support with organization/tenant structure.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quantgrid.db.session import Base

if TYPE_CHECKING:
    from quantgrid.db.models.user import User
    from quantgrid.db.models.api_key import APIKey


class Tenant(Base):
    """
    Tenant/Organization model.
    
    Each tenant has isolated data and can have multiple users.
    Supports different subscription plans with rate limits.
    """
    __tablename__ = "tenants"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    
    # Tenant info
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    
    # Subscription
    plan: Mapped[str] = mapped_column(
        String(50),
        default="free",
        nullable=False,
    )  # free, pro, enterprise
    
    # Limits (based on plan)
    max_users: Mapped[int] = mapped_column(default=5)
    max_api_keys: Mapped[int] = mapped_column(default=3)
    max_requests_per_day: Mapped[int] = mapped_column(default=1000)
    max_vector_docs: Mapped[int] = mapped_column(default=10000)
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    # Metadata
    settings: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # JSON string for tenant-specific settings
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        return f"<Tenant {self.slug} ({self.plan})>"
