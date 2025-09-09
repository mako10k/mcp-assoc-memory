"""
Memory management tools for MCP Associative Memory Server
"""

import base64
import binascii
import gzip
import json
import traceback  # Add missing import
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import Context

from ...config import get_config
from ...core.memory_manager import MemoryManager
from ...core.singleton_memory_manager import get_or_create_memory_manager
from ..models import (
    DiversifiedSearchRequest,
    Memory,
    MemoryDiscoverAssociationsRequest,
    MemoryExportRequest,
    MemoryImportRequest,
    MemoryImportResponse,
    MemoryListAllRequest,
    MemoryManageRequest,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
    MemoryStoreRequest,
    MemoryStoreResponse,
    MemorySyncRequest,
    MemoryUpdateRequest,
    PaginationInfo,
    UnifiedSearchRequest,
)
from ..models.common import CommonToolParameters, ResponseBuilder, ResponseLevel
from ..models.responses import Association, SearchResultWithAssociations
from ..processing import process_tool_response
from .export_tools import handle_memory_export

# Global references (will be set by server.py)
memory_manager: Optional[MemoryManager] = None
memory_storage: Optional[Dict[str, Any]] = None
persistence = None
_initialized = False


def set_dependencies(mm: MemoryManager, ms: Dict[str, Any], p: Any) -> None:
    """Set global dependencies from server.py"""
    global memory_manager, memory_storage, persistence, _initialized
    memory_manager = mm
    memory_storage = ms
    persistence = p
    # Reset initialization flag when dependencies are updated
    _initialized = False


def get_local_memory_manager() -> Optional[MemoryManager]:
    """Get the current local memory manager instance (for backward compatibility)"""
    return memory_manager


async def ensure_initialized() -> MemoryManager:
    """Ensure memory manager is initialized using singleton pattern"""
    global _initialized, memory_manager

    # Always get from singleton pattern
    memory_manager = await get_or_create_memory_manager()

    # If memory_manager is still None, we cannot proceed with advanced operations
    if memory_manager is None:
        raise RuntimeError(
            "Memory manager is not initialized and could not be created dynamically. "
            "This suggests a configuration or dependency issue."
        )

    # Initialize if needed
    if not _initialized:
        try:
            await memory_manager.initialize()
            _initialized = True
            # Verify storage initialization properly
            if not hasattr(memory_manager, "vector_store"):
                raise RuntimeError("Vector store not initialized after initialization")
        except Exception as e:
            # Reset flag to allow retry
            _initialized = False
            raise RuntimeError(f"Memory manager initialization failed: {e}")

    return memory_manager


async def handle_memory_store(request: MemoryStoreRequest, ctx: Context) -> Dict[str, Any]:
    """Store a memory with pre-registration duplicate checking"""
    # Early validation - fail fast
    if not request.content or not request.content.strip():
        error_msg = "Content cannot be empty"
        await ctx.error(error_msg)
        return ResponseBuilder.build_response(
            request.response_level, {"success": False, "message": error_msg, "memory_id": None}
        )

    try:
        # Get memory manager with early None check
        memory_manager = await ensure_initialized()
        if memory_manager is None:
            raise RuntimeError("Memory manager is None after initialization")

        await ctx.info(f"Storing: {request.content[:50]}... in scope: {request.scope}")
        await ctx.info(
            f"DEBUG: duplicate_threshold = {request.duplicate_threshold} (type: {type(request.duplicate_threshold)})"
        )

        # Pre-registration duplicate check if threshold specified
        if request.duplicate_threshold is not None:
            await ctx.info(f"Checking for duplicates with threshold: {request.duplicate_threshold}")
            try:
                # Use the same search method as handle_memory_search for consistency
                search_results = await memory_manager.search_memories(
                    query=request.content,
                    scope=None,  # Search across all scopes for duplicates
                    limit=5,
                    min_score=0.1,  # Low threshold to find potential duplicates
                )

                await ctx.info(f"DEBUG: Found {len(search_results)} search results")
                for i, result in enumerate(search_results):
                    # Handle both result formats for compatibility
                    if hasattr(result, "memory"):
                        # SearchResultWithAssociations format
                        memory = result.memory
                        similarity = result.similarity_score  # type: ignore
                    else:
                        # Dict format
                        memory = result["memory"]
                        similarity = result["similarity"]
                    await ctx.info(f"DEBUG: Result {i}: ID={memory.id}, similarity={similarity}")

                # Check if any result exceeds the duplicate threshold
                for result in search_results:
                    # Handle both result formats for compatibility
                    if hasattr(result, "memory"):
                        memory = result.memory
                        similarity = result.similarity_score  # type: ignore
                    else:
                        memory = result["memory"]
                        similarity = result["similarity"]

                    await ctx.info(
                        f"DEBUG: Comparing {similarity} >= {request.duplicate_threshold}: {similarity >= request.duplicate_threshold}"
                    )
                    if similarity >= request.duplicate_threshold:
                        duplicate_candidate = {
                            "memory_id": memory.id,
                            "similarity_score": similarity,
                            "content_preview": memory.content[:100] + ("..." if len(memory.content) > 100 else ""),
                            "scope": memory.scope,
                            "created_at": memory.created_at.isoformat(),
                        }

                        error_msg = f"Duplicate content detected (similarity: {similarity:.3f} >= {request.duplicate_threshold})"
                        await ctx.warning(error_msg)

                        base_data = {"success": False, "message": error_msg, "memory_id": None}

                        full_data = {
                            "duplicate_analysis": {
                                "duplicate_found": True,
                                "duplicate_candidate": duplicate_candidate,
                                "threshold_used": request.duplicate_threshold,
                                "similarity_score": similarity,
                            }
                        }

                        return ResponseBuilder.build_response(request.response_level, base_data, None, full_data)

            except Exception as e:
                await ctx.warning(f"Failed to check for duplicates: {e}")
                # Continue with storage if duplicate check fails

        # Store memory with explicit None check
        memory = await memory_manager.store_memory(
            content=request.content,
            scope=request.scope,
            allow_duplicates=request.allow_duplicates,
            auto_associate=request.auto_associate,
        )

        # Early None check - this is the critical fix
        if memory is None:
            error_msg = "store_memory returned None - check memory manager implementation"
            await ctx.error(error_msg)
            raise RuntimeError(error_msg)

        # Success - return using proper response class
        await ctx.info(f"Successfully stored memory: {memory.id}")

        # Convert to Memory model
        memory_model = Memory(
            id=memory.id,
            content=memory.content,
            scope=memory.scope,
            tags=memory.tags or [],
            category=memory.category,
            created_at=memory.created_at,
            updated_at=memory.updated_at,
            metadata=memory.metadata or {},
        )

        # Use response level to build appropriate response
        base_data = {"success": True, "message": f"Memory stored successfully: {memory.id}", "memory_id": memory.id}

        standard_data = {
            "scope": memory.scope,
            "associations_count": 0,  # TODO: Update when auto-association is implemented
            "created_at": memory.created_at.isoformat(),
        }

        store_full_data: dict[str, Any] = {
            "memory": memory_model.model_dump() if memory_model else None,
            "duplicate_analysis": {
                "duplicate_check_performed": request.duplicate_threshold is not None,
                "threshold_used": request.duplicate_threshold,
            },
        }

        return ResponseBuilder.build_response(request.response_level, base_data, standard_data, store_full_data)

    except Exception as e:
        error_msg = f"Failed to store memory: {str(e)}"
        await ctx.error(error_msg)

        # Use response level for error responses too
        base_data = {"success": False, "message": error_msg, "memory_id": None}

        return ResponseBuilder.build_response(request.response_level, base_data)


