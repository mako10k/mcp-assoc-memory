"""
FastMCP準拠のメモリ管理サーバー実装
"""

from typing import Any, Dict, List, Optional, Annotated
from fastmcp import FastMCP, Context
from pydantic import Field, BaseModel
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

# FastMCPサーバーインスタンス
mcp = FastMCP(name="AssocMemoryServer")

# 簡単なメモリ保存（実際の実装のスタブ）
memory_storage = {}


# Pydanticモデル定義
class MemoryCreateRequest(BaseModel):
    content: str = Field(description="記憶の内容")
    domain: str = Field(default="user", description="記憶のドメイン")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="追加のメタデータ")


class MemoryResponse(BaseModel):
    memory_id: str
    content: str
    domain: str
    metadata: Dict[str, Any]
    created_at: datetime


class MemorySearchRequest(BaseModel):
    query: str = Field(description="検索クエリ")
    domain: Optional[str] = Field(default=None, description="検索対象のドメイン")
    limit: int = Field(default=10, ge=1, le=100, description="取得件数の上限")


# メモリ管理ツール
@mcp.tool(
    name="memory_store",
    description="新しい記憶を保存します",
    annotations={
        "title": "記憶の保存",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False
    }
)
async def memory_store(
    request: MemoryCreateRequest,
    ctx: Context
) -> MemoryResponse:
    """記憶を保存する"""
    try:
        await ctx.info(f"記憶を保存中: {request.content[:50]}...")
        
        # 記憶を保存
        memory_id = str(uuid.uuid4())
        memory_data = {
            "memory_id": memory_id,
            "content": request.content,
            "domain": request.domain,
            "metadata": request.metadata or {},
            "created_at": datetime.now()
        }
        
        memory_storage[memory_id] = memory_data
        
        await ctx.info(f"記憶を保存しました: {memory_id}")
        
        return MemoryResponse(**memory_data)
        
    except Exception as e:
        await ctx.error(f"記憶の保存に失敗: {e}")
        raise


