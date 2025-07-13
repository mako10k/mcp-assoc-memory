"""Additional memory tools for MCP associative memory server."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ...simple_persistence import get_persistent_storage
from ..models.requests import MemoryMoveRequest, SessionManageRequest
from ..models.responses import (
    MemoryDiscoverAssociationsResponse,
    MemoryMoveResponse,
    SearchResultWithAssociations,
    SessionInfo,
    SessionManageResponse,
)
from ...core.singleton_memory_manager import get_memory_manager, get_or_create_memory_manager

# Module-level dependencies (for backward compatibility)
memory_manager = None


def set_dependencies(mm: Any) -> None:
    """Set module dependencies from server initialization (backward compatibility)"""
    global memory_manager
    memory_manager = mm


# Get storage
memory_storage, persistence = get_persistent_storage()


async def handle_memory_move(request: MemoryMoveRequest, ctx: Any) -> Dict[str, Any]:
    """Handle memory_move tool requests."""
    try:
        await ctx.info(f"Moving {len(request.memory_ids)} memories to scope: {request.target_scope}")

        # Get memory manager instance
        memory_manager = await get_or_create_memory_manager()
        if not memory_manager:
            error_msg = "Memory manager not available"
            await ctx.error(error_msg)
            return MemoryMoveResponse(
                success=False,
                message=error_msg,
                data={},
                moved_memories=[],
                failed_memory_ids=request.memory_ids,
            ).model_dump()

        moved_count = 0
        failed_memory_ids = []

        for memory_id in request.memory_ids:
            try:
                # Update memory with new scope (both scope field and metadata)
                updated_memory = await memory_manager.update_memory(
                    memory_id=memory_id,
                    scope=request.target_scope,
                    metadata={"scope": request.target_scope}  # Also update metadata scope
                )
                
                # Critical: Check if update_memory returned None
                if updated_memory is None:
                    error_msg = f"Failed to update memory {memory_id} - update_memory returned None"
                    await ctx.warning(error_msg)
                    failed_memory_ids.append(memory_id)
                    continue
                
                moved_count += 1
                await ctx.info(f"Successfully moved memory {memory_id} to {request.target_scope}")
                
            except Exception as move_error:
                error_msg = f"Failed to move memory {memory_id}: {move_error}"
                await ctx.warning(error_msg)
                failed_memory_ids.append(memory_id)

        success_msg = f"Successfully moved {moved_count} memories to {request.target_scope}"
        if failed_memory_ids:
            success_msg += f" ({len(failed_memory_ids)} failed)"
        
        await ctx.info(success_msg)

        return MemoryMoveResponse(
            success=True,
            message=success_msg,
            data={"moved_count": moved_count, "target_scope": request.target_scope},
            moved_memories=[],  # Simplified: don't return full memory objects to avoid serialization issues
            failed_memory_ids=failed_memory_ids,
        ).model_dump()

    except Exception as e:
        error_msg = f"Failed to move memories: {e}"
        await ctx.error(error_msg)
        return MemoryMoveResponse(
            success=False,
            message=error_msg,
            data={},
            moved_memories=[],
            failed_memory_ids=request.memory_ids,
        ).model_dump()


async def handle_memory_discover_associations(
    memory_id: str, ctx: Any, limit: int = 10, similarity_threshold: float = 0.1
) -> Dict[str, Any]:
    """Handle memory_discover_associations tool requests."""
    try:
        await ctx.info(f"Discovering associations for memory: {memory_id}")

        # Use comprehensive memory manager access
        manager = await get_or_create_memory_manager()
        if not manager:
            return {
                "success": False,
                "message": "No memory manager available",
                "data": {},
                "source_memory": None,
                "associations": [],
                "total_found": 0,
            }

        # Get the source memory
        source_memory = await manager.get_memory(memory_id)
        if not source_memory:
            await ctx.warning(f"Memory not found: {memory_id}")
            return {
                "success": False,
                "message": "Memory not found",
                "data": {},
                "source_memory": None,
                "associations": [],
                "total_found": 0,
            }

        # Use search_memories to find semantically related memories
        # First try with the exact content
        search_results = await manager.search_memories(
            query=source_memory.content,
            limit=limit + 1,  # +1 to account for source memory in results
            min_score=similarity_threshold,
        )

        # If no results, try with a shorter query from content
        if not search_results and len(source_memory.content) > 100:
            short_query = source_memory.content[:100]
            search_results = await manager.search_memories(
                query=short_query,
                limit=limit + 1,
                min_score=similarity_threshold,
            )

        # If still no results, try with keywords from the content
        if not search_results:
            # Extract key terms from content
            words = source_memory.content.split()
            important_words = [w for w in words if len(w) > 4 and w.isalpha()][:10]
            if important_words:
                keyword_query = " ".join(important_words)
                search_results = await memory_manager.search_memories(  # type: ignore
                    query=keyword_query,
                    limit=limit + 1,
                    min_score=max(0.1, similarity_threshold),
                )

        # Filter out the source memory and format results
        associations = []
        for result in search_results:
            # Handle different possible result formats
            if isinstance(result, dict):
                # If result is already a dict with memory key
                memory = result.get("memory")
                similarity = result.get("similarity", result.get("similarity_score", 1.0))
            else:
                # If result is a memory object directly
                memory = result
                similarity = getattr(result, "similarity_score", 1.0)

            if not memory:
                continue

            # Skip the source memory itself
            if memory.id == memory_id:
                continue

            associations.append(
                {
                    "memory": memory,
                    "similarity_score": similarity,
                    "associations": [],
                }
            )

            # Stop when we have enough associations
            if len(associations) >= limit:
                break

        return {
            "success": True,
            "message": f"Found {len(associations)} associations",
            "data": {},
            "source_memory": source_memory,
            "associations": associations,
            "total_found": len(associations),
        }

    except Exception as e:
        await ctx.error(f"Failed to discover associations: {e}")
        return {"success": False, "error": f"Failed to discover associations: {e}", "data": {}}


async def handle_session_manage(request: SessionManageRequest, ctx: Any) -> SessionManageResponse:
    """Manage sessions and cleanup"""
    try:
        await ctx.info(f"Session management action: {request.action}")

        if request.action == "create":
            # Create a new session scope
            session_id = request.session_id or f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            session_scope = f"session/{session_id}"

            # Add a session marker memory
            session_memory = {
                "memory_id": str(uuid.uuid4()),
                "content": f"Session created: {session_id}",
                "scope": session_scope,
                "metadata": {"session_marker": True, "created_by": "session_manage"},
                "created_at": datetime.now(),
            }
            memory_storage[session_memory["memory_id"]] = session_memory

            # Save to persistent storage
            persistence.save_memories(memory_storage)

            await ctx.info(f"Created session: {session_id}")

            return SessionManageResponse(
                success=True,
                message=f"Created session: {session_id}",
                data={"action": "create", "session_id": session_id},
                session=SessionInfo(
                    session_id=session_id, created_at=datetime.now(), memory_count=1, last_activity=datetime.now()
                ),
                sessions=[],
            )

        elif request.action == "list":
            # List all active sessions
            session_scopes = {}
            for memory_data in memory_storage.values():
                scope = memory_data["scope"]
                if scope.startswith("session/"):
                    session_id = scope.split("/", 1)[1]
                    if session_id not in session_scopes:
                        session_scopes[session_id] = {
                            "scope": scope,
                            "memories": [],
                            "created_at": memory_data["created_at"],
                            "last_updated": memory_data["created_at"],
                        }
                    session_scopes[session_id]["memories"].append(memory_data)
                    session_scopes[session_id]["last_updated"] = max(
                        session_scopes[session_id]["last_updated"], memory_data["created_at"]
                    )

            active_sessions = [
                SessionInfo(
                    session_id=session_id,
                    created_at=data["created_at"],
                    memory_count=len(data["memories"]),
                    last_activity=data.get("last_updated"),
                )
                for session_id, data in session_scopes.items()
            ]

            await ctx.info(f"Found {len(active_sessions)} active sessions")

            return SessionManageResponse(
                success=True,
                message=f"Found {len(active_sessions)} active sessions",
                data={"action": "list"},
                session=None,
                sessions=active_sessions,
            )

        elif request.action == "cleanup":
            # Clean up old sessions
            cutoff_date = datetime.now() - timedelta(days=request.max_age_days or 7)
            cleaned_count = 0

            memories_to_delete = []
            for memory_id, memory_data in memory_storage.items():
                if memory_data["scope"].startswith("session/") and memory_data["created_at"] < cutoff_date:
                    memories_to_delete.append(memory_id)

            for memory_id in memories_to_delete:
                del memory_storage[memory_id]
                cleaned_count += 1

            # Save to persistent storage if any memories were cleaned
            if cleaned_count > 0:
                persistence.save_memories(memory_storage)

            await ctx.info(f"Cleaned up {cleaned_count} old session memories")

            return SessionManageResponse(
                success=True,
                message=f"Cleaned up {cleaned_count} old session memories",
                data={"action": "cleanup"},
                session=None,
                sessions=[],
                cleaned_sessions=[f"session-{i}" for i in range(cleaned_count)],  # simplified representation
            )

        else:
            raise ValueError(f"Unknown action: {request.action}")

    except Exception as e:
        await ctx.error(f"Failed to manage session: {e}")
        raise
