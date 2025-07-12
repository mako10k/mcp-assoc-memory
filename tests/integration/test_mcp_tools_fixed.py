"""
Simplified integration tests for MCP API tools.

Tests basic integration of MCP tools with the memory system.
"""

import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock, patch

from mcp_assoc_memory.api.tools.memory_tools import (
    handle_memory_search,
    handle_memory_store
)
from mcp_assoc_memory.core.memory_manager import MemoryManager


class TestMemoryToolsIntegration:
    """Integration tests for memory-related MCP tools."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_store_tool_basic(self, test_memory_manager: MemoryManager):
        """Test memory store tool with basic parameters."""
        arguments = {
            "request": {
                "content": "Test memory via MCP tool",
                "scope": "test/mcp",
                "tags": ["test", "mcp"],
                "category": "test"
            }
        }
        
        result = await handle_memory_store(arguments, test_memory_manager)
        
        assert result["success"] is True
        assert "data" in result
        assert "memory_id" in result["data"]
        assert result["data"]["content"] == "Test memory via MCP tool"
        assert result["data"]["scope"] == "test/mcp"
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_search_tool_basic(self, test_memory_manager: MemoryManager):
        """Test memory search tool with basic parameters."""
        # First store a memory to search for
        store_args = {
            "request": {
                "content": "Python programming language basics",
                "scope": "test/search",
                "tags": ["python", "programming"]
            }
        }
        store_result = await handle_memory_store(store_args, test_memory_manager)
        assert store_result["success"] is True
        
        # Now search for it
        search_args = {
            "request": {
                "query": "Python programming",
                "limit": 5,
                "mode": "standard",
                "similarity_threshold": 0.1
            }
        }
        
        result = await handle_memory_search(search_args, test_memory_manager)
        
        assert result["success"] is True
        assert "data" in result
        assert isinstance(result["data"], list)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_store_tool_error_handling(self, test_memory_manager: MemoryManager):
        """Test memory store tool error handling."""
        # Test with missing required content
        arguments = {
            "request": {
                "scope": "test/error",
                # content is missing
            }
        }
        
        result = await handle_memory_store(arguments, test_memory_manager)
        
        # Should handle missing content gracefully
        # The exact behavior depends on the implementation
        assert "success" in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_search_tool_empty_query(self, test_memory_manager: MemoryManager):
        """Test memory search tool with empty query."""
        arguments = {
            "request": {
                "query": "",
                "limit": 5
            }
        }
        
        result = await handle_memory_search(arguments, test_memory_manager)
        
        # Should handle empty query gracefully
        assert "success" in result


class TestToolIntegrationWorkflow:
    """Test complete workflows using multiple tools."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_store_and_search_workflow(self, test_memory_manager: MemoryManager):
        """Test complete store and search workflow."""
        # Store multiple memories
        memories_to_store = [
            {
                "content": "Machine learning fundamentals",
                "scope": "learning/ml",
                "tags": ["ml", "fundamentals"]
            },
            {
                "content": "Deep learning neural networks",
                "scope": "learning/dl",
                "tags": ["dl", "neural-networks"]
            },
            {
                "content": "Python programming basics",
                "scope": "learning/programming",
                "tags": ["python", "programming"]
            }
        ]
        
        stored_ids = []
        for memory_data in memories_to_store:
            store_args = {"request": memory_data}
            result = await handle_memory_store(store_args, test_memory_manager)
            
            assert result["success"] is True
            stored_ids.append(result["data"]["memory_id"])
        
        # Search for machine learning related content
        search_args = {
            "request": {
                "query": "machine learning",
                "limit": 10,
                "mode": "standard",
                "similarity_threshold": 0.1
            }
        }
        
        search_result = await handle_memory_search(search_args, test_memory_manager)
        
        assert search_result["success"] is True
        assert isinstance(search_result["data"], list)
        
        # Should find at least some relevant memories
        if search_result["data"]:
            found_memory = search_result["data"][0]
            assert "memory_id" in found_memory
            assert "content" in found_memory
            assert "similarity_score" in found_memory


class TestToolParameterValidation:
    """Test tool parameter validation."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_store_parameter_validation(self, test_memory_manager: MemoryManager):
        """Test parameter validation for memory store tool."""
        # Test with invalid arguments structure
        invalid_args = {
            "invalid_key": "invalid_value"
        }
        
        result = await handle_memory_store(invalid_args, test_memory_manager)
        
        # Should handle invalid arguments gracefully
        assert "success" in result
        if not result["success"]:
            assert "error" in result or "message" in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_search_parameter_validation(self, test_memory_manager: MemoryManager):
        """Test parameter validation for memory search tool."""
        # Test with invalid arguments structure  
        invalid_args = {
            "request": {
                "limit": "not_a_number"  # Should be int
            }
        }
        
        result = await handle_memory_search(invalid_args, test_memory_manager)
        
        # Should handle invalid arguments gracefully
        assert "success" in result
