# アーキテクチャ設計書

## 1. システム全体構成（マルチトランスポート対応）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          LLM クライアント層                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │Claude Desktop│  │VS Code Ext  │  │Web App      │  │Custom Integration   │ │
│  │             │  │             │  │             │  │                     │ │
│  │   (STDIO)   │  │   (STDIO)   │  │ (HTTP/SSE)  │  │ (HTTP/STDIO/SSE)    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┘
      │                 │                 │                 │
      │ JSON-RPC        │ JSON-RPC        │ JSON-RPC        │ JSON-RPC
      │ over STDIO      │ over STDIO      │ over HTTP/SSE   │ Multiple
      │                 │                 │                 │
┌─────▼─────────────────▼─────────────────▼─────────────────▼─────────────────┐
│                    MCP Server Transport Layer                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │STDIO Handler│  │HTTP Handler │  │SSE Handler  │  │Transport Manager    │ │
│  │             │  │             │  │             │  │                     │ │
│  │- stdin/out  │  │- REST API   │  │- WebSocket  │  │- Route requests     │ │
│  │- Process    │  │- CORS       │  │- Events     │  │- Load balancing     │ │
│  │- Simple     │  │- Auth       │  │- Realtime   │  │- Health monitoring  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                              │                                               │
│                     ┌────────▼────────┐                                     │
│                     │  Request Router │                                     │
│                     │ - Parse JSON-RPC│                                     │
│                     │ - Route to tools│                                     │
│                     │ - Handle errors │                                     │
│                     └────────┬────────┘                                     │
└─────────────────────────────────┼─────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┼─────────────────────────────────────────┐
│              MCP Server Core    │                                         │
├─────────────────────────────────┼─────────────────────────────────────────┤
│  ┌─────────────────────────────┬┴───────────────────────────────────────┐ │
│  │     Tool Handler            │     Resource Handler                   │ │
│  │ ┌─────────────────────────┐ │ ┌─────────────────────────────────────┐ │ │
│  │ │ - store_memory_*        │ │ │ - memory_map                        │ │ │
│  │ │ - search_memories_*     │ │ │ - memory_stats                      │ │ │
│  │ │ - get_related_memories  │ │ │ - memory_graph                      │ │ │
│  │ │ - create_project        │ │ │ - real-time updates (SSE)           │ │ │
│  │ │ - add_project_member    │ │ │                                     │ │ │
│  │ └─────────────────────────┘ │ └─────────────────────────────────────┘ │ │
│  └─────────────────────────────┴─────────────────────────────────────────┘ │
└─────────────────────────────────┼─────────────────────────────────────────┘
                                  │
                    [Memory Engine Layer - 変更なし]
                                  │
                     [Storage Layer - 変更なし]
```

## 2. コンポーネント詳細設計

### 2.1 MCP Server Layer

#### 2.1.1 Tool Handler
**責務**: LLMからのツール呼び出しを処理

```python
class ToolHandler:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def handle_store_memory(self, args: StoreMemoryArgs) -> StoreMemoryResult:
        """記憶保存ツール"""
        pass
    
    async def handle_search_memory(self, args: SearchMemoryArgs) -> SearchMemoryResult:
        """記憶検索ツール"""
        pass
    
    async def handle_get_related_memories(self, args: GetRelatedMemoriesArgs) -> GetRelatedMemoriesResult:
        """関連記憶取得ツール"""
        pass
```

#### 2.1.2 Resource Handler
**責務**: LLMからのリソース要求を処理

```python
class ResourceHandler:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
    
    async def get_memory_map(self) -> str:
        """記憶マップのHTMLを返す"""
        pass
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """記憶統計を返す"""
        pass
