# 連想記憶MCPサーバー 仕様書

## 1. プロジェクト概要

### 1.1 目的
LLMが効率的に情報を記憶し、人間の連想記憶のように関連する情報を取得できるMCPサーバーを開発する。

### 1.2 ターゲットユーザー
- LLMを活用した開発者
- 知識管理システムを構築する研究者
- AI アシスタントを構築するエンジニア

### 1.3 主要価値提案
- **意味的検索**: キーワードだけでなく、意味的類似性による検索
- **連想機能**: 関連する記憶を自動的に取得
- **学習機能**: 使用パターンに基づく記憶の重み付け
- **拡張性**: プラグイン形式での機能拡張

## 2. 機能要件

### 2.1 コア機能（サブコマンド統合版）

#### 2.1.1 記憶操作 (memory)
```json
{
  "name": "memory",
  "description": "記憶の基本操作（保存、検索、取得、更新、削除）",
  "inputSchema": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "enum": ["store", "search", "get", "get_related", "update", "delete"],
        "description": "実行するアクション"
      },
      "memory_id": {
        "type": "string",
        "description": "記憶ID（get, get_related, update, delete時必須）"
      },
      "content": {
        "type": "string",
        "description": "記憶する内容（store, update時）"
      },
      "query": {
        "type": "string",
        "description": "検索クエリ（search時必須）"
      },
      "domain": {
        "type": "string",
        "enum": ["global", "user", "project", "session"],
        "description": "記憶ドメイン（store時必須）"
      },
      "include_domains": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["global", "user", "project", "session"]
        },
        "description": "検索対象ドメインリスト（search時）"
      },
      "project_id": {
        "type": "string",
        "description": "プロジェクトID"
      },
      "session_id": {
        "type": "string",
        "description": "セッションID"
      },
      "tags": {
        "type": "array",
        "items": {"type": "string"},
        "description": "記憶のタグ"
      },
      "category": {
        "type": "string",
        "description": "記憶のカテゴリ"
      },
      "importance": {
        "type": "number",
        "minimum": 0,
        "maximum": 1,
        "description": "記憶の重要度 (0-1)"
      },
      "limit": {
        "type": "number",
        "default": 10,
        "description": "取得する記憶の最大数"
      },
      "threshold": {
        "type": "number",
        "default": 0.7,
        "description": "類似度の閾値"
      },
      "depth": {
        "type": "number",
        "default": 2,
        "description": "関連性の深度（get_related時）"
      }
    },
    "required": ["action"]
  }
}
```

#### 2.1.2 記憶管理 (memory_manage)
```json
{
  "name": "memory_manage",
  "description": "記憶の管理・統計・バッチ操作",
  "inputSchema": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "enum": ["stats", "export", "import", "change_domain", "batch_delete", "cleanup", "list_categories"],
        "description": "実行するアクション"
      },
      "memory_ids": {
        "type": "array",
        "items": {"type": "string"},
        "description": "対象記憶IDリスト（batch_delete, change_domain時）"
      },
      "new_domain": {
        "type": "string",
        "enum": ["global", "user", "project", "session"],
        "description": "変更先ドメイン（change_domain時必須）"
      },
      "target_domain": {
        "type": "string",
        "enum": ["global", "user", "project", "session"],
        "description": "対象ドメイン（stats, cleanup時）"
      },
      "project_id": {
        "type": "string",
        "description": "プロジェクトID"
      },
      "session_id": {
        "type": "string",
        "description": "セッションID"
      },
      "export_format": {
        "type": "string",
        "enum": ["json", "csv", "markdown"],
        "default": "json",
        "description": "エクスポート形式"
      },
      "import_data": {
        "type": "string",
        "description": "インポートするデータ（JSON文字列）"
      },
      "cleanup_before": {
        "type": "string",
        "format": "date-time",
        "description": "この日時より前のセッション記憶を削除"
      }
    },
    "required": ["action"]
  }
}
```

