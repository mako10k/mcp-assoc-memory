"""
FastMCP準拠のメモリ管理サーバー実装
"""

from typing import Any, Dict, List, Optional, Union, Annotated
from fastmcp import FastMCP, Context
from pydantic import Field, BaseModel
from datetime import datetime
import logging
import asyncio
import os

# 暫定的な実装 - 実際のコンポーネントがない場合のスタブ
try:
    from .core.memory_manager import MemoryManager
    from .core.similarity import SimilarityCalculator
    from .core.embedding_service import EmbeddingService
    from .storage.metadata_store import MetadataStore
    from .storage.vector_store import VectorStore
    from .storage.graph_store import GraphStore
    from .config import Config
    from .utils.validation import ValidationError
except ImportError:
    # スタブ実装
    class ValidationError(Exception):
        pass
    
    class Config:
        def __init__(self):
            self.database_url = "sqlite:///memory.db"
            self.vector_db_config = {}
            self.graph_db_config = {}
            self.embedding_config = {}
    
    class Memory:
        def __init__(self, memory_id, content, domain, metadata, created_at):
            self.memory_id = memory_id
            self.content = content
            self.domain = domain
            self.metadata = metadata
            self.created_at = created_at
    
    class MemoryManager:
        def __init__(self, **kwargs):
            pass
        
        async def store_memory(self, content, domain="user", metadata=None, tags=None, project_id=None, user_id=None):
            import uuid
            return Memory(
                memory_id=str(uuid.uuid4()),
                content=content,
                domain=domain,
                metadata=metadata or {},
                created_at=datetime.now()
            )
        
        async def search_memories(self, query, domain=None, limit=10, min_similarity=0.3, project_id=None, user_id=None):
            # スタブ実装
            import uuid
            return [Memory(
                memory_id=str(uuid.uuid4()),
                content=f"Found: {query}",
                domain=domain or "user",
                metadata={"similarity": 0.8},
                created_at=datetime.now()
            )]
        
        async def get_memory(self, memory_id):
            # スタブ実装
            return Memory(
                memory_id=memory_id,
                content="Sample memory content",
                domain="user",
                metadata={},
                created_at=datetime.now()
            )
        
        async def delete_memory(self, memory_id):
            return True
        
        async def update_memory(self, memory_id, content=None, metadata=None, tags=None):
            return Memory(
                memory_id=memory_id,
                content=content or "Updated content",
                domain="user",
                metadata=metadata or {},
                created_at=datetime.now()
            )
    
    class SimilarityCalculator:
        def __init__(self, **kwargs):
            pass
        
        async def find_similar_memories(self, base_memory_id, limit=10, min_similarity=0.3):
            # スタブ実装
            import uuid
            return [Memory(
                memory_id=str(uuid.uuid4()),
                content=f"Related to {base_memory_id}",
                domain="user",
                metadata={"similarity": 0.7},
                created_at=datetime.now()
            )]

logger = logging.getLogger(__name__)

# FastMCPサーバーインスタンス
mcp = FastMCP(
    name="AssocMemoryServer",
    description="Memory association management server using FastMCP"
)

# グローバル設定とマネージャー
config = None
memory_manager = None
similarity_calculator = None


async def initialize_components():
    """コンポーネントの初期化"""
    global config, memory_manager, similarity_calculator
    
    config = Config()
    memory_manager = MemoryManager()
    similarity_calculator = SimilarityCalculator()
    logger.info("Components initialized")


# Pydanticモデル定義
class MemoryCreateRequest(BaseModel):
    content: str = Field(description="記憶の内容")
    domain: str = Field(default="user", description="記憶のドメイン（user, project, systemなど）")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="追加のメタデータ")
    tags: Optional[List[str]] = Field(default=None, description="タグのリスト")
    project_id: Optional[str] = Field(default=None, description="プロジェクトID")
    user_id: Optional[str] = Field(default=None, description="ユーザーID")


