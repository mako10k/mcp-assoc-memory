"""
セッション管理
"""

from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """セッション情報"""
    session_id: str
    user_id: str
    project_id: Optional[str] = None
    created_at: Optional[datetime] = None
    last_access: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.last_access is None:
            self.last_access = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}
    
    def is_expired(self) -> bool:
        """セッションが期限切れかチェック"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def refresh(self) -> None:
        """セッションを更新"""
        self.last_access = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書に変換"""
        result = asdict(self)
        # datetimeを文字列に変換
        if self.created_at:
            result['created_at'] = self.created_at.isoformat()
        if self.last_access:
            result['last_access'] = self.last_access.isoformat()
        if self.expires_at:
            result['expires_at'] = self.expires_at.isoformat()
        return result


class SessionManager:
    """セッション管理クラス"""
    
    def __init__(self, session_timeout_minutes: int = 60):
        self.session_timeout_minutes = session_timeout_minutes
        self.sessions: Dict[str, Session] = {}
    
    def create_session(
        self, 
        user_id: str, 
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Session:
        """新しいセッションを作成"""
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=self.session_timeout_minutes)
        
        session = Session(
            session_id=session_id,
            user_id=user_id,
            project_id=project_id,
            expires_at=expires_at,
            metadata=metadata or {}
        )
        
        self.sessions[session_id] = session
        logger.info(f"セッション作成: {session_id} (ユーザー: {user_id})")
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """セッションを取得"""
        session = self.sessions.get(session_id)
        
        if session is None:
            return None
        
        if session.is_expired():
            self.end_session(session_id)
            return None
        
        session.refresh()
        return session
    
    def switch_session(self, session_id: str, project_id: str) -> bool:
        """セッションのプロジェクトを切り替え"""
        session = self.get_session(session_id)
        
        if session is None:
            return False
        
        session.project_id = project_id
        session.refresh()
        
        logger.info(f"セッション切り替え: {session_id} -> プロジェクト: {project_id}")
        return True
    
    def end_session(self, session_id: str) -> bool:
        """セッションを終了"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            del self.sessions[session_id]
            logger.info(f"セッション終了: {session_id} (ユーザー: {session.user_id})")
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """期限切れセッションをクリーンアップ"""
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.is_expired()
        ]
        
        for session_id in expired_sessions:
            self.end_session(session_id)
        
        logger.info(f"期限切れセッション削除: {len(expired_sessions)}件")
        return len(expired_sessions)
    
    def get_user_sessions(self, user_id: str) -> List[Session]:
        """ユーザーのセッション一覧を取得"""
        return [
            session for session in self.sessions.values()
            if session.user_id == user_id and not session.is_expired()
        ]
    
    def get_sessions_stats(self) -> Dict[str, Any]:
        """セッション統計を取得"""
        total_sessions = len(self.sessions)
        active_sessions = len([
            s for s in self.sessions.values() if not s.is_expired()
        ])
        
        return {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'expired_sessions': total_sessions - active_sessions,
            'session_timeout_minutes': self.session_timeout_minutes
        }
