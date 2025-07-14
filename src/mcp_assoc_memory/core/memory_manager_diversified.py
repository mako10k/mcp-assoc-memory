"""
Diversified memory search algorithms - for broader knowledge exploration
Implements diversity-based result filtering for creative exploration
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from ..models.memory import Memory
from ..utils.logging import get_memory_logger

if TYPE_CHECKING:
    from ..core.embedding_service import EmbeddingService
    from ..storage.base import BaseVectorStore

logger = get_memory_logger(__name__)


class MemoryManagerDiversified:
    """Diversified search algorithms mixin - requires MemoryManagerCore inheritance"""

    # Type annotations for inherited attributes
    embedding_service: "EmbeddingService"
    vector_store: "BaseVectorStore"

    # Method stubs for inherited methods
    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Stub - implemented in MemoryManagerCore"""
        raise NotImplementedError("This method should be inherited from MemoryManagerCore")

    async def find_similar_memories(
        self, reference_id: str, scope: Optional[str] = None, limit: int = 10, min_score: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Stub - implemented in MemoryManagerSearch"""
        raise NotImplementedError("This method should be inherited from MemoryManagerSearch")

    async def search_by_tags(
        self, tags: List[str], scope: Optional[str] = None, match_all: bool = False, limit: int = 10
    ) -> List[Memory]:
        """Stub - implemented in MemoryManagerSearch"""
        raise NotImplementedError("This method should be inherited from MemoryManagerSearch")

    async def search_by_category(self, category: str, scope: Optional[str] = None, limit: int = 10) -> List[Memory]:
        """Stub - implemented in MemoryManagerSearch"""
        raise NotImplementedError("This method should be inherited from MemoryManagerSearch")

    async def diversified_similarity_search(
        self,
        query: str,
        scope: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.1,
        diversity_threshold: float = 0.8,
        expansion_factor: float = 2.5,
        max_expansion_factor: float = 5.0,
    ) -> List[Tuple[Memory, float]]:
        """
        Diversified similarity search for broader knowledge exploration

        This method finds diverse memories by avoiding clusters of similar content,
        ensuring broader coverage of the knowledge space rather than drilling deep
        into specific topics.

        Args:
            query: Search query
            scope: Target scope for search
            limit: Number of diverse results to return
            min_score: Minimum similarity threshold
            diversity_threshold: Similarity threshold for excluding similar items (0.8 = exclude items >80% similar)
            expansion_factor: Initial expansion multiplier for candidate search (2.5x)
            max_expansion_factor: Maximum expansion when fallback is needed (5.0x)

        Returns:
            List of diverse memories with similarity scores, prioritizing variety
        """
        try:
            logger.info(f"Starting diversified similarity search: query='{query}', limit={limit}")

            # Generate query embedding
            query_embedding = await self.embedding_service.get_embedding(query)
            if query_embedding is None:
                logger.warning("Failed to generate query embedding for diversified search")
                return []

            # Ensure embedding is valid
            if hasattr(query_embedding, "__len__") and len(query_embedding) == 0:
                logger.warning("Empty query embedding generated for diversified search")
                return []

            # Calculate initial search size with expansion factor
            initial_search_size = max(limit * expansion_factor, limit + 10)
            initial_search_size = min(initial_search_size, 100)  # Cap at reasonable limit

            logger.info(f"Searching for candidates: initial_size={initial_search_size}")

            # Get initial candidates
            candidates = await self._get_similarity_candidates(
                query_embedding, scope, int(initial_search_size), min_score
            )

            logger.info(f"Found {len(candidates)} initial candidates")

            if len(candidates) < limit:
                # Fallback: try with larger search and lower threshold
                fallback_size = min(limit * max_expansion_factor, 200)
                fallback_min_score = max(min_score * 0.5, 0.05)

                logger.info(f"Fallback search: size={fallback_size}, min_score={fallback_min_score}")

                candidates = await self._get_similarity_candidates(
                    query_embedding, scope, int(fallback_size), fallback_min_score
                )

                logger.info(f"Fallback found {len(candidates)} candidates")

            if not candidates:
                logger.warning("No candidates found for diversified search")
                return []

            # Apply diversity filtering
            diverse_results = await self._apply_diversity_filter(candidates, scope, diversity_threshold, limit)

            logger.info(f"Diversified search completed: {len(diverse_results)} diverse results")

            return diverse_results

        except Exception as e:
            logger.error(f"Diversified similarity search error: {e}")
            return []

    async def _get_similarity_candidates(
        self,
        query_embedding: Any,  # Support numpy arrays, lists, and other formats
        scope: Optional[str],
        limit: int,
        min_score: float,
    ) -> List[dict]:
        """Get similarity candidates from vector store"""
        try:
            # Convert embedding to list format for vector store
            try:
                if hasattr(query_embedding, "tolist"):
                    embedding_list = query_embedding.tolist()
                elif hasattr(query_embedding, "flatten"):
                    embedding_list = query_embedding.flatten().tolist()
                else:
                    # Try to convert numpy array or other array-like objects
                    import numpy as np

                    embedding_array = np.array(query_embedding)
                    embedding_list = embedding_array.flatten().tolist()
            except Exception as conv_e:
                logger.error(f"Failed to convert embedding to list: {conv_e}")
                return []

            if not embedding_list:
                logger.warning("Empty embedding list after conversion")
                return []

            # Search vector store
            candidates = await self.vector_store.search_similar(
                embedding_list, scope=scope, include_child_scopes=False, limit=limit, min_similarity=min_score
            )

            # Filter by minimum score
            filtered_candidates = [
                candidate
                for candidate in candidates
                if candidate.get("similarity", candidate.get("score", 0.0)) >= min_score
            ]

            return filtered_candidates

        except Exception as e:
            logger.error(f"Error getting similarity candidates: {e}")
            return []

    async def _apply_diversity_filter(
        self, candidates: List[dict], scope: Optional[str], diversity_threshold: float, limit: int
    ) -> List[Tuple[Memory, float]]:
        """Apply diversity filtering to candidates"""
        try:
            diverse_results: List[Tuple[Memory, float]] = []
            exclude_set: Set[str] = set()

            # Sort candidates by similarity score (descending)
            sorted_candidates = sorted(candidates, key=lambda x: x.get("similarity", x.get("score", 0.0)), reverse=True)

            for candidate in sorted_candidates:
                if len(diverse_results) >= limit:
                    break

                memory_id = candidate["memory_id"]
                similarity_score = candidate.get("similarity", candidate.get("score", 0.0))

                # Skip if already excluded for diversity
                if memory_id in exclude_set:
                    continue

                # Get memory object
                memory = await self.get_memory(memory_id)
                if not memory:
                    continue

                # Add to results
                diverse_results.append((memory, similarity_score))

                # Add similar memories to exclude set for diversity
                await self._add_to_exclude_set(memory, exclude_set, scope, diversity_threshold)

            return diverse_results

        except Exception as e:
            logger.error(f"Error applying diversity filter: {e}")
            return []

    async def _add_to_exclude_set(
        self, memory: Memory, exclude_set: Set[str], scope: Optional[str], diversity_threshold: float
    ) -> None:
        """Add similar memories to exclude set for diversity"""
        try:
            # Add current memory to exclude set
            exclude_set.add(memory.id)

            # Find similar memories to exclude for diversity
            similar_memories = await self.find_similar_memories(
                reference_id=memory.id,
                scope=scope,
                limit=10,  # Small limit for efficiency
                min_score=diversity_threshold,
            )

            # Add similar memory IDs to exclude set
            for result in similar_memories:
                similar_memory = result["memory"]
                exclude_set.add(similar_memory.id)

        except Exception as e:
            logger.error(f"Error adding to exclude set: {e}")

    async def diverse_tag_search(
        self, tags: List[str], scope: Optional[str] = None, limit: int = 10, diversity_threshold: float = 0.8
    ) -> List[Memory]:
        """Diversified search by tags"""
        try:
            # Get more candidates than needed
            candidates = await self.search_by_tags(tags, scope, match_all=False, limit=limit * 3)

            if not candidates:
                return []

            # Apply diversity filtering
            diverse_results: List[Any] = []
            exclude_set: Set[str] = set()

            for memory in candidates:
                if len(diverse_results) >= limit:
                    break

                if memory.id in exclude_set:
                    continue

                diverse_results.append(memory)

                # Add similar memories to exclude set
                await self._add_to_exclude_set(memory, exclude_set, scope, diversity_threshold)

            return diverse_results

        except Exception as e:
            logger.error(f"Diverse tag search error: {e}")
            return []

    async def diverse_category_search(
        self, category: str, scope: Optional[str] = None, limit: int = 10, diversity_threshold: float = 0.8
    ) -> List[Memory]:
        """Diversified search by category"""
        try:
            # Get more candidates than needed
            candidates = await self.search_by_category(category, scope, limit=limit * 3)

            if not candidates:
                return []

            # Apply diversity filtering
            diverse_results: List[Any] = []
            exclude_set: Set[str] = set()

            for memory in candidates:
                if len(diverse_results) >= limit:
                    break

                if memory.id in exclude_set:
                    continue

                diverse_results.append(memory)

                # Add similar memories to exclude set
                await self._add_to_exclude_set(memory, exclude_set, scope, diversity_threshold)

            return diverse_results

        except Exception as e:
            logger.error(f"Diverse category search error: {e}")
            return []

    async def explore_knowledge_space(
        self,
        starting_memory_id: str,
        exploration_depth: int = 3,
        diversity_threshold: float = 0.7,
        limit_per_level: int = 5,
    ) -> List[Tuple[Memory, int]]:
        """Explore knowledge space starting from a memory with diversity"""
        try:
            explored_memories = []
            exclude_set: Set[str] = set()
            current_level = [starting_memory_id]

            for depth in range(exploration_depth):
                next_level: List[Any] = []

                for memory_id in current_level:
                    if memory_id in exclude_set:
                        continue

                    memory = await self.get_memory(memory_id)
                    if memory:
                        explored_memories.append((memory, depth))
                        exclude_set.add(memory_id)

                        # Find diverse similar memories for next level
                        similar_memories = await self.find_similar_memories(memory_id, limit=limit_per_level * 2)

                        # Select diverse candidates for next level
                        level_exclude: Set[Any] = set()
                        for result in similar_memories:
                            similar_memory = result["memory"]
                            if (
                                len(next_level) < limit_per_level
                                and similar_memory.id not in exclude_set
                                and similar_memory.id not in level_exclude
                            ):

                                next_level.append(similar_memory.id)

                                # Add similar memories to level exclude set
                                await self._add_to_exclude_set(similar_memory, level_exclude, None, diversity_threshold)

                current_level = next_level
                if not current_level:
                    break

            return explored_memories

        except Exception as e:
            logger.error(f"Knowledge space exploration error: {e}")
            return []
