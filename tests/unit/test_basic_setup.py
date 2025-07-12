"""
Simple unit test to verify pytest framework setup
"""

import pytest


class TestBasicSetup:
    """Basic tests to verify pytest configuration."""
    
    def test_pytest_works(self):
        """Test that pytest is working correctly."""
        assert True
        
    def test_basic_arithmetic(self):
        """Test basic arithmetic to verify test execution."""
        assert 2 + 2 == 4
        assert 5 * 3 == 15
        
    @pytest.mark.unit
    def test_unit_marker(self):
        """Test that unit marker works."""
        assert True
        
    @pytest.mark.asyncio
    async def test_async_support(self):
        """Test that async test support works."""
        result = await self._async_helper()
        assert result == "async_works"
        
    async def _async_helper(self):
        """Helper async method."""
        return "async_works"


class TestPytestFixtures:
    """Test pytest fixtures."""
    
    def test_temp_dir_fixture(self, temp_dir):
        """Test temporary directory fixture."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
        # Create a test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        assert test_file.exists()
        assert test_file.read_text() == "test content"
        
    def test_test_config_fixture(self, test_config):
        """Test configuration fixture."""
        assert isinstance(test_config, dict)
        assert "storage" in test_config
        assert "embedding" in test_config
        assert "server" in test_config
