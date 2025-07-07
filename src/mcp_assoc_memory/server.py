if __name__ == "__main__":
    import os
    import sys
    from mcp_assoc_memory.config import Config
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    import logging
    log_path = os.path.join(logs_dir, "mcp_server.log")
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        filemode="a"
    )
    # 標準出力にもログを出す
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    console.setFormatter(formatter)
    logging.getLogger("").addHandler(console)
    # 設定ロード
    config = Config.load()
    from mcp_assoc_memory.server import MCPAssocMemoryServer
    try:
        server = MCPAssocMemoryServer(config)
        logging.info("MCPサーバ初期化完了。起動します...")
        server.run()
    except Exception as e:
        logging.exception("MCPサーバ起動時に例外が発生しました")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nMCPサーバを停止します...")
        sys.exit(0)
"""
MCPAssocMemoryServer - SDK統合サーバ実装
"""


# FastMCP公式SDKベースの統合サーバ実装

# FastMCP公式SDKベースの統合サーバ実装
from fastmcp import FastMCP
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
        import os
        metadata_db_path = os.path.join(config.storage.data_dir, "memory.db")
        graph_path = os.path.join(config.storage.data_dir, "memory_graph.gml")
        self.vector_store = ChromaVectorStore(persist_directory=config.storage.data_dir)
        self.metadata_store = SQLiteMetadataStore(database_path=metadata_db_path)
        self.graph_store = NetworkXGraphStore(graph_path=graph_path)
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
        self.mcp.tool(name="memory")(memory_handler.__call__)
        self.mcp.tool(name="memory_manage")(memory_manage_handler.__call__)
        self.mcp.tool(name="search")(search_handler.__call__)
        self.mcp.tool(name="project")(project_handler.__call__)
        self.mcp.tool(name="user")(user_handler.__call__)
        self.mcp.tool(name="visualize")(visualize_handler.__call__)
        self.mcp.tool(name="admin")(admin_handler.__call__)

    # FastMCPのリソース登録が必要な場合はここで実装
    # def _register_resources(self):
    #     self.mcp.resource(uri)(resource_func)

    def run(self):
        # Configのtransport設定に応じてFastMCPを起動
        tcfg = self.config.transport
        # 優先順位: HTTP > SSE > STDIO
        if getattr(tcfg, "http_enabled", False):
            self.mcp.run(
                transport="http",
                host=tcfg.http_host,
                port=tcfg.http_port
            )
        elif getattr(tcfg, "sse_enabled", False):
            self.mcp.run(
                transport="sse",
                host=tcfg.sse_host,
                port=tcfg.sse_port
            )
        elif getattr(tcfg, "stdio_enabled", True):
            self.mcp.run(transport="stdio")
        else:
            # どれも有効でなければデフォルト（STDIO）
            self.mcp.run(transport="stdio")
