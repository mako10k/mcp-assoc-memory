"""
Session management for organizing temporary memories
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
import uuid

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages session-based memory organization"""
    
    def __init__(self):
        self._current_session: Optional[str] = None
        self._session_created_at: Optional[datetime] = None
    
    def get_current_session(self) -> str:
        """Get or create current session ID"""
        if not self._current_session:
            self.create_new_session()
        assert self._current_session is not None, "Session should be created"
        return self._current_session
    
    def create_new_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session"""
        if session_id:
            self._current_session = session_id
        else:
            # Generate session ID with timestamp
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            self._current_session = f"{timestamp}-{unique_id}"
        
        self._session_created_at = datetime.now()
        logger.info(f"Created new session: {self._current_session}")
        return self._current_session
    
    def get_session_info(self) -> dict:
        """Get current session information"""
        return {
            "session_id": self._current_session,
            "created_at": self._session_created_at.isoformat() if self._session_created_at else None,
            "active_duration": str(datetime.now() - self._session_created_at) if self._session_created_at else None
        }
    
    def end_session(self) -> Optional[str]:
        """End current session and return session ID"""
        ended_session = self._current_session
        self._current_session = None
        self._session_created_at = None
        if ended_session:
            logger.info(f"Ended session: {ended_session}")
        return ended_session


# Global session manager instance
_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get global session manager instance"""
    return _session_manager
