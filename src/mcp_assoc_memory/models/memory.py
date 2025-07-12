"""
Memory model definitions
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Memory:
    """Memory record with scope-based organization"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scope: str = "user/default"  # Hierarchical scope (replaces domain)
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None

    # Access control
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None

    # Category
    category: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    accessed_at: Optional[datetime] = field(default_factory=datetime.utcnow)

    # Statistics
    access_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "id": self.id,
            "scope": self.scope,
            "content": self.content,
            "metadata": self.metadata,
            "tags": self.tags,
            "category": self.category,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat() if self.accessed_at else None,
            "access_count": self.access_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Memory":
        """Restore from dictionary"""
        return cls(
            id=data["id"],
            scope=data.get("scope", "user/default"),
            content=data["content"],
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            category=data.get("category"),
            user_id=data.get("user_id"),
            project_id=data.get("project_id"),
            session_id=data.get("session_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            accessed_at=datetime.fromisoformat(data["accessed_at"]) if data.get("accessed_at") else None,
            access_count=data.get("access_count", 0),
        )

    def update_access(self) -> None:
        """アクセス情報を更新"""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1


@dataclass
class MemorySearchResult:
    """Memory search result"""

    memory: Memory
    similarity_score: float
    match_type: str  # "semantic", "keyword", "tag"
    match_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryStats:
    """Memory statistics"""

    total_count: int = 0
    scope_counts: Dict[str, int] = field(default_factory=dict)  # Changed from domain_counts
    tag_counts: Dict[str, int] = field(default_factory=dict)
    recent_activity: List[Dict[str, Any]] = field(default_factory=list)
    storage_size_mb: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)
