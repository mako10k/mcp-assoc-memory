"""
関連性モデル定義
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid


@dataclass
class Association:
    """記憶間の関連性"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_memory_id: str = ""
    target_memory_id: str = ""
    
    # 関連性の種類
    association_type: str = "semantic"  # semantic, temporal, causal, similar
    strength: float = 0.0  # 0.0-1.0の関連強度
    
    # メタデータ
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    
    # 自動生成か手動作成か
    auto_generated: bool = True
    
    # タイムスタンプ
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "source_memory_id": self.source_memory_id,
            "target_memory_id": self.target_memory_id,
            "association_type": self.association_type,
            "strength": self.strength,
            "metadata": self.metadata,
            "description": self.description,
            "auto_generated": self.auto_generated,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Association":
        """辞書から復元"""
        return cls(
            id=data["id"],
            source_memory_id=data["source_memory_id"],
            target_memory_id=data["target_memory_id"],
            association_type=data["association_type"],
            strength=data["strength"],
            metadata=data.get("metadata", {}),
            description=data.get("description"),
            auto_generated=data.get("auto_generated", True),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class AssociationGraph:
    """関連性グラフ"""
    # memory_id -> node_data
    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # association_id -> association
    edges: Dict[str, Association] = field(default_factory=dict)
    
    def add_memory(self, memory_id: str, metadata: Dict[str, Any] = None):
        """記憶ノードを追加"""
        self.nodes[memory_id] = metadata or {}
    
    def add_association(self, association: Association):
        """関連性エッジを追加"""
        self.edges[association.id] = association
    
    def get_related_memories(
        self, memory_id: str, min_strength: float = 0.0
    ) -> List[Dict[str, Any]]:
        """関連する記憶を取得"""
        related = []
        for assoc in self.edges.values():
            if assoc.strength >= min_strength:
                if assoc.source_memory_id == memory_id:
                    related.append({
                        "memory_id": assoc.target_memory_id,
                        "association": assoc,
                        "direction": "outgoing"
                    })
                elif assoc.target_memory_id == memory_id:
                    related.append({
                        "memory_id": assoc.source_memory_id,
                        "association": assoc,
                        "direction": "incoming"
                    })
        return related
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "nodes": self.nodes,
            "edges": {k: v.to_dict() for k, v in self.edges.items()}
        }