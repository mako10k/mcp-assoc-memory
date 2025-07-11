"""
Memory management tools for MCP Associative Memory Server
"""

import json
import gzip
import base64
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Annotated
from fastmcp import Context
from pydantic import Field

from ..models import (
    MemoryStoreRequest, MemorySearchRequest, DiversifiedSearchRequest, MemoryUpdateRequest,
    MemoryImportRequest, MemoryImportResponse,
    MemoryResponse, PaginationInfo
)
from ...core.memory_manager import MemoryManager
from ...simple_persistence import get_persistent_storage
from ...config import get_config

# Get the config instance
config = get_config()

# Global references (will be set by server.py)
memory_manager: Optional[MemoryManager] = None
memory_storage: Optional[Dict[str, Any]] = None
persistence = None
_initialized = False


def set_dependencies(mm: MemoryManager, ms: Dict[str, Any], p):
    """Set global dependencies from server.py"""
    global memory_manager, memory_storage, persistence
    memory_manager = mm
    memory_storage = ms
    persistence = p


async def ensure_initialized():
    """Ensure memory manager is initialized"""
    global _initialized
    if not _initialized and memory_manager:
        await memory_manager.initialize()
        _initialized = True


async def handle_memory_store(
    request: MemoryStoreRequest,
    ctx: Context
) -> MemoryResponse:
    """Store a memory with full associative capabilities"""
    try:
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
                    similarity_threshold=request.similarity_threshold
                )
                await ctx.info(f"Memory stored using advanced manager with ID: {memory.id}")
            except Exception as e:
                await ctx.warning(f"Advanced storage failed: {e}, falling back to simple storage")
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
                        return MemoryResponse(
                            memory_id=existing_id,
                            content=existing_memory["content"],
                            scope=existing_memory["scope"],
                            metadata=existing_memory.get("metadata", {}),
                            tags=existing_memory.get("tags", []),
                            category=existing_memory.get("category"),
                            created_at=existing_memory["created_at"],
                            is_duplicate=True,
                            duplicate_of=existing_id
                        )
            
            # Store in simple storage
            memory_data = {
                "memory_id": memory_id,
                "content": request.content,
                "scope": request.scope,
                "metadata": request.metadata or {},
                "tags": request.tags or [],
                "category": request.category,
                "created_at": datetime.now()
            }
            
            memory_storage[memory_id] = memory_data
            persistence.save_memories(memory_storage)
            
            await ctx.info(f"Memory stored using simple storage with ID: {memory_id}")
            
            return MemoryResponse(
                memory_id=memory_id,
                content=request.content,
                scope=request.scope,
                metadata=request.metadata or {},
                tags=request.tags or [],
                category=request.category,
                created_at=memory_data["created_at"],
                is_duplicate=False
            )
        
        # Advanced storage succeeded - check for duplicates if not allowed
        if not request.allow_duplicates and memory:
            if hasattr(memory, 'metadata') and memory.metadata and memory.metadata.get("is_duplicate"):
                await ctx.warning(f"Duplicate memory detected. Existing memory_id: {memory.metadata.get('original_memory_id')}")
                return MemoryResponse(
                    memory_id=memory.metadata.get("original_memory_id", "unknown"),
                    content=memory.content,
                    scope=memory.scope,
                    metadata=memory.metadata,
                    tags=memory.tags or [],
                    category=memory.category,
                    created_at=memory.created_at,
                    is_duplicate=True,
                    duplicate_of=memory.metadata.get("original_memory_id")
                )
        
        # Return successful advanced storage result
        return MemoryResponse(
            memory_id=memory.id,
            content=memory.content,
            scope=memory.scope,
            metadata=memory.metadata if hasattr(memory, 'metadata') else {},
            tags=memory.tags or [],
            category=memory.category,
            created_at=memory.created_at,
            is_duplicate=False
        )
        
    except Exception as e:
        await ctx.error(f"Failed to store memory: {e}")
        # Return a minimal valid response for error case
        return MemoryResponse(
            memory_id="error",
            content="",
            scope="error",
            created_at=datetime.now()
        )


async def handle_memory_search(
    request: MemorySearchRequest,
    ctx: Context
) -> Dict[str, Any]:
    """Search memories using semantic similarity"""
    try:
        await ensure_initialized()
        await ctx.info(f"Searching memories: '{request.query[:50]}...' in scope: {request.scope}")
        
        # Perform search using memory manager
        results = await memory_manager.search_memories(
            query=request.query,
            scope=request.scope,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
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
                "metadata": memory.metadata
            }
            
            # Include associations if requested
            if request.include_associations:
                try:
                    associations = await memory_manager.metadata_store.get_memory_associations(memory.id)
                    formatted_memory["associations"] = [
                        {
                            "memory_id": assoc.target_memory_id,
                            "association_type": assoc.association_type,
                            "strength": assoc.strength,
                            "auto_generated": assoc.auto_generated
                        }
                        for assoc in associations[:3]  # Limit to top 3 associations
                    ]
                except Exception as e:
                    await ctx.warning(f"Failed to get associations for memory {memory.id}: {e}")
                    formatted_memory["associations"] = []
            
            formatted_results.append(formatted_memory)
        
        await ctx.info(f"Found {len(formatted_results)} memories")
        
        return {
            "results": formatted_results,
            "query": request.query,
            "scope": request.scope,
            "total_found": len(formatted_results),
            "similarity_threshold": request.similarity_threshold
        }
        
    except Exception as e:
        await ctx.error(f"Failed to search memories: {e}")
        return {"error": str(e), "results": []}


