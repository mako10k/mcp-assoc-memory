# 技術検討事項

## 1. アーキテクチャ選択

### 1.1 埋め込みモデルの選択

#### Option A: OpenAI Embeddings API
**メリット**:
- 高品質な埋め込み（最新のtext-embedding-3-small）
- クラウドでの計算（ローカルリソース不要）
- 継続的な改善とアップデート

**デメリット**:
- APIコスト（$0.02/1Mトークン）
- インターネット接続必須
- レート制限（3,000 RPM）
- プライバシー懸念

#### Option B: Sentence Transformers (ローカル)
**メリット**:
- 完全オフライン動作
- コスト0
- プライバシー保護
- 高速（GPU利用時）

**デメリット**:
- ローカルリソース消費
- モデル品質が劣る場合がある
- GPU推奨（CPU では遅い）

**推奨**: **ハイブリッド方式**
- デフォルト: OpenAI API
- オプション: Sentence Transformers
- 設定で切り替え可能

### 1.2 ベクトルデータベースの選択

#### Option A: Chroma
**メリット**:
- Pythonネイティブ
- 軽量でセットアップ簡単
- ローカル永続化
- 豊富なメタデータフィルタリング

**デメリット**:
- スケーラビリティ制限
- 分散対応なし
- エンタープライズ機能不足

#### Option B: Pinecone
**メリット**:
- 高性能・高スケール
- 完全マネージド
- 高度な検索機能

**デメリット**:
- 高コスト
- ベンダーロックイン
- インターネット接続必須

#### Option C: Weaviate
**メリット**:
- 高機能
- オンプレミス・クラウド両対応
- GraphQL API

**デメリット**:
- セットアップ複雑
- リソース消費大

**推奨**: **Chroma（フェーズ1）→ 拡張オプション（将来）**

### 1.3 グラフデータベースの選択

#### Option A: NetworkX (Python)
**メリット**:
- Pythonネイティブ
- 豊富なアルゴリズム
- 軽量
- 学習コスト低

**デメリット**:
- インメモリのみ
- スケーラビリティ制限
- 永続化は手動

#### Option B: Neo4j
**メリット**:
- 本格的グラフDB
- 高性能クエリ（Cypher）
- 豊富な機能

**デメリット**:
- セットアップ複雑
- リソース消費大
- 学習コスト高

**推奨**: **NetworkX（フェーズ1）→ Neo4j（拡張時）**

## 2. データモデリング戦略

### 2.1 記憶の階層化

```
Level 1: 基本記憶
├── content (生テキスト)
├── embedding (ベクトル)
├── metadata (タグ、カテゴリ等)
└── lifecycle (作成日時、アクセス回数等)

Level 2: 関連記憶
├── semantic_relations (意味的関連)
├── temporal_relations (時系列関連)
├── manual_relations (手動関連)
└── inferred_relations (推論関連)

Level 3: 記憶クラスター
├── topic_clusters (トピッククラスター)
├── importance_groups (重要度グループ)
└── usage_patterns (使用パターン)
```

### 2.2 関連性のタイプ定義

```python
class RelationType(Enum):
    SEMANTIC = "semantic"        # 意味的類似性
    TEMPORAL = "temporal"        # 時系列的関連
    CAUSAL = "causal"           # 因果関係
    HIERARCHICAL = "hierarchical" # 階層関係
    MANUAL = "manual"           # 手動設定
    INFERRED = "inferred"       # AI推論
```

### 2.3 記憶の重み付け戦略

```python
def calculate_memory_importance(memory: Memory) -> float:
    """記憶の重要度を動的計算"""
    base_importance = memory.importance
    
    # アクセス頻度による重み
    access_weight = min(memory.access_count / 100, 0.3)
    
    # 時間経過による減衰
    days_old = (datetime.now() - memory.created_at).days
    temporal_decay = max(0.5, 1.0 - (days_old / 365) * 0.5)
    
    # 関連数による重み
    relation_weight = min(len(memory.relations) / 50, 0.2)
    
    return min(1.0, base_importance + access_weight + relation_weight) * temporal_decay
```

