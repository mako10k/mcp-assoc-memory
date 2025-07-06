"""
コア記憶管理エンジン実装
記憶の保存、検索、関連性管理の中核機能
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np

from ..models.memory import Memory, MemoryDomain
from ..models.association import Association
from ..storage.base import (
    BaseVectorStore,
    BaseMetadataStore,
    BaseGraphStore
)
from ..core.embedding_service import EmbeddingService
from ..core.similarity import SimilarityCalculator
from ..utils.logging import get_memory_logger
from ..utils.cache import LRUCache


logger = get_memory_logger(__name__)


class MemoryManager:
    """記憶管理エンジン"""

    def __init__(
        self,
        vector_store: BaseVectorStore,
        metadata_store: BaseMetadataStore,
        graph_store: BaseGraphStore,
        embedding_service: EmbeddingService,
        similarity_calculator: Optional[SimilarityCalculator] = None
    ):
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        self.graph_store = graph_store
        self.embedding_service = embedding_service
        self.similarity_calculator = (
            similarity_calculator or SimilarityCalculator()
        )

        # キャッシュ
        self.memory_cache = LRUCache(max_size=1000)
        self.association_cache = LRUCache(max_size=500)

        # 管理用ロック
        self.operation_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """システム初期化"""
        try:
            await asyncio.gather(
                self.vector_store.initialize(),
                self.metadata_store.initialize(),
                self.graph_store.initialize()
            )

            logger.info("Memory manager initialized successfully")

        except Exception as e:
            logger.error(
                "Failed to initialize memory manager",
                error_code="MEMORY_MANAGER_INIT_ERROR",
                error=str(e)
            )
            raise

    async def close(self) -> None:
        """システムクリーンアップ"""
        try:
            await asyncio.gather(
                self.vector_store.close(),
                self.metadata_store.close(),
                self.graph_store.close()
            )

            logger.info("Memory manager closed successfully")

        except Exception as e:
            logger.error(
                "Failed to close memory manager",
                error_code="MEMORY_MANAGER_CLOSE_ERROR",
                error=str(e)
            )

    async def store_memory(
        self,
        domain: MemoryDomain,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        auto_associate: bool = True
    ) -> Optional[Memory]:
        """記憶を保存"""
        try:
            # 記憶オブジェクト作成
            memory = Memory(
                domain=domain,
                content=content,
                metadata=metadata or {},
                tags=tags or [],
                category=category,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id
            )

            # 埋め込みベクトル生成
            embedding = await self.embedding_service.get_embedding(content)
            if embedding is None:
                logger.warning(
                    "Failed to generate embedding, storing without vector",
                    extra_data={"memory_id": memory.id}
                )

            async with self.operation_lock:
                # ベクトルストアに保存
                if embedding is not None:
                    success = await self.vector_store.store_embedding(
                        memory.id,
                        embedding,
                        memory.to_dict()
                    )
                    if not success:
                        logger.warning(
                            "Failed to store in vector store",
                            extra_data={"memory_id": memory.id}
                        )

                # メタデータストアに保存
                metadata_id = await self.metadata_store.store_memory(memory)
                if not metadata_id:
                    logger.error(
                        "Failed to store in metadata store",
                        error_code="METADATA_STORE_ERROR",
                        memory_id=memory.id
                    )
                    return None

                # グラフストアに記憶ノード追加
                graph_success = await self.graph_store.add_memory_node(memory)
                if not graph_success:
                    logger.warning(
                        "Failed to add to graph store",
                        extra_data={"memory_id": memory.id}
                    )

                # キャッシュに保存
                self.memory_cache.set(memory.id, memory)

                # 自動関連付け
                if auto_associate and embedding is not None:
                    await self._auto_associate_memory(memory, embedding)

                logger.info(
                    "Memory stored successfully",
                    extra_data={
                        "memory_id": memory.id,
                        "domain": domain.value,
                        "content_length": len(content),
                        "has_embedding": embedding is not None
                    }
                )

                return memory

        except Exception as e:
            logger.error(
                "Failed to store memory",
                error_code="MEMORY_STORE_ERROR",
                domain=domain.value,
                content_length=len(content),
                error=str(e)
            )
            return None

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """記憶を取得"""
        try:
            # キャッシュから確認
            cached_memory = self.memory_cache.get(memory_id)
            if cached_memory:
                # アクセス回数を更新
                cached_memory.access_count += 1
                cached_memory.accessed_at = datetime.utcnow()
                return cached_memory

            # メタデータストアから取得
            memory = await self.metadata_store.get_memory(memory_id)
            if memory:
                # キャッシュに保存
                self.memory_cache.set(memory_id, memory)

                # アクセス統計を更新
                await self.metadata_store.update_access_stats(
                    memory_id,
                    memory.access_count + 1
                )

                logger.debug(
                    "Memory retrieved",
                    extra_data={"memory_id": memory_id}
                )

            return memory

        except Exception as e:
            logger.error(
                "Failed to get memory",
                error_code="MEMORY_GET_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            return None

    async def search_memories(
        self,
        query: str,
        domains: Optional[List[MemoryDomain]] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """記憶を検索"""
        try:
            # クエリの埋め込みベクトル生成
            query_embedding = await self.embedding_service.get_embedding(query)
            if query_embedding is None:
                logger.warning("Failed to generate query embedding")
                return []

            # フィルタ条件構築
            filters = {}
            if domains:
                filters["domain"] = [d.value for d in domains]
            if user_id:
                filters["user_id"] = user_id
            if project_id:
                filters["project_id"] = project_id
            if session_id:
                filters["session_id"] = session_id
            if tags:
                filters["tags"] = tags

            # ベクトル検索実行
            vector_results = await self.vector_store.search_similar(
                query_embedding,
                limit=limit * 2,  # フィルタリング後に十分な結果を確保
                metadata_filter=filters
            )

            # 類似度フィルタリング
            filtered_results = []
            for result in vector_results:
                if result["similarity"] >= similarity_threshold:
                    # 記憶詳細情報を取得
                    memory = await self.get_memory(result["id"])
                    if memory:
                        filtered_results.append({
                            "memory": memory,
                            "similarity": result["similarity"],
                            "score": result.get("score", result["similarity"])
                        })

            # 結果を制限
            filtered_results = filtered_results[:limit]

            logger.info(
                "Memory search completed",
                extra_data={
                    "query_length": len(query),
                    "total_results": len(vector_results),
                    "filtered_results": len(filtered_results),
                    "filters": filters
                }
            )

            return filtered_results

        except Exception as e:
            logger.error(
                "Failed to search memories",
                error_code="MEMORY_SEARCH_ERROR",
                query_length=len(query),
                error=str(e)
            )
            return []

    async def get_related_memories(
        self,
        memory_id: str,
        max_depth: int = 2,
        max_results: int = 10,
        min_strength: float = 0.3
    ) -> List[Dict[str, Any]]:
        """関連記憶を取得"""
        try:
            # グラフから近隣記憶を取得
            neighbors = await self.graph_store.get_neighbors(
                memory_id,
                max_depth=max_depth,
                max_neighbors=max_results * 2
            )

            # 関連強度でフィルタリング
            related_memories = []
            for neighbor in neighbors:
                if neighbor["association_strength"] >= min_strength:
                    # 記憶詳細を取得
                    memory = await self.get_memory(neighbor["memory_id"])
                    if memory:
                        related_memories.append({
                            "memory": memory,
                            "association_strength": neighbor["association_strength"],
                            "association_type": neighbor["association_type"],
                            "depth": neighbor["depth"]
                        })

            # 結果を制限
            related_memories = related_memories[:max_results]

            logger.debug(
                "Related memories retrieved",
                extra_data={
                    "memory_id": memory_id,
                    "total_neighbors": len(neighbors),
                    "related_count": len(related_memories)
                }
            )

            return related_memories

        except Exception as e:
            logger.error(
                "Failed to get related memories",
                error_code="RELATED_MEMORIES_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            return []

    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """記憶を更新"""
        try:
            # 既存記憶を取得
            memory = await self.get_memory(memory_id)
            if not memory:
                logger.warning(
                    "Memory not found for update",
                    extra_data={"memory_id": memory_id}
                )
                return False

            # 更新内容を適用
            updated = False
            if content is not None and content != memory.content:
                memory.content = content
                updated = True

                # 新しい埋め込みベクトル生成
                embedding = await self.embedding_service.get_embedding(content)
                if embedding is not None:
                    await self.vector_store.store_embedding(
                        memory_id,
                        embedding,
                        memory.to_dict()
                    )

            if metadata is not None:
                memory.metadata.update(metadata)
                updated = True

            if tags is not None:
                memory.tags = tags
                updated = True

            if updated:
                memory.updated_at = datetime.utcnow()

                async with self.operation_lock:
                    # メタデータストア更新
                    success = await self.metadata_store.update_memory(memory)
                    if not success:
                        logger.error(
                            "Failed to update memory in metadata store",
                            error_code="METADATA_UPDATE_ERROR",
                            memory_id=memory_id
                        )
                        return False

                    # キャッシュ更新
                    self.memory_cache.set(memory_id, memory)

                    logger.info(
                        "Memory updated successfully",
                        extra_data={"memory_id": memory_id}
                    )

            return True

        except Exception as e:
            logger.error(
                "Failed to update memory",
                error_code="MEMORY_UPDATE_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """記憶を削除"""
        try:
            async with self.operation_lock:
                # 関連するエッジを削除
                associations = await self.metadata_store.get_memory_associations(
                    memory_id
                )
                for assoc in associations:
                    await self.graph_store.remove_association_edge(assoc.id)
                    await self.metadata_store.delete_association(assoc.id)

                # ストレージから削除
                await asyncio.gather(
                    self.vector_store.delete_embedding(memory_id),
                    self.metadata_store.delete_memory(memory_id),
                    self.graph_store.remove_memory_node(memory_id)
                )

                # キャッシュから削除
                self.memory_cache.delete(memory_id)

                logger.info(
                    "Memory deleted successfully",
                    extra_data={"memory_id": memory_id}
                )

                return True

        except Exception as e:
            logger.error(
                "Failed to delete memory",
                error_code="MEMORY_DELETE_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            return False

    async def _auto_associate_memory(
        self,
        memory: Memory,
        embedding: np.ndarray
    ) -> None:
        """記憶の自動関連付け"""
        try:
            # 類似記憶を検索
            similar_results = await self.vector_store.search_similar(
                embedding,
                limit=10,
                metadata_filter={
                    "domain": memory.domain.value
                }
            )

            # 関連性を作成
            for result in similar_results:
                if result["id"] == memory.id:
                    continue  # 自己関連を除外

                similarity_score = result["similarity"]
                if similarity_score >= 0.7:  # 高い類似度のみ
                    association = Association(
                        source_memory_id=memory.id,
                        target_memory_id=result["id"],
                        association_type="semantic",
                        strength=similarity_score,
                        auto_generated=True
                    )

                    # 関連性を保存
                    await self._store_association(association)

            logger.debug(
                "Auto-association completed",
                extra_data={
                    "memory_id": memory.id,
                    "similar_count": len(similar_results)
                }
            )

        except Exception as e:
            logger.error(
                "Failed to auto-associate memory",
                error_code="AUTO_ASSOCIATION_ERROR",
                memory_id=memory.id,
                error=str(e)
            )

    async def _store_association(self, association: Association) -> bool:
        """関連性を保存"""
        try:
            # メタデータストアに保存
            assoc_id = await self.metadata_store.store_association(association)
            if not assoc_id:
                return False

            # グラフストアに保存
            success = await self.graph_store.add_association_edge(association)
            if not success:
                # ロールバック
                await self.metadata_store.delete_association(association.id)
                return False

            # キャッシュに保存
            self.association_cache.set(association.id, association)

            return True

        except Exception as e:
            logger.error(
                "Failed to store association",
                error_code="ASSOCIATION_STORE_ERROR",
                association_id=association.id,
                error=str(e)
            )
            return False

    async def get_statistics(self) -> Dict[str, Any]:
        """システム統計を取得"""
        try:
            # 並列でヘルスチェック実行
            vector_health, metadata_health, graph_health = await asyncio.gather(
                self.vector_store.health_check(),
                self.metadata_store.health_check(),
                self.graph_store.health_check()
            )

            # キャッシュ統計
            cache_stats = {
                "memory_cache": {
                    "size": len(self.memory_cache.cache),
                    "max_size": self.memory_cache.max_size
                },
                "association_cache": {
                    "size": len(self.association_cache.cache),
                    "max_size": self.association_cache.max_size
                },
                "embedding_cache": self.embedding_service.get_cache_stats()
            }

            return {
                "vector_store": vector_health,
                "metadata_store": metadata_health,
                "graph_store": graph_health,
                "cache_stats": cache_stats,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(
                "Failed to get statistics",
                error_code="STATISTICS_ERROR",
                error=str(e)
            )
            return {}

    async def get_memory_stats(self, domain: Optional[MemoryDomain] = None) -> Dict[str, Any]:
        """記憶統計を取得"""
        try:
            stats = await self.metadata_store.get_memory_stats(domain)
            cache_stats = self.memory_cache.get_stats()
            embedding_stats = self.embedding_service.get_cache_stats()
            
            return {
                'total_memories': stats.get('total_count', 0),
                'memories_by_domain': stats.get('by_domain', {}),
                'memories_by_category': stats.get('by_category', {}),
                'total_size_bytes': stats.get('total_size', 0),
                'cache_stats': cache_stats,
                'embedding_cache_stats': embedding_stats,
                'last_updated': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"統計取得エラー: {e}")
            return {'error': str(e)}

    async def export_memories(
        self, 
        domain: Optional[MemoryDomain] = None,
        format_type: str = 'json'
    ) -> Dict[str, Any]:
        """記憶をエクスポート"""
        try:
            memories = await self.metadata_store.get_memories_by_domain(domain)
            
            if format_type == 'json':
                exported_data = [memory.to_dict() for memory in memories]
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            return {
                'format': format_type,
                'count': len(exported_data),
                'data': exported_data,
                'exported_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"エクスポートエラー: {e}")
            return {'error': str(e)}

    async def import_memories(
        self,
        data: List[Dict[str, Any]],
        domain: MemoryDomain,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """記憶をインポート"""
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        try:
            for item in data:
                try:
                    # 既存チェック
                    if 'id' in item and not overwrite:
                        existing = await self.get_memory(item['id'])
                        if existing:
                            skipped_count += 1
                            continue
                    
                    # 記憶を作成・保存
                    memory = await self.store_memory(
                        domain=domain,
                        content=item.get('content', ''),
                        metadata=item.get('metadata', {}),
                        tags=item.get('tags', []),
                        category=item.get('category')
                    )
                    
                    if memory:
                        imported_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"インポートアイテムエラー: {e}")
                    error_count += 1
            
            return {
                'imported_count': imported_count,
                'skipped_count': skipped_count,
                'error_count': error_count
            }
        except Exception as e:
            logger.error(f"インポートエラー: {e}")
            return {'error': str(e)}

    async def change_memory_domain(
        self,
        memory_id: str,
        new_domain: MemoryDomain
    ) -> bool:
        """記憶のドメインを変更"""
        try:
            memory = await self.get_memory(memory_id)
            if not memory:
                return False
            
            memory.domain = new_domain
            memory.updated_at = datetime.utcnow()
            
            success = await self.metadata_store.update_memory(memory)
            if success:
                # キャッシュを更新
                self.memory_cache.set(memory_id, memory)
                logger.info(f"記憶ドメイン変更: {memory_id} -> {new_domain.value}")
            
            return success
        except Exception as e:
            logger.error(f"ドメイン変更エラー: {e}")
            return False

    async def batch_delete_memories(self, criteria: Dict[str, Any]) -> int:
        """記憶を一括削除"""
        try:
            deleted_count = await self.metadata_store.batch_delete_memories(criteria)
            
            # キャッシュからも削除（簡易実装）
            self.memory_cache.clear()
            
            logger.info(f"一括削除完了: {deleted_count}件")
            return deleted_count
        except Exception as e:
            logger.error(f"一括削除エラー: {e}")
            return 0

    async def cleanup_database(
        self,
        cleanup_orphans: bool = True,
        reindex: bool = False,
        vacuum: bool = False
    ) -> Dict[str, Any]:
        """データベースクリーンアップ"""
        try:
            result = {
                'cleanup_orphans': 0,
                'reindex_completed': False,
                'vacuum_completed': False
            }
            
            if cleanup_orphans:
                result['cleanup_orphans'] = await self.metadata_store.cleanup_orphans()
            
            if reindex:
                await self.metadata_store.reindex()
                result['reindex_completed'] = True
            
            if vacuum:
                await self.metadata_store.vacuum()
                result['vacuum_completed'] = True
            
            return result
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")
            return {'error': str(e)}

    async def semantic_search(
        self,
        query: str,
        domain: MemoryDomain,
        limit: int = 10,
        min_score: float = 0.7
    ) -> List[Tuple[Memory, float]]:
        """意味的検索"""
        try:
            embedding = await self.embedding_service.get_embedding(query)
            if not embedding:
                return []
            
            # ベクトル検索
            results = await self.vector_store.search(
                embedding,
                domain.value,
                limit,
                min_score
            )
            
            # 記憶オブジェクトに変換
            memories_with_scores = []
            for memory_id, score in results:
                memory = await self.get_memory(memory_id)
                if memory:
                    memories_with_scores.append((memory, score))
            
            return memories_with_scores
        except Exception as e:
            logger.error(f"意味的検索エラー: {e}")
            return []

    async def search_by_tags(
        self,
        tags: List[str],
        domain: MemoryDomain,
        match_all: bool = False,
        limit: int = 10
    ) -> List[Memory]:
        """タグ検索"""
        try:
            return await self.metadata_store.search_by_tags(
                tags, domain, match_all, limit
            )
        except Exception as e:
            logger.error(f"タグ検索エラー: {e}")
            return []

    async def search_by_timerange(
        self,
        start_date: datetime,
        end_date: datetime,
        domain: MemoryDomain,
        limit: int = 10
    ) -> List[Memory]:
        """時間範囲検索"""
        try:
            return await self.metadata_store.search_by_timerange(
                start_date, end_date, domain, limit
            )
        except Exception as e:
            logger.error(f"時間範囲検索エラー: {e}")
            return []

    async def advanced_search(
        self,
        query: str = '',
        domain: MemoryDomain = MemoryDomain.USER,
        tags: List[str] = None,
        category: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        min_score: float = 0.5,
        limit: int = 10
    ) -> List[Tuple[Memory, float]]:
        """高度検索"""
        try:
            # 複合検索条件でメタデータ検索
            memories = await self.metadata_store.advanced_search(
                domain=domain,
                tags=tags or [],
                category=category,
                start_date=start_date,
                end_date=end_date,
                limit=limit * 3  # より多く取得してスコアフィルタリング
            )
            
            if not query:
                # クエリなしの場合は時系列順
                return [(memory, 1.0) for memory in memories[:limit]]
            
            # 意味的類似度でフィルタリング
            query_embedding = await self.embedding_service.get_embedding(query)
            if not query_embedding:
                return [(memory, 1.0) for memory in memories[:limit]]
            
            scored_memories = []
            for memory in memories:
                # 記憶の埋め込みを取得
                memory_embedding = await self.vector_store.get_embedding(memory.id)
                if memory_embedding:
                    score = self.similarity_calc.cosine_similarity(
                        query_embedding, memory_embedding
                    )
                    if score >= min_score:
                        scored_memories.append((memory, score))
            
            # スコア順にソート
            scored_memories.sort(key=lambda x: x[1], reverse=True)
            return scored_memories[:limit]
            
        except Exception as e:
            logger.error(f"高度検索エラー: {e}")
            return []

    async def find_similar_memories(
        self,
        reference_id: str,
        domain: MemoryDomain,
        limit: int = 10,
        min_score: float = 0.7
    ) -> List[Tuple[Memory, float]]:
        """類似記憶検索"""
        try:
            # 参照記憶の埋め込みを取得
            reference_embedding = await self.vector_store.get_embedding(reference_id)
            if not reference_embedding:
                return []
            
            # 類似検索
            results = await self.vector_store.search(
                reference_embedding,
                domain.value,
                limit + 1,  # 自分自身を除外するため+1
                min_score
            )
            
            # 記憶オブジェクトに変換（参照記憶を除外）
            memories_with_scores = []
            for memory_id, score in results:
                if memory_id != reference_id:
                    memory = await self.get_memory(memory_id)
                    if memory:
                        memories_with_scores.append((memory, score))
            
            return memories_with_scores[:limit]
        except Exception as e:
            logger.error(f"類似記憶検索エラー: {e}")
            return []

    async def get_related_memories(
        self,
        memory_id: str,
        limit: int = 5,
        min_score: float = 0.7
    ) -> List[Tuple[Memory, float]]:
        """関連記憶を取得"""
        try:
            memory = await self.get_memory(memory_id)
            if not memory:
                return []
            
            return await self.find_similar_memories(
                reference_id=memory_id,
                domain=memory.domain,
                limit=limit,
                min_score=min_score
            )
        except Exception as e:
            logger.error(f"関連記憶取得エラー: {e}")
            return []

    async def update_memory(
        self,
        memory_id: str,
        content: str = None,
        metadata: Dict[str, Any] = None,
        tags: List[str] = None,
        category: str = None
    ) -> Optional[Memory]:
        """記憶を更新"""
        try:
            memory = await self.get_memory(memory_id)
            if not memory:
                return None
            
            # 更新フィールドを適用
            if content is not None:
                memory.content = content
            if metadata is not None:
                memory.metadata.update(metadata)
            if tags is not None:
                memory.tags = tags
            if category is not None:
                memory.category = category
            
            memory.updated_at = datetime.utcnow()
            
            # 埋め込みを再生成（コンテンツが変更された場合）
            if content is not None:
                embedding = await self.embedding_service.get_embedding(content)
                if embedding:
                    await self.vector_store.store_embedding(
                        memory_id, embedding, memory.to_dict()
                    )
            
            # メタデータストアを更新
            success = await self.metadata_store.update_memory(memory)
            if success:
                # キャッシュを更新
                self.memory_cache.set(memory_id, memory)
                logger.info(f"記憶更新: {memory_id}")
                return memory
            
            return None
        except Exception as e:
            logger.error(f"記憶更新エラー: {e}")
            return None