#### 2.1.3 高度な検索 (search)
```json
{
  "name": "search",
  "description": "高度な検索機能（タグ、時間範囲、複合条件）",
  "inputSchema": {
    "type": "object",
    "properties": {
      "type": {
        "type": "string",
        "enum": ["semantic", "tags", "timerange", "advanced", "similar"],
        "description": "検索タイプ"
      },
      "query": {
        "type": "string",
        "description": "検索クエリ（semantic, advanced時）"
      },
      "tags": {
        "type": "array",
        "items": {"type": "string"},
        "description": "検索対象タグ（tags時必須）"
      },
      "start_time": {
        "type": "string",
        "format": "date-time",
        "description": "開始時間（timerange時）"
      },
      "end_time": {
        "type": "string",
        "format": "date-time",
        "description": "終了時間（timerange時）"
      },
      "memory_id": {
        "type": "string",
        "description": "類似検索の基準記憶ID（similar時必須）"
      },
      "filters": {
        "type": "object",
        "properties": {
          "domains": {
            "type": "array",
            "items": {"type": "string"}
          },
          "categories": {
            "type": "array",
            "items": {"type": "string"}
          },
          "importance_min": {"type": "number"},
          "importance_max": {"type": "number"},
          "project_ids": {
            "type": "array",
            "items": {"type": "string"}
          }
        },
        "description": "検索フィルター（advanced時）"
      },
      "limit": {
        "type": "number",
        "default": 10,
        "description": "取得する記憶の最大数"
      },
      "threshold": {
        "type": "number",
        "default": 0.7,
        "description": "類似度の閾値"
      }
    },
    "required": ["type"]
  }
}
```

#### 2.1.4 プロジェクト管理 (project)
```json
{
  "name": "project",
  "description": "プロジェクトの作成・管理・メンバー操作",
  "inputSchema": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "enum": ["create", "list", "get", "add_member", "remove_member", "update", "delete"],
        "description": "実行するアクション"
      },
      "project_id": {
        "type": "string",
        "description": "プロジェクトID（create以外で必須）"
      },
      "name": {
        "type": "string",
        "description": "プロジェクト名（create, update時）"
      },
      "description": {
        "type": "string",
        "description": "プロジェクトの説明（create, update時）"
      },
      "user_id": {
        "type": "string",
        "description": "操作対象ユーザーID（add_member, remove_member時必須）"
      },
      "role": {
        "type": "string",
        "enum": ["editor", "viewer"],
        "description": "ロール（add_member時必須）"
      },
      "role_filter": {
        "type": "string",
        "enum": ["editor", "viewer"],
        "description": "特定のロールでフィルタリング（list時）"
      }
    },
    "required": ["action"]
  }
}
```

#### 2.1.5 ユーザー・セッション管理 (user)
```json
{
  "name": "user",
  "description": "ユーザー情報とセッション管理",
  "inputSchema": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "enum": ["get_current", "get_projects", "get_sessions", "create_session", "switch_session", "end_session"],
        "description": "実行するアクション"
      },
      "session_name": {
        "type": "string",
        "description": "セッション名（create_session時）"
      },
      "session_id": {
        "type": "string",
        "description": "セッションID（switch_session, end_session時必須）"
      },
      "include_stats": {
        "type": "boolean",
        "default": false,
        "description": "統計情報も含めるか（get_current, get_projects時）"
      }
    },
    "required": ["action"]
  }
}
```

#### 2.1.6 可視化・分析 (visualize)
```json
{
  "name": "visualize",
  "description": "記憶の可視化と分析機能",
  "inputSchema": {
    "type": "object",
    "properties": {
      "type": {
        "type": "string",
        "enum": ["memory_map", "stats_dashboard", "domain_graph", "timeline", "category_chart"],
        "description": "可視化タイプ"
      },
      "target_domain": {
        "type": "string",
        "enum": ["global", "user", "project", "session"],
        "description": "対象ドメイン"
      },
      "project_id": {
        "type": "string",
        "description": "プロジェクトID"
      },
      "session_id": {
        "type": "string",
        "description": "セッションID"
      },
      "center_memory_id": {
        "type": "string",
        "description": "中心記憶ID（memory_map時）"
      },
      "depth": {
        "type": "number",
        "default": 2,
        "description": "表示する関連性の深度"
      },
      "format": {
        "type": "string",
        "enum": ["html", "svg", "json", "graphviz"],
        "default": "html",
        "description": "出力形式"
      },
      "time_range": {
        "type": "object",
        "properties": {
          "start": {"type": "string", "format": "date-time"},
          "end": {"type": "string", "format": "date-time"}
        },
        "description": "時間範囲（timeline時）"
      }
    },
    "required": ["type"]
  }
}
```

