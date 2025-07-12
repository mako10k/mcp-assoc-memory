#!/usr/bin/env python3
"""
Performance analysis tool for MCP Associative Memory Server
"""

import asyncio
import time
import json
from pathlib import Path
from typing import Dict, List, Any
import psutil
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_assoc_memory.core.memory_manager import MemoryManager
from mcp_assoc_memory.storage.metadata_store import SQLiteMetadataStore
from mcp_assoc_memory.storage.vector_store import ChromaVectorStore
from mcp_assoc_memory.config import get_config


class PerformanceProfiler:
    """Performance profiling utilities for the memory system"""
    
    def __init__(self):
        self.results = {}
        self.config = get_config()
    
    def measure_time(self, name: str):
        """Context manager for measuring execution time"""
        class TimeContext:
            def __init__(self, profiler, name):
                self.profiler = profiler
                self.name = name
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.perf_counter()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.perf_counter() - self.start_time
                self.profiler.results[self.name] = duration
                print(f"⏱️  {self.name}: {duration:.3f}s")
        
        return TimeContext(self, name)
    
    async def profile_memory_operations(self) -> Dict[str, Any]:
        """Profile core memory operations"""
        print("🔍 Profiling Memory Operations...")
        
        # Setup temporary test environment
        test_data_dir = Path("data/performance_test")
        test_data_dir.mkdir(exist_ok=True)
        
        # Initialize components
        metadata_store = SQLiteMetadataStore(str(test_data_dir / "test_metadata.db"))
        vector_store = ChromaVectorStore(persist_directory=str(test_data_dir / "test_chroma"))
        
        # Mock embedding service
        class MockEmbeddingService:
            async def get_embedding(self, text: str) -> List[float]:
                return [0.1] * 1536
            
            async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
                return [[0.1] * 1536 for _ in texts]
        
        mock_embedding = MockEmbeddingService()
        
        # Initialize stores
        with self.measure_time("metadata_store_init"):
            await metadata_store.initialize()
        
        with self.measure_time("vector_store_init"):
            await vector_store.initialize()
        
        # Mock graph store
        class MockGraphStore:
            async def initialize(self): pass
            async def close(self): pass
        
        mock_graph = MockGraphStore()
        
        # Create memory manager
        memory_manager = MemoryManager(
            vector_store=vector_store,
            metadata_store=metadata_store,
            graph_store=mock_graph,
            embedding_service=mock_embedding
        )
        
        with self.measure_time("memory_manager_init"):
            await memory_manager.initialize()
        
        # Test memory operations
        test_memories = [
            "Python is a programming language used for web development",
            "FastAPI is a modern web framework for building APIs with Python",
            "ChromaDB is a vector database for AI applications",
            "Machine learning models require training data",
            "REST APIs provide HTTP endpoints for data access"
        ]
        
        stored_memories = []
        
        # Measure storage performance
        with self.measure_time("store_5_memories"):
            for i, content in enumerate(test_memories):
                memory = await memory_manager.store_memory(
                    content=content,
                    scope=f"test/performance/{i}",
                    tags=["performance", "test"],
                    metadata={"index": i}
                )
                stored_memories.append(memory)
        
        # Measure search performance
        search_queries = [
            "programming language",
            "web framework",
            "vector database",
            "machine learning",
            "REST API"
        ]
        
        with self.measure_time("search_5_queries"):
            for query in search_queries:
                results = await memory_manager.search_memories(
                    query=query,
                    limit=10
                )
        
        # Measure single search performance
        with self.measure_time("single_search_detailed"):
            results = await memory_manager.search_memories(
                query="Python programming FastAPI",
                limit=10,
                min_score=0.1
            )
        
        # Measure retrieval performance
        if stored_memories and stored_memories[0] is not None:
            with self.measure_time("retrieve_memory_by_id"):
                memory = await memory_manager.get_memory(stored_memories[0].id)
        else:
            print("⚠️  No memories were stored successfully for retrieval test")
        
        # Cleanup
        await memory_manager.close()
        
        return self.results
    
    def analyze_system_resources(self) -> Dict[str, Any]:
        """Analyze current system resource usage"""
        print("📊 Analyzing System Resources...")
        
        # Memory analysis
        memory = psutil.virtual_memory()
        
        # CPU analysis
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Disk analysis
        disk = psutil.disk_usage('/')
        
        # Process analysis
        current_process = psutil.Process()
        process_info = {
            "memory_mb": current_process.memory_info().rss / (1024 * 1024),
            "cpu_percent": current_process.cpu_percent(),
            "threads": current_process.num_threads(),
            "open_files": len(current_process.open_files())
        }
        
        return {
            "system_memory": {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "used_percent": memory.percent
            },
            "cpu": {
                "cores": psutil.cpu_count(),
                "usage_percent": cpu_percent
            },
            "disk": {
                "total_gb": disk.total / (1024**3),
                "free_gb": disk.free / (1024**3),
                "used_percent": (disk.used / disk.total) * 100
            },
            "current_process": process_info
        }
    
    def analyze_data_sizes(self) -> Dict[str, Any]:
        """Analyze database and file sizes"""
        print("📁 Analyzing Data Sizes...")
        
        data_dir = Path("data")
        sizes = {}
        
        if data_dir.exists():
            # ChromaDB database
            chroma_files = list(data_dir.glob("**/*.sqlite3"))
            for chroma_file in chroma_files:
                if chroma_file.exists():
                    size_mb = chroma_file.stat().st_size / (1024 * 1024)
                    sizes[f"chroma_{chroma_file.name}"] = f"{size_mb:.2f} MB"
            
            # Metadata databases
            db_files = list(data_dir.glob("**/*.db"))
            for db_file in db_files:
                if db_file.exists():
                    size_mb = db_file.stat().st_size / (1024 * 1024)
                    sizes[f"metadata_{db_file.name}"] = f"{size_mb:.2f} MB"
            
            # Export files
            json_files = list(data_dir.glob("**/*.json"))
            for json_file in json_files:
                if json_file.exists():
                    size_mb = json_file.stat().st_size / (1024 * 1024)
                    sizes[f"export_{json_file.name}"] = f"{size_mb:.2f} MB"
        
        return sizes
    
    async def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run complete performance analysis"""
        print("🚀 Starting Comprehensive Performance Analysis...")
        print("=" * 60)
        
        start_time = time.perf_counter()
        
        # System resource analysis
        system_resources = self.analyze_system_resources()
        
        # Data size analysis
        data_sizes = self.analyze_data_sizes()
        
        # Memory operations profiling
        operation_timings = await self.profile_memory_operations()
        
        total_time = time.perf_counter() - start_time
        
        results = {
            "analysis_info": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_analysis_time": f"{total_time:.3f}s"
            },
            "system_resources": system_resources,
            "data_sizes": data_sizes,
            "operation_timings": operation_timings,
            "performance_score": self._calculate_performance_score(operation_timings)
        }
        
        return results
    
    def _calculate_performance_score(self, timings: Dict[str, float]) -> Dict[str, Any]:
        """Calculate overall performance score"""
        scores = {}
        
        # Storage performance (target: < 0.1s per memory)
        if "store_5_memories" in timings:
            avg_store_time = timings["store_5_memories"] / 5
            scores["storage_score"] = min(100, max(0, (0.1 - avg_store_time) / 0.1 * 100))
        
        # Search performance (target: < 0.5s per search)
        if "search_5_queries" in timings:
            avg_search_time = timings["search_5_queries"] / 5
            scores["search_score"] = min(100, max(0, (0.5 - avg_search_time) / 0.5 * 100))
        
        # Initialization performance (target: < 1s total)
        init_times = [
            timings.get("metadata_store_init", 0),
            timings.get("vector_store_init", 0),
            timings.get("memory_manager_init", 0)
        ]
        total_init_time = sum(init_times)
        scores["initialization_score"] = min(100, max(0, (1.0 - total_init_time) / 1.0 * 100))
        
        # Overall score
        if scores:
            scores["overall_score"] = sum(scores.values()) / len(scores)
        
        return scores


async def main():
    """Main performance analysis entry point"""
    profiler = PerformanceProfiler()
    
    try:
        results = await profiler.run_comprehensive_analysis()
        
        # Save results
        output_file = Path(".copilot-temp/performance_analysis.json")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE ANALYSIS COMPLETE")
        print("=" * 60)
        
        # Display key metrics
        print(f"🎯 Overall Performance Score: {results['performance_score'].get('overall_score', 0):.1f}/100")
        print(f"💾 Storage Score: {results['performance_score'].get('storage_score', 0):.1f}/100")
        print(f"🔍 Search Score: {results['performance_score'].get('search_score', 0):.1f}/100")
        print(f"⚡ Initialization Score: {results['performance_score'].get('initialization_score', 0):.1f}/100")
        
        print(f"\n📁 Full results saved to: {output_file}")
        
        # Performance recommendations
        print("\n🎯 PERFORMANCE RECOMMENDATIONS:")
        if results['performance_score'].get('storage_score', 0) < 70:
            print("• Consider optimizing memory storage operations")
        if results['performance_score'].get('search_score', 0) < 70:
            print("• Consider implementing search result caching")
        if results['performance_score'].get('initialization_score', 0) < 70:
            print("• Consider lazy initialization for faster startup")
        
        system_mem_usage = results['system_resources']['system_memory']['used_percent']
        if system_mem_usage > 80:
            print(f"• High memory usage detected ({system_mem_usage:.1f}%), consider memory optimization")
        
        return results
        
    except Exception as e:
        print(f"❌ Performance analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(main())
