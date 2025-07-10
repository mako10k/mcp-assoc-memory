# Tool Description Implementation Guidelines - Updated with 2025 Best Practices

## � 2025年最新ベストプラクティス適用版

### 📚 参考資料
- **最新調査**: [MCP Tool Description Best Practices 2025](./knowledges/mcp-tool-description-best-practices-2025.md)
- **情報源**: MCP公式仕様 2025-03-26、Anthropic Claude、最新研究論文
- **更新日**: 2025年7月10日

## �🎯 2025年推奨実装ガイドライン

### 📝 統一された説明文フォーマット（最新版）

```python
@mcp.tool(
    name="action_oriented_name",  # 動作が明確な名前
    description="""🎯 [Purpose]: Clear value proposition in one line
    
When to use:
→ [Specific scenario 1]
→ [Specific scenario 2] 
→ [Specific scenario 3]

How it works:
[Brief technical explanation if helpful]

💡 Quick Start:
- Default: [recommended default usage]
- No results? [troubleshooting step]
- Advanced: [power user tip]

⚠️ Important: [key limitations or side effects]

➡️ What's next: [suggested follow-up actions]""",
    annotations={
        "title": "[User-Friendly Japanese Title]",
        "readOnlyHint": True/False,      # 2025標準: 副作用の明確化
        "destructiveHint": True/False,   # 破壊的変更の警告
        "idempotentHint": True/False     # 冪等性の保証
    }
)
```

### 🔧 パラメータ説明の2025年標準

```python
parameter_name: Type = Field(
    default=recommended_value,
    ge=min_value,  # 範囲制限
    le=max_value,  # 範囲制限
    description="""Parameter purpose and impact:
    
    Values & Use Cases:
    • [range]: [specific use case] ← RECOMMENDED for [scenario]
    • [range]: [specific use case] (for [scenario])
    • [range]: [specific use case] (advanced users)
    
    Strategy: [step-by-step approach]
    Example: parameter_name=[value] for [common case]""",
    examples=[common_value, edge_case_value]  # 2025新標準
)
```

## 🚀 Phase 1: 最新ベストプラクティス適用の優先ツール改善

### 1. memory_search の2025年仕様準拠改善

#### 改善内容（最新版）
```python
@mcp.tool(
    name="memory_search",
    description="""🔍 Semantic Memory Search: Find related memories using natural language

When to use:
→ "What did I learn about [topic]?"
→ "Find memories related to [concept]"  
→ "Show me similar ideas to [content]"

How it works:
Converts your query to semantic embeddings and searches the vector space for conceptually similar memories, ranked by relevance.

💡 Quick Start:
- Default: similarity_threshold=0.7 (reliable connections)
- No results? Lower to 0.5, then 0.3 for broader search
- Too many? Raise to 0.8 for precision
- Include associations: include_associations=True for richer context

⚠️ Important: Lower thresholds = more creative but less precise results

➡️ What's next: Use memory_get for details, memory_discover_associations for deeper exploration""",
    annotations={
        "title": "意味的記憶検索",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
```

### 2. memory_store の2025年仕様準拠改善

#### 改善内容（最新版）
```python
@mcp.tool(
    name="memory_store",
    description="""💾 Store New Memory: Solve "I want to remember this for later"

When to use:
→ Important insights you don't want to lose
→ Learning content that should connect with existing knowledge
→ Reference information for future projects

How it works:
Stores your content as a searchable memory, automatically discovers connections to existing memories, and integrates into your knowledge network.

💡 Quick Start:
- Auto-categorize: Let scope_suggest recommend the best scope
- Prevent duplicates: allow_duplicates=False (default) saves space
- Enable connections: auto_associate=True (default) builds knowledge links
- Quality control: similarity_threshold=0.95 prevents near-duplicates

⚠️ Important: Duplicate detection may block intentionally similar content

➡️ What's next: Use memory_discover_associations to explore new connections""",
    annotations={
        "title": "記憶保存と自動連想",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False
    }
)
```

### 3. memory_discover_associations の2025年仕様準拠改善

#### 改善内容（最新版）
```python
@mcp.tool(
    name="memory_discover_associations",
    description="""🧩 Discover Memory Associations: "What else is related to this idea?"

When to use:
→ After finding a relevant memory (follow-up exploration)
→ Before making decisions (gather related context)
→ During creative thinking (find unexpected connections)

How it works:
Takes a specific memory as starting point and finds semantically related memories using advanced similarity matching and diversity filtering.

💡 Quick Start:
- Reliable connections: similarity_threshold=0.7, limit=10
- Idea expansion: threshold=0.5, limit=15 (broader exploration)
- Creative brainstorming: threshold=0.3, limit=20+ (surprising links)
- Quality results: System automatically filters duplicates for diversity

⚠️ Important: Lower thresholds may include tangentially related content

➡️ What's next: Use memory_get for details, memory_store for new insights""",
    annotations={
        "title": "記憶連想発見",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
```

