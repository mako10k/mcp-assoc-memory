"""
Memory management tools for MCP Associative Memory Server
"""

import base64
import binascii
import gzip
import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

from fastmcp import Context
from pydantic import Field

from ...config import get_config
from ...core.memory_manager import MemoryManager
from ...core.singleton_memory_manager import get_memory_manager, is_memory_manager_initialized
from ...simple_persistence import get_persistent_storage
from .export_tools import handle_memory_export
from ..dependencies import dependencies, ensure_dependencies_initialized
from ..models import (
    DiversifiedSearchRequest,
    MemoryExportRequest,
    MemoryImportRequest,
    MemoryImportResponse,
    MemoryManageRequest,
    MemoryResponse,
    MemorySearchRequest,
    MemoryStoreRequest,
    MemorySyncRequest,
    MemoryUpdateRequest,
    PaginationInfo,
    UnifiedSearchRequest,
)

# Get the config instance
config = get_config()

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


async def _get_or_create_memory_manager() -> Optional[MemoryManager]:
    """
    Get memory manager using singleton pattern with fallback to dynamic creation
    """
    global memory_manager
    
    # First try to get from singleton
    singleton_manager = await get_memory_manager()
    if singleton_manager is not None:
        memory_manager = singleton_manager  # Update local reference
        return singleton_manager
    
    # Fallback: check if local memory manager exists
    if memory_manager is not None:
        return memory_manager
    
    # Try to dynamically create memory manager if not injected
    try:
        from ...core.memory_manager import MemoryManager
        from ...storage.vector_store import ChromaVectorStore
        from ...storage.metadata_store import SQLiteMetadataStore
        from ...storage.graph_store import NetworkXGraphStore
        from ...core.embedding_service import SentenceTransformerEmbeddingService, MockEmbeddingService
        from ...core.similarity import SimilarityCalculator
        
        # Initialize storage components
        vector_store = ChromaVectorStore()
        metadata_store = SQLiteMetadataStore()
        graph_store = NetworkXGraphStore()
        
        # Use SentenceTransformerEmbeddingService for production, fallback to Mock
        try:
            embedding_service = SentenceTransformerEmbeddingService()
        except Exception:
            embedding_service = MockEmbeddingService()
        
        similarity_calculator = SimilarityCalculator()
        
        # Create memory manager
        mm = MemoryManager(
            vector_store=vector_store,
            metadata_store=metadata_store,
            graph_store=graph_store,
            embedding_service=embedding_service,
            similarity_calculator=similarity_calculator,
        )
        
        # Update global reference
        memory_manager = mm
        return mm
        
    except Exception as e:
        print(f"Failed to dynamically create memory manager: {e}")
        return None


async def ensure_initialized() -> None:
    """Ensure memory manager is initialized using singleton pattern"""
    global _initialized, memory_manager
    
    # Check if singleton is already initialized
    if is_memory_manager_initialized():
        memory_manager = await get_memory_manager()
        _initialized = True
        return
    
    # Try to get or create memory manager
    memory_manager = await _get_or_create_memory_manager()
    
    # If memory_manager is still None, we cannot proceed with advanced operations
    if memory_manager is None:
        raise RuntimeError(
            "Memory manager is not initialized and could not be created dynamically. "
            "This suggests a configuration or dependency issue."
        )
    
    if not _initialized:
        try:
            await memory_manager.initialize()
            _initialized = True
            # Verify vector store is properly initialized
            if memory_manager.vector_store.collection is None:
                raise RuntimeError("Vector store collection not initialized after initialization")
        except Exception as e:
            # Reset flag to allow retry
            _initialized = False
            raise RuntimeError(f"Memory manager initialization failed: {e}")


