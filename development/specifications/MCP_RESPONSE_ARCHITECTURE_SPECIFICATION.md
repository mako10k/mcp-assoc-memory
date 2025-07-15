# MCP Response Architecture Specification

## 概要
MCP Associative Memory Server API の応答アーキテクチャの仕様書

## 基本設計原則

### 1. 基底クラス設計
- **MCPResponseBase**: 抽象基底クラス
- **ABC (Abstract Base Class)** を継承
- **統一的な応答生成メソッド** `to_response_dict()` を抽象メソッドとして定義

### 2. 派生クラス設計
- 各ツールの応答は **MCPResponseBase の派生クラス**
- 派生クラスには **MAX応答に必要な全属性** を定義
- **抽象メソッドの実装** (`to_response_dict()`) を必須とする

### 3. 応答生成層の統一
- **個別のツール出力調整は禁止**
- **共通応答処理層で統一的** に `to_response_dict()` を呼び出し
- ツール固有の応答ロジックは応答クラス内に封じ込める

### 共通応答処理層の設計
- **process_tool_response()** 関数を作成
- **Config, MCPRequestBase, MCPResponseBase, Context** を受け取り
- **最終的な出力Dict** を生成して返す
- **設定やリクエストから出力レベルを決定** する仕組みを提供

```python
def process_tool_response(
    config: Config,
    request: MCPRequestBase,  # 新しい基底クラス
    response: MCPResponseBase,
    ctx: Context
) -> Dict[str, Any]:
    # 設定やリクエストから出力レベルを決定
    level = determine_response_level(config, request)
    # response.to_response_dict(level=level) を呼び出し
    return response.to_response_dict(level=level, **kwargs)
```

### 4. 応答レベル制御
- **1つのメソッド** `to_response_dict(level="minimal")` で全てを制御
- **引数で出力レベルを指定**:
  - `"minimal"`: 最小限の必須フィールドのみ
  - `"standard"`: 標準的なフィールド
  - `"full"`: 全てのフィールドを含む完全な応答

## memory_store の応答要件

### minimal レベル (デフォルト)
```json
{
    "success": true,        // 必須
    "memory_id": "...",     // 必須  
    "created_at": "..."     // 登録時生成なので返す
}
```

### 条件付きフィールド
- **scope**: Parameterから変更された場合のみ出力
- **tags, category**: 通常は出力しない（Parameter値と同じため）
- **metadata**: 自動生成された場合のみ出力

## 実装パターン

### MCPResponseBase
```python
from abc import ABC, abstractmethod

class MCPResponseBase(BaseModel, ABC):
    @abstractmethod
    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        """統一的な応答生成メソッド"""
        pass
```

### 派生クラスの実装例
```python
class MemoryStoreResponse(MCPResponseBase):
    # 全属性を定義
    success: bool
    message: str
    memory: Optional[Memory]
    # ... その他の属性

    def to_response_dict(self, level: str = "minimal", **kwargs: Any) -> Dict[str, Any]:
        if level == "minimal":
            return {
                "success": self.success,
                "memory_id": self.memory.id if self.memory else None,
                "created_at": self.memory.created_at.isoformat() if self.memory else None,
            }
        elif level == "standard":
            # 標準レベルの実装
        elif level == "full":
            # 完全レベルの実装
```

### ツール応答層での使用
```python
# ❌ 個別調整は禁止
if minimal_response:
    return response.to_minimal_dict()
else:
    return response.model_dump()

# ✅ 統一的な呼び出し
return response.to_response_dict(level="minimal")
```

## 重要な注意点

1. **忘れてはいけない**: 個別のツール出力調整は行わない
2. **統一原則**: 全て `to_response_dict()` 経由で応答生成
3. **レベル制御**: `level` パラメータで出力内容を制御
4. **現在の方針**: 常に `"minimal"` レベルで応答（デフォルト動作）

## 今後の拡張
- `rich_response` パラメータが必要な場合に `level="full"` を指定
- 現時点では `minimal_response` パラメータは廃止
- デフォルト動作は常に minimal 形式

---

**この仕様書を参照して、要件を忘れないこと！**

## 作業品質方針

### 🚨 **絶対原則: 品質優先**
- **「時間を節約するため」は品質低下の言い訳にならない**
- **同じ品質で時短可能な場合のみ時短方針を選択**
- **品質を低下させる可能性がある作業への変更は一切許容しない**

### 作業進行方針
1. **地道にしっかりと作業を進める**
2. **一つずつ確実に実装・テスト・確認**
3. **まとめて修正する場合は同等の品質を保証**
4. **デグレードを発生させない**

### 品質保証
- 各変更後に必ずテスト実行
- 型チェック・lintチェックを怠らない
- サーバ再起動を忘れない
- **エラーが発生した場合は必ずユーザーに報告し、指示を仰ぐ**

### 🚨 **判断力の限界認識**
- **Copilotのコンテキスト理解力には限界がある**
- **分岐する可能性がある判断は必ずユーザーの指示を仰ぐ**
- **自己判断による修正は禁止**
- **小さなコンテキストでの細かい判断のみ許可**
- **不明な場合は必ず質問する**

---

**重要**: この方針に違反した作業は即座に中止し、正しい方法で再実行すること
