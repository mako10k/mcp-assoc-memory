# 記憶ドメイン仕様書

## 1. 記憶ドメイン概要

記憶ドメインは、連想記憶システムにおけるアクセス制御とデータ分離の仕組みです。異なるスコープでの記憶共有を可能にし、プライバシー保護とコラボレーションを両立させます。

## 2. ドメイン定義

### 2.1 グローバルドメイン (Global)
**スコープ**: すべての利用者が参照可能
**アクセス権限**:
- 書き込み: 管理者のみ
- 読み取り: 全ユーザー

**用途**:
- 共通知識ベース
- FAQ・ドキュメント
- ベストプラクティス
- 組織の公式情報

**例**:
```json
{
  "domain": "global",
  "content": "Pythonでのエラーハンドリングは try-except 文を使用します",
  "category": "programming-knowledge",
  "tags": ["python", "error-handling", "best-practice"]
}
```

### 2.2 ユーザードメイン (User)
**スコープ**: 利用者個人専用
**アクセス権限**:
- 書き込み: 本人のみ
- 読み取り: 本人のみ

**用途**:
- 個人的な学習メモ
- プライベートな考察
- 個人設定・好み
- 機密情報

**例**:
```json
{
  "domain": "user",
  "user_id": "user123",
  "content": "昨日学んだReactのuseEffectフックについて復習が必要",
  "category": "personal-learning",
  "tags": ["react", "hooks", "todo"]
}
```

### 2.3 プロジェクトドメイン (Project)
**スコープ**: プロジェクト参加者が参照可能
**アクセス権限**:
- 書き込み: Editor権限を持つ参加者
- 読み取り: すべての参加者（Editor + Viewer）

**用途**:
- プロジェクト固有の知識
- チーム内での情報共有
- 作業履歴・議事録
- 設計決定事項

**例**:
```json
{
  "domain": "project",
  "project_id": "proj-ecommerce-2024",
  "content": "ユーザー認証にはJWT + Refresh Tokenパターンを採用することに決定",
  "category": "architecture-decision",
  "tags": ["authentication", "jwt", "security"],
  "author": "user123"
}
```

### 2.4 セッションドメイン (Session)
**スコープ**: 会話セッション内でのみ参照可能
**アクセス権限**:
- 書き込み: セッション参加者
- 読み取り: セッション参加者
- 自動削除: セッション終了時

**用途**:
- 会話の文脈保持
- 一時的な作業メモ
- セッション固有の仮説
- 短期記憶の役割

**例**:
```json
{
  "domain": "session",
  "session_id": "sess-20240706-001",
  "content": "このAPIエンドポイントのレスポンス時間を改善する必要がある",
  "category": "session-context",
  "tags": ["performance", "api", "investigation"],
  "expires_at": "2024-07-06T23:59:59Z"
}
```

## 3. 権限マトリックス

| ドメイン | 作成 | 読み取り | 更新 | 削除 | 検索対象 |
|---------|-----|---------|-----|-----|---------|
| **Global** | 管理者 | 全ユーザー | 管理者 | 管理者 | デフォルト有効 |
| **User** | 本人 | 本人 | 本人 | 本人 | デフォルト有効 |
| **Project** | Editor | 参加者 | Editor | Editor+Author | オプション |
| **Session** | 参加者 | 参加者 | 参加者 | 参加者+自動 | オプション |

## 4. データモデル拡張

### 4.1 記憶モデルの拡張

```python
from enum import Enum
from typing import Optional, List

class MemoryDomain(Enum):
    GLOBAL = "global"
    USER = "user"
    PROJECT = "project"
    SESSION = "session"

class ProjectRole(Enum):
    EDITOR = "editor"    # 読み書き可能
    VIEWER = "viewer"    # 読み取りのみ

@dataclass
class MemoryAccess:
    """記憶アクセス制御情報"""
    domain: MemoryDomain
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    author_id: Optional[str] = None

@dataclass
class Memory:
    # ...existing fields...
    access: MemoryAccess
    
    def can_read(self, user_id: str, user_projects: Dict[str, ProjectRole], 
                 session_id: Optional[str] = None) -> bool:
        """読み取り権限をチェック"""
        if self.access.domain == MemoryDomain.GLOBAL:
            return True
        elif self.access.domain == MemoryDomain.USER:
            return self.access.user_id == user_id
        elif self.access.domain == MemoryDomain.PROJECT:
            return self.access.project_id in user_projects
        elif self.access.domain == MemoryDomain.SESSION:
            return self.access.session_id == session_id
        return False
    
    def can_write(self, user_id: str, user_projects: Dict[str, ProjectRole], 
                  is_admin: bool = False) -> bool:
        """書き込み権限をチェック"""
        if self.access.domain == MemoryDomain.GLOBAL:
            return is_admin
        elif self.access.domain == MemoryDomain.USER:
            return self.access.user_id == user_id
        elif self.access.domain == MemoryDomain.PROJECT:
            project_role = user_projects.get(self.access.project_id)
            return project_role == ProjectRole.EDITOR
        elif self.access.domain == MemoryDomain.SESSION:
            return True  # セッション参加者は全員書き込み可能
        return False
```

