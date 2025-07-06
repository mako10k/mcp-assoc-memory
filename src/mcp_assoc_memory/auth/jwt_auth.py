"""
JWT認証
"""

from typing import Optional, Dict, Any
import jwt
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class JWTClaims:
    """JWT クレーム情報"""
    user_id: str
    project_id: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    issued_at: Optional[float] = None
    expires_at: Optional[float] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = {}
        if self.issued_at is None:
            self.issued_at = time.time()


class JWTAuth:
    """JWT認証クラス"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def generate_token(
        self, 
        user_id: str, 
        project_id: Optional[str] = None,
        expires_minutes: int = 60,
        permissions: Optional[Dict[str, Any]] = None
    ) -> str:
        """JWTトークンを生成"""
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=expires_minutes)
        
        payload = {
            'user_id': user_id,
            'project_id': project_id,
            'permissions': permissions or {},
            'iat': now.timestamp(),
            'exp': expires_at.timestamp()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"JWTトークン生成: ユーザー {user_id}")
        
        return token
    
    def verify_token(self, token: str) -> Optional[JWTClaims]:
        """JWTトークンを検証"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            claims = JWTClaims(
                user_id=payload['user_id'],
                project_id=payload.get('project_id'),
                permissions=payload.get('permissions', {}),
                issued_at=payload.get('iat'),
                expires_at=payload.get('exp')
            )
            
            return claims
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWTトークンが期限切れです")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"無効なJWTトークン: {e}")
            return None
    
    def refresh_token(self, token: str, expires_minutes: int = 60) -> Optional[str]:
        """トークンをリフレッシュ"""
        claims = self.verify_token(token)
        if claims is None:
            return None
        
        return self.generate_token(
            user_id=claims.user_id,
            project_id=claims.project_id,
            expires_minutes=expires_minutes,
            permissions=claims.permissions
        )
    
    def decode_token_unsafe(self, token: str) -> Optional[Dict[str, Any]]:
        """トークンを検証なしでデコード（デバッグ用）"""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            logger.error(f"トークンデコードエラー: {e}")
            return None
