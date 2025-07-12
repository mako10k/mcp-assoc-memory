"""
入力値検証ユーティリティ
"""
from typing import Any, Dict, Optional


class ValidationError(Exception):
    pass


def validate_required_fields(data: Dict[str, Any], required_fields: list[str]) -> None:
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")


def scope_value(scope: Optional[str]) -> str:
    """Convert scope to consistent string format"""
    if scope is None:
        return "user/default"
    return str(scope)
