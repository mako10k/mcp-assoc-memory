"""Session management tools for MCP associative memory server."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

from fastmcp import Context

from ...core.singleton_memory_manager import get_memory_manager
from ..models.requests import SessionManageRequest
from ..models.responses import SessionInfo, SessionManageResponse
from ..models.common import ResponseBuilder


# Import the ensure_initialized function from memory_tools
async def ensure_initialized():
    """Ensure memory manager is initialized and return it."""
    try:
        memory_manager = await get_memory_manager()
        if memory_manager is None:
            raise RuntimeError("Failed to initialize memory manager")
        return memory_manager
    except Exception as e:
        raise RuntimeError(f"Memory manager initialization failed: {e}")


async def handle_session_manage(request: SessionManageRequest, ctx: Context) -> Dict[str, Any]:
    """Handle session_manage tool requests."""
    try:
        await ctx.info(f"Session management action: {request.action}")

        # Get the memory manager instance
        memory_manager = await ensure_initialized()

        if request.action == "create":
            # Create a new session scope
            session_id = request.session_id or f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            session_scope = f"session/{session_id}"

            # Add a session marker memory
            session_marker_content = f"Session created: {session_id}"

            # Store the session marker memory
            memory = await memory_manager.store_memory(
                content=session_marker_content,
                scope=session_scope,
                metadata={"session_marker": True, "created_by": "session_manage"},
                tags=["session", "marker"],
                category="session_management"
            )

            # Check for None result
            if memory is None:
                error_msg = "Failed to create session - store_memory returned None"
                await ctx.error(error_msg)
                return ResponseBuilder.build_response(
                    request.response_level,
                    {
                        "success": False,
                        "message": error_msg,
                        "error": error_msg,
                        "data": {}
                    }
                )

            await ctx.info(f"Created session: {session_id}")

            # Use ResponseBuilder to build appropriate response
            return ResponseBuilder.build_response(
                request.response_level,
                {
                    "success": True,
                    "message": f"Session {session_id} created successfully",
                    "data": {"session_id": session_id, "scope": session_scope, "marker_memory_id": memory.id}
                }
            )

        elif request.action == "list":
            # Search for all session marker memories
            session_memories = await memory_manager.search_memories(
                query="session_marker:true",
                scope="session",
                include_child_scopes=True,
                limit=1000  # High limit to get all sessions
            )

            # Group by session
            session_scopes = {}
            for memory in session_memories:
                scope = memory.get("scope", "")
                if scope.startswith("session/"):
                    session_id = scope.split("/", 1)[1]
                    if session_id not in session_scopes:
                        session_scopes[session_id] = {
                            "scope": scope,
                            "memories": [],
                            "created_at": memory.get("created_at"),
                            "last_updated": memory.get("created_at"),
                        }
                    session_scopes[session_id]["memories"].append(memory)
                    current_created_at = memory.get("created_at")
                    if current_created_at and session_scopes[session_id]["last_updated"]:
                        if current_created_at > session_scopes[session_id]["last_updated"]:
                            session_scopes[session_id]["last_updated"] = current_created_at

            await ctx.info(f"Found {len(session_scopes)} active sessions")

            return ResponseBuilder.build_response(
                request.response_level,
                {
                    "success": True,
                    "message": f"Found {len(session_scopes)} active sessions",
                    "data": {
                        "session_count": len(session_scopes),
                        "sessions": [
                            {
                                "session_id": session_id,
                                "memory_count": len(data["memories"]),
                                "created_at": data["created_at"].isoformat() if data["created_at"] else None,
                                "last_activity": data["last_updated"].isoformat() if data["last_updated"] else None,
                                "scope": data["scope"]
                            }
                            for session_id, data in session_scopes.items()
                        ]
                    }
                }
            )

        elif request.action == "cleanup":
            # Clean up old sessions
            cutoff_date = datetime.now() - timedelta(days=request.max_age_days or 7)

            # Search for all session memories
            all_session_memories = await memory_manager.search_memories(
                query="",
                scope="session",
                include_child_scopes=True,
                limit=10000  # High limit to get all session memories
            )

            # Filter old memories and delete them
            cleaned_count = 0
            cleaned_sessions = set()

            for memory in all_session_memories:
                created_at = memory.get("created_at")
                if created_at and created_at < cutoff_date:
                    memory_id = memory.get("id") or memory.get("memory_id")
                    if memory_id:
                        await memory_manager.delete_memory(memory_id)
                        cleaned_count += 1
                        # Extract session ID from scope
                        scope = memory.get("scope", "")
                        if scope.startswith("session/"):
                            session_id = scope.split("/", 1)[1]
                            cleaned_sessions.add(session_id)

            await ctx.info(f"Cleaned up {cleaned_count} old session memories from {len(cleaned_sessions)} sessions")

            return ResponseBuilder.build_response(
                request.response_level,
                {
                    "success": True,
                    "message": f"Cleaned up {cleaned_count} old session memories from {len(cleaned_sessions)} sessions",
                    "data": {
                        "cleaned_count": cleaned_count,
                        "cleaned_sessions": list(cleaned_sessions),
                        "cutoff_date": cutoff_date.isoformat()
                    }
                }
            )

        else:
            return ResponseBuilder.build_response(
                request.response_level,
                {
                    "success": False,
                    "message": f"Unknown action: {request.action}",
                    "error": f"Unknown action: {request.action}",
                    "data": {}
                }
            )

    except Exception as e:
        await ctx.error(f"Failed to manage session: {e}")
        return ResponseBuilder.build_response(
            request.response_level,
            {
                "success": False,
                "message": f"Failed to manage session: {e}",
                "error": str(e),
                "data": {}
            }
        )