### 4.2 プロジェクト管理モデル

```python
@dataclass
class Project:
    id: str
    name: str
    description: str
    owner_id: str
    created_at: datetime
    members: Dict[str, ProjectRole]  # user_id -> role
    
    def add_member(self, user_id: str, role: ProjectRole):
        """メンバーを追加"""
        self.members[user_id] = role
    
    def remove_member(self, user_id: str):
        """メンバーを削除"""
        if user_id in self.members:
            del self.members[user_id]
    
    def get_member_role(self, user_id: str) -> Optional[ProjectRole]:
        """メンバーの権限を取得"""
        return self.members.get(user_id)
```

## 5. 技術実装戦略

### 5.1 段階的実装アプローチ

#### Phase 1: プロジェクトドメイン基盤
```python
class ProjectBasedMemoryManager:
    """プロジェクトベースの記憶管理（基盤実装）"""
    
    def __init__(self):
        self.default_project_id = "global"  # グローバルドメイン用
        self.user_project_prefix = "user-"   # ユーザードメイン用
        self.session_project_prefix = "session-"  # セッションドメイン用
    
    async def store_memory(self, content: str, domain: MemoryDomain, 
                          user_id: str, **kwargs) -> Memory:
        """ドメインに応じた記憶保存"""
        project_id = self._resolve_project_id(domain, user_id, kwargs)
        
        access = MemoryAccess(
            domain=domain,
            user_id=user_id if domain == MemoryDomain.USER else None,
            project_id=project_id,
            session_id=kwargs.get('session_id'),
            author_id=user_id
        )
        
        memory = Memory(content=content, access=access, **kwargs)
        return await self._store_memory_with_access_control(memory)
    
    def _resolve_project_id(self, domain: MemoryDomain, user_id: str, 
                           kwargs: Dict) -> str:
        """ドメインに応じたプロジェクトIDを解決"""
        if domain == MemoryDomain.GLOBAL:
            return self.default_project_id
        elif domain == MemoryDomain.USER:
            return f"{self.user_project_prefix}{user_id}"
        elif domain == MemoryDomain.PROJECT:
            return kwargs['project_id']
        elif domain == MemoryDomain.SESSION:
            return f"{self.session_project_prefix}{kwargs['session_id']}"
        raise ValueError(f"Unknown domain: {domain}")
```

#### Phase 2: 本格的なマルチドメイン実装
```python
class MultiDomainMemoryManager:
    """本格的なマルチドメイン記憶管理"""
    
    def __init__(self):
        self.project_manager = ProjectManager()
        self.session_manager = SessionManager()
        self.access_controller = AccessController()
    
    async def search_memories(self, query: str, user_id: str, 
                             session_id: Optional[str] = None,
                             include_domains: List[MemoryDomain] = None) -> List[Memory]:
        """ドメインを考慮した記憶検索"""
        
        # ユーザーのアクセス可能なプロジェクト取得
        user_projects = await self.project_manager.get_user_projects(user_id)
        
        # 検索対象ドメインの決定
        if include_domains is None:
            include_domains = [MemoryDomain.GLOBAL, MemoryDomain.USER]
        
        # ドメインごとに検索実行
        all_memories = []
        for domain in include_domains:
            domain_memories = await self._search_in_domain(
                query, domain, user_id, user_projects, session_id
            )
            all_memories.extend(domain_memories)
        
        # アクセス権限でフィルタリング
        accessible_memories = [
            memory for memory in all_memories
            if memory.can_read(user_id, user_projects, session_id)
        ]
        
        return accessible_memories
```

### 5.2 データベース設計

