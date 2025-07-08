

from typing import Optional, Dict, Any, List
from .base import ToolResult


def tool_result(
    *,
    content: Optional[List[Any]] = None,
    success: Optional[bool] = None,
    error: Optional[str] = None,
    message: Optional[str] = None
) -> ToolResult:
    """
    MCP ToolResult（tools/callのcontent要素）を生成する共通関数。
    - 必須フィールド・型安全性を担保
    - error_resultもこのラッパーで統一
    """
    import logging
    logger = logging.getLogger("tool_result")
    try:
        import json
        logger.info("[tool_result] result dump: %s", json.dumps({
            "content": content,
            "success": success,
            "error": error,
            "message": message
        }, ensure_ascii=False, default=str))
    except Exception as e:
        logger.warning(f"[tool_result] dump failed: {e}")
    return ToolResult(
        content=content,
        success=success,
        error=error,
        message=message
    )

def error_result(
    code: str,
    message: str,
    *,
    content: Any = None
) -> ToolResult:
    """
    エラー用ToolResult（tool_resultのラッパー）
    """
    return tool_result(success=False, message=message, error=code, content=content)
