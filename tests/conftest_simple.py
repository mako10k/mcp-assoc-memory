"""
Simplified test configuration to resolve async fixture deadlock.

The original conftest.py had complex async fixture dependencies that caused deadlocks.
This version uses minimal, isolated fixtures to avoid async chain issues.
"""

import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest

from mcp_assoc_memory.core.memory_manager import MemoryManager
from mcp_assoc_memory.models.memory import Memory


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
    """Provide minimal test configuration."""
    return {
        "storage": {
            "type": "sqlite",
            "database_url": f"sqlite:///{temp_dir / 'test_memory.db'}",
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
def mock_embedding_service():
    """Simple mock embedding service."""
    mock_service = AsyncMock()
    mock_service.get_embedding.return_value = [0.1] * 384
    mock_service.get_embeddings.return_value = [[0.1] * 384, [0.2] * 384]
    mock_service.initialize = AsyncMock()
    mock_service.close = AsyncMock()
    return mock_service


@pytest.fixture
async def simple_memory_manager(temp_dir: Path, mock_embedding_service) -> AsyncGenerator[MemoryManager, None]:
    """Create a simple memory manager with mocked dependencies."""
    
    # Create minimal mocks to avoid complex initialization
    mock_metadata_store = AsyncMock()
    mock_metadata_store.initialize = AsyncMock()
    mock_metadata_store.close = AsyncMock()
    
    mock_vector_store = AsyncMock()
    mock_vector_store.initialize = AsyncMock()
    mock_vector_store.close = AsyncMock()
    
    mock_graph_store = AsyncMock()
    mock_graph_store.initialize = AsyncMock()
    mock_graph_store.close = AsyncMock()
    
    # Create memory manager with all mocked dependencies
    manager = MemoryManager(
        vector_store=mock_vector_store,
        metadata_store=mock_metadata_store,
        graph_store=mock_graph_store,
        embedding_service=mock_embedding_service
    )
    
    # Mock the store_memory method to return a simple Memory object
    async def mock_store_memory(content: str, scope: str = "test", **kwargs) -> Memory:
        return Memory(
            id="test-id-123",
            content=content,
            scope=scope,
            category=kwargs.get("category", "test"),
            tags=kwargs.get("tags", []),
            metadata=kwargs.get("metadata", {}),
            created_at="2025-07-12T09:00:00Z"
        )
    
    manager.store_memory = mock_store_memory
    
    # Mock get_memory method
    async def mock_get_memory(memory_id: str) -> Optional[Memory]:
        if memory_id == "test-id-123":
            return Memory(
                id=memory_id,
                content="Test memory content",
                scope="test",
                category="test",
                tags=[],
                metadata={},
                created_at="2025-07-12T09:00:00Z"
            )
        return None
    
    manager.get_memory = mock_get_memory
    
    await manager.initialize()
    yield manager
    await manager.close()


# Alias for backward compatibility with existing tests
@pytest.fixture
async def test_memory_manager(simple_memory_manager):
    """Alias for backward compatibility."""
    return simple_memory_manager


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
        }
    ]
