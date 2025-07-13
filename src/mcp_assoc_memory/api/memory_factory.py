"""
On-demand memory manager factory for MCP tools
Solves the process isolation problem by creating memory manager instances dynamically
"""

import logging
from typing import Optional

from ..config import get_config
from ..core.embedding_service import EmbeddingService
from ..core.memory_manager import MemoryManager
from ..simple_persistence import get_persistent_storage

logger = logging.getLogger(__name__)


class MemoryManagerFactory:
    """Factory for creating memory manager instances on demand"""

    _instance: Optional["MemoryManagerFactory"] = None
    _cached_memory_manager: Optional[MemoryManager] = None
    _initialized: bool = False

    def __new__(cls) -> "MemoryManagerFactory":
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def get_memory_manager(self) -> Optional[MemoryManager]:
        """Get or create memory manager instance"""
        if self._cached_memory_manager is not None and self._initialized:
            return self._cached_memory_manager

        try:
            # Create fresh memory manager instance following server.py pattern
            get_config()  # Ensure config is loaded

            # Create all required components dynamically
            from ..core.embedding_service import (
                MockEmbeddingService,
                SentenceTransformerEmbeddingService,
            )
            from ..core.similarity import SimilarityCalculator
            from ..storage.graph_store import NetworkXGraphStore
            from ..storage.metadata_store import SQLiteMetadataStore
            from ..storage.vector_store import ChromaVectorStore

            # Initialize stores (same as server.py)
            vector_store = ChromaVectorStore()
            metadata_store = SQLiteMetadataStore()
            graph_store = NetworkXGraphStore()

            # Use SentenceTransformerEmbeddingService for production, fallback to Mock for testing
            # Initialize embedding service with fallback
            embedding_service: EmbeddingService
            try:
                embedding_service = SentenceTransformerEmbeddingService()
                logger.info("Using SentenceTransformerEmbeddingService for production")
            except Exception as e:
                logger.warning(f"Failed to initialize SentenceTransformerEmbeddingService: {e}")
                embedding_service = MockEmbeddingService()
                logger.info("Falling back to MockEmbeddingService")

            similarity_calculator = SimilarityCalculator()

            # Create memory manager
            memory_manager = MemoryManager(
                vector_store=vector_store,
                metadata_store=metadata_store,
                graph_store=graph_store,
                embedding_service=embedding_service,
                similarity_calculator=similarity_calculator,
            )

            # Initialize it
            await memory_manager.initialize()

            # Cache for future use
            self._cached_memory_manager = memory_manager
            self._initialized = True

            logger.info("Memory manager created and initialized successfully via factory")
            return memory_manager

        except Exception as e:
            logger.error(f"Failed to create memory manager via factory: {e}")
            return None

    def reset(self) -> None:
        """Reset cached memory manager (for testing)"""
        self._cached_memory_manager = None
        self._initialized = False


# Global factory instance
memory_factory = MemoryManagerFactory()


async def get_or_create_memory_manager() -> Optional[MemoryManager]:
    """Get or create memory manager instance"""
    return await memory_factory.get_memory_manager()
