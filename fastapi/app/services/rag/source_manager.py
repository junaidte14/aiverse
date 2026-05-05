"""
RAG Source Manager - Unified interface for all source types
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta

from app.db.models.rag_source import RAGSource, SourceType, SyncStatus
from app.db.models.user import User
from app.services.rag.vector_store import VectorStoreService
from app.services.rag.github_integration import GitHubRAGIntegration


class RAGSourceManager:
    """
    Manage RAG sources and synchronization
    """

    def __init__(self, db: AsyncSession, user: User):
        """
        Initialize source manager

        Args:
            db: Database session
            user: Current user
        """
        self.db = db
        self.user = user
        self.vector_store = VectorStoreService()
        self.github = GitHubRAGIntegration()

    async def add_github_source(
        self,
        repo_url: str,
        collection_name: str,
        display_name: Optional[str] = None,
        branch: Optional[str] = None,
        file_extensions: Optional[List[str]] = None,
        auto_sync: bool = False,
        sync_interval_hours: int = 24,
    ) -> RAGSource:
        """
        Add GitHub repository as RAG source

        Args:
            repo_url: GitHub repository URL
            collection_name: Collection to ingest into
            display_name: Display name for source
            branch: Branch to use (None = default)
            file_extensions: File types to include
            auto_sync: Enable automatic syncing
            sync_interval_hours: Sync frequency

        Returns:
            Created RAGSource
        """
        # Validate repository
        repo_info = self.github.get_repo_info(repo_url)

        # Create source record
        source = RAGSource(
            user_id=self.user.id,
            collection_name=collection_name,
            source_type=SourceType.GITHUB,
            source_identifier=repo_url,
            display_name=display_name or repo_info["full_name"],
            auto_sync=auto_sync,
            sync_interval_hours=sync_interval_hours,
            last_commit_sha=repo_info["last_commit_sha"],
            config={
                "branch": branch or repo_info["default_branch"],
                "file_extensions": file_extensions,
                "repo_info": repo_info,
            },
        )

        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)

        # Trigger initial sync
        await self.sync_source(source.id)

        return source

    async def sync_source(self, source_id: int) -> Dict[str, Any]:
        """
        Synchronize a source (GitHub or Google Drive)

        Args:
            source_id: Source ID to sync

        Returns:
            Sync results
        """
        # Get source
        result = await self.db.execute(
            select(RAGSource).where(RAGSource.id == source_id)
        )
        source = result.scalar_one_or_none()

        if not source:
            raise ValueError(f"Source {source_id} not found")

        # Update status
        source.last_sync_status = SyncStatus.IN_PROGRESS
        await self.db.commit()

        try:
            if source.source_type == SourceType.GITHUB:
                results = await self._sync_github(source)
            elif source.source_type == SourceType.GOOGLE_DRIVE:
                results = await self._sync_google_drive(source)
            else:
                raise ValueError(f"Unsupported source type: {source.source_type}")

            # Update source
            source.last_sync_status = SyncStatus.COMPLETED
            source.last_sync_at = datetime.utcnow()
            source.last_sync_error = None
            source.total_files = results["files_processed"]
            source.total_chunks = results["chunks_created"]

            if "commit_sha" in results:
                source.last_commit_sha = results["commit_sha"]

            await self.db.commit()

            return results

        except Exception as e:
            # Update error status
            source.last_sync_status = SyncStatus.FAILED
            source.last_sync_error = str(e)
            await self.db.commit()
            raise

    async def _sync_github(self, source: RAGSource) -> Dict[str, Any]:
        """Sync GitHub repository"""
        config = source.config or {}

        # Process repository
        repo_path, documents = self.github.process_repository(
            repo_url=source.source_identifier,
            branch=config.get("branch"),
            file_extensions=config.get("file_extensions"),
            metadata={"source_id": source.id, "collection": source.collection_name},
        )

        # Ingest into vector store
        if documents:
            self.vector_store.add_documents(
                collection_name=source.collection_name,
                documents=[doc["text"] for doc in documents],
                metadatas=[doc["metadata"] for doc in documents],
                ids=[doc["id"] for doc in documents],
            )

        # Get latest commit
        commit_sha = self.github.get_last_commit_sha(repo_path)

        return {
            "files_processed": len(set(doc["metadata"]["source"] for doc in documents)),
            "chunks_created": len(documents),
            "commit_sha": commit_sha,
        }

    async def list_sources(
        self, collection_name: Optional[str] = None
    ) -> List[RAGSource]:
        """List all sources for user"""
        query = select(RAGSource).where(RAGSource.user_id == self.user.id)

        if collection_name:
            query = query.where(RAGSource.collection_name == collection_name)

        query = query.order_by(RAGSource.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_source(self, source_id: int) -> None:
        """Delete a source"""
        result = await self.db.execute(
            select(RAGSource).where(
                RAGSource.id == source_id, RAGSource.user_id == self.user.id
            )
        )
        source = result.scalar_one_or_none()

        if not source:
            raise ValueError(f"Source {source_id} not found")

        # Delete from database
        await self.db.delete(source)
        await self.db.commit()

        # Cleanup (optional - keep data in vector store)
        # If you want to delete the data too, implement collection filtering by source_id

    async def check_and_sync_due_sources(self) -> List[Dict[str, Any]]:
        """
        Check for sources that need syncing and sync them
        Called by background task

        Returns:
            List of sync results
        """
        # Find sources that need syncing
        cutoff_time = datetime.utcnow()

        result = await self.db.execute(
            select(RAGSource).where(
                RAGSource.auto_sync == True,
                RAGSource.last_sync_at
                < cutoff_time - timedelta(hours=RAGSource.sync_interval_hours),
            )
        )
        sources = result.scalars().all()

        sync_results = []

        for source in sources:
            try:
                result = await self.sync_source(source.id)
                sync_results.append(
                    {"source_id": source.id, "status": "success", "result": result}
                )
            except Exception as e:
                sync_results.append(
                    {"source_id": source.id, "status": "failed", "error": str(e)}
                )

        return sync_results
