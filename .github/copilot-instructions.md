# GitHub Copilot Development Instructions

## プロジェクト概要
LLM向け連想記憶MCPサーバ - 記憶ドメイン（グローバル/ユーザ/プロジェクト/セッション）を考慮した知識管理システム

## 技術スタック
- **言語**: TypeScript
- **ランタイム**: Node.js
- **データベース**: SQLite (開発), PostgreSQL (本番)
- **MCPプロトコル**: STDIO, HTTP, SSE対応
- **テスト**: Jest
- **パッケージマネージャー**: npm

## コーディング規約

### 1. TypeScript規約
```typescript
// 型定義は厳密に
interface MemoryRecord {
  id: string;
  domain: MemoryDomain;
  content: string;
  metadata: Record<string, unknown>;
  createdAt: Date;
  updatedAt: Date;
}

// 関数は型安全に
async function storeMemory(
  domain: MemoryDomain,
  content: string,
  metadata?: Record<string, unknown>
): Promise<MemoryRecord> {
  // 実装
}
```

### 2. ファイル命名規則
- **インターフェース**: `types/`ディレクトリに配置
- **実装クラス**: PascalCase (例: `MemoryManager.ts`)
- **ユーティリティ**: `utils/`ディレクトリ、camelCase
- **テスト**: `*.test.ts`

### 3. インポート順序
```typescript
// 1. Node.js標準モジュール
import { readFile } from 'fs/promises';

// 2. 外部ライブラリ
import express from 'express';
import { Database } from 'sqlite3';

// 3. 内部モジュール（絶対パス）
import { MemoryDomain } from '@/types/memory';
import { Logger } from '@/utils/logger';

// 4. 相対パス
import './types';
```

## アーキテクチャガイドライン

### 1. レイヤー分離
```
src/
├── transport/     # STDIO/HTTP/SSE層
├── core/          # ビジネスロジック
├── storage/       # データ永続化層
├── types/         # 型定義
└── utils/         # ユーティリティ
```

### 2. 記憶ドメイン設計
```typescript
enum MemoryDomain {
  GLOBAL = 'global',     // システム全体
  USER = 'user',         // ユーザー固有
  PROJECT = 'project',   // プロジェクト固有
  SESSION = 'session'    // セッション固有
}

// ドメイン固有のストレージ戦略
interface DomainStorage {
  store(domain: MemoryDomain, key: string, value: unknown): Promise<void>;
  retrieve(domain: MemoryDomain, key: string): Promise<unknown>;
  search(domain: MemoryDomain, query: string): Promise<MemoryRecord[]>;
}
```

### 3. トランスポート抽象化
```typescript
interface TransportServer {
  start(): Promise<void>;
  stop(): Promise<void>;
  onRequest(handler: RequestHandler): void;
}

// 各トランスポートで統一インターフェース実装
class StdioTransport implements TransportServer { /* */ }
class HttpTransport implements TransportServer { /* */ }
class SseTransport implements TransportServer { /* */ }
```

## エラーハンドリング

### 1. カスタムエラークラス
```typescript
export class MemoryError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly domain?: MemoryDomain
  ) {
    super(message);
    this.name = 'MemoryError';
  }
}

export class ValidationError extends MemoryError {
  constructor(field: string, value: unknown) {
    super(`Invalid value for ${field}: ${value}`, 'VALIDATION_ERROR');
  }
}
```

### 2. エラーレスポンス統一
```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
```

## テスト戦略

### 1. テストファイル構成
```
tests/
├── unit/          # 単体テスト
├── integration/   # 統合テスト
├── e2e/          # E2Eテスト
└── fixtures/     # テストデータ
```

### 2. テストパターン
```typescript
describe('MemoryManager', () => {
  let memoryManager: MemoryManager;
  
  beforeEach(async () => {
    memoryManager = new MemoryManager(':memory:');
    await memoryManager.initialize();
  });

  afterEach(async () => {
    await memoryManager.close();
  });

  describe('storeMemory', () => {
    it('should store memory with correct domain', async () => {
      const record = await memoryManager.storeMemory(
        MemoryDomain.USER,
        'test content',
        { tag: 'test' }
      );
      
      expect(record.domain).toBe(MemoryDomain.USER);
      expect(record.content).toBe('test content');
    });
  });
});
```

## ログ戦略