async def handle_memory_search(request: MemorySearchRequest, ctx: Context) -> Dict[str, Any]:
    """Search memories using semantic similarity with hierarchical scope support"""
    try:
        # Get memory manager using unified function
        manager_instance = await ensure_initialized()
        await ctx.info(
            f"Searching memories: '{request.query[:50]}...' in scope: {request.scope} "
            f"(include_child_scopes: {request.include_child_scopes})"
        )

        # Perform search using memory manager with enhanced parameters
        results = await manager_instance.search_memories(
            query=request.query,
            scope=request.scope,
            include_child_scopes=request.include_child_scopes,
            limit=request.limit,
            min_score=request.similarity_threshold,
        )

        # Format results for response
        formatted_results: List[Any] = []
        for result in results:
            memory = result["memory"]
            memory_scope = memory.metadata.get("scope", memory.scope)

            formatted_memory = {
                "memory_id": memory.id,
                "content": memory.content,
                "scope": memory_scope,
                "similarity_score": result["similarity"],
                "tags": memory.tags,
                "category": memory.category,
                "created_at": memory.created_at,
                "metadata": memory.metadata,
            }

            # Include associations if requested
            if request.include_associations:
                try:
                    associations = await manager_instance.metadata_store.get_memory_associations(memory.id)
                    formatted_memory["associations"] = [
                        {
                            "source_id": assoc.source_memory_id,
                            "target_id": assoc.target_memory_id,
                            "association_type": assoc.association_type,
                            "strength": assoc.strength,
                            "auto_generated": assoc.auto_generated,
                            "created_at": assoc.created_at,
                        }
                        for assoc in associations[:3]  # Limit to top 3 associations
                    ]
                except Exception as e:
                    await ctx.warning(f"Failed to get associations for memory {memory.id}: {e}")
                    formatted_memory["associations"] = []
            else:
                formatted_memory["associations"] = None

            # Create SearchResultWithAssociations object for proper validation
            try:
                # Create proper Memory instance for SearchResultWithAssociations
                memory_instance = Memory(
                    id=memory.id,
                    content=memory.content,
                    scope=memory_scope,
                    metadata=memory.metadata or {},
                    tags=memory.tags or [],
                    category=memory.category,
                    created_at=memory.created_at,
                    updated_at=memory.updated_at,
                )
                search_result = SearchResultWithAssociations(
                    memory=memory_instance,
                    similarity_score=result["similarity"],
                    associations=formatted_memory.get("associations", []),
                )
                formatted_results.append(search_result)
            except Exception as e:
                await ctx.error(f"Failed to create SearchResultWithAssociations for memory {memory.id}: {e}")
                # Fallback: create minimal valid response with Memory instance
                memory_instance = Memory(
                    id=memory.id,
                    content=memory.content,
                    scope=memory_scope,
                    metadata=memory.metadata or {},
                    tags=memory.tags or [],
                    category=memory.category,
                    created_at=memory.created_at,
                    updated_at=memory.updated_at,
                )
                search_result = SearchResultWithAssociations(
                    memory=memory_instance,
                    similarity_score=result["similarity"],
                    associations=formatted_memory.get("associations", []),
                )
                formatted_results.append(search_result)

        await ctx.info(f"Found {len(formatted_results)} memories")

        # Use ResponseBuilder for level-appropriate response
        base_data = {
            "success": True,
            "message": f"Found {len(formatted_results)} memories for query: {request.query}",
            "total_count": len(formatted_results),
        }

        standard_data: dict[str, Any] = {"query": request.query, "scope": request.scope, "results": []}

        # Add level-appropriate results
        if request.response_level != ResponseLevel.MINIMAL:
            for result in formatted_results:
                memory = result.memory  # type: ignore
                if request.response_level == ResponseLevel.STANDARD:
                    # Standard: ID, scope, content preview
                    result_data = {
                        "memory_id": memory.id,
                        "scope": memory.scope,
                        "content_preview": ResponseBuilder.truncate_content(memory.content, 50),
                        "similarity_score": result.similarity_score,  # type: ignore
                    }
                else:  # FULL
                    # Full: Complete memory objects with associations
                    result_data = {
                        "memory_id": memory.id,
                        "content": memory.content,
                        "scope": memory.scope,
                        "similarity_score": result.similarity_score,  # type: ignore
                        "tags": memory.tags,
                        "category": memory.category,
                        "created_at": memory.created_at.isoformat() if memory.created_at else None,
                        "metadata": memory.metadata,
                        "associations": result.associations if request.include_associations else [],  # type: ignore
                    }
                standard_data["results"].append(result_data)

        full_data = {
            "search_metadata": {
                "scope_coverage": "hierarchical" if request.include_child_scopes else "exact",
                "similarity_threshold": request.similarity_threshold,
                "include_child_scopes": request.include_child_scopes,
                "include_associations": request.include_associations,
            }
        }

        return ResponseBuilder.build_response(request.response_level, base_data, standard_data, full_data)

    except Exception as e:
        error_message = f"Failed to search memories: {str(e)}"
        await ctx.error(error_message)

        # Use ResponseBuilder for error responses
        base_data = {"success": False, "message": error_message, "total_count": 0}

        full_data = {
            "error_details": {
                "error_type": type(e).__name__,
                "query": getattr(request, "query", "unknown"),
                "scope": getattr(request, "scope", "unknown"),
            }
        }

        return ResponseBuilder.build_response(request.response_level, base_data, None, full_data)