async def handle_memory_store(request: MemoryStoreRequest, ctx: Context) -> MemoryResponse:
    """Store a memory with full associative capabilities"""
    try:
        # Basic input validation
        if not request.content or len(request.content.strip()) == 0:
            await ctx.error("Content cannot be empty")
            return MemoryResponse(
                memory_id="error",
                content="",
                scope="error",
                created_at=datetime.now(),
                metadata={"error": "Content cannot be empty", "suggestions": ["Provide non-empty content for the memory"]}
            )
        
        if not request.scope or len(request.scope.strip()) == 0:
            await ctx.error("Scope cannot be empty")
            return MemoryResponse(
                memory_id="error",
                content="",
                scope="error",
                created_at=datetime.now(),
                metadata={"error": "Scope cannot be empty", "suggestions": ["Provide a valid scope like 'work/projects'"]}
            )

        await ctx.info(f"Storing memory in scope '{request.scope}': {request.content[:50]}...")

        # Try advanced memory manager first, fallback to simple storage
        memory = None

        if memory_manager:
            try:
                await ensure_initialized()
                memory = await memory_manager.store_memory(
                    content=request.content,
                    scope=request.scope,
                    tags=request.tags or [],
                    category=request.category,
                    metadata=request.metadata or {},
                    similarity_threshold=request.similarity_threshold,
                )
                await ctx.info(f"Memory stored using advanced manager with ID: {memory.id}")
            except Exception as e:
                await ctx.warning(f"Advanced storage failed: {str(e)}, falling back to simple storage")
                memory = None

        # Fallback to simple storage if advanced storage failed or unavailable
        if not memory:
            import uuid

            memory_id = str(uuid.uuid4())

            # Check for duplicates in simple storage if not allowed
            if not request.allow_duplicates:
                for existing_id, existing_memory in memory_storage.items():
                    if existing_memory["content"].strip().lower() == request.content.strip().lower():
                        await ctx.warning(f"Duplicate content detected. Existing memory_id: {existing_id}")

                        # Return minimal or full response for duplicate
                        if request.minimal_response:
                            return MemoryResponse(
                                memory_id=existing_id,
                                content="[Content hidden for minimal response]",
                                scope=existing_memory["scope"],
                                metadata={},
                                tags=[],
                                category=existing_memory.get("category"),
                                created_at=existing_memory["created_at"],
                                is_duplicate=True,
                                duplicate_of=existing_id,
                            )
                        else:
                            return MemoryResponse(
                                memory_id=existing_id,
                                content=existing_memory["content"],
                                scope=existing_memory["scope"],
                                metadata=existing_memory.get("metadata", {}),
                                tags=existing_memory.get("tags", []),
                                category=existing_memory.get("category"),
                                created_at=existing_memory["created_at"],
                                is_duplicate=True,
                                duplicate_of=existing_id,
                            )

            # Store in simple storage
            memory_data = {
                "memory_id": memory_id,
                "content": request.content,
                "scope": request.scope,
                "metadata": request.metadata or {},
                "tags": request.tags or [],
                "category": request.category,
                "created_at": datetime.now(),
            }

            memory_storage[memory_id] = memory_data
            persistence.save_memories(memory_storage)

            await ctx.info(f"Memory stored using simple storage with ID: {memory_id}")

            # Return minimal or full response
            if request.minimal_response:
                return MemoryResponse(
                    memory_id=memory_id,
                    content="[Content hidden for minimal response]",
                    scope=request.scope,
                    metadata={},
                    tags=[],
                    category=request.category,
                    created_at=memory_data["created_at"],
                    is_duplicate=False,
                )
            else:
                return MemoryResponse(
                    memory_id=memory_id,
                    content=request.content,
                    scope=request.scope,
                    metadata=request.metadata or {},
                    tags=request.tags or [],
                    category=request.category,
                    created_at=memory_data["created_at"],
                    is_duplicate=False,
                )

        # Advanced storage succeeded - check for duplicates if not allowed
        if not request.allow_duplicates and memory:
            if hasattr(memory, "metadata") and memory.metadata and memory.metadata.get("is_duplicate"):
                await ctx.warning(
                    f"Duplicate memory detected. Existing memory_id: {memory.metadata.get('original_memory_id')}"
                )

                # Return minimal or full response based on request
                if request.minimal_response:
                    return MemoryResponse(
                        memory_id=memory.metadata.get("original_memory_id", "unknown"),
                        content="[Content hidden for minimal response]",  # Required field but minimized
                        scope=memory.scope,
                        metadata={},  # Minimal metadata
                        tags=[],
                        category=memory.category,
                        created_at=memory.created_at,
                        is_duplicate=True,
                        duplicate_of=memory.metadata.get("original_memory_id"),
                    )
                else:
                    return MemoryResponse(
                        memory_id=memory.metadata.get("original_memory_id", "unknown"),
                        content=memory.content,
                        scope=memory.scope,
                        metadata=memory.metadata,
                        tags=memory.tags or [],
                        category=memory.category,
                        created_at=memory.created_at,
                        is_duplicate=True,
                        duplicate_of=memory.metadata.get("original_memory_id"),
                    )

        # Return successful advanced storage result
        if request.minimal_response:
            return MemoryResponse(
                memory_id=memory.id,
                content="[Content hidden for minimal response]",  # Required field but minimized
                scope=memory.scope,
                metadata={},  # Minimal metadata
                tags=[],
                category=memory.category,
                created_at=memory.created_at,
                is_duplicate=False,
            )
        else:
            return MemoryResponse(
                memory_id=memory.id,
                content=memory.content,
                scope=memory.scope,
                metadata=memory.metadata if hasattr(memory, "metadata") else {},
                tags=memory.tags or [],
                category=memory.category,
                created_at=memory.created_at,
                is_duplicate=False,
            )

    except Exception as e:
        error_message = f"Failed to store memory: {str(e)}"
        await ctx.error(error_message)
        
        # Provide more detailed error information
        suggestions = [
            "Check if the content and scope are valid",
            "Try again in a moment if this was a temporary issue",
            "Contact support if the problem persists"
        ]
        
        return MemoryResponse(
            memory_id="error",
            content="",
            scope="error",
            created_at=datetime.now(),
            metadata={
                "error": "Memory storage failed",
                "details": str(e),
                "suggestions": suggestions,
                "error_type": type(e).__name__
            }
        )


