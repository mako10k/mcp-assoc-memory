"""Additional memory tools for MCP associative memory server."""

import uuid
from typing import Any, Dict
from datetime import datetime, timedelta

from ...core import memory_manager
from ..models.requests import MemoryMoveRequest, SessionManageRequest
from ..models.responses import (
    MemoryMoveResponse,
    MemoryDiscoverAssociationsResponse,
    SessionManageResponse,
    SessionInfo,
    SearchResultWithAssociations,
)
from ...simple_persistence import get_persistent_storage

# Get storage
memory_storage, persistence = get_persistent_storage()

async def handle_memory_move(request: MemoryMoveRequest, ctx: Any) -> Dict[str, Any]:
    """Handle memory_move tool requests."""
    try:
        # Move implementation would go here - this is a placeholder
        # for the full implementation that exists in the handlers
        await ctx.info(f"Moving {len(request.memory_ids)} memories to scope: {request.target_scope}")
        
        moved_count = 0
        for memory_id in request.memory_ids:
            if memory_id in memory_storage:
                memory_storage[memory_id]["scope"] = request.target_scope
                moved_count += 1
        
        if moved_count > 0:
            persistence.save_memories(memory_storage)
        
        await ctx.info(f"Successfully moved {moved_count} memories")
        
        return MemoryMoveResponse(
            success=True,
            moved_count=len(request.memory_ids),
            target_scope=request.target_scope,
            moved_memories=[]
        ).model_dump()
        
    except Exception as e:
        await ctx.error(f"Failed to move memories: {e}")
        return {
            "success": False,
            "error": f"Failed to move memories: {e}",
            "data": {}
        }


async def handle_memory_discover_associations(
    memory_id: str, 
    ctx: Any, 
    limit: int = 10, 
    similarity_threshold: float = 0.1
) -> Dict[str, Any]:
    """Handle memory_discover_associations tool requests."""
    try:
        await ctx.info(f"Discovering associations for memory: {memory_id}")

        # Retrieve related memories using association traversal
        related_memories = await memory_manager.get_related_memories(
            memory_id,
            min_strength=similarity_threshold,
            limit=limit,
        )

        return MemoryDiscoverAssociationsResponse(
            success=True,
            message="Associations discovered",
            data={},
            source_memory=None,
            associations=[
                SearchResultWithAssociations(
                    memory=mem,
                    similarity_score=1.0,
                    associations=[],
                )
                for mem in related_memories
            ],
            total_found=len(related_memories),
        ).model_dump()
        
    except Exception as e:
        await ctx.error(f"Failed to discover associations: {e}")
        return {
            "success": False,
            "error": f"Failed to discover associations: {e}",
            "data": {}
        }


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
                "created_at": datetime.now()
            }
            memory_storage[session_memory["memory_id"]] = session_memory
            
            # Save to persistent storage
            persistence.save_memories(memory_storage)
            
            await ctx.info(f"Created session: {session_id}")
            
            return SessionManageResponse(
                action="create",
                session_id=session_id,
                active_sessions=[SessionInfo(
                    session_id=session_id,
                    scope=session_scope,
                    memory_count=1,
                    created_at=datetime.now(),
                    last_updated=datetime.now()
                )]
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
                            "last_updated": memory_data["created_at"]
                        }
                    session_scopes[session_id]["memories"].append(memory_data)
                    session_scopes[session_id]["last_updated"] = max(
                        session_scopes[session_id]["last_updated"],
                        memory_data["created_at"]
                    )
            
            active_sessions = [
                SessionInfo(
                    session_id=session_id,
                    scope=data["scope"],
                    memory_count=len(data["memories"]),
                    created_at=data["created_at"],
                    last_updated=data["last_updated"]
                )
                for session_id, data in session_scopes.items()
            ]
            
            await ctx.info(f"Found {len(active_sessions)} active sessions")
            
            return SessionManageResponse(
                action="list",
                active_sessions=active_sessions
            )
        
        elif request.action == "cleanup":
            # Clean up old sessions
            cutoff_date = datetime.now() - timedelta(days=request.max_age_days or 7)
            cleaned_count = 0
            
            memories_to_delete = []
            for memory_id, memory_data in memory_storage.items():
                if (memory_data["scope"].startswith("session/") and
                        memory_data["created_at"] < cutoff_date):
                    memories_to_delete.append(memory_id)
            
            for memory_id in memories_to_delete:
                del memory_storage[memory_id]
                cleaned_count += 1
            
            # Save to persistent storage if any memories were cleaned
            if cleaned_count > 0:
                persistence.save_memories(memory_storage)
            
            await ctx.info(f"Cleaned up {cleaned_count} old session memories")
            
            return SessionManageResponse(
                action="cleanup",
                active_sessions=[],
                cleaned_sessions=cleaned_count
            )
        
        else:
            raise ValueError(f"Unknown action: {request.action}")
        
    except Exception as e:
        await ctx.error(f"Failed to manage session: {e}")
        raise
