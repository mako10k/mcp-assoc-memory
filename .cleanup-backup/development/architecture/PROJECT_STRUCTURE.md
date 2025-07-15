# プロジェクト構造設計

## 1. ディレクトリ構造

```
mcp-assoc-memory/
├── README.md                    # プロジェクト概要
├── SPECIFICATION.md             # 詳細仕様書
├── ARCHITECTURE.md              # アーキテクチャ設計
├── DEVELOPMENT_PLAN.md          # 開発計画
├── TECHNICAL_CONSIDERATIONS.md  # 技術検討事項
├── PROJECT_STRUCTURE.md         # プロジェクト構造（このファイル）
├── LICENSE                      # ライセンス
├── .gitignore                   # Git除外ファイル
├── pyproject.toml              # プロジェクト設定・依存関係
├── requirements.txt            # 依存パッケージ
├── docker-compose.yml          # 開発環境用
├── Dockerfile                  # コンテナイメージ
│
├── src/                        # ソースコード
│   └── mcp_assoc_memory/
│       ├── __init__.py
│       ├── main.py             # エントリーポイント
│       ├── server.py           # MCPサーバー実装
│       ├── config.py           # 設定管理
│       │
│       ├── transport/          # 通信層 🆕
│       │   ├── __init__.py
│       │   ├── sse_handler.py   # FastMCP SSEラッパー（SDKベース）
│       │
│       ├── handlers/           # MCP ハンドラー
│       │   ├── __init__.py
│       │   ├── tools.py        # ツールハンドラー
│       │   └── resources.py    # リソースハンドラー
│       │
│       ├── core/               # コア機能
│       │   ├── __init__.py
│       │   ├── memory_manager.py    # 記憶管理
│       │   ├── embedding_service.py # 埋め込みサービス
│       │   ├── similarity.py        # 類似度計算
│       │   └── association.py       # 関連性管理
│       │
│       ├── storage/            # ストレージ層
│       │   ├── __init__.py
│       │   ├── base.py         # 基底クラス
│       │   ├── vector_store.py # ベクトルストア
│       │   ├── metadata_store.py # メタデータストア
│       │   └── graph_store.py  # グラフストア
│       │
│       ├── models/             # データモデル
│       │   ├── __init__.py
│       │   ├── memory.py       # 記憶モデル
│       │   ├── association.py  # 関連性モデル
│       │   ├── project.py      # プロジェクトモデル 🆕
│       │   └── schemas.py      # MCPスキーマ
│       │
│       ├── auth/               # 認証・認可 🆕
│       │   ├── __init__.py
│       │   ├── api_key.py      # APIキー認証
│       │   ├── jwt_auth.py     # JWT認証
│       │   └── session.py      # セッション管理
│       │
│       ├── utils/              # ユーティリティ
│       │   ├── __init__.py
│       │   ├── cache.py        # キャッシュ機能
│       │   ├── logging.py      # ログ設定
│       │   ├── metrics.py      # メトリクス収集
│       │   └── validation.py   # 入力値検証
│       │
│       └── visualization/      # 可視化機能
│           ├── __init__.py
│           ├── graph_viz.py    # グラフ可視化
│           ├── stats.py        # 統計表示
│           └── templates/      # HTMLテンプレート
│               ├── memory_map.html
│               └── stats_dashboard.html
│
├── tests/                      # テストコード
│   ├── __init__.py
│   ├── conftest.py            # pytest設定
│   ├── test_server.py         # サーバーテスト
│   │
│   ├── unit/                  # 単体テスト
│   │   ├── __init__.py
│   │   ├── test_memory_manager.py
│   │   ├── test_embedding_service.py
│   │   ├── test_similarity.py
│   │   ├── test_vector_store.py
│   │   ├── test_metadata_store.py
│   │   └── test_graph_store.py
│   │
│   ├── integration/           # 統合テスト
│   │   ├── __init__.py
│   │   ├── test_memory_operations.py
│   │   ├── test_search_functionality.py
│   │   └── test_data_consistency.py
│   │
│   └── performance/           # パフォーマンステスト
│       ├── __init__.py
│       ├── test_response_time.py
│       └── test_memory_usage.py
│
├── docs/                      # ドキュメント
│   ├── installation.md       # インストール手順
│   ├── user_guide.md         # ユーザーガイド
│   ├── api_reference.md      # API リファレンス
│   ├── deployment.md         # デプロイメントガイド
│   ├── troubleshooting.md    # トラブルシューティング
│   └── examples/             # 使用例
│       ├── basic_usage.py
│       ├── advanced_search.py
│       └── custom_plugins.py
│
├── scripts/                   # スクリプト
│   ├── setup_dev_env.sh      # 開発環境セットアップ
│   ├── run_tests.sh          # テスト実行
│   ├── build_docker.sh       # Docker ビルド
│   └── backup_data.py        # データバックアップ
│
├── config/                    # 設定ファイル
│   ├── default.json          # デフォルト設定
│   ├── development.json      # 開発環境設定
│   ├── production.json       # 本番環境設定
│   └── test.json             # テスト環境設定
│
├── data/                      # データディレクトリ（gitignore）
│   ├── chroma/               # Chroma データ
│   ├── metadata.db           # SQLite データベース
│   ├── graph.pkl             # グラフデータ
│   └── logs/                 # ログファイル
│
└── examples/                  # 実行例・デモ
    ├── claude_integration.py  # Claude連携例
    ├── chatgpt_integration.py # ChatGPT連携例
    ├── basic_demo.py          # 基本デモ
    └── advanced_demo.py       # 高度な使用例
```