#### 2.1.7 システム管理 (admin)
```json
{
  "name": "admin",
  "description": "システム管理・設定・メンテナンス機能",
  "inputSchema": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "enum": ["health_check", "system_stats", "backup", "restore", "reindex", "cleanup_orphans", "migrate_domain"],
        "description": "実行するアクション"
      },
      "backup_path": {
        "type": "string",
        "description": "バックアップファイルパス（backup, restore時）"
      },
      "include_data": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["memories", "projects", "sessions", "associations"]
        },
        "description": "バックアップ対象データ"
      },
      "migration_config": {
        "type": "object",
        "properties": {
          "source_domain": {"type": "string"},
          "target_domain": {"type": "string"},
          "filter_criteria": {"type": "object"}
        },
        "description": "ドメイン移行設定（migrate_domain時）"
      },
      "force": {
        "type": "boolean",
        "default": false,
        "description": "強制実行フラグ"
      }
    },
    "required": ["action"]
  }
}
```

### 2.2 ツール構成概要

本MCPサーバーは以下の**7つのメインツール**で全機能を提供します：

1. **`memory`** - 基本的な記憶操作（保存・検索・取得・更新・削除）
2. **`memory_manage`** - 記憶管理・統計・バッチ操作・ドメイン変更
3. **`search`** - 高度な検索（タグ・時間・複合条件・類似検索）
4. **`project`** - プロジェクト管理・メンバー操作
5. **`user`** - ユーザー情報・セッション管理
6. **`visualize`** - 可視化・分析機能
7. **`admin`** - システム管理・メンテナンス

各ツールは`action`または`type`パラメータでサブコマンドを指定し、関連機能をグループ化することで名前空間を効率的に利用します。

### 2.3 使用例

#### 基本的な記憶操作
```javascript
// 記憶の保存
await memory({action: "store", content: "TypeScriptの型安全性について", domain: "user", tags: ["programming", "typescript"]})

// 記憶の検索
await memory({action: "search", query: "TypeScript", include_domains: ["user", "global"]})

// 記憶の更新
await memory({action: "update", memory_id: "mem_123", content: "更新された内容", tags: ["updated"]})
```

#### ユーザー・セッション管理
```javascript
// 現在のユーザー情報取得
await user({action: "get_current", include_stats: true})

// セッション作成・切り替え
await user({action: "create_session", session_name: "開発セッション2024"})
await user({action: "switch_session", session_id: "sess_456"})

// ユーザーのプロジェクト一覧
await user({action: "get_projects"})
```

#### プロジェクト管理
```javascript
// プロジェクト作成
await project({action: "create", name: "AIプロジェクト", description: "機械学習研究"})

// メンバー追加
await project({action: "add_member", project_id: "proj_789", user_id: "user_123", role: "editor"})
```

#### 記憶管理・統計
```javascript
// 記憶統計取得
await memory_manage({action: "stats", target_domain: "user"})

// ドメイン変更
await memory_manage({action: "change_domain", memory_ids: ["mem_123", "mem_456"], new_domain: "project", project_id: "proj_789"})

// セッション記憶のクリーンアップ
await memory_manage({action: "cleanup", target_domain: "session", cleanup_before: "2024-01-01T00:00:00Z"})
```

#### 高度な検索
```javascript
// タグ検索
await search({type: "tags", tags: ["programming", "typescript"]})

// 時間範囲検索
await search({type: "timerange", start_time: "2024-01-01T00:00:00Z", end_time: "2024-12-31T23:59:59Z"})

// 複合条件検索
await search({
  type: "advanced", 
  query: "機械学習",
  filters: {
    domains: ["user", "project"],
    categories: ["research"],
    importance_min: 0.7
  }
})
```