async def handle_memory_search(request: MemorySearchRequest, ctx: Context) -> Dict[str, Any]:
    """Search memories using semantic similarity with hierarchical scope support"""
    try:
        # Debug: Check memory manager state when tool is called
        await ctx.info(f"DEBUG: memory_manager (global) = {memory_manager}")
        await ctx.info(f"DEBUG: dependencies.memory_manager = {dependencies.memory_manager}")
        
        await ensure_initialized()
        await ctx.info(
            f"Searching memories: '{request.query[:50]}...' in scope: {request.scope} (include_child_scopes: {request.include_child_scopes})"
        )

        # Perform search using memory manager with enhanced parameters
        results = await memory_manager.search_memories(
            query=request.query,
            scope=request.scope,
            include_child_scopes=request.include_child_scopes,
            limit=request.limit,
            min_score=request.similarity_threshold,
        )

        # Format results for response
        formatted_results = []
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

            formatted_results.append(formatted_memory)

        await ctx.info(f"Found {len(formatted_results)} memories")

        # Enhanced response with search metadata
        response = {
            "results": formatted_results,
            "query": request.query,
            "scope": request.scope,
            "include_child_scopes": request.include_child_scopes,
            "total_found": len(formatted_results),
            "similarity_threshold": request.similarity_threshold,
            "search_metadata": {
                "scope_coverage": "hierarchical" if request.include_child_scopes else "exact",
                "fallback_used": len(formatted_results) > 0 and request.scope is not None,
            },
        }

        # Add enhanced scope suggestions with hierarchical fallback if no results found
        if not formatted_results and request.scope:
            await ctx.info("No results found, performing hierarchical fallback search")
            fallback_suggestions = await _perform_hierarchical_fallback_search(
                query=request.query,
                original_scope=request.scope,
                ctx=ctx,
                limit=request.limit,
                similarity_threshold=request.similarity_threshold,
                include_child_scopes=request.include_child_scopes
            )
            response["suggestions"] = fallback_suggestions
            
            # Keep legacy suggestions for backward compatibility
            response["legacy_suggestions"] = {
                "try_include_child_scopes": not request.include_child_scopes,
                "try_broader_scope": request.scope.rsplit("/", 1)[0] if "/" in request.scope else None,
                "try_lower_threshold": max(0.05, request.similarity_threshold - 0.05),
            }

        return response

    except Exception as e:
        error_message = f"Failed to search memories: {str(e)}"
        await ctx.error(error_message)
        
        # Provide helpful error response with fallback empty results
        return {
            "error": "Memory search failed",
            "details": str(e),
            "error_type": type(e).__name__,
            "results": [],  # Graceful fallback
            "query": getattr(request, 'query', 'unknown'),
            "scope": getattr(request, 'scope', 'unknown'),
            "suggestions": [
                "Check if the query format is valid",
                "Try a simpler search query",
                "Verify the scope exists using scope_list",
                "Try again in a moment if this was a temporary issue"
            ],
            "fallback_used": True
        }


