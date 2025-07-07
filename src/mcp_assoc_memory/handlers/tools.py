"""
MCPツールハンドラー実装

7つのメインツールグループを統合管理:
1. memory - 基本記憶操作
2. memory_manage - 記憶管理・統計
3. search - 高度検索機能
4. project - プロジェクト管理
5. user - ユーザー・セッション管理
6. visualize - 可視化・分析
7. admin - システム管理・保守
"""

from typing import Any, Dict, List, Optional, Union
import json
import logging
from datetime import datetime, timedelta
from dataclasses import asdict

from ..models.memory import Memory, MemoryDomain
from ..models.project import Project, ProjectMember, ProjectRole
from ..core.memory_manager import MemoryManager
from ..core.similarity import SimilarityCalculator
from ..auth.session import SessionManager
from ..utils.validation import ValidationError
from .base import BaseHandler, ToolCall, ToolResponse


logger = logging.getLogger(__name__)


class MemoryToolHandler(BaseHandler):
    """記憶操作ツールハンドラー"""

    def __init__(self, memory_manager: MemoryManager):
        super().__init__()
        self.memory_manager = memory_manager


    async def __call__(self, args: Dict[str, Any]) -> ToolResponse:
        """
        サブコマンド分岐型エントリポイント (mode必須)
        args['mode'] で分岐し、各サブコマンドを呼び出す。
        """
        mode = args.get('mode')
        if not mode:
            return ToolResponse(
                success=False,
                error="MODE_REQUIRED",
                message="mode（サブコマンド名）は必須です。例: mode='store'"
            )
        try:
            if mode == 'store':
                return await self._store(args)
            elif mode == 'search':
                return await self._search(args)
            elif mode == 'get':
                return await self._get(args)
            elif mode == 'get_related':
                return await self._get_related(args)
            elif mode == 'update':
                return await self._update(args)
            elif mode == 'delete':
                return await self._delete(args)
            else:
                return ToolResponse(
                    success=False,
                    error="UNKNOWN_MODE",
                    message=f"未対応のmode: {mode}"
                )
        except Exception as e:
            logger.error(f"MemoryToolHandler {mode} エラー: {e}")
            return ToolResponse(
                success=False,
                error=str(e),
                message=f"{mode}の実行に失敗しました"
            )

    # --- 以下は個別のサブコマンド実装（private化） ---
    async def _store(self, args: Dict[str, Any]) -> ToolResponse:
        domain = MemoryDomain(args['domain'])
        content = args['content']
        metadata = args.get('metadata', {})
        tags = args.get('tags', [])
        category = args.get('category')
        memory = await self.memory_manager.store_memory(
            domain=domain,
            content=content,
            metadata=metadata,
            tags=tags,
            category=category
        )
        if memory is None:
            return ToolResponse(
                success=False,
                error="MEMORY_STORE_ERROR",
                message="記憶の保存に失敗しました"
            )
        return ToolResponse(
            success=True,
            data={
                'memory_id': memory.id,
                'domain': memory.domain.value,
                'created_at': memory.created_at.isoformat(),
                'tags': memory.tags,
                'category': memory.category
            },
            message=f"記憶を保存しました (ID: {memory.id})"
        )

    async def _search(self, args: Dict[str, Any]) -> ToolResponse:
        query = args['query']
        domain = MemoryDomain(args.get('domain', 'user'))
        limit = args.get('limit', 10)
        tags = args.get('tags', [])
        category = args.get('category')
        results = await self.memory_manager.search_memories(
            query=query,
            domains=[domain] if domain else None,
            limit=limit,
            tags=tags
        )
        formatted_results = []
        for item in results:
            memory = item.get('memory')
            if memory is None:
                continue
            formatted_results.append({
                'memory_id': memory.id,
                'content': memory.content[:200] + '...' if len(memory.content) > 200 else memory.content,
                'domain': memory.domain.value,
                'score': item.get('score'),
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat()
            })
        return ToolResponse(
            success=True,
            data={
                'results': formatted_results,
                'count': len(formatted_results),
                'query': query
            },
            message=f"{len(formatted_results)}件の記憶が見つかりました"
        )

    async def _get(self, args: Dict[str, Any]) -> ToolResponse:
        memory_id = args['memory_id']
        memory = await self.memory_manager.get_memory(memory_id)
        if not memory:
            return ToolResponse(
                success=False,
                error="MEMORY_NOT_FOUND",
                message=f"記憶 {memory_id} が見つかりません"
            )
        return ToolResponse(
            success=True,
            data={
                'memory_id': memory.id,
                'content': memory.content,
                'domain': memory.domain.value,
                'metadata': memory.metadata,
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat(),
                'updated_at': memory.updated_at.isoformat()
            },
            message="記憶を取得しました"
        )

    async def _get_related(self, args: Dict[str, Any]) -> ToolResponse:
        memory_id = args['memory_id']
        limit = args.get('limit', 5)
        min_score = args.get('min_score', 0.7)
        related_memories = await self.memory_manager.get_related_memories(
            memory_id=memory_id,
            limit=limit,
            min_score=min_score
        )
        formatted_results = []
        for memory, score in related_memories:
            if memory is None:
                continue
            formatted_results.append({
                'memory_id': memory.id,
                'content': memory.content[:200] + '...' if len(memory.content) > 200 else memory.content,
                'domain': memory.domain.value,
                'score': score,
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat()
            })
        return ToolResponse(
            success=True,
            data={
                'related_memories': formatted_results,
                'count': len(formatted_results),
                'source_memory_id': memory_id
            },
            message=f"{len(formatted_results)}件の関連記憶が見つかりました"
        )

    async def _update(self, args: Dict[str, Any]) -> ToolResponse:
        memory_id = args['memory_id']
        content = args.get('content')
        metadata = args.get('metadata')
        tags = args.get('tags')
        category = args.get('category')
        update_result = await self.memory_manager.update_memory(
            memory_id=memory_id,
            content=content,
            metadata=metadata,
            tags=tags
        )
        if not update_result:
            return ToolResponse(
                success=False,
                error="MEMORY_NOT_FOUND",
                message=f"記憶 {memory_id} が見つかりません"
            )
        memory = await self.memory_manager.get_memory(memory_id)
        updated_at = memory.updated_at.isoformat() if memory and memory.updated_at else None
        return ToolResponse(
            success=True,
            data={
                'memory_id': memory_id,
                'updated_at': updated_at
            },
            message="記憶を更新しました"
        )

    async def _delete(self, args: Dict[str, Any]) -> ToolResponse:
        memory_id = args['memory_id']
        success = await self.memory_manager.delete_memory(memory_id)
        if not success:
            return ToolResponse(
                success=False,
                error="MEMORY_NOT_FOUND",
                message=f"記憶 {memory_id} が見つかりません"
            )
        return ToolResponse(
            success=True,
            data={'memory_id': memory_id},
            message="記憶を削除しました"
        )


