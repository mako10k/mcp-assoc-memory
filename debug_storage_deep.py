#!/usr/bin/env python3
"""
Deep debugging of storage components to identify why store_memory returns None
"""
import asyncio
import sys
import traceback
sys.path.insert(0, 'src')

async def test_storage_components():
    print("=== Deep Storage Component Testing ===")
    
    try:
        # Test embedding service first
        print("\n1. Testing Embedding Service...")
        from src.mcp_assoc_memory.core.embedding_service import SentenceTransformerEmbeddingService
        
        try:
            embedding_service = SentenceTransformerEmbeddingService()
            test_embedding = await embedding_service.get_embedding("test content")
            print(f"   SentenceTransformer embedding result: {type(test_embedding)}, shape: {test_embedding.shape if test_embedding is not None else 'None'}")
        except Exception as e:
            print(f"   SentenceTransformer failed: {e}")
            # Fallback to Mock
            from src.mcp_assoc_memory.core.embedding_service import MockEmbeddingService
            embedding_service = MockEmbeddingService()
            test_embedding = await embedding_service.get_embedding("test content")
            print(f"   Mock embedding result: {type(test_embedding)}, shape: {test_embedding.shape if test_embedding is not None else 'None'}")
        
        # Test individual storage components
        print("\n2. Testing Storage Components...")
        
        # Vector Store
        print("   Testing ChromaVectorStore...")
        from src.mcp_assoc_memory.storage.vector_store import ChromaVectorStore
        vector_store = ChromaVectorStore(persist_directory="data/chroma_db")
        await vector_store.initialize()
        print(f"   Vector store initialized: {hasattr(vector_store, '_collection')}")
        
        # Metadata Store
        print("   Testing SQLiteMetadataStore...")
        from src.mcp_assoc_memory.storage.metadata_store import SQLiteMetadataStore
        metadata_store = SQLiteMetadataStore(database_path="data/memory.db")
        await metadata_store.initialize()
        print(f"   Metadata store initialized: {hasattr(metadata_store, '_connection')}")
        
        # Graph Store
        print("   Testing NetworkXGraphStore...")
        from src.mcp_assoc_memory.storage.graph_store import NetworkXGraphStore
        graph_store = NetworkXGraphStore(graph_path="data/memory_graph.pkl")
        await graph_store.initialize()
        print(f"   Graph store initialized: {hasattr(graph_store, '_graph')}")
        
        # Test storage operations individually
        print("\n3. Testing Individual Storage Operations...")
        
        # Create test memory
        from src.mcp_assoc_memory.core.models import Memory
        import uuid
        
        test_memory = Memory(
            id=str(uuid.uuid4()),
            content="Test content for individual storage operations",
            scope="test/individual",
            metadata={"scope": "test/individual"}
        )
        
        # Test vector storage
        if test_embedding is not None:
            print(f"   Testing vector store operation...")
            try:
                vector_result = await vector_store.store_embedding(test_memory.id, test_embedding, test_memory.to_dict())
                print(f"   Vector store result: {vector_result}")
            except Exception as e:
                print(f"   Vector store failed: {e}")
                traceback.print_exc()
        
        # Test metadata storage
        print(f"   Testing metadata store operation...")
        try:
            metadata_result = await metadata_store.store_memory(test_memory)
            print(f"   Metadata store result: {metadata_result}")
        except Exception as e:
            print(f"   Metadata store failed: {e}")
            traceback.print_exc()
        
        # Test graph storage
        print(f"   Testing graph store operation...")
        try:
            graph_result = await graph_store.add_memory_node(test_memory)
            print(f"   Graph store result: {graph_result}")
        except Exception as e:
            print(f"   Graph store failed: {e}")
            traceback.print_exc()
        
        print("\n4. Testing Parallel Operations...")
        
        # Test parallel operations like in memory_manager_core
        test_memory2 = Memory(
            id=str(uuid.uuid4()),
            content="Test content for parallel operations",
            scope="test/parallel",
            metadata={"scope": "test/parallel"}
        )
        
        storage_tasks = []
        if test_embedding is not None:
            storage_tasks.append(vector_store.store_embedding(test_memory2.id, test_embedding, test_memory2.to_dict()))
        storage_tasks.append(metadata_store.store_memory(test_memory2))
        storage_tasks.append(graph_store.add_memory_node(test_memory2))
        
        print(f"   Executing {len(storage_tasks)} parallel tasks...")
        results = await asyncio.gather(*storage_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            print(f"   Task {i}: {type(result)} = {result}")
            if isinstance(result, Exception):
                print(f"     Exception: {result}")
                traceback.print_exception(type(result), result, result.__traceback__)
        
    except Exception as e:
        print(f"ERROR in deep testing: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_storage_components())
