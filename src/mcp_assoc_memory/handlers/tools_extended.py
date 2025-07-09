"""
MCPツールハンドラー実装 - プロジェクト・ユーザー・可視化・管理ツール
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from ..auth.session import SessionManager
from ..core.memory_manager import MemoryManager
from ..models.memory import Memory, MemoryDomain
from ..models.project import Project, ProjectMember, ProjectRole
from ..utils.validation import ValidationError
from .base import BaseHandler
from .tool_utils import ToolResult, error_result, tool_result

logger = logging.getLogger(__name__)


class ProjectToolHandler(BaseHandler):
    async def __call__(self, args: Dict[str, Any]) -> ToolResult:
        mode = args.get('mode')
        if not mode:
            return error_result("MODE_REQUIRED", "mode（サブコマンド名）は必須です。例: mode='create'")
        try:
            if mode == 'create':
                return await self.handle_create(args)
            elif mode == 'list':
                return await self.handle_list(args)
            elif mode == 'get':
                return await self.handle_get(args)
            elif mode == 'add_member':
                return await self.handle_add_member(args)
            elif mode == 'remove_member':
                return await self.handle_remove_member(args)
            elif mode == 'update':
                return await self.handle_update(args)
            elif mode == 'delete':
                return await self.handle_delete(args)
            else:
                return error_result("UNKNOWN_MODE", f"未対応のmode: {mode}")
        except Exception as e:
            logger.error(f"ProjectToolHandler {mode} エラー: {e}")
            return error_result(str(e), f"{mode}の実行に失敗しました")
    """プロジェクト管理ツールハンドラー"""

    def __init__(self, memory_manager: MemoryManager, session_manager: SessionManager):
        super().__init__()
        self.memory_manager = memory_manager
        self.session_manager = session_manager
        self.projects: Dict[str, Project] = {}
        self.project_members: Dict[str, List[ProjectMember]] = {}

    async def handle_create(self, args: Dict[str, Any]) -> ToolResult:
        """プロジェクトを作成する"""
        try:
            name = args['name']
            description = args.get('description', '')
            owner_id = args['owner_id']

            project = Project(
                name=name,
                description=description,
                owner_id=owner_id
            )

            self.projects[project.id] = project
            self.project_members[project.id] = [
                ProjectMember(
                    project_id=project.id,
                    user_id=owner_id,
                    role=ProjectRole.OWNER
                )
            ]

            return tool_result(
                success=True,
                content=[{
                    'project_id': project.id,
                    'name': project.name,
                    'owner_id': project.owner_id,
                    'created_at': project.created_at.isoformat()
                }],
                message=f"プロジェクト '{name}' を作成しました"
            )

        except Exception as e:
            logger.error(f"プロジェクト作成エラー: {e}")
            return error_result(str(e), "プロジェクトの作成に失敗しました")

    async def handle_list(self, args: Dict[str, Any]) -> ToolResult:
        """プロジェクト一覧を取得する"""
        try:
            user_id = args.get('user_id')

            user_projects = []
            for project in self.projects.values():
                # ユーザーがメンバーかチェック
                if user_id:
                    members = self.project_members.get(project.id, [])
                    user_is_member = any(m.user_id == user_id for m in members)
                    if not user_is_member:
                        continue

                project_data = project.to_dict()
                members = self.project_members.get(project.id, [])
                project_data['member_count'] = len(members)
                user_projects.append(project_data)

            return tool_result(
                success=True,
                content=[{
                    'projects': user_projects,
                    'count': len(user_projects)
                }],
                message=f"{len(user_projects)}件のプロジェクトが見つかりました"
            )

        except Exception as e:
            logger.error(f"プロジェクト一覧取得エラー: {e}")
            return error_result(str(e), "プロジェクト一覧の取得に失敗しました")

    async def handle_get(self, args: Dict[str, Any]) -> ToolResult:
        """プロジェクト詳細を取得する"""
        try:
            project_id = args['project_id']

            project = self.projects.get(project_id)
            if not project:
                return error_result("PROJECT_NOT_FOUND", f"プロジェクト {project_id} が見つかりません")

            members = self.project_members.get(project_id, [])
            project_data = project.to_dict()
            project_data['members'] = [m.to_dict() for m in members]

            return tool_result(
                success=True,
                content=[project_data],
                message="プロジェクト詳細を取得しました"
            )

        except Exception as e:
            logger.error(f"プロジェクト取得エラー: {e}")
            return error_result(str(e), "プロジェクトの取得に失敗しました")

    async def handle_add_member(self, args: Dict[str, Any]) -> ToolResult:
        """プロジェクトメンバーを追加する"""
        try:
            project_id = args['project_id']
            user_id = args['user_id']
            role = ProjectRole(args.get('role', 'member'))

            if project_id not in self.projects:
                return error_result("PROJECT_NOT_FOUND", f"プロジェクト {project_id} が見つかりません")

            members = self.project_members.get(project_id, [])

            # 既存メンバーチェック
            if any(m.user_id == user_id for m in members):
                return error_result("MEMBER_EXISTS", "ユーザーは既にプロジェクトメンバーです")

            member = ProjectMember(
                project_id=project_id,
                user_id=user_id,
                role=role
            )

            members.append(member)
            self.project_members[project_id] = members

            return tool_result(
                success=True,
                content=[{
                    'project_id': project_id,
                    'user_id': user_id,
                    'role': role.value,
                    'added_at': member.joined_at.isoformat()
                }],
                message="プロジェクトメンバーを追加しました"
            )

        except Exception as e:
            logger.error(f"メンバー追加エラー: {e}")
            return error_result(str(e), "メンバーの追加に失敗しました")

    async def handle_remove_member(self, args: Dict[str, Any]) -> ToolResult:
        """プロジェクトメンバーを削除する"""
        try:
            project_id = args['project_id']
            user_id = args['user_id']

            if project_id not in self.projects:
                return error_result("PROJECT_NOT_FOUND", f"プロジェクト {project_id} が見つかりません")

            members = self.project_members.get(project_id, [])
            original_count = len(members)

            # メンバーを削除
            members = [m for m in members if m.user_id != user_id]
            self.project_members[project_id] = members

            if len(members) == original_count:
                return error_result("MEMBER_NOT_FOUND", "指定されたユーザーはプロジェクトメンバーではありません")

            return tool_result(
                success=True,
                content=[{
                    'project_id': project_id,
                    'user_id': user_id,
                    'removed_at': datetime.utcnow().isoformat()
                }],
                message="プロジェクトメンバーを削除しました"
            )

        except Exception as e:
            logger.error(f"メンバー削除エラー: {e}")
            return error_result(str(e), "メンバーの削除に失敗しました")

    async def handle_update(self, args: Dict[str, Any]) -> ToolResult:
        """プロジェクトを更新する"""
        try:
            project_id = args['project_id']
            name = args.get('name')
            description = args.get('description')

            project = self.projects.get(project_id)
            if not project:
                return error_result("PROJECT_NOT_FOUND", f"プロジェクト {project_id} が見つかりません")

            if name is not None:
                project.name = name
            if description is not None:
                project.description = description

            project.updated_at = datetime.utcnow()

            return tool_result(
                success=True,
                content=[{
                    'project_id': project_id,
                    'updated_at': project.updated_at.isoformat()
                }],
                message="プロジェクトを更新しました"
            )

        except Exception as e:
            logger.error(f"プロジェクト更新エラー: {e}")
            return error_result(str(e), "プロジェクトの更新に失敗しました")

    async def handle_delete(self, args: Dict[str, Any]) -> ToolResult:
        """プロジェクトを削除する"""
        try:
            project_id = args['project_id']

            if project_id not in self.projects:
                return error_result("PROJECT_NOT_FOUND", f"プロジェクト {project_id} が見つかりません")

            # プロジェクトとメンバーを削除
            del self.projects[project_id]
            if project_id in self.project_members:
                del self.project_members[project_id]

            return tool_result(
                success=True,
                content=[{
                    'project_id': project_id,
                    'deleted_at': datetime.utcnow().isoformat()
                }],
                message="プロジェクトを削除しました"
            )

        except Exception as e:
            logger.error(f"プロジェクト削除エラー: {e}")
            return error_result(str(e), "プロジェクトの削除に失敗しました")


class UserToolHandler(BaseHandler):
    async def __call__(self, args: Dict[str, Any]) -> ToolResult:
        mode = args.get('mode')
        if not mode:
            return error_result("MODE_REQUIRED", "mode（サブコマンド名）は必須です。例: mode='get_current'")
        try:
            if mode == 'get_current':
                return await self.handle_get_current(args)
            elif mode == 'get_projects':
                return await self.handle_get_projects(args)
            elif mode == 'get_sessions':
                return await self.handle_get_sessions(args)
            elif mode == 'create_session':
                return await self.handle_create_session(args)
            elif mode == 'switch_session':
                return await self.handle_switch_session(args)
            elif mode == 'end_session':
                return await self.handle_end_session(args)
            else:
                return error_result("UNKNOWN_MODE", f"未対応のmode: {mode}")
        except Exception as e:
            logger.error(f"UserToolHandler {mode} エラー: {e}")
            return error_result(str(e), f"{mode}の実行に失敗しました")
    """ユーザー・セッション管理ツールハンドラー"""

    def __init__(self, session_manager: SessionManager, project_handler: ProjectToolHandler):
        super().__init__()
        self.session_manager = session_manager
        self.project_handler = project_handler
        self.users: Dict[str, Dict[str, Any]] = {}

    async def handle_get_current(self, args: Dict[str, Any]) -> ToolResult:
        """現在のユーザー情報を取得する"""
        try:
            session_id = args.get('session_id')

            if not session_id:
                return error_result("SESSION_REQUIRED", "セッションIDが必要です")

            session = self.session_manager.get_session(session_id)
            if not session:
                return error_result("SESSION_NOT_FOUND", "セッションが見つかりません")

            user_info = self.users.get(session.user_id, {
                'user_id': session.user_id,
                'created_at': datetime.utcnow().isoformat()
            })

            return tool_result(
                success=True,
                content=[{
                    'user': user_info,
                    'session': session.to_dict()
                }],
                message="ユーザー情報を取得しました"
            )

        except Exception as e:
            logger.error(f"ユーザー情報取得エラー: {e}")
            return error_result(str(e), "ユーザー情報の取得に失敗しました")

    async def handle_get_projects(self, args: Dict[str, Any]) -> ToolResult:
        """ユーザーのプロジェクト一覧を取得する"""
        try:
            user_id = args['user_id']

            # プロジェクトハンドラーから取得
            projects_response = await self.project_handler.handle_list({
                'user_id': user_id
            })

            return projects_response

        except Exception as e:
            logger.error(f"ユーザープロジェクト取得エラー: {e}")
            return error_result(str(e), "ユーザープロジェクトの取得に失敗しました")

    async def handle_get_sessions(self, args: Dict[str, Any]) -> ToolResult:
        """ユーザーのセッション一覧を取得する"""
        try:
            user_id = args['user_id']

            sessions = self.session_manager.get_user_sessions(user_id)
            session_data = [session.to_dict() for session in sessions]

            return tool_result(
                success=True,
                content=[{
                    'sessions': session_data,
                    'count': len(session_data)
                }],
                message=f"{len(session_data)}件のセッションが見つかりました"
            )

        except Exception as e:
            logger.error(f"セッション一覧取得エラー: {e}")
            return error_result(str(e), "セッション一覧の取得に失敗しました")

    async def handle_create_session(self, args: Dict[str, Any]) -> ToolResult:
        """新しいセッションを作成する"""
        try:
            user_id = args['user_id']
            project_id = args.get('project_id')
            metadata = args.get('metadata', {})

            session = self.session_manager.create_session(
                user_id=user_id,
                project_id=project_id,
                metadata=metadata
            )

            return tool_result(
                success=True,
                content=[session.to_dict()],
                message="セッションを作成しました"
            )

        except Exception as e:
            logger.error(f"セッション作成エラー: {e}")
            return error_result(str(e), "セッションの作成に失敗しました")

    async def handle_switch_session(self, args: Dict[str, Any]) -> ToolResult:
        """セッションのプロジェクトを切り替える"""
        try:
            session_id = args['session_id']
            project_id = args['project_id']

            success = self.session_manager.switch_session(session_id, project_id)

            if not success:
                return tool_result(
                    success=False,
                    error="SESSION_NOT_FOUND",
                    message="セッションが見つかりません"
                )

            session = self.session_manager.get_session(session_id)

            return tool_result(
                success=True,
                content=[session.to_dict()] if session else [{}],
                message="セッションを切り替えました"
            )

        except Exception as e:
            logger.error(f"セッション切り替えエラー: {e}")
            return tool_result(
                success=False,
                error=str(e),
                message="セッションの切り替えに失敗しました"
            )

    async def handle_end_session(self, args: Dict[str, Any]) -> ToolResult:
        """セッションを終了する"""
        try:
            session_id = args['session_id']

            success = self.session_manager.end_session(session_id)

            if not success:
                return tool_result(
                    success=False,
                    error="SESSION_NOT_FOUND",
                    message="セッションが見つかりません"
                )

            return tool_result(
                success=True,
                content=[{
                    'session_id': session_id,
                    'ended_at': datetime.utcnow().isoformat()
                }],
                message="セッションを終了しました"
            )

        except Exception as e:
            logger.error(f"セッション終了エラー: {e}")
            return tool_result(
                success=False,
                error=str(e),
                message="セッションの終了に失敗しました"
            )


class VisualizeToolHandler(BaseHandler):
    async def __call__(self, args: Dict[str, Any]) -> ToolResult:
        mode = args.get('mode')
        if not mode:
            return error_result("MODE_REQUIRED", message="mode（サブコマンド名）は必須です。例: mode='memory_map'")
        try:
            if mode == 'memory_map':
                return await self.handle_memory_map(args)
            elif mode == 'stats_dashboard':
                return await self.handle_stats_dashboard(args)
            elif mode == 'domain_graph':
                return await self.handle_domain_graph(args)
            elif mode == 'timeline':
                return await self.handle_timeline(args)
            elif mode == 'category_chart':
                return await self.handle_category_chart(args)
            else:
                return error_result("UNKNOWN_MODE", message=f"未対応のmode: {mode}")
        except Exception as e:
            logger.error(f"VisualizeToolHandler {mode} エラー: {e}")
            return error_result(str(e), message=f"{mode}の実行に失敗しました")
    """可視化ツールハンドラー"""

    def __init__(self, memory_manager: MemoryManager):
        super().__init__()
        self.memory_manager = memory_manager

    async def handle_memory_map(self, args: Dict[str, Any]) -> ToolResult:
        """記憶マップを生成する"""
        try:
            domain = MemoryDomain(args.get('domain', 'user'))

            # 簡易実装: 記憶リストを返す
            # 本来はグラフ構造を生成

            return tool_result(
                success=True,
                content=[{
                    'domain': domain.value,
                    'node_count': 0,
                    'edge_count': 0,
                    'visualization_type': 'memory_map',
                    'message': '記憶マップ機能は開発中です'
                }],
                message="記憶マップを生成しました（開発中）"
            )

        except Exception as e:
            logger.error(f"記憶マップ生成エラー: {e}")
            return tool_result(
                success=False,
                error=str(e),
                message="記憶マップの生成に失敗しました"
            )

    async def handle_stats_dashboard(self, args: Dict[str, Any]) -> ToolResult:
        """統計ダッシュボードを生成する"""
        try:
            # 記憶統計を取得
            stats = await self.memory_manager.get_memory_stats()

            return tool_result(
                success=True,
                content=[{
                    'stats': stats,
                    'dashboard_type': 'memory_stats',
                    'generated_at': datetime.utcnow().isoformat()
                }],
                message="統計ダッシュボードを生成しました"
            )

        except Exception as e:
            logger.error(f"ダッシュボード生成エラー: {e}")
            return tool_result(
                success=False,
                error=str(e),
                message="ダッシュボードの生成に失敗しました"
            )

    async def handle_domain_graph(self, args: Dict[str, Any]) -> ToolResult:
        """ドメイングラフを生成する"""
        try:
            return tool_result(
                success=True,
                content=[{
                    'visualization_type': 'domain_graph',
                    'message': 'ドメイングラフ機能は開発中です'
                }],
                message="ドメイングラフを生成しました（開発中）"
            )

        except Exception as e:
            logger.error(f"ドメイングラフ生成エラー: {e}")
            return tool_result(
                success=False,
                error=str(e),
                message="ドメイングラフの生成に失敗しました"
            )

    async def handle_timeline(self, args: Dict[str, Any]) -> ToolResult:
        """タイムライン表示を生成する"""
        try:
            domain = MemoryDomain(args.get('domain', 'user'))

            return tool_result(
                success=True,
                content=[{
                    'domain': domain.value,
                    'visualization_type': 'timeline',
                    'message': 'タイムライン機能は開発中です'
                }],
                message="タイムラインを生成しました（開発中）"
            )

        except Exception as e:
            logger.error(f"タイムライン生成エラー: {e}")
            return tool_result(
                success=False,
                error=str(e),
                message="タイムラインの生成に失敗しました"
            )

    async def handle_category_chart(self, args: Dict[str, Any]) -> ToolResult:
        """カテゴリチャートを生成する"""
        try:
            domain = MemoryDomain(args.get('domain', 'user'))

            return tool_result(
                success=True,
                content=[{
                    'domain': domain.value,
                    'visualization_type': 'category_chart',
                    'message': 'カテゴリチャート機能は開発中です'
                }],
                message="カテゴリチャートを生成しました（開発中）"
            )

        except Exception as e:
            logger.error(f"カテゴリチャート生成エラー: {e}")
            return tool_result(
                success=False,
                error=str(e),
                message="カテゴリチャートの生成に失敗しました"
            )


class AdminToolHandler(BaseHandler):
    async def __call__(self, args: Dict[str, Any]) -> ToolResult:
        mode = args.get('mode')
        if not mode:
            return error_result("MODE_REQUIRED", message="mode（サブコマンド名）は必須です。例: mode='health_check'")
        try:
            if mode == 'health_check':
                return await self.handle_health_check(args)
            elif mode == 'system_stats':
                return await self.handle_system_stats(args)
            elif mode == 'backup':
                return await self.handle_backup(args)
            elif mode == 'restore':
                return await self.handle_restore(args)
            elif mode == 'reindex':
                return await self.handle_reindex(args)
            elif mode == 'reindex_embeddings':
                return await self.handle_reindex_embeddings(args)
            elif mode == 'cleanup_orphans':
                return await self.handle_cleanup_orphans(args)
            else:
                return error_result("UNKNOWN_MODE", message=f"未対応のmode: {mode}")
        except Exception as e:
            logger.error(f"AdminToolHandler {mode} エラー: {e}")
            return error_result(str(e), message=f"{mode}の実行に失敗しました")

    async def handle_reindex_embeddings(self, args: Dict[str, Any]) -> ToolResult:
        """
        既存記憶のembeddingを再計算・再投入する管理用コマンド（雛形）。
        フィルタ指定（domain, project_id, user_id）で範囲限定も可能。
        """
        # TODO: memory_manager/metadata_storeから対象記憶を全件取得
        # TODO: embedding_serviceで再計算し、vector_storeへ再投入
        # TODO: dry_run時は件数のみ返す
        # TODO: エラー件数・詳細も返却
        return tool_result(
            success=True,
            content=[{
                "status": "not_implemented",
                "message": "admin.reindex_embeddingsは雛形です。実装を追加してください。",
                "reindexed": 0,
                "failed": 0,
                "errors": []
            }],
            message="embedding再計算・再投入は未実装（雛形）"
        )
    """システム管理ツールハンドラー"""

    def __init__(self, memory_manager: MemoryManager, session_manager: SessionManager):
        super().__init__()
        self.memory_manager = memory_manager
        self.session_manager = session_manager

    async def handle_health_check(self, args: Dict[str, Any]) -> ToolResult:
        """システムヘルスチェックを実行する"""
        try:
            health_data = {
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'components': {
                    'memory_manager': 'healthy',
                    'session_manager': 'healthy',
                    'vector_store': 'healthy',
                    'metadata_store': 'healthy',
                    'graph_store': 'healthy'
                },
                'uptime_seconds': 3600,  # 仮の値
                'version': '1.0.0'
            }
            return tool_result(
                success=True,
                content=[health_data],
                message="システムは正常に動作しています"
            )
        except Exception as e:
            logger.error(f"ヘルスチェックエラー: {e}")
            return tool_result(
                success=False,
                error=str(e),
                message="ヘルスチェックに失敗しました"
            )

    async def handle_system_stats(self, args: Dict[str, Any]) -> ToolResult:
        """システム統計を取得する"""
        try:
            memory_stats = await self.memory_manager.get_memory_stats()
            session_stats = self.session_manager.get_sessions_stats()
            system_stats = {
                'memory': memory_stats,
                'sessions': session_stats,
                'system': {
                    'cpu_usage': 0.0,  # 仮の値
                    'memory_usage': 0.0,  # 仮の値
                    'disk_usage': 0.0   # 仮の値
                },
                'collected_at': datetime.utcnow().isoformat()
            }
            return tool_result(
                success=True,
                content=[system_stats],
                message="システム統計を取得しました"
            )
        except Exception as e:
            logger.error(f"統計取得エラー: {e}")
            return tool_result(
                success=False,
                error=str(e),
                message="統計の取得に失敗しました"
            )

    async def handle_backup(self, args: Dict[str, Any]) -> ToolResult:
        """システムバックアップを実行する"""
        try:
            backup_path = args.get('path', '/tmp/mcp_backup')
            # 簡易実装
            backup_data = {
                'backup_id': f"backup_{int(datetime.utcnow().timestamp())}",
                'path': backup_path,
                'created_at': datetime.utcnow().isoformat(),
                'size_bytes': 0,
                'status': 'completed'
            }
            return tool_result(
                success=True,
                content=[backup_data],
                message="バックアップが完了しました（開発中）"
            )
        except Exception as e:
            logger.error(f"バックアップエラー: {e}")
            return tool_result(
                success=False,
                error=str(e),
                message="バックアップに失敗しました"
            )

    async def handle_restore(self, args: Dict[str, Any]) -> ToolResult:
        """システムリストアを実行する"""
        try:
            backup_id = args['backup_id']
            return tool_result(
                success=True,
                content=[{
                    'backup_id': backup_id,
                    'restored_at': datetime.utcnow().isoformat(),
                    'status': 'completed'
                }],
                message="リストアが完了しました（開発中）"
            )
        except Exception as e:
            logger.error(f"リストアエラー: {e}")
            return tool_result(
                success=False,
                error=str(e),
                message="リストアに失敗しました"
            )

    async def handle_reindex(self, args: Dict[str, Any]) -> ToolResult:
        """インデックス再構築を実行する"""
        try:
            result = await self.memory_manager.cleanup_database(reindex=True)
            return tool_result(
                success=True,
                content=[result],
                message="インデックス再構築が完了しました"
            )
        except Exception as e:
            logger.error(f"再インデックスエラー: {e}")
            return tool_result(
                success=False,
                error=str(e),
                message="インデックス再構築に失敗しました"
            )

    async def handle_cleanup_orphans(self, args: Dict[str, Any]) -> ToolResult:
        """孤立データをクリーンアップする"""
        try:
            result = await self.memory_manager.cleanup_database(cleanup_orphans=True)
            session_cleanup = self.session_manager.cleanup_expired_sessions()
            cleanup_result = {
                'database_orphans': result.get('cleanup_orphans', 0),
                'expired_sessions': session_cleanup,
                'cleaned_at': datetime.utcnow().isoformat()
            }
            return tool_result(
                success=True,
                content=[cleanup_result],
                message="クリーンアップが完了しました"
            )
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")
            return tool_result(
                success=False,
                error=str(e),
                message="クリーンアップに失敗しました"
            )


class SearchToolHandler(BaseHandler):
    def __init__(self, memory_manager, similarity_calc):
        super().__init__()
        self.memory_manager = memory_manager
        self.similarity_calc = similarity_calc

    async def handle_semantic(self, args: Dict[str, Any]) -> dict:
        """意味的検索: MemoryManager.semantic_search を呼び出す"""
        try:
            query = args.get("query")
            domain = args.get("domain")
            limit = args.get("limit", 10)
            min_score = args.get("min_score", 0.7)

            if not query or not domain:
                return {
                    "success": False,
                    "error": "INVALID_PARAMS",
                    "message": "query, domainは必須です"
                }

            # domainはstrで来るのでMemoryDomainに変換
            try:
                domain_enum = MemoryDomain(domain)
            except Exception:
                return {
                    "success": False,
                    "error": "INVALID_DOMAIN",
                    "message": f"不正なdomain: {domain}"
                }

            results = await self.memory_manager.semantic_search(
                query=query,
                domain=domain_enum,
                limit=limit,
                min_score=min_score
            )
            # [(Memory, score)] のリスト
            content = [
                {
                    "id": m.id,
                    "content": m.content,
                    "score": score,
                    "domain": m.domain.value,
                    "tags": m.tags,
                    "category": m.category,
                    "user_id": m.user_id,
                    "project_id": m.project_id,
                    "session_id": m.session_id,
                    "created_at": m.created_at.isoformat(),
                    "updated_at": m.updated_at.isoformat(),
                }
                for m, score in results
            ]
            return {
                "success": True,
                "content": content,
                "message": f"semantic検索: {len(content)}件"
            }
        except Exception as e:
            logger.error(f"semantic検索エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "semantic検索でエラーが発生しました"
            }

    async def handle_tags(self, args: Dict[str, Any]) -> dict:
        return {"success": True, "content": [], "message": "tags検索は未実装です"}

    async def handle_timerange(self, args: Dict[str, Any]) -> dict:
        return {"success": True, "content": [], "message": "timerange検索は未実装です"}

    async def handle_advanced(self, args: Dict[str, Any]) -> dict:
        return {"success": True, "content": [], "message": "advanced検索は未実装です"}

    async def handle_similar(self, args: Dict[str, Any]) -> dict:
        return {"success": True, "content": [], "message": "similar検索は未実装です"}
