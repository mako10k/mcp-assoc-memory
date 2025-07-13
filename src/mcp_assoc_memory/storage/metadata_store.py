import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

from ..models.association import Association
from ..models.memory import Memory
from ..utils.logging import get_memory_logger
from .base import BaseMetadataStore
from .database_pool import DatabasePool, get_database_pool

logger = get_memory_logger(__name__)


class SQLiteMetadataStore(BaseMetadataStore):
    async def search_by_tags(
        self, tags: List[str], scope: Optional[str] = None, match_all: bool = False, limit: int = 10
    ) -> List[Memory]:
        """Tag search"""
        try:
            where_conditions = ["JSON_EXTRACT(metadata, '$.scope') = ?"]
            params = [scope]
            if tags:
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f'%"{tag}"%')
                if match_all:
                    where_conditions.extend(tag_conditions)
                else:
                    where_conditions.append(f"({' OR '.join(tag_conditions)})")
            sql = f"""
                SELECT * FROM memories
                WHERE {' AND '.join(where_conditions)}
                ORDER BY created_at DESC
                LIMIT ?
            """
            params.append(str(limit))
            async with aiosqlite.connect(self.database_path) as db:
                async with db.execute(sql, params) as cursor:
                    rows = await cursor.fetchall()
                    memories = [self._row_to_memory(row) for row in rows if row]
                    return [m for m in memories if m is not None]
        except Exception as e:
            logger.error("Failed to search by tags", error=str(e))
            return []

    async def search_by_timerange(
        self, start_date: datetime, end_date: datetime, scope: Optional[str] = None, limit: int = 10
    ) -> List[Memory]:
        """Time range search"""
        try:
            sql = """
                SELECT * FROM memories
                WHERE JSON_EXTRACT(metadata, '$.scope') = ? AND created_at >= ? AND created_at <= ?
                ORDER BY created_at DESC
                LIMIT ?
            """
            params = [scope, start_date.isoformat(), end_date.isoformat(), str(limit)]
            async with aiosqlite.connect(self.database_path) as db:
                async with db.execute(sql, params) as cursor:
                    rows = await cursor.fetchall()
                    memories = [self._row_to_memory(row) for row in rows if row]
                    return [m for m in memories if m is not None]
        except Exception as e:
            logger.error("Failed to search by timerange", error=str(e))
            return []

    async def advanced_search(
        self,
        scope: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 30,
    ) -> List[Memory]:
        """Advanced search (complex conditions)"""
        try:
            where_conditions = ["JSON_EXTRACT(metadata, '$.scope') = ?"]
            params = [scope]
            if tags:
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f'%"{tag}"%')
                where_conditions.append(f"({' OR '.join(tag_conditions)})")
            if category:
                where_conditions.append("metadata LIKE ?")
                params.append(f'%"category": "{category}"%')
            if start_date:
                where_conditions.append("created_at >= ?")
                params.append(start_date.isoformat())
            if end_date:
                where_conditions.append("created_at <= ?")
                params.append(end_date.isoformat())
            sql = f"""
                SELECT * FROM memories
                WHERE {' AND '.join(where_conditions)}
                ORDER BY created_at DESC
                LIMIT ?
            """
            params.append(str(limit))
            async with aiosqlite.connect(self.database_path) as db:
                async with db.execute(sql, params) as cursor:
                    rows = await cursor.fetchall()
                    memories = [self._row_to_memory(row) for row in rows if row]
                    return [m for m in memories if m is not None]
        except Exception as e:
            logger.error("Failed to advanced search", error=str(e))
            return []

    async def update_access_stats(self, memory_id: str, access_count: int) -> bool:
        try:
            async with self.db_lock:
                async with aiosqlite.connect(self.database_path) as db:
                    await db.execute("UPDATE memories SET access_count = ? WHERE id = ?", (access_count, memory_id))
                    await db.commit()
            return True
        except Exception as e:
            logger.error("Failed to update access stats", error=str(e))
            return False

    async def get_memory_associations(self, memory_id: str) -> List[Association]:
        try:
            async with aiosqlite.connect(self.database_path) as db:
                async with db.execute(
                    "SELECT * FROM associations WHERE source_memory_id = ? OR target_memory_id = ?",
                    (memory_id, memory_id),
                ) as cursor:
                    rows = await cursor.fetchall()
                    associations = []
                    for row in rows:
                        association = Association(
                            id=row[0],
                            source_memory_id=row[1],
                            target_memory_id=row[2],
                            association_type=row[3],
                            strength=row[4],
                            metadata=json.loads(row[5]) if row[5] else {},
                            description=row[6],
                            auto_generated=bool(row[7]),
                            created_at=datetime.fromisoformat(row[8]),
                            updated_at=datetime.fromisoformat(row[9]),
                        )
                        associations.append(association)
                    return associations
        except Exception as e:
            logger.error("Failed to get memory associations", error=str(e))
            return []

    async def batch_delete_memories(self, criteria: Dict[str, Any]) -> int:
        try:
            where_conditions = []
            params = []
            for key, value in criteria.items():
                where_conditions.append(f"{key} = ?")
                params.append(value)
            sql = f"DELETE FROM memories WHERE {' AND '.join(where_conditions)}"
            async with self.db_lock:
                async with aiosqlite.connect(self.database_path) as db:
                    cursor = await db.execute(sql, params)
                    count = cursor.rowcount
                    await db.commit()
            return count or 0
        except Exception as e:
            logger.error("Failed to batch delete memories", error=str(e))
            return 0

    async def cleanup_orphans(self) -> int:
        try:
            # Delete orphaned memories (those without associations)
            sql = """
                DELETE FROM memories
                WHERE id NOT IN (
                    SELECT source_memory_id FROM associations
                    UNION
                    SELECT target_memory_id FROM associations
                )
            """
            async with self.db_lock:
                async with aiosqlite.connect(self.database_path) as db:
                    cursor = await db.execute(sql)
                    count = cursor.rowcount
                    await db.commit()
            return count or 0
        except Exception as e:
            logger.error("Failed to cleanup orphans", error=str(e))
            return 0

    async def reindex(self) -> None:
        try:
            async with aiosqlite.connect(self.database_path) as db:
                await db.execute("REINDEX")
                await db.commit()
        except Exception as e:
            logger.error("Failed to reindex", error=str(e))

    async def vacuum(self) -> None:
        try:
            async with aiosqlite.connect(self.database_path) as db:
                await db.execute("VACUUM")
                await db.commit()
        except Exception as e:
            logger.error("Failed to vacuum", error=str(e))

    def _row_to_memory(self, row: Any) -> Optional[Memory]:
        if not row:
            return None
        try:
            # Parse metadata to get scope, with fallback for backward compatibility
            metadata = json.loads(row[3]) if row[3] else {}
            scope = metadata.get("scope")
            if not scope:
                # Fallback to legacy scope field for backward compatibility
                scope = str(row[1]) if row[1] else "user/default"

            return Memory(
                id=str(row[0]),
                scope=scope,
                content=str(row[2]),
                metadata=metadata,
                tags=json.loads(row[4]) if row[4] else [],
                embedding=None,
                user_id=str(row[5]) if row[5] is not None else None,
                project_id=str(row[6]) if row[6] is not None else None,
                session_id=str(row[7]) if row[7] is not None else None,
                category=str(row[12]) if row[12] is not None else None,  # Fixed: use row[12] for category
                created_at=datetime.fromisoformat(row[8]),
                updated_at=datetime.fromisoformat(row[9]),
                accessed_at=datetime.fromisoformat(row[10]) if row[10] else None,
                access_count=int(row[11]) if row[11] is not None else 0,
            )
        except Exception as e:
            logger.error("Failed to convert row to Memory", error_code="ROW_CONVERT_ERROR", row=row, error=str(e))
            return None

    async def get_memories_by_scope(
        self, scope: Optional[str] = None, limit: int = 1000, order_by: Optional[str] = None
    ) -> List[Memory]:
        """Get memories by scope"""
        async with aiosqlite.connect(self.database_path) as db:
            query = "SELECT * FROM memories WHERE 1=1"
            params: List[Any] = []
            if scope:
                # Filter by scope stored in metadata
                query += " AND JSON_EXTRACT(metadata, '$.scope') = ?"
                params.append(scope)
            if order_by:
                query += f" ORDER BY {order_by}"
            else:
                query += " ORDER BY created_at DESC"
            query += " LIMIT ?"
            params.append(limit)
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
            memories = []
            for row in rows:
                memory = self._row_to_memory(row)
                if memory:
                    memories.append(memory)
            return memories

    async def get_memory_stats(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """Get memory statistics by scope and category"""
        stats: Dict[str, Any] = {"total": 0, "by_category": {}}
        async with aiosqlite.connect(self.database_path) as db:
            query = "SELECT metadata, COUNT(*) as cnt FROM memories WHERE 1=1"
            params: List[Any] = []
            if scope:
                query += " AND JSON_EXTRACT(metadata, '$.scope') = ?"
                params.append(scope)
            if scope:
                query += " AND JSON_EXTRACT(metadata, '$.scope') = ?"
                params.append(scope)
            query += " GROUP BY metadata"
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
            for row in rows:
                # カテゴリはmetadataの中に含まれる場合があるため、ここではmetadataからcategoryを抽出
                try:
                    meta = json.loads(row[0]) if row[0] else {}
                    category = meta.get("category", "unknown")
                except Exception:
                    category = "unknown"
                stats["by_category"][category] = row[1]
                stats["total"] += row[1]
        return stats

    """SQLite implementation of metadata store"""

    def __init__(self, database_path: str = "./data/memory.db"):
        self.database_path = database_path
        self.db_lock = asyncio.Lock()
        self._pool: Optional[DatabasePool] = None

        # Create database directory
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        """Initialize database pool and tables"""
        try:
            # Initialize database pool
            self._pool = await get_database_pool(self.database_path)

            # Create tables using pool connection
            conn_manager = await self._pool.get_connection()
            async with conn_manager as db:
                # Memories table
                await db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS memories (
                        id TEXT PRIMARY KEY,
                        scope TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata TEXT,
                        tags TEXT,
                        user_id TEXT,
                        project_id TEXT,
                        session_id TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        accessed_at TEXT,
                        access_count INTEGER DEFAULT 0,
                        category TEXT
                    )
                """
                )

                # Associations table
                await db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS associations (
                        id TEXT PRIMARY KEY,
                        source_memory_id TEXT NOT NULL,
                        target_memory_id TEXT NOT NULL,
                        association_type TEXT NOT NULL,
                        strength REAL NOT NULL,
                        metadata TEXT,
                        description TEXT,
                        auto_generated INTEGER DEFAULT 1,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (source_memory_id)
                            REFERENCES memories (id),
                        FOREIGN KEY (target_memory_id)
                            REFERENCES memories (id)
                    )
                """
                )

                # Create indexes
                await db.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_memories_scope
                    ON memories (scope)
                """
                )
                await db.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_memories_user_project
                    ON memories (user_id, project_id)
                """
                )
                await db.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_memories_created_at
                    ON memories (created_at)
                """
                )
                await db.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_associations_source
                    ON associations (source_memory_id)
                """
                )
                await db.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_associations_target
                    ON associations (target_memory_id)
                """
                )

                await db.commit()

            logger.info("SQLite metadata store initialized", extra={"database_path": self.database_path})

        except Exception as e:
            logger.error(
                f"Failed to initialize SQLite metadata store: {str(e)}", extra={"error_code": "SQLITE_INIT_ERROR"}
            )
            raise

    async def close(self) -> None:
        """Close database connection"""
        # aiosqliteは自動でクローズされる
        logger.info("SQLite metadata store closed")

    async def health_check(self) -> Dict[str, Any]:
        """Health check"""
        try:
            async with aiosqlite.connect(self.database_path) as db:
                # Get memory count
                async with db.execute("SELECT COUNT(*) FROM memories") as cursor:
                    row = await cursor.fetchone()
                    memory_count = row[0] if row and row[0] is not None else 0

                # Get association count
                async with db.execute("SELECT COUNT(*) FROM associations") as cursor:
                    row = await cursor.fetchone()
                    association_count = row[0] if row and row[0] is not None else 0

                # スコープ別統計
                scope_stats = {}
                # 既存のスコープを動的に取得
                async with db.execute(
                    "SELECT DISTINCT JSON_EXTRACT(metadata, '$.scope') as scope FROM memories WHERE scope IS NOT NULL"
                ) as cursor:
                    scope_rows = await cursor.fetchall()

                for scope_row in scope_rows:
                    scope = scope_row[0] if scope_row[0] else "unknown"
                    async with db.execute(
                        "SELECT COUNT(*) FROM memories WHERE JSON_EXTRACT(metadata, '$.scope') = ?", (scope,)
                    ) as cursor:
                        row = await cursor.fetchone()
                        count = row[0] if row and row[0] is not None else 0
                        scope_stats[scope] = count

                return {
                    "status": "healthy",
                    "database_path": self.database_path,
                    "total_memories": memory_count,
                    "total_associations": association_count,
                    "scope_stats": scope_stats,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            return {
                "status": "error",
                "database_path": self.database_path,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def store_memory(self, memory: Memory) -> str:
        """Store memory with scope information"""
        try:
            async with self.db_lock:
                async with aiosqlite.connect(self.database_path) as db:
                    await db.execute(
                        """
                        INSERT OR REPLACE INTO memories (
                            id, scope, content, metadata, tags, user_id,
                            project_id, session_id, created_at, updated_at,
                            accessed_at, access_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            memory.id,
                            memory.scope,
                            memory.content,
                            json.dumps(memory.metadata),
                            json.dumps(memory.tags),
                            memory.user_id,
                            memory.project_id,
                            memory.session_id,
                            memory.created_at.isoformat(),
                            memory.updated_at.isoformat(),
                            (memory.accessed_at.isoformat() if memory.accessed_at else None),
                            memory.access_count,
                        ),
                    )
                    await db.commit()

            logger.info("Memory stored", extra_data={"memory_id": memory.id, "scope": memory.scope})

            return memory.id

        except Exception as e:
            logger.error("Failed to store memory", error_code="MEMORY_STORE_ERROR", memory_id=memory.id, error=str(e))
            raise

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """Get memory"""
        try:
            async with aiosqlite.connect(self.database_path) as db:
                async with db.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)) as cursor:
                    row = await cursor.fetchone()
                    return self._row_to_memory(row)
        except Exception as e:
            logger.error("Failed to get memory", error_code="MEMORY_GET_ERROR", memory_id=memory_id, error=str(e))
            return None

    async def update_memory(self, memory: Memory) -> bool:
        """Update memory"""
        try:
            async with self.db_lock:
                async with aiosqlite.connect(self.database_path) as db:
                    await db.execute(
                        """
                        UPDATE memories SET
                            scope = ?, content = ?, metadata = ?, tags = ?, category = ?,
                            updated_at = ?, accessed_at = ?, access_count = ?
                        WHERE id = ?
                    """,
                        (
                            memory.scope,
                            memory.content,
                            json.dumps(memory.metadata),
                            json.dumps(memory.tags),
                            memory.category,
                            memory.updated_at.isoformat(),
                            memory.accessed_at.isoformat() if memory.accessed_at else None,
                            memory.access_count,
                            memory.id,
                        ),
                    )
                    await db.commit()

            logger.info("Memory updated", extra_data={"memory_id": memory.id})

            return True

        except Exception as e:
            logger.error("Failed to update memory", error_code="MEMORY_UPDATE_ERROR", memory_id=memory.id, error=str(e))
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete memory"""
        try:
            async with self.db_lock:
                async with aiosqlite.connect(self.database_path) as db:
                    # Also delete related associations
                    await db.execute(
                        """
                        DELETE FROM associations
                        WHERE source_memory_id = ? OR target_memory_id = ?
                    """,
                        (memory_id, memory_id),
                    )

                    # Delete memory
                    await db.execute("DELETE FROM memories WHERE id = ?", (memory_id,))

                    await db.commit()

            logger.info("Memory deleted", extra_data={"memory_id": memory_id})

            return True

        except Exception as e:
            logger.error("Failed to delete memory", error_code="MEMORY_DELETE_ERROR", memory_id=memory_id, error=str(e))
            return False

    async def search_memories(
        self,
        scope: Optional[str] = None,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Memory]:
        """Search memories"""
        try:
            where_conditions = ["JSON_EXTRACT(metadata, '$.scope') = ?"]
            params = [scope]

            # Build conditions
            if query:
                where_conditions.append("content LIKE ?")
                params.append(f"%{query}%")

            if user_id:
                where_conditions.append("user_id = ?")
                params.append(user_id)

            if project_id:
                where_conditions.append("project_id = ?")
                params.append(project_id)

            if session_id:
                where_conditions.append("session_id = ?")
                params.append(session_id)

            if date_from:
                where_conditions.append("created_at >= ?")
                params.append(date_from.isoformat())

            if date_to:
                where_conditions.append("created_at <= ?")
                params.append(date_to.isoformat())

            # Tag search
            if tags:
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f'%"{tag}"%')
                where_conditions.append(f"({' OR '.join(tag_conditions)})")

            sql = f"""
                SELECT * FROM memories
                WHERE {' AND '.join(where_conditions)}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params.append(str(limit))
            params.append(str(offset))

            async with aiosqlite.connect(self.database_path) as db:
                async with db.execute(sql, params) as cursor:
                    rows = await cursor.fetchall()

                    memories = []
                    for row in rows:
                        memory = self._row_to_memory(row)
                        if memory:
                            memories.append(memory)

                    logger.info(
                        "Memory search completed",
                        extra_data={"scope": scope, "result_count": len(memories), "query": query},
                    )

                    return memories

        except Exception as e:
            logger.error("Failed to search memories", error_code="MEMORY_SEARCH_ERROR", scope=scope, error=str(e))
            return []

    async def get_memory_count(
        self, scope: Optional[str] = None, user_id: Optional[str] = None, project_id: Optional[str] = None
    ) -> int:
        """Get memory count"""
        try:
            where_conditions: List[str] = ["JSON_EXTRACT(metadata, '$.scope') = ?"]
            params: List[Any] = [scope]

            if user_id:
                where_conditions.append("user_id = ?")
                params.append(user_id)

            if project_id:
                where_conditions.append("project_id = ?")
                params.append(project_id)

            sql = f"""
                SELECT COUNT(*) FROM memories
                WHERE {' AND '.join(where_conditions)}
            """

            async with aiosqlite.connect(self.database_path) as db:
                async with db.execute(sql, params) as cursor:
                    row = await cursor.fetchone()
                    if row and row[0] is not None:
                        return int(row[0])
                    else:
                        return 0

        except Exception as e:
            logger.error("Failed to get memory count", error_code="MEMORY_COUNT_ERROR", scope=scope, error=str(e))
            return 0

    async def store_association(self, association: Association) -> str:
        """Store association"""
        try:
            async with self.db_lock:
                async with aiosqlite.connect(self.database_path) as db:
                    await db.execute(
                        """
                        INSERT OR REPLACE INTO associations (
                            id, source_memory_id, target_memory_id,
                            association_type, strength, metadata, description,
                            auto_generated, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            association.id,
                            association.source_memory_id,
                            association.target_memory_id,
                            association.association_type,
                            association.strength,
                            json.dumps(association.metadata),
                            association.description,
                            association.auto_generated,
                            association.created_at.isoformat(),
                            association.updated_at.isoformat(),
                        ),
                    )
                    await db.commit()

            logger.info("Association stored", extra_data={"association_id": association.id})

            return association.id

        except Exception as e:
            logger.error(
                "Failed to store association",
                error_code="ASSOCIATION_STORE_ERROR",
                association_id=association.id,
                error=str(e),
            )
            raise

    async def get_associations(self, memory_id: str, direction: Optional[str] = None) -> List[Association]:
        """Get associations"""
        try:
            if direction == "incoming":
                where_clause = "target_memory_id = ?"
            elif direction == "outgoing":
                where_clause = "source_memory_id = ?"
            else:
                where_clause = "source_memory_id = ? OR target_memory_id = ?"

            params = [memory_id]
            if direction is None:
                params.append(memory_id)

            async with aiosqlite.connect(self.database_path) as db:
                async with db.execute(f"SELECT * FROM associations WHERE {where_clause}", params) as cursor:
                    rows = await cursor.fetchall()

                    associations = []
                    for row in rows:
                        association = Association(
                            id=row[0],
                            source_memory_id=row[1],
                            target_memory_id=row[2],
                            association_type=row[3],
                            strength=row[4],
                            metadata=json.loads(row[5]) if row[5] else {},
                            description=row[6],
                            auto_generated=bool(row[7]),
                            created_at=datetime.fromisoformat(row[8]),
                            updated_at=datetime.fromisoformat(row[9]),
                        )
                        associations.append(association)

                    return associations

        except Exception as e:
            logger.error(
                "Failed to get associations", error_code="ASSOCIATION_GET_ERROR", memory_id=memory_id, error=str(e)
            )
            return []

    async def delete_association(self, association_id: str) -> bool:
        """Delete association"""
        try:
            async with self.db_lock:
                async with aiosqlite.connect(self.database_path) as db:
                    await db.execute("DELETE FROM associations WHERE id = ?", (association_id,))
                    await db.commit()

            logger.info("Association deleted", extra_data={"association_id": association_id})

            return True

        except Exception as e:
            logger.error(
                "Failed to delete association",
                error_code="ASSOCIATION_DELETE_ERROR",
                association_id=association_id,
                error=str(e),
            )
            return False

    async def get_all_memories(self, limit: int = 1000) -> List[Memory]:
        """Get all memories with limit"""
        try:
            async with aiosqlite.connect(self.database_path) as db:
                async with db.execute("SELECT * FROM memories ORDER BY created_at DESC LIMIT ?", (limit,)) as cursor:
                    rows = await cursor.fetchall()
                    memories = [self._row_to_memory(row) for row in rows if row]
                    return [m for m in memories if m is not None]
        except Exception as e:
            logger.error("Failed to get all memories", error=str(e))
            return []

    async def get_all_scopes(self) -> List[str]:
        """Get all unique scopes"""
        try:
            async with aiosqlite.connect(self.database_path) as db:
                async with db.execute(
                    "SELECT DISTINCT JSON_EXTRACT(metadata, '$.scope') as scope FROM memories WHERE scope IS NOT NULL"
                ) as cursor:
                    rows = await cursor.fetchall()
                    return [row[0] for row in rows if row[0]]
        except Exception as e:
            logger.error("Failed to get all scopes", error=str(e))
            return []

    async def get_association_count(self, scope: Optional[str] = None) -> int:
        """Get count of associations, optionally filtered by scope"""
        try:
            if scope:
                # Count associations where both memories are in the specified scope
                async with aiosqlite.connect(self.database_path) as db:
                    async with db.execute(
                        """
                        SELECT COUNT(*) FROM associations a
                        JOIN memories m1 ON a.source_memory_id = m1.id
                        JOIN memories m2 ON a.target_memory_id = m2.id
                        WHERE JSON_EXTRACT(m1.metadata, '$.scope') = ?
                        AND JSON_EXTRACT(m2.metadata, '$.scope') = ?
                    """,
                        (scope, scope),
                    ) as cursor:
                        result = await cursor.fetchone()
                        return result[0] if result else 0
            else:
                async with aiosqlite.connect(self.database_path) as db:
                    async with db.execute("SELECT COUNT(*) FROM associations") as cursor:
                        result = await cursor.fetchone()
                        return result[0] if result else 0
        except Exception as e:
            logger.error("Failed to get association count", error=str(e))
            return 0

    async def update_association(self, association: Association) -> bool:
        """Update an existing association"""
        try:
            async with self.db_lock:
                async with aiosqlite.connect(self.database_path) as db:
                    await db.execute(
                        """
                        UPDATE associations SET
                            association_type = ?,
                            strength = ?,
                            metadata = ?,
                            description = ?,
                            updated_at = ?
                        WHERE id = ?
                    """,
                        (
                            association.association_type,
                            association.strength,
                            json.dumps(association.metadata),
                            association.description,
                            association.updated_at.isoformat(),
                            association.id,
                        ),
                    )
                    await db.commit()
            return True
        except Exception as e:
            logger.error("Failed to update association", error=str(e))
            return False

    async def get_memory_count_by_scope(self, scope: str) -> int:
        """Get count of memories in a specific scope"""
        try:
            async with aiosqlite.connect(self.database_path) as db:
                async with db.execute(
                    "SELECT COUNT(*) FROM memories WHERE JSON_EXTRACT(metadata, '$.scope') = ?", (scope,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row and row[0] is not None else 0
        except Exception as e:
            logger.error(f"Failed to get memory count for scope '{scope}': {e}")
            return 0
