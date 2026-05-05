"""
Pydantic schemas for RAG sources
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.db.models.rag_source import SourceType, SyncStatus


class RAGSourceBase(BaseModel):
    """Base RAG source schema"""

    collection_name: str
    display_name: str
    auto_sync: bool = False
    sync_interval_hours: int = 24


class GitHubSourceCreate(RAGSourceBase):
    """Create GitHub source"""

    repo_url: str = Field(..., description="GitHub repository URL")
    branch: Optional[str] = None
    file_extensions: Optional[List[str]] = None


class GoogleDriveSourceCreate(RAGSourceBase):
    """Create Google Drive source"""

    folder_url: str = Field(..., description="Google Drive folder URL or ID")
    recursive: bool = True
    file_extensions: Optional[List[str]] = None


class RAGSourceResponse(BaseModel):
    """RAG source response"""

    id: int
    user_id: int
    collection_name: str
    source_type: SourceType
    source_identifier: str
    display_name: str
    auto_sync: bool
    sync_interval_hours: int
    last_sync_at: Optional[datetime]
    last_sync_status: SyncStatus
    last_sync_error: Optional[str]
    total_files: int
    total_chunks: int
    last_commit_sha: Optional[str]
    config: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SyncResult(BaseModel):
    """Sync operation result"""

    source_id: int
    status: str
    files_processed: Optional[int] = None
    chunks_created: Optional[int] = None
    commit_sha: Optional[str] = None
    error: Optional[str] = None


class RAGSourceUpdate(BaseModel):
    """Update RAG source"""

    display_name: Optional[str] = None
    auto_sync: Optional[bool] = None
    sync_interval_hours: Optional[int] = None
