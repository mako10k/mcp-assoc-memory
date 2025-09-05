"""
ChromaDB Vector Store Implementation - Scope-based single collection
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import chromadb

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from ..utils.logging import get_memory_logger
from ..utils.paths import get_chroma_dir
from .base import BaseVectorStore

logger = get_memory_logger(__name__)


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB implementation with single collection and scope-based organization"""

    def __init__(self, persist_directory: Optional[str] = None, host: Optional[str] = None, port: Optional[int] = None):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB is not installed. Install it with: pip install chromadb")

        if persist_directory is None:
            self.persist_directory = str(get_chroma_dir())
        else:
            p = Path(persist_directory).expanduser().resolve()
            assert p.is_absolute(), f"persist_directory must be absolute: {p}"
            self.persist_directory = str(p)

        self.host = host
        self.port = port
        self.client: Optional[Any] = None
        self.collection: Optional[Any] = None  # Single collection for all memories

    async def initialize(self) -> None:
        """Initialize ChromaDB client with single collection"""
        try:
            if self.host and self.port:
                # Remote connection
                self.client = chromadb.HttpClient(host=self.host, port=self.port)
            else:
                # Local persistence with new API
                self.client = chromadb.PersistentClient(path=self.persist_directory)

            # Initialize single collection for all memories
            collection_name = "memories"
            if self.client is None:
                raise RuntimeError("ChromaDB client not initialized")

            try:
                # Use synchronous API directly instead of run_in_executor
                self.collection = self.client.get_collection(collection_name)
                logger.info(f"Using existing collection: {collection_name}")
            except Exception:
                # Create new collection with cosine distance
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={
                        "description": "Unified memory collection with scope-based organization",
                        "hnsw:space": "cosine",  # Use cosine distance as per design spec
                    },
                )
                logger.info(f"Created new collection: {collection_name} with cosine distance")

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

    async def store_vector(self, memory_id: str, embedding: Any, metadata: Dict[str, Any]) -> None:
        """Store vector in ChromaDB"""
        try:
            if self.collection is None:
                raise RuntimeError("ChromaDB collection not initialized")

            # Prepare metadata (ChromaDB requires string values)
            chroma_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    chroma_metadata[key] = str(value)
                else:
                    chroma_metadata[key] = str(value)

            # Use synchronous API directly
            self.collection.add(ids=[memory_id], embeddings=[embedding], metadatas=[chroma_metadata])

            logger.info(
                "Vector stored successfully", extra={"memory_id": memory_id, "scope": metadata.get("scope", "unknown")}
            )

        except Exception as e:
            logger.error("Failed to store vector", error_code="VECTOR_STORE_ERROR", memory_id=memory_id, error=str(e))

    async def get_embedding(self, memory_id: str) -> Optional[Any]:
        """Get embedding by memory ID"""
        try:
            if self.collection is None:
                raise RuntimeError("ChromaDB collection not initialized")

            result = self.collection.get(ids=[memory_id], include=["embeddings"])
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
            if self.collection is None:
                raise RuntimeError("ChromaDB collection not initialized")

            self.collection.delete(ids=[memory_id])
            logger.info("Vector deleted successfully", extra={"memory_id": memory_id})
            return True
        except Exception as e:
            logger.debug(
                "Vector not found for deletion (this is normal)", extra={"memory_id": memory_id, "error": str(e)}
            )
            # Return True because the vector doesn't exist (desired state)
            return True

    async def search_similar(
        self,
        query_embedding: List[float],
        scope: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.1,
        filters: Optional[Dict[str, Any]] = None,
        include_child_scopes: bool = False,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors with hierarchical scope support"""
        try:
            # Prepare where clause for scope filtering
            where_clause = None
            if scope:
                if include_child_scopes:
                    # Use prefix matching for hierarchical scopes
                    # Note: ChromaDB doesn't support prefix matching directly,
                    # so we'll filter post-query
                    where_clause = None  # Get all results and filter after
                else:
                    where_clause = {"scope": scope}

            # Log debug info
            logger.info(
                f"[DEBUG] search_similar: scope={scope}, include_child_scopes={include_child_scopes}, where_clause={where_clause}"
            )

            if self.collection is None:
                raise RuntimeError("ChromaDB collection not initialized")

            result = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=int(limit * 3) if include_child_scopes else int(limit),  # Ensure integers
                where=where_clause,
                include=["metadatas", "distances"],
            )

            logger.info(
                f"[DEBUG] ChromaDB raw results count: {len(result['ids'][0]) if result['ids'] and result['ids'][0] else 0}"
            )

            # Convert and filter results
            results = []
            if result["ids"] and result["ids"][0]:
                for i, memory_id in enumerate(result["ids"][0]):
                    distance = result["distances"][0][i]

                    # Handle cosine distance properly
                    # ChromaDB cosine distance: 0 = identical, 2 = opposite
                    # Convert to similarity: 1 = identical, 0 = opposite
                    if distance <= 0:
                        similarity = 1.0  # Perfect match
                    elif distance >= 2.0:
                        similarity = 0.0  # Completely opposite (rare)
                    else:
                        # Standard cosine distance to similarity conversion
                        similarity = 1.0 - distance

                    metadata = result["metadatas"][0][i] if result["metadatas"] and result["metadatas"][0] else {}

                    # Apply hierarchical scope filtering if needed
                    result_scope = metadata.get("scope", "")
                    scope_match = True

                    if scope and include_child_scopes:
                        # Check if result scope is under the requested scope hierarchy
                        if isinstance(result_scope, str) and isinstance(scope, str):
                            scope_match = (
                                result_scope == scope
                                or result_scope.startswith(scope + "/")
                                or scope.startswith(result_scope + "/")
                            )
                        else:
                            scope_match = False
                    elif scope and not include_child_scopes:
                        # Exact scope match (already handled by where_clause, but double-check)
                        scope_match = result_scope == scope

                    logger.info(
                        f"[DEBUG] Processing result: memory_id={memory_id}, scope={result_scope}, similarity={similarity:.3f}, scope_match={scope_match}"
                    )

                    if similarity >= min_similarity and scope_match:
                        results.append(
                            {
                                "id": None,  # For compatibility
                                "memory_id": memory_id,
                                "similarity": similarity,
                                "distance": distance,
                                "metadata": metadata,
                            }
                        )

            # Limit final results
            results = results[:limit]

            logger.info(
                f"Vector search completed: {len(results)} results after filtering (scope={scope}, include_child={include_child_scopes})"
            )
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def search(
        self, embedding: Any, scope: Optional[str] = None, limit: int = 10, min_score: float = 0.7
    ) -> List[Tuple[str, float]]:
        """Search for similar vectors (compatibility method)"""
        results = await self.search_similar(embedding, scope, limit, min_score)
        return [(r["memory_id"], r["similarity"]) for r in results]

    async def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            if self.collection is None:
                raise RuntimeError("ChromaDB collection not initialized")

            result = self.collection.get(include=["metadatas"])

            total_count = len(result["ids"]) if result["ids"] else 0

            # Count by scope
            scope_counts: Dict[str, int] = {}
            if result["metadatas"]:
                for metadata in result["metadatas"]:
                    scope = metadata.get("scope", "unknown")
                    scope_counts[scope] = scope_counts.get(scope, 0) + 1

            return {"total_vectors": total_count, "scope_counts": scope_counts, "collection_name": "memories"}

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {"error": str(e)}

    async def update_metadata(self, memory_id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for existing vector"""
        try:
            if self.collection is None:
                raise RuntimeError("ChromaDB collection not initialized")

            # Prepare metadata (ChromaDB requires string values)
            chroma_metadata = {}
            for key, value in metadata.items():
                chroma_metadata[key] = str(value)

            self.collection.update(ids=[memory_id], metadatas=[chroma_metadata])

            logger.info("Vector metadata updated", extra={"memory_id": memory_id})
            return True

        except Exception as e:
            logger.error(
                "Failed to update vector metadata", error_code="VECTOR_UPDATE_ERROR", memory_id=memory_id, error=str(e)
            )
            return False

    async def close(self) -> None:
        """Close the ChromaDB connection"""
        try:
            # ChromaDB doesn't require explicit connection closing
            self.client = None
            self.collection = None
            logger.info("ChromaDB vector store closed")
        except Exception as e:
            logger.error("Failed to close ChromaDB vector store", error=str(e))

    async def health_check(self) -> Dict[str, Any]:
        """Check ChromaDB health status"""
        try:
            if not self.client or not self.collection:
                return {"status": "error", "message": "ChromaDB not initialized"}

            # Get collection stats as health check
            count = self.collection.count()

            return {
                "status": "healthy",
                "collection_name": self.collection.name,
                "document_count": count,
                "persist_directory": self.persist_directory,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {"status": "error", "message": str(e), "timestamp": datetime.utcnow().isoformat()}

    async def get_collection_stats(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """Get collection statistics, optionally filtered by scope"""
        try:
            if not self.collection:
                return {"error": "Collection not initialized"}

            total_count = self.collection.count()

            stats = {
                "total_documents": total_count,
                "collection_name": self.collection.name,
            }

            if scope:
                # Get documents for specific scope
                try:
                    results = self.collection.get(where={"scope": scope})
                    scope_count = len(results.get("ids", []))
                    stats["scope_documents"] = scope_count
                    stats["filtered_by_scope"] = scope
                except Exception as e:
                    logger.warning(f"Failed to get scope-specific stats: {e}")
                    stats["scope_documents"] = "unknown"

            return stats

        except Exception as e:
            logger.error("Failed to get collection stats", error_code="COLLECTION_STATS_ERROR", error=str(e))
            return {"error": str(e)}
