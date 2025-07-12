"""
ストレージ基底クラス定義
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ..models.association import Association
from ..models.memory import Memory


class BaseStorage(ABC):
    """ストレージの抽象基底クラス"""

    @abstractmethod
    async def initialize(self) -> None:
        """ストレージを初期化"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """ストレージを閉じる"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        pass


class BaseVectorStore(BaseStorage):
    @abstractmethod
    async def store_embedding(self, memory_id: str, embedding: Any, metadata: Dict[str, Any]) -> bool:
        """埋め込みを保存"""
        pass

    @abstractmethod
    async def get_embedding(self, memory_id: str) -> Optional[Any]:
        """埋め込みを取得"""
        pass

    @abstractmethod
    async def delete_embedding(self, memory_id: str) -> bool:
        """埋め込みを削除"""
        pass

    @abstractmethod
    async def search(
        self, embedding: Any, scope: str, limit: int = 10, min_score: float = 0.7
    ) -> List["Tuple[str, float]"]:
        """ベクトル検索（ID, score返却）"""
        pass

    """ベクトルストレージの抽象基底クラス"""

    @abstractmethod
    async def store_vector(self, memory_id: str, embedding: List[float], metadata: Dict[str, Any]) -> None:
        """ベクトルを保存"""
        pass

    @abstractmethod
    async def search_similar(
        self,
        query_embedding: List[float],
        scope: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
        include_child_scopes: bool = False,
    ) -> List[Dict[str, Any]]:
        """Search similar vectors"""
        pass

    @abstractmethod
    async def delete_vector(self, memory_id: str) -> bool:
        """ベクトルを削除"""
        pass

    @abstractmethod
    async def update_metadata(self, memory_id: str, metadata: Dict[str, Any]) -> bool:
        """メタデータを更新"""
        pass

    @abstractmethod
    async def get_collection_stats(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """コレクション統計を取得"""
        pass


class BaseMetadataStore(BaseStorage):
    @abstractmethod
    async def get_memories_by_scope(
        self, scope: Optional[str] = None, limit: int = 1000, order_by: Optional[str] = None
    ) -> List[Memory]:
        """スコープごとの記憶一覧取得"""
        pass

    @abstractmethod
    async def get_memory_stats(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """記憶統計取得"""
        pass

    @abstractmethod
    async def search_by_tags(
        self, tags: List[str], scope: Optional[str] = None, match_all: bool = False, limit: int = 10
    ) -> List[Memory]:
        """タグ検索"""
        pass

    @abstractmethod
    async def search_by_timerange(
        self, start_date: datetime, end_date: datetime, scope: Optional[str] = None, limit: int = 10
    ) -> List[Memory]:
        """時間範囲検索"""
        pass

    @abstractmethod
    async def advanced_search(
        self,
        scope: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 30,
    ) -> List[Memory]:
        """高度検索（複合条件）"""
        pass

    @abstractmethod
    async def update_access_stats(self, memory_id: str, access_count: int) -> bool:
        """アクセス統計を更新"""
        pass

    @abstractmethod
    async def get_memory_associations(self, memory_id: str) -> List[Association]:
        """記憶に紐づく関連性一覧取得"""
        pass

    @abstractmethod
    async def batch_delete_memories(self, criteria: Dict[str, Any]) -> int:
        """一括削除"""
        pass

    @abstractmethod
    async def cleanup_orphans(self) -> int:
        """孤立データのクリーンアップ"""
        pass

    @abstractmethod
    async def reindex(self) -> None:
        """インデックス再構築"""
        pass

    @abstractmethod
    async def vacuum(self) -> None:
        """VACUUM実行"""
        pass

    """メタデータストレージの抽象基底クラス"""

    @abstractmethod
    async def store_memory(self, memory: Memory) -> str:
        """記憶を保存"""
        pass

    @abstractmethod
    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """記憶を取得"""
        pass

    @abstractmethod
    async def update_memory(self, memory: Memory) -> bool:
        """記憶を更新"""
        pass

    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """記憶を削除"""
        pass

    @abstractmethod
    async def search_memories(
        self,
        scope: Optional[str] = None,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Memory]:
        """記憶を検索"""
        pass

    @abstractmethod
    async def get_memory_count(
        self, scope: Optional[str] = None, user_id: Optional[str] = None, project_id: Optional[str] = None
    ) -> int:
        """記憶数を取得"""
        pass

    @abstractmethod
    async def store_association(self, association: Association) -> str:
        """関連性を保存"""
        pass

    @abstractmethod
    async def get_associations(
        self, memory_id: str, direction: Optional[str] = None  # 'incoming', 'outgoing', None(both)
    ) -> List[Association]:
        """関連性を取得"""
        pass

    @abstractmethod
    @abstractmethod
    async def delete_association(self, association_id: str) -> bool:
        """Delete association relationship"""
        pass

    @abstractmethod
    async def get_all_scopes(self) -> List[str]:
        """Get all available scopes"""
        pass

    @abstractmethod
    async def get_all_memories(self, limit: int = 1000) -> List[Memory]:
        """Get all memories"""
        pass

    @abstractmethod
    async def get_association_count(self, scope: Optional[str] = None) -> int:
        """Get count of associations"""
        pass

    @abstractmethod
    async def update_association(self, association: Association) -> bool:
        """関連性を更新"""
        pass

    @abstractmethod
    async def get_memory_count_by_scope(self, scope: str) -> int:
        """Get count of memories in a specific scope"""
        pass


class BaseGraphStore(BaseStorage):
    @abstractmethod
    async def get_all_association_edges(self, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all association edges (for visualization)"""
        pass

    @abstractmethod
    async def export_graph(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """グラフ構造エクスポート（可視化用）"""
        pass

    """グラフストレージの抽象基底クラス"""

    @abstractmethod
    async def add_memory_node(self, memory: "Memory") -> bool:
        """記憶ノードを追加"""
        pass

    @abstractmethod
    async def add_association_edge(self, association: Association) -> None:
        """関連性エッジを追加"""
        pass

    @abstractmethod
    async def remove_memory_node(self, memory_id: str) -> bool:
        """記憶ノードを削除"""
        pass

    @abstractmethod
    async def remove_association_edge(self, association_id: str) -> bool:
        """関連性エッジを削除"""
        pass

    @abstractmethod
    async def find_shortest_path(
        self, source_memory_id: str, target_memory_id: str, max_depth: int = 6
    ) -> Optional[List[str]]:
        """最短パスを検索"""
        pass

    @abstractmethod
    async def get_neighbors(self, memory_id: str, depth: int = 1, min_strength: float = 0.0) -> List[Dict[str, Any]]:
        """近傍ノードを取得"""
        pass

    @abstractmethod
    async def calculate_centrality(
        self, centrality_type: str = "betweenness"  # betweenness, closeness, degree
    ) -> Dict[str, float]:
        """中心性を計算"""
        pass

    @abstractmethod
    async def detect_communities(self) -> Dict[str, List[str]]:
        """コミュニティを検出"""
        pass

    # 旧export_graphは廃止（新しいexport_graphに統合）


class BaseEmbeddingService(ABC):
    """埋め込みサービスの抽象基底クラス"""

    @abstractmethod
    async def generate_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """テキストの埋め込みを生成"""
        pass

    @abstractmethod
    async def generate_batch_embeddings(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """バッチ埋め込みを生成"""
        pass

    @abstractmethod
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float], method: str = "cosine") -> float:
        """類似度を計算"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        pass


class StorageManager:
    """ストレージマネージャー - 各ストレージを統合管理"""

    def __init__(
        self,
        vector_store: BaseVectorStore,
        metadata_store: BaseMetadataStore,
        graph_store: BaseGraphStore,
        embedding_service: BaseEmbeddingService,
    ):
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        self.graph_store = graph_store
        self.embedding_service = embedding_service

    async def initialize(self) -> None:
        """全ストレージを初期化"""
        await self.vector_store.initialize()
        await self.metadata_store.initialize()
        await self.graph_store.initialize()

    async def close(self) -> None:
        """全ストレージを閉じる"""
        await self.vector_store.close()
        await self.metadata_store.close()
        await self.graph_store.close()

    async def health_check(self) -> Dict[str, Any]:
        """全ストレージのヘルスチェック"""
        return {
            "vector_store": await self.vector_store.health_check(),
            "metadata_store": await self.metadata_store.health_check(),
            "graph_store": await self.graph_store.health_check(),
            "embedding_service": await self.embedding_service.health_check(),
        }
