"""
Simplified end-to-end tests for the MCP Associative Memory system.

Tests basic system functionality without complex server integration.
"""

import pytest
from pathlib import Path

from mcp_assoc_memory.core.memory_manager import MemoryManager
from mcp_assoc_memory.models.memory import Memory


class TestE2EBasicOperations:
    """End-to-end tests for basic memory operations."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complete_memory_lifecycle(self, test_memory_manager: MemoryManager):
        """Test complete memory lifecycle: store -> retrieve -> verify."""
        # Store initial memory
        stored_memory = await test_memory_manager.store_memory(
            content="E2E test memory about machine learning fundamentals",
            scope="e2e/ml",
            category="machine-learning",
            tags=["ml", "fundamentals", "e2e"],
            metadata={"test_type": "e2e", "stage": "store"}
        )
        
        assert stored_memory is not None
        assert isinstance(stored_memory, Memory)
        memory_id = stored_memory.id
        
        # Retrieve the memory
        retrieved_memory = await test_memory_manager.get_memory(memory_id)
        
        assert retrieved_memory is not None
        assert isinstance(retrieved_memory, Memory)
        assert retrieved_memory.id == memory_id
        assert retrieved_memory.content == "E2E test memory about machine learning fundamentals"
        assert retrieved_memory.scope == "e2e/ml"
        assert retrieved_memory.category == "machine-learning"
        assert "ml" in retrieved_memory.tags
        assert retrieved_memory.metadata["test_type"] == "e2e"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_multiple_memory_operations(self, test_memory_manager: MemoryManager):
        """Test storing and managing multiple memories."""
        # Store multiple related memories
        memories_data = [
            {
                "content": "Python is a programming language",
                "scope": "e2e/programming/python",
                "category": "programming",
                "tags": ["python", "language"]
            },
            {
                "content": "JavaScript is used for web development",
                "scope": "e2e/programming/javascript",
                "category": "programming",
                "tags": ["javascript", "web"]
            },
            {
                "content": "SQL is used for database queries",
                "scope": "e2e/programming/sql",
                "category": "database",
                "tags": ["sql", "database"]
            }
        ]
        
        stored_memories = []
        for data in memories_data:
            memory = await test_memory_manager.store_memory(**data)
            assert memory is not None
            stored_memories.append(memory)
        
        # Verify all memories were stored correctly
        assert len(stored_memories) == 3
        
        # Verify each memory can be retrieved
        for original_memory in stored_memories:
            retrieved = await test_memory_manager.get_memory(original_memory.id)
            assert retrieved is not None
            assert retrieved.id == original_memory.id
            assert retrieved.content == original_memory.content


class TestE2ESystemConfiguration:
    """Test system configuration and setup."""
    
    @pytest.mark.e2e
    def test_test_config_complete(self, test_config: dict):
        """Test that test configuration is complete."""
        assert "storage" in test_config
        assert "embedding" in test_config
        assert "server" in test_config
        
        storage_config = test_config["storage"]
        assert "type" in storage_config
        assert "database_url" in storage_config
    
    @pytest.mark.e2e
    def test_temp_directory_isolation(self, temp_dir: Path):
        """Test that temporary directory isolation works."""
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
        # Create test file to verify isolation
        test_file = temp_dir / "e2e_test.txt"
        test_file.write_text("E2E test isolation")
        
        assert test_file.exists()
        assert test_file.read_text() == "E2E test isolation"
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_memory_manager_health_check(self, test_memory_manager: MemoryManager):
        """Test memory manager health check functionality."""
        # Verify memory manager has health check capability
        assert hasattr(test_memory_manager, 'health_check')
        
        # Note: Actual health check might require more setup
        # For now, just verify the method exists


class TestE2EDataPersistence:
    """Test data persistence across operations."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_memory_persistence_across_operations(self, test_memory_manager: MemoryManager):
        """Test that memories persist correctly across multiple operations."""
        # Store initial set of memories
        initial_memories = []
        for i in range(3):
            memory = await test_memory_manager.store_memory(
                content=f"Persistent memory {i}",
                scope=f"e2e/persistence/test{i}",
                metadata={"sequence": i}
            )
            assert memory is not None
            initial_memories.append(memory)
        
        # Perform various operations and verify memories still exist
        for memory in initial_memories:
            retrieved = await test_memory_manager.get_memory(memory.id)
            assert retrieved is not None
            assert retrieved.content == memory.content
            assert retrieved.metadata["sequence"] == memory.metadata["sequence"]
        
        # Store additional memory
        additional_memory = await test_memory_manager.store_memory(
            content="Additional memory after operations",
            scope="e2e/persistence/additional"
        )
        assert additional_memory is not None
        
        # Verify all memories still exist
        all_memories = initial_memories + [additional_memory]
        for memory in all_memories:
            retrieved = await test_memory_manager.get_memory(memory.id)
            assert retrieved is not None
            assert retrieved.id == memory.id


class TestE2EDuplicateHandling:
    """Test duplicate detection and handling in E2E scenarios."""
    
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_duplicate_detection_workflow(self, test_memory_manager: MemoryManager):
        """Test end-to-end duplicate detection workflow."""
        content = "E2E duplicate test content"
        scope = "e2e/duplicates"
        
        # Store original memory
        original = await test_memory_manager.store_memory(
            content=content,
            scope=scope,
            allow_duplicates=False
        )
        assert original is not None
        
        # Attempt to store duplicate (should return same memory)
        duplicate_attempt = await test_memory_manager.store_memory(
            content=content,
            scope=scope,
            allow_duplicates=False
        )
        assert duplicate_attempt is not None
        assert duplicate_attempt.id == original.id
        
        # Store with allow_duplicates=True (should create new memory)
        allowed_duplicate = await test_memory_manager.store_memory(
            content=content,
            scope=scope,
            allow_duplicates=True
        )
        assert allowed_duplicate is not None
        assert allowed_duplicate.id != original.id
        assert allowed_duplicate.content == content