### 1. 構造化ログ
```typescript
interface LogEntry {
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  domain?: MemoryDomain;
  metadata?: Record<string, unknown>;
}

// 使用例
logger.info('Memory stored', {
  domain: MemoryDomain.USER,
  recordId: record.id,
  contentLength: content.length
});
```

### 2. パフォーマンス測定
```typescript
const timer = logger.startTimer();
await heavyOperation();
timer.done({ message: 'Heavy operation completed' });
```

## セキュリティ考慮事項

### 1. 入力検証
```typescript
import Joi from 'joi';

const storeMemorySchema = Joi.object({
  domain: Joi.string().valid(...Object.values(MemoryDomain)).required(),
  content: Joi.string().max(10000).required(),
  metadata: Joi.object().unknown(true).optional()
});
```

### 2. 認証・認可
```typescript
interface AuthContext {
  userId?: string;
  projectId?: string;
  permissions: string[];
}

function authorize(domain: MemoryDomain, action: string, context: AuthContext): boolean {
  // ドメイン固有の認可ロジック
}
```

## パフォーマンス最適化

### 1. インデックス戦略
```sql
-- 記憶検索の最適化
CREATE INDEX idx_memory_domain_content ON memories(domain, content_vector);
CREATE INDEX idx_memory_tags ON memory_tags(tag, memory_id);
```

### 2. キャッシュ戦略
```typescript
interface CacheStrategy {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T, ttl?: number): Promise<void>;
  invalidate(pattern: string): Promise<void>;
}
```

## MCP仕様準拠

### 1. ツール定義
```typescript
const tools: Tool[] = [
  {
    name: 'store_memory',
    description: 'Store information in associative memory',
    inputSchema: {
      type: 'object',
      properties: {
        domain: { type: 'string', enum: Object.values(MemoryDomain) },
        content: { type: 'string' },
        metadata: { type: 'object' }
      },
      required: ['domain', 'content']
    }
  }
];
```

### 2. リソース定義
```typescript
const resources: Resource[] = [
  {
    uri: 'memory://domain/{domain}',
    name: 'Memory Domain',
    description: 'Access memories in specific domain',
    mimeType: 'application/json'
  }
];
```

## デバッグ支援

### 1. 開発時設定
```typescript
if (process.env.NODE_ENV === 'development') {
  // 詳細ログ有効化
  logger.level = 'debug';
  
  // クエリログ出力
  database.on('query', (sql, params) => {
    logger.debug('SQL Query', { sql, params });
  });
}
```

### 2. ヘルスチェック
```typescript
app.get('/health', async (req, res) => {
  const health = {
    status: 'ok',
    timestamp: new Date().toISOString(),
    database: await checkDatabaseHealth(),
    memory: process.memoryUsage()
  };
  res.json(health);
});
```

## CI/CD対応

### 1. GitHub Actions設定例
```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run lint
      - run: npm test
      - run: npm run build
```

### 2. 品質ゲート
- TypeScript厳密モード必須
- テストカバレッジ80%以上
- ESLint警告ゼロ
- セキュリティ脆弱性ゼロ

## 開発フロー

📋 **[実装計画・チェックリスト](../IMPLEMENTATION_PLAN.md)** - 段階的実装計画と進捗管理

1. **機能開発**
   - feature/記述的な名前でブランチ作成
   - 型定義から実装
   - テスト駆動開発

2. **PR作成**
   - 変更内容の明確な説明
   - テスト結果の添付
   - レビュー項目のチェックリスト

3. **デプロイ**
   - ステージング環境での動作確認
   - 本番デプロイはmainブランチから自動化

### 実装フェーズ

本プロジェクトは4つのフェーズで実装します：

1. **Phase 1: 基盤構築** (2週間) - プロジェクト構造・基本データモデル
2. **Phase 2: コア機能** (3週間) - 記憶操作・ドメイン管理・認証
3. **Phase 3: 高度機能** (2週間) - MCPツール・トランスポート・可視化
4. **Phase 4: 統合・最適化** (1週間) - パフォーマンス・監視・ドキュメント

各フェーズの詳細なチェックリストは[実装計画書](../IMPLEMENTATION_PLAN.md)を参照してください。

## 参考資料
- [MCP仕様書](https://spec.modelcontextprotocol.io/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Node.js Best Practices](https://github.com/goldbergyoni/nodebestpractices)
