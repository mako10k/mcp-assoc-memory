"""
記憶モデル定義
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid


class MemoryDomain(Enum):
    """記憶ドメイン"""
    GLOBAL = "global"      # システム全体で共有
    USER = "user"          # ユーザー固有
    PROJECT = "project"    # プロジェクト固有
    SESSION = "session"    # セッション固有


@dataclass
class Memory:
    """記憶レコード"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    domain: MemoryDomain = MemoryDomain.USER
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None

    # アクセス制御
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None

    # タイムスタンプ
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    accessed_at: datetime = field(default_factory=datetime.utcnow)

    # 統計情報
    access_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "domain": self.domain.value,
            "content": self.content,
            "metadata": self.metadata,
            "tags": self.tags,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat(),
            "access_count": self.access_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """辞書から復元"""
        return cls(
            id=data["id"],
            domain=MemoryDomain(data["domain"]),
            content=data["content"],
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            user_id=data.get("user_id"),
            project_id=data.get("project_id"),
            session_id=data.get("session_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            accessed_at=datetime.fromisoformat(data["accessed_at"]),
            access_count=data.get("access_count", 0),
        )

    def update_access(self):
        """アクセス情報を更新"""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1


@dataclass
class MemorySearchResult:
    """記憶検索結果"""
    memory: Memory
    similarity_score: float
    match_type: str  # "semantic", "keyword", "tag"
    match_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryStats:
    """記憶統計情報"""
    total_count: int = 0
    domain_counts: Dict[str, int] = field(default_factory=dict)
    tag_counts: Dict[str, int] = field(default_factory=dict)
    recent_activity: List[Dict[str, Any]] = field(default_factory=list)
    storage_size_mb: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
