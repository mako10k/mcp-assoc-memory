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
from ..utils.validation import ValidationError, domain_value
from .base import BaseHandler, ToolCall, ToolResult
from .tool_utils import error_result, tool_result


logger = logging.getLogger(__name__)


class MemoryToolHandler(BaseHandler):

    # --- MCPToolRouter向け: 個別ハンドラ公開 ---
    async def handle_store(self, args: Dict[str, Any]) -> ToolResult:
        """memory.store 用: 記憶保存"""
        # 新スキーマ: subcommand, domain, content, metadata, tags, category, user_id, project_id, session_id
        return await self._store(args)

    async def handle_search(self, args: Dict[str, Any]) -> ToolResult:
        """memory.search 用: 記憶検索"""
        # 新スキーマ: subcommand, query, domain, limit, tags, category, user_id, project_id, session_id
        return await self._search(args)

    async def handle_get(self, args: Dict[str, Any]) -> ToolResult:
        """memory.get 用: 記憶取得"""
        # 新スキーマ: subcommand, memory_id
        return await self._get(args)

    async def handle_get_related(self, args: Dict[str, Any]) -> ToolResult:
        """memory.get_related 用: 関連記憶取得"""
        # 新スキーマ: subcommand, memory_id, limit, min_score
        return await self._get_related(args)

    async def handle_update(self, args: Dict[str, Any]) -> ToolResult:
        """memory.update 用: 記憶更新"""
        # 新スキーマ: subcommand, memory_id, content, metadata, tags, category
        return await self._update(args)

    async def handle_delete(self, args: Dict[str, Any]) -> ToolResult:
        """memory.delete 用: 記憶削除"""
        # 新スキーマ: subcommand, memory_id
        return await self._delete(args)
    """記憶操作ツールハンドラー"""

    def __init__(self, memory_manager: MemoryManager):
        super().__init__()
        self.memory_manager = memory_manager


    async def __call__(self, args: Dict[str, Any]) -> ToolResult:
        """
        サブコマンド分岐型エントリポイント (mode必須)
        args['mode'] で分岐し、各サブコマンドを呼び出す。
        """
        mode = args.get('mode')
        if not mode:
            return error_result(
                "MODE_REQUIRED",
                "mode（サブコマンド名）は必須です。例: mode='store'"
            )
        import traceback
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
                return error_result(
                    "UNKNOWN_MODE",
                    f"未対応のmode: {mode}"
                )
        except Exception as e:
            logger.error(f"MemoryToolHandler {mode} エラー: {e} ({type(e)})")
            logger.error(traceback.format_exc())
            return error_result(
                type(e).__name__,
                f"{mode}の実行に失敗しました: {e}"
            )

    # --- 以下は個別のサブコマンド実装（private化） ---
    async def _store(self, args: Dict[str, Any]) -> ToolResult:
        domain = MemoryDomain(args['domain'])
        content = args['content']
        metadata = args.get('metadata', {})
        tags = args.get('tags', [])
        category = args.get('category')
        user_id = args.get('user_id')
        project_id = args.get('project_id')
        session_id = args.get('session_id')
        memory = await self.memory_manager.store_memory(
            domain=domain,
            content=content,
            metadata=metadata,
            tags=tags,
            category=category,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id
        )
        if memory is None:
            return error_result(
                code="MEMORY_STORE_ERROR",
                message="記憶の保存に失敗しました"
            )
        return tool_result(
            success=True,
            content=[{
                'memory_id': memory.id,
                'domain': domain_value(memory.domain),
                'created_at': memory.created_at.isoformat(),
                'tags': memory.tags,
                'category': memory.category
            }],
            message=f"記憶を保存しました (ID: {memory.id})"
        )

    async def _search(self, args: Dict[str, Any]) -> ToolResult:
        query = args['query']
        # --- 型正規化: str/list/enum→List[MemoryDomain] 以外は例外 ---
        def normalize_domains(raw) -> Optional[list]:
            if raw is None:
                return None
            if isinstance(raw, MemoryDomain):
                return [raw]
            if isinstance(raw, str):
                return [MemoryDomain(raw)]
            if isinstance(raw, list):
                return [MemoryDomain(d) if not isinstance(d, MemoryDomain) else d for d in raw]
            raise TypeError(f"Invalid domain type: {type(raw)}")

        # 柔軟な入力（domain, domains, include_domains, exclude_domains）をすべて正規化
        raw_domain = args.get('domain')
        raw_domains = args.get('domains')
        raw_include = args.get('include_domains')
        # 優先順位: include_domains > domains > domain
        domains = None
        if raw_include is not None:
            domains = normalize_domains(raw_include)
        elif raw_domains is not None:
            domains = normalize_domains(raw_domains)
        elif raw_domain is not None:
            domains = normalize_domains(raw_domain)
        else:
            # デフォルト: ユーザードメイン
            domains = [MemoryDomain.USER]

        limit = args.get('limit', 10)
        tags = args.get('tags', [])
        category = args.get('category')
        user_id = args.get('user_id')
        project_id = args.get('project_id')
        session_id = args.get('session_id')
        min_score = args.get('min_score')
        search_kwargs = dict(
            query=query,
            domains=domains,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            tags=tags,
            limit=limit
        )
        if min_score is not None:
            search_kwargs['similarity_threshold'] = min_score
        results = await self.memory_manager.search_memories(**search_kwargs)
        formatted_results = []
        for item in results:
            memory = item.get('memory')
            if memory is None:
                continue
            content = memory.content
            if not isinstance(content, str):
                # dictやlistなども含め、必ずstr型に変換
                try:
                    content = str(content)
                except Exception:
                    content = ""
            if not isinstance(content, str):
                content = ""
            content_short = content[:200] + '...' if isinstance(content, str) and len(content) > 200 else content
            domain_val = domain_value(memory.domain)
            formatted_results.append({
                'memory_id': memory.id,
                'content': content_short,
                'domain': domain_val,
                'score': item.get('score'),
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat()
            })
        # MCP ToolResult.contentはリスト（成功時）で返す: クライアント期待値に合わせる
        return tool_result(
            success=True,
            content=formatted_results,
            message=f"{len(formatted_results)}件の記憶が見つかりました"
        )

    async def _get(self, args: Dict[str, Any]) -> ToolResult:
        memory_id = args['memory_id']
        memory = await self.memory_manager.get_memory(memory_id)
        if not memory:
            return error_result(
                code="MEMORY_NOT_FOUND",
                message=f"記憶 {memory_id} が見つかりません"
            )
        domain_val = domain_value(memory.domain)
        return tool_result(
            success=True,
            content=[{
                'memory_id': memory.id,
                'content': memory.content,
                'domain': domain_val,
                'metadata': memory.metadata,
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat(),
                'updated_at': memory.updated_at.isoformat()
            }],
            message="記憶を取得しました"
        )

    async def _get_related(self, args: Dict[str, Any]) -> ToolResult:
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
            content = memory.content
            if not isinstance(content, str):
                # dictやlistなども含め、必ずstr型に変換
                try:
                    content = str(content)
                except Exception:
                    content = ""
            if not isinstance(content, str):
                content = ""
            content_short = content[:200] + '...' if isinstance(content, str) and len(content) > 200 else content
            domain_val = domain_value(memory.domain)
            formatted_results.append({
                'memory_id': memory.id,
                'content': content_short,
                'domain': domain_val,
                'score': score,
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat()
            })
        return tool_result(
            success=True,
            content=formatted_results,
            message=f"{len(formatted_results)}件の関連記憶が見つかりました"
        )

    async def _update(self, args: Dict[str, Any]) -> ToolResult:
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
            return error_result(
                code="MEMORY_NOT_FOUND",
                message=f"記憶 {memory_id} が見つかりません"
            )
        memory = await self.memory_manager.get_memory(memory_id)
        updated_at = memory.updated_at.isoformat() if memory and memory.updated_at else None
        return tool_result(
            success=True,
            content=[{
                'memory_id': memory_id,
                'updated_at': updated_at
            }],
            message="記憶を更新しました"
        )

    async def _delete(self, args: Dict[str, Any]) -> ToolResult:
        memory_id = args['memory_id']
        success = await self.memory_manager.delete_memory(memory_id)
        if not success:
            return error_result(
                code="MEMORY_NOT_FOUND",
                message=f"記憶 {memory_id} が見つかりません"
            )
        return tool_result(
            success=True,
            content=[{'memory_id': memory_id}],
            message="記憶を削除しました"
        )