async def handle_diversified_search(request: DiversifiedSearchRequest, ctx: Context) -> Dict[str, Any]:
    """Handle diversified similarity search for broader knowledge exploration"""
    try:
        memory_manager = await ensure_initialized()
        await ctx.info(f"Starting diversified search: query='{request.query}', limit={request.limit}")

        # Perform diversified similarity search
        diverse_results = await memory_manager.diversified_similarity_search(
            query=request.query,
            scope=request.scope,
            limit=request.limit,
            min_score=request.min_score,
            diversity_threshold=request.diversity_threshold,
            expansion_factor=request.expansion_factor,
            max_expansion_factor=request.max_expansion_factor,
        )

        # Format results
        formatted_results = []
        for memory, similarity_score in diverse_results:
            memory_scope = memory.metadata.get("scope", memory.scope)

            formatted_memory = {
                "memory_id": memory.id,
                "content": memory.content,
                "scope": memory_scope,
                "similarity_score": similarity_score,
                "tags": memory.tags,
                "category": memory.category,
                "created_at": memory.created_at,
                "metadata": memory.metadata or {},
            }

            # Include associations if requested
            if request.include_associations:
                try:
                    # Get associations via metadata store
                    associations = await memory_manager.metadata_store.get_memory_associations(memory.id)
                    formatted_memory["associations"] = [
                        {
                            "source_id": assoc.source_memory_id,
                            "target_id": assoc.target_memory_id,
                            "association_type": assoc.association_type,
                            "strength": assoc.strength,
                            "auto_generated": assoc.auto_generated,
                            "created_at": assoc.created_at,
                        }
                        for assoc in associations[:3]  # Limit to top 3 associations
                    ]
                except Exception as e:
                    await ctx.warning(f"Failed to get associations for memory {memory.id}: {e}")
                    formatted_memory["associations"] = []
            else:
                formatted_memory["associations"] = None

            # Create MemoryResponse object for proper validation
            try:
                memory_response = MemoryResponse(**formatted_memory)
                formatted_results.append(memory_response)
            except Exception as e:
                await ctx.error(f"Failed to create MemoryResponse for memory {memory.id}: {e}")
                # Fallback: create minimal valid response
                memory_response = MemoryResponse(
                    memory_id=memory.id,
                    content=memory.content,
                    scope=memory_scope,
                    metadata=memory.metadata or {},
                    tags=memory.tags or [],
                    category=memory.category,
                    created_at=memory.created_at,
                    similarity_score=similarity_score,
                    associations=None,
                    is_duplicate=False,
                    duplicate_of=None,
                )
                formatted_results.append(memory_response)

        await ctx.info(f"Found {len(formatted_results)} diverse memories")

        return {
            "results": formatted_results,
            "query": request.query,
            "scope": request.scope,
            "total_found": len(formatted_results),
            "min_score": request.min_score,
            "diversity_threshold": request.diversity_threshold,
            "expansion_factor": request.expansion_factor,
            "search_type": "diversified",
        }

    except Exception as e:
        await ctx.error(f"Failed to perform diversified search: {e}")
        return {"error": str(e), "results": []}


async def handle_memory_get(memory_id: str, ctx: Context, include_associations: bool = True) -> Dict[str, Any]:
    """Get a specific memory by ID with optional associations"""
    try:
        memory_manager = await ensure_initialized()
        await ctx.info(f"Retrieving memory: {memory_id}")

        # Get memory
        memory = await memory_manager.get_memory(memory_id)
        if not memory:
            await ctx.warning(f"Memory not found: {memory_id}")
            return {"error": "Memory not found"}

        memory_scope = memory.metadata.get("scope", memory.scope)

        result = {
            "memory_id": memory.id,
            "content": memory.content,
            "scope": memory_scope,
            "tags": memory.tags,
            "category": memory.category,
            "created_at": memory.created_at,
            "metadata": memory.metadata,
        }

        # Include associations if requested
        if include_associations:
            try:
                # Use get_associations instead of get_related_memories to avoid inheritance issues
                associations_data = await memory_manager.get_associations(memory_id, limit=10)
                result["associations"] = [
                    {
                        "association_id": assoc.id if hasattr(assoc, "id") else str(assoc),
                        "source_id": assoc.source_memory_id if hasattr(assoc, "source_memory_id") else memory_id,
                        "target_id": assoc.target_memory_id if hasattr(assoc, "target_memory_id") else "unknown",
                        "association_type": (
                            assoc.association_type if hasattr(assoc, "association_type") else "semantic"
                        ),
                        "strength": assoc.strength if hasattr(assoc, "strength") else 0.0,
                        "auto_generated": assoc.auto_generated if hasattr(assoc, "auto_generated") else True,
                    }
                    for assoc in associations_data[:3]  # Limit to top 3 associations
                ]
            except Exception as e:
                await ctx.warning(f"Failed to get associations: {e}")
                result["associations"] = []

        await ctx.info(f"Retrieved memory: {memory_id}")
        return result

    except Exception as e:
        await ctx.error(f"Failed to get memory: {e}")
        return {"error": str(e)}


async def handle_memory_delete(memory_id: str, ctx: Context) -> Dict[str, Any]:
    """Delete a specific memory by ID"""
    try:
        memory_manager = await ensure_initialized()
        await ctx.info(f"Deleting memory: {memory_id}")

        # Check if memory exists
        memory = await memory_manager.get_memory(memory_id)
        if not memory:
            await ctx.warning(f"Memory not found: {memory_id}")
            return {"success": False, "error": "Memory not found"}

        # Delete the memory
        await memory_manager.delete_memory(memory_id)
        await ctx.info(f"Deleted memory successfully: {memory_id}")

        return {"success": True, "message": f"Memory {memory_id} deleted successfully"}

    except Exception as e:
        await ctx.error(f"Failed to delete memory: {e}")
        return {"success": False, "error": str(e)}


