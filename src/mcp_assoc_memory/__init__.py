"""
MCP Associative Memory Server - Scope-based knowledge management system for LLMs
"""

__version__ = "2.0.0"
__author__ = "MCP Assoc Memory Team"
__description__ = "MCP Associative Memory Server - Scope-based hierarchical memory management"

from .models.memory import Memory
from .models.project import Project, ProjectMember, ProjectRole

__all__ = [
    "Memory",
    "Project",
    "ProjectMember",
    "ProjectRole",
]
