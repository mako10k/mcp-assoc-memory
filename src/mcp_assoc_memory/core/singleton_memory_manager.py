"""Singleton Memory Manager with contract enforcement and async initialization.

This module provides a single global manager to coordinate the unified
`MemoryManager` instance used across the server and tools. It uses
platformdirs-based path helpers for default storage locations and follows
Design by Contract rules (assertions and fail-fast behavior).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from ..core.embedding_service import EmbeddingService
from ..core.memory_manager import MemoryManager
from ..core.similarity import SimilarityCalculator
from ..storage.base import BaseGraphStore, BaseMetadataStore, BaseVectorStore
from ..storage.graph_store import NetworkXGraphStore
from ..storage.metadata_store import SQLiteMetadataStore
from ..storage.vector_store import ChromaVectorStore
from ..utils.paths import get_chroma_dir, get_database_path, get_graph_path

logger = logging.getLogger(__name__)


class SingletonMemoryManager:
    """Async-safe singleton wrapper for the unified MemoryManager."""

    def __init__(self) -> None:
        self._memory_manager: Optional[MemoryManager] = None
        self._initialized: bool = False
        self._lock = asyncio.Lock()

    def get_instance(self) -> Optional[MemoryManager]:
        """Get current MemoryManager instance (may be None)."""
        return self._memory_manager

    async def initialize(
        self,
        *,
        vector_store: BaseVectorStore,
        metadata_store: BaseMetadataStore,
        graph_store: BaseGraphStore,
        embedding_service: EmbeddingService,
        similarity_calculator: Optional[SimilarityCalculator] = None,
        force_reinit: bool = False,
    ) -> MemoryManager:
        """Initialize the singleton MemoryManager instance.

        Preconditions are validated with assertions and the function is
        guarded by an asyncio lock to ensure consistent initialization.
        """
        # Preconditions
        assert vector_store is not None, "vector_store is required"
        assert metadata_store is not None, "metadata_store is required"
        assert graph_store is not None, "graph_store is required"
        assert embedding_service is not None, "embedding_service is required"

        async with self._lock:
            if self._initialized and self._memory_manager and not force_reinit:
                return self._memory_manager

            # Create and initialize unified MemoryManager
            manager = MemoryManager(
                vector_store=vector_store,
                metadata_store=metadata_store,
                graph_store=graph_store,
                embedding_service=embedding_service,
                similarity_calculator=similarity_calculator,
            )
            await manager.initialize()

            self._memory_manager = manager
            self._initialized = True
            return manager

    async def close(self) -> None:
        """Close and reset the singleton manager."""
        async with self._lock:
            if self._memory_manager is not None:
                try:
                    await self._memory_manager.close()
                finally:
                    self._memory_manager = None
                    self._initialized = False

    def is_initialized(self) -> bool:
        return self._initialized and self._memory_manager is not None


# Global singleton instance
_singleton_manager = SingletonMemoryManager()


def get_singleton_manager() -> SingletonMemoryManager:
    """Get the global singleton manager instance."""
    return _singleton_manager


async def get_memory_manager() -> Optional[MemoryManager]:
    """Get the MemoryManager instance from singleton (may be None)."""
    return _singleton_manager.get_instance()


async def initialize_memory_manager(
    *,
    vector_store: BaseVectorStore,
    metadata_store: BaseMetadataStore,
    graph_store: BaseGraphStore,
    embedding_service: EmbeddingService,
    similarity_calculator: Optional[SimilarityCalculator] = None,
    force_reinit: bool = False,
) -> MemoryManager:
    """Initialize the global MemoryManager singleton."""
    return await _singleton_manager.initialize(
        vector_store=vector_store,
        metadata_store=metadata_store,
        graph_store=graph_store,
        embedding_service=embedding_service,
        similarity_calculator=similarity_calculator,
        force_reinit=force_reinit,
    )


async def close_memory_manager() -> None:
    """Close the global MemoryManager singleton."""
    await _singleton_manager.close()


def is_memory_manager_initialized() -> bool:
    """Check if the global MemoryManager is initialized."""
    return _singleton_manager.is_initialized()


async def get_or_create_memory_manager() -> Optional[MemoryManager]:
    """Get or create the MemoryManager with default dependencies.

    Contract Programming:
    - If manager reports initialized, the instance MUST be retrievable.
    - Fallbacks are explicit and logged; no silent behavior.
    """
    if is_memory_manager_initialized():
        manager = await get_memory_manager()
        assert manager is not None, "Initialized but manager is None - critical state inconsistency"
        return manager

    # Create default dependencies using platformdirs-based paths
    try:
        vector_store = ChromaVectorStore(persist_directory=str(get_chroma_dir()))
        metadata_store = SQLiteMetadataStore(database_path=str(get_database_path()))
        graph_store = NetworkXGraphStore(graph_path=str(get_graph_path()))

        # Embedding service with explicit, logged fallback
        from ..core.embedding_service import (
            MockEmbeddingService,
            SentenceTransformerEmbeddingService,
        )

        try:
            embedding_service: EmbeddingService = SentenceTransformerEmbeddingService()
        except Exception as e:  # User-approved, transparent fallback
            logger.warning(
                "SentenceTransformer initialization failed; falling back to MockEmbeddingService",
                extra={"exception": str(e)},
            )
            embedding_service = MockEmbeddingService()

        similarity_calculator = SimilarityCalculator()

        # Initialize singleton and return instance
        return await initialize_memory_manager(
            vector_store=vector_store,
            metadata_store=metadata_store,
            graph_store=graph_store,
            embedding_service=embedding_service,
            similarity_calculator=similarity_calculator,
        )
    except Exception as e:
        # Explicit error reporting; no silent fallbacks
        logger.error(
            "Failed to create default memory manager dependencies",
            extra={"error_code": "MEMORY_MANAGER_CREATION_ERROR", "exception": str(e)},
        )
        return None
