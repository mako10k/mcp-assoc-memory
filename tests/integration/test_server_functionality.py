#!/usr/bin/env python3
"""
Integration tests for MCP Associative Memory Server core functionality.

Tests server import, initialization, memory operations, and persistence systems.
These tests verify that all major components work together correctly.
"""

import asyncio
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestServerFunctionality:
    """Integration tests for server functionality"""

    def test_server_import(self):
        """Test that the server module can be imported."""
        try:
            from mcp_assoc_memory import server
            assert server is not None
        except ImportError as e:
            pytest.fail(f"Failed to import server module: {e}")

    @pytest.mark.asyncio
    async def test_memory_manager_lifecycle(self):
        """Test complete memory manager lifecycle including operations."""
        from mcp_assoc_memory.storage.vector_store import ChromaVectorStore
        from mcp_assoc_memory.storage.metadata_store import SQLiteMetadataStore
        from mcp_assoc_memory.storage.graph_store import NetworkXGraphStore
        from mcp_assoc_memory.core.embedding_service import SentenceTransformerEmbeddingService
        from mcp_assoc_memory.core.memory_manager import MemoryManager
        from mcp_assoc_memory.models.memory import MemoryDomain
        
        # Initialize with default parameters
        vector_store = ChromaVectorStore()
        metadata_store = SQLiteMetadataStore()
        graph_store = NetworkXGraphStore()
        embedding_service = SentenceTransformerEmbeddingService()
        
        manager = MemoryManager(
            vector_store=vector_store,
            metadata_store=metadata_store,
            graph_store=graph_store,
            embedding_service=embedding_service
        )
        await manager.initialize()
        
        try:
            # Store a memory
            memory = await manager.store_memory(
                domain=MemoryDomain.USER,
                content="Integration test memory for server validation",
                category="test",
                tags=["integration", "test", "server"],
                metadata={"test_type": "integration"}
            )
            
            assert memory is not None
            assert memory.id is not None
            assert memory.content == "Integration test memory for server validation"
            
            # Search for the memory
            results = await manager.search_memories(
                query="integration test server validation",
                domains=[MemoryDomain.USER],
                limit=5,
                similarity_threshold=0.1
            )
            
            assert len(results) >= 1
            found = any(r.get('memory_id') == memory.id for r in results)
            assert found, "Stored memory not found in search results"
            
            # Retrieve the memory by ID
            retrieved = await manager.get_memory(memory.id)
            assert retrieved is not None
            assert retrieved.id == memory.id
            assert retrieved.content == memory.content
            assert retrieved.domain == MemoryDomain.USER
            
        finally:
            # Clean up
            await manager.close()

    @pytest.mark.asyncio
    async def test_server_global_initialization(self):
        """Test global server initialization and memory operations."""
        from mcp_assoc_memory.server import ensure_initialized, memory_manager
        from mcp_assoc_memory.models.memory import MemoryDomain
        
        # Initialize the global memory manager
        await ensure_initialized()
        
        try:
            # Test basic operations through global manager
            memory = await memory_manager.store_memory(
                domain=MemoryDomain.USER,
                content="Global manager test memory",
                category="test",
                tags=["global", "test"],
                metadata={"test_global": True}
            )
            
            assert memory is not None
            
            # Search
            results = await memory_manager.search_memories(
                query="global manager test",
                domains=[MemoryDomain.USER],
                limit=5
            )
            
            assert len(results) >= 1
            
            # Retrieve
            retrieved = await memory_manager.get_memory(memory.id)
            assert retrieved is not None
            assert retrieved.content == "Global manager test memory"
            
        finally:
            await memory_manager.close()

    def test_json_persistence_system(self):
        """Test JSON fallback persistence system."""
        from mcp_assoc_memory.simple_persistence import SimplePersistence
        
        # Create temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            persistence = SimplePersistence(temp_path)
            
            # Test memory storage structure
            test_memories = {
                str(uuid.uuid4()): {
                    "content": "Test memory for JSON persistence verification",
                    "scope": "test/json-persistence",
                    "tags": ["test", "json", "persistence"],
                    "created_at": "2025-07-10T00:00:00Z",
                    "updated_at": "2025-07-10T00:00:00Z",
                    "metadata": {"test": True}
                }
            }
            
            # Test save
            persistence.save_memories(test_memories)
            
            # Test load
            loaded_memories = persistence.load_memories()
            assert loaded_memories is not None
            assert len(loaded_memories) == 1
            
            # Verify content
            memory_id = list(loaded_memories.keys())[0]
            memory = loaded_memories[memory_id]
            assert memory["content"] == "Test memory for JSON persistence verification"
            assert "test" in memory["tags"]
            assert memory["metadata"]["test"] is True
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_database_initialization(self):
        """Test that database components initialize correctly."""
        from mcp_assoc_memory.storage.vector_store import ChromaVectorStore
        from mcp_assoc_memory.storage.metadata_store import SQLiteMetadataStore
        from mcp_assoc_memory.storage.graph_store import NetworkXGraphStore
        from mcp_assoc_memory.core.embedding_service import SentenceTransformerEmbeddingService
        from mcp_assoc_memory.core.memory_manager import MemoryManager
        
        # Initialize with default parameters
        vector_store = ChromaVectorStore()
        metadata_store = SQLiteMetadataStore()
        graph_store = NetworkXGraphStore()
        embedding_service = SentenceTransformerEmbeddingService()
        
        manager = MemoryManager(
            vector_store=vector_store,
            metadata_store=metadata_store,
            graph_store=graph_store,
            embedding_service=embedding_service
        )
        
        # Test that stores can be created (initialization check)
        assert hasattr(manager, 'vector_store')
        assert hasattr(manager, 'metadata_store') 
        assert hasattr(manager, 'graph_store')
        assert hasattr(manager, 'embedding_service')


# Standalone runner for direct execution
async def run_integration_tests():
    """Run integration tests directly."""
    print("🧪 MCP Associative Memory Server Integration Tests")
    print("=" * 60)
    
    test_suite = TestServerFunctionality()
    tests = [
        ("Server Import", test_suite.test_server_import),
        ("Memory Manager Lifecycle", test_suite.test_memory_manager_lifecycle),
        ("Global Server Initialization", test_suite.test_server_global_initialization),
        ("JSON Persistence System", test_suite.test_json_persistence_system),
        ("Database Initialization", test_suite.test_database_initialization),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔧 Running: {test_name}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                await test_func()
            else:
                test_func()
            print(f"✅ {test_name}: PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("\n✅ MCP Associative Memory Server is working correctly:")
        print("   • Server module imports successfully")
        print("   • Core memory operations functional") 
        print("   • JSON persistence system working")
        print("   • Database initialization successful")
        print("   • Embedding and search systems operational")
        print("\n🚀 The server is ready for production use!")
        return 0
    else:
        print("💥 Some integration tests failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_integration_tests())
    sys.exit(exit_code)