class MemoryManageToolHandler(BaseHandler):
    """記憶管理ツールハンドラー"""

    def __init__(self, memory_manager: MemoryManager):
        super().__init__()
        self.memory_manager = memory_manager


    async def __call__(self, args: Dict[str, Any]) -> ToolResponse:
        """
        サブコマンド分岐型エントリポイント (mode必須)
        args['mode'] で分岐し、各サブコマンドを呼び出す。
        """
        mode = args.get('mode')
        if not mode:
            return ToolResponse(
                success=False,
                error="MODE_REQUIRED",
                message="mode（サブコマンド名）は必須です。例: mode='stats'"
            )
        try:
            if mode == 'stats':
                return await self._stats(args)
            elif mode == 'export':
                return await self._export(args)
            elif mode == 'import':
                return await self._import(args)
            elif mode == 'change_domain':
                return await self._change_domain(args)
            elif mode == 'batch_delete':
                return await self._batch_delete(args)
            elif mode == 'cleanup':
                return await self._cleanup(args)
            else:
                return ToolResponse(
                    success=False,
                    error="UNKNOWN_MODE",
                    message=f"未対応のmode: {mode}"
                )
        except Exception as e:
            logger.error(f"MemoryManageToolHandler {mode} エラー: {e}")
            return ToolResponse(
                success=False,
                error=str(e),
                message=f"{mode}の実行に失敗しました"
            )

    # --- 以下は個別のサブコマンド実装（private化） ---
    async def _stats(self, args: Dict[str, Any]) -> ToolResponse:
        domain = args.get('domain')
        domain_filter = MemoryDomain(domain) if domain else None
        stats = await self.memory_manager.get_memory_stats(domain_filter)
        return ToolResponse(
            success=True,
            data=stats,
            message="記憶統計を取得しました"
        )

    async def _export(self, args: Dict[str, Any]) -> ToolResponse:
        domain = args.get('domain')
        format_type = args.get('format', 'json')
        domain_filter = MemoryDomain(domain) if domain else None
        exported_data = await self.memory_manager.export_memories(
            domain=domain_filter,
            format_type=format_type
        )
        return ToolResponse(
            success=True,
            data={
                'exported_data': exported_data,
                'format': format_type,
                'exported_at': datetime.utcnow().isoformat()
            },
            message="記憶をエクスポートしました"
        )

    async def _import(self, args: Dict[str, Any]) -> ToolResponse:
        data = args['data']
        domain = MemoryDomain(args['domain'])
        overwrite = args.get('overwrite', False)
        result = await self.memory_manager.import_memories(
            data=data,
            domain=domain,
            overwrite=overwrite
        )
        return ToolResponse(
            success=True,
            data={
                'imported_count': result['imported_count'],
                'skipped_count': result['skipped_count'],
                'error_count': result['error_count']
            },
            message=f"{result['imported_count']}件の記憶をインポートしました"
        )

    async def _change_domain(self, args: Dict[str, Any]) -> ToolResponse:
        memory_id = args['memory_id']
        new_domain = MemoryDomain(args['new_domain'])
        success = await self.memory_manager.change_memory_domain(
            memory_id=memory_id,
            new_domain=new_domain
        )
        if not success:
            return ToolResponse(
                success=False,
                error="MEMORY_NOT_FOUND",
                message=f"記憶 {memory_id} が見つかりません"
            )
        return ToolResponse(
            success=True,
            data={
                'memory_id': memory_id,
                'new_domain': new_domain.value
            },
            message="記憶のドメインを変更しました"
        )

    async def _batch_delete(self, args: Dict[str, Any]) -> ToolResponse:
        domain = args.get('domain')
        tags = args.get('tags', [])
        category = args.get('category')
        older_than_days = args.get('older_than_days')
        criteria = {}
        if domain:
            criteria['domain'] = MemoryDomain(domain)
        if tags:
            criteria['tags'] = tags
        if category:
            criteria['category'] = category
        if older_than_days:
            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
            criteria['older_than'] = cutoff_date
        deleted_count = await self.memory_manager.batch_delete_memories(criteria)
        return ToolResponse(
            success=True,
            data={'deleted_count': deleted_count},
            message=f"{deleted_count}件の記憶を削除しました"
        )

    async def _cleanup(self, args: Dict[str, Any]) -> ToolResponse:
        cleanup_orphans = args.get('cleanup_orphans', True)
        reindex = args.get('reindex', False)
        vacuum = args.get('vacuum', False)
        result = await self.memory_manager.cleanup_database(
            cleanup_orphans=cleanup_orphans,
            reindex=reindex,
            vacuum=vacuum
        )
        return ToolResponse(
            success=True,
            data=result,
            message="データベースクリーンアップが完了しました"
        )


