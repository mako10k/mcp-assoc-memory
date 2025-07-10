"""
ChromaDBベクトルストア実装
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from ..models.memory import MemoryDomain
from ..utils.logging import get_memory_logger
from ..utils.validation import domain_value
from .base import BaseVectorStore

logger = get_memory_logger(__name__)


class ChromaVectorStore(BaseVectorStore):
    async def store_embedding(self, memory_id: str, embedding: Any, metadata: Dict[str, Any]) -> bool:
        """埋め込みを保存 (memory_manager.py互換)"""
        try:
            await self.store_vector(memory_id, embedding, metadata)
            return True
        except Exception as e:
            logger.error(f"store_embedding error: {e}")
            return False

    async def get_embedding(self, memory_id: str) -> Optional[Any]:
        """埋め込みを取得 (memory_manager.py互換)"""
        # ChromaDBはembedding単体取得APIがないため、ID検索で取得
        for domain, collection in self.collections.items():
            try:
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: collection.get(ids=[memory_id])
                )
                if result["embeddings"] and result["embeddings"][0]:
                    return result["embeddings"][0]
            except Exception:
                continue
        return None

    async def delete_embedding(self, memory_id: str) -> bool:
        """埋め込みを削除 (memory_manager.py互換)"""
        return await self.delete_vector(memory_id)

    async def search(self, embedding: Any, domain, limit: int = 10, min_score: float = 0.7) -> List[Tuple[str, float]]:
        """ベクトル検索 (memory_manager.py互換)"""
        results = await self.search_similar(embedding, domain, limit, min_score)
        return [(r["memory_id"], r["similarity"]) for r in results]

    # 既存のsearch_similar（互換ラッパー）は削除。実装は下部のsearch_similarのみ。
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
                domain_key = domain_value(domain)
                collection_name = f"memories_{domain_key}"
                try:
                    collection = self.client.get_collection(collection_name)
                except Exception:
                    # コレクションが存在しない場合は作成
                    # embedding_functionを設定しないことで、手動でembeddingを管理
                    collection = self.client.create_collection(
                        name=collection_name,
                        metadata={"domain": domain_key},
                        embedding_function=None  # 手動でembeddingを管理
                    )
                self.collections[domain_key] = collection

            logger.info(
                "ChromaDB initialized",
                extra={
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
            for domain_key, collection in self.collections.items():
                try:
                    count = collection.count()
                    collection_stats[domain_key] = {
                        "count": count,
                        "status": "healthy"
                    }
                except Exception as e:
                    collection_stats[domain_key] = {
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
        """ベクトルを保存 (ChromaDBのmetadata仕様に合わせて変換)"""
        try:
            domain = metadata.get("domain", "user")
            domain_key = domain_value(domain)
            collection = self.collections[domain_key]

            # ChromaDBのmetadataはstr/int/float/bool/Noneのみ許容
            def flatten_metadata(md: Dict[str, Any]) -> Dict[str, Any]:
                flat = {}
                for k, v in md.items():
                    if isinstance(v, (str, int, float, bool)):
                        flat[k] = v
                    elif v is None:
                        flat[k] = "null"
                    else:
                        # dictやlist等はstr化
                        flat[k] = str(v)
                return flat

            chroma_metadata = flatten_metadata(metadata)

            # 解析用ログ出力
            logger.info(f"[DEBUG] store_vector metadata(raw): {metadata}")
            logger.info(f"[DEBUG] store_vector chroma_metadata(flat): {chroma_metadata}")

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: collection.add(
                    ids=[memory_id],
                    embeddings=[embedding],
                    metadatas=[chroma_metadata]
                )
            )

            logger.info(
                "Vector stored",
                extra={
                    "memory_id": memory_id,
                    "domain": str(domain),
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
        domain: Any,
        limit: int = 10,
        min_similarity: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """類似ベクトルを検索"""
        try:
            # ドメインを適切な文字列キーに変換
            if hasattr(domain, 'value'):
                domain_key = domain.value
            else:
                domain_key = str(domain)
            
            if domain_key not in self.collections:
                logger.warning(f"Collection not found for domain: {domain_key}")
                return []
                
            collection = self.collections[domain_key]

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
                        metadata = results["metadatas"][0][i] if results["metadatas"] else {
                        }

                        similar_memories.append({
                            "memory_id": memory_id,
                            "similarity": similarity,
                            "distance": distance,
                            "metadata": metadata
                        })

            logger.info(
                "Vector search completed",
                extra={
                    "domain": str(domain),
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
                domain=str(domain),
                error=str(e)
            )
            raise

    async def delete_vector(self, memory_id: str) -> bool:
        """ベクトルを削除"""
        # 全ドメインから削除を試行
        deleted = False
        for domain_key, collection in self.collections.items():
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: collection.delete(ids=[memory_id])
                )
                deleted = True
                logger.info(
                    "Vector deleted",
                    extra={
                        "memory_id": memory_id,
                        "domain": domain_key
                    }
                )
            except Exception as e:
                # このドメインにはベクトルが存在しない
                logger.error(
                    "Failed to delete vector",
                    error_code="VECTOR_DELETE_ERROR",
                    memory_id=memory_id,
                    domain=domain_key,
                    error=str(e)
                )
                continue
        return deleted

    async def update_metadata(
        self,
        memory_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """メタデータを更新"""
        try:
            domain = metadata.get("domain", "user")
            domain_key = domain_value(domain)
            collection = self.collections[domain_key]

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: collection.update(
                    ids=[memory_id],
                    metadatas=[metadata]
                )
            )

            logger.info(
                "Vector metadata updated",
                extra={
                    "memory_id": memory_id,
                    "domain": str(domain)
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
            domain_key = domain_value(domain)
            collection = self.collections[domain_key]

            count = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: collection.count()
            )

            return {
                "domain": str(domain),
                "total_vectors": count,
                "collection_name": f"memories_{str(domain)}",
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(
                "Failed to get collection stats",
                error_code="COLLECTION_STATS_ERROR",
                domain=str(domain),
                error=str(e)
            )
            return {
                "domain": str(domain),
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