#### 可視化
```javascript
// 記憶マップ生成
await visualize({type: "memory_map", center_memory_id: "mem_123", depth: 3, format: "html"})

// 統計ダッシュボード
await visualize({type: "stats_dashboard", target_domain: "project", project_id: "proj_789"})
```

## 3. 技術仕様

```python
from enum import Enum
from typing import Optional

class MemoryDomain(Enum):
    GLOBAL = "global"    # 全ユーザー参照可能
    USER = "user"        # ユーザー個人専用
    PROJECT = "project"  # プロジェクト参加者
    SESSION = "session"  # セッション内限定

class ProjectRole(Enum):
    EDITOR = "editor"    # 読み書き可能
    VIEWER = "viewer"    # 読み取りのみ

class Memory:
    id: str                    # UUID
    content: str              # 記憶内容
    embedding: List[float]    # ベクトル埋め込み
    tags: List[str]          # タグリスト
    category: str            # カテゴリ
    importance: float        # 重要度 (0-1)
    created_at: datetime     # 作成日時
    updated_at: datetime     # 更新日時
    access_count: int        # アクセス回数
    metadata: Dict[str, Any] # 追加メタデータ
    
    # ドメイン関連フィールド
    domain: MemoryDomain     # 記憶ドメイン
    user_id: Optional[str]   # ユーザーID（userドメイン用）
    project_id: Optional[str] # プロジェクトID（projectドメイン用）
    session_id: Optional[str] # セッションID（sessionドメイン用）
    author_id: str           # 作成者ID
    expires_at: Optional[datetime] # 有効期限（sessionドメイン用）
```

### 3.2 関連性データ構造

```python
class Association:
    from_memory_id: str      # 関連元記憶ID
    to_memory_id: str        # 関連先記憶ID
    strength: float          # 関連強度 (0-1)
    type: str               # 関連タイプ (semantic, temporal, manual)
    created_at: datetime     # 作成日時
```

### 3.3 埋め込みモデル

#### 3.3.1 デフォルト: OpenAI Embeddings
- モデル: `text-embedding-3-small` (1536次元)
- 料金効率とパフォーマンスのバランス

#### 3.3.2 代替: Sentence Transformers
- モデル: `all-MiniLM-L6-v2` (384次元)
- ローカル実行可能

### 3.4 データベース設計

#### 3.4.1 Vector Store (Chroma)
```
Collection: memories
- Documents: memory.content
- Embeddings: memory.embedding
- Metadata: {id, tags, category, importance, created_at}
```

#### 3.4.2 Metadata Store (SQLite)
```sql
-- 記憶テーブル
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    tags TEXT,  -- JSON array
    category TEXT,
    importance REAL DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    metadata TEXT  -- JSON object
);

-- 関連性テーブル
CREATE TABLE associations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_memory_id TEXT NOT NULL,
    to_memory_id TEXT NOT NULL,
    strength REAL NOT NULL,
    type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_memory_id) REFERENCES memories(id),
    FOREIGN KEY (to_memory_id) REFERENCES memories(id)
);

-- インデックス
CREATE INDEX idx_memories_category ON memories(category);
CREATE INDEX idx_memories_created_at ON memories(created_at);
CREATE INDEX idx_associations_from ON associations(from_memory_id);
CREATE INDEX idx_associations_to ON associations(to_memory_id);
```

## 4. 通信方式要件

### 4.1 サポートする通信方式

#### 4.1.1 STDIO (Standard Input/Output)
**用途**: デスクトップアプリケーション、IDE拡張
**特徴**:
- JSON-RPC 2.0 over stdin/stdout
- プロセス間通信
- Claude Desktop、VS Code拡張での標準方式
- 軽量で高速

**起動方法**:
```bash
mcp-assoc-memory --transport stdio
```

#### 4.1.2 HTTP (RESTful API)
**用途**: Webアプリケーション、マイクロサービス
**特徴**:
- JSON-RPC 2.0 over HTTP POST
- ステートレス通信
- 複数クライアント対応
- デバッグしやすい

