"""
Centralized dependency injection system for MCP tools
"""

from typing import Any, Dict, Optional
from ..core.memory_manager import MemoryManager


class DependencyManager:
    """Centralized dependency manager for all MCP tools"""
    
    _instance: Optional['DependencyManager'] = None
    _memory_manager: Optional[MemoryManager] = None
    _memory_storage: Optional[Dict[str, Any]] = None
    _persistence: Optional[Any] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'DependencyManager':
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def set_dependencies(
        self,
        memory_manager: MemoryManager,
        memory_storage: Dict[str, Any],
        persistence: Any
    ) -> None:
        """Set dependencies for all tools"""
        self._memory_manager = memory_manager
        self._memory_storage = memory_storage
        self._persistence = persistence
        self._initialized = False  # Reset initialization flag
    
    @property
    def memory_manager(self) -> Optional[MemoryManager]:
        """Get memory manager instance"""
        return self._memory_manager
    
    @property
    def memory_storage(self) -> Optional[Dict[str, Any]]:
        """Get memory storage instance"""
        return self._memory_storage
    
    @property
    def persistence(self) -> Optional[Any]:
        """Get persistence instance"""
        return self._persistence
    
    @property
    def is_memory_manager_available(self) -> bool:
        """Check if memory manager is available"""
        return self._memory_manager is not None
    
    async def ensure_initialized(self) -> None:
        """Ensure memory manager is initialized"""
        if not self._initialized and self._memory_manager:
            try:
                await self._memory_manager.initialize()
                self._initialized = True
                # Verify basic initialization
                if not hasattr(self._memory_manager, 'vector_store') or self._memory_manager.vector_store is None:
                    raise RuntimeError("Vector store not initialized after initialization")
            except Exception as e:
                # Reset flag to allow retry
                self._initialized = False
                raise RuntimeError(f"Memory manager initialization failed: {e}")
        
        # Final check - if memory_manager is still None, raise error with helpful message
        if self._memory_manager is None:
            raise RuntimeError(
                "Memory manager is not initialized. This suggests a dependency injection issue. "
                "Please ensure the MCP server is properly started and set_dependencies() has been called."
            )


# Global singleton instance
dependencies = DependencyManager()


def get_memory_manager() -> Optional[MemoryManager]:
    """Get memory manager instance"""
    return dependencies.memory_manager


def get_memory_storage() -> Optional[Dict[str, Any]]:
    """Get memory storage instance"""
    return dependencies.memory_storage


def get_persistence() -> Optional[Any]:
    """Get persistence instance"""
    return dependencies.persistence


def set_global_dependencies(
    memory_manager: MemoryManager,
    memory_storage: Dict[str, Any],
    persistence: Any
) -> None:
    """Set global dependencies for all tools"""
    dependencies.set_dependencies(memory_manager, memory_storage, persistence)


async def ensure_dependencies_initialized() -> None:
    """Ensure all dependencies are initialized"""
    await dependencies.ensure_initialized()
