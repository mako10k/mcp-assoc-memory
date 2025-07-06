"""
MCP連想記憶サーバ - LLM向け記憶ドメイン対応知識管理システム
"""

__version__ = "0.1.0"
__author__ = "MCP Assoc Memory Team"
__description__ = "LLM向け連想記憶MCPサーバ - 記憶ドメイン（グローバル/ユーザ/プロジェクト/セッション）対応"

from .models.memory import Memory, MemoryDomain
from .models.project import Project, ProjectMember, ProjectRole

__all__ = [
    "Memory",
    "MemoryDomain",
    "Project",
    "ProjectMember",
    "ProjectRole",
]