async def handle_diversified_search(request: DiversifiedSearchRequest, ctx: Context) -> Dict[str, Any]:
    """Handle diversified similarity search for broader knowledge exploration"""
    try:
        await ensure_initialized()
        await ctx.info(f"Starting diversified search: query='{request.query}', limit={request.limit}")

        if not memory_manager:
            await ctx.error("Memory manager not initialized")
            return {"error": "Memory manager not initialized", "results": []}

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
                "created_at": memory.created_at.isoformat() if memory.created_at else None,
                "metadata": memory.metadata or {},
                "associations": [],
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

            formatted_results.append(formatted_memory)

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
        await ensure_initialized()
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
        await ensure_initialized()
        await ctx.info(f"Deleting memory: {memory_id}")

        # Check if memory exists in advanced storage
        memory = await memory_manager.get_memory(memory_id)
        if not memory:
            # Check simple storage
            if memory_id not in memory_storage:
                await ctx.warning(f"Memory not found: {memory_id}")
                return {"success": False, "error": "Memory not found"}

        # Delete from advanced storage
        if memory:
            await memory_manager.delete_memory(memory_id)
            await ctx.info(f"Deleted memory from advanced storage: {memory_id}")

        # Delete from simple storage
        if memory_id in memory_storage:
            del memory_storage[memory_id]
            persistence.save_memories(memory_storage)
            await ctx.info(f"Deleted memory from simple storage: {memory_id}")

        return {"success": True, "message": f"Memory {memory_id} deleted successfully"}

    except Exception as e:
        await ctx.error(f"Failed to delete memory: {e}")
        return {"success": False, "error": str(e)}


async def handle_memory_update(request: MemoryUpdateRequest, ctx: Context) -> MemoryResponse:
    """Update an existing memory"""
    try:
        await ensure_initialized()
        await ctx.info(f"Updating memory: {request.memory_id}")

        # Get existing memory
        memory = await memory_manager.get_memory(request.memory_id)
        if not memory:
            await ctx.warning(f"Memory not found: {request.memory_id}")
            return MemoryResponse(success=False, message="Memory not found", memory_id=request.memory_id)

        # Update memory
        updated_memory = await memory_manager.update_memory(
            memory_id=request.memory_id,
            content=request.content,
            scope=request.scope,
            tags=request.tags,
            category=request.category,
            metadata=request.metadata,
        )

        await ctx.info(f"Memory updated successfully: {request.memory_id}")

        return MemoryResponse(
            memory_id=updated_memory.id,
            content=updated_memory.content,
            scope=updated_memory.scope,
            metadata=updated_memory.metadata,
            tags=updated_memory.tags or [],
            category=updated_memory.category,
            created_at=updated_memory.created_at,
        )

    except Exception as e:
        await ctx.error(f"Failed to update memory: {e}")
        # Return a minimal valid response for error case
        return MemoryResponse(memory_id=request.memory_id, content="", scope="error", created_at=datetime.now())


async def handle_memory_discover_associations(
    memory_id: str, ctx: Context, limit: int = 10, similarity_threshold: float = 0.1
) -> Dict[str, Any]:
    """Discover semantic associations for a specific memory"""
    try:
        await ensure_initialized()
        await ctx.info(f"Discovering associations for memory: {memory_id}")

        # Get the source memory
        memory = await memory_manager.get_memory(memory_id)
        if not memory:
            await ctx.warning(f"Memory not found: {memory_id}")
            return {"error": "Memory not found", "associations": []}

        # Find similar memories with enhanced search strategy
        search_results = await memory_manager.search_memories(
            query=memory.content,
            limit=limit * 3,  # Search more to account for filtering
            min_score=max(0.1, similarity_threshold - 0.2),  # Lower threshold for diversity
        )

        # If we didn't find enough diverse results, try with the original content plus tags
        if len(search_results) < limit:
            # Create enhanced query with tags and category
            enhanced_query = memory.content
            if memory.tags:
                enhanced_query += " " + " ".join(memory.tags)
            if memory.category:
                enhanced_query += " " + memory.category

            additional_results = await memory_manager.search_memories(
                query=enhanced_query, limit=limit * 2, min_score=max(0.1, similarity_threshold - 0.3)
            )

            # Merge results (will be deduplicated later)
            search_results.extend(additional_results)

        # Filter out the source memory and format results
        associations = []
        seen_content = set()  # Track content to avoid duplicates

        for result in search_results:
            assoc_memory = result["memory"]

            # Skip the source memory itself
            if assoc_memory.id == memory_id:
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
            if len(associations) >= limit:
                break

        await ctx.info(f"Found {len(associations)} associations for memory {memory_id}")

        return {
            "source_memory_id": memory_id,
            "source_content": memory.content[:100] + "..." if len(memory.content) > 100 else memory.content,
            "associations": associations,
            "total_found": len(associations),
            "similarity_threshold": similarity_threshold,
        }

    except Exception as e:
        await ctx.error(f"Failed to discover associations: {e}")
        return {"error": str(e), "associations": []}


