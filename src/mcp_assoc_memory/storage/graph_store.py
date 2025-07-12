"""
NetworkXベースのグラフストア実装
記憶間の関連性をグラフ構造で管理
"""

import asyncio
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx

from ..models.association import Association
from ..models.memory import Memory
from ..utils.logging import get_memory_logger
from .base import BaseGraphStore

logger = get_memory_logger(__name__)


class NetworkXGraphStore(BaseGraphStore):
    async def get_all_association_edges(self, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        """全関連エッジ取得（可視化用）"""
        try:
            edges = []
            for u, v, key, data in self.graph.edges(keys=True, data=True):
                if (
                    scope is None
                    or self.graph.nodes[u].get("scope") == scope
                    or self.graph.nodes[v].get("scope") == scope
                ):
                    edge_info = {
                        "source": u,
                        "target": v,
                        "association_id": data.get("association_id"),
                        "association_type": data.get("association_type"),
                        "strength": data.get("strength"),
                        "metadata": data.get("metadata"),
                        "description": data.get("description"),
                        "auto_generated": data.get("auto_generated"),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                    }
                    edges.append(edge_info)
            return edges
        except Exception as e:
            logger.error("Failed to get all association edges", error=str(e))
            return []

    async def export_graph(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """グラフ構造エクスポート（可視化用）"""
        try:
            nodes = []
            for node_id, data in self.graph.nodes(data=True):
                if scope is None or data.get("scope") == scope:
                    nodes.append({"id": node_id, **data})
            edges = await self.get_all_association_edges(scope)
            return {"nodes": nodes, "edges": edges}
        except Exception as e:
            logger.error("Failed to export graph", error=str(e))
            return {"nodes": [], "edges": []}

    async def find_shortest_path(
        self, source_memory_id: str, target_memory_id: str, max_depth: int = 6
    ) -> Optional[List[str]]:
        """最短パスを検索"""
        try:
            if source_memory_id not in self.graph or target_memory_id not in self.graph:
                return None
            try:
                path = nx.shortest_path(self.graph, source_memory_id, target_memory_id)
                if isinstance(path, list) and len(path) > max_depth + 1:
                    return None
                if isinstance(path, list):
                    return [str(n) for n in path]
                return None
            except nx.NetworkXNoPath:
                return None
        except Exception as e:
            logger.error("Failed to find shortest path", error=str(e))
            return None

    async def calculate_centrality(self, centrality_type: str = "betweenness") -> Dict[str, float]:
        """中心性を計算"""
        try:
            if centrality_type == "betweenness":
                centrality = nx.betweenness_centrality(self.graph)
            elif centrality_type == "closeness":
                centrality = nx.closeness_centrality(self.graph)
            elif centrality_type == "degree":
                # Fallback: try both callable and non-callable degree
                try:
                    degree_view = getattr(self.graph, "degree", None)
                    if degree_view is not None and hasattr(degree_view, "__iter__"):
                        centrality = {str(n): float(d) for n, d in degree_view}
                    else:
                        centrality = {}
                except Exception:
                    centrality = {}
            else:
                centrality = {}
            return {str(k): float(v) for k, v in centrality.items()}
        except Exception as e:
            logger.error("Failed to calculate centrality", error=str(e))
            return {}

    async def detect_communities(self) -> Dict[str, List[str]]:
        """コミュニティを検出"""
        try:
            import collections.abc

            import networkx.algorithms.community as nx_comm

            try:
                communities = []
                if hasattr(nx_comm, "greedy_modularity_communities"):
                    comms = nx_comm.greedy_modularity_communities(self.graph)
                    # 型安全: set/generator/iterableのみリスト化、そうでなければ空リスト
                    if hasattr(comms, "__iter__") and not isinstance(comms, (str, bytes, int, float, complex, bool)):
                        try:
                            # NetworkX community detection returns generator of node sets
                            communities = [list(c) for c in comms]
                        except Exception:
                            communities = []
                    else:
                        communities = []
            except Exception:
                communities = []
            result = {f"community_{i}": [str(n) for n in comm] for i, comm in enumerate(communities)}
            return result
        except Exception as e:
            logger.error("Failed to detect communities", error=str(e))
            return {}

    """NetworkX実装のグラフストア"""

    def __init__(self, graph_path: str = "./data/memory_graph.pkl"):
        self.graph_path = graph_path
        self.graph = nx.MultiDiGraph()
        self.graph_lock = asyncio.Lock()

        # グラフファイルディレクトリを作成
        Path(self.graph_path).parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        """グラフを初期化"""
        try:
            # 既存グラフファイルの読み込み
            if Path(self.graph_path).exists():
                with open(self.graph_path, "rb") as f:
                    loaded_graph = pickle.load(f)
                    if isinstance(loaded_graph, nx.MultiDiGraph):
                        self.graph = loaded_graph
                    else:
                        logger.error("Loaded graph is not a MultiDiGraph. Reinitializing.")
                        self.graph = nx.MultiDiGraph()
                logger.info(
                    "Graph loaded from file",
                    extra_data={
                        "graph_path": self.graph_path,
                        "nodes": self.graph.number_of_nodes(),
                        "edges": self.graph.number_of_edges(),
                    },
                )
            else:
                # 新規グラフ作成
                self.graph = nx.MultiDiGraph()
                logger.info("New graph created")

        except Exception as e:
            logger.error("Failed to initialize graph store", error_code="GRAPH_INIT_ERROR", error=str(e))
            # フォールバック: 新規グラフ作成
            self.graph = nx.MultiDiGraph()
            logger.info("Fallback: created new graph")

    async def close(self) -> None:
        """グラフを保存"""
        try:
            await self._save_graph()
            logger.info("Graph store closed")
        except Exception as e:
            logger.error("Failed to save graph on close", error_code="GRAPH_SAVE_ERROR", error=str(e))

    async def _save_graph(self) -> None:
        """グラフをファイルに保存"""
        async with self.graph_lock:
            try:
                with open(self.graph_path, "wb") as f:
                    pickle.dump(self.graph, f)
                logger.info(
                    "Graph saved",
                    extra_data={
                        "graph_path": self.graph_path,
                        "nodes": self.graph.number_of_nodes(),
                        "edges": self.graph.number_of_edges(),
                    },
                )
            except Exception as e:
                logger.error("Failed to save graph", error_code="GRAPH_SAVE_ERROR", error=str(e))
                raise

    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            # 基本統計
            stats = {
                "status": "healthy",
                "graph_path": self.graph_path,
                "nodes": self.graph.number_of_nodes(),
                "edges": self.graph.number_of_edges(),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # スコープ別統計
            scope_stats = {}
            # 既存のスコープを動的に収集
            existing_scopes = set()
            for node_id, data in self.graph.nodes(data=True):
                node_scope = data.get("scope", "unknown")
                existing_scopes.add(node_scope)

            for scope in existing_scopes:
                nodes = [n for n, d in self.graph.nodes(data=True) if d.get("scope") == scope]
                scope_stats[scope] = len(nodes)

            stats["scope_stats"] = scope_stats

            # グラフの連結性チェック
            if self.graph.number_of_nodes() > 0:
                # 最大弱連結成分のサイズ
                largest_component: set[str] = max(nx.weakly_connected_components(self.graph), key=len, default=set())
                stats["largest_component_size"] = len(largest_component)
                stats["connectivity_ratio"] = (
                    len(largest_component) / self.graph.number_of_nodes() if self.graph.number_of_nodes() > 0 else 0
                )
            else:
                stats["largest_component_size"] = 0
                stats["connectivity_ratio"] = 0

            return stats

        except Exception as e:
            return {
                "status": "error",
                "graph_path": self.graph_path,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def add_memory_node(self, memory: Memory) -> bool:
        """記憶ノードを追加"""
        try:
            async with self.graph_lock:
                node_attributes = {
                    "scope": memory.scope,
                    "content": memory.content,
                    "metadata": memory.metadata,
                    "tags": memory.tags,
                    "category": memory.category,
                    "user_id": memory.user_id,
                    "project_id": memory.project_id,
                    "session_id": memory.session_id,
                    "created_at": memory.created_at.isoformat() if memory.created_at else None,
                    "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
                    "accessed_at": memory.accessed_at.isoformat() if memory.accessed_at else None,
                    "access_count": memory.access_count,
                }

                self.graph.add_node(memory.id, **node_attributes)

            logger.info("Memory node added", extra_data={"memory_id": memory.id, "scope": memory.scope})

            # 定期的にグラフを保存
            if self.graph.number_of_nodes() % 100 == 0:
                await self._save_graph()

            return True

        except Exception as e:
            logger.error(
                "Failed to add memory node", error_code="GRAPH_ADD_NODE_ERROR", memory_id=memory.id, error=str(e)
            )
            return False

    async def remove_memory_node(self, memory_id: str) -> bool:
        """記憶ノードを削除"""
        try:
            async with self.graph_lock:
                if memory_id in self.graph:
                    self.graph.remove_node(memory_id)

                    logger.info("Memory node removed", extra_data={"memory_id": memory_id})
                    return True
                else:
                    logger.warning("Memory node not found for removal", extra_data={"memory_id": memory_id})
                    return False

        except Exception as e:
            logger.error(
                "Failed to remove memory node", error_code="GRAPH_REMOVE_NODE_ERROR", memory_id=memory_id, error=str(e)
            )
            return False

    async def add_association_edge(self, association: Association) -> None:
        """関連性エッジを追加"""
        try:
            async with self.graph_lock:
                edge_attributes = {
                    "association_id": association.id,
                    "association_type": association.association_type,
                    "strength": association.strength,
                    "metadata": association.metadata,
                    "description": association.description,
                    "auto_generated": association.auto_generated,
                    "created_at": association.created_at.isoformat(),
                    "updated_at": association.updated_at.isoformat(),
                }

                self.graph.add_edge(
                    association.source_memory_id, association.target_memory_id, key=association.id, **edge_attributes
                )

            logger.info(
                "Association edge added",
                extra_data={
                    "association_id": association.id,
                    "source": association.source_memory_id,
                    "target": association.target_memory_id,
                    "association_type": association.association_type,
                },
            )

        except Exception as e:
            logger.error(
                "Failed to add association edge",
                error_code="GRAPH_ADD_EDGE_ERROR",
                association_id=association.id,
                error=str(e),
            )

    async def remove_association_edge(self, association_id: str) -> bool:
        """関連性エッジを削除"""
        try:
            async with self.graph_lock:
                # エッジを検索
                edge_to_remove = None
                for u, v, key, data in self.graph.edges(keys=True, data=True):
                    if data.get("association_id") == association_id:
                        edge_to_remove = (u, v, key)
                        break

                if edge_to_remove:
                    u, v, key = edge_to_remove
                    self.graph.remove_edge(u, v, key)

                    logger.info("Association edge removed", extra_data={"association_id": association_id})
                    return True
                else:
                    logger.warning(
                        "Association edge not found for removal", extra_data={"association_id": association_id}
                    )
                    return False

        except Exception as e:
            logger.error(
                "Failed to remove association edge",
                error_code="GRAPH_REMOVE_EDGE_ERROR",
                association_id=association_id,
                error=str(e),
            )
            return False

    async def get_neighbors(self, memory_id: str, depth: int = 1, min_strength: float = 0.0) -> List[Dict[str, Any]]:
        """近隣記憶を取得"""
        try:
            if memory_id not in self.graph:
                return []

            neighbors: List[Dict[str, Any]] = []
            visited = set()

            # Default max neighbors and max depth for compatibility
            max_neighbors = 20
            max_depth = min(depth + 1, 3)  # Convert depth to max_depth

            # BFS で近隣ノードを探索
            queue = [(memory_id, 0)]
            visited.add(memory_id)

            while queue and len(neighbors) < max_neighbors:
                current_id, current_depth = queue.pop(0)

                if current_depth >= max_depth:
                    continue

                # 隣接ノードを取得
                for neighbor_id in self.graph.neighbors(current_id):
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)

                        # エッジ情報を取得
                        edge_data = self.graph.get_edge_data(current_id, neighbor_id)

                        # 最も強い関連を取得
                        best_edge = max(edge_data.values(), key=lambda x: x.get("strength", 0))

                        edge_strength = best_edge.get("strength", 0)

                        # min_strength でフィルタリング
                        if edge_strength < min_strength:
                            continue

                        # ノード情報を取得
                        node_data = self.graph.nodes[neighbor_id]

                        neighbor_info = {
                            "memory_id": neighbor_id,
                            "depth": current_depth + 1,
                            "association_strength": edge_strength,
                            "association_type": best_edge.get("association_type"),
                            "node_data": node_data,
                        }

                        neighbors.append(neighbor_info)

                        # 深度制限内であれば次のレベルを探索
                        if current_depth + 1 < max_depth:
                            queue.append((neighbor_id, current_depth + 1))

            # 関連強度でソート
            neighbors.sort(key=lambda x: x["association_strength"], reverse=True)

            return neighbors[:max_neighbors]

        except Exception as e:
            logger.error(
                "Failed to get neighbors", error_code="GRAPH_GET_NEIGHBORS_ERROR", memory_id=memory_id, error=str(e)
            )
            return []

    async def find_path(
        self, source_id: str, target_id: str, max_path_length: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """記憶間のパスを検索"""
        try:
            if source_id not in self.graph or target_id not in self.graph:
                return None

            try:
                # 最短パスを検索
                path = nx.shortest_path(
                    self.graph, source_id, target_id, weight=lambda u, v, d: 1.0 / (d.get("strength", 0.1) + 0.1)
                )

                if len(path) > max_path_length + 1:
                    return None

                # パス情報を構築
                path_info = []
                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    edge_data = self.graph.get_edge_data(u, v)

                    # 最も強い関連を取得
                    best_edge = max(edge_data.values(), key=lambda x: x.get("strength", 0))

                    step = {
                        "from": u,
                        "to": v,
                        "association_strength": best_edge.get("strength", 0),
                        "association_type": best_edge.get("association_type"),
                        "association_id": best_edge.get("association_id"),
                    }

                    path_info.append(step)

                return path_info

            except nx.NetworkXNoPath:
                return None

        except Exception as e:
            logger.error(
                "Failed to find path",
                error_code="GRAPH_FIND_PATH_ERROR",
                source_id=source_id,
                target_id=target_id,
                error=str(e),
            )
            return None

    async def get_graph_stats(self) -> dict:
        """グラフ統計を取得"""
        try:
            stats: dict = {
                "nodes": self.graph.number_of_nodes(),
                "edges": self.graph.number_of_edges(),
            }

            if self.graph.number_of_nodes() > 0:
                # 次数統計
                node_degrees = {node: int(deg) for node, deg in getattr(self.graph, "degree")()}
                if node_degrees:
                    stats["avg_degree"] = sum(node_degrees.values()) / len(node_degrees)
                    stats["max_degree"] = max(node_degrees.values())
                    stats["min_degree"] = min(node_degrees.values())
                else:
                    stats["avg_degree"] = 0
                    stats["max_degree"] = 0
                    stats["min_degree"] = 0

                # 連結成分
                components = list(nx.weakly_connected_components(self.graph))
                stats["num_components"] = len(components)
                if components:
                    stats["largest_component_size"] = len(max(components, key=len))
                else:
                    stats["largest_component_size"] = 0

                # 関連タイプ別統計
                type_stats: Dict[str, int] = {}
                for u, v, data in self.graph.edges(data=True):
                    assoc_type = data.get("association_type", "unknown")
                    type_stats[assoc_type] = type_stats.get(assoc_type, 0) + 1

                stats["association_type_stats"] = type_stats

            return stats

        except Exception as e:
            logger.error("Failed to get graph stats", error_code="GRAPH_STATS_ERROR", error=str(e))
            return {}

    async def cleanup_orphaned_nodes(self) -> int:
        """孤立ノードをクリーンアップ"""
        try:
            async with self.graph_lock:
                orphaned_nodes = []
                for node in self.graph.nodes():
                    # NetworkX degree() method returns int but mypy incorrectly sees it as property
                    deg = self.graph.degree(node)
                    if deg == 0:
                        orphaned_nodes.append(node)

                for node in orphaned_nodes:
                    self.graph.remove_node(node)

                if orphaned_nodes:
                    await self._save_graph()

                logger.info("Orphaned nodes cleaned up", extra_data={"removed_count": len(orphaned_nodes)})

                return len(orphaned_nodes)

        except Exception as e:
            logger.error("Failed to cleanup orphaned nodes", error_code="GRAPH_CLEANUP_ERROR", error=str(e))
            return 0
