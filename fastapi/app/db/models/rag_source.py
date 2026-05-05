"""
RAG Source tracking model
Tracks external sources (GitHub repos, Google Drive folders)
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class SourceType(str, enum.Enum):
    """Source type enumeration"""

    MANUAL = "manual"
    GITHUB = "github"


class SyncStatus(str, enum.Enum):
    """Sync status enumeration"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RAGSource(Base):
    """
    External source for RAG collections
    """

    __tablename__ = "rag_sources"

    id = Column(Integer, primary_key=True, index=True)

    # Ownership
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    collection_name = Column(String(255), nullable=False, index=True)

    # Source info
    source_type = Column(SQLEnum(SourceType), nullable=False)
    source_identifier = Column(String(500), nullable=False)  # URL, folder ID, etc.
    display_name = Column(String(255), nullable=False)

    # Sync configuration
    auto_sync = Column(Boolean, default=False)
    sync_interval_hours = Column(Integer, default=24)  # How often to sync
    last_sync_at = Column(DateTime, nullable=True)
    last_sync_status = Column(SQLEnum(SyncStatus), default=SyncStatus.PENDING)
    last_sync_error = Column(String(1000), nullable=True)

    # Statistics
    total_files = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)
    last_commit_sha = Column(String(255), nullable=True)  # For GitHub

    # Configuration (JSON field for flexibility)
    config = Column(JSON, nullable=True)  # Branch, file filters, etc.

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="rag_sources")
