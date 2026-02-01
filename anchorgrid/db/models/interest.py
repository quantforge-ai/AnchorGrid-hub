# backend/db/models/interest.py
"""
Interest Library Database Models - "Shadow Watch"
Tracks user activity and builds personalized interest graph
Part of Shadow Watch behavioral biometric system

Technical layer: Keeps generic "interest" naming for subtlety
Service layer: branded as "Shadow Watch" in shadow_watch.py
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Boolean,
    UniqueConstraint,
    Index
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from anchorgrid.db.session import Base


class UserActivityEvent(Base):
    """
    Raw activity event log (audit trail)
    Every user interaction creates an event
    Retained for 90 days per GDPR policy
    """
    __tablename__ = "user_activity_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Asset info
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(20), default="stock")  # stock, crypto, etf, option
    
    # Action type
    action_type = Column(String(30), nullable=False)  # view, trade, search, alert, watchlist_add
    
    # Additional context (flexible JSON) - renamed from 'metadata' (SQLAlchemy reserved word)
    event_metadata = Column(JSON, default=dict)  # e.g., {"duration": 45, "source": "quote_page", "price": 182.31}
    
    # Timestamp
    occurred_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Relationship
    user = relationship("User", back_populates="activity_events")
    
    # Composite index for common queries
    __table_args__ = (
        Index('ix_user_symbol_date', 'user_id', 'symbol', 'occurred_at'),
        Index('ix_user_action_date', 'user_id', 'action_type', 'occurred_at'),
    )
    
    def __repr__(self):
        return f"<ActivityEvent user={self.user_id} {self.action_type} {self.symbol}>"


class UserInterest(Base):
    """
    Aggregated user interest scores (canonical library)
    One row per user+symbol combination
    Scored 0.0-1.0 based on activity patterns
    """
    __tablename__ = "user_interests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Asset info
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(20), default="stock")
    
    # Interest scoring
    score = Column(Float, default=0.0, nullable=False)  # 0.0 - 1.0
    activity_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    first_seen = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    last_interaction = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    # Pinning (investment-based or manual)
    is_pinned = Column(Boolean, default=False, nullable=False)
    portfolio_value = Column(Float, nullable=True)  # $$ invested (if any)
    
    # Relationship
    user = relationship("User", back_populates="interests")
    
    # Unique constraint: one row per user+symbol
    __table_args__ = (
        UniqueConstraint('user_id', 'symbol', name='uq_user_symbol'),
        Index('ix_user_score', 'user_id', 'score'),  # For top-N queries
        Index('ix_user_pinned', 'user_id', 'is_pinned'),  # For pinned items
    )
    
    def __repr__(self):
        pin_status = "📌" if self.is_pinned else ""
        return f"<Interest {pin_status}{self.symbol} score={self.score:.2f} user={self.user_id}>"


class LibraryVersion(Base):
    """
    Snapshot of user's interest library at a point in time
    Used for fingerprinting and recovery
    """
    __tablename__ = "library_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Version tracking
    version = Column(Integer, nullable=False)  # Increments on changes
    fingerprint_hash = Column(String(64), nullable=False)  # SHA256 of top interests
    
    # Metadata
    generated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    item_count = Column(Integer, default=0)
    total_score = Column(Float, default=0.0)
    
    # Snapshot (top 50 items as JSON)
    snapshot = Column(JSON, default=list)  # [{symbol, score, is_pinned}, ...]
    
    # Relationship
    user = relationship("User", back_populates="library_versions")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'version', name='uq_user_version'),
        Index('ix_user_generated', 'user_id', 'generated_at'),
    )
    
    def __repr__(self):
        return f"<LibraryVersion user={self.user_id} v{self.version} items={self.item_count}>"