class SearchToolHandler(BaseHandler):
    """高度検索ツールハンドラー"""

    def __init__(self, memory_manager: MemoryManager, similarity_calc: SimilarityCalculator):
        super().__init__()
        self.memory_manager = memory_manager
        self.similarity_calc = similarity_calc


    async def __call__(self, args: Dict[str, Any]) -> ToolResponse:
        """
        サブコマンド分岐型エントリポイント (mode必須)
        args['mode'] で分岐し、各サブコマンドを呼び出す。
        """
        mode = args.get('mode')
        if not mode:
            return ToolResponse(
                success=False,
                error="MODE_REQUIRED",
                message="mode（サブコマンド名）は必須です。例: mode='semantic'"
            )
        try:
            if mode == 'semantic':
                return await self._semantic(args)
            elif mode == 'tags':
                return await self._tags(args)
            elif mode == 'timerange':
                return await self._timerange(args)
            elif mode == 'advanced':
                return await self._advanced(args)
            elif mode == 'similar':
                return await self._similar(args)
            else:
                return ToolResponse(
                    success=False,
                    error="UNKNOWN_MODE",
                    message=f"未対応のmode: {mode}"
                )
        except Exception as e:
            logger.error(f"SearchToolHandler {mode} エラー: {e}")
            return ToolResponse(
                success=False,
                error=str(e),
                message=f"{mode}の実行に失敗しました"
            )

    # --- 以下は個別のサブコマンド実装（private化） ---
    async def _semantic(self, args: Dict[str, Any]) -> ToolResponse:
        query = args['query']
        domain = MemoryDomain(args.get('domain', 'user'))
        limit = args.get('limit', 10)
        min_score = args.get('min_score', 0.7)
        results = await self.memory_manager.semantic_search(
            query=query,
            domain=domain,
            limit=limit,
            min_score=min_score
        )
        formatted_results = []
        for memory, score in results:
            formatted_results.append({
                'memory_id': memory.id,
                'content': memory.content,
                'domain': memory.domain.value,
                'semantic_score': score,
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat()
            })
        return ToolResponse(
            success=True,
            data={
                'results': formatted_results,
                'count': len(formatted_results),
                'query': query,
                'search_type': 'semantic'
            },
            message=f"意味的検索で{len(formatted_results)}件が見つかりました"
        )

    async def _tags(self, args: Dict[str, Any]) -> ToolResponse:
        tags = args['tags']
        domain = MemoryDomain(args.get('domain', 'user'))
        match_all = args.get('match_all', False)
        limit = args.get('limit', 10)
        results = await self.memory_manager.search_by_tags(
            tags=tags,
            domain=domain,
            match_all=match_all,
            limit=limit
        )
        formatted_results = []
        for memory in results:
            if memory is None:
                continue
            formatted_results.append({
                'memory_id': memory.id,
                'content': memory.content[:200] + '...' if len(memory.content) > 200 else memory.content,
                'domain': memory.domain.value,
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat()
            })
        return ToolResponse(
            success=True,
            data={
                'results': formatted_results,
                'count': len(formatted_results),
                'search_tags': tags,
                'match_all': match_all
            },
            message=f"タグ検索で{len(formatted_results)}件が見つかりました"
        )

    async def _timerange(self, args: Dict[str, Any]) -> ToolResponse:
        start_date = datetime.fromisoformat(args['start_date'])
        end_date = datetime.fromisoformat(args['end_date'])
        domain = MemoryDomain(args.get('domain', 'user'))
        limit = args.get('limit', 10)
        results = await self.memory_manager.search_by_timerange(
            start_date=start_date,
            end_date=end_date,
            domain=domain,
            limit=limit
        )
        formatted_results = []
        for memory in results:
            formatted_results.append({
                'memory_id': memory.id,
                'content': memory.content[:200] + '...' if len(memory.content) > 200 else memory.content,
                'domain': memory.domain.value,
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat()
            })
        return ToolResponse(
            success=True,
            data={
                'results': formatted_results,
                'count': len(formatted_results),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            message=f"時間範囲検索で{len(formatted_results)}件が見つかりました"
        )

    async def _advanced(self, args: Dict[str, Any]) -> ToolResponse:
        query = args.get('query', '')
        domain = MemoryDomain(args.get('domain', 'user'))
        tags = args.get('tags', [])
        category = args.get('category')
        start_date = args.get('start_date')
        end_date = args.get('end_date')
        min_score = args.get('min_score', 0.5)
        limit = args.get('limit', 10)
        start_datetime = datetime.fromisoformat(start_date) if start_date else None
        end_datetime = datetime.fromisoformat(end_date) if end_date else None
        results = await self.memory_manager.advanced_search(
            query=query,
            domain=domain,
            tags=tags,
            category=category,
            start_date=start_datetime,
            end_date=end_datetime,
            min_score=min_score,
            limit=limit
        )
        formatted_results = []
        for memory, score in results:
            if memory is None:
                continue
            formatted_results.append({
                'memory_id': memory.id,
                'content': memory.content,
                'domain': memory.domain.value,
                'score': score,
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat()
            })
        return ToolResponse(
            success=True,
            data={
                'results': formatted_results,
                'count': len(formatted_results),
                'search_criteria': {
                    'query': query,
                    'domain': domain.value,
                    'tags': tags,
                    'category': category,
                    'start_date': start_date,
                    'end_date': end_date,
                    'min_score': min_score
                }
            },
            message=f"高度検索で{len(formatted_results)}件が見つかりました"
        )

    async def _similar(self, args: Dict[str, Any]) -> ToolResponse:
        reference_id = args['reference_id']
        domain = MemoryDomain(args.get('domain', 'user'))
        limit = args.get('limit', 10)
        min_score = args.get('min_score', 0.7)
        results = await self.memory_manager.find_similar_memories(
            reference_id=reference_id,
            domain=domain,
            limit=limit,
            min_score=min_score
        )
        formatted_results = []
        for memory, score in results:
            if memory is None:
                continue
            formatted_results.append({
                'memory_id': memory.id,
                'content': memory.content,
                'domain': memory.domain.value,
                'similarity_score': score,
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat()
            })
        return ToolResponse(
            success=True,
            data={
                'results': formatted_results,
                'count': len(formatted_results),
                'reference_id': reference_id,
                'min_score': min_score
            },
            message=f"類似記憶検索で{len(formatted_results)}件が見つかりました"
        )
