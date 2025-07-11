"""
Core memory management engine implementation
Core functionality for memory storage, search, and relationship management
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..core.embedding_service import EmbeddingService
from ..core.similarity import SimilarityCalculator
from ..models.association import Association
from ..models.memory import Memory
from ..storage.base import BaseGraphStore, BaseMetadataStore, BaseVectorStore
from ..utils.cache import LRUCache
from ..utils.logging import get_memory_logger

logger = get_memory_logger(__name__)


class MemoryManager:
    # --- Visualization, statistics, and management methods ---
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
        """Get memory timeline data"""
        try:
            memories = await self.metadata_store.get_memories_by_scope(scope, limit=limit, order_by="created_at DESC")
            return [
                {
                    "id": m.id,
                    "content": m.content,
                    "created_at": m.created_at.isoformat(),
                    "category": m.category,
                }
                for m in memories
            ]
        except Exception as e:
            logger.error(f"Timeline generation error: {e}")
            return []

    async def category_chart(self, scope: Optional[str] = None) -> Dict[str, int]:
        """Get category-wise count chart data"""
        try:
            stats = await self.metadata_store.get_memory_stats(scope)
            return stats.get("by_category", {})
        except Exception as e:
            logger.error(f"Category chart generation error: {e}")
            return {}

    async def stats_dashboard(self) -> Dict[str, Any]:
        """Get statistics dashboard data"""
        try:
            stats = await self.get_memory_stats()
            sys_stats = await self.get_statistics()
            return {"memory_stats": stats, "system_stats": sys_stats}
        except Exception as e:
            logger.error(f"Stats dashboard generation error: {e}")
            return {"error": str(e)}

    # --- Performance, operations, and extension methods ---
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics (for Phase 4)"""
        try:
            import psutil
            mem = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=0.1)
            return {
                "memory_total": mem.total,
                "memory_used": mem.used,
                "memory_percent": mem.percent,
                "cpu_percent": cpu,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Performance metrics acquisition error: {e}")
            return {"error": str(e)}

    async def move_memories_to_scope(self, source_scope: Optional[str] = None, target_scope: Optional[str] = None) -> int:
        """Bulk move memories to another scope (for operations/management)"""
        try:
            memories = await self.metadata_store.get_memories_by_scope(source_scope)
            moved = 0
            for m in memories:
                m.scope = target_scope if target_scope else "user/default"
                m.updated_at = datetime.utcnow()
                success = await self.metadata_store.update_memory(m)
                if success:
                    self.memory_cache.set(m.id, m)
                    moved += 1
            logger.info(f"Moved {moved} items from {source_scope} to {target_scope}")
            return moved
        except Exception as e:
            logger.error(f"Scope bulk move error: {e}")
            return 0

    async def batch_update_memories(self, scope: Optional[str] = None, update_fields: Optional[Dict[str, Any]] = None) -> int:
        """Bulk update memories (for management and optimization)"""
        try:
            memories = await self.metadata_store.get_memories_by_scope(scope)
            updated = 0
            for m in memories:
                for k, v in update_fields.items():
                    if hasattr(m, k):
                        setattr(m, k, v)
                m.updated_at = datetime.utcnow()
                success = await self.metadata_store.update_memory(m)
                if success:
                    self.memory_cache.set(m.id, m)
                    updated += 1
            logger.info(f"Bulk updated {updated} items ({scope})")
            return updated
        except Exception as e:
            logger.error(f"Bulk update error: {e}")
            return 0

    # --- Future extension and optimization method stubs ---
    # Example: async def reindex_all(self): ...
    # Example: async def backup_database(self): ...
    # Example: async def restore_database(self, backup_path: str): ...
    # Example: async def detect_memory_leaks(self): ...
    # Add as needed
    """Memory management engine"""

    def __init__(
        self,
        vector_store: BaseVectorStore,
        metadata_store: BaseMetadataStore,
        graph_store: BaseGraphStore,
        embedding_service: EmbeddingService,
        similarity_calculator: Optional[SimilarityCalculator] = None
    ):
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        self.graph_store = graph_store
        self.embedding_service = embedding_service
        self.similarity_calculator = (
            similarity_calculator or SimilarityCalculator()
        )

        # Cache
        self.memory_cache = LRUCache(max_size=1000)
        self.association_cache = LRUCache(max_size=500)

        # Management lock
        self.operation_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """System initialization"""
        try:
            await asyncio.gather(
                self.vector_store.initialize(),
                self.metadata_store.initialize(),
                self.graph_store.initialize()
            )

            logger.info("Memory manager initialized successfully")

        except Exception as e:
            logger.error(
                "Failed to initialize memory manager: %s",
                str(e),
                extra={"error_code": "MEMORY_MANAGER_INIT_ERROR"}
            )
            raise

    async def close(self) -> None:
        """System cleanup"""
        try:
            await asyncio.gather(
                self.vector_store.close(),
                self.metadata_store.close(),
                self.graph_store.close()
            )

            logger.info("Memory manager closed successfully")

        except Exception as e:
            logger.error(
                "Failed to close memory manager",
                error_code="MEMORY_MANAGER_CLOSE_ERROR",
                error=str(e)
            )

    async def check_content_duplicate(
        self,
        content: str,
        scope: Optional[str] = None,
        similarity_threshold: float = 0.95
    ) -> Optional[Memory]:
        """Check for duplicate content within the specified scope"""
        try:
            # Search for similar content using vector search
            search_results = await self.search_memories(
                query=content,
                scope=scope,
                limit=10,  # Check top 10 most similar
                min_score=similarity_threshold
            )
            
            # Check for exact or near-exact matches
            for result in search_results:
                existing_memory = result["memory"]
                similarity = result["similarity"]
                
                # Check for very high similarity (potential duplicate)
                if similarity >= similarity_threshold:
                    # Additional check: compare content length and key phrases
                    content_normalized = content.strip().lower()
                    existing_normalized = existing_memory.content.strip().lower()
                    
                    # If content is very similar in both similarity score and normalized form
                    if (len(content_normalized) > 10 and 
                        len(existing_normalized) > 10 and
                        abs(len(content_normalized) - len(existing_normalized)) / max(len(content_normalized), len(existing_normalized)) < 0.2):
                        
                        logger.info(
                            "Duplicate content detected",
                            extra_data={
                                "existing_memory_id": existing_memory.id,
                                "similarity_score": similarity,
                                "content_length_diff": abs(len(content) - len(existing_memory.content))
                            }
                        )
                        return existing_memory
            
            return None
            
        except Exception as e:
            logger.warning(f"Error checking for duplicates: {e}")
            # Return None to allow storing if duplicate check fails
            return None

    async def store_memory(
        self,
        scope: str = "user/default",  # Hierarchical scope for organization
        content: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        auto_associate: bool = True,
        allow_duplicates: bool = False,
        similarity_threshold: float = 0.95
    ) -> Optional[Memory]:
        """Store memory with scope-based organization"""
        try:
            # Duplicate check (when allow_duplicates is False)
            if not allow_duplicates:
                existing_memory = await self.check_content_duplicate(
                    content, 
                    scope,  # Hierarchical scope for organization
                    similarity_threshold
                )
                if existing_memory:
                    logger.info(
                        "Duplicate content detected, returning existing memory",
                        extra_data={
                            "existing_memory_id": existing_memory.id,
                            "content_preview": content[:50]
                        }
                    )
                    return existing_memory
            
            # Add scope to metadata
            final_metadata = metadata or {}
            final_metadata["scope"] = scope
            
            # Create memory object
            memory = Memory(
                scope=scope,  # Hierarchical scope for organization
                content=content,
                metadata=final_metadata,
                tags=tags or [],
                category=category,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id
            )

            # Generate embedding vector
            embedding = await self.embedding_service.get_embedding(content)
            if embedding is None:
                logger.warning(
                    "Failed to generate embedding, storing without vector",
                    extra_data={"memory_id": memory.id}
                )

            async with self.operation_lock:
                # Store in vector store
                if embedding is not None:
                    success = await self.vector_store.store_embedding(
                        memory.id,
                        embedding,
                        memory.to_dict()
                    )
                    if not success:
                        logger.warning(
                            "Failed to store in vector store",
                            extra_data={"memory_id": memory.id}
                        )

                # Store in metadata store
                metadata_id = await self.metadata_store.store_memory(memory)
                if not metadata_id:
                    logger.error(
                        "Failed to store in metadata store",
                        error_code="METADATA_STORE_ERROR",
                        memory_id=memory.id
                    )
                    return None

                # Add memory node to graph store
                graph_success = await self.graph_store.add_memory_node(memory)
                if not graph_success:
                    logger.warning(
                        "Failed to add to graph store",
                        extra_data={"memory_id": memory.id}
                    )

                # Store in cache
                self.memory_cache.set(memory.id, memory)

                # Auto-association
                if auto_associate and embedding is not None:
                    await self._auto_associate_memory(memory, embedding)

                logger.info(
                    "Memory stored successfully",
                    extra_data={
                        "memory_id": memory.id,
                        "scope": scope,  # Hierarchical scope for organization
                        "content_length": len(content),
                        "has_embedding": embedding is not None
                    }
                )

                return memory

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            try:
                with open('/tmp/mcp_memory_error.log', 'a') as f:
                    f.write('=== MEMORY_STORE_ERROR TRACEBACK ===\n')
                    f.write(tb)
                    f.write('\n')
            except Exception as file_e:
                print('Failed to write traceback to /tmp/mcp_memory_error.log:', file_e)
            logger.error(
                "Failed to store memory",
                error_code="MEMORY_STORE_ERROR",
                scope=scope,  # Hierarchical scope for organization
                content_length=len(content),
                error=str(e),
                traceback=tb
            )
            return None

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory"""
        try:
            # Check cache
            cached_memory = self.memory_cache.get(memory_id)
            if cached_memory:
                # Update access count
                cached_memory.access_count += 1
                cached_memory.accessed_at = datetime.utcnow()
                return cached_memory

            # Get from metadata store
            memory = await self.metadata_store.get_memory(memory_id)
            if memory:
                # Store in cache
                self.memory_cache.set(memory_id, memory)

                # Update access statistics
                await self.metadata_store.update_access_stats(
                    memory_id,
                    memory.access_count + 1
                )

                logger.debug(
                    "Memory retrieved",
                    extra_data={"memory_id": memory_id}
                )

            return memory

        except Exception as e:
            logger.error(
                "Failed to get memory",
                error_code="MEMORY_GET_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            return None

    async def search_memories(
        self,
        query: str,
        scope: Optional[str] = None,  # Hierarchical scope for organization
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
        similarity_threshold: float = 0.7,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search memories using scope-based organization"""
        try:
            if min_score is not None:
                similarity_threshold = min_score
            logger.info(f"[DEBUG] search_memories called with similarity_threshold={similarity_threshold!r} (min_score={min_score!r})")
            # Generate query embedding vector
            query_embedding = await self.embedding_service.get_embedding(query)
            if query_embedding is None:
                logger.warning("Failed to generate query embedding")
                return []

            # Build filter conditions
            filters = {}
            if scope:
                filters["scope"] = scope
            if user_id:
                filters["user_id"] = user_id
            if project_id:
                filters["project_id"] = project_id
            if session_id:
                filters["session_id"] = session_id
            if tags:
                filters["tags"] = tags

            # Execute vector search
            # Convert to 1D list
            if hasattr(query_embedding, 'flatten'):
                embedding_list = query_embedding.flatten().tolist()
            elif hasattr(query_embedding, 'tolist'):
                embedding_list = query_embedding.tolist()
            else:
                embedding_list = list(query_embedding) if not isinstance(query_embedding, list) else query_embedding

            vector_results = await self.vector_store.search_similar(
                embedding_list,
                scope=scope,  # Use scope directly
                limit=limit * 2,
                min_score=similarity_threshold  # Use min_score parameter
            )
            # DEBUG→INFO temporary upgrade (can be easily commented out later)
            logger.info(
                f"[DEBUG] vector_results: {[{'id': r.get('id'), 'memory_id': r.get('memory_id'), 'similarity': r.get('similarity')} for r in vector_results]}"
            )

            # Filter by similarity
            filtered_results = []
            for result in vector_results:
                logger.info(f"[DEBUG] result dump: {result!r}")
                logger.info(f"[DEBUG] similarity={result.get('similarity')!r} threshold={similarity_threshold!r}")
                if result["similarity"] >= similarity_threshold:
                    memory_id = result.get("id") or result.get("memory_id")
                    # Dump memory_id value
                    logger.info(f"[DEBUG] memory_id before check: {memory_id!r} type={type(memory_id)}")
                    if not memory_id:
                        logger.info(f"[DEBUG] Skipping result with no id: {result}")
                        continue
                    logger.info(f"[DEBUG] get_memory({memory_id}) type={type(memory_id)} repr={repr(memory_id)}")
                    memory = await self.get_memory(memory_id)
                    if not memory:
                        logger.info(f"[DEBUG] get_memory({memory_id}) returned None")
                        continue
                    filtered_results.append({
                        "memory": memory,
                        "similarity": result["similarity"],
                        "score": result.get("score", result["similarity"])
                    })

            # Limit results
            filtered_results = filtered_results[:limit]

            logger.info(
                "Memory search completed",
                extra_data={
                    "query_length": len(query),
                    "total_results": len(vector_results),
                    "filtered_results": len(filtered_results),
                    "filters": filters
                }
            )

            return filtered_results

        except Exception as e:
            import traceback
            logger.error(traceback.format_exc())
            logger.error(
                "Failed to search memories",
                error_code="MEMORY_SEARCH_ERROR",
                query_length=len(query),
                error=str(e)
            )
            return []

    # --- Graph-based get_related_memories removed (unified with find_similar_memories/semantic_search) ---

    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Update memory"""
        try:
            # Get existing memory
            memory = await self.get_memory(memory_id)
            if not memory:
                logger.warning(
                    "Memory not found for update",
                    extra_data={"memory_id": memory_id}
                )
                return False

            # Apply updates
            updated = False
            if content is not None and content != memory.content:
                memory.content = content
                updated = True

                # Generate new embedding vector
                embedding = await self.embedding_service.get_embedding(content)
                if embedding is not None:
                    await self.vector_store.store_embedding(
                        memory_id,
                        embedding,
                        memory.to_dict()
                    )

            if metadata is not None:
                memory.metadata.update(metadata)
                updated = True

            if tags is not None:
                memory.tags = tags
                updated = True

            if updated:
                memory.updated_at = datetime.utcnow()

                async with self.operation_lock:
                    # Update metadata store
                    success = await self.metadata_store.update_memory(memory)
                    if not success:
                        logger.error(
                            "Failed to update memory in metadata store",
                            error_code="METADATA_UPDATE_ERROR",
                            memory_id=memory_id
                        )
                        return False

                    # Update cache
                    self.memory_cache.set(memory_id, memory)

                    logger.info(
                        "Memory updated successfully",
                        extra_data={"memory_id": memory_id}
                    )

            return True

        except Exception as e:
            logger.error(
                "Failed to update memory",
                error_code="MEMORY_UPDATE_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory"""
        try:
            async with self.operation_lock:
                # Delete related edges
                associations = await self.metadata_store.get_memory_associations(
                    memory_id
                )
                for assoc in associations:
                    await self.graph_store.remove_association_edge(assoc.id)
                    await self.metadata_store.delete_association(assoc.id)

                # Delete from storage
                await asyncio.gather(
                    self.vector_store.delete_embedding(memory_id),
                    self.metadata_store.delete_memory(memory_id),
                    self.graph_store.remove_memory_node(memory_id)
                )

                # Delete from cache
                self.memory_cache.delete(memory_id)

                logger.info(
                    "Memory deleted successfully",
                    extra_data={"memory_id": memory_id}
                )

                return True

        except Exception as e:
            logger.error(
                "Failed to delete memory",
                error_code="MEMORY_DELETE_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            return False

    async def _auto_associate_memory(
        self,
        memory: Memory,
        embedding: np.ndarray
    ) -> None:
        """Auto-associate memory"""
        try:
            # Search for similar memories
            if hasattr(embedding, 'flatten'):
                emb_list = embedding.flatten().tolist()
            elif hasattr(embedding, 'tolist'):
                emb_list = embedding.tolist()
            else:
                emb_list = list(embedding) if not isinstance(embedding, list) else embedding
            similar_results = await self.vector_store.search_similar(
                emb_list,
                scope=memory.scope,
                limit=10
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
                        auto_generated=True
                    )

                    # Store relationship
                    await self._store_association(association)

            # DEBUG→INFO temporary upgrade
            logger.info(
                "Auto-association completed",
                extra_data={
                    "memory_id": memory.id,
                    "similar_count": len(similar_results)
                }
            )

        except Exception as e:
            logger.error(
                "Failed to auto-associate memory",
                error_code="AUTO_ASSOCIATION_ERROR",
                memory_id=memory.id,
                error=str(e)
            )

    async def _store_association(self, association: Association) -> bool:
        """Store relationship"""
        try:
            # Store in metadata store
            assoc_id = await self.metadata_store.store_association(association)
            if not assoc_id:
                return False

            # Store in graph store
            success = await self.graph_store.add_association_edge(association)
            if not success:
                # Rollback
                await self.metadata_store.delete_association(association.id)
                return False

            # Store in cache
            self.association_cache.set(association.id, association)

            return True

        except Exception as e:
            logger.error(
                "Failed to store association",
                error_code="ASSOCIATION_STORE_ERROR",
                association_id=association.id,
                error=str(e)
            )
            return False

    async def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            # Execute health checks in parallel
            vector_health, metadata_health, graph_health = await asyncio.gather(
                self.vector_store.health_check(),
                self.metadata_store.health_check(),
                self.graph_store.health_check()
            )

            # Cache statistics
            cache_stats = {
                "memory_cache": {
                    "size": len(self.memory_cache.cache),
                    "max_size": self.memory_cache.capacity
                },
                "association_cache": {
                    "size": len(self.association_cache.cache),
                    "max_size": self.association_cache.capacity
                },
                "embedding_cache": self.embedding_service.get_cache_stats()
            }

            return {
                "vector_store": vector_health,
                "metadata_store": metadata_health,
                "graph_store": graph_health,
                "cache_stats": cache_stats,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(
                "Failed to get statistics",
                error_code="STATISTICS_ERROR",
                error=str(e)
            )
            return {}

    async def get_memory_stats(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            stats = await self.metadata_store.get_memory_stats(scope)
            cache_stats = self.memory_cache.get_stats()
            embedding_stats = self.embedding_service.get_cache_stats()

            return {
                'total_memories': stats.get('total_count', 0),
                'memories_by_scope': stats.get('by_scope', {}),
                'memories_by_category': stats.get('by_category', {}),
                'total_size_bytes': stats.get('total_size', 0),
                'cache_stats': cache_stats,
                'embedding_cache_stats': embedding_stats,
                'last_updated': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Statistics acquisition error: {e}")
            return {'error': str(e)}

    async def export_memories(
        self,
        scope: Optional[str] = None,
        format_type: str = 'json'
    ) -> Dict[str, Any]:
        """Export memories"""
        try:
            memories = await self.metadata_store.get_memories_by_scope(scope)

            if format_type == 'json':
                exported_data = [memory.to_dict() for memory in memories]
            else:
                raise ValueError(f"Unsupported format: {format_type}")

            return {
                'format': format_type,
                'count': len(exported_data),
                'data': exported_data,
                'exported_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Export error: {e}")
            return {'error': str(e)}

    async def import_memories(
        self,
        data: List[Dict[str, Any]],
        scope: Optional[str] = None,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """Import memories"""
        imported_count = 0
        skipped_count = 0
        error_count = 0

        try:
            for item in data:
                try:
                    # Check existing
                    if 'id' in item and not overwrite:
                        existing = await self.get_memory(item['id'])
                        if existing:
                            skipped_count += 1
                            continue

                    # Create and store memory
                    memory = await self.store_memory(
                        scope=scope or "user/default",
                        content=item.get('content', ''),
                        metadata=item.get('metadata', {}),
                        tags=item.get('tags', []),
                        category=item.get('category')
                    )

                    if memory:
                        imported_count += 1
                    else:
                        error_count += 1

                except Exception as e:
                    logger.error(f"Import item error: {e}")
                    error_count += 1

            return {
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'error_count': error_count
            }
        except Exception as e:
            logger.error(f"Import error: {e}")
            return {'error': str(e)}

    async def change_memory_scope(
        self,
        memory_id: str,
        new_scope: Optional[str] = None
    ) -> bool:
        """Change memory scope"""
        try:
            memory = await self.get_memory(memory_id)
            if not memory:
                return False

            memory.scope = new_scope if new_scope else "user/default"
            memory.updated_at = datetime.utcnow()

            success = await self.metadata_store.update_memory(memory)
            if success:
                # Update cache
                self.memory_cache.set(memory_id, memory)
                logger.info(f"Memory scope changed: {memory_id} -> {new_scope}")

            return success
        except Exception as e:
            logger.error(f"Scope change error: {e}")
            return False

    async def batch_delete_memories(self, criteria: Dict[str, Any]) -> int:
        """Bulk delete memories"""
        try:
            deleted_count = await self.metadata_store.batch_delete_memories(criteria)

            # Also delete from cache (simple implementation)
            self.memory_cache.clear()

            logger.info(f"Bulk deletion completed: {deleted_count} items")
            return deleted_count
        except Exception as e:
            logger.error(f"Bulk deletion error: {e}")
            return 0

    async def cleanup_database(
        self,
        cleanup_orphans: bool = True,
        reindex: bool = False,
        vacuum: bool = False
    ) -> Dict[str, Any]:
        """Database cleanup"""
        try:
            result = {
                'cleanup_orphans': 0,
                'reindex_completed': False,
                'vacuum_completed': False
            }

            if cleanup_orphans:
                result['cleanup_orphans'] = await self.metadata_store.cleanup_orphans()

            if reindex:
                await self.metadata_store.reindex()
                result['reindex_completed'] = True

            if vacuum:
                await self.metadata_store.vacuum()
                result['vacuum_completed'] = True

            return result
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return {'error': str(e)}

    async def semantic_search(
        self,
        query: str,
        scope: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.7
    ) -> List[Tuple[Memory, float]]:
        """
        Traditional semantic search for focused content discovery
        
        This method performs standard similarity-based search, returning the most
        relevant memories for a given query. Best for finding specific information
        or exploring content within the same knowledge domain.
        
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
        """Tag search"""
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
            logger.error(f"時間範囲検索エラー: {e}")
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
        """高度検索"""
        try:
            # 複合検索条件でメタデータ検索
            memories = await self.metadata_store.advanced_search(
                scope=scope,
                tags=tags or [],
                category=category,
                start_date=start_date,
                end_date=end_date,
                limit=limit * 3  # より多く取得してスコアフィルタリング
            )

            if not query:
                # クエリなしの場合は時系列順
                return [(memory, 1.0) for memory in memories[:limit]]

            # 意味的類似度でフィルタリング
            query_embedding = await self.embedding_service.get_embedding(query)
            if not query_embedding:
                return [(memory, 1.0) for memory in memories[:limit]]

            scored_memories = []
            for memory in memories:
                # 記憶の埋め込みを取得
                memory_embedding = await self.vector_store.get_embedding(memory.id)
                if memory_embedding:
                    score = self.similarity_calculator.cosine_similarity(
                        query_embedding, memory_embedding
                    )
                    if score >= min_score:
                        scored_memories.append((memory, score))

            # スコア順にソート
            scored_memories.sort(key=lambda x: x[1], reverse=True)
            return scored_memories[:limit]

        except Exception as e:
            logger.error(f"高度検索エラー: {e}")
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
            # 参照記憶の埋め込みを取得
            reference_embedding = await self.vector_store.get_embedding(reference_id)
            if not reference_embedding:
                return []

            # 類似検索
            results = await self.vector_store.search(
                reference_embedding,
                scope or "user/default",
                limit + 1,  # 自分自身を除外するため+1
                min_score
            )

            # 記憶オブジェクトに変換（参照記憶を除外）
            memories_with_scores = []
            for memory_id, score in results:
                if memory_id != reference_id:
                    memory = await self.get_memory(memory_id)
                    if memory:
                        memories_with_scores.append((memory, score))

            return memories_with_scores[:limit]
        except Exception as e:
            logger.error(f"類似記憶検索エラー: {e}")
            return []

    async def diversified_similarity_search(
        self,
        query: str,
        scope: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.1,
        diversity_threshold: float = 0.8,
        expansion_factor: float = 2.5,
        max_expansion_factor: float = 5.0
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
            if hasattr(query_embedding, 'size') and query_embedding.size == 0:
                logger.warning("Empty query embedding generated for diversified search")
                return []

            # Calculate initial search size with expansion factor
            initial_search_size = max(limit * expansion_factor, limit + 10)
            initial_search_size = min(initial_search_size, 100)  # Cap at reasonable limit
            
            # Phase 1: Get initial candidate pool
            candidates = await self._get_similarity_candidates(
                query_embedding, scope, int(initial_search_size), min_score
            )
            
            if not candidates:
                logger.info("No candidates found in initial search")
                return []

            # Phase 2: Diversified selection algorithm
            selected_results = []
            exclude_set = set()
            candidate_index = 0
            
            logger.info(f"Starting diversification with {len(candidates)} candidates")
            
            while len(selected_results) < limit:
                # Check if we need more candidates
                if candidate_index >= len(candidates):
                    # Expand search with larger pool
                    expanded_size = min(
                        int(limit * max_expansion_factor), 
                        len(candidates) + limit * 2,
                        200  # Absolute maximum
                    )
                    
                    if expanded_size > len(candidates):
                        logger.info(f"Expanding candidate pool to {expanded_size}")
                        expanded_candidates = await self._get_similarity_candidates(
                            query_embedding, scope, expanded_size, min_score
                        )
                        
                        if len(expanded_candidates) <= len(candidates):
                            # No new candidates found, break
                            logger.info("No additional candidates found, stopping diversification")
                            break
                            
                        candidates = expanded_candidates
                    else:
                        # Cannot expand further
                        break

                # Get current candidate
                if candidate_index >= len(candidates):
                    break
                    
                current_candidate = candidates[candidate_index]
                memory_id = current_candidate.get("memory_id") or current_candidate.get("id")
                
                candidate_index += 1
                
                # Skip if in exclude set
                if memory_id in exclude_set:
                    continue
                
                # Get memory object
                memory = await self.get_memory(memory_id)
                if not memory:
                    continue
                
                # Add to results
                similarity_score = current_candidate.get("similarity", current_candidate.get("score", 0.0))
                selected_results.append((memory, similarity_score))
                
                # Add similar memories to exclude set for diversity
                await self._add_to_exclude_set(
                    memory, exclude_set, scope, diversity_threshold
                )
                
                logger.debug(f"Selected memory {memory_id} (similarity: {similarity_score:.3f}), "
                           f"exclude_set size: {len(exclude_set)}")

            logger.info(f"Diversified search completed: found {len(selected_results)} diverse results")
            return selected_results
            
        except Exception as e:
            logger.error(f"Diversified similarity search error: {e}")
            return []

    async def _get_similarity_candidates(
        self,
        query_embedding: Any,
        scope: Optional[str],
        limit: int,
        min_score: float
    ) -> List[Dict[str, Any]]:
        """Get similarity search candidates from vector store"""
        try:
            # Convert embedding to list format safely
            embedding_list = None
            try:
                if hasattr(query_embedding, 'flatten'):
                    embedding_list = query_embedding.flatten().tolist()
                elif hasattr(query_embedding, 'tolist'):
                    embedding_list = query_embedding.tolist()
                elif isinstance(query_embedding, (list, tuple)):
                    embedding_list = list(query_embedding)
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
                embedding_list,
                scope=scope,
                limit=limit,
                min_score=min_score
            )
            
            # Filter by minimum score
            filtered_candidates = [
                candidate for candidate in candidates 
                if candidate.get("similarity", candidate.get("score", 0.0)) >= min_score
            ]
            
            return filtered_candidates
            
        except Exception as e:
            logger.error(f"Error getting similarity candidates: {e}")
            return []

    async def _add_to_exclude_set(
        self,
        memory: Memory,
        exclude_set: set,
        scope: Optional[str],
        diversity_threshold: float
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
                min_score=diversity_threshold
            )
            
            # Add similar memory IDs to exclude set
            for similar_memory, _ in similar_memories:
                exclude_set.add(similar_memory.id)
                
        except Exception as e:
            logger.error(f"Error adding to exclude set: {e}")
