#!/usr/bin/env python3
"""
Optimized performance analysis tool with batch processing tests
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

import psutil

from mcp_assoc_memory.config import get_config
from mcp_assoc_memory.core.memory_manager import MemoryManager
from mcp_assoc_memory.storage.metadata_store import SQLiteMetadataStore
from mcp_assoc_memory.storage.vector_store import ChromaVectorStore

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class OptimizedPerformanceProfiler:
    """Enhanced performance profiling with batch processing tests"""

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

    async def profile_batch_operations(self) -> Dict[str, float]:
        """Profile both individual and batch storage operations"""
        print("🔄 Profiling Batch vs Individual Operations...")

        # Test setup
        metadata_store = SQLiteMetadataStore("./data/test_memory.db")
        vector_store = ChromaVectorStore()

        # Mock embedding service
        class MockEmbeddingService:
            async def get_embedding(self, text: str):
                # Simulate embedding generation delay
                await asyncio.sleep(0.001)  # 1ms delay to simulate real embedding
                return [0.1] * 384  # Mock 384-dimensional embedding

        mock_embedding = MockEmbeddingService()

        # Initialize stores
        with self.measure_time("optimized_metadata_store_init"):
            await metadata_store.initialize()

        with self.measure_time("optimized_vector_store_init"):
            await vector_store.initialize()

        # Mock graph store
        class MockGraphStore:
            async def initialize(self):
                pass

            async def close(self):
                pass

            async def add_memory_node(self, memory):
                return True

        mock_graph = MockGraphStore()

        # Create memory manager
        memory_manager = MemoryManager(
            vector_store=vector_store,
            metadata_store=metadata_store,
            graph_store=mock_graph,
            embedding_service=mock_embedding,
        )

        with self.measure_time("optimized_memory_manager_init"):
            await memory_manager.initialize()

        # Test individual storage
        individual_memories = [
            f"Individual memory test {i}: Python programming concepts and best practices" for i in range(10)
        ]

        with self.measure_time("individual_store_10_memories"):
            for i, content in enumerate(individual_memories):
                await memory_manager.store_memory(
                    content=content,
                    scope=f"test/individual/{i}",
                    tags=["performance", "individual"],
                    metadata={"test_type": "individual", "index": i},
                )

        # Test batch storage (if method exists)
        if hasattr(memory_manager, "store_memories_batch"):
            batch_data = [
                {
                    "content": f"Batch memory test {i}: Advanced Python patterns and optimization techniques",
                    "scope": f"test/batch/{i}",
                    "tags": ["performance", "batch"],
                    "metadata": {"test_type": "batch", "index": i},
                }
                for i in range(10)
            ]

            with self.measure_time("batch_store_10_memories"):
                await memory_manager.store_memories_batch(batch_data)

        # Test search performance on larger dataset
        search_queries = [
            "Python programming concepts",
            "optimization techniques",
            "advanced patterns",
            "best practices",
            "performance testing",
        ]

        with self.measure_time("optimized_search_5_queries"):
            for query in search_queries:
                await memory_manager.search_memories(query=query, limit=10)

        # Test concurrent operations
        with self.measure_time("concurrent_10_searches"):
            search_tasks = [
                memory_manager.search_memories(query=query, limit=5)
                for query in search_queries * 2  # 10 searches total
            ]
            await asyncio.gather(*search_tasks)

        # Cleanup
        await memory_manager.close()

        return self.results

    def calculate_improvement_metrics(self, timings: Dict[str, float]) -> Dict[str, Any]:
        """Calculate performance improvements from optimizations"""
        metrics = {}

        # Compare individual vs batch storage if both exist
        if "individual_store_10_memories" in timings and "batch_store_10_memories" in timings:
            individual_time = timings["individual_store_10_memories"]
            batch_time = timings["batch_store_10_memories"]

            improvement_factor = individual_time / batch_time if batch_time > 0 else 1
            time_saved = individual_time - batch_time

            metrics["batch_performance"] = {
                "individual_time": individual_time,
                "batch_time": batch_time,
                "improvement_factor": improvement_factor,
                "time_saved_seconds": time_saved,
                "time_saved_percent": (time_saved / individual_time) * 100 if individual_time > 0 else 0,
            }

        # Search performance analysis
        if "optimized_search_5_queries" in timings and "concurrent_10_searches" in timings:
            sequential_time = timings["optimized_search_5_queries"]
            concurrent_time = timings["concurrent_10_searches"]

            # Normalize to per-search time
            sequential_per_search = sequential_time / 5
            concurrent_per_search = concurrent_time / 10

            metrics["search_concurrency"] = {
                "sequential_per_search": sequential_per_search,
                "concurrent_per_search": concurrent_per_search,
                "concurrency_benefit": sequential_per_search - concurrent_per_search,
                "efficiency_gain_percent": (
                    ((sequential_per_search - concurrent_per_search) / sequential_per_search) * 100
                    if sequential_per_search > 0
                    else 0
                ),
            }

        return metrics

    async def run_optimized_analysis(self) -> Dict[str, Any]:
        """Run complete optimized performance analysis"""
        print("🚀 Starting Optimized Performance Analysis...")
        print("=" * 60)

        start_time = time.perf_counter()

        # System resource analysis
        system_resources = self.analyze_system_resources()

        # Data size analysis
        data_sizes = self.analyze_data_sizes()

        # Enhanced memory operations profiling
        operation_timings = await self.profile_batch_operations()

        # Calculate improvement metrics
        improvement_metrics = self.calculate_improvement_metrics(operation_timings)

        total_time = time.perf_counter() - start_time

        results = {
            "analysis_info": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_analysis_time": f"{total_time:.3f}s",
                "test_type": "optimized_batch_analysis",
            },
            "system_resources": system_resources,
            "data_sizes": data_sizes,
            "operation_timings": operation_timings,
            "improvement_metrics": improvement_metrics,
            "performance_score": self._calculate_optimized_performance_score(operation_timings),
        }

        return results

    def analyze_system_resources(self) -> Dict[str, Any]:
        """Analyze current system resource usage"""
        print("📊 Analyzing System Resources...")

        # Memory analysis
        memory = psutil.virtual_memory()

        # CPU analysis
        cpu_percent = psutil.cpu_percent(interval=1)

        # Disk analysis
        disk = psutil.disk_usage("/")

        # Process analysis
        current_process = psutil.Process()
        process_info = {
            "memory_mb": current_process.memory_info().rss / (1024 * 1024),
            "cpu_percent": current_process.cpu_percent(),
            "threads": current_process.num_threads(),
            "open_files": len(current_process.open_files()),
        }

        return {
            "system_memory": {
                "total_gb": memory.total / (1024**3),
                "available_gb": memory.available / (1024**3),
                "used_percent": memory.percent,
            },
            "cpu": {"cores": psutil.cpu_count(), "usage_percent": cpu_percent},
            "disk": {
                "total_gb": disk.total / (1024**3),
                "free_gb": disk.free / (1024**3),
                "used_percent": (disk.used / disk.total) * 100,
            },
            "current_process": process_info,
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

        return sizes

    def _calculate_optimized_performance_score(self, timings: Dict[str, float]) -> Dict[str, Any]:
        """Calculate optimized performance scores"""
        scores = {}

        # Batch storage performance
        if "batch_store_10_memories" in timings:
            batch_time = timings["batch_store_10_memories"]
            avg_batch_time = batch_time / 10
            # Target: < 0.05s per memory for batch operations
            scores["batch_storage_score"] = min(100, max(0, (0.05 - avg_batch_time) / 0.05 * 100))

        # Individual storage performance
        if "individual_store_10_memories" in timings:
            individual_time = timings["individual_store_10_memories"]
            avg_individual_time = individual_time / 10
            # Target: < 0.08s per memory for individual operations
            scores["individual_storage_score"] = min(100, max(0, (0.08 - avg_individual_time) / 0.08 * 100))

        # Search performance
        if "optimized_search_5_queries" in timings:
            search_time = timings["optimized_search_5_queries"]
            avg_search_time = search_time / 5
            # Target: < 0.05s per search
            scores["search_score"] = min(100, max(0, (0.05 - avg_search_time) / 0.05 * 100))

        # Concurrent search performance
        if "concurrent_10_searches" in timings:
            concurrent_time = timings["concurrent_10_searches"]
            avg_concurrent_time = concurrent_time / 10
            # Target: < 0.03s per concurrent search (should be faster due to parallelization)
            scores["concurrent_search_score"] = min(100, max(0, (0.03 - avg_concurrent_time) / 0.03 * 100))

        # Overall score
        if scores:
            scores["overall_optimized_score"] = sum(scores.values()) / len(scores)

        return scores


async def main():
    """Main optimized performance analysis entry point"""
    profiler = OptimizedPerformanceProfiler()

    try:
        results = await profiler.run_optimized_analysis()

        # Save results
        output_file = Path(".copilot-temp/optimized_performance_analysis.json")
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print("\n" + "=" * 60)
        print("📊 OPTIMIZED PERFORMANCE ANALYSIS COMPLETE")
        print("=" * 60)

        # Display key metrics
        scores = results["performance_score"]
        print(f"🎯 Overall Optimized Score: {scores.get('overall_optimized_score', 0):.1f}/100")

        if "batch_storage_score" in scores:
            print(f"📦 Batch Storage Score: {scores['batch_storage_score']:.1f}/100")
        if "individual_storage_score" in scores:
            print(f"📝 Individual Storage Score: {scores['individual_storage_score']:.1f}/100")
        if "search_score" in scores:
            print(f"🔍 Search Score: {scores['search_score']:.1f}/100")
        if "concurrent_search_score" in scores:
            print(f"⚡ Concurrent Search Score: {scores['concurrent_search_score']:.1f}/100")

        # Display improvement metrics
        if "improvement_metrics" in results:
            metrics = results["improvement_metrics"]

            if "batch_performance" in metrics:
                batch = metrics["batch_performance"]
                print("\n🚀 BATCH PERFORMANCE IMPROVEMENTS:")
                print(f"• Individual storage: {batch['individual_time']:.3f}s")
                print(f"• Batch storage: {batch['batch_time']:.3f}s")
                print(f"• Improvement factor: {batch['improvement_factor']:.1f}x")
                print(f"• Time saved: {batch['time_saved_percent']:.1f}%")

            if "search_concurrency" in metrics:
                search = metrics["search_concurrency"]
                print("\n⚡ SEARCH CONCURRENCY BENEFITS:")
                print(f"• Sequential search: {search['sequential_per_search']:.3f}s per query")
                print(f"• Concurrent search: {search['concurrent_per_search']:.3f}s per query")
                print(f"• Efficiency gain: {search['efficiency_gain_percent']:.1f}%")

        print(f"\n📁 Full results saved to: {output_file}")

        return results

    except Exception as e:
        print(f"❌ Optimized performance analysis failed: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(main())
