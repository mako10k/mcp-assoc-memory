# MCP Tool Description Improvement Plan

## 🎯 目標

LLMが連想記憶システムを効率的に活用できるよう、ツール説明とパラメータ記述を改善する。

## 📊 現状分析

### 現在のツール一覧（10個）

| ツール名 | 現在の説明 | 主な問題点 |
|---------|-----------|----------|
| `memory_store` | "Store a new memory with automatic association discovery" | 使用場面が不明確、パラメータの効果が不明 |
| `memory_search` | "Search memories using semantic similarity and associations" | 検索戦略や閾値の指針がない |
| `memory_get` | "Retrieve a memory by its ID with associations" | 連想表示の価値が不明 |
| `memory_delete` | "Delete a specified memory" | 削除の影響範囲が不明 |
| `memory_list_all` | "List all memories with pagination (for debugging purposes)" | デバッグ用途に限定、実用性が低い |
| `scope_list` | "List available scopes with hierarchy and memory counts" | スコープの活用方法が不明 |
| `scope_suggest` | "Suggest appropriate scope based on content analysis" | 提案精度や活用場面が不明 |
| `memory_move` | "Move memories to different scope" | 移動の目的や効果が不明 |
| `memory_discover_associations` | "Discover and analyze associations between memories" | 連想発見の価値や活用法が不明 |
| `session_manage` | "Manage session scopes and lifecycle" | セッションの概念や用途が不明 |

### 🚨 主要な問題点

1. **文脈不足**: いつ使うべきかが不明
2. **ワークフロー欠如**: ツール間の関係性が不明
3. **パラメータガイダンス不足**: 適切な設定値が不明
4. **実用例なし**: 具体的な使用パターンがない
5. **LLM観点の欠如**: LLMの思考プロセスを考慮していない

## 🔄 改善戦略

### 1. 使用場面の明確化

**Before**: "Store a new memory"
**After**: "💾 記憶保存: 新しい情報や学習内容を長期記憶として保存し、関連する既存記憶との自動連想を構築"

#### 改善ポイント
- 🎯 **目的明示**: 何のために使うのか
- 🔗 **連携効果**: 他の機能との関係
- 📝 **使用タイミング**: いつ使うべきか

### 2. ワークフロー指向の説明

#### 典型的なワークフロー例

```
1. 新情報の処理
   memory_store → memory_discover_associations

2. 記憶の探索
   memory_search → memory_get → memory_discover_associations

3. 記憶の整理
   scope_suggest → memory_move → scope_list

4. セッション管理
   session_manage(create) → memory_store → session_manage(cleanup)
```

### 3. パラメータガイダンス強化

#### 現在の問題例
```python
similarity_threshold: float = Field(default=0.7, description="Minimum similarity score")
```

#### 改善案
```python
similarity_threshold: float = Field(
    default=0.7, 
    ge=0.0, le=1.0,
    description="""類似度閾値 (0.0-1.0):
    - 0.8-1.0: 非常に類似した記憶のみ (厳密検索)
    - 0.6-0.8: 関連性の高い記憶 (推奨: 一般的な検索)
    - 0.4-0.6: 幅広い関連記憶 (発想拡張)
    - 0.0-0.4: 弱い関連も含む (創造的思考)"""
)
```

## 📝 具体的改善案

### A. ツール説明文の構造化

```
🎯 [目的] - [効果] - [使用場面]
💡 [典型的なワークフロー]
⚙️ [重要パラメータと推奨値]
📋 [実用例]
⚠️ [注意点・制限事項]
```

### B. 機能グループ化

#### 1. 📚 記憶管理の基本操作
- `memory_store`: 新しい記憶の保存
- `memory_get`: 特定記憶の詳細取得
- `memory_delete`: 不要記憶の削除

#### 2. 🔍 記憶の探索・発見
- `memory_search`: 意味的検索
- `memory_discover_associations`: 連想発見
- `memory_list_all`: 全体把握（デバッグ用）

#### 3. 🗂️ 組織化・管理
- `scope_list`: スコープ構造の確認
- `scope_suggest`: 適切なスコープ提案
- `memory_move`: 記憶の再配置

#### 4. 🔄 セッション・ライフサイクル
- `session_manage`: セッション管理

### C. 説明文の改善例

#### memory_store（改善前）
```
"Store a new memory with automatic association discovery"
```

#### memory_store（改善後）
```
"💾 新記憶の保存: 学習内容や重要情報を長期記憶として保存し、既存記憶との自動連想ネットワークを構築。知識の蓄積と体系化に使用。"
```

#### memory_search（改善前）
```
"Search memories using semantic similarity and associations"
```

#### memory_search（改善後）
```
"🔍 意味的記憶検索: 自然言語クエリで関連記憶を発見。アイデア発想、知識想起、関連情報収集に活用。埋め込みベクトルによる高精度な意味理解。"
```

## 🚀 実装計画

### Phase 1: 基本改善（即座に実行可能）
- [ ] 各ツールの説明文を改善
- [ ] パラメータ説明の詳細化
- [ ] 使用例の追加

### Phase 2: 構造化改善
- [ ] ツールグループの明確化
- [ ] ワークフロー例の追加
- [ ] 推奨パラメータ設定の提示

### Phase 3: 高度な改善
- [ ] 動的な説明文生成
- [ ] 使用状況に応じた推奨値調整
- [ ] LLMフィードバックに基づく継続改善

## 💡 ブレストアイデア

### 1. LLM思考プロセス考慮
- **情報収集段階**: 幅広い検索 (threshold: 0.4-0.6)
- **詳細分析段階**: 精密な関連付け (threshold: 0.7-0.8)
- **創造的発想段階**: 多様な連想 (limit: 20+, threshold: 0.3-0.5)

### 2. 状況適応型パラメータ
- **初回使用**: より詳細な説明とガイダンス
- **経験豊富**: 簡潔な説明と高度なオプション
- **エラー時**: トラブルシューティング情報

### 3. 使用パターンテンプレート
```python
# 学習セッション開始
session_manage(action="create")

# 新しい学習内容の記録
memory_store(content="...", scope="learning/today")

# 関連知識の発見
related = memory_discover_associations(memory_id, threshold=0.6)

# 理解の深化
for related_id in related:
    detail = memory_get(related_id, include_associations=True)
```

### 4. エラーパターンと対策
- **検索結果が空**: 閾値を下げる提案
- **重複記憶大量生成**: 重複検出の説明
- **スコープ混乱**: スコープ階層の説明

## 🎯 成功指標

### 定量的指標
- ツール使用時のエラー率削減
- 適切なパラメータ設定率向上
- ワークフロー完遂率向上

### 定性的指標
- LLMの自律的な最適使用
- 創造的な記憶活用パターンの出現
- 長期記憶システムとしての実用性向上

## 📋 次のアクション

1. **優先ツールの選定**: 使用頻度の高いツールから改善
2. **改善テンプレートの確定**: 統一された改善フォーマット
3. **実装とテスト**: 段階的な改善適用
4. **フィードバック収集**: 実使用での効果測定

---

**作成日**: 2025年7月10日  
**ステータス**: ブレスト完了、実装準備中  
**次回更新予定**: 具体的改善実装後