## 2. コアモジュール設計

### 2.1 main.py（エントリーポイント）

```python
"""
MCP Associative Memory Server
マルチトランスポート対応エントリーポイント
"""
import asyncio
import argparse
import logging
from mcp_assoc_memory.server import MCPAssocMemoryServer
from mcp_assoc_memory.config import load_config

async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="MCP Associative Memory Server")
    parser.add_argument(
        "--transport", 
        default="stdio",
        choices=["stdio", "http", "sse", "all"],
        help="通信方式 (stdio/http/sse/all)"
    )
    parser.add_argument("--http-port", type=int, default=8000, help="HTTP ポート")
    parser.add_argument("--sse-port", type=int, default=8001, help="SSE ポート")
    parser.add_argument("--config", help="設定ファイルパス")
    
    args = parser.parse_args()
    
    # 設定読み込み
    config = load_config(args.config)
    
    # CLI引数で設定を上書き
    if args.transport != "stdio":
        if args.transport == "http" or args.transport == "all":
            config.transports.http.enabled = True
            config.transports.http.port = args.http_port
        if args.transport == "sse" or args.transport == "all":
            config.transports.sse.enabled = True
            config.transports.sse.port = args.sse_port
        if args.transport != "all":
            config.transports.stdio.enabled = False
    
    # ログ設定
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # サーバー起動
    server = MCPAssocMemoryServer(config)
    
    try:
        # FastMCPサーバ起動例
        server.run(transport=args.transport, host="0.0.0.0", port=args.http_port)
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logging.info("Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2.2 server.py（MCPサーバー）

```python
"""
MCP サーバー実装
Model Context Protocol に準拠したサーバー
"""
from mcp.server import Server
from mcp.types import Tool, Resource
from mcp_assoc_memory.handlers.tools import ToolHandler
from mcp_assoc_memory.handlers.resources import ResourceHandler
from mcp_assoc_memory.core.memory_manager import MemoryManager

class MCPAssocMemoryServer:
    def __init__(self, config):
        self.config = config
        self.server = Server("mcp-assoc-memory")
        self.memory_manager = MemoryManager(config)
        self.tool_handler = ToolHandler(self.memory_manager)
        self.resource_handler = ResourceHandler(self.memory_manager)
        
        self._register_tools()
        self._register_resources()
    
    def _register_tools(self):
        """ツールを登録"""
        tools = [
            Tool(
                name="store_memory",
                description="記憶を保存する",
                inputSchema={...}
            ),
            Tool(
                name="search_memory", 
                description="記憶を検索する",
                inputSchema={...}
            ),
            # 他のツール...
        ]
        
        for tool in tools:
            self.server.register_tool(tool)
    
    def _register_resources(self):
        """リソースを登録"""
        resources = [
            Resource(
                uri="memory://map",
                name="記憶マップ",
                description="記憶のネットワーク構造を可視化"
            ),
            Resource(
                uri="memory://stats", 
                name="記憶統計",
                description="記憶に関する統計情報"
            ),
        ]
        
        for resource in resources:
            self.server.register_resource(resource)
```

### 2.3 models/memory.py（データモデル）

```python
"""
記憶データモデル
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

@dataclass
class Memory:
    """記憶を表すデータクラス"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    embedding: Optional[List[float]] = None
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    importance: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_access(self):
        """アクセス回数を更新"""
        self.access_count += 1
        self.updated_at = datetime.now()
    
    def calculate_dynamic_importance(self) -> float:
        """動的重要度を計算"""
        # アクセス頻度による重み
        access_weight = min(self.access_count / 100, 0.3)
        
        # 時間経過による減衰
        days_old = (datetime.now() - self.created_at).days
        temporal_decay = max(0.5, 1.0 - (days_old / 365) * 0.5)
        
        return min(1.0, self.importance + access_weight) * temporal_decay

@dataclass 
class Association:
    """記憶間の関連性を表すデータクラス"""
    from_memory_id: str
    to_memory_id: str
    strength: float
    type: str  # semantic, temporal, manual, inferred
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 2.4 core/memory_manager.py（記憶管理）

