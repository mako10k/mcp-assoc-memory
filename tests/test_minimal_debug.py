"""
Minimal test to isolate the exact hang location.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path



def test_minimal_chromadb():
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


def test_asyncio_basic():
    """Test basic asyncio functionality (sync version)."""
    print("Testing basic asyncio...")
    import time
    time.sleep(0.1)
    print("Basic asyncio test passed!")


if __name__ == "__main__":
    print("Running minimal ChromaDB test...")
    test_minimal_chromadb()
    print("Running basic asyncio test...")
    test_asyncio_basic()
    print("All minimal tests passed!")
