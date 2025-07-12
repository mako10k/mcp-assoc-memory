"""
Database connection pool for optimized SQLite operations
"""

import asyncio
from pathlib import Path
from typing import Any, AsyncContextManager, Optional

import aiosqlite

from ..utils.logging import get_memory_logger

logger = get_memory_logger(__name__)


class DatabasePool:
    """Connection pool for SQLite database operations"""

    def __init__(self, database_path: str, max_connections: int = 5, timeout: float = 30.0):
        self.database_path = database_path
        self.max_connections = max_connections
        self.timeout = timeout
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_connections)
        self._created_connections = 0
        self._lock = asyncio.Lock()

        # Ensure database directory exists
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        """Initialize the connection pool"""
        logger.info(f"Initializing database pool with {self.max_connections} connections")

        # Pre-create initial connections
        for _ in range(min(2, self.max_connections)):  # Start with 2 connections
            conn = await self._create_connection()
            await self._pool.put(conn)

    async def _create_connection(self) -> aiosqlite.Connection:
        """Create a new database connection with optimizations"""
        conn = await aiosqlite.connect(self.database_path, timeout=self.timeout)

        # Enable performance optimizations
        await conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for concurrency
        await conn.execute("PRAGMA synchronous=NORMAL")  # Balanced durability/performance
        await conn.execute("PRAGMA cache_size=10000")  # Larger cache for better performance
        await conn.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
        await conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory mapping

        self._created_connections += 1
        logger.debug(f"Created database connection {self._created_connections}")

        return conn

    async def get_connection(self) -> AsyncContextManager[aiosqlite.Connection]:
        """Get a connection from the pool"""

        class ConnectionManager:
            def __init__(self, pool: "DatabasePool"):
                self.pool = pool
                self.connection: Optional[aiosqlite.Connection] = None

            async def __aenter__(self) -> aiosqlite.Connection:
                try:
                    # Try to get an existing connection from pool
                    self.connection = await asyncio.wait_for(self.pool._pool.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    # Create new connection if pool is empty and under limit
                    async with self.pool._lock:
                        if self.pool._created_connections < self.pool.max_connections:
                            self.connection = await self.pool._create_connection()
                        else:
                            # Wait for an available connection
                            self.connection = await self.pool._pool.get()

                if self.connection is None:
                    raise RuntimeError("Failed to get database connection")
                return self.connection

            async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
                if self.connection:
                    # Return connection to pool
                    try:
                        await self.pool._pool.put(self.connection)
                    except asyncio.QueueFull:
                        # Pool is full, close the connection
                        await self.connection.close()
                        self.pool._created_connections -= 1

        return ConnectionManager(self)

    async def close(self) -> None:
        """Close all connections in the pool"""
        logger.info("Closing database connection pool")

        # Close all connections in the pool
        while not self._pool.empty():
            try:
                conn = await asyncio.wait_for(self._pool.get(), timeout=1.0)
                await conn.close()
                self._created_connections -= 1
            except asyncio.TimeoutError:
                break

        logger.info(f"Closed {self._created_connections} database connections")


# Global pool instance
_database_pools = {}


async def get_database_pool(database_path: str) -> DatabasePool:
    """Get or create a database pool for the given path"""
    if database_path not in _database_pools:
        pool = DatabasePool(database_path)
        await pool.initialize()
        _database_pools[database_path] = pool

    return _database_pools[database_path]


async def close_all_pools() -> None:
    """Close all database pools"""
    for pool in _database_pools.values():
        await pool.close()
    _database_pools.clear()