async def handle_diversified_search(
    request: DiversifiedSearchRequest,
    ctx: Context
) -> Dict[str, Any]:
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
            max_expansion_factor=request.max_expansion_factor
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
                "associations": []
            }
            
            # Include associations if requested
            if request.include_associations:
                try:
                    # Get associations via metadata store
                    associations = await memory_manager.metadata_store.get_memory_associations(memory.id)
                    formatted_memory["associations"] = [
                        {
                            "memory_id": assoc.target_memory_id,
                            "association_type": assoc.association_type,
                            "strength": assoc.strength,
                            "auto_generated": assoc.auto_generated
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
            "search_type": "diversified"
        }
        
    except Exception as e:
        await ctx.error(f"Failed to perform diversified search: {e}")
        return {"error": str(e), "results": []}


async def handle_memory_get(
    memory_id: str,
    ctx: Context,
    include_associations: bool = True
) -> Dict[str, Any]:
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
            "metadata": memory.metadata
        }
        
        # Include associations if requested
        if include_associations:
            try:
                associations = await memory_manager.get_associations(memory_id, limit=10)
                result["associations"] = [
                    {
                        "memory_id": assoc.id,
                        "content": assoc.content[:100] + "..." if len(assoc.content) > 100 else assoc.content,
                        "scope": assoc.metadata.get("scope", assoc.scope),
                        "similarity_score": getattr(assoc, 'similarity_score', 0.0),
                        "tags": assoc.tags,
                        "category": assoc.category,
                        "created_at": assoc.created_at
                    }
                    for assoc in associations
                ]
            except Exception as e:
                await ctx.warning(f"Failed to get associations: {e}")
                result["associations"] = []
        
        await ctx.info(f"Retrieved memory: {memory_id}")
        return result
        
    except Exception as e:
        await ctx.error(f"Failed to get memory: {e}")
        return {"error": str(e)}


async def handle_memory_delete(
    memory_id: str,
    ctx: Context
) -> Dict[str, Any]:
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


async def handle_memory_update(
    request: MemoryUpdateRequest,
    ctx: Context
) -> MemoryResponse:
    """Update an existing memory"""
    try:
        await ensure_initialized()
        await ctx.info(f"Updating memory: {request.memory_id}")
        
        # Get existing memory
        memory = await memory_manager.get_memory(request.memory_id)
        if not memory:
            await ctx.warning(f"Memory not found: {request.memory_id}")
            return MemoryResponse(
                success=False,
                message="Memory not found",
                memory_id=request.memory_id
            )
        
        # Update memory
        updated_memory = await memory_manager.update_memory(
            memory_id=request.memory_id,
            content=request.content,
            scope=request.scope,
            tags=request.tags,
            category=request.category,
            metadata=request.metadata
        )
        
        await ctx.info(f"Memory updated successfully: {request.memory_id}")
        
        return MemoryResponse(
            memory_id=updated_memory.id,
            content=updated_memory.content,
            scope=updated_memory.scope,
            metadata=updated_memory.metadata,
            tags=updated_memory.tags or [],
            category=updated_memory.category,
            created_at=updated_memory.created_at
        )
        
    except Exception as e:
        await ctx.error(f"Failed to update memory: {e}")
        # Return a minimal valid response for error case
        return MemoryResponse(
            memory_id=request.memory_id,
            content="",
            scope="error",
            created_at=datetime.now()
        )