async def handle_memory_update(request: MemoryUpdateRequest, ctx: Context) -> MemoryResponse:
    """Update an existing memory"""
    try:
        memory_manager = await ensure_initialized()
        await ctx.info(f"Updating memory: {request.memory_id}")

        # Get existing memory
        memory = await memory_manager.get_memory(request.memory_id)
        if not memory:
            await ctx.warning(f"Memory not found: {request.memory_id}")
            return MemoryResponse(
                success=False,
                message="Memory not found",
                memory_id=request.memory_id,
                content="",
                scope="",
                created_at=datetime.now(),
            )

        # Update memory with explicit None check
        updated_memory = await memory_manager.update_memory(
            memory_id=request.memory_id,
            content=request.content,
            scope=request.scope,
            tags=request.tags,
            category=request.category,
            metadata=request.metadata,
        )

        # Critical: Check if update_memory returned None
        if updated_memory is None:
            error_msg = f"Memory update operation returned None for memory_id: {request.memory_id}"
            await ctx.error(error_msg)
            return MemoryResponse(
                success=False,
                message="Memory update failed",
                memory_id=request.memory_id,
                content="",
                scope="error",
                created_at=datetime.now(),
            )

        await ctx.info(f"Memory updated successfully: {request.memory_id}")

        return MemoryResponse(
            success=True,
            message="Memory updated successfully",
            memory_id=updated_memory.id,
            content=updated_memory.content,
            scope=updated_memory.scope,
            metadata=updated_memory.metadata,
            tags=updated_memory.tags or [],
            category=updated_memory.category,
            created_at=updated_memory.created_at,
        )

    except Exception as e:
        error_msg = f"Failed to update memory: {str(e)}"
        await ctx.error(error_msg)
        return MemoryResponse(
            success=False,
            message=error_msg,
            memory_id=request.memory_id,
            content="",
            scope="error",
            created_at=datetime.now(),
            metadata={"error": error_msg, "error_type": type(e).__name__},
        )


async def handle_memory_discover_associations(
    request: MemoryDiscoverAssociationsRequest, ctx: Context
) -> Dict[str, Any]:
    """Discover semantic associations for a specific memory"""
    try:
        await ensure_initialized()
        await ctx.info(f"Discovering associations for memory: {request.memory_id}")

        # Get memory manager using unified function
        manager = await get_or_create_memory_manager()
        if not manager:
            error_msg = "Memory manager not available"
            await ctx.error(error_msg)

            base_data = {
                "success": False,
                "message": error_msg,
                "source_memory_id": request.memory_id,
                "total_found": 0,
            }

            return ResponseBuilder.build_response(request.response_level, base_data)

        # Get the source memory
        memory = await manager.get_memory(request.memory_id)
        if not memory:
            error_msg = f"Memory not found: {request.memory_id}"
            await ctx.warning(error_msg)

            base_data = {
                "success": False,
                "message": error_msg,
                "source_memory_id": request.memory_id,
                "total_found": 0,
            }

            return ResponseBuilder.build_response(request.response_level, base_data)

        # Find similar memories with enhanced search strategy
        search_results = await manager.search_memories(
            query=memory.content,
            limit=request.limit * 3,  # Search more to account for filtering
            min_score=max(0.1, request.similarity_threshold - 0.2),  # Lower threshold for diversity
        )

        # If we didn't find enough diverse results, try with the original content plus tags
        if len(search_results) < request.limit:
            # Create enhanced query with tags and category
            enhanced_query = memory.content
            if memory.tags:
                enhanced_query += " " + " ".join(memory.tags)
            if memory.category:
                enhanced_query += " " + memory.category

            additional_results = await manager.search_memories(
                query=enhanced_query, limit=request.limit * 2, min_score=max(0.1, request.similarity_threshold - 0.3)
            )

            # Merge results (will be deduplicated later)
            search_results.extend(additional_results)

        # Filter out the source memory and format results
        associations = []
        seen_content = set()  # Track content to avoid duplicates

        for result in search_results:
            assoc_memory = result["memory"]

            # Skip the source memory itself
            if assoc_memory.id == request.memory_id:
                continue

            # Skip memories with identical content to promote diversity
            content_hash = hash(assoc_memory.content.strip().lower())
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)

            memory_scope = assoc_memory.metadata.get("scope", assoc_memory.scope)

            associations.append(
                {
                    "memory_id": assoc_memory.id,
                    "content": (
                        assoc_memory.content[:100] + "..." if len(assoc_memory.content) > 100 else assoc_memory.content
                    ),
                    "scope": memory_scope,
                    "similarity_score": result["similarity"],
                    "category": assoc_memory.category,
                    "tags": assoc_memory.tags,
                    "created_at": assoc_memory.created_at,
                }
            )

            # Break if we have enough diverse associations
            if len(associations) >= request.limit:
                break

        await ctx.info(f"Found {len(associations)} associations for memory {request.memory_id}")

        # Use ResponseBuilder for level-appropriate response
        base_data = {
            "success": True,
            "message": f"Found {len(associations)} associations for memory: {request.memory_id}",
            "source_memory_id": request.memory_id,
            "total_found": len(associations),
        }

        standard_data: dict[str, Any] = {
            "source_content_preview": ResponseBuilder.truncate_content(memory.content, 100),
            "associations": [],
        }

        # Add level-appropriate associations
        if request.response_level != ResponseLevel.MINIMAL:
            for assoc in associations:
                if request.response_level == ResponseLevel.STANDARD:
                    # Standard: ID, scope, content preview, similarity
                    assoc_data = {
                        "memory_id": assoc["memory_id"],
                        "scope": assoc["scope"],
                        "content_preview": ResponseBuilder.truncate_content(assoc["content"], 50),
                        "similarity_score": assoc["similarity_score"],
                    }
                else:  # FULL
                    # Full: Complete association objects
                    assoc_data = assoc
                standard_data["associations"].append(assoc_data)

        full_data = {
            "source_memory": {
                "memory_id": memory.id,
                "content": memory.content,
                "scope": memory.scope,
                "tags": memory.tags,
                "category": memory.category,
                "created_at": memory.created_at.isoformat() if memory.created_at else None,
                "metadata": memory.metadata,
            },
            "search_metadata": {
                "similarity_threshold": request.similarity_threshold,
                "limit": request.limit,
                "search_strategy": "enhanced_query_with_tags",
            },
        }

        return ResponseBuilder.build_response(request.response_level, base_data, standard_data, full_data)

    except Exception as e:
        error_msg = f"Failed to discover associations: {str(e)}"
        await ctx.error(error_msg)

        base_data = {"success": False, "message": error_msg, "source_memory_id": request.memory_id, "total_found": 0}

        return ResponseBuilder.build_response(request.response_level, base_data)


