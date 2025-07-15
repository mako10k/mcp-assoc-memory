"""
Simplified test configuration to resolve async fixture deadlock.

The original conftest.py had complex async fixture dependencies that caused deadlocks.
This version uses minimal, isolated fixtures to avoid async chain issues.
"""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional
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

    # Mock the store_memory method with duplicate detection support
    memory_counter = {"count": 0}  # Use dict to allow modification in nested function
    stored_memories = {}  # Store memories by content+scope for duplicate detection
    stored_memories_by_id = {}  # Store memories by ID for retrieval

    async def mock_store_memory(
        scope: str = "user/default",
        content: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        auto_associate: bool = True,
        allow_duplicates: bool = False,
        similarity_threshold: float = 0.95,
        **kwargs
    ) -> Optional[Memory]:
        # Check for duplicates if allow_duplicates is False
        if not allow_duplicates:
            duplicate_key = f"{content}||{scope}"
            if duplicate_key in stored_memories:
                # Return existing memory for duplicate content
                return stored_memories[duplicate_key]

        # Create new memory
        memory_counter["count"] += 1
        from datetime import datetime
        memory = Memory(
            id=f"test-id-{memory_counter['count']:03d}",
            content=content,
            scope=scope,
            category=category or "test",
            tags=tags or [],
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )

        # Store for duplicate detection
        duplicate_key = f"{content}||{scope}"
        stored_memories[duplicate_key] = memory

        # Store by ID for retrieval
        stored_memories_by_id[memory.id] = memory

        return memory

    manager.store_memory = mock_store_memory

    # Mock get_memory method
    async def mock_get_memory(memory_id: str) -> Optional[Memory]:
        # Check stored memories first
        if memory_id in stored_memories_by_id:
            return stored_memories_by_id[memory_id]

        # Fallback for fixed test ID
        from datetime import datetime
        if memory_id == "test-id-123":
            return Memory(
                id=memory_id,
                content="Test memory content",
                scope="test",
                category="test",
                tags=[],
                metadata={},
                created_at=datetime.utcnow()
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
        },
        {
            "content": "REST APIs provide web service interfaces",
            "scope": "learning/web",
            "category": "web-development",
            "tags": ["rest", "api", "web"],
            "metadata": {"difficulty": "intermediate"}
        }
    ]


@pytest.fixture
async def populated_memory_manager(simple_memory_manager, sample_memory_data) -> AsyncGenerator[MemoryManager, None]:
    """Create a memory manager pre-populated with sample data."""
    manager = simple_memory_manager

    # Store sample memories
    stored_memories = []
    for data in sample_memory_data:
        memory = await manager.store_memory(**data)
        stored_memories.append(memory)

    # Mock the search_memories method to return the stored memories
    async def mock_search_memories(query: str = "", scope: Optional[str] = None, limit: int = 10, **kwargs):
        # Simple mock search that returns all stored memories
        return stored_memories[:limit]

    manager.search_memories = mock_search_memories

    yield manager


class TestMemoryFactory:
    """Test memory factory for creating test Memory instances."""

    def __init__(self):
        self.counter = 0

    def create_memory(self, content: str = "Test content", scope: str = "test",
                      category: str = "test", tags: Optional[List[str]] = None,
                      metadata: Optional[Dict] = None) -> Memory:
        """Create a test Memory instance."""
        self.counter += 1
        return Memory(
            id=f"test-memory-{self.counter:03d}",
            content=content,
            scope=scope,
            category=category,
            tags=tags or [],
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )

    def create_memories(self, count: int = 1) -> List[Memory]:
        """Create multiple test Memory instances."""
        return [
            self.create_memory(
                content=f"Test memory content {i + 1}",
                scope=f"test/memory/{i + 1}",
                category="auto-generated",
                tags=[f"test-{i + 1}", "auto"],
                metadata={"index": i + 1}
            )
            for i in range(count)
        ]


@pytest.fixture
def memory_factory():
    """Provide a memory factory for tests."""
    return TestMemoryFactory()


@pytest.fixture
def test_embeddings():
    """Provide test embeddings data."""
    # Create embeddings with standard size (1536)
    import random
    random.seed(42)  # For consistent test results
    return [
        [random.random() for _ in range(1536)],
        [random.random() for _ in range(1536)],
        [random.random() for _ in range(1536)]
    ]


@pytest.fixture
def test_search_results():
    """Provide test search results data."""
    return [
        {
            "id": "test-result-1",
            "memory_id": "test-result-1",
            "content": "Test search result 1",
            "scope": "test",
            "similarity_score": 0.95
        },
        {
            "id": "test-result-2",
            "memory_id": "test-result-2",
            "content": "Test search result 2",
            "scope": "test",
            "similarity_score": 0.85
        }
    ]
