"""
Utility functions for MCP Associative Memory Server
"""

from typing import List, Dict, Any
import re


def validate_scope_path(scope: str) -> bool:
    """
    Validate scope path format

    Args:
        scope: Scope path to validate

    Returns:
        True if valid scope path, False otherwise

    Rules:
        - Must contain only letters, numbers, underscores, hyphens, and forward slashes
        - Cannot start or end with forward slash
        - Cannot contain consecutive forward slashes
        - Maximum depth of 10 levels
        - Cannot use reserved patterns like . or ..
    """
    if not scope or not isinstance(scope, str):
        return False

    # Basic pattern validation
    if not re.match(r"^[a-zA-Z0-9_/-]+$", scope):
        return False

    # Cannot start or end with slash
    if scope.startswith("/") or scope.endswith("/"):
        return False

    # Cannot contain consecutive slashes
    if "//" in scope:
        return False

    # Check depth (maximum 10 levels)
    parts = scope.split("/")
    if len(parts) > 10:
        return False

    # Check for reserved patterns
    for part in parts:
        if part in [".", "..", ""]:
            return False

    return True


def get_child_scopes(parent_scope: str, all_scopes: List[str]) -> List[str]:
    """
    Get direct child scopes of a parent scope

    Args:
        parent_scope: Parent scope path
        all_scopes: List of all available scopes

    Returns:
        List of direct child scope paths
    """
    children = []
    parent_prefix = parent_scope + "/"

    for scope in all_scopes:
        if scope.startswith(parent_prefix):
            # Get the part after parent prefix
            remainder = scope[len(parent_prefix) :]
            # Check if it's a direct child (no further slashes)
            if "/" not in remainder:
                children.append(scope)

    return sorted(children)


def build_scope_hierarchy(all_scopes: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Build hierarchical structure from flat scope list

    Args:
        all_scopes: List of all scope paths

    Returns:
        Nested dictionary representing scope hierarchy
    """
    hierarchy: Dict[str, Any] = {}

    for scope in sorted(all_scopes):
        parts = scope.split("/")
        current = hierarchy

        for i, part in enumerate(parts):
            if part not in current:
                current[part] = {"children": {}, "full_path": "/".join(parts[: i + 1])}
            current = current[part]["children"]

    return hierarchy


def flatten_scope_hierarchy(hierarchy: Dict[str, Dict[str, Any]], prefix: str = "") -> List[str]:
    """
    Flatten hierarchical scope structure back to flat list

    Args:
        hierarchy: Nested scope hierarchy
        prefix: Current path prefix

    Returns:
        Flat list of scope paths
    """
    scopes = []

    for key, value in hierarchy.items():
        full_path = f"{prefix}/{key}" if prefix else key
        scopes.append(full_path)

        if "children" in value and value["children"]:
            scopes.extend(flatten_scope_hierarchy(value["children"], full_path))

    return scopes


def normalize_scope_path(scope: str) -> str:
    """
    Normalize scope path by removing extra slashes and trimming

    Args:
        scope: Raw scope path

    Returns:
        Normalized scope path
    """
    if not scope:
        return "user/default"

    # Remove leading/trailing whitespace and slashes
    normalized = scope.strip().strip("/")

    # Replace multiple consecutive slashes with single slash
    normalized = re.sub(r"/+", "/", normalized)

    # Return default if empty after normalization
    if not normalized:
        return "user/default"

    return normalized


def get_scope_depth(scope: str) -> int:
    """
    Get the depth of a scope path

    Args:
        scope: Scope path

    Returns:
        Depth level (number of path segments)
    """
    if not scope:
        return 0
    return len(scope.split("/"))


def get_parent_scope(scope: str) -> str:
    """
    Get the parent scope of a given scope

    Args:
        scope: Child scope path

    Returns:
        Parent scope path, or empty string if at root level
    """
    if not scope or "/" not in scope:
        return ""

    parts = scope.split("/")
    return "/".join(parts[:-1])


def is_descendant_scope(child_scope: str, parent_scope: str) -> bool:
    """
    Check if a scope is a descendant of another scope

    Args:
        child_scope: Potential child scope
        parent_scope: Potential parent scope

    Returns:
        True if child_scope is a descendant of parent_scope
    """
    if not child_scope or not parent_scope:
        return False

    return child_scope.startswith(parent_scope + "/") or child_scope == parent_scope


def get_scope_siblings(scope: str, all_scopes: List[str]) -> List[str]:
    """
    Get sibling scopes (scopes at the same level with same parent)

    Args:
        scope: Target scope
        all_scopes: List of all available scopes

    Returns:
        List of sibling scope paths
    """
    parent = get_parent_scope(scope)
    if not parent:
        # Root level scopes
        return [s for s in all_scopes if "/" not in s and s != scope]

    return get_child_scopes(parent, all_scopes)


def scope_path_to_parts(scope: str) -> List[str]:
    """
    Convert scope path to list of parts

    Args:
        scope: Scope path

    Returns:
        List of scope path parts
    """
    if not scope:
        return []
    return scope.split("/")


def parts_to_scope_path(parts: List[str]) -> str:
    """
    Convert list of parts to scope path

    Args:
        parts: List of scope path parts

    Returns:
        Scope path string
    """
    if not parts:
        return ""
    return "/".join(str(part) for part in parts if part)
