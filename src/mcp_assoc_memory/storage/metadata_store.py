


import aiosqlite
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from .base import BaseMetadataStore
from ..models.memory import Memory, MemoryDomain
from ..models.association import Association
from ..utils.logging import get_memory_logger


logger = get_memory_logger(__name__)


class SQLiteMetadataStore(BaseMetadataStore):

    def _row_to_memory(self, row) -> Optional[Memory]:
        if not row:
            return None
        try:
            # 明示的に各引数を渡す（embedding, categoryはNoneでOK）
            return Memory(
                id=str(row[0]),
                domain=MemoryDomain(row[1]),
                content=str(row[2]),
                metadata=json.loads(row[3]) if row[3] else {},
                tags=json.loads(row[4]) if row[4] else [],
                embedding=None,
                user_id=str(row[5]) if row[5] is not None else None,
                project_id=str(row[6]) if row[6] is not None else None,
                session_id=str(row[7]) if row[7] is not None else None,
                category=None,
                created_at=datetime.fromisoformat(row[8]),
                updated_at=datetime.fromisoformat(row[9]),
                accessed_at=datetime.fromisoformat(row[10]) if row[10] else None,
                access_count=int(row[11]) if row[11] is not None else 0
            )
        except Exception as e:
            logger.error(
                "Failed to convert row to Memory",
                error_code="ROW_CONVERT_ERROR",
                row=row,
                error=str(e)
            )
            return None

    async def get_memories_by_domain(self, domain: Optional[MemoryDomain], limit: int = 1000, order_by: Optional[str] = None) -> List[Memory]:
        """指定ドメインの記憶一覧を取得"""
        async with aiosqlite.connect(self.database_path) as db:
            query = "SELECT * FROM memories WHERE 1=1"
            params = []
            if domain:
                query += " AND domain = ?"
                params.append(domain.value if hasattr(domain, 'value') else str(domain))
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

    async def get_memory_stats(self, domain: Optional[MemoryDomain] = None) -> Dict[str, Any]:
        """ドメイン別・カテゴリ別件数など統計情報を返す"""
        stats: Dict[str, Any] = {"total": 0, "by_category": {}}
        async with aiosqlite.connect(self.database_path) as db:
            query = "SELECT metadata, COUNT(*) as cnt FROM memories WHERE 1=1"
            params: List[Any] = []
            if domain:
                query += " AND domain = ?"
                params.append(domain.value if hasattr(domain, 'value') else str(domain))
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
    """SQLite実装のメタデータストア"""

    def __init__(self, database_path: str = "./data/memory.db"):
        self.database_path = database_path
        self.db_lock = asyncio.Lock()

        # データベースディレクトリを作成
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        """データベースとテーブルを初期化"""
        try:
            async with aiosqlite.connect(self.database_path) as db:
                # 記憶テーブル
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS memories (
                        id TEXT PRIMARY KEY,
                        domain TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata TEXT,
                        tags TEXT,
                        user_id TEXT,
                        project_id TEXT,
                        session_id TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        accessed_at TEXT,
                        access_count INTEGER DEFAULT 0
                    )
                ''')

                # 関連性テーブル
                await db.execute('''
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
                ''')

                # インデックス作成
                await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_memories_domain
                    ON memories (domain)
                ''')
                await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_memories_user_project
                    ON memories (user_id, project_id)
                ''')
                await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_memories_created_at
                    ON memories (created_at)
                ''')
                await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_associations_source
                    ON associations (source_memory_id)
                ''')
                await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_associations_target
                    ON associations (target_memory_id)
                ''')

                await db.commit()

            logger.info(
                "SQLite metadata store initialized",
                extra_data={"database_path": self.database_path}
            )

        except Exception as e:
            logger.error(
                "Failed to initialize SQLite metadata store",
                error_code="SQLITE_INIT_ERROR",
                error=str(e)
            )
            raise

    async def close(self) -> None:
        """データベース接続を閉じる"""
        # aiosqliteは自動でクローズされる
        logger.info("SQLite metadata store closed")

    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            async with aiosqlite.connect(self.database_path) as db:
                # 記憶数を取得
                async with db.execute(
                    "SELECT COUNT(*) FROM memories"
                ) as cursor:
                    row = await cursor.fetchone()
                    memory_count = row[0] if row and row[0] is not None else 0

                # 関連性数を取得
                async with db.execute(
                    "SELECT COUNT(*) FROM associations"
                ) as cursor:
                    row = await cursor.fetchone()
                    association_count = row[0] if row and row[0] is not None else 0

                # ドメイン別統計
                domain_stats = {}
                for domain in MemoryDomain:
                    async with db.execute(
                        "SELECT COUNT(*) FROM memories WHERE domain = ?",
                        (domain.value,)
                    ) as cursor:
                        row = await cursor.fetchone()
                        count = row[0] if row and row[0] is not None else 0
                        domain_stats[domain.value] = count

                return {
                    "status": "healthy",
                    "database_path": self.database_path,
                    "total_memories": memory_count,
                    "total_associations": association_count,
                    "domain_stats": domain_stats,
                    "timestamp": datetime.utcnow().isoformat()
                }

        except Exception as e:
            return {
                "status": "error",
                "database_path": self.database_path,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def store_memory(self, memory: Memory) -> str:
        """記憶を保存"""
        try:
            async with self.db_lock:
                async with aiosqlite.connect(self.database_path) as db:
                    await db.execute('''
                        INSERT OR REPLACE INTO memories (
                            id, domain, content, metadata, tags, user_id,
                            project_id, session_id, created_at, updated_at,
                            accessed_at, access_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        memory.id,
                        memory.domain.value,
                        memory.content,
                        json.dumps(memory.metadata),
                        json.dumps(memory.tags),
                        memory.user_id,
                        memory.project_id,
                        memory.session_id,
                        memory.created_at.isoformat(),
                        memory.updated_at.isoformat(),
                        (memory.accessed_at.isoformat()
                         if memory.accessed_at else None),
                        memory.access_count
                    ))
                    await db.commit()

            logger.info(
                "Memory stored",
                extra_data={
                    "memory_id": memory.id,
                    "domain": memory.domain.value
                }
            )

            return memory.id

        except Exception as e:
            logger.error(
                "Failed to store memory",
                error_code="MEMORY_STORE_ERROR",
                memory_id=memory.id,
                error=str(e)
            )
            raise

    async def get_memory(self, memory_id: str) -> Optional[Memory]:
        """記憶を取得"""
        try:
            async with aiosqlite.connect(self.database_path) as db:
                async with db.execute(
                    "SELECT * FROM memories WHERE id = ?",
                    (memory_id,)
                ) as cursor:
                    row = await cursor.fetchone()
                    return self._row_to_memory(row)
        except Exception as e:
            logger.error(
                "Failed to get memory",
                error_code="MEMORY_GET_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            return None

    async def update_memory(self, memory: Memory) -> bool:
        """記憶を更新"""
        try:
            async with self.db_lock:
                async with aiosqlite.connect(self.database_path) as db:
                    await db.execute('''
                        UPDATE memories SET
                            content = ?, metadata = ?, tags = ?,
                            updated_at = ?, accessed_at = ?, access_count = ?
                        WHERE id = ?
                    ''', (
                        memory.content,
                        json.dumps(memory.metadata),
                        json.dumps(memory.tags),
                        memory.updated_at.isoformat(),
                        memory.accessed_at.isoformat() if memory.accessed_at else None,
                        memory.access_count,
                        memory.id
                    ))
                    await db.commit()

            logger.info(
                "Memory updated",
                extra_data={"memory_id": memory.id}
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to update memory",
                error_code="MEMORY_UPDATE_ERROR",
                memory_id=memory.id,
                error=str(e)
            )
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """記憶を削除"""
        try:
            async with self.db_lock:
                async with aiosqlite.connect(self.database_path) as db:
                    # 関連する関連性も削除
                    await db.execute('''
                        DELETE FROM associations
                        WHERE source_memory_id = ? OR target_memory_id = ?
                    ''', (memory_id, memory_id))

                    # 記憶を削除
                    await db.execute(
                        "DELETE FROM memories WHERE id = ?",
                        (memory_id,)
                    )

                    await db.commit()

            logger.info(
                "Memory deleted",
                extra_data={"memory_id": memory_id}
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to delete memory",
                error_code="MEMORY_DELETE_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            return False
    async def search_memories(
        self,
        domain: MemoryDomain,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Memory]:
        """記憶を検索"""
        try:
            where_conditions = ["domain = ?"]
            params = [domain.value]

            # 条件を構築
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

            # タグ検索
            if tags:
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append("tags LIKE ?")
                    params.append(f'%"{tag}"%')
                where_conditions.append(f"({' OR '.join(tag_conditions)})")

            sql = f'''
                SELECT * FROM memories
                WHERE {' AND '.join(where_conditions)}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            '''
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
                        extra_data={
                            "domain": domain.value,
                            "result_count": len(memories),
                            "query": query
                        }
                    )

                    return memories

        except Exception as e:
            logger.error(
                "Failed to search memories",
                error_code="MEMORY_SEARCH_ERROR",
                domain=domain.value,
                error=str(e)
            )
            return []

    async def get_memory_count(
        self,
        domain: MemoryDomain,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> int:
        """記憶数を取得"""
        try:
            where_conditions: List[str] = ["domain = ?"]
            params: List[Any] = [domain.value]

            if user_id:
                where_conditions.append("user_id = ?")
                params.append(user_id)

            if project_id:
                where_conditions.append("project_id = ?")
                params.append(project_id)

            sql = f'''
                SELECT COUNT(*) FROM memories
                WHERE {' AND '.join(where_conditions)}
            '''

            async with aiosqlite.connect(self.database_path) as db:
                async with db.execute(sql, params) as cursor:
                    row = await cursor.fetchone()
                    if row and row[0] is not None:
                        return int(row[0])
                    else:
                        return 0

        except Exception as e:
            logger.error(
                "Failed to get memory count",
                error_code="MEMORY_COUNT_ERROR",
                domain=domain.value,
                error=str(e)
            )
            return 0

    async def store_association(self, association: Association) -> str:
        """関連性を保存"""
        try:
            async with self.db_lock:
                async with aiosqlite.connect(self.database_path) as db:
                    await db.execute('''
                        INSERT OR REPLACE INTO associations (
                            id, source_memory_id, target_memory_id,
                            association_type, strength, metadata, description,
                            auto_generated, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        association.id,
                        association.source_memory_id,
                        association.target_memory_id,
                        association.association_type,
                        association.strength,
                        json.dumps(association.metadata),
                        association.description,
                        association.auto_generated,
                        association.created_at.isoformat(),
                        association.updated_at.isoformat()
                    ))
                    await db.commit()

            logger.info(
                "Association stored",
                extra_data={"association_id": association.id}
            )

            return association.id

        except Exception as e:
            logger.error(
                "Failed to store association",
                error_code="ASSOCIATION_STORE_ERROR",
                association_id=association.id,
                error=str(e)
            )
            raise

    async def get_associations(
        self,
        memory_id: str,
        direction: Optional[str] = None
    ) -> List[Association]:
        """関連性を取得"""
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
                async with db.execute(
                    f"SELECT * FROM associations WHERE {where_clause}",
                    params
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
                            updated_at=datetime.fromisoformat(row[9])
                        )
                        associations.append(association)

                    return associations

        except Exception as e:
            logger.error(
                "Failed to get associations",
                error_code="ASSOCIATION_GET_ERROR",
                memory_id=memory_id,
                error=str(e)
            )
            return []

    async def delete_association(self, association_id: str) -> bool:
        """関連性を削除"""
        try:
            async with self.db_lock:
                async with aiosqlite.connect(self.database_path) as db:
                    await db.execute(
                        "DELETE FROM associations WHERE id = ?",
                        (association_id,)
                    )
                    await db.commit()

            logger.info(
                "Association deleted",
                extra_data={"association_id": association_id}
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to delete association",
                error_code="ASSOCIATION_DELETE_ERROR",
                association_id=association_id,
                error=str(e)
            )
            return False