## 3. パフォーマンス最適化戦略

### 3.1 埋め込み生成の最適化

#### 戦略1: バッチ処理
```python
async def batch_embed_texts(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """テキストを一括で埋め込み生成"""
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = await embedding_service.embed_batch(batch)
        embeddings.extend(batch_embeddings)
    return embeddings
```

#### 戦略2: キャッシュ戦略
```python
class EmbeddingCache:
    def __init__(self, max_size: int = 10000):
        self.cache = LRUCache(maxsize=max_size)
        self.hash_cache = {}
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return self.cache.get(text_hash)
    
    def set_embedding(self, text: str, embedding: List[float]):
        text_hash = hashlib.md5(text.encode()).hexdigest()
        self.cache[text_hash] = embedding
```

### 3.2 検索性能の最適化

#### 戦略1: インデックス最適化
```sql
-- SQLite インデックス戦略
CREATE INDEX idx_memories_category_importance ON memories(category, importance DESC);
CREATE INDEX idx_memories_created_at_desc ON memories(created_at DESC);
CREATE INDEX idx_memories_tags_gin ON memories(tags) WHERE tags IS NOT NULL;
CREATE INDEX idx_associations_strength ON associations(strength DESC);
```

#### 戦略2: 段階的検索
```python
async def hierarchical_search(query: str, limit: int = 10) -> List[Memory]:
    """段階的検索で高速化"""
    
    # Stage 1: 高速フィルタリング（メタデータベース）
    candidates = await metadata_store.quick_filter(
        query_keywords=extract_keywords(query),
        limit=limit * 5  # より多くの候補を取得
    )
    
    # Stage 2: ベクトル類似度計算（候補のみ）
    query_embedding = await embedding_service.embed_text(query)
    scored_candidates = await vector_store.score_candidates(
        candidates, query_embedding
    )
    
    # Stage 3: 最終ランキング
    return await rank_by_multiple_factors(scored_candidates)[:limit]
```

### 3.3 メモリ使用量の最適化

#### 戦略1: 遅延読み込み
```python
class LazyMemory:
    def __init__(self, memory_id: str, metadata_store: MetadataStore):
        self.id = memory_id
        self._content = None
        self._embedding = None
        self.metadata_store = metadata_store
    
    @property
    def content(self) -> str:
        if self._content is None:
            self._content = self.metadata_store.get_content(self.id)
        return self._content
    
    @property
    def embedding(self) -> List[float]:
        if self._embedding is None:
            self._embedding = self.metadata_store.get_embedding(self.id)
        return self._embedding
```

## 4. セキュリティとプライバシー

### 4.1 データ暗号化

#### Option A: 透明暗号化
```python
class EncryptedMetadataStore:
    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key.encode())
    
    def encrypt_content(self, content: str) -> str:
        return self.cipher.encrypt(content.encode()).decode()
    
    def decrypt_content(self, encrypted_content: str) -> str:
        return self.cipher.decrypt(encrypted_content.encode()).decode()
```

#### Option B: フィールドレベル暗号化
- 記憶内容のみ暗号化
- メタデータは平文（検索性能維持）
- 埋め込みは暗号化しない（類似検索のため）

### 4.2 アクセス制御

```python
class AccessController:
    def __init__(self):
        self.permissions = {}
    
    def check_permission(self, user_id: str, memory_id: str, action: str) -> bool:
        """アクセス権限をチェック"""
        user_perms = self.permissions.get(user_id, {})
        memory_perms = user_perms.get(memory_id, [])
        return action in memory_perms
    
    def grant_permission(self, user_id: str, memory_id: str, action: str):
        """権限を付与"""
        if user_id not in self.permissions:
            self.permissions[user_id] = {}
        if memory_id not in self.permissions[user_id]:
            self.permissions[user_id][memory_id] = []
        self.permissions[user_id][memory_id].append(action)
```

## 5. 拡張性の設計

### 5.1 プラグインアーキテクチャ

