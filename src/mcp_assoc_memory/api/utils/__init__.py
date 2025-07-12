"""
Utility functions initialization
"""

from .scope_utils import (
    build_scope_hierarchy,
    flatten_scope_hierarchy,
    get_child_scopes,
    get_parent_scope,
    get_scope_depth,
    get_scope_siblings,
    is_descendant_scope,
    normalize_scope_path,
    parts_to_scope_path,
    scope_path_to_parts,
    validate_scope_path,
)

__all__ = [
    "validate_scope_path",
    "get_child_scopes",
    "build_scope_hierarchy",
    "flatten_scope_hierarchy",
    "normalize_scope_path",
    "get_scope_depth",
    "get_parent_scope",
    "is_descendant_scope",
    "get_scope_siblings",
    "scope_path_to_parts",
    "parts_to_scope_path",
]