class MemoryManageToolHandler(BaseHandler):

    # --- MCPToolRouter向け: 個別ハンドラ公開 ---
    async def handle_stats(self, args: Dict[str, Any]) -> ToolResult:
        """memory_manage.stats 用: 統計取得"""
        return await self._stats(args)

    async def handle_export(self, args: Dict[str, Any]) -> ToolResult:
        """memory_manage.export 用: エクスポート"""
        return await self._export(args)

    async def handle_import(self, args: Dict[str, Any]) -> ToolResult:
        """memory_manage.import 用: インポート"""
        return await self._import(args)

    async def handle_change_domain(self, args: Dict[str, Any]) -> ToolResult:
        """memory_manage.change_domain 用: ドメイン変更"""
        return await self._change_domain(args)

    async def handle_batch_delete(self, args: Dict[str, Any]) -> ToolResult:
        """memory_manage.batch_delete 用: バッチ削除"""
        return await self._batch_delete(args)

    async def handle_cleanup(self, args: Dict[str, Any]) -> ToolResult:
        """memory_manage.cleanup 用: クリーンアップ"""
        return await self._cleanup(args)
    """記憶管理ツールハンドラー"""

    def __init__(self, memory_manager: MemoryManager):
        super().__init__()
        self.memory_manager = memory_manager


    async def __call__(self, args: Dict[str, Any]) -> ToolResult:
        """
        サブコマンド分岐型エントリポイント (mode必須)
        args['mode'] で分岐し、各サブコマンドを呼び出す。
        """
        mode = args.get('mode')
        if not mode:
            return error_result(
                code="MODE_REQUIRED",
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
                return error_result(
                    code="UNKNOWN_MODE",
                    message=f"未対応のmode: {mode}"
                )
        except Exception as e:
            logger.error(f"MemoryManageToolHandler {mode} エラー: {e}")
            return error_result(
                code=str(e),
                message=f"{mode}の実行に失敗しました"
            )

    # --- 以下は個別のサブコマンド実装（private化） ---
    async def _stats(self, args: Dict[str, Any]) -> ToolResult:
        domain = args.get('domain')
        domain_filter = MemoryDomain(domain) if domain else None
        stats = await self.memory_manager.get_memory_stats(domain_filter)
        return tool_result(
            success=True,
            content=[stats],
            message="記憶統計を取得しました"
        )

    async def _export(self, args: Dict[str, Any]) -> ToolResult:
        domain = args.get('domain')
        format_type = args.get('format', 'json')
        domain_filter = MemoryDomain(domain) if domain else None
        exported_data = await self.memory_manager.export_memories(
            domain=domain_filter,
            format_type=format_type
        )
        return tool_result(
            success=True,
            content=[{
                'exported_data': exported_data,
                'format': format_type,
                'exported_at': datetime.utcnow().isoformat()
            }],
            message="記憶をエクスポートしました"
        )

    async def _import(self, args: Dict[str, Any]) -> ToolResult:
        data = args['data']
        domain = MemoryDomain(args['domain'])
        overwrite = args.get('overwrite', False)
        result = await self.memory_manager.import_memories(
            data=data,
            domain=domain,
            overwrite=overwrite
        )
        return tool_result(
            success=True,
            content=[{
                'imported_count': result['imported_count'],
                'skipped_count': result['skipped_count'],
                'error_count': result['error_count']
            }],
            message=f"{result['imported_count']}件の記憶をインポートしました"
        )

    async def _change_domain(self, args: Dict[str, Any]) -> ToolResult:
        memory_id = args['memory_id']
        new_domain = MemoryDomain(args['new_domain'])
        success = await self.memory_manager.change_memory_domain(
            memory_id=memory_id,
            new_domain=new_domain
        )
        if not success:
            return error_result(
                code="MEMORY_NOT_FOUND",
                message=f"記憶 {memory_id} が見つかりません"
            )
        return tool_result(
            success=True,
            content=[{
                'memory_id': memory_id,
                'new_domain': new_domain.value
            }],
            message="記憶のドメインを変更しました"
        )

    async def _batch_delete(self, args: Dict[str, Any]) -> ToolResult:
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
        return tool_result(
            success=True,
            content=[{'deleted_count': deleted_count}],
            message=f"{deleted_count}件の記憶を削除しました"
        )

    async def _cleanup(self, args: Dict[str, Any]) -> ToolResult:
        cleanup_orphans = args.get('cleanup_orphans', True)
        reindex = args.get('reindex', False)
        vacuum = args.get('vacuum', False)
        result = await self.memory_manager.cleanup_database(
            cleanup_orphans=cleanup_orphans,
            reindex=reindex,
            vacuum=vacuum
        )
        return tool_result(
            success=True,
            content=[result],
            message="データベースクリーンアップが完了しました"
        )


class SearchToolHandler(BaseHandler):

    # --- MCPToolRouter向け: 個別ハンドラ公開 ---
    async def handle_semantic(self, args: Dict[str, Any]) -> ToolResult:
        """search.semantic 用: 意味検索"""
        return await self._semantic(args)

    async def handle_tags(self, args: Dict[str, Any]) -> ToolResult:
        """search.tags 用: タグ検索"""
        return await self._tags(args)

    async def handle_timerange(self, args: Dict[str, Any]) -> ToolResult:
        """search.timerange 用: 時間範囲検索"""
        return await self._timerange(args)

    async def handle_advanced(self, args: Dict[str, Any]) -> ToolResult:
        """search.advanced 用: 高度検索"""
        return await self._advanced(args)

    async def handle_similar(self, args: Dict[str, Any]) -> ToolResult:
        """search.similar 用: 類似検索"""
        return await self._similar(args)
    """高度検索ツールハンドラー"""

    def __init__(self, memory_manager: MemoryManager, similarity_calc: SimilarityCalculator):
        super().__init__()
        self.memory_manager = memory_manager
        self.similarity_calc = similarity_calc


    async def __call__(self, args: Dict[str, Any]) -> ToolResult:
        """
        サブコマンド分岐型エントリポイント (mode必須)
        args['mode'] で分岐し、各サブコマンドを呼び出す。
        """
        mode = args.get('mode')
        if not mode:
            return error_result(
                code="MODE_REQUIRED",
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
                return error_result(
                    code="UNKNOWN_MODE",
                    message=f"未対応のmode: {mode}"
                )
        except Exception as e:
            logger.error(f"SearchToolHandler {mode} エラー: {e}")
            return error_result(
                code=str(e),
                message=f"{mode}の実行に失敗しました"
            )

    # --- 以下は個別のサブコマンド実装（private化） ---
    async def _semantic(self, args: Dict[str, Any]) -> ToolResult:
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
            content = memory.content
            if not isinstance(content, str):
                # dictやlistなども含め、必ずstr型に変換
                try:
                    content = str(content)
                except Exception:
                    content = ""
            if not isinstance(content, str):
                content = ""
            domain_val = domain_value(memory.domain)
            formatted_results.append({
                'memory_id': memory.id,
                'content': content,
                'domain': domain_val,
                'semantic_score': score,
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat()
            })
        return tool_result(
            success=True,
            content=formatted_results,
            message=f"意味的検索で{len(formatted_results)}件が見つかりました"
        )

    async def _tags(self, args: Dict[str, Any]) -> ToolResult:
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
            content = memory.content
            if not isinstance(content, str):
                # dictやlistなども含め、必ずstr型に変換
                try:
                    content = str(content)
                except Exception:
                    content = ""
            if not isinstance(content, str):
                content = ""
            content_short = content[:200] + '...' if isinstance(content, str) and len(content) > 200 else content
            domain_val = domain_value(memory.domain)
            formatted_results.append({
                'memory_id': memory.id,
                'content': content_short,
                'domain': domain_val,
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat()
            })
        return tool_result(
            success=True,
            content=formatted_results,
            message=f"タグ検索で{len(formatted_results)}件が見つかりました"
        )

    async def _timerange(self, args: Dict[str, Any]) -> ToolResult:
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
            content = memory.content
            if not isinstance(content, str):
                # dictやlistなども含め、必ずstr型に変換
                try:
                    content = str(content)
                except Exception:
                    content = ""
            if not isinstance(content, str):
                content = ""
            content_short = content[:200] + '...' if isinstance(content, str) and len(content) > 200 else content
            domain_val = domain_value(memory.domain)
            formatted_results.append({
                'memory_id': memory.id,
                'content': content_short,
                'domain': domain_val,
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat()
            })
        return tool_result(
            success=True,
            content=formatted_results,
            message=f"時間範囲検索で{len(formatted_results)}件が見つかりました"
        )

    async def _advanced(self, args: Dict[str, Any]) -> ToolResult:
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
            content = memory.content
            if not isinstance(content, str):
                # dictやlistなども含め、必ずstr型に変換
                try:
                    content = str(content)
                except Exception:
                    content = ""
            if not isinstance(content, str):
                content = ""
            domain_val = domain_value(memory.domain)
            formatted_results.append({
                'memory_id': memory.id,
                'content': content,
                'domain': domain_val,
                'score': score,
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat()
            })
        return tool_result(
            success=True,
            content=formatted_results,
            message=f"高度検索で{len(formatted_results)}件が見つかりました"
        )

    async def _similar(self, args: Dict[str, Any]) -> ToolResult:
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
            content = memory.content
            if not isinstance(content, str):
                # dictやlistなども含め、必ずstr型に変換
                try:
                    content = str(content)
                except Exception:
                    content = ""
            if not isinstance(content, str):
                content = ""
            domain_val = domain_value(memory.domain)
            formatted_results.append({
                'memory_id': memory.id,
                'content': content,
                'domain': domain_val,
                'similarity_score': score,
                'tags': memory.tags,
                'category': memory.category,
                'created_at': memory.created_at.isoformat()
            })
        return tool_result(
            success=True,
            content=formatted_results,
            message=f"類似記憶検索で{len(formatted_results)}件が見つかりました"
        )