```

### 2.2 Memory Engine Layer

#### 2.2.1 Memory Manager
**責務**: 記憶操作の中心的な管理（ドメイン対応）

```python
class MemoryManager:
    def __init__(self, 
                 vector_store: VectorStore,
                 metadata_store: MetadataStore,
                 association_manager: AssociationManager,
                 embedding_service: EmbeddingService,
                 access_controller: AccessController):
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        self.association_manager = association_manager
        self.embedding_service = embedding_service
        self.access_controller = access_controller
    
    async def store_memory(self, content: str, domain: str, user_id: str, 
                          **kwargs) -> Memory:
        """記憶を保存（ドメイン指定）"""
        pass
    
    async def search_memories(self, query: str, user_id: str,
                             include_domains: List[str] = None,
                             **kwargs) -> List[Memory]:
        """記憶を検索（アクセス制御考慮）"""
        pass
    
    async def get_related_memories(self, memory_id: str, user_id: str,
                                  **kwargs) -> List[Memory]:
        """関連記憶を取得（アクセス制御考慮）"""
        pass
```

#### 2.2.2 Embedding Service
**責務**: テキストのベクトル埋め込み生成

```python
class EmbeddingService:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        self.client = OpenAI()
    
    async def embed_text(self, text: str) -> List[float]:
        """テキストを埋め込みベクトルに変換"""
        pass
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """複数テキストを一括で埋め込み"""
        pass
```

#### 2.2.3 Similarity Calculator
**責務**: 記憶間の類似度計算

```python
class SimilarityCalculator:
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """コサイン類似度を計算"""
        pass
    
    @staticmethod
    def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
        """ユークリッド距離を計算"""
        pass
    
    def calculate_semantic_similarity(self, memory1: Memory, memory2: Memory) -> float:
        """意味的類似度を計算"""
        pass
```

#### 2.2.4 Association Manager
**責務**: 記憶間の関連性管理

```python
class AssociationManager:
    def __init__(self, graph_store: GraphStore):
        self.graph_store = graph_store
    
    async def create_association(self, from_id: str, to_id: str, strength: float, type: str):
        """関連性を作成"""
        pass
    
    async def get_related_memories(self, memory_id: str, depth: int = 2) -> List[str]:
        """関連記憶IDを取得"""
        pass
    
    async def update_association_strength(self, from_id: str, to_id: str, new_strength: float):
        """関連強度を更新"""
        pass
```

#### 2.2.5 Access Controller
**責務**: ドメインベースのアクセス制御

```python
class AccessController:
    def __init__(self, project_manager: ProjectManager):
        self.project_manager = project_manager
    
    async def check_read_permission(self, memory: Memory, user_id: str,
                                   session_id: str = None) -> bool:
        """読み取り権限をチェック"""
        pass
    
    async def check_write_permission(self, memory: Memory, user_id: str,
                                    is_admin: bool = False) -> bool:
        """書き込み権限をチェック"""
        pass
    
    async def filter_accessible_memories(self, memories: List[Memory],
                                        user_id: str, session_id: str = None) -> List[Memory]:
        """アクセス可能な記憶のみフィルタリング"""
        pass
    
    async def get_user_accessible_domains(self, user_id: str) -> List[str]:
        """ユーザーがアクセス可能なドメインを取得"""
        pass

class ProjectManager:
    def __init__(self, metadata_store: MetadataStore):
        self.metadata_store = metadata_store
    
    async def create_project(self, name: str, owner_id: str, description: str = "") -> str:
        """プロジェクトを作成"""
        pass
    
    async def add_member(self, project_id: str, user_id: str, role: str):
        """プロジェクトメンバーを追加"""
        pass
    
    async def get_user_projects(self, user_id: str) -> Dict[str, str]:
        """ユーザーが参加するプロジェクトとロールを取得"""
        pass
    
    async def check_project_access(self, project_id: str, user_id: str) -> Optional[str]:
        """プロジェクトアクセス権限とロールを確認"""
        pass
```

### 2.3 Storage Layer

#### 2.3.1 Vector Store (Chroma)
**責務**: ベクトル埋め込みの保存と類似検索

```python
class ChromaVectorStore:
    def __init__(self, persist_directory: str):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection("memories")
    
    async def add_memory(self, memory: Memory):
        """記憶をベクトルストアに追加"""
        pass
    
    async def search_similar(self, query_embedding: List[float], limit: int = 10) -> List[Dict]:
        """類似記憶を検索"""
        pass
    
    async def delete_memory(self, memory_id: str):
        """記憶を削除"""
        pass