```python
"""
記憶管理の中心的なクラス
"""
from typing import List, Optional, Dict, Any
from mcp_assoc_memory.models.memory import Memory, Association
from mcp_assoc_memory.storage.vector_store import VectorStore
from mcp_assoc_memory.storage.metadata_store import MetadataStore
from mcp_assoc_memory.storage.graph_store import GraphStore
from mcp_assoc_memory.core.embedding_service import EmbeddingService
from mcp_assoc_memory.core.association import AssociationManager

class MemoryManager:
    """記憶操作の中心的な管理クラス"""
    
    def __init__(self, config):
        self.config = config
        self.vector_store = VectorStore(config.vector_store)
        self.metadata_store = MetadataStore(config.metadata_store)
        self.graph_store = GraphStore(config.graph_store)
        self.embedding_service = EmbeddingService(config.embedding)
        self.association_manager = AssociationManager(
            self.graph_store, self.vector_store
        )
    
    async def store_memory(self, 
                          content: str,
                          tags: List[str] = None,
                          category: str = "general",
                          importance: float = 0.5,
                          **metadata) -> Memory:
        """記憶を保存"""
        memory = Memory(
            content=content,
            tags=tags or [],
            category=category,
            importance=importance,
            metadata=metadata
        )
        
        # 埋め込み生成
        memory.embedding = await self.embedding_service.embed_text(content)
        
        # ストレージに保存
        await self.vector_store.add_memory(memory)
        await self.metadata_store.save_memory(memory)
        await self.graph_store.add_node(memory.id, memory)
        
        # 関連性の自動生成
        await self.association_manager.create_auto_associations(memory)
        
        return memory
    
    async def search_memories(self,
                             query: str,
                             limit: int = 10,
                             threshold: float = 0.7,
                             category: Optional[str] = None) -> List[Memory]:
        """記憶を検索"""
        # クエリの埋め込み生成
        query_embedding = await self.embedding_service.embed_text(query)
        
        # ベクトル検索
        candidates = await self.vector_store.search_similar(
            query_embedding, limit * 2, category
        )
        
        # メタデータで詳細情報を取得
        memories = []
        for candidate in candidates:
            if candidate['score'] >= threshold:
                memory_data = await self.metadata_store.get_memory(candidate['id'])
                if memory_data:
                    memory = Memory(**memory_data)
                    memory.update_access()  # アクセス回数更新
                    memories.append(memory)
        
        # 重要度でソート
        memories.sort(key=lambda m: m.calculate_dynamic_importance(), reverse=True)
        return memories[:limit]
    
    async def get_related_memories(self,
                                  memory_id: str,
                                  depth: int = 2,
                                  limit: int = 10) -> List[Memory]:
        """関連記憶を取得"""
        related_ids = await self.association_manager.get_related_memories(
            memory_id, depth
        )
        
        memories = []
        for mem_id in related_ids[:limit]:
            memory_data = await self.metadata_store.get_memory(mem_id)
            if memory_data:
                memories.append(Memory(**memory_data))
        
        return memories
```

## 3. 設定管理設計

### 3.1 config.py

```python
"""
設定管理モジュール（マルチトランスポート対応）
"""
import json
import os
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class CORSConfig:
    allowed_origins: List[str] = None
    allowed_methods: List[str] = None
    
    def __post_init__(self):
        if self.allowed_origins is None:
            self.allowed_origins = ["http://localhost:3000"]
        if self.allowed_methods is None:
            self.allowed_methods = ["GET", "POST", "OPTIONS"]

@dataclass
class STDIOConfig:
    enabled: bool = True

@dataclass
class HTTPConfig:
    enabled: bool = False
    host: str = "localhost"
    port: int = 8000
    cors: CORSConfig = None
    auth_type: str = "api_key"  # none, api_key, jwt
    
    def __post_init__(self):
        if self.cors is None:
            self.cors = CORSConfig()

@dataclass
class SSEConfig:
    enabled: bool = False
    host: str = "localhost"
    port: int = 8001
    max_connections: int = 100
    heartbeat_interval: int = 30

@dataclass
class TransportsConfig:
    stdio: STDIOConfig = None
    http: HTTPConfig = None
    sse: SSEConfig = None
    
    def __post_init__(self):
        if self.stdio is None:
            self.stdio = STDIOConfig()
        if self.http is None:
            self.http = HTTPConfig()
        if self.sse is None:
            self.sse = SSEConfig()

@dataclass
class EmbeddingConfig:
    provider: str = "openai"
    model: str = "text-embedding-3-small"
    api_key: Optional[str] = None
    batch_size: int = 100

@dataclass
class VectorStoreConfig:
    type: str = "chroma"
    persist_directory: str = "./data/chroma"

@dataclass
class MetadataStoreConfig:
    type: str = "sqlite"
    path: str = "./data/metadata.db"

@dataclass 
class GraphStoreConfig:
    type: str = "networkx"
    persist_path: str = "./data/graph.pkl"

@dataclass
class MemoryConfig:
    default_importance: float = 0.5
    similarity_threshold: float = 0.7
    max_associations_per_memory: int = 10
    auto_association_threshold: float = 0.8

@dataclass
class ServerConfig:
    host: str = "localhost"
    port: int = 8000
    log_level: str = "INFO"

@dataclass
class Config:
    embedding: EmbeddingConfig
    vector_store: VectorStoreConfig
    metadata_store: MetadataStoreConfig
    graph_store: GraphStoreConfig
    memory: MemoryConfig
    server: ServerConfig

def load_config(config_path: Optional[str] = None) -> Config:
    """設定を読み込み"""
    if config_path is None:
        env = os.getenv("ENVIRONMENT", "development")
        config_path = f"config/{env}.json"
    
    with open(config_path, 'r') as f:
        config_dict = json.load(f)
    
    # 環境変数による上書き
    if api_key := os.getenv("OPENAI_API_KEY"):
        config_dict["embedding"]["api_key"] = api_key
    
    return Config(
        embedding=EmbeddingConfig(**config_dict["embedding"]),
        vector_store=VectorStoreConfig(**config_dict["vector_store"]),
        metadata_store=MetadataStoreConfig(**config_dict["metadata_store"]),
        graph_store=GraphStoreConfig(**config_dict["graph_store"]),
        memory=MemoryConfig(**config_dict["memory"]),
        server=ServerConfig(**config_dict["server"])
    )
```

