"""
Simplified test to isolate the ChromaDB initialization hang issue.
"""

import pytest
import tempfile
import asyncio
from pathlib import Path


@pytest.mark.asyncio
async def test_chromadb_simple_init():
    """Test ChromaDB initialization in isolation."""
    try:
        import chromadb

        with tempfile.TemporaryDirectory() as tmpdir:
            # Use new ChromaDB client API
            client = chromadb.PersistentClient(path=tmpdir)

            # Test collection creation without asyncio.run_in_executor
            collection = client.get_or_create_collection(
                name="test_collection",
                metadata={"hnsw:space": "cosine"}
            )

            assert collection is not None
            print("ChromaDB simple initialization successful")

            # Cleanup
            client.reset()

    except ImportError:
        pytest.skip("ChromaDB not available")


@pytest.mark.asyncio
async def test_chromadb_async_executor():
    """Test ChromaDB with run_in_executor (current implementation)."""
    try:
        import chromadb

        with tempfile.TemporaryDirectory() as tmpdir:
            client = chromadb.PersistentClient(path=tmpdir)

            # Test with run_in_executor (might cause hang)
            collection = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.get_or_create_collection(
                    name="test_collection",
                    metadata={"hnsw:space": "cosine"}
                )
            )

            assert collection is not None
            print("ChromaDB async executor initialization successful")

            # Cleanup
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.reset()
            )

    except ImportError:
        pytest.skip("ChromaDB not available")


if __name__ == "__main__":
    # Run directly for quick testing
    import sys

    async def main():
        print("Testing ChromaDB simple init...")
        await test_chromadb_simple_init()

        print("Testing ChromaDB async executor...")
        await test_chromadb_async_executor()

        print("All ChromaDB tests passed!")

    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
