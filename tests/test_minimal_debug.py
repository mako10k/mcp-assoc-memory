"""
Minimal test to isolate the exact hang location.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path


@pytest.mark.asyncio
async def test_minimal_chromadb():
    """Minimal ChromaDB test without any complex dependencies."""
    try:
        import chromadb
        
        with tempfile.TemporaryDirectory() as tmpdir:
            print("Creating ChromaDB client...")
            client = chromadb.PersistentClient(path=tmpdir)
            print("ChromaDB client created successfully")
            
            print("Creating collection...")
            collection = client.get_or_create_collection(
                name="test_minimal",
                metadata={"hnsw:space": "cosine"}
            )
            print("Collection created successfully")
            
            print("Adding test data...")
            collection.add(
                ids=["test1"],
                embeddings=[[0.1, 0.2, 0.3]],
                metadatas=[{"scope": "test"}]
            )
            print("Data added successfully")
            
            print("Querying data...")
            results = collection.query(
                query_embeddings=[[0.1, 0.2, 0.3]],
                n_results=1
            )
            print(f"Query completed: {len(results['ids'][0])} results")
            
            print("Test completed successfully!")
            
    except ImportError:
        pytest.skip("ChromaDB not available")


@pytest.mark.asyncio
async def test_asyncio_basic():
    """Test basic asyncio functionality."""
    print("Testing basic asyncio...")
    await asyncio.sleep(0.1)
    print("Basic asyncio test passed!")


if __name__ == "__main__":
    # Run directly for debugging
    async def main():
        print("Running minimal ChromaDB test...")
        await test_minimal_chromadb()
        
        print("Running basic asyncio test...")
        await test_asyncio_basic()
        
        print("All minimal tests passed!")
    
    asyncio.run(main())
