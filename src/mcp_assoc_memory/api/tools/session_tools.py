"""Session management tools for MCP associative memory server."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

from ...storage.simple_persistence import memory_storage, persistence
from ..models.requests import SessionManageRequest
from ..models.responses import SessionManageResponse, SessionInfo


async def handle_session_manage(request: SessionManageRequest, ctx: Any) -> Dict[str, Any]:
    """Handle session_manage tool requests."""
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
                message=f"Session {session_id} created successfully",
                data={"session_id": session_id, "scope": session_scope},
                session=SessionInfo(
                    session_id=session_id, memory_count=1, created_at=datetime.now(), last_activity=datetime.now()
                ),
            ).model_dump()

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
                    memory_count=len(data["memories"]),
                    created_at=data["created_at"],
                    last_activity=data["last_updated"],
                )
                for session_id, data in session_scopes.items()
            ]

            await ctx.info(f"Found {len(active_sessions)} active sessions")

            return SessionManageResponse(
                success=True,
                message=f"Found {len(active_sessions)} active sessions",
                data={"session_count": len(active_sessions)},
                sessions=active_sessions,
            ).model_dump()

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
                data={"cleaned_count": cleaned_count},
                cleaned_sessions=[],  # TODO: Return actual cleaned session IDs
            ).model_dump()

        else:
            return {"success": False, "error": f"Unknown action: {request.action}", "data": {}}

    except Exception as e:
        await ctx.error(f"Failed to manage session: {e}")
        return {"success": False, "error": f"Failed to manage session: {e}", "data": {}}