async def handle_memory_discover_associations(
    memory_id: str,
    ctx: Context,
    limit: int = 10,
    similarity_threshold: float = 0.1
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
            similarity_threshold=max(0.1, similarity_threshold - 0.2)  # Lower threshold for diversity
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
                query=enhanced_query,
                limit=limit * 2,
                similarity_threshold=max(0.1, similarity_threshold - 0.3)
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
            
            associations.append({
                "memory_id": assoc_memory.id,
                "content": assoc_memory.content[:100] + "..." if len(assoc_memory.content) > 100 else assoc_memory.content,
                "scope": memory_scope,
                "similarity_score": result["similarity"],
                "category": assoc_memory.category,
                "tags": assoc_memory.tags,
                "created_at": assoc_memory.created_at
            })
            
            # Break if we have enough diverse associations
            if len(associations) >= limit:
                break
        
        await ctx.info(f"Found {len(associations)} associations for memory {memory_id}")
        
        return {
            "source_memory_id": memory_id,
            "source_content": memory.content[:100] + "..." if len(memory.content) > 100 else memory.content,
            "associations": associations,
            "total_found": len(associations),
            "similarity_threshold": similarity_threshold
        }
        
    except Exception as e:
        await ctx.error(f"Failed to discover associations: {e}")
        return {"error": str(e), "associations": []}


async def handle_memory_import(
    request: MemoryImportRequest,
    ctx: Context
) -> MemoryImportResponse:
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
            
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
                
            # Handle compressed files
            if file_content.startswith("# Compressed MCP Memory Export"):
                lines = file_content.split('\n', 1)
                if len(lines) > 1:
                    compressed_data = base64.b64decode(lines[1])
                    import_data_str = gzip.decompress(compressed_data).decode('utf-8')
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
                if not import_data_str.strip().startswith('{'):
                    # Assume it's compressed
                    compressed_data = base64.b64decode(import_data_str)
                    import_data_str = gzip.decompress(compressed_data).decode('utf-8')
            except:
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
        imported_scopes = set();
        
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
                    "created_at": datetime.fromisoformat(memory_data["created_at"]) if isinstance(memory_data["created_at"], str) else memory_data["created_at"]
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
        
        await ctx.info(f"Import completed: {imported_count} imported, {skipped_count} skipped, {overwritten_count} overwritten")
        
        return MemoryImportResponse(
            success=True,
            imported_count=imported_count,
            skipped_count=skipped_count,
            overwritten_count=overwritten_count,
            import_source=import_source,
            merge_strategy_used=request.merge_strategy,
            validation_errors=validation_errors,
            imported_scopes=list(imported_scopes)
        )
        
    except Exception as e:
        await ctx.error(f"Failed to import memories: {e}")
        raise


async def handle_memory_list_all(
    page: int = 1,
    per_page: int = 10,
    ctx: Context = None
) -> Dict[str, Any]:
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
            results.append(MemoryResponse(
                memory_id=memory_data["memory_id"],
                content=memory_data["content"],
                scope=memory_data["scope"],
                metadata=memory_data.get("metadata", {}),
                tags=memory_data.get("tags", []),
                category=memory_data.get("category"),
                created_at=memory_data["created_at"]
            ))
        
        pagination = PaginationInfo(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        if ctx:
            await ctx.info(f"Retrieved {len(results)} memories (page {page}/{total_pages})")
        
        return {
            "memories": results,
            "pagination": pagination
        }
        
    except Exception as e:
        if ctx:
            await ctx.error(f"Failed to list memories: {e}")
        raise


# File path resolution utilities
async def _resolve_export_path(file_path: str) -> Path:
    """Resolve and validate export file path"""
    if Path(file_path).is_absolute():
        try:
            allow_absolute = config.storage.allow_absolute_paths
        except AttributeError:
            allow_absolute = False
        if not allow_absolute:
            raise ValueError("Absolute paths not allowed in configuration")
        return Path(file_path)
    else:
        # Relative to export directory
        try:
            data_dir = config.storage.data_dir
            export_dir_name = config.storage.export_dir
        except AttributeError:
            data_dir = "data"
            export_dir_name = "exports"
        export_dir = Path(data_dir) / export_dir_name
        return export_dir / file_path


async def _resolve_import_path(file_path: str) -> Path:
    """Resolve and validate import file path"""
    if Path(file_path).is_absolute():
        try:
            allow_absolute = config.storage.allow_absolute_paths
        except AttributeError:
            allow_absolute = False
        if not allow_absolute:
            raise ValueError("Absolute paths not allowed in configuration")
        return Path(file_path)
    else:
        # Try import directory first, then export directory
        try:
            data_dir = config.storage.data_dir
            import_dir_name = config.storage.import_dir
            export_dir_name = config.storage.export_dir
        except AttributeError:
            data_dir = "data"
            import_dir_name = "imports"
            export_dir_name = "exports"
            
        import_dir = Path(data_dir) / import_dir_name
        import_path = import_dir / file_path
        
        if import_path.exists():
            return import_path
        
        # Fallback to export directory
        export_dir = Path(data_dir) / export_dir_name
        export_path = export_dir / file_path
        
        if export_path.exists():
            return export_path
            
        # Return original path for error handling
        return import_path


async def _validate_import_data(import_data: Dict[str, Any]) -> List[str]:
    """Validate import data structure"""
    errors = []
    
    # Check required fields
    if "memories" not in import_data:
        errors.append("Missing 'memories' field")
        return errors
    
    if not isinstance(import_data["memories"], list):
        errors.append("'memories' must be a list")
        return errors
    
    # Validate each memory
    for i, memory in enumerate(import_data["memories"]):
        if not isinstance(memory, dict):
            errors.append(f"Memory {i}: must be an object")
            continue
            
        required_fields = ["memory_id", "content", "scope", "created_at"]
        for field in required_fields:
            if field not in memory:
                errors.append(f"Memory {i}: missing required field '{field}'")
    
    return errors