class MemoryResponse(BaseModel):
    memory_id: str
    content: str
    domain: str
    metadata: Dict[str, Any]
    created_at: datetime
    similarity_score: Optional[float] = None


class MemorySearchRequest(BaseModel):
    query: str = Field(description="検索クエリ")
    domain: Optional[str] = Field(default=None, description="検索対象のドメイン")
    limit: int = Field(default=10, ge=1, le=100, description="取得件数の上限")
    min_similarity: float = Field(default=0.3, ge=0.0, le=1.0, description="最小類似度閾値")
    project_id: Optional[str] = Field(default=None, description="プロジェクトID")
    user_id: Optional[str] = Field(default=None, description="ユーザーID")


# メモリ管理ツール
@mcp.tool(
    name="memory_store",
    description="新しい記憶を保存します"
)
async def store_memory(
    request: MemoryCreateRequest,
    ctx: Context
) -> MemoryResponse:
    """記憶を保存する"""
    try:
        if not memory_manager:
            await initialize_components()
        
        await ctx.info(f"記憶を保存中: {request.content[:50]}...")
        
        # 記憶を保存
        memory = await memory_manager.store_memory(
            content=request.content,
            domain=request.domain,
            metadata=request.metadata or {},
            tags=request.tags or [],
            project_id=request.project_id,
            user_id=request.user_id
        )
        
        await ctx.info(f"記憶を保存しました: {memory.memory_id}")
        
        return MemoryResponse(
            memory_id=memory.memory_id,
            content=memory.content,
            domain=memory.domain,
            metadata=memory.metadata,
            created_at=memory.created_at
        )
        
    except Exception as e:
        await ctx.error(f"記憶の保存に失敗: {e}")
        raise


@mcp.tool(
    name="memory_search",
    description="記憶を検索します。類似度ベースの検索を行います"
)
async def search_memory(
    request: MemorySearchRequest,
    ctx: Context
) -> List[MemoryResponse]:
    """記憶を検索する"""
    try:
        if not memory_manager:
            await initialize_components()
            
        await ctx.info(f"記憶を検索中: {request.query}")
        
        # 記憶を検索
        memories = await memory_manager.search_memories(
            query=request.query,
            domain=request.domain,
            limit=request.limit,
            min_similarity=request.min_similarity,
            project_id=request.project_id,
            user_id=request.user_id
        )
        
        await ctx.info(f"{len(memories)}件の記憶が見つかりました")
        
        return [
            MemoryResponse(
                memory_id=memory.memory_id,
                content=memory.content,
                domain=memory.domain,
                metadata=memory.metadata,
                created_at=memory.created_at,
                similarity_score=getattr(memory, 'similarity_score', None)
            )
            for memory in memories
        ]
        
    except Exception as e:
        await ctx.error(f"記憶の検索に失敗: {e}")
        raise


@mcp.tool(
    name="memory_get",
    description="指定されたIDの記憶を取得します"
)
async def get_memory(
    memory_id: Annotated[str, Field(description="記憶のID")],
    ctx: Context
) -> Optional[MemoryResponse]:
    """記憶を取得する"""
    try:
        if not memory_manager:
            await initialize_components()
            
        await ctx.info(f"記憶を取得中: {memory_id}")
        
        memory = await memory_manager.get_memory(memory_id)
        
        if not memory:
            await ctx.warning(f"記憶が見つかりませんでした: {memory_id}")
            return None
            
        await ctx.info(f"記憶を取得しました: {memory_id}")
        
        return MemoryResponse(
            memory_id=memory.memory_id,
            content=memory.content,
            domain=memory.domain,
            metadata=memory.metadata,
            created_at=memory.created_at
        )
        
    except Exception as e:
        await ctx.error(f"記憶の取得に失敗: {e}")
        raise


