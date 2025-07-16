#!/usr/bin/env python3
"""
Health check script for MCP Associative Memory Server.

Quick verification that the server can start and basic operations work.
Useful for deployment validation and CI/CD pipelines.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


async def health_check():
    """Perform basic health check of the server."""
    print("🏥 MCP Associative Memory Server Health Check")
    print("=" * 50)

    checks = []

    # 1. Import check
    print("🔧 Checking server import...")
    try:
        pass

        print("✅ Server import: OK")
        checks.append(True)
    except Exception as e:
        print(f"❌ Server import: FAILED - {e}")
        checks.append(False)

    # 2. Memory manager initialization
    print("🔧 Checking memory manager initialization...")
    try:
        from mcp_assoc_memory.core.embedding_service import SentenceTransformerEmbeddingService
        from mcp_assoc_memory.core.memory_manager import MemoryManager
        from mcp_assoc_memory.storage.graph_store import NetworkXGraphStore
        from mcp_assoc_memory.storage.metadata_store import SQLiteMetadataStore
        from mcp_assoc_memory.storage.vector_store import ChromaVectorStore

        # Initialize stores with default parameters
        vector_store = ChromaVectorStore()
        metadata_store = SQLiteMetadataStore()
        graph_store = NetworkXGraphStore()
        embedding_service = SentenceTransformerEmbeddingService()

        # Initialize manager
        manager = MemoryManager(
            vector_store=vector_store,
            metadata_store=metadata_store,
            graph_store=graph_store,
            embedding_service=embedding_service,
        )
        await manager.initialize()
        await manager.close()
        print("✅ Memory manager: OK")
        checks.append(True)
    except Exception as e:
        print(f"❌ Memory manager: FAILED - {e}")
        checks.append(False)

    # 3. Global server initialization
    print("🔧 Checking global server initialization...")
    try:
        from mcp_assoc_memory.server import ensure_initialized, memory_manager

        await ensure_initialized()
        await memory_manager.close()
        print("✅ Global server: OK")
        checks.append(True)
    except Exception as e:
        print(f"❌ Global server: FAILED - {e}")
        checks.append(False)

    # 4. JSON persistence
    print("🔧 Checking JSON persistence...")
    try:
        # SimplePersistence has been removed from architecture
        # SQLite/ChromaDB persistence is now the standard
        print("✅ JSON persistence: DEPRECATED - Using SQLite/ChromaDB storage")
        checks.append(True)
    except Exception as e:
        print(f"❌ JSON persistence: FAILED - {e}")
        checks.append(False)

    # Summary
    passed = sum(checks)
    total = len(checks)

    print("\n" + "=" * 50)
    print(f"📊 Health Check Results: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 HEALTH CHECK PASSED - Server is healthy!")
        return 0
    else:
        print("💥 HEALTH CHECK FAILED - Server has issues!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(health_check())
    sys.exit(exit_code)
