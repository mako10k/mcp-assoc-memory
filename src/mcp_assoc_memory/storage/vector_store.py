"""
ChromaDBベクトルストア実装
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from .base import BaseVectorStore
from ..models.memory import MemoryDomain
from ..utils.logging import get_memory_logger


logger = get_memory_logger(__name__)


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB実装のベクトルストア"""
    
    def __init__(
        self,
        persist_directory: str = "./data/chroma_db",
        host: Optional[str] = None,
        port: Optional[int] = None
    ):
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB is not installed. "
                "Install it with: pip install chromadb"
            )
        
        self.persist_directory = persist_directory
        self.host = host
        self.port = port
        self.client = None
        self.collections = {}
        
    async def initialize(self) -> None:
        """ChromaDBクライアントを初期化"""
        try:
            if self.host and self.port:
                # リモート接続
                self.client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port
                )
            else:
                # ローカル永続化
                self.client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            
            # 各ドメイン用のコレクションを初期化
            for domain in MemoryDomain:
                collection_name = f"memories_{domain.value}"
                try:
                    collection = self.client.get_collection(collection_name)
                except Exception:
                    # コレクションが存在しない場合は作成
                    collection = self.client.create_collection(
                        name=collection_name,
                        metadata={"domain": domain.value}
                    )
                self.collections[domain] = collection
            
            logger.info(
                "ChromaDB initialized",
                extra_data={
                    "persist_directory": self.persist_directory,
                    "collections": list(self.collections.keys())
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to initialize ChromaDB",
                error_code="CHROMADB_INIT_ERROR",
                error=str(e)
            )
            raise
    
    async def close(self) -> None:
        """クライアントを閉じる"""
        # ChromaDBクライアントは明示的なclose不要
        self.client = None
        self.collections = {}
        logger.info("ChromaDB client closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            if not self.client:
                return {"status": "error", "message": "Client not initialized"}
            
            # 各コレクションの統計を取得
            collection_stats = {}
            for domain, collection in self.collections.items():
                try:
                    count = collection.count()
                    collection_stats[domain.value] = {
                        "count": count,
                        "status": "healthy"
                    }
                except Exception as e:
                    collection_stats[domain.value] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            return {
                "status": "healthy",
                "client_type": type(self.client).__name__,
                "collections": collection_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def store_vector(
        self,
        memory_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """ベクトルを保存"""
        try:
            domain = MemoryDomain(metadata.get("domain", "user"))
            collection = self.collections[domain]
            
            # ChromaDBに保存
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: collection.add(
                    ids=[memory_id],
                    embeddings=[embedding],
                    metadatas=[metadata]
                )
            )
            
            logger.info(
                "Vector stored",
                extra_data={
                    "memory_id": memory_id,
                    "domain": domain.value,
                    "embedding_dim": len(embedding)
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to store vector",
                error_code="VECTOR_STORE_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            raise
    
    async def search_similar(
        self,
        query_embedding: List[float],
        domain: MemoryDomain,
        limit: int = 10,
        min_similarity: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """類似ベクトルを検索"""
        try:
            collection = self.collections[domain]
            
            # ChromaDBで検索
            query_kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": limit
            }
            
            # フィルターがある場合は追加
            if filters:
                query_kwargs["where"] = filters
            
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: collection.query(**query_kwargs)
            )
            
            # 結果を整形
            similar_memories = []
            if results["ids"] and results["ids"][0]:
                for i, memory_id in enumerate(results["ids"][0]):
                    distance = results["distances"][0][i]
                    similarity = 1.0 - distance  # 距離を類似度に変換
                    
                    if similarity >= min_similarity:
                        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                        
                        similar_memories.append({
                            "memory_id": memory_id,
                            "similarity": similarity,
                            "distance": distance,
                            "metadata": metadata
                        })
            
            logger.info(
                "Vector search completed",
                extra_data={
                    "domain": domain.value,
                    "query_dim": len(query_embedding),
                    "result_count": len(similar_memories),
                    "min_similarity": min_similarity
                }
            )
            
            return similar_memories
            
        except Exception as e:
            logger.error(
                "Failed to search similar vectors",
                error_code="VECTOR_SEARCH_ERROR",
                domain=domain.value,
                error=str(e)
            )
            raise
    
    async def delete_vector(self, memory_id: str) -> bool:
        """ベクトルを削除"""
        try:
            # 全ドメインから削除を試行
            deleted = False
            for domain, collection in self.collections.items():
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: collection.delete(ids=[memory_id])
                    )
                    deleted = True
                    logger.info(
                        "Vector deleted",
                        extra_data={
                            "memory_id": memory_id,
                            "domain": domain.value
                        }
                    )
                except Exception:
                    # このドメインにはベクトルが存在しない
                    continue
            
            return deleted
            
        except Exception as e:
            logger.error(
                "Failed to delete vector",
                error_code="VECTOR_DELETE_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            return False
    
    async def update_metadata(
        self,
        memory_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """メタデータを更新"""
        try:
            domain = MemoryDomain(metadata.get("domain", "user"))
            collection = self.collections[domain]
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: collection.update(
                    ids=[memory_id],
                    metadatas=[metadata]
                )
            )
            
            logger.info(
                "Vector metadata updated",
                extra_data={
                    "memory_id": memory_id,
                    "domain": domain.value
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to update vector metadata",
                error_code="VECTOR_METADATA_UPDATE_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            return False
    
    async def get_collection_stats(
        self, domain: MemoryDomain
    ) -> Dict[str, Any]:
        """コレクション統計を取得"""
        try:
            collection = self.collections[domain]
            
            count = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: collection.count()
            )
            
            return {
                "domain": domain.value,
                "total_vectors": count,
                "collection_name": f"memories_{domain.value}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(
                "Failed to get collection stats",
                error_code="COLLECTION_STATS_ERROR",
                domain=domain.value,
                error=str(e)
            )
            return {
                "domain": domain.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
