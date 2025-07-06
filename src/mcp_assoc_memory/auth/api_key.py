"""
APIキー認証
"""

from typing import Optional, Dict, Any
import hashlib
import secrets
import time
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class APIKey:
    """APIキー情報"""
    key_id: str
    key_hash: str
    user_id: str
    name: str
    created_at: float
    last_used: Optional[float] = None
    is_active: bool = True
    permissions: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = {}


class APIKeyAuth:
    """APIキー認証クラス"""
    
    def __init__(self):
        self.api_keys: Dict[str, APIKey] = {}
    
    def generate_api_key(self, user_id: str, name: str = "Default") -> tuple[str, APIKey]:
        """新しいAPIキーを生成"""
        # 32バイトのランダムキーを生成
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_id = hashlib.sha256(f"{user_id}:{time.time()}".encode()).hexdigest()[:16]
        
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_id,
            name=name,
            created_at=time.time()
        )
        
        self.api_keys[key_id] = api_key
        logger.info(f"APIキー生成: {key_id} (ユーザー: {user_id})")
        
        return raw_key, api_key
    
    def verify_api_key(self, raw_key: str) -> Optional[APIKey]:
        """APIキーを検証"""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        for api_key in self.api_keys.values():
            if api_key.key_hash == key_hash and api_key.is_active:
                api_key.last_used = time.time()
                return api_key
        
        return None
    
    def revoke_api_key(self, key_id: str) -> bool:
        """APIキーを無効化"""
        if key_id in self.api_keys:
            self.api_keys[key_id].is_active = False
            logger.info(f"APIキー無効化: {key_id}")
            return True
        return False
    
    def list_user_keys(self, user_id: str) -> list[APIKey]:
        """ユーザーのAPIキー一覧を取得"""
        return [
            api_key for api_key in self.api_keys.values()
            if api_key.user_id == user_id
        ]
    
    def get_api_key_stats(self) -> Dict[str, Any]:
        """APIキー統計を取得"""
        total_keys = len(self.api_keys)
        active_keys = len([k for k in self.api_keys.values() if k.is_active])
        
        return {
            'total_keys': total_keys,
            'active_keys': active_keys,
            'revoked_keys': total_keys - active_keys
        }
