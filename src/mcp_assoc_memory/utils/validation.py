"""
入力値検証ユーティリティ
"""

import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from ..models.memory import MemoryDomain
from ..models.project import ProjectRole


class ValidationError(Exception):
    """検証エラー"""
    
    def __init__(self, field: str, value: Any, message: str):
        self.field = field
        self.value = value
        self.message = message
        super().__init__(f"Validation error for '{field}': {message}")


class Validator:
    """入力値検証"""
    
    @staticmethod
    def validate_memory_content(content: str) -> str:
        """記憶内容の検証"""
        if not isinstance(content, str):
            raise ValidationError("content", content, "Content must be a string")
        
        if not content.strip():
            raise ValidationError("content", content, "Content cannot be empty")
        
        if len(content) > 50000:  # 50KB制限
            raise ValidationError("content", content, "Content is too long (max 50KB)")
        
        return content.strip()
    
    @staticmethod
    def validate_memory_domain(domain: Union[str, MemoryDomain]) -> MemoryDomain:
        """記憶ドメインの検証"""
        if isinstance(domain, str):
            try:
                return MemoryDomain(domain)
            except ValueError:
                valid_domains = [d.value for d in MemoryDomain]
                raise ValidationError("domain", domain, f"Invalid domain. Valid domains: {valid_domains}")
        
        if isinstance(domain, MemoryDomain):
            return domain
        
        raise ValidationError("domain", domain, "Domain must be a string or MemoryDomain enum")
    
    @staticmethod
    def validate_tags(tags: List[str]) -> List[str]:
        """タグの検証"""
        if not isinstance(tags, list):
            raise ValidationError("tags", tags, "Tags must be a list")
        
        validated_tags = []
        for tag in tags:
            if not isinstance(tag, str):
                raise ValidationError("tags", tag, "Each tag must be a string")
            
            tag = tag.strip().lower()
            if not tag:
                continue
            
            if len(tag) > 50:
                raise ValidationError("tags", tag, "Tag is too long (max 50 characters)")
            
            if not re.match(r'^[a-zA-Z0-9_-]+$', tag):
                raise ValidationError("tags", tag, "Tag contains invalid characters (only alphanumeric, _, - allowed)")
            
            validated_tags.append(tag)
        
        # 重複除去
        return list(set(validated_tags))
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """メタデータの検証"""
        if not isinstance(metadata, dict):
            raise ValidationError("metadata", metadata, "Metadata must be a dictionary")
        
        # メタデータサイズ制限（10KB）
        import json
        try:
            metadata_json = json.dumps(metadata)
            if len(metadata_json.encode('utf-8')) > 10240:
                raise ValidationError("metadata", metadata, "Metadata is too large (max 10KB)")
        except (TypeError, ValueError) as e:
            raise ValidationError("metadata", metadata, f"Metadata is not JSON serializable: {e}")
        
        return metadata
    
    @staticmethod
    def validate_user_id(user_id: Optional[str]) -> Optional[str]:
        """ユーザーIDの検証"""
        if user_id is None:
            return None
        
        if not isinstance(user_id, str):
            raise ValidationError("user_id", user_id, "User ID must be a string")
        
        user_id = user_id.strip()
        if not user_id:
            return None
        
        if len(user_id) > 100:
            raise ValidationError("user_id", user_id, "User ID is too long (max 100 characters)")
        
        if not re.match(r'^[a-zA-Z0-9_@.-]+$', user_id):
            raise ValidationError("user_id", user_id, "User ID contains invalid characters")
        
        return user_id
    
    @staticmethod
    def validate_project_id(project_id: Optional[str]) -> Optional[str]:
        """プロジェクトIDの検証"""
        if project_id is None:
            return None
        
        if not isinstance(project_id, str):
            raise ValidationError("project_id", project_id, "Project ID must be a string")
        
        project_id = project_id.strip()
        if not project_id:
            return None
        
        # UUID形式チェック
        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', project_id):
            raise ValidationError("project_id", project_id, "Project ID must be a valid UUID")
        
        return project_id
    
    @staticmethod
    def validate_session_id(session_id: Optional[str]) -> Optional[str]:
        """セッションIDの検証"""
        if session_id is None:
            return None
        
        if not isinstance(session_id, str):
            raise ValidationError("session_id", session_id, "Session ID must be a string")
        
        session_id = session_id.strip()
        if not session_id:
            return None
        
        # UUID形式チェック
        if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', session_id):
            raise ValidationError("session_id", session_id, "Session ID must be a valid UUID")
        
        return session_id
    
    @staticmethod
    def validate_project_name(name: str) -> str:
        """プロジェクト名の検証"""
        if not isinstance(name, str):
            raise ValidationError("name", name, "Project name must be a string")
        
        name = name.strip()
        if not name:
            raise ValidationError("name", name, "Project name cannot be empty")
        
        if len(name) > 100:
            raise ValidationError("name", name, "Project name is too long (max 100 characters)")
        
        return name
    
    @staticmethod
    def validate_project_role(role: Union[str, ProjectRole]) -> ProjectRole:
        """プロジェクトロールの検証"""
        if isinstance(role, str):
            try:
                return ProjectRole(role)
            except ValueError:
                valid_roles = [r.value for r in ProjectRole]
                raise ValidationError("role", role, f"Invalid role. Valid roles: {valid_roles}")
        
        if isinstance(role, ProjectRole):
            return role
        
        raise ValidationError("role", role, "Role must be a string or ProjectRole enum")
    
    @staticmethod
    def validate_search_query(query: str) -> str:
        """検索クエリの検証"""
        if not isinstance(query, str):
            raise ValidationError("query", query, "Search query must be a string")
        
        query = query.strip()
        if not query:
            raise ValidationError("query", query, "Search query cannot be empty")
        
        if len(query) > 1000:
            raise ValidationError("query", query, "Search query is too long (max 1000 characters)")
        
        return query
    
    @staticmethod
    def validate_limit(limit: Optional[int], max_limit: int = 100) -> int:
        """検索制限数の検証"""
        if limit is None:
            return 10  # デフォルト値
        
        if not isinstance(limit, int):
            raise ValidationError("limit", limit, "Limit must be an integer")
        
        if limit < 1:
            raise ValidationError("limit", limit, "Limit must be at least 1")
        
        if limit > max_limit:
            raise ValidationError("limit", limit, f"Limit is too large (max {max_limit})")
        
        return limit