async def handle_memory_import(request: MemoryImportRequest, ctx: Context) -> MemoryImportResponse:
    """Import memories from file or direct data"""
    try:
        # Contract Programming: Get memory manager using singleton pattern
        memory_manager = await get_or_create_memory_manager()
        assert memory_manager is not None, "Memory manager not available for import operations"
        assert hasattr(
            memory_manager, "metadata_store"
        ), f"Memory manager missing metadata_store: {type(memory_manager)}"

        import_mode = "file" if request.file_path else "direct data"
        await ctx.info(f"Importing memories via {import_mode} with merge strategy: {request.merge_strategy}")

        # Load import data
        import_data_str = None
        import_source = ""

        if request.file_path:
            # Pattern A: File import
            file_path = await _resolve_import_path(request.file_path)

            if not Path(file_path).exists():
                raise ValueError(f"Import file not found: {file_path}")

            # Check file size
            file_size = Path(file_path).stat().st_size
            try:
                config = get_config()
                max_size_mb = (
                    config.storage.max_import_size_mb if hasattr(config.storage, "max_import_size_mb") else 100
                )
            except AttributeError:
                max_size_mb = 100  # Default 100MB limit

            if file_size > max_size_mb * 1024 * 1024:
                raise ValueError(f"Import file size ({file_size / 1024 / 1024:.1f}MB) exceeds limit ({max_size_mb}MB)")

            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            # Handle compressed files
            if file_content.startswith("# Compressed MCP Memory Export"):
                lines = file_content.split("\n", 1)
                if len(lines) > 1:
                    compressed_data = base64.b64decode(lines[1])
                    import_data_str = gzip.decompress(compressed_data).decode("utf-8")
                else:
                    raise ValueError("Invalid compressed file format")
            else:
                import_data_str = file_content

            import_source = f"file:{file_path}"

        elif request.import_data:
            # Pattern B: Direct data import
            import_data_str = request.import_data

            # Check if it's compressed (base64 encoded)
            try:
                if not import_data_str.strip().startswith("{"):
                    # Assume it's compressed
                    compressed_data = base64.b64decode(import_data_str)
                    import_data_str = gzip.decompress(compressed_data).decode("utf-8")
            except (ValueError, binascii.Error, gzip.BadGzipFile, UnicodeDecodeError):
                pass  # If decompression fails, assume it's plain JSON

            import_source = "direct_data"

        else:
            raise ValueError("Either file_path or import_data must be provided")

        # Parse JSON data
        try:
            import_data = json.loads(import_data_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data: {e}")

        # Validate data structure if requested
        validation_errors: List[str] = []
        if request.validate_data:
            is_valid = await _validate_import_data(import_data)
            if not is_valid:
                validation_errors.append("Import data validation failed")
            if validation_errors and request.validate_data:
                raise ValueError(f"Validation errors: {validation_errors}")

        # Process import
        imported_count = 0
        skipped_count = 0
        overwritten_count = 0
        imported_scopes = set()

        memories_to_import = import_data.get("memories", [])

        for memory_data in memories_to_import:
            try:
                memory_id = memory_data["memory_id"]
                original_scope = memory_data["scope"]

                # Apply scope prefix if specified
                final_scope = original_scope
                if request.target_scope_prefix:
                    final_scope = f"{request.target_scope_prefix.rstrip('/')}/{original_scope}"

                imported_scopes.add(final_scope)

                # Check for existing memory using memory manager
                existing_memory = None
                try:
                    existing_memory = await memory_manager.metadata_store.get_memory(memory_id)
                except Exception:
                    # Memory not found is acceptable for new imports
                    existing_memory = None

                if existing_memory:
                    if request.merge_strategy == "skip_duplicates":
                        skipped_count += 1
                        continue
                    elif request.merge_strategy == "overwrite":
                        # Proceed with overwrite
                        overwritten_count += 1
                    elif request.merge_strategy == "create_versions":
                        # Create new ID for version
                        memory_id = f"{memory_id}_v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    elif request.merge_strategy == "merge_metadata":
                        # Merge metadata while keeping existing content - skip for now
                        # TODO: Implement metadata merging with proper Memory object handling
                        skipped_count += 1
                        continue

                # Prepare memory for import using memory manager
                # Contract Programming: All required fields MUST be present
                assert "content" in memory_data, f"Memory data missing required 'content' field: {memory_id}"
                assert "scope" in memory_data, f"Memory data missing required 'scope' field: {memory_id}"

                # Create memory using memory manager's store_memory method
                memory_content = memory_data["content"]
                memory_scope = final_scope
                memory_metadata = memory_data.get("metadata", {})
                memory_tags = memory_data.get("tags", [])
                memory_category = memory_data.get("category")

                # Store memory using memory manager - this will handle all proper persistence
                stored_memory = await memory_manager.store_memory(
                    content=memory_content,
                    scope=memory_scope,
                    metadata=memory_metadata,
                    tags=memory_tags,
                    category=memory_category,
                )

                if stored_memory:
                    imported_count += 1
                else:
                    validation_errors.append(f"Failed to store imported memory: {memory_id}")

            except Exception as e:
                validation_errors.append(f"Failed to import memory {memory_data.get('memory_id', 'unknown')}: {e}")
                continue

        # No need for separate persistence save - memory_manager.store_memory handles it

        await ctx.info(
            f"Import completed: {imported_count} imported, {skipped_count} skipped, {overwritten_count} overwritten"
        )

        return MemoryImportResponse(
            success=True,
            message=f"Import completed: {imported_count} imported, {skipped_count} skipped",
            data={
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "overwritten_count": overwritten_count,
                "import_source": import_source,
                "merge_strategy_used": request.merge_strategy,
                "validation_errors": validation_errors,
                "imported_scopes": list(imported_scopes),
            },
            imported_count=imported_count,
            skipped_count=skipped_count,
            error_count=len(validation_errors),
            import_summary={
                "overwritten_count": overwritten_count,
                "merge_strategy_used": request.merge_strategy,
                "imported_scopes": list(imported_scopes),
                "validation_errors": validation_errors,
            },
        )

    except Exception as e:
        await ctx.error(f"Failed to import memories: {e}")
        raise


async def handle_memory_list_all(request: MemoryListAllRequest, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """List all memories with pagination and response level support"""
    try:
        await ensure_initialized()

        if ctx:
            await ctx.info(f"Retrieving memories (page {request.page}, {request.per_page} per page)...")

        # Get all memories from memory manager
        memory_mgr = await get_or_create_memory_manager()
        all_memory_objects = await memory_mgr.metadata_store.get_all_memories(limit=10000)  # type: ignore

        # Convert Memory objects to dictionaries
        all_memories: List[Dict[str, Any]] = []
        for memory in all_memory_objects:
            all_memories.append(
                {
                    "memory_id": memory.id,
                    "content": memory.content,
                    "scope": memory.scope,
                    "metadata": memory.metadata,
                    "tags": memory.tags,
                    "category": memory.category,
                    "created_at": memory.created_at,
                }
            )

        total_items = len(all_memories)

        # Calculate pagination
        total_pages = (total_items + request.per_page - 1) // request.per_page
        start_idx = (request.page - 1) * request.per_page
        end_idx = start_idx + request.per_page

        # Get page items
        page_memories = all_memories[start_idx:end_idx]
        results = []
        for memory_data in page_memories:
            try:
                # Ensure required fields exist and add defaults if missing
                memory_id = memory_data.get("memory_id", memory_data.get("id", "unknown"))
                content = memory_data.get("content", "")
                scope = memory_data.get("scope", "unknown")
                metadata = memory_data.get("metadata", {})
                tags = memory_data.get("tags", [])
                category = memory_data.get("category")
                created_at = memory_data.get("created_at", datetime.now())

                results.append(
                    MemoryResponse(
                        memory_id=memory_id,
                        content=content,
                        scope=scope,
                        metadata=metadata,
                        tags=tags,
                        category=category,
                        created_at=created_at,
                    )
                )
            except Exception as e:
                if ctx:
                    await ctx.warning(f"Skipping invalid memory data: {e}, data: {memory_data}")
                continue

        pagination = PaginationInfo(
            page=request.page,
            per_page=request.per_page,
            total_items=total_items,
            total_pages=total_pages,
            has_next=request.page < total_pages,
            has_previous=request.page > 1,
        )

        if ctx:
            await ctx.info(f"Retrieved {len(results)} memories (page {request.page}/{total_pages})")

        # Use ResponseBuilder for level-appropriate responses
        response_level = request.response_level

        base_data = {
            "success": True,
            "message": f"Retrieved {len(results)} memories (page {request.page}/{total_pages})",
            "total_count": total_items,
        }

        if response_level == ResponseLevel.MINIMAL:
            # Minimal: Only essential pagination and count
            standard_data = {"page": request.page, "per_page": request.per_page, "total_pages": total_pages}
            return ResponseBuilder.build_response(response_level, base_data, standard_data)
        elif response_level == ResponseLevel.FULL:
            # Full: Include all memory details and metadata
            standard_data = {"memories": results, "pagination": pagination}
            full_data = {
                "search_metadata": {
                    "request_type": "memory_list_all",
                    "timestamp": datetime.now().isoformat(),
                    "page_size": request.per_page,
                    "current_page": request.page,
                }
            }
            return ResponseBuilder.build_response(response_level, base_data, standard_data, full_data)
        else:
            # Standard: Balanced response with memories and pagination
            standard_data = {"memories": results, "pagination": pagination}
            return ResponseBuilder.build_response(response_level, base_data, standard_data)

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to list memories: {e}")

        response_level = getattr(request, "response_level", ResponseLevel.STANDARD)
        base_data = {"success": False, "message": f"Failed to list memories: {str(e)}", "total_count": 0}
        return ResponseBuilder.build_response(response_level, base_data)


async def handle_unified_search(request: UnifiedSearchRequest, ctx: Context) -> Dict[str, Any]:
    """Unified search handler supporting both standard and diversified search modes"""
    try:
        await ensure_initialized()
        await ctx.info(f"Unified search: mode={request.mode}, query='{request.query[:50]}...', scope={request.scope}")

        if request.mode == "standard":
            # Use standard search
            standard_request = MemorySearchRequest(
                query=request.query,
                scope=request.scope,
                include_child_scopes=request.include_child_scopes,
                limit=request.limit,
                similarity_threshold=request.similarity_threshold,
                include_associations=request.include_associations,
            )
            return await handle_memory_search(standard_request, ctx)

        elif request.mode == "diversified":
            # Use diversified search
            diversified_request = DiversifiedSearchRequest(
                query=request.query,
                scope=request.scope,
                include_associations=request.include_associations,
                limit=request.limit,
                min_score=request.min_score,
                diversity_threshold=request.diversity_threshold,
                expansion_factor=request.expansion_factor,
                max_expansion_factor=request.max_expansion_factor,
            )
            return await handle_diversified_search(diversified_request, ctx)

        else:
            await ctx.error(f"Unknown search mode: {request.mode}")
            return {
                "error": f"Unknown search mode: {request.mode}. Supported modes: 'standard', 'diversified'",
                "results": [],
                "query": request.query,
                "mode": request.mode,
                "total": 0,
            }

    except Exception as e:
        await ctx.error(f"Unified search failed: {e}")
        return {
            "error": f"Unified search failed: {str(e)}",
            "results": [],
            "query": request.query,
            "mode": request.mode,
            "total": 0,
        }


async def handle_memory_manage(request: MemoryManageRequest, ctx: Context) -> Dict[str, Any]:
    """Unified CRUD operations handler"""
    try:
        await ensure_initialized()
        await ctx.info(f"Memory manage: operation={request.operation}, memory_id={request.memory_id}")

        if request.operation == "get":
            # Delegate to existing get handler and format with ResponseBuilder
            result = await handle_memory_get(request.memory_id, ctx, request.include_associations)

            if "error" in result:
                base_data = {
                    "success": False,
                    "message": result["error"],
                    "operation": "get",
                    "memory_id": request.memory_id,
                }
                return ResponseBuilder.build_response(request.response_level, base_data)

            # Success case
            base_data = {
                "success": True,
                "message": f"Memory retrieved successfully: {request.memory_id}",
                "operation": "get",
                "memory_id": request.memory_id,
            }

            standard_data = {
                "memory": {
                    "memory_id": result["memory_id"],
                    "scope": result["scope"],
                    "content_preview": ResponseBuilder.truncate_content(result["content"], 100),
                }
            }

            full_data = {"memory": result}

            return ResponseBuilder.build_response(request.response_level, base_data, standard_data, full_data)

        elif request.operation == "update":
            # Create update request from manage request
            update_request = MemoryUpdateRequest(
                memory_id=request.memory_id,
                content=request.content,
                scope=request.scope,
                tags=request.tags,
                category=request.category,
                metadata=request.metadata,
                preserve_associations=request.preserve_associations,
            )
            response = await handle_memory_update(update_request, ctx)

            # Convert response to dict if needed
            response_dict = response.dict() if hasattr(response, "dict") else response
            if not isinstance(response_dict, dict):
                response_dict = {"success": False, "message": "Invalid response format"}

            if not response_dict.get("success", False):
                base_data = {
                    "success": False,
                    "message": response_dict.get("message", "Update failed"),
                    "operation": "update",
                    "memory_id": request.memory_id,
                }
                return ResponseBuilder.build_response(request.response_level, base_data)

            # Success case
            base_data = {
                "success": True,
                "message": f"Memory updated successfully: {request.memory_id}",
                "operation": "update",
                "memory_id": request.memory_id,
            }

            update_standard_data: dict[str, Any] = {
                "memory": {
                    "memory_id": response_dict.get("memory_id", ""),
                    "scope": response_dict.get("scope", ""),
                    "content_preview": ResponseBuilder.truncate_content(response_dict.get("content", ""), 100),
                }
            }

            update_full_data: dict[str, Any] = {"memory": response_dict}

            return ResponseBuilder.build_response(
                request.response_level, base_data, update_standard_data, update_full_data
            )

        elif request.operation == "delete":
            # Delegate to existing delete handler
            result = await handle_memory_delete(request.memory_id, ctx)

            base_data = {
                "success": result.get("success", False),
                "message": result.get("message", result.get("error", "Unknown error")),
                "operation": "delete",
                "memory_id": request.memory_id,
            }

            return ResponseBuilder.build_response(request.response_level, base_data)

        else:
            error_msg = f"Unknown operation: {request.operation}. Supported operations: 'get', 'update', 'delete'"
            await ctx.error(error_msg)

            base_data = {
                "success": False,
                "message": error_msg,
                "operation": request.operation,
                "memory_id": request.memory_id,
            }

            return ResponseBuilder.build_response(request.response_level, base_data)

    except Exception as e:
        error_msg = f"Memory manage operation failed: {str(e)}"
        await ctx.error(error_msg)

        base_data = {
            "success": False,
            "message": error_msg,
            "operation": request.operation,
            "memory_id": request.memory_id,
        }

        return ResponseBuilder.build_response(request.response_level, base_data)


async def handle_memory_sync(request: MemorySyncRequest, ctx: Context) -> Dict[str, Any]:
    """Unified import/export operations handler"""
    try:
        await ensure_initialized()
        await ctx.info(f"Memory sync: operation={request.operation}, file_path={request.file_path}")

        if request.operation == "export":
            # Create export request from sync request
            export_request = MemoryExportRequest(
                scope=request.scope,
                file_path=request.file_path,
                include_associations=request.include_associations,
                compression=request.compression,
                export_format="json",  # Default format
            )
            export_response = await handle_memory_export(export_request, ctx)

            # Use ResponseBuilder for level-appropriate response
            base_data = {
                "success": True,
                "operation": "export",
                "exported_count": export_response.get("exported_count", 0),
            }

            standard_data = {
                "file_path": request.file_path,
                "scope": request.scope,
                "include_associations": request.include_associations,
            }

            full_data = {
                "export_details": export_response,
                "compression_enabled": request.compression,
                "format": "json",
            }

            return ResponseBuilder.build_response(request.response_level, base_data, standard_data, full_data)

        elif request.operation == "import":
            # Create import request from sync request
            import_request = MemoryImportRequest(
                file_path=request.file_path,
                import_data=None,  # Will be loaded from file
                target_scope_prefix=request.scope,  # Use scope as target_scope_prefix
                merge_strategy="skip_duplicates",  # Default strategy
                validate_data=True,  # Default validation
            )
            import_response = await handle_memory_import(import_request, ctx)
            response_dict = import_response.dict() if hasattr(import_response, "dict") else import_response
            if not isinstance(response_dict, dict):
                response_dict = {"imported_count": 0, "skipped_count": 0}

            # Use ResponseBuilder for level-appropriate response
            base_data = {
                "success": True,
                "operation": "import",
                "imported_count": response_dict.get("imported_count", 0),
            }

            import_standard_data: dict[str, Any] = {
                "file_path": request.file_path,
                "target_scope": request.scope,
                "skipped_count": response_dict.get("skipped_count", 0),
            }

            import_full_data = {
                "import_details": response_dict,
                "merge_strategy": "skip_duplicates",
                "validation_enabled": True,
            }

            return ResponseBuilder.build_response(
                request.response_level, base_data, import_standard_data, import_full_data
            )

        else:
            error_msg = f"Unknown sync operation: {request.operation}. Supported operations: 'export', 'import'"
            await ctx.error(error_msg)

            base_data = {"success": False, "error": error_msg, "operation": request.operation}

            return ResponseBuilder.build_response(request.response_level, base_data)

    except Exception as e:
        error_msg = f"Memory sync operation failed: {str(e)}"
        await ctx.error(error_msg)

        base_data = {"success": False, "error": error_msg, "operation": request.operation}

        return ResponseBuilder.build_response(request.response_level, base_data)


async def _resolve_import_path(file_path: str) -> Path:
    """Resolve import file path with proper validation."""
    path = Path(file_path)
    from ...utils.paths import get_imports_dir

    # If it's a relative path, make it relative to the user data imports dir
    if not path.is_absolute():
        data_dir = get_imports_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        path = data_dir / path

    return path


async def _validate_import_data(data: Dict[str, Any]) -> bool:
    """Validate import data structure."""
    try:
        # Check required fields
        if not isinstance(data, dict):
            return False

        # Check if it has memories list
        if "memories" not in data:
            return False

        memories = data["memories"]
        if not isinstance(memories, list):
            return False

        # Validate each memory has required fields
        for memory in memories[:5]:  # Check first 5 for performance
            if not isinstance(memory, dict):
                return False
            if "content" not in memory:
                return False

        # All validations passed
        return True
    except Exception:
        # Return False if any exception occurs during validation
        return False


async def _extract_parent_scope(scope: str) -> Optional[str]:
    """Extract parent scope from a hierarchical scope string"""
    if not scope or "/" not in scope:
        return None
    return scope.rsplit("/", 1)[0]


async def _perform_hierarchical_fallback_search(
    query: str,
    original_scope: str,
    ctx: Context,
    limit: int = 5,
    similarity_threshold: float = 0.1,
    include_child_scopes: bool = False,
) -> Dict[str, Any]:
    """
    Perform hierarchical fallback search when original search returns 0 results.

    Algorithm:
    1. Search parent scope level by level
    2. Return candidates immediately when results found
    3. If no results at any parent level, perform global search

    Returns helpful suggestions even if memory_manager is not available.
    """
    # Get memory manager using unified approach
    try:
        current_memory_manager = await ensure_initialized()
        await ctx.info("Using memory manager for fallback search")
    except Exception as e:
        await ctx.warning(f"Memory manager initialization failed for fallback search: {e}")
        # Return useful manual suggestions even without advanced search
        return {
            "type": "scope_fallback",
            "original_scope": original_scope,
            "error": "Advanced fallback search unavailable - memory manager not initialized",
            "candidates": [],
            "fallback_level": 0,
            "manual_suggestions": {
                "try_parent_scope": original_scope.rsplit("/", 1)[0] if "/" in original_scope else None,
                "try_include_child_scopes": not include_child_scopes,
                "try_lower_threshold": max(0.05, similarity_threshold - 0.05),
                "try_broader_search": "Remove scope restriction for global search",
                "suggested_scopes": [
                    "work/projects",
                    "learning/programming",
                    "personal/notes",
                    original_scope.rsplit("/", 1)[0] if "/" in original_scope else "global",
                ],
            },
            "note": "Manual suggestions provided due to initialization issue",
        }

    fallback_suggestions: Dict[str, Any] = {
        "type": "scope_fallback",
        "original_scope": original_scope,
        "found_in_scope": None,
        "candidates": [],
        "fallback_level": 0,
        "search_strategy": "hierarchical",
    }

    current_scope = original_scope
    fallback_level = 0

    # Try parent scopes level by level
    while current_scope:
        parent_scope = await _extract_parent_scope(current_scope)
        if not parent_scope:
            break

        fallback_level += 1
        await ctx.info(f"Fallback search level {fallback_level}: searching in '{parent_scope}'")

        # Search in parent scope
        try:
            results = await current_memory_manager.search_memories(
                query=query,
                scope=parent_scope,
                include_child_scopes=include_child_scopes,
                limit=limit,
                min_score=similarity_threshold,
            )

            if results:
                # Found results at this level - collect scope candidates
                unique_scopes = set()
                for result in results[:limit]:
                    memory = result["memory"]
                    memory_scope = memory.metadata.get("scope", memory.scope)
                    unique_scopes.add(memory_scope)

                fallback_suggestions.update(
                    {
                        "found_in_scope": parent_scope,
                        "candidates": list(unique_scopes)[:5],  # Max 5 candidates
                        "fallback_level": fallback_level,
                        "results_count": len(results),
                    }
                )

                await ctx.info(f"Found {len(results)} results in parent scope '{parent_scope}'")
                return fallback_suggestions

        except Exception as e:
            await ctx.warning(f"Error during fallback search in scope '{parent_scope}': {e}")

        current_scope = parent_scope

    # If no results found at any parent level, try global search
    await ctx.info("No results in parent scopes, attempting global search")
    try:
        global_results = await current_memory_manager.search_memories(
            query=query,
            scope=None,  # Global search
            include_child_scopes=True,
            limit=limit,
            min_score=max(0.05, similarity_threshold - 0.05),  # Lower threshold for global
        )

        if global_results:
            unique_scopes = set()
            for result in global_results[:limit]:
                memory = result["memory"]
                memory_scope = memory.metadata.get("scope", memory.scope)
                unique_scopes.add(memory_scope)

            fallback_suggestions.update(
                {
                    "found_in_scope": "global",
                    "candidates": list(unique_scopes)[:5],
                    "fallback_level": fallback_level + 1,
                    "search_strategy": "global_fallback",
                    "results_count": len(global_results),
                    "note": "Results found via global search with relaxed threshold",
                }
            )

            await ctx.info(f"Found {len(global_results)} results via global search")
            return fallback_suggestions

    except Exception as e:
        await ctx.warning(f"Error during global fallback search: {e}")

    # No results found anywhere - provide helpful manual suggestions
    fallback_suggestions.update(
        {
            "found_in_scope": None,
            "candidates": [],
            "fallback_level": fallback_level + 1,
            "search_strategy": "no_results",
            "manual_suggestions": {
                "try_parent_scope": original_scope.rsplit("/", 1)[0] if "/" in original_scope else None,
                "try_include_child_scopes": not include_child_scopes,
                "try_lower_threshold": max(0.05, similarity_threshold - 0.05),
                "try_different_keywords": "Rephrase query with different terms",
                "suggested_scopes": [
                    "work/projects",
                    "learning/programming",
                    "personal/notes",
                    original_scope.rsplit("/", 1)[0] if "/" in original_scope else "global",
                ],
            },
            "note": "No results found - try suggestions below",
        }
    )

    await ctx.info("No results found in hierarchical or global search")
    return fallback_suggestions