**起動方法**:
```bash
mcp-assoc-memory --transport http --port 8000
```

**エンドポイント**:
- `POST /mcp` - JSON-RPC リクエスト
- `GET /health` - ヘルスチェック
- `GET /metrics` - メトリクス（Prometheus形式）

#### 4.1.3 SSE (Server-Sent Events)
**用途**: リアルタイムWebアプリケーション
**特徴**:
- JSON-RPC 2.0 over WebSocket
- 双方向リアルタイム通信
- ブラウザからの直接利用
- プッシュ通知対応

**起動方法**:
```bash
mcp-assoc-memory --transport sse --port 8001
```

**エンドポイント**:
- `GET /sse` - SSE接続確立
- `POST /sse` - JSON-RPCリクエスト送信

### 4.2 マルチトランスポート対応

#### 4.2.1 同時起動
複数の通信方式を同時に起動可能：
```bash
mcp-assoc-memory --transport stdio,http,sse --http-port 8000 --sse-port 8001
```

#### 4.2.2 設定ファイルでの指定
```json
{
  "transports": {
    "stdio": {
      "enabled": true
    },
    "http": {
      "enabled": true,
      "port": 8000,
      "host": "localhost",
      "cors": {
        "allowed_origins": ["http://localhost:3000"],
        "allowed_methods": ["GET", "POST", "OPTIONS"]
      }
    },
    "sse": {
      "enabled": true,
      "port": 8001,
      "host": "localhost",
      "max_connections": 100,
      "heartbeat_interval": 30
    }
  }
}
```

## 5. 非機能要件

### 5.1 パフォーマンス
- **STDIO**: 記憶保存 < 500ms, 検索応答 < 200ms
- **HTTP**: 記憶保存 < 600ms, 検索応答 < 300ms（ネットワークオーバーヘッド含む）
- **SSE**: 記憶保存 < 800ms, 検索応答 < 400ms（双方向通信オーバーヘッド含む）
- 同時接続: STDIO 1クライアント, HTTP 50クライアント, SSE 100クライアント

### 5.2 スケーラビリティ
- 記憶数: 100,000件まで
- 埋め込み次元: 最大2048次元
- ディスク使用量: < 10GB
- 水平スケーリング: HTTP/SSEでのロードバランサー対応

### 5.3 信頼性
- データ整合性: ACID準拠
- バックアップ: 自動日次バックアップ
- エラー処理: グレースフルな例外処理
- 接続復旧: SSEでの自動再接続機能

## 6. セキュリティ

### 6.1 データ保護
- 記憶内容の暗号化オプション
- アクセス制御機能
- プライバシー設定

### 6.2 API セキュリティ
#### 6.2.1 STDIO
- プロセス分離による安全性
- ローカルアクセスのみ

#### 6.2.2 HTTP
- HTTPS対応（TLS 1.3）
- API キー認証
- JWT トークン認証（オプション）
- CORS設定
- レート制限（IP/ユーザー別）
- 入力値検証

#### 6.2.3 SSE
- WebSocket Secure (WSS)
- Origin検証
- セッション管理
- 接続制限
- ハートビート監視

### 6.3 認証・認可
```json
{
  "authentication": {
    "stdio": {
      "type": "none"
    },
    "http": {
      "type": "api_key",
      "header": "X-API-Key",
      "jwt_secret": "${JWT_SECRET}"
    },
    "sse": {
      "type": "session",
      "timeout": 3600
    }
  }
}
```

## 7. 拡張機能 (将来実装)

### 7.1 高度な連想機能
- 時系列パターン学習
- 感情分析による記憶分類
- マルチモーダル記憶 (画像、音声)

### 7.2 分散機能
- 複数ノードでの記憶共有
- クラウドストレージ連携
- リアルタイム同期

### 7.3 AI強化機能
- 自動要約機能
- 記憶の重要度自動判定
- 記憶間の新しい関連性発見

### 7.4 通信方式拡張
- GraphQL over HTTP
- gRPC サポート
- WebRTC P2P通信
- MQTT IoTデバイス連携
