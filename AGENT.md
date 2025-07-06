# MCP連想記憶サーバ - AI開発エージェント向けドキュメント

## プロジェクト概要

このプロジェクトは、LLM向けの連想記憶MCPサーバです。記憶ドメイン（グローバル/ユーザ/プロジェクト/セッション）を考慮した知識管理システムを提供し、STDIO、HTTP、SSEの3つのトランスポート方式に対応しています。

## AI開発エージェント向け情報

### 開発ガイドライン

このプロジェクトの開発では、以下のガイドラインに従ってください：

📋 **[GitHub Copilot開発ルール](.github/copilot-instructions.md)**
- TypeScript規約
- アーキテクチャガイドライン
- テスト戦略
- セキュリティ考慮事項
- パフォーマンス最適化
- MCP仕様準拠

### プロジェクト構造

詳細なプロジェクト構造については、以下のドキュメントを参照してください：

- **[プロジェクト構造](PROJECT_STRUCTURE.md)** - ディレクトリ構成とファイル配置
- **[仕様書](SPECIFICATION.md)** - API仕様と機能詳細
- **[アーキテクチャ](ARCHITECTURE.md)** - システム設計と構成要素
- **[記憶ドメイン](MEMORY_DOMAINS.md)** - ドメイン設計と管理戦略

### 技術スタック

- **コア技術**: TypeScript, Node.js
- **データベース**: SQLite (開発), PostgreSQL (本番)
- **プロトコル**: Model Context Protocol (MCP)
- **トランスポート**: STDIO, HTTP, SSE
- **テスト**: Jest
- **開発ツール**: ESLint, Prettier, TypeScript

### 主要コンポーネント

1. **Transport Layer** - STDIO/HTTP/SSE対応の通信層
2. **Core Engine** - 連想記憶のコア機能
3. **Storage Layer** - データ永続化とクエリ処理
4. **Domain Manager** - 記憶ドメインの管理
5. **Auth Layer** - 認証と認可の処理

### 記憶ドメイン

| ドメイン | 説明 | 利用シーン |
|---------|------|-----------|
| Global | システム全体の記憶 | 一般知識、定数情報 |
| User | ユーザー固有の記憶 | 個人設定、学習データ |
| Project | プロジェクト固有の記憶 | プロジェクト情報、コード文脈 |
| Session | セッション固有の記憶 | 一時的な会話状態 |

### API設計パターン

```typescript
// サブコマンド方式による統合ツール設計
interface MemoryTool {
  action: 'store' | 'search' | 'get' | 'get_related' | 'update' | 'delete';
  memory_id?: string;
  content?: string;
  query?: string;
  domain?: MemoryDomain;
  // ...その他のパラメータ
}

interface UserTool {
  action: 'get_current' | 'get_projects' | 'get_sessions' | 'create_session' | 'switch_session' | 'end_session';
  session_name?: string;
  session_id?: string;
  include_stats?: boolean;
}

// 7つのメインツールで全機能を提供
const tools = [
  'memory',          // 基本記憶操作
  'memory_manage',   // 記憶管理・統計
  'search',          // 高度検索
  'project',         // プロジェクト管理
  'user',           // ユーザー・セッション管理
  'visualize',      // 可視化・分析
  'admin'           // システム管理
];
```

### 開発時の注意事項

1. **型安全性の確保**
   - 全ての関数とクラスに適切な型注釈
   - 厳密なTypeScript設定の使用

2. **エラーハンドリング**
   - カスタムエラークラスの使用
   - 適切なエラーレスポンスの返却

3. **テスト駆動開発**
   - 機能実装前のテストケース作成
   - 単体・統合・E2Eテストの実装

4. **パフォーマンス考慮**
   - データベースインデックスの最適化
   - キャッシュ戦略の実装

5. **セキュリティ**
   - 入力検証の徹底
   - 認証・認可の適切な実装

### 開発フロー

1. **要件確認** - 仕様書とアーキテクチャドキュメントの確認
2. **設計** - インターフェース設計と型定義
3. **実装** - TDD原則に従った開発
4. **テスト** - 各種テストの実行と品質確認
5. **レビュー** - コードレビューと品質チェック

### デバッグとトラブルシューティング

- **ログ設定**: 構造化ログの使用
- **ヘルスチェック**: システム状態の監視
- **パフォーマンス監視**: メトリクス収集と分析

### 関連資料

- **[実装計画・チェックリスト](IMPLEMENTATION_PLAN.md)** - 段階的開発計画と進捗管理
- **[開発計画](DEVELOPMENT_PLAN.md)** - 開発ロードマップ
- **[技術検討](TECHNICAL_CONSIDERATIONS.md)** - 技術的な考慮事項
- **[トランスポート設定](TRANSPORT_CONFIG.md)** - 各種起動方式の設定
- **[認証戦略](AUTHENTICATION_STRATEGY.md)** - 認証システムの設計

### サポート

開発中の質問や問題については、以下を参照してください：

1. 既存のドキュメント（上記リンク先）
2. GitHub Copilot開発ルール
3. MCP仕様書
4. TypeScript公式ドキュメント

---

**重要**: このプロジェクトは活発に開発中です。新機能の追加や既存機能の変更を行う際は、必ず関連ドキュメントの更新も合わせて行ってください。
