"""
Core memory management operations - CRUD functionality
Handles memory storage, retrieval, updates, and deletion
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.embedding_service import EmbeddingService
from ..core.similarity import SimilarityCalculator
from ..models.memory import Memory
from ..storage.base import BaseGraphStore, BaseMetadataStore, BaseVectorStore
from ..utils.cache import LRUCache
from ..utils.logging import get_memory_logger

logger = get_memory_logger(__name__)


class MemoryManagerCore:
    """Core memory management operations"""

    def __init__(
        self,
        vector_store: BaseVectorStore,
        metadata_store: BaseMetadataStore,
        graph_store: BaseGraphStore,
        embedding_service: EmbeddingService,
        similarity_calculator: Optional[SimilarityCalculator] = None,
    ):
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        self.graph_store = graph_store
        self.embedding_service = embedding_service
        self.similarity_calculator = similarity_calculator or SimilarityCalculator()

        # Cache
        self.memory_cache = LRUCache(max_size=1000)
        self.association_cache = LRUCache(max_size=500)

        # Management lock
        self.operation_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """System initialization"""
        try:
            await asyncio.gather(
                self.vector_store.initialize(), self.metadata_store.initialize(), self.graph_store.initialize()
            )

            logger.info("Memory manager initialized successfully")

        except Exception as e:
            logger.error(
                "Failed to initialize memory manager: %s", str(e), extra={"error_code": "MEMORY_MANAGER_INIT_ERROR"}
            )
            raise

    async def close(self) -> None:
        """System cleanup"""
        try:
            await asyncio.gather(
                self.vector_store.close(), self.metadata_store.close(), self.graph_store.close(), return_exceptions=True
            )

            logger.info("Memory manager closed successfully")

        except Exception as e:
            logger.warning(
                "Error during memory manager cleanup: %s", str(e), extra={"error_code": "MEMORY_MANAGER_CLOSE_ERROR"}
            )

    async def check_content_duplicate(
        self, content: str, scope: Optional[str] = None, similarity_threshold: float = 0.95
    ) -> Optional[Memory]:
        """Check for duplicate content in the specified scope"""
        try:
            if not content or not content.strip():
                return None

            # Generate embedding for the content
            content_embedding = await self.embedding_service.get_embedding(content)
            if content_embedding is None:
                logger.warning("Failed to generate embedding for duplicate check")
                return None

            # Search for similar content in the same scope
            similar_results = await self.vector_store.search(
                content_embedding, scope=scope, limit=5, min_score=similarity_threshold
            )

            # Check each result for actual duplicate
            for memory_id, similarity_score in similar_results:
                existing_memory = await self.get_memory(memory_id)
                if existing_memory and similarity_score >= similarity_threshold:
                    logger.info(
                        "Duplicate content found",
                        extra={
                            "existing_memory_id": existing_memory.id,
                            "similarity_score": similarity_score,
                            "content_length_diff": abs(len(content) - len(existing_memory.content)),
                        },
                    )
                    return existing_memory

            return None

        except Exception as e:
            logger.warning(f"Error checking for duplicates: {e}")
            # Return None to allow storing if duplicate check fails
            return None

    async def store_memory(
        self,
        scope: str = "user/default",
        content: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        auto_associate: bool = True,
        allow_duplicates: bool = False,
        similarity_threshold: float = 0.95,
    ) -> Optional[Memory]:
        """Store memory with scope-based organization"""
        try:
            # Duplicate check (when allow_duplicates is False)
            if not allow_duplicates:
                existing_memory = await self.check_content_duplicate(content, scope, similarity_threshold)
                if existing_memory:
                    logger.info(
                        "Duplicate content detected, returning existing memory",
                        extra_data={"existing_memory_id": existing_memory.id, "content_preview": content[:50]},
                    )
                    return existing_memory

            # Add scope to metadata
            final_metadata = metadata or {}
            final_metadata["scope"] = scope

            # Create memory object
            memory = Memory(
                scope=scope,
                content=content,
                metadata=final_metadata,
                tags=tags or [],
                category=category,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
            )

            # Generate embedding vector
            embedding = await self.embedding_service.get_embedding(content)
            if embedding is None:
                logger.warning(
                    "Failed to generate embedding, storing without vector", extra_data={"memory_id": memory.id}
                )

            async with self.operation_lock:
                # Parallel storage operations for better performance
                storage_tasks = []

                # Store in vector store (if embedding available)
                if embedding is not None:
                    storage_tasks.append(self.vector_store.store_embedding(memory.id, embedding, memory.to_dict()))

                # Store in metadata store (always required)
                storage_tasks.append(self.metadata_store.store_memory(memory))

                # Add memory node to graph store
                storage_tasks.append(self.graph_store.add_memory_node(memory))

                # Execute storage operations in parallel with detailed logging
                import traceback  # Import once at the beginning
                
                try:
                    logger.info(
                        "Starting parallel storage operations",
                        extra_data={
                            "memory_id": memory.id,
                            "has_embedding": embedding is not None,
                            "storage_tasks_count": len(storage_tasks),
                            "operations": [
                                "vector_store.store_embedding" if embedding is not None else None,
                                "metadata_store.store_memory",
                                "graph_store.add_memory_node"
                            ]
                        }
                    )
                    
                    # Debug: Force print for visibility
                    print(f"DEBUG: Starting storage for memory {memory.id}, embedding={embedding is not None}, tasks={len(storage_tasks)}")
                    
                    if embedding is not None:
                        # Execute all three operations
                        print("DEBUG: Executing 3 storage tasks with embedding")
                        results = await asyncio.gather(*storage_tasks, return_exceptions=True)
                        vector_success, metadata_id, graph_success = results
                        
                        print(f"DEBUG: Results - vector:{type(vector_success)}, metadata:{type(metadata_id)}, graph:{type(graph_success)}")
                        
                        # Check for exceptions in individual operations
                        if isinstance(vector_success, Exception):
                            print(f"DEBUG: Vector store failed: {vector_success}")
                            logger.error(
                                "Vector store operation failed",
                                error_code="VECTOR_STORE_ERROR",
                                memory_id=memory.id,
                                exception=str(vector_success),
                                traceback=traceback.format_exception(type(vector_success), vector_success, vector_success.__traceback__)
                            )
                            vector_success = False
                        
                        if isinstance(metadata_id, Exception):
                            print(f"DEBUG: Metadata store failed: {metadata_id}")
                            logger.error(
                                "Metadata store operation failed",
                                error_code="METADATA_STORE_ERROR",
                                memory_id=memory.id,
                                exception=str(metadata_id),
                                traceback=traceback.format_exception(type(metadata_id), metadata_id, metadata_id.__traceback__)
                            )
                            return None  # Metadata store is critical
                        
                        if isinstance(graph_success, Exception):
                            print(f"DEBUG: Graph store failed: {graph_success}")
                            logger.error(
                                "Graph store operation failed",
                                error_code="GRAPH_STORE_ERROR",
                                memory_id=memory.id,
                                exception=str(graph_success),
                                traceback=traceback.format_exception(type(graph_success), graph_success, graph_success.__traceback__)
                            )
                            graph_success = False
                    else:
                        # No vector storage needed - only metadata and graph
                        print("DEBUG: Executing 2 storage tasks without embedding")
                        results = await asyncio.gather(*storage_tasks, return_exceptions=True)
                        metadata_id, graph_success = results
                        vector_success = True  # No vector operation, consider success
                        
                        print(f"DEBUG: Results - metadata:{type(metadata_id)}, graph:{type(graph_success)}")
                        
                        if isinstance(metadata_id, Exception):
                            print(f"DEBUG: Metadata store failed (no vector): {metadata_id}")
                            logger.error(
                                "Metadata store operation failed (no vector)",
                                error_code="METADATA_STORE_ERROR",
                                memory_id=memory.id,
                                exception=str(metadata_id),
                                traceback=traceback.format_exception(type(metadata_id), metadata_id, metadata_id.__traceback__)
                            )
                            return None  # Metadata store is critical
                        
                        if isinstance(graph_success, Exception):
                            print(f"DEBUG: Graph store failed (no vector): {graph_success}")
                            logger.error(
                                "Graph store operation failed (no vector)",
                                error_code="GRAPH_STORE_ERROR",
                                memory_id=memory.id,
                                exception=str(graph_success),
                                traceback=traceback.format_exception(type(graph_success), graph_success, graph_success.__traceback__)
                            )
                            graph_success = False
                    
                    print(f"DEBUG: Final results - vector:{vector_success}, metadata:{metadata_id}, graph:{graph_success}")
                    
                    logger.info(
                        "Parallel storage operations completed",
                        extra_data={
                            "memory_id": memory.id,
                            "vector_success": vector_success,
                            "metadata_success": bool(metadata_id),
                            "graph_success": graph_success,
                            "metadata_id": str(metadata_id) if metadata_id else "None"
                        }
                    )
                    
                except Exception as e:
                    tb = traceback.format_exc()
                    logger.error(
                        "Unexpected error in parallel storage operations",
                        error_code="PARALLEL_STORAGE_UNEXPECTED_ERROR",
                        memory_id=memory.id,
                        exception=str(e),
                        traceback=tb,
                        has_embedding=embedding is not None,
                        storage_tasks_count=len(storage_tasks)
                    )
                    return None

                # Validate results
                if not metadata_id:
                    logger.error(
                        "Failed to store in metadata store", error_code="METADATA_STORE_ERROR", memory_id=memory.id
                    )
                    return None

                if embedding is not None and not vector_success:
                    logger.warning("Failed to store in vector store", extra_data={"memory_id": memory.id})

                if not graph_success:
                    logger.warning("Failed to add to graph store", extra_data={"memory_id": memory.id})

                # Store in cache
                self.memory_cache.set(memory.id, memory)

                logger.info(
                    "Memory stored successfully",
                    extra_data={
                        "memory_id": memory.id,
                        "scope": scope,
                        "content_length": len(content),
                        "has_embedding": embedding is not None,
                    },
                )

                return memory

        except Exception as e:
            import traceback

            tb = traceback.format_exc()
            logger.error(
                "Failed to store memory",
                error_code="MEMORY_STORE_ERROR",
                scope=scope,
                content_length=len(content),
                error=str(e),
                traceback=tb,
            )
            return None

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory by ID"""
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

                # Update access count
                memory.access_count += 1
                memory.accessed_at = datetime.utcnow()

                return memory

            return None

        except Exception as e:
            logger.error("Failed to get memory", error_code="MEMORY_GET_ERROR", memory_id=memory_id, error=str(e))
            return None

    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        scope: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        preserve_associations: bool = True,
    ) -> Optional[Memory]:
        """Update existing memory"""
        try:
            # Get existing memory
            existing_memory = await self.get_memory(memory_id)
            if not existing_memory:
                logger.warning(f"Memory not found for update: {memory_id}")
                return None

            # Prepare updated values and track changes
            update_data = {}
            updated_metadata = existing_memory.metadata
            if metadata is not None:
                # Merge with existing metadata
                updated_metadata = existing_memory.metadata.copy()
                updated_metadata.update(metadata)

            if content is not None:
                update_data["content"] = content
                # Regenerate embedding if content changed
                new_embedding = await self.embedding_service.get_embedding(content)
                if new_embedding is not None:
                    update_data["embedding"] = new_embedding

            if scope is not None:
                update_data["scope"] = scope

            if tags is not None:
                update_data["tags"] = tags

            if category is not None:
                update_data["category"] = category

            # Update timestamp
            update_data["updated_at"] = datetime.utcnow()

            async with self.operation_lock:
                # Create updated memory object
                updated_memory_obj = Memory(
                    id=existing_memory.id,
                    scope=scope if scope is not None else existing_memory.scope,
                    content=content if content is not None else existing_memory.content,
                    metadata=updated_metadata if metadata is not None else existing_memory.metadata,
                    tags=tags if tags is not None else existing_memory.tags,
                    category=category if category is not None else existing_memory.category,
                    user_id=existing_memory.user_id,
                    project_id=existing_memory.project_id,
                    session_id=existing_memory.session_id,
                    created_at=existing_memory.created_at,
                    updated_at=datetime.utcnow(),
                    accessed_at=existing_memory.accessed_at,
                    access_count=existing_memory.access_count,
                    embedding=update_data.get("embedding", existing_memory.embedding),
                )

                # Update metadata store
                success = await self.metadata_store.update_memory(updated_memory_obj)
                if not success:
                    return None

                # Update vector store if embedding changed
                if "embedding" in update_data:
                    # Delete old embedding and store new one
                    await self.vector_store.delete_embedding(memory_id)
                    await self.vector_store.store_embedding(
                        memory_id, update_data["embedding"], updated_memory_obj.to_dict()
                    )

                # Update graph store - remove and re-add node with updated data
                updated_memory = await self.get_memory(memory_id)
                if updated_memory:
                    await self.graph_store.remove_memory_node(memory_id)
                    await self.graph_store.add_memory_node(updated_memory)

                # Clear cache to force reload
                self.memory_cache.delete(memory_id)

                logger.info(
                    "Memory updated successfully",
                    extra_data={"memory_id": memory_id, "updated_fields": list(update_data.keys())},
                )

                return await self.get_memory(memory_id)

        except Exception as e:
            logger.error("Failed to update memory", error_code="MEMORY_UPDATE_ERROR", memory_id=memory_id, error=str(e))
            return None

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory and all associated data"""
        try:
            async with self.operation_lock:
                # Remove from all stores
                results = await asyncio.gather(
                    self.vector_store.delete_embedding(memory_id),
                    self.metadata_store.delete_memory(memory_id),
                    self.graph_store.remove_memory_node(memory_id),
                    return_exceptions=True,
                )

                # Check if any operation failed
                success = all(
                    result is True or result is None for result in results if not isinstance(result, Exception)
                )

                if success:
                    # Clear from cache
                    self.memory_cache.delete(memory_id)

                    logger.info("Memory deleted successfully", extra_data={"memory_id": memory_id})
                else:
                    logger.warning(
                        "Some delete operations failed",
                        extra_data={"memory_id": memory_id, "results": [str(r) for r in results]},
                    )

                return success

        except Exception as e:
            logger.error("Failed to delete memory", error_code="MEMORY_DELETE_ERROR", memory_id=memory_id, error=str(e))
            return False

    async def store_memories_batch(
        self,
        memories_data: List[Dict[str, Any]],
        auto_associate: bool = True,
        allow_duplicates: bool = False,
        similarity_threshold: float = 0.95,
    ) -> List[Optional[Memory]]:
        """Store multiple memories in batch for improved performance"""
        try:
            results = []

            # Process in smaller batches to avoid overwhelming the system
            batch_size = 10
            for i in range(0, len(memories_data), batch_size):
                batch = memories_data[i : i + batch_size]

                # Prepare batch data
                memory_objects = []
                embeddings = []

                for memory_data in batch:
                    # Extract data with defaults
                    scope = memory_data.get("scope", "user/default")
                    content = memory_data.get("content", "")
                    metadata = memory_data.get("metadata")
                    tags = memory_data.get("tags")
                    category = memory_data.get("category")
                    user_id = memory_data.get("user_id")
                    project_id = memory_data.get("project_id")
                    session_id = memory_data.get("session_id")

                    # Skip if duplicate check fails
                    if not allow_duplicates:
                        existing_memory = await self.check_content_duplicate(content, scope, similarity_threshold)
                        if existing_memory:
                            results.append(existing_memory)
                            continue

                    # Create memory object
                    final_metadata = metadata or {}
                    final_metadata["scope"] = scope

                    memory = Memory(
                        scope=scope,
                        content=content,
                        metadata=final_metadata,
                        tags=tags or [],
                        category=category,
                        user_id=user_id,
                        project_id=project_id,
                        session_id=session_id,
                    )

                    # Generate embedding
                    embedding = await self.embedding_service.get_embedding(content)

                    memory_objects.append(memory)
                    embeddings.append(embedding)

                # Batch storage operations
                async with self.operation_lock:
                    # Store all memories in parallel batch operations
                    batch_tasks = []

                    for memory, embedding in zip(memory_objects, embeddings):
                        storage_tasks = []

                        # Vector store
                        if embedding is not None:
                            storage_tasks.append(
                                self.vector_store.store_embedding(memory.id, embedding, memory.to_dict())
                            )

                        # Metadata store
                        storage_tasks.append(self.metadata_store.store_memory(memory))

                        # Graph store
                        storage_tasks.append(self.graph_store.add_memory_node(memory))

                        batch_tasks.append(asyncio.gather(*storage_tasks))

                    # Execute all batch operations
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                    # Process results and update cache
                    for memory, batch_result in zip(memory_objects, batch_results):
                        if isinstance(batch_result, Exception):
                            logger.error(
                                "Failed to store memory in batch",
                                error_code="BATCH_STORAGE_ERROR",
                                memory_id=memory.id,
                                exception=str(batch_result),
                            )
                            results.append(None)
                        else:
                            # Cache successful memories
                            self.memory_cache.set(memory.id, memory)
                            results.append(memory)

                            logger.info(
                                "Memory stored successfully in batch",
                                extra_data={"memory_id": memory.id, "scope": memory.scope},
                            )

            return results

        except Exception as e:
            logger.error("Batch memory storage failed", error_code="BATCH_STORAGE_FAILED", exception=str(e))
            return [None] * len(memories_data)
