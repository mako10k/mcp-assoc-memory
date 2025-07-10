"""
Validation tests
"""

import pytest

from mcp_assoc_memory.models.project import ProjectRole
from mcp_assoc_memory.utils.validation import ValidationError, Validator


class TestValidator:
    """Validator tests"""

    def test_validate_memory_content_valid(self):
        """Test valid memory content"""
        content = "This is valid memory content"
        result = Validator.validate_memory_content(content)
        assert result == content

    def test_validate_memory_content_invalid(self):
        """Test invalid memory content"""
        # Empty string
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_memory_content("")
        assert "cannot be empty" in str(exc_info.value)

        # Non-string
        with pytest.raises(ValidationError):
            Validator.validate_memory_content(123)

        # Too long content
        long_content = "a" * 60000
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_memory_content(long_content)
        assert "too long" in str(exc_info.value)

    def test_validate_scope_valid(self):
        """Test valid memory scope"""
        # Valid scope strings
        result = Validator.validate_scope("user/default")
        assert result == "user/default"
        
        result = Validator.validate_scope("work/project/alpha")
        assert result == "work/project/alpha"

    def test_validate_scope_invalid(self):
        """Test invalid memory scope"""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_scope("")
        assert "cannot be empty" in str(exc_info.value)

        with pytest.raises(ValidationError):
            Validator.validate_scope(123)

    def test_validate_tags_valid(self):
        """有効なタグのテスト"""
        tags = ["tag1", "tag-2", "tag_3", "TAG4"]
        result = Validator.validate_tags(tags)

        assert "tag1" in result
        assert "tag-2" in result
        assert "tag_3" in result
        assert "tag4" in result  # 小文字化される
        assert len(result) == 4

    def test_validate_tags_invalid(self):
        """無効なタグのテスト"""
        # 非リスト
        with pytest.raises(ValidationError):
            Validator.validate_tags("not a list")

        # 長すぎるタグ
        long_tag = "a" * 60
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_tags([long_tag])
        assert "too long" in str(exc_info.value)

        # 無効文字を含むタグ
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_tags(["tag@invalid"])
        assert "invalid characters" in str(exc_info.value)

    def test_validate_tags_deduplication(self):
        """タグの重複除去テスト"""
        tags = ["tag1", "TAG1", "tag1", "tag2"]
        result = Validator.validate_tags(tags)

        assert len(result) == 2
        assert "tag1" in result
        assert "tag2" in result

    def test_validate_metadata_valid(self):
        """有効なメタデータのテスト"""
        metadata = {
            "category": "test",
            "priority": 1,
            "tags": ["a", "b"],
            "nested": {"key": "value"}
        }
        result = Validator.validate_metadata(metadata)
        assert result == metadata

    def test_validate_metadata_invalid(self):
        """無効なメタデータのテスト"""
        # 非辞書
        with pytest.raises(ValidationError):
            Validator.validate_metadata("not a dict")

        # 大きすぎるメタデータ
        large_metadata = {"data": "x" * 20000}
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_metadata(large_metadata)
        assert "too large" in str(exc_info.value)

    def test_validate_user_id_valid(self):
        """有効なユーザーIDのテスト"""
        valid_ids = [
            "user123",
            "user@example.com",
            "user.name",
            "user-name",
            "user_name"
        ]

        for user_id in valid_ids:
            result = Validator.validate_user_id(user_id)
            assert result == user_id

        # None は許可
        result = Validator.validate_user_id(None)
        assert result is None

    def test_validate_user_id_invalid(self):
        """無効なユーザーIDのテスト"""
        # 長すぎる
        long_id = "a" * 150
        with pytest.raises(ValidationError):
            Validator.validate_user_id(long_id)

        # 無効文字
        with pytest.raises(ValidationError):
            Validator.validate_user_id("user@#invalid")

    def test_validate_project_id_valid(self):
        """有効なプロジェクトIDのテスト"""
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        result = Validator.validate_project_id(valid_uuid)
        assert result == valid_uuid

        # None は許可
        result = Validator.validate_project_id(None)
        assert result is None

    def test_validate_project_id_invalid(self):
        """無効なプロジェクトIDのテスト"""
        with pytest.raises(ValidationError) as exc_info:
            Validator.validate_project_id("not-a-uuid")
        assert "valid UUID" in str(exc_info.value)

    def test_validate_search_query_valid(self):
        """有効な検索クエリのテスト"""
        query = "検索テスト"
        result = Validator.validate_search_query(query)
        assert result == query

    def test_validate_search_query_invalid(self):
        """無効な検索クエリのテスト"""
        # 空文字列
        with pytest.raises(ValidationError):
            Validator.validate_search_query("")

        # 長すぎる
        long_query = "a" * 1500
        with pytest.raises(ValidationError):
            Validator.validate_search_query(long_query)

    def test_validate_limit_valid(self):
        """有効な制限数のテスト"""
        assert Validator.validate_limit(10) == 10
        assert Validator.validate_limit(None) == 10  # デフォルト値
        assert Validator.validate_limit(1) == 1
        assert Validator.validate_limit(100) == 100

    def test_validate_limit_invalid(self):
        """無効な制限数のテスト"""
        with pytest.raises(ValidationError):
            Validator.validate_limit(0)

        with pytest.raises(ValidationError):
            Validator.validate_limit(200)  # 上限超過

        with pytest.raises(ValidationError):
            Validator.validate_limit("not an int")
