"""
Memory search operations - semantic, tag, and advanced searc            for result in vector_results:
                memory_id = result["memory_id"]
                score = result["similarity"]
                memory = await self.get_memory(memory_id)  # type: ignore
                if memory:
                    memories_with_scores.append({"memory": memory, "similarity": score})tionality
Handles all search-related operations including complex queries
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..models.memory import Memory
from ..utils.logging import get_memory_logger

if TYPE_CHECKING:
    from ..core.embedding_service import EmbeddingService
    from ..storage.base import BaseMetadataStore, BaseVectorStore

logger = get_memory_logger(__name__)


class MemoryManagerSearch:
    """Memory search operations mixin - requires MemoryManagerCore inheritance"""

    # Type annotations for inherited attributes
    embedding_service: "EmbeddingService"
    vector_store: "BaseVectorStore"
    metadata_store: "BaseMetadataStore"
    # similarity_calculator inherited from MemoryManagerCore

    # Inherited attributes type annotations only

    async def search_memories(
        self,
        query: str,
        scope: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.5,
        include_child_scopes: bool = False,
    ) -> List[Dict[str, Any]]:
        """Standard semantic search for memories"""
        try:
            if not query:
                return []

            # Generate query embedding
            query_embedding = await self.embedding_service.get_embedding(query)
            if query_embedding is None:
                logger.warning("Failed to generate embedding for search query")
                return []

            # Check if embedding is empty using len() instead of size for numpy arrays
            if hasattr(query_embedding, "__len__") and len(query_embedding) == 0:
                logger.warning("Empty embedding for search query")
                return []

            # Search in vector store
            filters = {"include_child_scopes": include_child_scopes} if include_child_scopes else None
            # Convert numpy array to list
            query_emb_list = query_embedding.tolist() if hasattr(query_embedding, "tolist") else list(query_embedding)
            results = await self.vector_store.search_similar(
                query_emb_list, scope=scope, limit=limit, min_similarity=min_score, filters=filters
            )

            # Convert to memory objects with scores (dictionary format)
            memories_with_scores = []
            for result in results:
                memory_id = result["memory_id"]
                score = result["similarity"]
                memory = await self.get_memory(memory_id)  # type: ignore
                if memory:
                    memories_with_scores.append({"memory": memory, "similarity": score})

            logger.info(
                "Memory search completed",
                extra_data={
                    "query": query[:50],
                    "scope": scope,
                    "results_count": len(memories_with_scores),
                    "min_score": min_score,
                },
            )

            return memories_with_scores

        except Exception as e:
            logger.error(
                "Memory search failed", error_code="MEMORY_SEARCH_ERROR", query=query[:50], scope=scope, error=str(e)
            )
            return []

    async def semantic_search(
        self, query: str, scope: Optional[str] = None, limit: int = 10, min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Traditional semantic search for focused knowledge exploration

        This method finds memories most semantically similar to the query,
        ideal for finding specific information or exploring related topics.

        For diverse, broad exploration across different topics, use
        diversified_similarity_search() instead.
        """
        try:
            embedding = await self.embedding_service.get_embedding(query)
            if embedding is None:
                return []

            # Check if embedding is empty using len() instead of size for numpy arrays
            if hasattr(embedding, "__len__") and len(embedding) == 0:
                return []

            # Vector search
            emb_list = embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
            results = await self.vector_store.search_similar(
                emb_list, scope=scope or "user/default", limit=limit, min_similarity=min_score
            )

            # Convert to memory objects (dictionary format)
            memories_with_scores = []
            for result in results:
                memory_id = result["memory_id"]
                score = result["similarity"]
                memory = await self.get_memory(memory_id)  # type: ignore
                if memory:
                    memories_with_scores.append({"memory": memory, "similarity": score})

            return memories_with_scores
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []

    async def search_by_tags(
        self, tags: List[str], scope: Optional[str] = None, match_all: bool = False, limit: int = 10
    ) -> List[Memory]:
        """Tag-based search"""
        try:
            results = await self.metadata_store.search_by_tags(tags, scope, match_all, limit)
            return results
        except Exception as e:
            logger.error(f"Tag search error: {e}")
            return []

    async def search_by_timerange(
        self, start_date: datetime, end_date: datetime, scope: Optional[str] = None, limit: int = 10
    ) -> List[Memory]:
        """Time range search"""
        try:
            return await self.metadata_store.search_by_timerange(start_date, end_date, scope, limit)
        except Exception as e:
            logger.error(f"Time range search error: {e}")
            return []

    async def advanced_search(
        self,
        query: str = "",
        scope: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_score: float = 0.5,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Advanced search with multiple criteria"""
        try:
            # Complex search with metadata filtering
            memories = await self.metadata_store.advanced_search(
                scope=scope,
                tags=tags or [],
                category=category,
                start_date=start_date,
                end_date=end_date,
                limit=limit * 3,  # Get more for score filtering
            )

            if not query:
                # No query - return chronological order
                return [{"memory": memory, "similarity": 1.0} for memory in memories[:limit]]

            # Semantic similarity filtering
            query_embedding = await self.embedding_service.get_embedding(query)
            if query_embedding is None:
                return [{"memory": memory, "similarity": 1.0} for memory in memories[:limit]]

            # Check if embedding is empty using len() instead of size for numpy arrays
            if hasattr(query_embedding, "__len__") and len(query_embedding) == 0:
                return [{"memory": memory, "similarity": 1.0} for memory in memories[:limit]]

            scored_memories = []
            for memory in memories:
                # Get memory embedding
                memory_embedding = await self.vector_store.get_embedding(memory.id)
                if memory_embedding and self.similarity_calculator:  # type: ignore
                    score = self.similarity_calculator.cosine_similarity(query_embedding, memory_embedding)  # type: ignore
                    if score >= min_score:
                        scored_memories.append({"memory": memory, "similarity": score})

            # Sort by score
            scored_memories.sort(
                key=lambda x: x["similarity"] if isinstance(x["similarity"], (int, float)) else 0.0, reverse=True
            )
            return scored_memories[:limit]

        except Exception as e:
            logger.error(f"Advanced search error: {e}")
            return []

    async def find_similar_memories(
        self, reference_id: str, scope: Optional[str] = None, limit: int = 10, min_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Traditional similarity search for focused knowledge exploration

        This method finds memories most similar to a reference memory,
        ideal for drilling deeper into specific topics or knowledge areas.
        Use this when you want to explore related content in the same domain.

        For broader, more diverse exploration, use diversified_similarity_search() instead.
        """
        try:
            # Get reference memory embedding
            reference_embedding = await self.vector_store.get_embedding(reference_id)
            if reference_embedding is None:
                return []

            # Check if embedding is empty using len() instead of size for numpy arrays
            if hasattr(reference_embedding, "__len__") and len(reference_embedding) == 0:
                return []

            # Similarity search
            ref_emb_list = (
                reference_embedding.tolist() if hasattr(reference_embedding, "tolist") else list(reference_embedding)
            )
            results = await self.vector_store.search_similar(
                ref_emb_list,
                scope=scope or "user/default",
                limit=limit + 1,  # +1 to exclude self
                min_similarity=min_score,
            )

            # Convert to memory objects (exclude reference memory)
            memories_with_scores = []
            for result in results:
                memory_id = result["memory_id"]
                score = result["similarity"]
                if memory_id != reference_id:
                    memory = await self.get_memory(memory_id)  # type: ignore
                    if memory:
                        memories_with_scores.append({"memory": memory, "similarity": score})

            return memories_with_scores[:limit]
        except Exception as e:
            logger.error(f"Similar memories search error: {e}")
            return []

    async def search_by_scope_pattern(self, pattern: str, limit: int = 50) -> List[Memory]:
        """Search memories by scope pattern (supports wildcards)"""
        try:
            # TODO: Implement in BaseMetadataStore
            logger.warning("search_by_scope_pattern not implemented in BaseMetadataStore")
            return []
        except Exception as e:
            logger.error(f"Scope pattern search error: {e}")
            return []

    async def full_text_search(self, text: str, scope: Optional[str] = None, limit: int = 10) -> List[Memory]:
        """Full-text search in memory content"""
        try:
            # TODO: Implement in BaseMetadataStore
            logger.warning("full_text_search not implemented in BaseMetadataStore")
            return []
        except Exception as e:
            logger.error(f"Full-text search error: {e}")
            return []

    async def search_by_metadata(
        self, metadata_filters: Dict[str, Any], scope: Optional[str] = None, limit: int = 10
    ) -> List[Memory]:
        """Search memories by metadata criteria"""
        try:
            # TODO: Implement in BaseMetadataStore
            logger.warning("search_by_metadata not implemented in BaseMetadataStore")
            return []
        except Exception as e:
            logger.error(f"Metadata search error: {e}")
            return []

    async def search_recently_accessed(self, scope: Optional[str] = None, limit: int = 10) -> List[Memory]:
        """Get recently accessed memories"""
        try:
            # TODO: Implement in BaseMetadataStore
            logger.warning("get_recently_accessed not implemented in BaseMetadataStore")
            return []
        except Exception as e:
            logger.error(f"Recent access search error: {e}")
            return []

    async def search_by_category(self, category: str, scope: Optional[str] = None, limit: int = 10) -> List[Memory]:
        """Search memories by category"""
        try:
            # TODO: Implement in BaseMetadataStore
            logger.warning("search_by_category not implemented in BaseMetadataStore")
            return []
        except Exception as e:
            logger.error(f"Category search error: {e}")
            return []

    async def fuzzy_search(
        self, query: str, scope: Optional[str] = None, limit: int = 10, threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Fuzzy text matching search"""
        try:
            # TODO: Implement in BaseMetadataStore
            logger.warning("fuzzy_search not implemented in BaseMetadataStore")
            return []
        except Exception as e:
            logger.error(f"Fuzzy search error: {e}")
            return []
