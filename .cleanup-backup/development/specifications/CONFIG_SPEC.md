# MCP Assoc Memory 設定ファイル仕様書

## 概要
本サーバは `config.json` により動作設定を行います。JSON形式で記述し、各セクションごとに詳細なパラメータを指定できます。

---

## embedding セクション
LLM埋め込みサービスの設定。

| キー名         | 型      | 必須 | 説明                                                                                 | 例                                  |
|:--------------|:--------|:----:|:-----------------------------------------------------------------------------------|:------------------------------------|
| service/provder| string  | ◯    | 埋め込みサービス種別。`openai` / `sentence_transformer` / `mock`                    | `service: openai`                   |
| api_key       | string  | △    | OpenAI利用時のAPIキー                                                               | `api_key: sk-...`                   |
| model         | string  | △    | モデル名（OpenAI, Sentence Transformers用）                                         | `model: text-embedding-3-small`     |
| cache_size    | int     | ×    | 埋め込みキャッシュの最大件数                                                        | `cache_size: 1000`                  |
| cache_ttl_hours| int    | ×    | キャッシュ有効期間（時間）                                                          | `cache_ttl_hours: 24`               |
| embedding_dim | int     | ×    | mockサービス用の埋め込み次元                                                        | `embedding_dim: 384`                |
| batch_size    | int     | ×    | バッチ埋め込み時のバッチサイズ                                                      | `batch_size: 100`                   |
| device        | string  | ×    | Sentence Transformers用デバイス指定（`cpu`/`cuda`等）                               | `device: cpu`                       |
| model_name    | string  | ×    | Sentence Transformers用モデル名                                                     | `model_name: all-MiniLM-L6-v2`      |

- `service` または `provider` のどちらかで指定可能（`service`優先）
- `openai` の場合は `api_key` 必須
- `sentence_transformer` の場合は `model_name` 推奨
- `mock` の場合は `embedding_dim` 推奨

---


## 例: OpenAI埋め込み (config.json)
```json
{
  "embedding": {
    "service": "openai",
    "api_key": "sk-xxx",
    "model": "text-embedding-3-small",
    "cache_size": 1000,
    "cache_ttl_hours": 24
  }
}
```

## 例: Sentence Transformers (config.json)
```json
{
  "embedding": {
    "service": "sentence_transformer",
    "model_name": "all-MiniLM-L6-v2",
    "device": "cpu",
    "cache_size": 1000
  }
}
```

## 例: Mock埋め込み (config.json)
```json
{
  "embedding": {
    "service": "mock",
    "embedding_dim": 384
  }
}
```

---

## 注意
- `service` キーがない場合は `provider` キーも許容されます。
- サーバ起動時に設定内容がログ出力されます。

---

# 【重要】現状の設定反映仕様（2025-07-07時点）

## トップレベルセクションのみ反映
- サポートされるトップレベルセクションは `embedding`, `storage`, `security`, `transport`, `database` など `Config` クラスの属性名と一致するもののみ。
- 各セクションは該当Config属性のサブ属性（例: `transport.http_port`）を上書きできる。
- 未定義セクション（例: `http`）やネストが2段以上の項目は無視される。

## 反映優先順位
1. CLI引数
2. 環境変数
3. 設定ファイル（config.json）
4. デフォルト値（Configクラス定義）

## 設定ファイル例
```json
{
  "embedding": {
    "provider": "openai",
    "api_key": "sk-...",
    "model": "text-embedding-3-small",
    "cache_size": 1000
  },
  "transport": {
    "http_port": 3006,
    "mode": "http"
  },
  "storage": {
    "data_dir": "data"
  },
  "security": {
    "auth_enabled": false
  }
}
```

## 注意
- `http` など未定義セクションはConfigに反映されません。
- 今後の改善方針: 柔軟なマッピングやバリデーション強化、セクション名のエイリアス対応などを検討中。

---