```

#### 2.3.2 Metadata Store (SQLite)
**責務**: 記憶のメタデータ管理（ドメイン対応）

```python
class SQLiteMetadataStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    async def save_memory_metadata(self, memory: Memory):
        """記憶メタデータを保存（ドメイン情報含む）"""
        pass
    
    async def get_memory_metadata(self, memory_id: str) -> Optional[Dict]:
        """記憶メタデータを取得"""
        pass
    
    async def search_by_category(self, category: str, user_id: str, 
                                accessible_domains: List[str]) -> List[str]:
        """カテゴリで検索（アクセス制御考慮）"""
        pass
    
    async def search_by_domain(self, domain: str, user_id: str, 
                              project_ids: List[str] = None) -> List[str]:
        """ドメインで検索"""
        pass
    
    async def get_accessible_memories(self, user_id: str, 
                                     user_projects: Dict[str, str],
                                     session_id: str = None) -> List[str]:
        """ユーザーがアクセス可能な記憶IDを取得"""
        pass
```

#### 2.3.3 Graph Store (NetworkX)
**責務**: 記憶間の関連性グラフ管理

```python
class NetworkXGraphStore:
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def add_node(self, memory_id: str, **attributes):
        """ノード（記憶）を追加"""
        pass
    
    def add_edge(self, from_id: str, to_id: str, weight: float, type: str):
        """エッジ（関連性）を追加"""
        pass
    
    def get_neighbors(self, memory_id: str, depth: int = 1) -> List[str]:
        """近傍ノードを取得"""
        pass
    
    def visualize_subgraph(self, center_id: str, radius: int = 2) -> str:
        """部分グラフを可視化"""

### 2.1 MCP Server Layer（SDKベース設計）

#### 2.1.0 FastMCPサーバ統合設計

- すべてのトランスポート（STDIO/HTTP/SSE）は`FastMCP`インスタンスの`run()`または`xxx_app()`で一元管理
- 独自のTransportManager/Handler/Routerは廃止
- MCPツール・リソースは`@mcp.tool()`/`@mcp.resource()`で登録
- main/エントリーポイントで`mcp.run(transport=...)`を呼び出すだけで切替可能

#### 例: FastMCPベースのトランスポート統合

```python
from mcp.server.fastmcp import FastMCP

            ws_ping_timeout=10

@mcp.tool()
        )
# ...他ツール/リソースも同様

if __name__ == "__main__":
    # transport="stdio"|"http"|"sse" で切替
    mcp.run(transport="sse", host="0.0.0.0", port=8001)
```

#### SSE/WebSocket/HTTPの詳細

- HTTP: `mcp.run(transport="http", ...)` または `mcp.http_app()` をASGI/Starlette/FastAPIにマウント
- SSE: `mcp.run(transport="sse", ...)` または `mcp.sse_app()` をASGI/Starletteにマウント
- STDIO: `mcp.run()`（デフォルト）

#### 旧設計からの主な変更点

