"""
プロジェクトモデル定義
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ProjectRole(Enum):
    """プロジェクトロール"""
    OWNER = "owner"        # オーナー（全権限）
    ADMIN = "admin"        # 管理者（メンバー管理可能）
    MEMBER = "member"      # メンバー（読み書き可能）
    VIEWER = "viewer"      # 閲覧者（読み取り専用）


@dataclass
class Project:
    """プロジェクト"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    owner_id: str = ""

    # 設定
    is_public: bool = False
    memory_retention_days: Optional[int] = None  # None = 無制限
    max_memory_count: Optional[int] = None       # None = 無制限

    # メタデータ
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    # タイムスタンプ
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # 統計情報
    memory_count: int = 0
    member_count: int = 0
    last_activity: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "is_public": self.is_public,
            "memory_retention_days": self.memory_retention_days,
            "max_memory_count": self.max_memory_count,
            "metadata": self.metadata,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "memory_count": self.memory_count,
            "member_count": self.member_count,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        """辞書から復元"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get(
                "description",
                ""),
            owner_id=data["owner_id"],
            is_public=data.get(
                "is_public",
                False),
            memory_retention_days=data.get("memory_retention_days"),
            max_memory_count=data.get("max_memory_count"),
            metadata=data.get(
                "metadata",
                {}),
            tags=data.get(
                "tags",
                []),
            created_at=datetime.fromisoformat(
                data["created_at"]),
            updated_at=datetime.fromisoformat(
                data["updated_at"]),
            memory_count=data.get(
                "memory_count",
                0),
            member_count=data.get(
                "member_count",
                0),
            last_activity=datetime.fromisoformat(
                data["last_activity"]) if data.get("last_activity") else None,
        )


@dataclass
class ProjectMember:
    """プロジェクトメンバー"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    user_id: str = ""
    role: ProjectRole = ProjectRole.MEMBER

    # 権限設定
    can_read: bool = True
    can_write: bool = True
    can_delete: bool = False
    can_manage_members: bool = False

    # メタデータ
    invited_by: Optional[str] = None
    notes: str = ""

    # タイムスタンプ
    joined_at: datetime = field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "role": self.role.value,
            "can_read": self.can_read,
            "can_write": self.can_write,
            "can_delete": self.can_delete,
            "can_manage_members": self.can_manage_members,
            "invited_by": self.invited_by,
            "notes": self.notes,
            "joined_at": self.joined_at.isoformat(),
            "last_active": self.last_active.isoformat() if self.last_active else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectMember":
        """辞書から復元"""
        return cls(
            id=data["id"], project_id=data["project_id"], user_id=data["user_id"], role=ProjectRole(
                data["role"]), can_read=data.get(
                "can_read", True), can_write=data.get(
                "can_write", True), can_delete=data.get(
                    "can_delete", False), can_manage_members=data.get(
                        "can_manage_members", False), invited_by=data.get("invited_by"), notes=data.get(
                            "notes", ""), joined_at=datetime.fromisoformat(
                                data["joined_at"]), last_active=datetime.fromisoformat(
                                    data["last_active"]) if data.get("last_active") else None, )

    def has_permission(self, action: str) -> bool:
        """権限チェック"""
        permission_map = {
            "read": self.can_read,
            "write": self.can_write,
            "delete": self.can_delete,
            "manage_members": self.can_manage_members,
        }
        return permission_map.get(action, False)


@dataclass
class UserSession:
    """ユーザーセッション"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    project_id: Optional[str] = None
    session_name: str = ""

    # セッション状態
    is_active: bool = True
    memory_count: int = 0

    # タイムスタンプ
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "session_name": self.session_name,
            "is_active": self.is_active,
            "memory_count": self.memory_count,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserSession":
        """辞書から復元"""
        return cls(
            id=data["id"], user_id=data["user_id"], project_id=data.get("project_id"), session_name=data.get(
                "session_name", ""), is_active=data.get(
                "is_active", True), memory_count=data.get(
                "memory_count", 0), created_at=datetime.fromisoformat(
                    data["created_at"]), last_activity=datetime.fromisoformat(
                        data["last_activity"]), expires_at=datetime.fromisoformat(
                            data["expires_at"]) if data.get("expires_at") else None, )