## 📊 パラメータ説明の2025年標準適用例

### similarity_threshold の最新ベストプラクティス適用

```python
similarity_threshold: float = Field(
    default=0.7, 
    ge=0.0, le=1.0,
    description="""Similarity threshold for memory matching:
    
    Values & Use Cases:
    • 0.8-1.0: Near-identical content (duplicate detection, exact recall) ← ADVANCED
    • 0.6-0.8: Clear relevance (general search, learning review) ← RECOMMENDED  
    • 0.4-0.6: Broader associations (idea expansion, new perspectives)
    • 0.2-0.4: Creative connections (brainstorming, unexpected links)
    
    Strategy: Start with 0.7, lower gradually if no results found
    Example: similarity_threshold=0.6 for most typical searches""",
    examples=[0.6, 0.7, 0.4]  # 2025新標準: 具体例の提供
)
```

### scope パラメータの改善（2025年版）

```python
scope: str = Field(
    default="user/default", 
    description="""Memory scope for hierarchical organization:
    
    Values & Use Cases:
    • learning/[topic]/[subtopic]: Academic and skill development
      Example: learning/programming/python, learning/ml/transformers
    • work/[project]/[category]: Professional and project content  
      Example: work/webapp/backend, work/client-meetings/feedback
    • personal/[category]: Private thoughts and ideas
      Example: personal/ideas, personal/reflections, personal/goals
    • session/[identifier]: Temporary session-based memories
      Example: session/2025-07-10, session/current-project
    
    Strategy: Use scope_suggest for automatic categorization
    Example: scope="learning/mcp/implementation" for this context""",
    examples=["learning/programming/python", "work/project/backend", "personal/ideas"]
)
```

### limit パラメータの効果的説明（2025年版）

```python
limit: int = Field(
    default=10, ge=1, le=50,
    description="""Maximum number of memories to retrieve:
    
    Values & Use Cases:
    • 5-10: Focused search (finding specific information) ← RECOMMENDED
    • 10-20: Balanced exploration (general ideation, learning review)
    • 20-50: Comprehensive discovery (brainstorming, research phase)
    
    Strategy: Start small (10), increase if you need broader context
    Example: limit=15 for creative thinking sessions
    
    ⚠️ Performance: Higher values increase processing time""",
    examples=[10, 15, 5]
)
```

## 🔄 実装手順

### Step 1: 基本ツールの改善
```bash
# 1. memory_search の description 更新
# 2. memory_store の description 更新  
# 3. memory_discover_associations の description 更新
```

### Step 2: パラメータ説明の詳細化
```bash
# 1. similarity_threshold の詳細説明追加
# 2. scope パラメータの例示追加
# 3. limit パラメータのガイダンス追加
```

### Step 3: テストとフィードバック
```bash
# 1. 実際の使用テスト
# 2. LLMによる自然な使用確認
# 3. エラーパターンの確認と対策
```

## 🎯 成功指標

### 即座に確認可能
- [ ] ツール説明の理解しやすさ
- [ ] 適切なパラメータ設定率
- [ ] エラー発生率の低下

### 中長期的効果
- [ ] 自然なワークフロー使用
- [ ] 創造的な記憶活用パターン
- [ ] LLMの自律的最適化

## 📝 実装チェックリスト

### memory_search
- [ ] 説明文の改善
- [ ] similarity_threshold の詳細化
- [ ] scope パラメータの例示
- [ ] include_associations の説明

### memory_store  
- [ ] 説明文の改善
- [ ] auto_associate の効果説明
- [ ] allow_duplicates の注意事項
- [ ] scope設定のガイダンス

### memory_discover_associations
- [ ] 説明文の改善
- [ ] 用途別threshold推奨値
- [ ] limit設定の指針
- [ ] ワークフロー連携の説明

## 🚀 次のアクション

1. **Priority 1**: memory_search の改善実装
2. **Priority 2**: memory_store の改善実装  
3. **Priority 3**: memory_discover_associations の改善実装
4. **Testing**: 改善効果の確認
5. **Iteration**: フィードバックに基づく調整

---

**準備完了！** 具体的な実装を開始しましょう 🚀