- `TransportManager`, `STDIOHandler`, `HTTPHandler`, `SSEHandler`, `RequestRouter`は不要
- ルーティング・認証・エラー処理はFastMCPが自動で実施
- 設定値で`transport`/`host`/`port`を切替
```
## 3. データフロー

### 3.1 記憶保存フロー（ドメイン対応）

```
1. LLM → MCP Server: store_memory_with_domain(content, domain, project_id?, session_id?, ...)
2. Tool Handler → Access Controller: validate_store_permission(domain, user_id, project_id)
3. Tool Handler → Memory Manager: store_memory()
4. Memory Manager → Embedding Service: embed_text(content)
5. Embedding Service → OpenAI API: create_embedding()
6. Memory Manager → Vector Store: add_memory()
7. Memory Manager → Metadata Store: save_memory_metadata() (with domain info)
8. Memory Manager → Association Manager: create_associations()
9. Association Manager → Graph Store: add_node() + add_edge()
10. Memory Manager → Tool Handler: return Memory object
11. Tool Handler → LLM: return result
```

### 3.2 記憶検索フロー（ドメイン対応）

```
1. LLM → MCP Server: search_memories_with_domain(query, include_domains?, project_ids?, ...)
2. Tool Handler → Access Controller: get_accessible_domains(user_id)
3. Tool Handler → Memory Manager: search_memories()
4. Memory Manager → Embedding Service: embed_text(query)
5. Memory Manager → Vector Store: search_similar() (domain filtered)
6. Memory Manager → Metadata Store: get_memory_metadata() (for each result)
7. Memory Manager → Access Controller: filter_accessible_memories()
8. Memory Manager → Tool Handler: return List[Memory]
9. Tool Handler → LLM: return search results
```

### 3.3 関連記憶取得フロー（ドメイン対応）

```
1. LLM → MCP Server: get_related_memories(memory_id, depth, limit)
2. Tool Handler → Access Controller: check_read_permission(memory_id, user_id)
3. Tool Handler → Memory Manager: get_related_memories()
4. Memory Manager → Association Manager: get_related_memories()
5. Association Manager → Graph Store: get_neighbors()
6. Memory Manager → Metadata Store: get_memory_metadata() (for each related)
7. Memory Manager → Access Controller: filter_accessible_memories()
8. Memory Manager → Tool Handler: return List[Memory]
9. Tool Handler → LLM: return related memories
```

## 4. 設定管理

### 4.1 設定ファイル構造

```json
{
  "embedding": {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "api_key": "${OPENAI_API_KEY}",
    "batch_size": 100
  },
  "storage": {
    "vector_db": {
      "type": "chroma",
      "persist_directory": "./data/chroma"
    },
    "metadata_db": {
      "type": "sqlite",
      "path": "./data/metadata.db"
    },
    "graph_store": {
      "type": "networkx",
      "persist_path": "./data/graph.pkl"
    }
  },
  "memory": {
    "default_importance": 0.5,
    "similarity_threshold": 0.7,
    "max_associations_per_memory": 10,
    "auto_association_threshold": 0.8
  },
  "server": {
    "host": "localhost",
    "port": 8000,
    "log_level": "INFO"
  }
}
```

## 5. エラーハンドリング

### 5.1 例外階層

```python
class MemoryServerError(Exception):
    """基底例外クラス"""
    pass

class EmbeddingError(MemoryServerError):
    """埋め込み生成エラー"""
    pass

class StorageError(MemoryServerError):
    """ストレージエラー"""
    pass

class ValidationError(MemoryServerError):
    """入力値検証エラー"""
    pass

class MemoryNotFoundError(MemoryServerError):
    """記憶が見つからないエラー"""
    pass
```

### 5.2 エラー処理戦略

- **再試行機能**: 一時的な障害に対する指数バックオフ
- **フォールバック**: 代替手段での処理継続
- **ログ出力**: 詳細なエラー情報の記録
- **ユーザー通知**: 分かりやすいエラーメッセージ

## 6. パフォーマンス最適化

### 6.1 キャッシュ戦略

```python
class MemoryCache:
    def __init__(self, max_size: int = 1000):
        self.embedding_cache = LRUCache(maxsize=max_size)
        self.memory_cache = LRUCache(maxsize=max_size)
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """埋め込みキャッシュから取得"""
        pass
    
    def set_embedding(self, text: str, embedding: List[float]):
        """埋め込みをキャッシュに保存"""
        pass
```

### 6.2 バッチ処理

- 複数記憶の一括保存
- 埋め込み生成の一括処理
- 関連性計算の並列処理

### 6.3 インデックス戦略

- SQLiteのインデックス最適化
- Chromaのコレクション分割
- グラフの部分読み込み
