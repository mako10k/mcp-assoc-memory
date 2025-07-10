"""
ChromaDB Vector Store Implementation - Scope-based single collection
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from ..utils.logging import get_memory_logger
from .base import BaseVectorStore

logger = get_memory_logger(__name__)


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB implementation with single collection and scope-based organization"""

    def __init__(
        self,
        persist_directory: str = "./data/chroma_db",
        host: Optional[str] = None,
        port: Optional[int] = None
    ):
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB is not installed. "
                "Install it with: pip install chromadb"
            )

        self.persist_directory = persist_directory
        self.host = host
        self.port = port
        self.client = None
        self.collection = None  # Single collection for all memories

    async def initialize(self) -> None:
        """Initialize ChromaDB client with single collection"""
        try:
            if self.host and self.port:
                # Remote connection
                self.client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port
                )
            else:
                # Local persistence
                self.client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )

            # Initialize single collection for all memories
            collection_name = "memories"
            try:
                self.collection = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.get_collection(collection_name)
                )
                logger.info(f"Using existing collection: {collection_name}")
            except Exception:
                # Create new collection
                self.collection = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.create_collection(
                        name=collection_name,
                        metadata={"description": "Unified memory collection with scope-based organization"},
                    )
                )
                logger.info(f"Created new collection: {collection_name}")

            logger.info("ChromaDB vector store initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    async def store_embedding(self, memory_id: str, embedding: Any, metadata: Dict[str, Any]) -> bool:
        """Store embedding with metadata"""
        try:
            await self.store_vector(memory_id, embedding, metadata)
            return True
        except Exception as e:
            logger.error(f"store_embedding error: {e}")
            return False

    async def store_vector(
        self,
        memory_id: str,
        embedding: Any,
        metadata: Dict[str, Any]
    ) -> bool:
        """Store vector in ChromaDB"""
        try:
            # Prepare metadata (ChromaDB requires string values)
            chroma_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    chroma_metadata[key] = str(value)
                else:
                    chroma_metadata[key] = str(value)

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.collection.add(
                    ids=[memory_id],
                    embeddings=[embedding],
                    metadatas=[chroma_metadata]
                )
            )

            logger.info(
                "Vector stored successfully",
                extra={
                    "memory_id": memory_id,
                    "scope": metadata.get("scope", "unknown")
                }
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to store vector",
                error_code="VECTOR_STORE_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            return False

    async def get_embedding(self, memory_id: str) -> Optional[Any]:
        """Get embedding by memory ID"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.collection.get(ids=[memory_id], include=["embeddings"])
            )
            if result["embeddings"] and result["embeddings"][0]:
                return result["embeddings"][0]
            return None
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            return None

    async def delete_embedding(self, memory_id: str) -> bool:
        """Delete embedding by memory ID"""
        return await self.delete_vector(memory_id)

    async def delete_vector(self, memory_id: str) -> bool:
        """Delete vector from ChromaDB"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.collection.delete(ids=[memory_id])
            )
            logger.info(
                "Vector deleted successfully",
                extra={"memory_id": memory_id}
            )
            return True
        except Exception as e:
            logger.debug(
                "Vector not found for deletion (this is normal)",
                extra={"memory_id": memory_id, "error": str(e)}
            )
            # Return True because the vector doesn't exist (desired state)
            return True

    async def search_similar(
        self,
        embedding: Any,
        scope: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.1
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        try:
            # Prepare where clause for scope filtering
            where_clause = None
            if scope:
                where_clause = {"scope": scope}

            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.collection.query(
                    query_embeddings=[embedding],
                    n_results=limit,
                    where=where_clause,
                    include=["metadatas", "distances"]
                )
            )

            # Convert results
            results = []
            if result["ids"] and result["ids"][0]:
                for i, memory_id in enumerate(result["ids"][0]):
                    distance = result["distances"][0][i]
                    similarity = 1.0 - distance  # Convert distance to similarity
                    
                    if similarity >= min_score:
                        metadata = result["metadatas"][0][i] if result["metadatas"] and result["metadatas"][0] else {}
                        results.append({
                            "id": None,  # For compatibility
                            "memory_id": memory_id,
                            "similarity": similarity,
                            "distance": distance,
                            "metadata": metadata
                        })

            logger.info("Vector search completed", extra={"results_count": len(results)})
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def search(self, embedding: Any, scope: Optional[str] = None, limit: int = 10, min_score: float = 0.7) -> List[Tuple[str, float]]:
        """Search for similar vectors (compatibility method)"""
        results = await self.search_similar(embedding, scope, limit, min_score)
        return [(r["memory_id"], r["similarity"]) for r in results]

    async def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.collection.get(include=["metadatas"])
            )
            
            total_count = len(result["ids"]) if result["ids"] else 0
            
            # Count by scope
            scope_counts = {}
            if result["metadatas"]:
                for metadata in result["metadatas"]:
                    scope = metadata.get("scope", "unknown")
                    scope_counts[scope] = scope_counts.get(scope, 0) + 1

            return {
                "total_vectors": total_count,
                "scope_counts": scope_counts,
                "collection_name": "memories"
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}

    async def update_metadata(
        self,
        memory_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Update metadata for existing vector"""
        try:
            # Prepare metadata (ChromaDB requires string values)
            chroma_metadata = {}
            for key, value in metadata.items():
                chroma_metadata[key] = str(value)

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.collection.update(
                    ids=[memory_id],
                    metadatas=[chroma_metadata]
                )
            )

            logger.info(
                "Vector metadata updated",
                extra={"memory_id": memory_id}
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to update vector metadata",
                error_code="VECTOR_UPDATE_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            return False
