"""
入力値検証ユーティリティ
"""
from typing import Any, Dict


class ValidationError(Exception):
    pass


def validate_required_fields(data: Dict[str, Any], required_fields: list[str]) -> None:
    for field in required_fields:
        if field not in data:
            raise ValidationError(f"Missing required field: {field}")


def domain_value(domain):
    """MemoryDomain Enum または str を一貫して str に変換"""
    if hasattr(domain, "value"):
        return str(domain.value)
    return str(domain)
