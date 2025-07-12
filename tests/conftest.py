"""
Test configuration and fixtures for the MCP Associative Memory project.

This file provides comprehensive testing infrastructure including:
- Database fixtures for isolated testing
- Memory manager fixtures for core functionality testing
- Mock services for external dependencies
- Test data factories for consistent test data
- Cleanup utilities for test isolation
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from chromadb.api import ClientAPI
from chromadb.config import Settings

from mcp_assoc_memory.core.memory_manager import MemoryManager
from mcp_assoc_memory.models.memory import Memory
from mcp_assoc_memory.storage.base import BaseStorage
from mcp_assoc_memory.storage.metadata_store import SQLiteMetadataStore
from mcp_assoc_memory.storage.vector_store import ChromaVectorStore


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_config(temp_dir: Path) -> Dict:
    """Provide test configuration with temporary paths."""
    return {
        "storage": {
            "type": "sqlite",
            "database_url": f"sqlite:///{temp_dir / 'test_memory.db'}",
            "metadata_store": {
                "type": "sqlite",
                "database_url": f"sqlite:///{temp_dir / 'test_metadata.db'}"
            },
            "vector_store": {
                "type": "chromadb",
                "persist_directory": str(temp_dir / "test_chroma_db"),
                "collection_name": "test_memories"
            }
        },
        "embedding": {
            "provider": "openai",
            "model": "text-embedding-3-small",
            "api_key": "test-key"
        },
        "server": {
            "name": "test-mcp-assoc-memory",
            "version": "0.1.0"
        }
    }


@pytest.fixture
async def mock_embedding_service():
    """Mock embedding service for testing without API calls."""
    mock_service = AsyncMock()
    mock_service.get_embedding.return_value = [0.1] * 1536  # Standard embedding size
    mock_service.get_embeddings.return_value = [[0.1] * 1536, [0.2] * 1536]
    return mock_service


@pytest.fixture
async def test_chroma_client(temp_dir: Path) -> AsyncGenerator[ClientAPI, None]:
    """Create an isolated ChromaDB client for testing."""
    import chromadb
    
    persist_directory = temp_dir / "test_chroma_db"
    persist_directory.mkdir(exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=str(persist_directory),
        settings=Settings(
            is_persistent=True,
            allow_reset=True,
            anonymized_telemetry=False
        )
    )
    
    yield client
    
    # Cleanup
    try:
        client.reset()
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture
async def test_metadata_store(temp_dir: Path) -> AsyncGenerator[SQLiteMetadataStore, None]:
    """Create an isolated metadata store for testing."""
    db_path = temp_dir / "test_metadata.db"
    store = SQLiteMetadataStore(str(db_path))
    
    await store.initialize()
    yield store
    
    await store.close()


@pytest.fixture
async def test_vector_store(temp_dir: Path) -> AsyncGenerator[ChromaVectorStore, None]:
    """Create an isolated vector store for testing."""
    persist_directory = temp_dir / "test_chroma_db"
    persist_directory.mkdir(exist_ok=True)
    
    store = ChromaVectorStore(
        persist_directory=str(persist_directory)
    )
    
    await store.initialize()
    yield store
    
    # Cleanup
    try:
        await store.close()
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture
async def test_memory_manager(
    test_config: Dict,
    test_metadata_store: SQLiteMetadataStore,
    test_vector_store: ChromaVectorStore,
    mock_embedding_service
) -> AsyncGenerator[MemoryManager, None]:
    """Create a fully configured memory manager for testing."""
    # Mock graph store for simplicity
    mock_graph_store = AsyncMock()
    mock_graph_store.initialize = AsyncMock()
    mock_graph_store.close = AsyncMock()
    
    manager = MemoryManager(
        vector_store=test_vector_store,
        metadata_store=test_metadata_store,
        graph_store=mock_graph_store,
        embedding_service=mock_embedding_service
    )
    
    await manager.initialize()
    yield manager
    
    await manager.close()


@pytest.fixture
def sample_memory_data() -> List[Dict]:
    """Provide sample memory data for testing."""
    return [
        {
            "content": "Python is a programming language",
            "scope": "learning/programming",
            "category": "programming",
            "tags": ["python", "language"],
            "metadata": {"difficulty": "beginner"}
        },
        {
            "content": "Machine learning involves training models on data",
            "scope": "learning/ml",
            "category": "machine-learning",
            "tags": ["ml", "training", "models"],
            "metadata": {"difficulty": "intermediate"}
        },
        {
            "content": "Neural networks are inspired by biological neurons",
            "scope": "learning/ml/neural-networks",
            "category": "deep-learning",
            "tags": ["neural-networks", "biology", "ai"],
            "metadata": {"difficulty": "advanced"}
        }
    ]


@pytest.fixture
async def populated_memory_manager(
    test_memory_manager: MemoryManager,
    sample_memory_data: List[Dict]
) -> AsyncGenerator[MemoryManager, None]:
    """Create a memory manager populated with sample data."""
    for data in sample_memory_data:
        await test_memory_manager.store_memory(
            content=data["content"],
            scope=data["scope"],
            category=data.get("category"),
            tags=data.get("tags"),
            metadata=data.get("metadata")
        )
    
    yield test_memory_manager


class MemoryFactory:
    """Factory class for creating test memory objects."""
    
    @staticmethod
    def create_memory(
        content: str = "Test memory content",
        scope: str = "test/scope",
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        memory_id: Optional[str] = None
    ) -> Memory:
        """Create a memory object with specified or default values."""
        return Memory(
            id=memory_id or f"test-{hash(content) % 10000}",
            content=content,
            scope=scope,
            category=category,
            tags=tags or [],
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_memories(count: int = 3) -> List[Memory]:
        """Create multiple test memory objects."""
        return [
            MemoryFactory.create_memory(
                content=f"Test memory content {i}",
                scope=f"test/scope{i}",
                category=f"category{i}",
                tags=[f"tag{i}", f"tag{i + 1}"],
                metadata={"index": i}
            )
            for i in range(count)
        ]


@pytest.fixture
def memory_factory():
    """Provide the MemoryFactory for test data creation."""
    return MemoryFactory


@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for integration testing."""
    mock_server = MagicMock()
    mock_server.list_tools.return_value = []
    mock_server.call_tool.return_value = {"success": True, "data": {}}
    return mock_server


@pytest.fixture(autouse=True)
def cleanup_environment():
    """Automatically clean up environment variables after each test."""
    original_env = os.environ.copy()
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_logger():
    """Mock logger for testing log outputs."""
    mock_logger = MagicMock()
    return mock_logger


# Test data fixtures
@pytest.fixture
def test_embeddings():
    """Provide test embedding vectors."""
    return [
        [0.1, 0.2, 0.3] * 512,  # 1536 dimensions
        [0.4, 0.5, 0.6] * 512,
        [0.7, 0.8, 0.9] * 512
    ]


@pytest.fixture
def test_search_results():
    """Provide sample search results for testing."""
    return [
        {
            "memory_id": "test-1",
            "content": "First test result",
            "similarity_score": 0.95,
            "scope": "test/results"
        },
        {
            "memory_id": "test-2",
            "content": "Second test result",
            "similarity_score": 0.85,
            "scope": "test/results"
        }
    ]


# Parametrized fixtures for comprehensive testing
@pytest.fixture(params=["sqlite", "postgresql"])
def database_type(request):
    """Parametrized fixture for testing different database types."""
    return request.param


@pytest.fixture(params=["openai", "huggingface"])
def embedding_provider(request):
    """Parametrized fixture for testing different embedding providers."""
    return request.param


# Test markers are defined in pyproject.toml
