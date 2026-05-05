"""
RAG Service - Main interface for RAG operations
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rag.vector_store import VectorStoreService
from app.services.rag.document_processor import DocumentProcessor
from app.services.ai.unified_service import UnifiedAIService
from app.db.models.user import User


class RAGService:
    """
    Main RAG service that combines document processing,
    vector storage, and LLM generation
    """

    def __init__(
        self,
        db: AsyncSession,
        user: User,
        collection_name: str = "default",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """
        Initialize RAG service

        Args:
            db: Database session
            user: Current user
            collection_name: Vector store collection name
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.db = db
        self.user = user
        self.collection_name = collection_name

        self.vector_store = VectorStoreService()
        self.doc_processor = DocumentProcessor(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        self.ai_service = UnifiedAIService(db, user)

    async def ingest_file(
        self, file_path: str, metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Ingest a single file into the vector store

        Args:
            file_path: Path to file
            metadata: Additional metadata

        Returns:
            Number of chunks created
        """
        documents = self.doc_processor.process_file(file_path, metadata)

        if documents:
            self.vector_store.add_documents(
                collection_name=self.collection_name,
                documents=[doc["text"] for doc in documents],
                metadatas=[doc["metadata"] for doc in documents],
                ids=[doc["id"] for doc in documents],
            )

        return len(documents)

    async def ingest_directory(
        self,
        directory: str,
        file_extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Ingest entire directory into vector store

        Args:
            directory: Directory path
            file_extensions: File types to include
            exclude_patterns: Patterns to exclude
            metadata: Additional metadata

        Returns:
            Total number of chunks created
        """
        documents = self.doc_processor.process_directory(
            directory=directory,
            file_extensions=file_extensions,
            exclude_patterns=exclude_patterns,
            metadata=metadata,
        )

        if documents:
            self.vector_store.add_documents(
                collection_name=self.collection_name,
                documents=[doc["text"] for doc in documents],
                metadatas=[doc["metadata"] for doc in documents],
                ids=[doc["id"] for doc in documents],
            )

        return len(documents)

    def search_documents(
        self, query: str, n_results: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents

        Args:
            query: Search query
            n_results: Number of results
            filters: Metadata filters

        Returns:
            List of relevant documents with metadata
        """
        results = self.vector_store.search(
            collection_name=self.collection_name,
            query=query,
            n_results=n_results,
            where=filters,
        )

        documents = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                documents.append(
                    {
                        "content": doc,
                        "metadata": (
                            results["metadatas"][0][i] if results["metadatas"] else {}
                        ),
                        "distance": (
                            results["distances"][0][i] if results["distances"] else 0
                        ),
                    }
                )

        return documents

    async def query(
        self,
        question: str,
        provider: str = "groq",
        model: str = "llama-3.3-70b-versatile",
        n_context_docs: int = 5,
        include_sources: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """
        Query the RAG system

        Args:
            question: User question
            provider: AI provider
            model: Model to use
            n_context_docs: Number of context documents to retrieve
            include_sources: Include source references
            temperature: LLM temperature
            max_tokens: Maximum tokens in response

        Returns:
            Dictionary with answer and sources
        """
        # 1. Retrieve relevant documents
        relevant_docs = self.search_documents(question, n_results=n_context_docs)

        if not relevant_docs:
            return {
                "answer": "I couldn't find any relevant information in the knowledge base to answer your question.",
                "sources": [],
                "context_used": False,
            }

        # 2. Build context
        context = self._build_context(relevant_docs)

        # 3. Build prompt with context
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(question, context)

        # 4. Get LLM response
        from app.services.ai.base_provider import ChatMessage

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ]

        response = await self.ai_service.chat(
            provider=provider,
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # 5. Format response
        result = {
            "answer": response.content,
            "context_used": True,
            "tokens_used": response.tokens_used,
            "cost": response.cost,
        }

        if include_sources:
            result["sources"] = self._format_sources(relevant_docs)

        return result

    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context string from documents"""
        context_parts = []

        for i, doc in enumerate(documents, 1):
            source = doc["metadata"].get("source", "Unknown")
            content = doc["content"]

            context_parts.append(f"[Source {i}: {source}]\n{content}\n")

        return "\n".join(context_parts)

    def _build_system_prompt(self) -> str:
        return """You are a technical expert. Format your responses for high scannability:

    1. Use clear H3 headers for different sections.
    2. Use bullet points for lists of features or benefits.
    3. Keep paragraphs short (2-3 sentences) to create a 'line-spaced' effect.
    4. Use **bolding** for technical terms like "theme.json" or "FSE".
    5. ALWAYS cite sources as [N] at the end of the relevant sentence.

    Structure your answer logically: Overview -> Key Technical Details -> Installation/Usage (if needed/asked/required) -> Summary."""

    def _build_user_prompt(self, question: str, context: str) -> str:
        """Build user prompt with question and context"""
        return f"""Context Documents:
{context}

Question: {question}

Please answer the question based on the context provided above. If you reference specific information, cite the source number."""

    def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format sources for response"""
        sources = []

        for i, doc in enumerate(documents, 1):
            metadata = doc["metadata"]
            sources.append(
                {
                    "source_number": i,
                    "filename": metadata.get("filename", "Unknown"),
                    "source": metadata.get("source", "Unknown"),
                    "chunk_index": metadata.get("chunk_index", 0),
                    "distance": round(doc.get("distance", 0), 4),
                }
            )

        return sources

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        count = self.vector_store.get_collection_count(self.collection_name)

        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "status": "active" if count > 0 else "empty",
        }

    def delete_collection(self) -> None:
        """Delete the entire collection"""
        self.vector_store.delete_collection(self.collection_name)

    def list_all_collections(self) -> List[str]:
        """List all available collections"""
        return self.vector_store.list_collections()
