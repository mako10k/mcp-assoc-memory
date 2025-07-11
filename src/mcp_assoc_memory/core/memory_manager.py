"""
Unified Memory Manager - Integration of all memory management functionality
Combines core CRUD, search, associations, diversified search, and admin functions
"""

from typing import Optional

from ..core.embedding_service import EmbeddingService
from ..core.similarity import SimilarityCalculator
from ..storage.base import BaseGraphStore, BaseMetadataStore, BaseVectorStore
from .memory_manager_admin import MemoryManagerAdmin
from .memory_manager_associations import MemoryManagerAssociations
from .memory_manager_core import MemoryManagerCore
from .memory_manager_diversified import MemoryManagerDiversified
from .memory_manager_search import MemoryManagerSearch


class MemoryManager(
    MemoryManagerCore,
    MemoryManagerSearch,
    MemoryManagerAssociations,
    MemoryManagerDiversified,
    MemoryManagerAdmin
):
    """
    Unified Memory Manager integrating all functionality
    
    This class combines all memory management capabilities:
    - Core CRUD operations (MemoryManagerCore)
    - Search functionality (MemoryManagerSearch) 
    - Association management (MemoryManagerAssociations)
    - Diversified search algorithms (MemoryManagerDiversified)
    - Administrative functions (MemoryManagerAdmin)
    
    Usage:
        memory_manager = MemoryManager(
            vector_store=vector_store,
            metadata_store=metadata_store,
            graph_store=graph_store,
            embedding_service=embedding_service
        )
        
        await memory_manager.initialize()
        
        # All functionality is now available:
        memory = await memory_manager.store_memory(content="example")
        results = await memory_manager.search_memories("query")
        diverse_results = await memory_manager.diversified_similarity_search("query")
        stats = await memory_manager.get_statistics()
    """

    def __init__(
        self,
        vector_store: BaseVectorStore,
        metadata_store: BaseMetadataStore,
        graph_store: BaseGraphStore,
        embedding_service: EmbeddingService,
        similarity_calculator: Optional[SimilarityCalculator] = None
    ):
        """
        Initialize unified memory manager
        
        Args:
            vector_store: Vector storage backend
            metadata_store: Metadata storage backend  
            graph_store: Graph storage backend
            embedding_service: Embedding generation service
            similarity_calculator: Similarity calculation service (optional)
        """
        # Initialize the core functionality
        MemoryManagerCore.__init__(
            self,
            vector_store=vector_store,
            metadata_store=metadata_store,
            graph_store=graph_store,
            embedding_service=embedding_service,
            similarity_calculator=similarity_calculator
        )
        
        # All other mixins inherit the same attributes
        # No additional initialization needed for mixins
        
    async def health_check(self) -> dict:
        """Comprehensive health check for all components"""
        try:
            core_health = await self.get_statistics()
            performance_metrics = await self.get_performance_metrics()
            
            return {
                "status": "healthy",
                "components": {
                    "core": core_health,
                    "performance": performance_metrics
                },
                "integrated_modules": [
                    "MemoryManagerCore",
                    "MemoryManagerSearch", 
                    "MemoryManagerAssociations",
                    "MemoryManagerDiversified",
                    "MemoryManagerAdmin"
                ]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def get_available_methods(self) -> dict:
        """Get all available methods organized by module"""
        return {
            "core": [
                "store_memory", "get_memory", "update_memory", "delete_memory",
                "check_content_duplicate", "initialize", "close"
            ],
            "search": [
                "search_memories", "semantic_search", "search_by_tags",
                "search_by_timerange", "advanced_search", "find_similar_memories",
                "search_by_scope_pattern", "full_text_search", "search_by_metadata",
                "search_recently_accessed", "search_by_category", "fuzzy_search"
            ],
            "associations": [
                "get_associations", "create_manual_association", "delete_association",
                "update_association_strength", "get_related_memories", "rebuild_associations"
            ],
            "diversified": [
                "diversified_similarity_search", "diverse_tag_search",
                "diverse_category_search", "explore_knowledge_space"
            ],
            "admin": [
                "memory_map", "scope_graph", "timeline", "category_chart",
                "stats_dashboard", "get_performance_metrics", "move_memories_to_scope",
                "batch_update_memories", "get_statistics", "get_memory_stats",
                "export_memories", "import_memories", "change_memory_scope",
                "batch_delete_memories", "cleanup_database", "get_all_scopes"
            ]
        }


# Backward compatibility aliases
# These ensure existing code continues to work
MemoryEngine = MemoryManager  # Legacy alias