@mcp.tool(
    name="memory_search",
    description="記憶を検索します。類似度ベースの検索を行います",
    annotations={
        "title": "記憶の検索", 
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def memory_search(
    request: MemorySearchRequest,
    ctx: Context
) -> List[MemoryResponse]:
    """記憶を検索する"""
    try:
        await ctx.info(f"記憶を検索中: {request.query}")
        
        # 簡単な検索実装（実際の実装では埋め込みベースの類似度検索）
        results = []
        for memory_data in memory_storage.values():
            if request.domain and memory_data["domain"] != request.domain:
                continue
            if request.query.lower() in memory_data["content"].lower():
                results.append(MemoryResponse(**memory_data))
                if len(results) >= request.limit:
                    break
        
        await ctx.info(f"{len(results)}件の記憶が見つかりました")
        
        return results
        
    except Exception as e:
        await ctx.error(f"記憶の検索に失敗: {e}")
        raise


@mcp.tool(
    name="memory_get",
    description="指定されたIDの記憶を取得します",
    annotations={
        "title": "記憶の取得",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def memory_get(
    memory_id: Annotated[str, Field(description="記憶のID")],
    ctx: Context
) -> Optional[MemoryResponse]:
    """記憶を取得する"""
    try:
        await ctx.info(f"記憶を取得中: {memory_id}")
        
        memory_data = memory_storage.get(memory_id)
        
        if not memory_data:
            await ctx.warning(f"記憶が見つかりませんでした: {memory_id}")
            return None
            
        await ctx.info(f"記憶を取得しました: {memory_id}")
        
        return MemoryResponse(**memory_data)
        
    except Exception as e:
        await ctx.error(f"記憶の取得に失敗: {e}")
        raise


@mcp.tool(
    name="memory_delete",
    description="指定された記憶を削除します",
    annotations={
        "title": "記憶の削除",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True
    }
)
async def memory_delete(
    memory_id: Annotated[str, Field(description="削除する記憶のID")],
    ctx: Context
) -> Dict[str, Any]:
    """記憶を削除する"""
    try:
        await ctx.warning(f"記憶を削除中: {memory_id}")
        
        if memory_id in memory_storage:
            del memory_storage[memory_id]
            await ctx.info(f"記憶を削除しました: {memory_id}")
            return {"success": True, "message": "記憶を削除しました", "memory_id": memory_id}
        else:
            await ctx.warning(f"記憶が見つかりませんでした: {memory_id}")
            return {"success": False, "message": "記憶が見つかりませんでした", "memory_id": memory_id}
        
    except Exception as e:
        await ctx.error(f"記憶の削除に失敗: {e}")
        raise


@mcp.tool(
    name="memory_list_all",
    description="全ての記憶を一覧取得します（デバッグ用）",
    annotations={
        "title": "全記憶一覧",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True
    }
)
async def memory_list_all(ctx: Context) -> List[MemoryResponse]:
    """全ての記憶を一覧取得する（デバッグ用）"""
    try:
        await ctx.info("全記憶を取得中...")
        
        results = [MemoryResponse(**memory_data) for memory_data in memory_storage.values()]
        
        await ctx.info(f"{len(results)}件の記憶を取得しました")
        
        return results
        
    except Exception as e:
        await ctx.error(f"記憶の一覧取得に失敗: {e}")
        raise


# リソース（Resource）の定義 - FastMCPのもう一つの重要な概念
@mcp.resource("memory://stats")
async def get_memory_stats(ctx: Context) -> dict:
    """メモリ統計情報を提供するリソース"""
    await ctx.info("メモリ統計を生成中...")
    
    stats = {
        "total_memories": len(memory_storage),
        "domains": {},
        "recent_memories": []
    }
    
    # ドメイン別統計
    for memory_data in memory_storage.values():
        domain = memory_data["domain"]
        stats["domains"][domain] = stats["domains"].get(domain, 0) + 1
    
    # 最新の5件
    sorted_memories = sorted(
        memory_storage.values(),
        key=lambda x: x["created_at"],
        reverse=True
    )[:5]
    
    stats["recent_memories"] = [
        {"memory_id": m["memory_id"], "content": m["content"][:50] + "..."}
        for m in sorted_memories
    ]
    
    return stats


@mcp.resource("memory://domain/{domain}")
async def get_domain_memories(domain: str, ctx: Context) -> dict:
    """指定されたドメインの記憶一覧を提供するリソース"""
    await ctx.info(f"ドメイン '{domain}' の記憶を取得中...")
    
    domain_memories = [
        memory_data for memory_data in memory_storage.values()
        if memory_data["domain"] == domain
    ]
    
    result = {
        "domain": domain,
        "count": len(domain_memories),
        "memories": [
            {
                "memory_id": m["memory_id"],
                "content": m["content"],
                "created_at": m["created_at"]
            }
            for m in domain_memories
        ]
    }
    
    return result


# プロンプト（Prompt）の定義 - LLMとの相互作用パターン
@mcp.prompt(
    name="analyze_memories",
    description="記憶の分析を行うためのプロンプトを生成します"
)
async def analyze_memories_prompt(
    ctx: Context,
    domain: Annotated[str, Field(default="user", description="分析対象のドメイン")] = "user"
) -> str:
    """記憶分析用のプロンプトを生成する"""
    await ctx.info(f"ドメイン '{domain}' の分析プロンプトを生成中...")
    
    domain_memories = [
        memory_data for memory_data in memory_storage.values()
        if memory_data["domain"] == domain
    ]
    
    memories_text = "\n".join([
        f"- {m['content']}" for m in domain_memories[:10]  # 最大10件
    ])
    
    prompt = f"""以下は「{domain}」ドメインに保存された記憶です：

{memories_text}

これらの記憶を分析して、以下の項目について説明してください：
1. 主要なテーマやパターン
2. 重要なキーワード
3. 記憶間の関連性
4. 今後の記憶管理における推奨事項

分析結果を構造化された形式で提供してください。"""

    return prompt


@mcp.prompt(
    name="summarize_memory",
    description="特定の記憶の要約を行うためのプロンプトを生成します"
)
async def summarize_memory_prompt(
    memory_id: Annotated[str, Field(description="要約対象の記憶ID")],
    ctx: Context
) -> str:
    """記憶要約用のプロンプトを生成する"""
    await ctx.info(f"記憶 '{memory_id}' の要約プロンプトを生成中...")
    
    memory_data = memory_storage.get(memory_id)
    if not memory_data:
        raise ValueError(f"記憶が見つかりません: {memory_id}")
    
    prompt = f"""以下の記憶を要約してください：

記憶ID: {memory_data['memory_id']}
ドメイン: {memory_data['domain']}
作成日時: {memory_data['created_at']}
内容: {memory_data['content']}
メタデータ: {memory_data['metadata']}

要約は以下の形式で提供してください：
- 要点: [主要なポイント]
- キーワード: [重要なキーワード]
- カテゴリ: [適切なカテゴリ]
- 関連性: [他の記憶との潜在的な関連性]"""

    return prompt


if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")
