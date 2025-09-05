"""Additional memory tools for MCP associative memory server."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

from ...core.singleton_memory_manager import get_or_create_memory_manager
from ..models.common import ResponseBuilder, ResponseLevel

# SimplePersistence removed - using SingletonMemoryManager for all storage
from ..models.requests import MemoryMoveRequest, SessionManageRequest
from ..models.responses import MemoryMoveResponse, SessionInfo, SessionManageResponse

# Module-level dependencies (for backward compatibility)
memory_manager = None


def set_dependencies(mm: Any) -> None:
    """Set module dependencies from server initialization (backward compatibility)"""
    global memory_manager
    memory_manager = mm


# Storage now handled through SingletonMemoryManager - no separate persistence layer needed
# Legacy memory_storage and persistence references removed


async def handle_memory_move(request: MemoryMoveRequest, ctx: Any) -> Dict[str, Any]:
    """Handle memory_move tool requests."""
    try:
        await ctx.info(f"Moving {len(request.memory_ids)} memories to scope: {request.target_scope}")

        # Get memory manager instance
        memory_manager = await get_or_create_memory_manager()
        if not memory_manager:
            error_msg = "Memory manager not available"
            await ctx.error(error_msg)
            raise RuntimeError(error_msg)

        # Handle empty memory_ids list early
        if not request.memory_ids:
            base_data = {"success": True, "moved_count": 0, "failed_count": 0}
            return ResponseBuilder.build_response(request.response_level, base_data)

        moved_count = 0
        failed_memory_ids = []
        moved_memories = []

        for memory_id in request.memory_ids:
            try:
                # Update memory with new scope (both scope field and metadata)
                updated_memory = await memory_manager.update_memory(
                    memory_id=memory_id,
                    scope=request.target_scope,
                    metadata={"scope": request.target_scope},  # Also update metadata scope
                )

                # Critical: Check if update_memory returned None
                if updated_memory is None:
                    error_msg = f"Failed to update memory {memory_id} - update_memory returned None"
                    await ctx.error(error_msg)
                    raise RuntimeError(error_msg)

                moved_count += 1
                moved_memories.append(
                    {
                        "memory_id": memory_id,
                        "scope": request.target_scope,
                        "content_preview": updated_memory.content[:50] + "..."
                        if len(updated_memory.content) > 50
                        else updated_memory.content,
                        "created_at": getattr(updated_memory, "created_at", None),
                        "updated_at": getattr(updated_memory, "updated_at", None),
                    }
                )
                await ctx.info(f"Successfully moved memory {memory_id} to {request.target_scope}")

            except Exception as move_error:
                error_msg = f"Failed to move memory {memory_id}: {move_error}"
                await ctx.warning(error_msg)
                failed_memory_ids.append(memory_id)

        success = moved_count > 0 or len(request.memory_ids) == 0
        success_msg = f"Successfully moved {moved_count} memories to {request.target_scope}"
        if failed_memory_ids:
            success_msg += f" ({len(failed_memory_ids)} failed)"

        await ctx.info(success_msg)

        # Use ResponseBuilder for level-appropriate response
        base_data = {"success": success, "moved_count": moved_count, "failed_count": len(failed_memory_ids)}

        standard_data = {"target_scope": request.target_scope, "moved_memories": moved_memories}

        full_data = {
            "move_summary": {
                "total_requested": len(request.memory_ids),
                "successfully_moved": moved_count,
                "failed_moves": len(failed_memory_ids),
                "success_rate": moved_count / len(request.memory_ids) if request.memory_ids else 0,
            },
            "failed_memory_ids": failed_memory_ids,
        }

        return ResponseBuilder.build_response(request.response_level, base_data, standard_data, full_data)

    except Exception as e:
        error_msg = f"Failed to move memories: {e}"
        await ctx.error(error_msg)

        base_data = {"success": False, "error": error_msg, "moved_count": 0, "failed_count": len(request.memory_ids)}

        return ResponseBuilder.build_response(request.response_level, base_data)


async def handle_memory_discover_associations(
    memory_id: str, ctx: Any, limit: int = 10, similarity_threshold: float = 0.1
) -> Dict[str, Any]:
    """Handle memory_discover_associations tool requests."""
    try:
        await ctx.info(f"Discovering associations for memory: {memory_id}")

        # Use comprehensive memory manager access
        manager = await get_or_create_memory_manager()
        if not manager:
            error_msg = "No memory manager available"
            await ctx.error(error_msg)
            raise RuntimeError(error_msg)

        # Get the source memory
        source_memory = await manager.get_memory(memory_id)
        if not source_memory:
            error_msg = f"Memory not found: {memory_id}"
            await ctx.error(error_msg)
            raise RuntimeError(error_msg)

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
                search_results = await manager.search_memories(
                    query=keyword_query,
                    limit=limit + 1,
                    min_score=similarity_threshold,
                )

        # Filter out the source memory and format results
        associations = []
        for result in search_results:
            # Handle different possible result formats
            if isinstance(result, dict):
                # If result is already a dict with memory key
                memory = result.get("memory")
                similarity = result.get("similarity", result.get("similarity_score", 1.0))
            # else:
            #     # If result is a memory object directly (currently unreachable)
            #     memory = result
            #     similarity = getattr(result, "similarity_score", 1.0)

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
    """Manage sessions and cleanup using SingletonMemoryManager"""
    try:
        await ctx.info(f"Session management action: {request.action}")

        # Get memory manager instance
        manager = await get_or_create_memory_manager()
        if not manager:
            raise RuntimeError("Memory manager not available")

        if request.action == "create":
            # Create a new session scope
            session_id = request.session_id or f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            session_scope = f"session/{session_id}"

            # Add a session marker memory using memory manager
            session_memory = await manager.store_memory(
                scope=session_scope,
                content=f"Session created: {session_id}",
                metadata={"session_marker": True, "created_by": "session_manage"},
                category="session",
                tags=["session", "marker"],
            )

            if not session_memory:
                raise RuntimeError("Failed to create session marker memory")

            await ctx.info(f"Created session: {session_id}")

            return SessionManageResponse(
                success=True,
                message=f"Created session: {session_id}",
                data={"action": "create", "session_id": session_id},
                session=SessionInfo(
                    session_id=session_id,
                    created_at=session_memory.created_at,
                    memory_count=1,
                    last_activity=session_memory.created_at,
                ),
                sessions=[],
            )

        elif request.action == "list":
            # List all active sessions by searching session scope
            session_memories = await manager.search_memories(
                query="", scope="session", include_child_scopes=True, limit=1000  # Empty query to get all
            )

            # Group by session ID
            session_scopes = {}
            for memory_result in session_memories:
                memory = memory_result.get("memory") if isinstance(memory_result, dict) else memory_result
                if not memory:
                    continue

                scope = memory.scope
                if scope.startswith("session/"):
                    session_id = scope.split("/", 1)[1] if "/" in scope else scope
                    if session_id not in session_scopes:
                        session_scopes[session_id] = {
                            "memories": [],
                            "created_at": memory.created_at,
                            "last_updated": memory.created_at or memory.updated_at,
                        }
                    session_scopes[session_id]["memories"].append(memory)
                    if memory.updated_at:
                        session_scopes[session_id]["last_updated"] = max(
                            session_scopes[session_id]["last_updated"] or memory.created_at, memory.updated_at
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

            # Get all session memories
            session_memories = await manager.search_memories(
                query="", scope="session", include_child_scopes=True, limit=1000
            )

            cleaned_count = 0
            for memory_result in session_memories:
                memory = memory_result.get("memory") if isinstance(memory_result, dict) else memory_result
                if not memory:
                    continue

                # Check if memory is older than cutoff
                memory_date = memory.created_at
                if isinstance(memory_date, str):
                    try:
                        memory_date = datetime.fromisoformat(memory_date.replace("Z", "+00:00"))
                    except (ValueError, AttributeError) as date_error:
                        await ctx.error(f"Failed to parse date for memory {memory.id}: {date_error} - skipping memory")
                        continue  # Skip this memory and continue with next one

                if memory_date < cutoff_date:
                    success = await manager.delete_memory(memory.id)
                    if success:
                        cleaned_count += 1

            await ctx.info(f"Cleaned up {cleaned_count} old session memories")

            return SessionManageResponse(
                success=True,
                message=f"Cleaned up {cleaned_count} old session memories",
                data={"action": "cleanup", "cleaned_count": cleaned_count},
                session=None,
                sessions=[],
                cleaned_sessions=[f"session-cleanup-{i}" for i in range(cleaned_count)],
            )

        else:
            raise ValueError(f"Unknown action: {request.action}")

    except Exception as e:
        await ctx.error(f"Failed to manage session: {e}")
        return SessionManageResponse(
            success=False,
            message=f"Failed to manage session: {e}",
            data={"action": request.action, "error": str(e)},
            session=None,
            sessions=[],
        )
