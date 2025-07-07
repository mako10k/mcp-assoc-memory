"""
MCPAssocMemoryServer - SDK統合サーバ実装
"""


# FastMCP公式SDKベースの統合サーバ実装

# FastMCP公式SDKベースの統合サーバ実装
from mcp.server.fastmcp import FastMCP
from mcp_assoc_memory.core.memory_manager import MemoryManager
# 各ツールハンドラを直接import
from mcp_assoc_memory.handlers.tools import MemoryToolHandler, MemoryManageToolHandler, SearchToolHandler
from mcp_assoc_memory.handlers.tools_extended import ProjectToolHandler, UserToolHandler, VisualizeToolHandler, AdminToolHandler



from mcp_assoc_memory.storage.vector_store import ChromaVectorStore
from mcp_assoc_memory.storage.metadata_store import SQLiteMetadataStore
from mcp_assoc_memory.storage.graph_store import NetworkXGraphStore
from mcp_assoc_memory.core.embedding_service import EmbeddingService
from mcp_assoc_memory.core.similarity import SimilarityCalculator
from mcp_assoc_memory.auth.session import SessionManager

class MCPAssocMemoryServer:
    def __init__(self, config):
        self.config = config
        # ストレージ/サービス初期化
        self.vector_store = ChromaVectorStore(persist_directory=config.storage.data_dir)
        self.metadata_store = SQLiteMetadataStore(database_path=config.storage.metadata_db_path)
        self.graph_store = NetworkXGraphStore(graph_path=config.storage.graph_path)
        self.embedding_service = EmbeddingService()
        self.similarity_calc = SimilarityCalculator()
        self.session_manager = SessionManager(session_timeout_minutes=config.security.session_timeout_minutes)
        self.memory_manager = MemoryManager(
            vector_store=self.vector_store,
            metadata_store=self.metadata_store,
            graph_store=self.graph_store,
            embedding_service=self.embedding_service,
            similarity_calculator=self.similarity_calc
        )
        self.mcp = FastMCP("mcp-assoc-memory")
        self._register_tools()

    def _register_tools(self):
        # 各ツールハンドラのメソッドをFastMCPに直接登録
        memory_handler = MemoryToolHandler(self.memory_manager)
        memory_manage_handler = MemoryManageToolHandler(self.memory_manager)
        search_handler = SearchToolHandler(self.memory_manager, self.similarity_calc)
        project_handler = ProjectToolHandler(self.memory_manager, self.session_manager)
        user_handler = UserToolHandler(self.session_manager, project_handler)
        visualize_handler = VisualizeToolHandler(self.memory_manager)
        admin_handler = AdminToolHandler(self.memory_manager, self.session_manager)

        # memory
        self.mcp.tool(name="memory.store")(memory_handler.handle_store)
        self.mcp.tool(name="memory.search")(memory_handler.handle_search)
        self.mcp.tool(name="memory.get")(memory_handler.handle_get)
        self.mcp.tool(name="memory.get_related")(memory_handler.handle_get_related)
        self.mcp.tool(name="memory.update")(memory_handler.handle_update)
        self.mcp.tool(name="memory.delete")(memory_handler.handle_delete)
        # memory_manage
        self.mcp.tool(name="memory_manage.stats")(memory_manage_handler.handle_stats)
        self.mcp.tool(name="memory_manage.export")(memory_manage_handler.handle_export)
        self.mcp.tool(name="memory_manage.import")(memory_manage_handler.handle_import)
        self.mcp.tool(name="memory_manage.change_domain")(memory_manage_handler.handle_change_domain)
        self.mcp.tool(name="memory_manage.batch_delete")(memory_manage_handler.handle_batch_delete)
        self.mcp.tool(name="memory_manage.cleanup")(memory_manage_handler.handle_cleanup)
        # search
        self.mcp.tool(name="search.semantic")(search_handler.handle_semantic)
        self.mcp.tool(name="search.tags")(search_handler.handle_tags)
        self.mcp.tool(name="search.timerange")(search_handler.handle_timerange)
        self.mcp.tool(name="search.advanced")(search_handler.handle_advanced)
        self.mcp.tool(name="search.similar")(search_handler.handle_similar)
        # project
        self.mcp.tool(name="project.create")(project_handler.handle_create)
        self.mcp.tool(name="project.list")(project_handler.handle_list)
        self.mcp.tool(name="project.get")(project_handler.handle_get)
        self.mcp.tool(name="project.add_member")(project_handler.handle_add_member)
        self.mcp.tool(name="project.remove_member")(project_handler.handle_remove_member)
        self.mcp.tool(name="project.update")(project_handler.handle_update)
        self.mcp.tool(name="project.delete")(project_handler.handle_delete)
        # user
        self.mcp.tool(name="user.get_current")(user_handler.handle_get_current)
        self.mcp.tool(name="user.get_projects")(user_handler.handle_get_projects)
        self.mcp.tool(name="user.get_sessions")(user_handler.handle_get_sessions)
        self.mcp.tool(name="user.create_session")(user_handler.handle_create_session)
        self.mcp.tool(name="user.switch_session")(user_handler.handle_switch_session)
        self.mcp.tool(name="user.end_session")(user_handler.handle_end_session)
        # visualize
        self.mcp.tool(name="visualize.memory_map")(visualize_handler.handle_memory_map)
        self.mcp.tool(name="visualize.stats_dashboard")(visualize_handler.handle_stats_dashboard)
        self.mcp.tool(name="visualize.domain_graph")(visualize_handler.handle_domain_graph)
        self.mcp.tool(name="visualize.timeline")(visualize_handler.handle_timeline)
        self.mcp.tool(name="visualize.category_chart")(visualize_handler.handle_category_chart)
        # admin
        self.mcp.tool(name="admin.health_check")(admin_handler.handle_health_check)
        self.mcp.tool(name="admin.system_stats")(admin_handler.handle_system_stats)
        self.mcp.tool(name="admin.backup")(admin_handler.handle_backup)
        self.mcp.tool(name="admin.restore")(admin_handler.handle_restore)
        self.mcp.tool(name="admin.reindex")(admin_handler.handle_reindex)
        self.mcp.tool(name="admin.cleanup_orphans")(admin_handler.handle_cleanup_orphans)

    # FastMCPのリソース登録が必要な場合はここで実装
    # def _register_resources(self):
    #     self.mcp.resource(uri)(resource_func)

    def run(self):
        # FastMCPのAPIに合わせて起動
        # transports引数がない場合は、configで有効なものを環境変数等で切り替え
        # 例: MCP_SERVER_TRANSPORT=stdio,http,sse など
        self.mcp.run()