#### SQLite テーブル拡張
```sql
-- プロジェクトテーブル
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    owner_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- プロジェクトメンバーテーブル
CREATE TABLE project_members (
    project_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL, -- 'editor' or 'viewer'
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, user_id),
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- 記憶テーブル拡張
ALTER TABLE memories ADD COLUMN domain TEXT NOT NULL DEFAULT 'user';
ALTER TABLE memories ADD COLUMN user_id TEXT;
ALTER TABLE memories ADD COLUMN project_id TEXT;
ALTER TABLE memories ADD COLUMN session_id TEXT;
ALTER TABLE memories ADD COLUMN expires_at TIMESTAMP;
ALTER TABLE memories ADD COLUMN author_id TEXT;

-- インデックス追加
CREATE INDEX idx_memories_domain ON memories(domain);
CREATE INDEX idx_memories_user_id ON memories(user_id);
CREATE INDEX idx_memories_project_id ON memories(project_id);
CREATE INDEX idx_memories_session_id ON memories(session_id);
CREATE INDEX idx_memories_expires_at ON memories(expires_at);
```

## 6. MCPツール拡張

### 6.1 新しいツール定義

```json
{
  "name": "store_memory_with_domain",
  "description": "指定されたドメインに記憶を保存する",
  "inputSchema": {
    "type": "object",
    "properties": {
      "content": {"type": "string", "description": "記憶する内容"},
      "domain": {
        "type": "string", 
        "enum": ["global", "user", "project", "session"],
        "description": "記憶ドメイン"
      },
      "project_id": {
        "type": "string",
        "description": "プロジェクトドメインの場合のプロジェクトID"
      },
      "session_id": {
        "type": "string", 
        "description": "セッションドメインの場合のセッションID"
      },
      "tags": {
        "type": "array",
        "items": {"type": "string"},
        "description": "タグ"
      },
      "category": {"type": "string", "description": "カテゴリ"},
      "importance": {"type": "number", "description": "重要度"}
    },
    "required": ["content", "domain"]
  }
}
```

```json
{
  "name": "search_memories_with_domain",
  "description": "指定されたドメインから記憶を検索する",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "検索クエリ"},
      "include_domains": {
        "type": "array",
        "items": {
          "type": "string",
          "enum": ["global", "user", "project", "session"]
        },
        "description": "検索対象ドメインリスト"
      },
      "project_ids": {
        "type": "array",
        "items": {"type": "string"},
        "description": "検索対象プロジェクトIDリスト"
      },
      "limit": {"type": "number", "default": 10},
      "threshold": {"type": "number", "default": 0.7}
    },
    "required": ["query"]
  }
}
```

### 6.2 プロジェクト管理ツール

```json
{
  "name": "create_project",
  "description": "新しいプロジェクトを作成する",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {"type": "string", "description": "プロジェクト名"},
      "description": {"type": "string", "description": "プロジェクト説明"}
    },
    "required": ["name"]
  }
}
```

```json
{
  "name": "add_project_member",
  "description": "プロジェクトにメンバーを追加する",
  "inputSchema": {
    "type": "object", 
    "properties": {
      "project_id": {"type": "string", "description": "プロジェクトID"},
      "user_id": {"type": "string", "description": "ユーザーID"},
      "role": {
        "type": "string",
        "enum": ["editor", "viewer"],
        "description": "権限ロール"
      }
    },
    "required": ["project_id", "user_id", "role"]
  }
}
```

## 7. セキュリティ考慮事項

### 7.1 プライバシー保護
- **完全なデータ分離**: ユーザードメインは他ユーザーから完全に分離
- **暗号化**: 機密データの暗号化保存
- **アクセスログ**: すべてのアクセスをログ記録

### 7.2 権限管理
- **最小権限原則**: 必要最小限の権限のみ付与
- **権限の継承なし**: ドメイン間での権限継承を禁止
- **定期的な権限レビュー**: プロジェクトメンバーの定期確認

### 7.3 データ保護
- **自動削除**: セッションドメインの自動削除
- **バックアップ制御**: ドメインに応じたバックアップ戦略
- **匿名化**: 統計データでの個人情報除去

## 8. 運用での実現方法

### 8.1 プロジェクトベース実装での各ドメイン実現

```python
# 運用設定例
DOMAIN_CONFIG = {
    "global": {
        "project_id": "global-knowledge",
        "admin_users": ["admin1", "admin2"],
        "public_read": True
    },
    "user_template": {
        "project_id_pattern": "user-{user_id}",
        "auto_create": True,
        "single_member": True
    },
    "session_template": {
        "project_id_pattern": "session-{session_id}",
        "auto_create": True,
        "auto_cleanup": True,
        "ttl_hours": 24
    }
}
```

### 8.2 段階的移行戦略

1. **Phase 1**: プロジェクトドメインのみ実装
2. **Phase 2**: 設定による疑似ドメイン実現
3. **Phase 3**: 本格的なマルチドメイン実装
4. **Phase 4**: 高度な権限管理・監査機能

この記憶ドメイン設計により、LLMの連想記憶システムがエンタープライズ環境でも安全に利用できるようになります。
