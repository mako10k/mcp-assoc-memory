"""
ストレージ基底クラス定義
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from ..models.memory import Memory, MemoryDomain
from ..models.association import Association


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
    """ベクトルストレージの抽象基底クラス"""

    @abstractmethod
    async def store_vector(
        self,
        memory_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """ベクトルを保存"""
        pass

    @abstractmethod
    async def search_similar(
        self,
        query_embedding: List[float],
        domain: MemoryDomain,
        limit: int = 10,
        min_similarity: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """類似ベクトルを検索"""
        pass

    @abstractmethod
    async def delete_vector(self, memory_id: str) -> bool:
        """ベクトルを削除"""
        pass

    @abstractmethod
    async def update_metadata(
        self,
        memory_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """メタデータを更新"""
        pass

    @abstractmethod
    async def get_collection_stats(
        self, domain: MemoryDomain
    ) -> Dict[str, Any]:
        """コレクション統計を取得"""
        pass


class BaseMetadataStore(BaseStorage):
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
        domain: MemoryDomain,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Memory]:
        """記憶を検索"""
        pass

    @abstractmethod
    async def get_memory_count(
        self,
        domain: MemoryDomain,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> int:
        """記憶数を取得"""
        pass

    @abstractmethod
    async def store_association(self, association: Association) -> str:
        """関連性を保存"""
        pass

    @abstractmethod
    async def get_associations(
        self,
        memory_id: str,
        direction: Optional[str] = None  # 'incoming', 'outgoing', None(both)
    ) -> List[Association]:
        """関連性を取得"""
        pass

    @abstractmethod
    async def delete_association(self, association_id: str) -> bool:
        """関連性を削除"""
        pass


class BaseGraphStore(BaseStorage):
    """グラフストレージの抽象基底クラス"""

    @abstractmethod
    async def add_memory_node(
        self,
        memory_id: str,
        metadata: Dict[str, Any]
    ) -> None:
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
        self,
        source_memory_id: str,
        target_memory_id: str,
        max_depth: int = 6
    ) -> Optional[List[str]]:
        """最短パスを検索"""
        pass

    @abstractmethod
    async def get_neighbors(
        self,
        memory_id: str,
        depth: int = 1,
        min_strength: float = 0.0
    ) -> List[Dict[str, Any]]:
        """近傍ノードを取得"""
        pass

    @abstractmethod
    async def calculate_centrality(
        self,
        centrality_type: str = "betweenness"  # betweenness, closeness, degree
    ) -> Dict[str, float]:
        """中心性を計算"""
        pass

    @abstractmethod
    async def detect_communities(self) -> Dict[str, List[str]]:
        """コミュニティを検出"""
        pass

    @abstractmethod
    async def export_graph(self, format: str = "graphml") -> str:
        """グラフをエクスポート"""
        pass


class BaseEmbeddingService(ABC):
    """埋め込みサービスの抽象基底クラス"""

    @abstractmethod
    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """テキストの埋め込みを生成"""
        pass

    @abstractmethod
    async def generate_batch_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """バッチ埋め込みを生成"""
        pass

    @abstractmethod
    def calculate_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
        method: str = "cosine"
    ) -> float:
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
        embedding_service: BaseEmbeddingService
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
