"""
Singleton Memory Manager - Ensures single instance across the application
Provides thread-safe, lazy initialization of MemoryManager
"""

import asyncio
import threading
from typing import Optional

from ..core.embedding_service import EmbeddingService
from ..core.memory_manager import MemoryManager
from ..core.similarity import SimilarityCalculator
from ..storage.base import BaseGraphStore, BaseMetadataStore, BaseVectorStore


class SingletonMemoryManager:
    """
    Singleton wrapper for MemoryManager to ensure single instance across application
    
    Features:
    - Thread-safe lazy initialization
    - Async-safe singleton pattern
    - Automatic cleanup on shutdown
    - Dependency injection support
    """
    
    _instance: Optional['SingletonMemoryManager'] = None
    _lock = threading.Lock()
    _memory_manager: Optional[MemoryManager] = None
    _initialized = False
    _initialization_lock = asyncio.Lock()
    
    def __new__(cls) -> 'SingletonMemoryManager':
        """Ensure only one instance exists"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize singleton (called only once)"""
        # Prevent re-initialization
        if hasattr(self, '_singleton_initialized'):
            return
        self._singleton_initialized = True
    
    async def initialize(
        self,
        vector_store: BaseVectorStore,
        metadata_store: BaseMetadataStore,
        graph_store: BaseGraphStore,
        embedding_service: EmbeddingService,
        similarity_calculator: Optional[SimilarityCalculator] = None,
        force_reinit: bool = False
    ) -> MemoryManager:
        """
        Initialize or get the MemoryManager instance
        
        Args:
            vector_store: Vector storage backend
            metadata_store: Metadata storage backend
            graph_store: Graph storage backend
            embedding_service: Embedding generation service
            similarity_calculator: Similarity calculation service (optional)
            force_reinit: Force re-initialization even if already initialized
            
        Returns:
            MemoryManager: The singleton instance
        """
        async with self._initialization_lock:
            if self._memory_manager is not None and not force_reinit:
                return self._memory_manager
            
            # Close existing instance if force reinit
            if force_reinit and self._memory_manager is not None:
                await self._memory_manager.close()
                self._memory_manager = None
                self._initialized = False
            
            # Create new instance
            self._memory_manager = MemoryManager(
                vector_store=vector_store,
                metadata_store=metadata_store,
                graph_store=graph_store,
                embedding_service=embedding_service,
                similarity_calculator=similarity_calculator,
            )
            
            # Initialize the memory manager
            await self._memory_manager.initialize()
            self._initialized = True
            
            return self._memory_manager
    
    def get_instance(self) -> Optional[MemoryManager]:
        """
        Get the MemoryManager instance (non-async)
        
        Returns:
            MemoryManager if initialized, None otherwise
        """
        return self._memory_manager
    
    async def get_or_create_instance(
        self,
        vector_store: Optional[BaseVectorStore] = None,
        metadata_store: Optional[BaseMetadataStore] = None,
        graph_store: Optional[BaseGraphStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        similarity_calculator: Optional[SimilarityCalculator] = None,
    ) -> Optional[MemoryManager]:
        """
        Get existing instance or create new one if dependencies are provided
        
        Args:
            vector_store: Vector storage backend (required for creation)
            metadata_store: Metadata storage backend (required for creation)
            graph_store: Graph storage backend (required for creation)
            embedding_service: Embedding generation service (required for creation)
            similarity_calculator: Similarity calculation service (optional)
            
        Returns:
            MemoryManager if available or successfully created, None otherwise
        """
        if self._memory_manager is not None:
            return self._memory_manager
        
        # Try to create if all required dependencies are provided
        if all([vector_store, metadata_store, graph_store, embedding_service]):
            return await self.initialize(
                vector_store=vector_store,
                metadata_store=metadata_store,
                graph_store=graph_store,
                embedding_service=embedding_service,
                similarity_calculator=similarity_calculator,
            )
        
        return None
    
    def is_initialized(self) -> bool:
        """Check if the MemoryManager is initialized"""
        return self._initialized and self._memory_manager is not None
    
    async def close(self) -> None:
        """Close and cleanup the MemoryManager instance"""
        async with self._initialization_lock:
            if self._memory_manager is not None:
                await self._memory_manager.close()
                self._memory_manager = None
                self._initialized = False
    
    async def reset(self) -> None:
        """Reset the singleton (for testing purposes)"""
        await self.close()
        with self._lock:
            self.__class__._instance = None
    
    def get_status(self) -> dict:
        """Get status information about the singleton"""
        return {
            "singleton_initialized": hasattr(self, '_singleton_initialized'),
            "memory_manager_exists": self._memory_manager is not None,
            "memory_manager_initialized": self._initialized,
            "memory_manager_type": str(type(self._memory_manager)) if self._memory_manager else None,
            "instance_id": id(self),
        }


# Global singleton instance
_singleton_manager = SingletonMemoryManager()


def get_singleton_manager() -> SingletonMemoryManager:
    """Get the global singleton manager instance"""
    return _singleton_manager


async def get_memory_manager() -> Optional[MemoryManager]:
    """Get the MemoryManager instance from singleton"""
    return _singleton_manager.get_instance()


async def initialize_memory_manager(
    vector_store: BaseVectorStore,
    metadata_store: BaseMetadataStore,
    graph_store: BaseGraphStore,
    embedding_service: EmbeddingService,
    similarity_calculator: Optional[SimilarityCalculator] = None,
    force_reinit: bool = False
) -> MemoryManager:
    """Initialize the global MemoryManager singleton"""
    return await _singleton_manager.initialize(
        vector_store=vector_store,
        metadata_store=metadata_store,
        graph_store=graph_store,
        embedding_service=embedding_service,
        similarity_calculator=similarity_calculator,
        force_reinit=force_reinit,
    )


async def close_memory_manager() -> None:
    """Close the global MemoryManager singleton"""
    await _singleton_manager.close()


def is_memory_manager_initialized() -> bool:
    """Check if the global MemoryManager is initialized"""
    return _singleton_manager.is_initialized()


async def get_or_create_memory_manager() -> Optional[MemoryManager]:
    """
    Unified function to get or create memory manager with robust fallback
    
    This replaces the duplicated _get_or_create_memory_manager functions
    in various tool modules to ensure consistent behavior.
    
    Returns:
        MemoryManager instance if available, None otherwise
    """
    # Try to get from singleton first
    try:
        if is_memory_manager_initialized():
            return await get_memory_manager()
    except Exception:
        pass  # Fall through to initialization
    
    # Initialize singleton if not already done
    try:
        from ..storage.vector_store import ChromaVectorStore
        from ..storage.metadata_store import SQLiteMetadataStore
        from ..storage.graph_store import NetworkXGraphStore
        from ..core.embedding_service import EmbeddingService
        from ..core.similarity import SimilarityCalculator
        
        # Create dependencies
        vector_store = ChromaVectorStore(persist_directory="data/chroma_db")
        metadata_store = SQLiteMetadataStore(database_path="data/memory.db")
        graph_store = NetworkXGraphStore(graph_path="data/memory_graph.pkl")
        
        embedding_service = EmbeddingService()
        similarity_calculator = SimilarityCalculator()
        
        # Initialize singleton memory manager
        return await initialize_memory_manager(
            vector_store=vector_store,
            metadata_store=metadata_store,
            graph_store=graph_store,
            embedding_service=embedding_service,
            similarity_calculator=similarity_calculator,
        )
        
    except Exception as e:
        # Import logging for error reporting
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(
                "Failed to create memory manager",
                extra={"error_code": "MEMORY_MANAGER_CREATION_ERROR", "exception": str(e)},
            )
        except ImportError:
            # Fallback if logger not available
            print(f"Failed to create memory manager: {e}")
        return None
