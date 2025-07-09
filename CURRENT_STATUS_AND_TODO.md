# 現在の状態と直近のToDo

**更新日時**: 2025年7月9日

## 🎯 現在の状況

### ✅ 完了済み
- **FastMCP 2.0への完全移行** - レガシーコード削除、英語化完了
- **連想記憶（Associative Memory）機能の復活** - 既存の高度なアーキテクチャをFastMCPツール層に統合
- **埋め込みベースの検索機能復活** - MemoryManager、EmbeddingService、SimilarityCalculator統合
- **新しいスコープ管理ツール実装** - scope_list, scope_suggest, memory_move, session_manage
- **連想発見ツール追加** - memory_discover_associations（類似記憶の発見・分析）
- **ページネーション対応** - memory_list_all, scope_list
- **JSON永続化実装** - data/memories.json、simple_persistence.py

### 🔧 実装された主要機能
1. **memory_store** - 自動連想発見付きの記憶保存
2. **memory_search** - 意味的類似度検索（フォールバック付き）
3. **memory_get** - 関連記憶付きの記憶取得
4. **memory_discover_associations** - 特定記憶の連想発見
5. **埋め込みベクトル検索** - ChromaVectorStore統合
6. **SQLite統合** - メタデータストア（SQLiteMetadataStore）
7. **グラフストア** - NetworkXGraphStore（記憶間関係管理）

## 🚧 直近のToDo（優先度順）

### 1. 高優先度 - システム統合とテスト
- [ ] **依存関係の確認と修正**
  - `config.py`の設定項目確認（ChromaDB、SQLite設定）
  - 必要な環境変数やデータベースファイルの初期化
  - requirements.txtの更新（ChromaDB、networkx等）

- [ ] **初期化プロセスの安定化**
  - `ensure_initialized()`の堅牢性向上
  - フォールバック機能の動作確認（高度機能→JSON永続化）
  - エラーハンドリングの改善

- [ ] **基本機能のテスト**
  - memory_store, memory_search, memory_getの動作確認
  - 埋め込みベクトル生成の動作確認
  - 類似度計算の精度検証

### 2. 中優先度 - 連想記憶機能の最適化
- [ ] **連想発見精度の向上**
  - similarity_thresholdの調整
  - 連想アルゴリズムの最適化
  - カテゴリ別連想重み付け

- [ ] **パフォーマンス改善**
  - 埋め込みキャッシュの最適化
  - ベクトル検索の高速化
  - メモリ使用量の最適化

### 3. 低優先度 - 拡張機能
- [ ] **高度な連想機能**
  - 時系列による連想発見
  - タグベースの連想フィルタリング
  - クロススコープ連想分析

- [ ] **可視化機能の復活**
  - 記憶マップ生成
  - 連想グラフ可視化
  - スコープ階層可視化

## 📁 重要なファイル構成

```
src/mcp_assoc_memory/
├── server.py                    # 👈 FastMCPツール統合（連想記憶機能付き）
├── simple_persistence.py       # 👈 JSON永続化フォールバック
├── core/
│   ├── memory_manager.py       # 👈 連想記憶エンジン（完全実装済み）
│   ├── embedding_service.py    # 👈 埋め込みベクトル生成
│   ├── similarity.py          # 👈 類似度計算
│   └── association.py         # 👈 連想関係管理
├── storage/
│   ├── vector_store.py         # 👈 ChromaDBベクトル検索
│   ├── metadata_store.py       # 👈 SQLiteメタデータ管理
│   └── graph_store.py         # 👈 NetworkX記憶関係グラフ
└── models/
    ├── memory.py              # 👈 MemoryDomain定義
    └── association.py         # 👈 Association関係モデル
```

## 🐛 既知の課題

1. **初期化エラーの可能性**
   - ChromaDB、SQLite初期化失敗時の処理
   - 設定ファイル不足時の対応

2. **型エラーの修正必要**
   - MemoryResponseのデフォルト値調整
   - タグ・カテゴリのOptional処理

3. **フォールバック動作の検証**
   - 高度機能失敗時のJSON永続化動作
   - エラー時の適切なログ出力

## 💡 次回開始時の推奨作業

1. **依存関係確認**: `pip install -r requirements.txt`の実行とエラー確認
2. **設定ファイル確認**: `config.py`の設定項目とデータベースファイル準備
3. **基本テスト実行**: memory_store/searchの簡単なテスト
4. **ログ確認**: 初期化エラーの詳細分析

## 📝 メモ
- 連想記憶機能の要件は絶対要件として維持
- 既存の高度なアーキテクチャ（MemoryManager等）は完全に実装済み
- FastMCPツール層での統合は概ね完了、細かい調整とテストが必要
- フォールバック機能により段階的な機能提供が可能
