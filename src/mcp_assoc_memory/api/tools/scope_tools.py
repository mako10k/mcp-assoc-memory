"""
Scope management tool handlers for MCP Associative Memory Server
"""

import logging
from typing import Any, Dict, List

from fastmcp import Context

from ..models import (
    ErrorResponse,
    MCPResponse,
    ScopeInfo,
    ScopeListRequest,
    ScopeListResponse,
    ScopeRecommendation,
    ScopeSuggestRequest,
    ScopeSuggestResponse,
)
from ..utils import get_child_scopes, get_parent_scope, validate_scope_path

logger = logging.getLogger(__name__)

# Module-level dependencies (set by server initialization)
memory_manager = None


def set_dependencies(mm: Any) -> None:
    """Set module dependencies from server initialization"""
    global memory_manager
    memory_manager = mm


async def handle_scope_list(request: ScopeListRequest, ctx: Context) -> ScopeListResponse:
    """Handle scope list requests"""
    try:
        if memory_manager is None:
            return ErrorResponse(
                success=False, error="Memory manager not initialized", message="Internal server error", data={}
            )

        # Get all scopes from memory manager
        all_scopes = await memory_manager.get_all_scopes()
        logger.info(f"Retrieved {len(all_scopes)} total scopes")

        # Filter by parent scope if specified
        parent_scope = request.parent_scope
        if parent_scope:
            if not validate_scope_path(parent_scope):
                return ErrorResponse(
                    success=False,
                    error="INVALID_SCOPE",
                    message=f"Invalid parent scope format: {parent_scope}",
                    data={},
                )
            filtered_scopes = get_child_scopes(parent_scope, all_scopes)
        else:
            filtered_scopes = all_scopes

        # Build scope info list
        scope_infos = []
        for scope in filtered_scopes:
            memory_count = 0
            if request.include_memory_counts:
                try:
                    memory_count = await memory_manager.get_memory_count_by_scope(scope)
                except Exception as e:
                    logger.warning(f"Failed to get memory count for scope {scope}: {e}")
                    memory_count = 0

            scope_infos.append(
                ScopeInfo(
                    scope=scope,
                    memory_count=memory_count,
                    parent_scope=get_parent_scope(scope),
                    has_children=any(s.startswith(scope + "/") for s in all_scopes if s != scope),
                )
            )

        # Sort by scope name for consistent ordering
        scope_infos.sort(key=lambda x: x.scope)

        return ScopeListResponse(
            success=True,
            message=f"Retrieved {len(scope_infos)} scopes",
            data={"scopes": scope_infos, "parent_scope": parent_scope, "total_count": len(scope_infos)},
        )

    except Exception as e:
        logger.error(f"Error in scope_list: {e}", exc_info=True)
        return ErrorResponse(
            success=False, error="SCOPE_LIST_ERROR", message=f"Failed to list scopes: {str(e)}", data={}
        )


async def handle_scope_suggest(request: ScopeSuggestRequest, ctx: Context) -> ScopeSuggestResponse:
    """Handle scope suggestion requests"""
    try:
        if memory_manager is None:
            return ErrorResponse(
                success=False, error="Memory manager not initialized", message="Internal server error", data={}
            )

        content = request.content.lower()
        current_scope = request.current_scope

        # Simple keyword-based scope suggestion logic
        suggestions = []

        # Technical content patterns
        if any(keyword in content for keyword in ["python", "javascript", "typescript", "java", "c++", "rust", "go"]):
            suggestions.append(
                ScopeRecommendation(
                    scope="learning/programming", confidence=0.9, reasoning="Programming language mentioned"
                )
            )

        if any(keyword in content for keyword in ["api", "rest", "graphql", "endpoint", "http"]):
            suggestions.append(
                ScopeRecommendation(
                    scope="learning/api-design", confidence=0.8, reasoning="API-related content detected"
                )
            )

        # Work-related patterns
        if any(keyword in content for keyword in ["meeting", "standup", "retrospective", "planning"]):
            suggestions.append(
                ScopeRecommendation(scope="work/meetings", confidence=0.9, reasoning="Meeting-related content")
            )

        if any(keyword in content for keyword in ["project", "deadline", "milestone", "task"]):
            suggestions.append(
                ScopeRecommendation(scope="work/projects", confidence=0.8, reasoning="Project management content")
            )

        if any(keyword in content for keyword in ["bug", "issue", "error", "debug", "fix"]):
            suggestions.append(
                ScopeRecommendation(scope="work/debugging", confidence=0.85, reasoning="Debugging or issue resolution")
            )

        # Personal content patterns
        if any(keyword in content for keyword in ["personal", "private", "diary", "journal"]):
            suggestions.append(
                ScopeRecommendation(scope="personal/thoughts", confidence=0.9, reasoning="Personal content detected")
            )

        if any(keyword in content for keyword in ["idea", "innovation", "brainstorm", "concept"]):
            suggestions.append(
                ScopeRecommendation(scope="personal/ideas", confidence=0.8, reasoning="Creative or idea content")
            )

        # Learning patterns
        if any(keyword in content for keyword in ["learn", "study", "tutorial", "course", "training"]):
            suggestions.append(
                ScopeRecommendation(scope="learning/general", confidence=0.8, reasoning="Learning-related content")
            )

        # Context-aware suggestions
        if current_scope:
            # If we're in a work context, suggest work-related scopes
            if current_scope.startswith("work/"):
                if not any(s.scope.startswith("work/") for s in suggestions):
                    suggestions.append(
                        ScopeRecommendation(
                            scope="work/general",
                            confidence=0.6,
                            reasoning="Contextual suggestion based on current work scope",
                        )
                    )

            # If we're in a learning context, suggest learning-related scopes
            elif current_scope.startswith("learning/"):
                if not any(s.scope.startswith("learning/") for s in suggestions):
                    suggestions.append(
                        ScopeRecommendation(
                            scope="learning/general",
                            confidence=0.6,
                            reasoning="Contextual suggestion based on current learning scope",
                        )
                    )

        # Default fallback
        if not suggestions:
            suggestions.append(
                ScopeRecommendation(
                    scope="user/default", confidence=0.5, reasoning="Default scope for unclassified content"
                )
            )

        # Sort by confidence (highest first)
        suggestions.sort(key=lambda x: x.confidence, reverse=True)

        # Return top suggestion as primary, others as alternatives
        primary = suggestions[0]
        alternatives = suggestions[1:5]  # Limit to top 5 alternatives

        return ScopeSuggestResponse(
            success=True,
            message=f"Generated {len(suggestions)} scope suggestions",
            data={
                "suggested_scope": primary.scope,
                "confidence": primary.confidence,
                "reasoning": primary.reasoning,
                "alternatives": alternatives,
                "current_scope": current_scope,
            },
        )

    except Exception as e:
        logger.error(f"Error in scope_suggest: {e}", exc_info=True)
        return ErrorResponse(
            success=False, error="SCOPE_SUGGEST_ERROR", message=f"Failed to suggest scope: {str(e)}", data={}
        )
