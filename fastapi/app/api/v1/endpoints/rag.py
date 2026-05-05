"""
RAG API endpoints
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import os
import shutil
from pathlib import Path

from app.core.auth_dependencies import get_current_active_user, get_db
from app.db.models.user import User
from app.services.rag.rag_service import RAGService
from app.services.conversation_service import ConversationService

from app.services.rag.source_manager import RAGSourceManager
from app.schemas.rag_source import (
    GitHubSourceCreate,
    RAGSourceResponse,
    SyncResult,
    RAGSourceUpdate,
)

router = APIRouter(prefix="/rag", tags=["rag"])

# ==================== SCHEMAS ====================


class RAGQueryRequest(BaseModel):
    """RAG query request"""

    question: str
    collection_name: str = "default"
    conversation_id: int | None = None
    provider: str = "groq"
    model: str = "llama-3.3-70b-versatile"
    n_context_docs: int = 5
    include_sources: bool = True
    temperature: float = 0.7
    max_tokens: int = 1000


class RAGQueryResponse(BaseModel):
    """RAG query response"""

    answer: str
    context_used: bool
    conversation_id: Optional[int] = None
    sources: Optional[List[dict]] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None


class IngestDirectoryRequest(BaseModel):
    """Ingest directory request"""

    directory_path: str
    collection_name: str = "default"
    file_extensions: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    metadata: Optional[dict] = None


class CollectionStats(BaseModel):
    """Collection statistics"""

    collection_name: str
    document_count: int
    status: str


# ==================== ENDPOINTS ====================


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):

    rag_service = RAGService(
        db=db, user=current_user, collection_name=request.collection_name
    )
    conv_service = ConversationService(db)

    # 1. CONVERSATION SETUP (Same as multi-provider chat)
    if not request.conversation_id:
        conv = await conv_service.create_conversation(
            user_id=current_user.id,
            title=request.question[:50],  # Use question as title
            model_name=f"RAG: {request.model}",  # Mark it as a RAG conversation
        )
        conversation_id = conv.id
    else:
        conversation_id = request.conversation_id

    # 2. SAVE USER MESSAGE
    await conv_service.add_message(
        conversation_id=conversation_id,
        role="user",
        content=request.question,
    )

    # 3. EXECUTE RAG QUERY
    result = await rag_service.query(
        question=request.question,
        provider=request.provider,
        model=request.model,
        n_context_docs=request.n_context_docs,
        include_sources=request.include_sources,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )

    # 4. SAVE ASSISTANT RESPONSE
    # Note: We save the answer. You might also want to serialize 'sources'
    # into the metadata field if your add_message supports it.
    await conv_service.add_message(
        conversation_id=conversation_id,
        role="assistant",
        content=result["answer"],
        metadata={"sources": result.get("sources", [])},
    )

    # Ensure the conversation ID is returned to the frontend
    result["conversation_id"] = conversation_id

    return result


@router.post("/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    collection_name: str = "default",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Upload and ingest a single file into the vector store
    """
    # Save uploaded file temporarily
    upload_dir = Path("./data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Ingest file
        rag_service = RAGService(
            db=db, user=current_user, collection_name=collection_name
        )

        chunks_created = await rag_service.ingest_file(str(file_path))

        return {
            "message": "File ingested successfully",
            "filename": file.filename,
            "collection_name": collection_name,
            "chunks_created": chunks_created,
        }

    finally:
        # Clean up uploaded file
        if file_path.exists():
            os.remove(file_path)


@router.post("/ingest/directory")
async def ingest_directory(
    request: IngestDirectoryRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Ingest entire directory into vector store

    This can be a long-running operation, so it runs in the background.
    """
    if not os.path.exists(request.directory_path):
        raise HTTPException(status_code=404, detail="Directory not found")

    async def ingest_task():
        rag_service = RAGService(
            db=db, user=current_user, collection_name=request.collection_name
        )

        await rag_service.ingest_directory(
            directory=request.directory_path,
            file_extensions=request.file_extensions,
            exclude_patterns=request.exclude_patterns,
            metadata=request.metadata,
        )

    background_tasks.add_task(ingest_task)

    return {
        "message": "Directory ingestion started in background",
        "directory": request.directory_path,
        "collection_name": request.collection_name,
    }


@router.get("/collections", response_model=List[str])
async def list_collections(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all available RAG collections"""
    rag_service = RAGService(db=db, user=current_user)
    return rag_service.list_all_collections()


@router.get("/collections/{collection_name}/stats", response_model=CollectionStats)
async def get_collection_stats(
    collection_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get statistics about a collection"""
    rag_service = RAGService(db=db, user=current_user, collection_name=collection_name)

    return rag_service.get_collection_stats()


@router.delete("/collections/{collection_name}")
async def delete_collection(
    collection_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a collection and all its documents"""
    rag_service = RAGService(db=db, user=current_user, collection_name=collection_name)

    rag_service.delete_collection()

    return {"message": f"Collection '{collection_name}' deleted successfully"}


@router.post("/search")
async def search_documents(
    query: str,
    collection_name: str = "default",
    n_results: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Search for relevant documents without generating an answer

    Useful for debugging or seeing what context would be retrieved
    """
    rag_service = RAGService(db=db, user=current_user, collection_name=collection_name)

    results = rag_service.search_documents(query, n_results)

    return {"query": query, "results": results, "count": len(results)}


@router.post("/sources/github", response_model=RAGSourceResponse)
async def add_github_source(
    source_data: GitHubSourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Add GitHub repository as RAG source

    The repository will be cloned and processed automatically.
    If auto_sync is enabled, it will be re-synced periodically.
    """
    manager = RAGSourceManager(db, current_user)

    try:
        source = await manager.add_github_source(
            repo_url=source_data.repo_url,
            collection_name=source_data.collection_name,
            display_name=source_data.display_name,
            branch=source_data.branch,
            file_extensions=source_data.file_extensions,
            auto_sync=source_data.auto_sync,
            sync_interval_hours=source_data.sync_interval_hours,
        )
        return source
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sources", response_model=List[RAGSourceResponse])
async def list_sources(
    collection_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all RAG sources for the current user

    Optionally filter by collection name
    """
    manager = RAGSourceManager(db, current_user)
    sources = await manager.list_sources(collection_name)
    return sources


@router.get("/sources/{source_id}", response_model=RAGSourceResponse)
async def get_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get details of a specific source"""
    from sqlalchemy.future import select
    from app.db.models.rag_source import RAGSource

    result = await db.execute(
        select(RAGSource).where(
            RAGSource.id == source_id, RAGSource.user_id == current_user.id
        )
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return source


@router.put("/sources/{source_id}", response_model=RAGSourceResponse)
async def update_source(
    source_id: int,
    update_data: RAGSourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update source configuration"""
    from sqlalchemy.future import select
    from app.db.models.rag_source import RAGSource

    result = await db.execute(
        select(RAGSource).where(
            RAGSource.id == source_id, RAGSource.user_id == current_user.id
        )
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)

    return source


@router.post("/sources/{source_id}/sync", response_model=SyncResult)
async def sync_source(
    source_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Manually trigger sync for a source

    This will update the source with latest content from GitHub/Google Drive
    """
    manager = RAGSourceManager(db, current_user)

    try:
        result = await manager.sync_source(source_id)
        return SyncResult(
            source_id=source_id,
            status="success",
            files_processed=result.get("files_processed"),
            chunks_created=result.get("chunks_created"),
            commit_sha=result.get("commit_sha"),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/sources/{source_id}")
async def delete_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a RAG source"""
    manager = RAGSourceManager(db, current_user)

    try:
        await manager.delete_source(source_id)
        return {"message": "Source deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