```python
class MemoryPlugin:
    """記憶システム拡張用プラグインベースクラス"""
    
    def pre_store(self, memory: Memory) -> Memory:
        """記憶保存前の処理"""
        return memory
    
    def post_store(self, memory: Memory) -> None:
        """記憶保存後の処理"""
        pass
    
    def pre_search(self, query: str) -> str:
        """検索前の処理"""
        return query
    
    def post_search(self, results: List[Memory]) -> List[Memory]:
        """検索後の処理"""
        return results

class SentimentAnalysisPlugin(MemoryPlugin):
    """感情分析プラグイン"""
    
    def pre_store(self, memory: Memory) -> Memory:
        sentiment = self.analyze_sentiment(memory.content)
        memory.metadata['sentiment'] = sentiment
        return memory
```

### 5.2 マルチモーダル対応の準備

```python
class MultimodalMemory(Memory):
    """マルチモーダル記憶（将来拡張）"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.modalities = {}  # 'text', 'image', 'audio' etc.
        self.cross_modal_embeddings = {}

class ImageMemoryHandler:
    """画像記憶ハンドラー（将来実装）"""
    
    async def store_image_memory(self, image_data: bytes, description: str) -> Memory:
        # CLIP等での画像埋め込み生成
        # OCRでのテキスト抽出
        # 画像特徴量の保存
        pass
```

## 6. テスト戦略

### 6.1 テストピラミッド

```
    ┌─────────────────┐
    │   E2E Tests     │  ← 少数、重要シナリオ
    │   (5-10)        │
    ├─────────────────┤
    │ Integration     │  ← 中程度、コンポーネント間
    │ Tests (20-30)   │
    ├─────────────────┤
    │  Unit Tests     │  ← 多数、個別機能
    │  (100+)         │
    └─────────────────┘
```

### 6.2 テストカテゴリ

#### 単体テスト
- 各クラス・関数の動作確認
- エッジケースの処理
- エラーハンドリング

#### 統合テスト
- ストレージ連携テスト
- API連携テスト
- データフロー確認

#### パフォーマンステスト
- レスポンス時間測定
- メモリ使用量測定
- 同時接続テスト

#### セキュリティテスト
- 入力値検証
- 権限チェック
- データ漏洩防止

## 7. 運用監視

### 7.1 メトリクス収集

```python
class MemoryMetrics:
    def __init__(self):
        self.counters = {
            'memories_stored': 0,
            'searches_performed': 0,
            'associations_created': 0,
            'errors_occurred': 0
        }
        self.histograms = {
            'search_latency': [],
            'store_latency': [],
            'embedding_latency': []
        }
    
    def record_search_latency(self, latency_ms: float):
        self.histograms['search_latency'].append(latency_ms)
    
    def increment_searches(self):
        self.counters['searches_performed'] += 1
```

### 7.2 ヘルスチェック

```python
async def health_check() -> Dict[str, str]:
    """システムヘルスチェック"""
    health = {}
    
    # データベース接続確認
    try:
        await metadata_store.ping()
        health['metadata_db'] = 'healthy'
    except Exception as e:
        health['metadata_db'] = f'unhealthy: {e}'
    
    # ベクトルDB確認
    try:
        await vector_store.ping()
        health['vector_db'] = 'healthy'
    except Exception as e:
        health['vector_db'] = f'unhealthy: {e}'
    
    # 埋め込みAPI確認
    try:
        await embedding_service.ping()
        health['embedding_api'] = 'healthy'
    except Exception as e:
        health['embedding_api'] = f'unhealthy: {e}'
    
    return health
```

## 8. 技術的負債の管理

### 8.1 優先対応項目

1. **パフォーマンス最適化**
   - N+1 クエリ問題の解決
   - 不要な埋め込み生成の削減
   - キャッシュ効率の改善

2. **コード品質向上**
   - 複雑な関数の分割
   - 型安全性の向上
   - テストカバレージ向上

3. **スケーラビリティ対応**
   - データベース分割戦略
   - 非同期処理の拡充
   - リソース使用量の最適化

### 8.2 リファクタリング計画

- **フェーズ1完了後**: 基本構造の見直し
- **フェーズ2完了後**: パフォーマンス最適化
- **フェーズ3完了後**: 拡張性向上
- **リリース後**: 継続的改善
