"""
QuantTerminal Database Models - User
Authentication and user management
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from quantgrid.db.session import Base


class User(Base):
    """User model for authentication and profiles"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    activity_events = relationship(
        "UserActivityEvent",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    interests = relationship(
        "UserInterest",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    library_versions = relationship(
        "LibraryVersion",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    portfolio = relationship(
        "Portfolio",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    # Security relationships
    ip_history = relationship(
        "UserIPHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    devices = relationship(
        "UserDevice",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    login_pattern = relationship(
        "UserLoginPattern",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    api_activity = relationship(
        "UserAPIActivity",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User {self.username}>"
