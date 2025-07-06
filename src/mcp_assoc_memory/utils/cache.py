"""
LRUキャッシュ実装
"""

from typing import Any, Dict, Optional, OrderedDict
from datetime import datetime, timedelta
import threading
import json
import hashlib


class LRUCache:
    """LRU（Least Recently Used）キャッシュ"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: Optional[int] = None):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, key: Any) -> str:
        """キーからハッシュを生成"""
        if isinstance(key, str):
            return key
        
        # 複雑なオブジェクトの場合はJSONシリアライズしてハッシュ化
        try:
            key_str = json.dumps(key, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(key_str.encode('utf-8')).hexdigest()
        except (TypeError, ValueError):
            return str(hash(str(key)))
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """エントリが期限切れかチェック"""
        if self.ttl_seconds is None:
            return False
        
        created_at = entry.get('created_at')
        if not created_at:
            return True
        
        expiry_time = created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry_time
    
    def get(self, key: Any) -> Optional[Any]:
        """値を取得"""
        cache_key = self._generate_key(key)
        
        with self.lock:
            if cache_key not in self.cache:
                self.misses += 1
                return None
            
            entry = self.cache[cache_key]
            
            # 期限切れチェック
            if self._is_expired(entry):
                del self.cache[cache_key]
                self.misses += 1
                return None
            
            # 最後にアクセスしたアイテムを最新にする
            self.cache.move_to_end(cache_key)
            entry['accessed_at'] = datetime.utcnow()
            
            self.hits += 1
            return entry['value']
    
    def set(self, key: Any, value: Any) -> None:
        """値を設定"""
        cache_key = self._generate_key(key)
        
        with self.lock:
            # 既存エントリの更新
            if cache_key in self.cache:
                self.cache[cache_key] = {
                    'value': value,
                    'created_at': datetime.utcnow(),
                    'accessed_at': datetime.utcnow()
                }
                self.cache.move_to_end(cache_key)
                return
            
            # 新規エントリの追加
            self.cache[cache_key] = {
                'value': value,
                'created_at': datetime.utcnow(),
                'accessed_at': datetime.utcnow()
            }
            
            # サイズ制限チェック
            if len(self.cache) > self.max_size:
                # 最も古いアイテムを削除
                self.cache.popitem(last=False)
    
    def delete(self, key: Any) -> bool:
        """値を削除"""
        cache_key = self._generate_key(key)
        
        with self.lock:
            if cache_key in self.cache:
                del self.cache[cache_key]
                return True
            return False
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
    
    def cleanup_expired(self) -> int:
        """期限切れエントリをクリーンアップ"""
        if self.ttl_seconds is None:
            return 0
        
        removed_count = 0
        with self.lock:
            expired_keys = []
            for key, entry in self.cache.items():
                if self._is_expired(entry):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                removed_count += 1
        
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'ttl_seconds': self.ttl_seconds
            }


class EmbeddingCache(LRUCache):
    """埋め込みベクトル専用キャッシュ"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):  # 1時間TTL
        super().__init__(max_size, ttl_seconds)
    
    def get_embedding(self, text: str, model: str) -> Optional[list]:
        """埋め込みベクトルを取得"""
        key = f"{model}:{text}"
        return self.get(key)
    
    def set_embedding(self, text: str, model: str, embedding: list) -> None:
        """埋め込みベクトルを設定"""
        key = f"{model}:{text}"
        self.set(key, embedding)


class SearchCache(LRUCache):
    """検索結果専用キャッシュ"""
    
    def __init__(self, max_size: int = 500, ttl_seconds: int = 300):  # 5分TTL
        super().__init__(max_size, ttl_seconds)
    
    def get_search_result(self, query: str, domain: str, filters: Dict[str, Any]) -> Optional[list]:
        """検索結果を取得"""
        key = {
            'query': query,
            'domain': domain,
            'filters': filters
        }
        return self.get(key)
    
    def set_search_result(self, query: str, domain: str, filters: Dict[str, Any], results: list) -> None:
        """検索結果を設定"""
        key = {
            'query': query,
            'domain': domain,
            'filters': filters
        }
        self.set(key, results)