async def handle_memory_import(request: MemoryImportRequest, ctx: Context) -> MemoryImportResponse:
    """Import memories from file or direct data"""
    try:
        await ensure_initialized()

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
                max_size_mb = config.storage.max_import_size_mb
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
        validation_errors = []
        if request.validate_data:
            validation_errors = await _validate_import_data(import_data)
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

                # Check for existing memory
                existing_memory = memory_storage.get(memory_id)

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
                        # Merge metadata while keeping existing content
                        if "metadata" not in existing_memory:
                            existing_memory["metadata"] = {}
                        existing_memory["metadata"].update(memory_data.get("metadata", {}))
                        memory_storage[memory_id] = existing_memory
                        imported_count += 1
                        continue

                # Prepare memory for import
                imported_memory = {
                    "memory_id": memory_id,
                    "content": memory_data["content"],
                    "scope": final_scope,
                    "metadata": memory_data.get("metadata", {}),
                    "tags": memory_data.get("tags", []),
                    "category": memory_data.get("category"),
                    "created_at": (
                        datetime.fromisoformat(memory_data["created_at"])
                        if isinstance(memory_data["created_at"], str)
                        else memory_data["created_at"]
                    ),
                }

                # Store in simple storage
                memory_storage[memory_id] = imported_memory
                imported_count += 1

                # TODO: Store in advanced storage if available
                # This would require re-computing embeddings and associations

            except Exception as e:
                validation_errors.append(f"Failed to import memory {memory_data.get('memory_id', 'unknown')}: {e}")
                continue

        # Save to persistent storage
        persistence.save_memories(memory_storage)

        await ctx.info(
            f"Import completed: {imported_count} imported, {skipped_count} skipped, {overwritten_count} overwritten"
        )

        return MemoryImportResponse(
            success=True,
            imported_count=imported_count,
            skipped_count=skipped_count,
            overwritten_count=overwritten_count,
            import_source=import_source,
            merge_strategy_used=request.merge_strategy,
            validation_errors=validation_errors,
            imported_scopes=list(imported_scopes),
        )

    except Exception as e:
        await ctx.error(f"Failed to import memories: {e}")
        raise


async def handle_memory_list_all(page: int = 1, per_page: int = 10, ctx: Optional[Context] = None) -> Dict[str, Any]:
    """List all memories with pagination (for debugging)"""
    try:
        await ensure_initialized()

        if ctx:
            await ctx.info(f"Retrieving memories (page {page}, {per_page} per page)...")

        all_memories = list(memory_storage.values())
        total_items = len(all_memories)

        # Calculate pagination
        total_pages = (total_items + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        # Get page items
        page_memories = all_memories[start_idx:end_idx]
        results = []
        for memory_data in page_memories:
            results.append(
                MemoryResponse(
                    memory_id=memory_data["memory_id"],
                    content=memory_data["content"],
                    scope=memory_data["scope"],
                    metadata=memory_data.get("metadata", {}),
                    tags=memory_data.get("tags", []),
                    category=memory_data.get("category"),
                    created_at=memory_data["created_at"],
                )
            )

        pagination = PaginationInfo(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        )

        if ctx:
            await ctx.info(f"Retrieved {len(results)} memories (page {page}/{total_pages})")

        return {"memories": results, "pagination": pagination}

    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to list memories: {e}")
        raise


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
            # Delegate to existing get handler
            return await handle_memory_get(request.memory_id, ctx, request.include_associations)

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
            return await handle_memory_update(update_request, ctx)

        elif request.operation == "delete":
            # Delegate to existing delete handler
            return await handle_memory_delete(request.memory_id, ctx)

        else:
            await ctx.error(f"Unknown operation: {request.operation}")
            return {
                "error": f"Unknown operation: {request.operation}. Supported operations: 'get', 'update', 'delete'",
                "operation": request.operation,
                "memory_id": request.memory_id,
                "success": False,
            }

    except Exception as e:
        await ctx.error(f"Memory manage operation failed: {e}")
        return {
            "error": f"Memory manage operation failed: {str(e)}",
            "operation": request.operation,
            "memory_id": request.memory_id,
            "success": False,
        }


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
                export_format=request.export_format,
            )
            return await handle_memory_export(export_request, ctx)

        elif request.operation == "import":
            # Create import request from sync request
            import_request = MemoryImportRequest(
                file_path=request.file_path,
                import_data=request.import_data,
                target_scope_prefix=request.scope,  # Use scope as target_scope_prefix for import
                merge_strategy=request.merge_strategy,
                validate_data=request.validate_data,
            )
            return await handle_memory_import(import_request, ctx)

        else:
            await ctx.error(f"Unknown sync operation: {request.operation}")
            return {
                "error": f"Unknown sync operation: {request.operation}. Supported operations: 'export', 'import'",
                "operation": request.operation,
                "success": False,
            }

    except Exception as e:
        await ctx.error(f"Memory sync operation failed: {e}")
        return {"error": f"Memory sync operation failed: {str(e)}", "operation": request.operation, "success": False}


