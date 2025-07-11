"""
Memory search operations - semantic, tag, and advanced search functionality
Handles all search-related operations including complex queries
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..models.memory import Memory
from ..utils.logging import get_memory_logger

logger = get_memory_logger(__name__)


class MemoryManagerSearch:
    """Memory search operations"""

    async def search_memories(
        self,
        query: str,
        scope: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.5,
        include_child_scopes: bool = False
    ) -> List[Dict[str, Any]]:
        """Standard semantic search for memories"""
        try:
            if not query:
                return []

            # Generate query embedding
            query_embedding = await self.embedding_service.get_embedding(query)
            if not query_embedding:
                logger.warning("Failed to generate embedding for search query")
                return []

            # Search in vector store
            search_scope = scope
            if include_child_scopes and scope:
                # Include child scopes in search
                search_scope = f"{scope}/*"

            results = await self.vector_store.search(
                query_embedding,
                scope=search_scope,
                limit=limit,
                min_score=min_score
            )

            # Convert to memory objects with scores (dictionary format)
            memories_with_scores = []
            for memory_id, score in results:
                memory = await self.get_memory(memory_id)
                if memory:
                    memories_with_scores.append({
                        "memory": memory,
                        "similarity": score
                    })

            logger.info(
                "Memory search completed",
                extra_data={
                    "query": query[:50],
                    "scope": scope,
                    "results_count": len(memories_with_scores),
                    "min_score": min_score
                }
            )

            return memories_with_scores

        except Exception as e:
            logger.error(
                "Memory search failed",
                error_code="MEMORY_SEARCH_ERROR",
                query=query[:50],
                scope=scope,
                error=str(e)
            )
            return []

    async def semantic_search(
        self,
        query: str,
        scope: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.5
    ) -> List[Tuple[Memory, float]]:
        """
        Traditional semantic search for focused knowledge exploration
        
        This method finds memories most semantically similar to the query,
        ideal for finding specific information or exploring related topics.
        
        For diverse, broad exploration across different topics, use 
        diversified_similarity_search() instead.
        """
        try:
            embedding = await self.embedding_service.get_embedding(query)
            if not embedding:
                return []

            # Vector search
            results = await self.vector_store.search(
                embedding,
                scope or "user/default",
                limit,
                min_score
            )

            # Convert to memory objects
            memories_with_scores = []
            for memory_id, score in results:
                memory = await self.get_memory(memory_id)
                if memory:
                    memories_with_scores.append((memory, score))

            return memories_with_scores
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []

    async def search_by_tags(
        self,
        tags: List[str],
        scope: Optional[str] = None,
        match_all: bool = False,
        limit: int = 10
    ) -> List[Memory]:
        """Tag-based search"""
        try:
            return await self.metadata_store.search_by_tags(
                tags, scope, match_all, limit
            )
        except Exception as e:
            logger.error(f"Tag search error: {e}")
            return []

    async def search_by_timerange(
        self,
        start_date: datetime,
        end_date: datetime,
        scope: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Time range search"""
        try:
            return await self.metadata_store.search_by_timerange(
                start_date, end_date, scope, limit
            )
        except Exception as e:
            logger.error(f"Time range search error: {e}")
            return []

    async def advanced_search(
        self,
        query: str = '',
        scope: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_score: float = 0.5,
        limit: int = 10
    ) -> List[Tuple[Memory, float]]:
        """Advanced search with multiple criteria"""
        try:
            # Complex search with metadata filtering
            memories = await self.metadata_store.advanced_search(
                scope=scope,
                tags=tags or [],
                category=category,
                start_date=start_date,
                end_date=end_date,
                limit=limit * 3  # Get more for score filtering
            )

            if not query:
                # No query - return chronological order
                return [(memory, 1.0) for memory in memories[:limit]]

            # Semantic similarity filtering
            query_embedding = await self.embedding_service.get_embedding(query)
            if not query_embedding:
                return [(memory, 1.0) for memory in memories[:limit]]

            scored_memories = []
            for memory in memories:
                # Get memory embedding
                memory_embedding = await self.vector_store.get_embedding(memory.id)
                if memory_embedding:
                    score = self.similarity_calculator.cosine_similarity(
                        query_embedding, memory_embedding
                    )
                    if score >= min_score:
                        scored_memories.append((memory, score))

            # Sort by score
            scored_memories.sort(key=lambda x: x[1], reverse=True)
            return scored_memories[:limit]

        except Exception as e:
            logger.error(f"Advanced search error: {e}")
            return []

    async def find_similar_memories(
        self,
        reference_id: str,
        scope: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.7
    ) -> List[Tuple[Memory, float]]:
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
            if not reference_embedding:
                return []

            # Similarity search
            results = await self.vector_store.search(
                reference_embedding,
                scope or "user/default",
                limit + 1,  # +1 to exclude self
                min_score
            )

            # Convert to memory objects (exclude reference memory)
            memories_with_scores = []
            for memory_id, score in results:
                if memory_id != reference_id:
                    memory = await self.get_memory(memory_id)
                    if memory:
                        memories_with_scores.append((memory, score))

            return memories_with_scores[:limit]
        except Exception as e:
            logger.error(f"Similar memories search error: {e}")
            return []

    async def search_by_scope_pattern(
        self,
        pattern: str,
        limit: int = 50
    ) -> List[Memory]:
        """Search memories by scope pattern (supports wildcards)"""
        try:
            return await self.metadata_store.search_by_scope_pattern(pattern, limit)
        except Exception as e:
            logger.error(f"Scope pattern search error: {e}")
            return []

    async def full_text_search(
        self,
        text: str,
        scope: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Full-text search in memory content"""
        try:
            return await self.metadata_store.full_text_search(text, scope, limit)
        except Exception as e:
            logger.error(f"Full-text search error: {e}")
            return []

    async def search_by_metadata(
        self,
        metadata_filters: Dict[str, Any],
        scope: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Search memories by metadata criteria"""
        try:
            return await self.metadata_store.search_by_metadata(
                metadata_filters, scope, limit
            )
        except Exception as e:
            logger.error(f"Metadata search error: {e}")
            return []

    async def search_recently_accessed(
        self,
        scope: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Get recently accessed memories"""
        try:
            return await self.metadata_store.get_recently_accessed(scope, limit)
        except Exception as e:
            logger.error(f"Recent access search error: {e}")
            return []

    async def search_by_category(
        self,
        category: str,
        scope: Optional[str] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Search memories by category"""
        try:
            return await self.metadata_store.search_by_category(category, scope, limit)
        except Exception as e:
            logger.error(f"Category search error: {e}")
            return []

    async def fuzzy_search(
        self,
        query: str,
        scope: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.6
    ) -> List[Tuple[Memory, float]]:
        """Fuzzy text matching search"""
        try:
            return await self.metadata_store.fuzzy_search(query, scope, limit, threshold)
        except Exception as e:
            logger.error(f"Fuzzy search error: {e}")
            return []