## 4. テスト構造設計

### 4.1 conftest.py（pytest設定）

```python
"""
pytest設定とフィクスチャ
"""
import pytest
import tempfile
import shutil
from mcp_assoc_memory.config import Config, EmbeddingConfig, VectorStoreConfig
from mcp_assoc_memory.core.memory_manager import MemoryManager

@pytest.fixture
def temp_dir():
    """テスト用一時ディレクトリ"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def test_config(temp_dir):
    """テスト用設定"""
    return Config(
        embedding=EmbeddingConfig(
            provider="sentence_transformers",
            model="all-MiniLM-L6-v2"
        ),
        vector_store=VectorStoreConfig(
            persist_directory=f"{temp_dir}/chroma"
        ),
        metadata_store=MetadataStoreConfig(
            path=f"{temp_dir}/test.db"
        ),
        # ... 他の設定
    )

@pytest.fixture
def memory_manager(test_config):
    """テスト用記憶管理インスタンス"""
    return MemoryManager(test_config)

@pytest.fixture
def sample_memories():
    """サンプル記憶データ"""
    return [
        {
            "content": "Pythonは素晴らしいプログラミング言語です。",
            "tags": ["python", "programming"],
            "category": "technology"
        },
        {
            "content": "機械学習は人工知能の重要な分野です。",
            "tags": ["ai", "machine-learning"],
            "category": "technology"
        },
        # ... 他のサンプル
    ]
```

## 5. ビルド・デプロイメント設計

### 5.1 pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mcp-assoc-memory"
version = "0.1.0"
description = "Associative Memory Server for LLMs using Model Context Protocol"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.11"

dependencies = [
    "mcp>=0.1.0",
    "chromadb>=0.4.0",
    "openai>=1.0.0",
    "sentence-transformers>=2.2.0",
    "networkx>=3.0",
    "sqlite3",
    "aiofiles>=23.0.0",
    "pydantic>=2.0.0",
    "numpy>=1.24.0",
    "plotly>=5.0.0",
    "jinja2>=3.1.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "websockets>=12.0",
    "python-jose>=3.3.0",
    "bcrypt>=4.0.0",
    "httpx>=0.25.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.4.0",
    "flake8>=6.0.0"
]

[project.scripts]
mcp-assoc-memory = "mcp_assoc_memory.main:main"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### 5.2 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY src/ ./src/
COPY config/ ./config/

# データディレクトリの作成
RUN mkdir -p /app/data/chroma /app/data/logs

# 非rootユーザーの作成
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || \
        python -c "import sys; sys.exit(0)"  # STDIO mode fallback

# ポート公開
EXPOSE 8000 8001

# 起動コマンド（環境変数で制御）
CMD ["python", "-m", "src.mcp_assoc_memory.main", "--transport", "${TRANSPORT:-stdio}"]
```

この構造設計により、以下の利点が得られます：

1. **モジュラー設計**: 各機能が独立したモジュールとして実装
2. **テスト容易性**: 各レイヤーが独立してテスト可能
3. **拡張性**: 新機能の追加が容易
4. **保守性**: コードの可読性と修正の容易さ
5. **デプロイ容易性**: Docker化とCI/CD対応
