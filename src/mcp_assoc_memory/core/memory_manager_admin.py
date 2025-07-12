"""
Memory manager administrative functions - statistics, visualization, and bulk operations
Handles system administration, monitoring, and maintenance operations
"""

import asyncio
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..models.memory import Memory
from ..utils.logging import get_memory_logger

if TYPE_CHECKING:
    from ..storage.base import BaseGraphStore, BaseMetadataStore, BaseVectorStore
    from ..utils.cache import LRUCache

logger = get_memory_logger(__name__)


class MemoryManagerAdmin:
    """Administrative and management functions mixin - requires MemoryManagerCore inheritance"""

    # Type annotations for inherited attributes
    metadata_store: "BaseMetadataStore"
    vector_store: "BaseVectorStore"
    graph_store: "BaseGraphStore"
    memory_cache: "LRUCache"
    association_cache: "LRUCache"

    # Method stubs for inherited methods
    async def update_memory(self, memory_id: str, **kwargs: Any) -> Optional[Memory]:
        """Stub - implemented in MemoryManagerCore"""
        raise NotImplementedError("This method should be inherited from MemoryManagerCore")

    async def get_associations(self, memory_id: str, **kwargs: Any) -> List[Any]:
        """Stub - implemented in MemoryManagerAssociations"""
        raise NotImplementedError("This method should be inherited from MemoryManagerAssociations")

    async def check_content_duplicate(self, content: str, **kwargs: Any) -> Optional[Memory]:
        """Stub - implemented in MemoryManagerCore"""
        raise NotImplementedError("This method should be inherited from MemoryManagerCore")

    async def store_memory(self, content: str, **kwargs: Any) -> Memory:
        """Stub - implemented in MemoryManagerCore"""
        raise NotImplementedError("This method should be inherited from MemoryManagerCore")

    async def create_manual_association(self, **kwargs: Any) -> bool:
        """Stub - implemented in MemoryManagerAssociations"""
        raise NotImplementedError("This method should be inherited from MemoryManagerAssociations")

    async def memory_map(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """Get memory map (visualization data)"""
        try:
            memories = await self.metadata_store.get_memories_by_scope(scope)
            nodes = [
                {
                    "id": m.id,
                    "label": m.content[:32],
                    "category": m.category,
                    "scope": m.scope,
                }
                for m in memories
            ]
            edges = await self.graph_store.get_all_association_edges(scope)
            return {"nodes": nodes, "edges": edges}
        except Exception as e:
            logger.error(f"memory_map generation error: {e}")
            return {"error": str(e)}

    async def scope_graph(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """Get scope graph structure"""
        try:
            graph = await self.graph_store.export_graph(scope)
            return graph
        except Exception as e:
            logger.error(f"scope_graph generation error: {e}")
            return {"error": str(e)}

    async def timeline(self, scope: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get memory timeline"""
        try:
            memories = await self.metadata_store.get_memories_by_scope(scope)

            # Sort by creation time
            sorted_memories = sorted(memories, key=lambda m: m.created_at, reverse=True)[:limit]

            timeline_data = []
            for memory in sorted_memories:
                timeline_data.append(
                    {
                        "id": memory.id,
                        "content": memory.content[:100],
                        "scope": memory.scope,
                        "category": memory.category,
                        "created_at": memory.created_at.isoformat(),
                        "tags": memory.tags,
                    }
                )

            return timeline_data
        except Exception as e:
            logger.error(f"Timeline generation error: {e}")
            return []

    async def category_chart(self, scope: Optional[str] = None) -> Dict[str, int]:
        """Get category distribution chart data"""
        try:
            memories = await self.metadata_store.get_memories_by_scope(scope)
            category_counts: Dict[str, int] = {}

            for memory in memories:
                category = memory.category or "uncategorized"
                category_counts[category] = category_counts.get(category, 0) + 1

            return category_counts
        except Exception as e:
            logger.error(f"Category chart generation error: {e}")
            return {}

    async def stats_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive statistics dashboard"""
        try:
            # Get basic statistics
            stats = await self.get_statistics()

            # Get category distribution
            categories = await self.category_chart()

            # Get recent activity
            recent_memories = await self.timeline(limit=10)

            return {
                "statistics": stats,
                "categories": categories,
                "recent_activity": recent_memories,
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Stats dashboard generation error: {e}")
            return {"error": str(e)}

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            # Cache hit rates
            memory_cache_stats = {
                "size": len(self.memory_cache.cache),
                "max_size": self.memory_cache.capacity,
                "hit_rate": getattr(self.memory_cache, "hit_rate", 0.0),
            }

            association_cache_stats = {
                "size": len(self.association_cache.cache),
                "max_size": self.association_cache.capacity,
                "hit_rate": getattr(self.association_cache, "hit_rate", 0.0),
            }

            # Store health checks
            health_checks = await asyncio.gather(
                self.vector_store.health_check(),
                self.metadata_store.health_check(),
                self.graph_store.health_check(),
                return_exceptions=True,
            )

            return {
                "cache": {"memory_cache": memory_cache_stats, "association_cache": association_cache_stats},
                "stores": {
                    "vector_store": health_checks[0] if not isinstance(health_checks[0], Exception) else False,
                    "metadata_store": health_checks[1] if not isinstance(health_checks[1], Exception) else False,
                    "graph_store": health_checks[2] if not isinstance(health_checks[2], Exception) else False,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Performance metrics error: {e}")
            return {"error": str(e)}

    async def move_memories_to_scope(
        self, source_scope: Optional[str] = None, target_scope: Optional[str] = None
    ) -> int:
        """Move memories from source scope to target scope"""
        try:
            if not target_scope:
                raise ValueError("Target scope is required")

            # Get memories in source scope
            memories = await self.metadata_store.get_memories_by_scope(source_scope)
            moved_count = 0

            for memory in memories:
                # Update memory scope
                success = await self.update_memory(memory.id, metadata={"scope": target_scope})
                if success:
                    moved_count += 1

            logger.info(
                "Scope migration completed",
                extra_data={
                    "source_scope": source_scope,
                    "target_scope": target_scope,
                    "moved_count": moved_count,
                    "total_memories": len(memories),
                },
            )

            return moved_count
        except Exception as e:
            logger.error(f"Scope migration error: {e}")
            return 0

    async def batch_update_memories(
        self, scope: Optional[str] = None, update_fields: Optional[Dict[str, Any]] = None
    ) -> int:
        """Batch update memories in scope"""
        try:
            if not update_fields:
                return 0

            memories = await self.metadata_store.get_memories_by_scope(scope)
            updated_count = 0

            for memory in memories:
                success = await self.update_memory(memory.id, **update_fields)
                if success:
                    updated_count += 1

            logger.info(
                "Batch update completed",
                extra_data={
                    "scope": scope,
                    "update_fields": list(update_fields.keys()),
                    "updated_count": updated_count,
                    "total_memories": len(memories),
                },
            )

            return updated_count
        except Exception as e:
            logger.error(f"Batch update error: {e}")
            return 0

    async def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            # Execute health checks in parallel
            vector_health, metadata_health, graph_health = await asyncio.gather(
                self.vector_store.health_check(), self.metadata_store.health_check(), self.graph_store.health_check()
            )

            # Cache statistics
            cache_stats = {
                "memory_cache": {"size": len(self.memory_cache.cache), "max_size": self.memory_cache.capacity},
                "association_cache": {
                    "size": len(self.association_cache.cache),
                    "max_size": self.association_cache.capacity,
                },
            }

            # Store health
            store_health = {
                "vector_store": vector_health,
                "metadata_store": metadata_health,
                "graph_store": graph_health,
            }

            # Get memory counts
            total_memories = await self.metadata_store.get_memory_count()
            total_associations = await self.metadata_store.get_association_count()

            return {
                "total_memories": total_memories,
                "total_associations": total_associations,
                "cache": cache_stats,
                "store_health": store_health,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Statistics error: {e}")
            return {"error": str(e)}

    async def get_memory_stats(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed memory statistics for scope"""
        try:
            memories = await self.metadata_store.get_memories_by_scope(scope)

            # Calculate statistics
            total_count = len(memories)
            total_content_length = sum(len(m.content) for m in memories)
            avg_content_length = total_content_length / total_count if total_count > 0 else 0

            # Category distribution
            categories: Dict[str, int] = {}
            for memory in memories:
                cat = memory.category or "uncategorized"
                categories[cat] = categories.get(cat, 0) + 1

            # Tag distribution
            tags: Dict[str, int] = {}
            for memory in memories:
                for tag in memory.tags:
                    tags[tag] = tags.get(tag, 0) + 1

            return {
                "scope": scope,
                "total_memories": total_count,
                "total_content_length": total_content_length,
                "average_content_length": avg_content_length,
                "categories": categories,
                "top_tags": dict(sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10]),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Memory stats error: {e}")
            return {"error": str(e)}

    async def export_memories(
        self, scope: Optional[str] = None, include_associations: bool = True, file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export memories to file or return data"""
        try:
            # Get memories and associations
            memories = await self.metadata_store.get_memories_by_scope(scope)

            export_data = {
                "memories": [memory.to_dict() for memory in memories],
                "export_info": {
                    "scope": scope,
                    "exported_at": datetime.utcnow().isoformat(),
                    "memory_count": len(memories),
                    "include_associations": include_associations,
                },
            }

            if include_associations:
                associations = []
                for memory in memories:
                    memory_associations = await self.get_associations(memory.id)
                    associations.extend([assoc.to_dict() for assoc in memory_associations])
                export_data["associations"] = associations
                export_info = export_data["export_info"]
                if isinstance(export_info, dict):
                    export_info["association_count"] = len(associations)

            # Write to file if path provided
            if file_path:
                import json

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)

                logger.info(
                    "Memories exported to file",
                    extra_data={"file_path": file_path, "memory_count": len(memories), "scope": scope},
                )

            return export_data

        except Exception as e:
            logger.error(f"Export error: {e}")
            return {"error": str(e)}

    async def import_memories(
        self, data: Dict[str, Any], target_scope: Optional[str] = None, merge_strategy: str = "skip_duplicates"
    ) -> Dict[str, Any]:
        """Import memories from data"""
        try:
            memories_data = data.get("memories", [])
            associations_data = data.get("associations", [])

            imported_memories = 0
            imported_associations = 0
            skipped_duplicates = 0
            errors = []

            # Import memories
            for memory_data in memories_data:
                try:
                    # Adjust scope if target_scope provided
                    if target_scope:
                        memory_data["scope"] = target_scope

                    # Check for duplicates based on strategy
                    if merge_strategy == "skip_duplicates":
                        existing = await self.check_content_duplicate(
                            memory_data["content"], scope=memory_data["scope"]
                        )
                        if existing:
                            skipped_duplicates += 1
                            continue

                    # Store memory
                    memory = await self.store_memory(
                        scope=memory_data["scope"],
                        content=memory_data["content"],
                        metadata=memory_data.get("metadata"),
                        tags=memory_data.get("tags"),
                        category=memory_data.get("category"),
                        allow_duplicates=(merge_strategy != "skip_duplicates"),
                    )

                    if memory:
                        imported_memories += 1
                    else:
                        errors.append(f"Failed to import memory: {memory_data.get('id', 'unknown')}")

                except Exception as e:
                    errors.append(f"Memory import error: {str(e)}")

            # Import associations if provided
            for assoc_data in associations_data:
                try:
                    success = await self.create_manual_association(
                        source_memory_id=assoc_data["source_memory_id"],
                        target_memory_id=assoc_data["target_memory_id"],
                        association_type=assoc_data.get("association_type", "imported"),
                        strength=assoc_data.get("strength", 1.0),
                        metadata=assoc_data.get("metadata"),
                    )

                    if success:
                        imported_associations += 1
                    else:
                        errors.append(f"Failed to import association: {assoc_data.get('id', 'unknown')}")

                except Exception as e:
                    errors.append(f"Association import error: {str(e)}")

            result = {
                "imported_memories": imported_memories,
                "imported_associations": imported_associations,
                "skipped_duplicates": skipped_duplicates,
                "errors": errors,
                "total_processed": len(memories_data),
                "import_strategy": merge_strategy,
                "target_scope": target_scope,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info("Memory import completed", extra_data=result)

            return result

        except Exception as e:
            logger.error(f"Import error: {e}")
            return {"error": str(e)}

    async def change_memory_scope(self, memory_ids: List[str], new_scope: str) -> Dict[str, Any]:
        """Change scope for multiple memories"""
        try:
            successful_updates = 0
            failed_updates = 0

            for memory_id in memory_ids:
                success = await self.update_memory(memory_id, metadata={"scope": new_scope})

                if success:
                    successful_updates += 1
                else:
                    failed_updates += 1

            result = {
                "successful_updates": successful_updates,
                "failed_updates": failed_updates,
                "new_scope": new_scope,
                "total_memories": len(memory_ids),
            }

            logger.info("Scope change completed", extra_data=result)

            return result

        except Exception as e:
            logger.error(f"Scope change error: {e}")
            return {"error": str(e)}

    async def batch_delete_memories(self, criteria: Dict[str, Any]) -> int:
        """Delete memories matching criteria"""
        try:
            # This is a placeholder - implement actual criteria matching
            deleted_count = 0

            logger.warning("Batch delete not fully implemented", extra_data={"criteria": criteria})

            return deleted_count
        except Exception as e:
            logger.error(f"Batch delete error: {e}")
            return 0

    async def cleanup_database(
        self,
        remove_orphaned_embeddings: bool = True,
        remove_broken_associations: bool = True,
        vacuum_stores: bool = False,
    ) -> Dict[str, Any]:
        """Clean up database inconsistencies"""
        try:
            cleanup_results = {
                "orphaned_embeddings_removed": 0,
                "broken_associations_removed": 0,
                "vacuum_performed": vacuum_stores,
            }

            if remove_orphaned_embeddings:
                # Placeholder for orphaned embedding cleanup
                logger.info("Orphaned embeddings cleanup not implemented")

            if remove_broken_associations:
                # Placeholder for broken association cleanup
                logger.info("Broken associations cleanup not implemented")

            if vacuum_stores:
                # Placeholder for store vacuum operations
                logger.info("Store vacuum operations not implemented")

            return cleanup_results

        except Exception as e:
            logger.error(f"Database cleanup error: {e}")
            return {"error": str(e)}

    async def get_all_scopes(self) -> List[str]:
        """Get all available scopes"""
        try:
            return await self.metadata_store.get_all_scopes()
        except Exception as e:
            logger.error(f"Get all scopes error: {e}")
            return []
