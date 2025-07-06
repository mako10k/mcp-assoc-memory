# MCP Associative Memory Server

LLM用の連想記憶を形成するModel Context Protocol (MCP) サーバーです。

## 概要

このプロジェクトは、LLMが効率的に情報を記憶し、関連する情報を連想的に取得できるようにするMCPサーバーを提供します。ベクトル埋め込みとグラフ構造を組み合わせることで、人間の記憶に近い連想記憶システムを実現します。

## 主要機能

- **記憶の保存**: テキスト情報をドメイン別にベクトル埋め込みとして保存
- **連想検索**: 意味的類似性に基づく高度な記憶検索
- **関連記憶**: グラフ構造による関連記憶の取得
- **記憶の管理**: 記憶の更新、削除、ドメイン変更、バッチ操作
- **プロジェクト管理**: 協調作業のためのプロジェクト・メンバー管理
- **セッション管理**: 一時的な記憶スコープの管理
- **可視化**: 記憶のネットワーク構造の可視化・分析

## MCPツール構成

本サーバーは**7つのメインツール**で全機能を提供し、サブコマンド方式で名前空間を効率化：

1. **`memory`** - 基本記憶操作（保存・検索・取得・更新・削除）
2. **`memory_manage`** - 記憶管理（統計・エクスポート・ドメイン変更・バッチ操作）
3. **`search`** - 高度検索（タグ・時間範囲・複合条件・類似検索）
4. **`project`** - プロジェクト管理（作成・メンバー操作・一覧取得）
5. **`user`** - ユーザー・セッション管理（現在情報・セッション作成/切替）
6. **`visualize`** - 可視化・分析（記憶マップ・統計ダッシュボード）
7. **`admin`** - システム管理（ヘルスチェック・バックアップ・メンテナンス）

## アーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM Client    │────│  MCP Server     │────│  Memory Store   │
│                 │    │                 │    │                 │
│ - Claude        │    │ - Tool Handler  │    │ - Vector DB     │
│ - ChatGPT       │    │ - Memory Engine │    │ - Graph DB      │
│ - Custom LLM    │    │ - API Layer     │    │ - Metadata DB   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 技術スタック

- **Language**: Python 3.11+
- **MCP Framework**: MCP Python SDK
- **Vector Database**: Chroma
- **Embedding Model**: OpenAI Embeddings / Sentence Transformers
- **Graph Database**: NetworkX (ローカル) / Neo4j (拡張)
- **Storage**: SQLite (メタデータ)

## インストール・使用方法

詳細な手順は `docs/installation.md` を参照してください。

## 開発者向け情報

### 開発ガイドライン

🤖 **AI開発エージェント向け**: [AGENT.md](AGENT.md)  
📋 **GitHub Copilot開発ルール**: [.github/copilot-instructions.md](.github/copilot-instructions.md)  
⚡ **Copilot簡易指示**: [.copilotrc.md](.copilotrc.md)

### ドキュメント

- **[実装計画・チェックリスト](IMPLEMENTATION_PLAN.md)** - 段階的開発計画と進捗管理
- **[仕様書](SPECIFICATION.md)** - API仕様と機能詳細
- **[アーキテクチャ](ARCHITECTURE.md)** - システム設計と構成要素
- **[記憶ドメイン](MEMORY_DOMAINS.md)** - ドメイン設計と管理戦略
- **[プロジェクト構造](PROJECT_STRUCTURE.md)** - ディレクトリ構成とファイル配置
- **[開発計画](DEVELOPMENT_PLAN.md)** - 開発ロードマップ
- **[技術検討](TECHNICAL_CONSIDERATIONS.md)** - 技術的な考慮事項
- **[トランスポート設定](TRANSPORT_CONFIG.md)** - 各種起動方式の設定

### 貢献

1. このプロジェクトに貢献する前に、[開発ガイドライン](.github/copilot-instructions.md)を確認してください
2. 新機能や変更を行う際は、関連ドキュメントの更新も必要です
3. TypeScript厳密モードとテスト駆動開発を徹底してください

## ライセンス

MIT License
