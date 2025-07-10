"""
ChromaDB Vector Store Implementation - Scope-based single collection
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

from ..utils.logging import get_memory_logger
from .base import BaseVectorStore

logger = get_memory_logger(__name__)


class ChromaVectorStore(BaseVectorStore):
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
        self.collection = None  # Single collection for all memories

    async def initialize(self) -> None:
        """Initialize ChromaDB client with single collection"""
    async def store_embedding(self, memory_id: str, embedding: Any, metadata: Dict[str, Any]) -> bool:
        """Store embedding (memory_manager.py compatible)"""
        try:
            await self.store_vector(memory_id, embedding, metadata)
            return True
        except Exception as e:
            logger.error(f"store_embedding error: {e}")
            return False

    async def get_embedding(self, memory_id: str) -> Optional[Any]:
        """埋め込みを取得 (memory_manager.py互換)"""
        # ChromaDBはembedding単体取得APIがないため、ID検索で取得
        for scope, collection in self.collections.items():
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

    async def search(self, embedding: Any, scope, limit: int = 10, min_score: float = 0.7) -> List[Tuple[str, float]]:
        """Vector search (memory_manager.py compatible)"""
        results = await self.search_similar(embedding, scope, limit, min_score)
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

            # Initialize collections for default scopes
            default_scopes = ["user", "work", "global", "session"]
            for scope in default_scopes:
                scope_key = scope_value(scope)
                collection_name = f"memories_{scope_key}"
                try:
                    collection = self.client.get_collection(collection_name)
                except Exception:
                    # Create collection if it doesn't exist
                    # Don't set embedding_function to manage embeddings manually
                    collection = self.client.create_collection(
                        name=collection_name,
                        metadata={"scope": scope_key},
                        embedding_function=None  # Manage embeddings manually
                    )
                self.collections[scope_key] = collection

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
            for scope_key, collection in self.collections.items():
                try:
                    count = collection.count()
                    collection_stats[scope_key] = {
                        "count": count,
                        "status": "healthy"
                    }
                except Exception as e:
                    collection_stats[scope_key] = {
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
        """Store vector (convert to ChromaDB metadata specification)"""
        try:
            scope = metadata.get("scope", "user/default")
            scope_key = scope_value(scope)
            collection = self.collections[scope_key]

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
                    "scope": str(scope),
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
        scope: Any,
        limit: int = 10,
        min_similarity: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """類似ベクトルを検索"""
        try:
            # スコープを適切な文字列キーに変換
            if hasattr(scope, 'value'):
                scope_key = scope.value
            else:
                scope_key = str(scope)
            
            if scope_key not in self.collections:
                logger.warning(f"Collection not found for scope: {scope_key}")
                return []
                
            collection = self.collections[scope_key]

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
                    "scope": str(scope),
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
                scope=str(scope),
                error=str(e)
            )
            raise

    async def delete_vector(self, memory_id: str) -> bool:
        """ベクトルを削除"""
        # 全スコープから削除を試行
        deleted = False
        for scope_key, collection in self.collections.items():
            try:
                # まず該当IDがこのコレクションに存在するかチェック
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: collection.get(ids=[memory_id])
                )
                
                # IDが存在する場合のみ削除実行
                if result["ids"]:
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: collection.delete(ids=[memory_id])
                    )
                    deleted = True
                    logger.info(
                        "Vector deleted",
                        extra={
                            "memory_id": memory_id,
                            "scope": scope_key
                        }
                    )
                else:
                    # このスコープにはベクトルが存在しない（正常）
                    logger.debug(
                        "Vector not found in scope",
                        extra={
                            "memory_id": memory_id,
                            "scope": scope_key
                        }
                    )
            except Exception as e:
                # ChromaDBのエラー（接続エラーなど）
                logger.warning(
                    "Failed to delete vector from scope",
                    extra={
                        "memory_id": memory_id,
                        "scope": scope_key,
                        "error": str(e)
                    }
                )
        return deleted

    async def update_metadata(
        self,
        memory_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Update metadata"""
        try:
            scope = metadata.get("scope", "user/default")
            scope_key = scope_value(scope)
            collection = self.collections[scope_key]

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
        self, scope: str
    ) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            scope_key = scope_value(scope)
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
