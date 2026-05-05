"""
Vector Store Service using ChromaDB
"""

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional, Any
import os
import re
from pathlib import Path


class VectorStoreService:
    """
    Manages vector storage and retrieval using ChromaDB
    """

    def __init__(self, persist_directory: str = "./data/chroma"):
        """
        Initialize ChromaDB client

        Args:
            persist_directory: Where to store the vector database
        """
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False, allow_reset=True, is_persistent=True
            ),
        )

        # Use sentence-transformers for embeddings
        self.embedding_function = (
            embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
        )

    def create_collection(
        self, name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> chromadb.Collection:
        """
        Create or get a collection

        Args:
            name: Collection name
            metadata: Optional metadata for the collection

        Returns:
            ChromaDB collection
        """

        sanitized_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        # Ensure it starts and ends with alphanumeric (Chroma requirement)
        sanitized_name = sanitized_name.strip("_").strip("-")

        # ChromaDB requires non-empty metadata dict
        if metadata is None or len(metadata) == 0:
            metadata = {"created": "true"}

        return self.client.get_or_create_collection(
            name=sanitized_name,
            embedding_function=self.embedding_function,
            metadata=metadata,
        )

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        """
        Add documents to a collection

        Args:
            collection_name: Name of the collection
            documents: List of document texts
            metadatas: List of metadata dicts
            ids: List of unique IDs
        """
        collection = self.create_collection(collection_name)

        # Add in batches to avoid memory issues
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i : i + batch_size]
            batch_meta = metadatas[i : i + batch_size]
            batch_ids = ids[i : i + batch_size]

            collection.add(documents=batch_docs, metadatas=batch_meta, ids=batch_ids)

    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Search for similar documents

        Args:
            collection_name: Collection to search
            query: Search query
            n_results: Number of results to return
            where: Optional metadata filter

        Returns:
            Dictionary with documents, metadatas, distances
        """
        try:
            collection = self.client.get_collection(
                name=collection_name, embedding_function=self.embedding_function
            )

            results = collection.query(
                query_texts=[query], n_results=n_results, where=where
            )

            return results
        except Exception as e:
            print(f"Search error: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    def delete_collection(self, name: str) -> None:
        """Delete a collection"""
        try:
            self.client.delete_collection(name=name)
        except Exception as e:
            print(f"Delete collection error: {e}")

    def list_collections(self) -> List[str]:
        """List all collections"""
        try:
            return [col.name for col in self.client.list_collections()]
        except Exception as e:
            print(f"List collections error: {e}")
            return []

    def get_collection_count(self, name: str) -> int:
        """Get document count in collection"""
        try:
            collection = self.client.get_collection(name=name)
            return collection.count()
        except:
            return 0