@mcp.tool(
    name="memory_get_related",
    description="指定された記憶に関連する記憶を取得します"
)
async def get_related_memories(
    memory_id: Annotated[str, Field(description="基準となる記憶のID")],
    limit: Annotated[int, Field(default=10, ge=1, le=50, description="取得件数の上限")],
    min_similarity: Annotated[float, Field(default=0.3, ge=0.0, le=1.0, description="最小類似度閾値")],
    ctx: Context
) -> List[MemoryResponse]:
    """関連する記憶を取得する"""
    try:
        if not memory_manager or not similarity_calculator:
            await initialize_components()
            
        await ctx.info(f"関連記憶を検索中: {memory_id}")
        
        # 基準記憶を取得
        base_memory = await memory_manager.get_memory(memory_id)
        if not base_memory:
            raise ValueError(f"記憶が見つかりません: {memory_id}")
        
        # 関連記憶を検索
        related_memories = await similarity_calculator.find_similar_memories(
            base_memory_id=memory_id,
            limit=limit,
            min_similarity=min_similarity
        )
        
        await ctx.info(f"{len(related_memories)}件の関連記憶が見つかりました")
        
        return [
            MemoryResponse(
                memory_id=memory.memory_id,
                content=memory.content,
                domain=memory.domain,
                metadata=memory.metadata,
                created_at=memory.created_at,
                similarity_score=getattr(memory, 'similarity_score', None)
            )
            for memory in related_memories
        ]
        
    except Exception as e:
        await ctx.error(f"関連記憶の取得に失敗: {e}")
        raise


@mcp.tool(
    name="memory_delete",
    description="指定された記憶を削除します"
)
async def delete_memory(
    memory_id: Annotated[str, Field(description="削除する記憶のID")],
    ctx: Context
) -> Dict[str, Any]:
    """記憶を削除する"""
    try:
        if not memory_manager:
            await initialize_components()
            
        await ctx.warning(f"記憶を削除中: {memory_id}")
        
        success = await memory_manager.delete_memory(memory_id)
        
        if success:
            await ctx.info(f"記憶を削除しました: {memory_id}")
            return {"success": True, "message": "記憶を削除しました", "memory_id": memory_id}
        else:
            await ctx.warning(f"記憶が見つかりませんでした: {memory_id}")
            return {"success": False, "message": "記憶が見つかりませんでした", "memory_id": memory_id}
        
    except Exception as e:
        await ctx.error(f"記憶の削除に失敗: {e}")
        raise


@mcp.tool(
    name="memory_update",
    description="既存の記憶を更新します"
)
async def update_memory(
    memory_id: Annotated[str, Field(description="更新する記憶のID")],
    ctx: Context,
    content: Annotated[Optional[str], Field(default=None, description="新しい記憶の内容")] = None,
    metadata: Annotated[Optional[Dict[str, Any]], Field(default=None, description="新しいメタデータ")] = None,
    tags: Annotated[Optional[List[str]], Field(default=None, description="新しいタグ")] = None
) -> Optional[MemoryResponse]:
    """記憶を更新する"""
    try:
        if not memory_manager:
            await initialize_components()
            
        await ctx.info(f"記憶を更新中: {memory_id}")
        
        memory = await memory_manager.update_memory(
            memory_id=memory_id,
            content=content,
            metadata=metadata,
            tags=tags
        )
        
        if not memory:
            await ctx.warning(f"記憶が見つかりませんでした: {memory_id}")
            return None
            
        await ctx.info(f"記憶を更新しました: {memory_id}")
        
        return MemoryResponse(
            memory_id=memory.memory_id,
            content=memory.content,
            domain=memory.domain,
            metadata=memory.metadata,
            created_at=memory.created_at
        )
        
    except Exception as e:
        await ctx.error(f"記憶の更新に失敗: {e}")
        raise


# サーバー起動関数
async def run_server():
    """サーバーを起動する"""
    await initialize_components()
    logger.info("FastMCP Memory Server started")


if __name__ == "__main__":
    # 初期化を実行してからサーバーを起動
    asyncio.run(initialize_components())
    mcp.run(transport="http", host="127.0.0.1", port=3006, path="/mcp")
