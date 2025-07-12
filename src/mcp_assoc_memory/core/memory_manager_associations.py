"""
Memory association management - auto-association and relationship handling
Manages semantic relationships between memories
"""

import numpy as np
from typing import List, Optional, TYPE_CHECKING

from ..models.association import Association
from ..models.memory import Memory
from ..utils.logging import get_memory_logger

if TYPE_CHECKING:
    from ..storage.base import BaseVectorStore, BaseMetadataStore, BaseGraphStore
    from ..utils.cache import LRUCache

logger = get_memory_logger(__name__)


class MemoryManagerAssociations:
    """Memory association management mixin - requires MemoryManagerCore inheritance"""

    # Type annotations for inherited attributes
    vector_store: "BaseVectorStore"
    metadata_store: "BaseMetadataStore"
    graph_store: "BaseGraphStore"
    association_cache: "LRUCache"

    # Method stubs for inherited methods
    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Stub - implemented in MemoryManagerCore"""
        raise NotImplementedError("This method should be inherited from MemoryManagerCore")

    async def _auto_associate_memory(self, memory: Memory, embedding: np.ndarray) -> None:
        """Auto-associate memory with similar memories"""
        try:
            # Search for similar memories
            emb_list: List[float]
            if hasattr(embedding, "flatten"):
                emb_list = embedding.flatten().tolist()
            elif hasattr(embedding, "tolist"):
                emb_list = embedding.tolist()
            else:
                # Handle list or other iterable types
                emb_list = embedding if isinstance(embedding, list) else list(embedding)

            similar_results = await self.vector_store.search_similar(
                emb_list, scope=memory.scope, limit=10, min_similarity=0.7  # Default threshold for auto-association
            )

            # Create relationships
            for result in similar_results:
                # vector_store.search_similar returns {"memory_id": ..., ...}
                if result["memory_id"] == memory.id:
                    continue  # Exclude self-reference

                similarity_score = result["similarity"]
                if similarity_score >= 0.7:  # Only high similarity
                    association = Association(
                        source_memory_id=memory.id,
                        target_memory_id=result["memory_id"],
                        association_type="semantic",
                        strength=similarity_score,
                        auto_generated=True,
                    )

                    # Store relationship
                    await self._store_association(association)

            logger.info(
                "Auto-association completed", extra_data={"memory_id": memory.id, "similar_count": len(similar_results)}
            )

        except Exception as e:
            logger.error(
                "Failed to auto-associate memory",
                error_code="AUTO_ASSOCIATION_ERROR",
                memory_id=memory.id,
                error=str(e),
            )

    async def _store_association(self, association: Association) -> bool:
        """Store association relationship"""
        try:
            # Store in metadata store
            assoc_id = await self.metadata_store.store_association(association)
            if not assoc_id:
                return False

            # Store in graph store
            await self.graph_store.add_association_edge(association)

            # Store in cache
            self.association_cache.set(association.id, association)

            return True

        except Exception as e:
            logger.error(
                "Failed to store association",
                error_code="ASSOCIATION_STORE_ERROR",
                association_id=association.id,
                error=str(e),
            )
            return False

    async def get_associations(
        self, memory_id: str, association_type: Optional[str] = None, min_strength: float = 0.0, limit: int = 10
    ) -> List[Association]:
        """Get associations for a memory"""
        try:
            # Check cache first
            cache_key = f"{memory_id}_{association_type}_{min_strength}_{limit}"
            cached_associations = self.association_cache.get(cache_key)
            if cached_associations:
                return cached_associations[:limit]

            # Get from metadata store
            all_associations: List[Association] = await self.metadata_store.get_memory_associations(memory_id)

            # Apply filters (association_type and min_strength)
            filtered_associations = []
            for assoc in all_associations:
                # Filter by association type
                if association_type and assoc.association_type != association_type:
                    continue
                # Filter by minimum strength
                if assoc.strength < min_strength:
                    continue
                filtered_associations.append(assoc)

            # Apply limit and cache results
            limited_associations = filtered_associations[:limit] if filtered_associations else []
            self.association_cache.set(cache_key, limited_associations)

            return limited_associations

        except Exception as e:
            logger.error(
                "Failed to get associations", error_code="GET_ASSOCIATIONS_ERROR", memory_id=memory_id, error=str(e)
            )
            return []

    async def create_manual_association(
        self,
        source_memory_id: str,
        target_memory_id: str,
        association_type: str = "manual",
        strength: float = 1.0,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Create manual association between memories"""
        try:
            # Validate that both memories exist
            source_memory = await self.get_memory(source_memory_id)
            target_memory = await self.get_memory(target_memory_id)

            if not source_memory or not target_memory:
                logger.warning(
                    "Cannot create association - memory not found",
                    extra_data={"source_exists": source_memory is not None, "target_exists": target_memory is not None},
                )
                return False

            # Create association
            association = Association(
                source_memory_id=source_memory_id,
                target_memory_id=target_memory_id,
                association_type=association_type,
                strength=strength,
                auto_generated=False,
                metadata=metadata or {},
            )

            return await self._store_association(association)

        except Exception as e:
            logger.error(
                "Failed to create manual association",
                error_code="MANUAL_ASSOCIATION_ERROR",
                source_memory_id=source_memory_id,
                target_memory_id=target_memory_id,
                error=str(e),
            )
            return False

    async def delete_association(self, association_id: str) -> bool:
        """Delete an association"""
        try:
            # Remove from graph store
            success = await self.graph_store.remove_association_edge(association_id)
            if not success:
                logger.warning(f"Failed to remove association from graph: {association_id}")

            # Remove from metadata store
            success = await self.metadata_store.delete_association(association_id)
            if not success:
                logger.warning(f"Failed to remove association from metadata: {association_id}")
                return False

            # Remove from cache
            self.association_cache.delete(association_id)

            logger.info("Association deleted successfully", extra_data={"association_id": association_id})

            return True

        except Exception as e:
            logger.error(
                "Failed to delete association",
                error_code="DELETE_ASSOCIATION_ERROR",
                association_id=association_id,
                error=str(e),
            )
            return False

    async def update_association_strength(self, association_id: str, new_strength: float) -> bool:
        """Update association strength"""
        try:
            # For now, we use a workaround by recreating the association
            # This is not ideal but works until proper update method is implemented
            logger.warning(f"Association strength update not implemented for {association_id}")
            return False  # Placeholder - not implemented yet

        except Exception as e:
            logger.error(
                "Failed to update association strength",
                error_code="UPDATE_ASSOCIATION_ERROR",
                association_id=association_id,
                error=str(e),
            )
            return False

    async def get_related_memories(
        self, memory_id: str, max_depth: int = 2, min_strength: float = 0.5, limit: int = 10
    ) -> List[Memory]:
        """Get memories related through associations (with depth)"""
        try:
            visited = set()
            related_memories = []

            async def _traverse(current_id: str, depth: int) -> None:
                if depth > max_depth or current_id in visited:
                    return

                visited.add(current_id)

                # Get direct associations
                associations = await self.get_associations(current_id, min_strength=min_strength)

                for association in associations:
                    # Get the other memory in the association
                    other_id = (
                        association.target_memory_id
                        if association.source_memory_id == current_id
                        else association.source_memory_id
                    )

                    if other_id not in visited:
                        other_memory = await self.get_memory(other_id)
                        if other_memory:
                            related_memories.append(other_memory)
                            # Stop if we reached the limit
                            if len(related_memories) >= limit:
                                return

                        # Recursive traversal
                        if depth < max_depth:
                            await _traverse(other_id, depth + 1)

            await _traverse(memory_id, 0)
            return related_memories[:limit]

        except Exception as e:
            logger.error(
                "Failed to get related memories",
                error_code="GET_RELATED_MEMORIES_ERROR",
                memory_id=memory_id,
                error=str(e),
            )
            return []

    async def rebuild_associations(self, scope: Optional[str] = None, min_similarity: float = 0.7) -> int:
        """Rebuild all automatic associations for memories in scope"""
        try:
            # Get all memories in scope
            if scope:
                memories = await self.metadata_store.get_memories_by_scope(scope)
            else:
                memories = await self.metadata_store.get_all_memories()

            rebuilt_count = 0

            for memory in memories:
                # Delete existing auto-generated associations
                existing_associations = await self.get_associations(memory.id)
                for assoc in existing_associations:
                    if assoc.auto_generated:
                        await self.delete_association(assoc.id)

                # Generate new associations
                memory_embedding = await self.vector_store.get_embedding(memory.id)
                if memory_embedding:
                    await self._auto_associate_memory(memory, memory_embedding)
                    rebuilt_count += 1

            logger.info(
                "Association rebuild completed",
                extra_data={"scope": scope, "rebuilt_count": rebuilt_count, "total_memories": len(memories)},
            )

            return rebuilt_count

        except Exception as e:
            logger.error(
                "Failed to rebuild associations", error_code="REBUILD_ASSOCIATIONS_ERROR", scope=scope, error=str(e)
            )
            return 0