async def _resolve_import_path(file_path: str) -> Path:
    """Resolve import file path with proper validation."""
    path = Path(file_path)

    # If it's a relative path, make it relative to the data directory
    if not path.is_absolute():
        data_dir = Path("data/imports")
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

        return True
    except Exception:
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
    include_child_scopes: bool = False
) -> Dict[str, Any]:
    """
    Perform hierarchical fallback search when original search returns 0 results.
    
    Algorithm:
    1. Search parent scope level by level
    2. Return candidates immediately when results found
    3. If no results at any parent level, perform global search
    
    Returns helpful suggestions even if memory_manager is not available.
    """
    # Try centralized dependency manager first
    current_memory_manager = dependencies.memory_manager
    
    # If not available, try factory approach
    if not current_memory_manager:
        from ..memory_factory import get_or_create_memory_manager
        try:
            current_memory_manager = await get_or_create_memory_manager()
            await ctx.info("Using factory-created memory manager for fallback search")
        except Exception as e:
            await ctx.warning(f"Factory memory manager creation failed: {e}")
    
    if not current_memory_manager:
        await ctx.error("Memory manager not initialized for fallback search")
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
                    "work/projects", "learning/programming", "personal/notes",
                    original_scope.rsplit("/", 1)[0] if "/" in original_scope else "global"
                ]
            },
            "note": "Manual suggestions provided due to initialization issue"
        }
    
    fallback_suggestions = {
        "type": "scope_fallback",
        "original_scope": original_scope,
        "found_in_scope": None,
        "candidates": [],
        "fallback_level": 0,
        "search_strategy": "hierarchical"
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
                
                fallback_suggestions.update({
                    "found_in_scope": parent_scope,
                    "candidates": list(unique_scopes)[:5],  # Max 5 candidates
                    "fallback_level": fallback_level,
                    "results_count": len(results)
                })
                
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
            
            fallback_suggestions.update({
                "found_in_scope": "global",
                "candidates": list(unique_scopes)[:5],
                "fallback_level": fallback_level + 1,
                "search_strategy": "global_fallback",
                "results_count": len(global_results),
                "note": "Results found via global search with relaxed threshold"
            })
            
            await ctx.info(f"Found {len(global_results)} results via global search")
            return fallback_suggestions
            
    except Exception as e:
        await ctx.warning(f"Error during global fallback search: {e}")
    
    # No results found anywhere - provide helpful manual suggestions
    fallback_suggestions.update({
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
                "work/projects", "learning/programming", "personal/notes",
                original_scope.rsplit("/", 1)[0] if "/" in original_scope else "global"
            ]
        },
        "note": "No results found - try suggestions below"
    })
    
    await ctx.info("No results found in hierarchical or global search")
    return fallback_suggestions
    fallback_suggestions.update({
        "found_in_scope": None,
        "candidates": [],
        "fallback_level": fallback_level + 1,
        "search_strategy": "exhausted",
        "note": "No results found in any scope or global search"
    })
    
    return fallback_suggestions
