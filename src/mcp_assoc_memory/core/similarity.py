"""
類似度計算ユーティリティ
ベクトル間の類似度計算とランキング機能
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..utils.logging import get_memory_logger

logger = get_memory_logger(__name__)


class SimilarityMetric(Enum):
    """類似度計算手法"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"


class SimilarityCalculator:
    def cosine_similarity(self, vector1, vector2) -> float:
        """コサイン類似度を直接計算 (memory_manager.py互換)"""
        return self._cosine_similarity(np.array(vector1), np.array(vector2))
    """類似度計算クラス"""

    def __init__(
        self,
        default_metric: SimilarityMetric = SimilarityMetric.COSINE
    ):
        self.default_metric = default_metric

    def calculate_similarity(
        self,
        vector1: np.ndarray,
        vector2: np.ndarray,
        metric: Optional[SimilarityMetric] = None
    ) -> float:
        """2つのベクトル間の類似度を計算"""
        if metric is None:
            metric = self.default_metric

        try:
            # ベクトルの正規化チェック
            if len(vector1) != len(vector2):
                logger.warning(
                    "Vector dimension mismatch",
                    extra_data={
                        "vector1_dim": len(vector1),
                        "vector2_dim": len(vector2)
                    }
                )
                return 0.0

            if metric == SimilarityMetric.COSINE:
                return self._cosine_similarity(vector1, vector2)
            elif metric == SimilarityMetric.EUCLIDEAN:
                return self._euclidean_similarity(vector1, vector2)
            elif metric == SimilarityMetric.DOT_PRODUCT:
                return self._dot_product_similarity(vector1, vector2)
            elif metric == SimilarityMetric.MANHATTAN:
                return self._manhattan_similarity(vector1, vector2)
            else:
                logger.warning(
                    f"Unknown similarity metric: {metric}, using cosine"
                )
                return self._cosine_similarity(vector1, vector2)

        except Exception as e:
            logger.error(
                "Failed to calculate similarity",
                error_code="SIMILARITY_CALC_ERROR",
                metric=metric.value,
                error=str(e)
            )
            return 0.0

    def _cosine_similarity(
        self,
        vector1: np.ndarray,
        vector2: np.ndarray
    ) -> float:
        """コサイン類似度を計算"""
        # ゼロベクトルのチェック
        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        # コサイン類似度計算
        dot_product = np.dot(vector1, vector2)
        similarity = dot_product / (norm1 * norm2)

        # 数値安定性のためのクリッピング
        return float(np.clip(similarity, -1.0, 1.0))

    def _euclidean_similarity(
        self,
        vector1: np.ndarray,
        vector2: np.ndarray
    ) -> float:
        """ユークリッド距離ベースの類似度を計算"""
        distance = np.linalg.norm(vector1 - vector2)
        # 距離を類似度に変換 (0-1の範囲)
        # 最大距離を sqrt(2) と仮定（正規化ベクトルの場合）
        max_distance = np.sqrt(2)
        similarity = 1.0 - min(distance / max_distance, 1.0)
        return float(similarity)

    def _dot_product_similarity(
        self,
        vector1: np.ndarray,
        vector2: np.ndarray
    ) -> float:
        """内積ベースの類似度を計算"""
        dot_product = np.dot(vector1, vector2)
        # 正規化ベクトルの場合、内積は-1から1の範囲
        # 0-1の範囲に変換
        similarity = (dot_product + 1.0) / 2.0
        return float(np.clip(similarity, 0.0, 1.0))

    def _manhattan_similarity(
        self,
        vector1: np.ndarray,
        vector2: np.ndarray
    ) -> float:
        """マンハッタン距離ベースの類似度を計算"""
        distance = np.sum(np.abs(vector1 - vector2))
        # 正規化ベクトルの最大マンハッタン距離は2
        max_distance = 2.0
        similarity = 1.0 - min(distance / max_distance, 1.0)
        return float(similarity)

    def rank_by_similarity(
        self,
        query_vector: np.ndarray,
        candidate_vectors: List[Tuple[str, np.ndarray]],
        metric: Optional[SimilarityMetric] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """クエリベクトルに対する候補ベクトルの類似度ランキング"""
        try:
            results = []

            for vector_id, vector in candidate_vectors:
                similarity = self.calculate_similarity(
                    query_vector, vector, metric
                )
                results.append({
                    "id": vector_id,
                    "similarity": similarity
                })

            # 類似度でソート（降順）
            results.sort(key=lambda x: x["similarity"], reverse=True)

            # top_k による制限
            if top_k is not None:
                results = results[:top_k]

            logger.debug(
                "Similarity ranking completed",
                extra_data={
                    "query_dim": len(query_vector),
                    "candidate_count": len(candidate_vectors),
                    "result_count": len(results),
                    "metric": (metric or self.default_metric).value
                }
            )

            return results

        except Exception as e:
            logger.error(
                "Failed to rank by similarity",
                error_code="SIMILARITY_RANK_ERROR",
                candidate_count=len(candidate_vectors),
                error=str(e)
            )
            return []

    def batch_similarity(
        self,
        query_vector: np.ndarray,
        target_vectors: np.ndarray,
        metric: Optional[SimilarityMetric] = None
    ) -> np.ndarray:
        """バッチで類似度を計算（効率的な実装）"""
        if metric is None:
            metric = self.default_metric

        try:
            if metric == SimilarityMetric.COSINE:
                return self._batch_cosine_similarity(
                    query_vector, target_vectors
                )
            elif metric == SimilarityMetric.DOT_PRODUCT:
                return self._batch_dot_product_similarity(
                    query_vector, target_vectors
                )
            else:
                # その他のメトリックは個別計算にフォールバック
                similarities = []
                for target_vector in target_vectors:
                    similarity = self.calculate_similarity(
                        query_vector, target_vector, metric
                    )
                    similarities.append(similarity)
                return np.array(similarities)

        except Exception as e:
            logger.error(
                "Failed to calculate batch similarity",
                error_code="BATCH_SIMILARITY_ERROR",
                metric=metric.value,
                error=str(e)
            )
            return np.zeros(len(target_vectors))

    def _batch_cosine_similarity(
        self,
        query_vector: np.ndarray,
        target_vectors: np.ndarray
    ) -> np.ndarray:
        """バッチコサイン類似度計算"""
        # クエリベクトルの正規化
        query_norm = np.linalg.norm(query_vector)
        if query_norm == 0:
            return np.zeros(len(target_vectors))

        query_normalized = query_vector / query_norm

        # ターゲットベクトルの正規化
        target_norms = np.linalg.norm(target_vectors, axis=1)
        # ゼロベクトルを避けるため、小さい値で置き換え
        target_norms = np.where(target_norms == 0, 1e-8, target_norms)
        target_normalized = target_vectors / target_norms.reshape(-1, 1)

        # バッチ内積計算
        similarities = np.dot(target_normalized, query_normalized)

        # 数値安定性のためのクリッピング
        return np.clip(similarities, -1.0, 1.0)

    def _batch_dot_product_similarity(
        self,
        query_vector: np.ndarray,
        target_vectors: np.ndarray
    ) -> np.ndarray:
        """バッチ内積類似度計算"""
        dot_products = np.dot(target_vectors, query_vector)
        # 0-1の範囲に変換
        similarities = (dot_products + 1.0) / 2.0
        return np.clip(similarities, 0.0, 1.0)

    def find_most_similar(
        self,
        query_vector: np.ndarray,
        candidate_vectors: List[Tuple[str, np.ndarray]],
        metric: Optional[SimilarityMetric] = None,
        threshold: float = 0.0
    ) -> Optional[Dict[str, Any]]:
        """最も類似したベクトルを検索"""
        rankings = self.rank_by_similarity(
            query_vector, candidate_vectors, metric, top_k=1
        )

        if rankings and rankings[0]["similarity"] >= threshold:
            return rankings[0]

        return None

    def find_similar_above_threshold(
        self,
        query_vector: np.ndarray,
        candidate_vectors: List[Tuple[str, np.ndarray]],
        threshold: float = 0.7,
        metric: Optional[SimilarityMetric] = None
    ) -> List[Dict[str, Any]]:
        """閾値以上の類似度を持つベクトルを検索"""
        rankings = self.rank_by_similarity(
            query_vector, candidate_vectors, metric
        )

        return [
            result for result in rankings
            if result["similarity"] >= threshold
        ]

    def calculate_diversity_score(
        self,
        vectors: List[np.ndarray],
        metric: Optional[SimilarityMetric] = None
    ) -> float:
        """ベクトル群の多様性スコアを計算"""
        if len(vectors) < 2:
            return 1.0  # 単一または空の場合は最大多様性

        try:
            total_similarity = 0.0
            pair_count = 0

            # 全ペアの類似度を計算
            for i in range(len(vectors)):
                for j in range(i + 1, len(vectors)):
                    similarity = self.calculate_similarity(
                        vectors[i], vectors[j], metric
                    )
                    total_similarity += similarity
                    pair_count += 1

            # 平均類似度を計算
            avg_similarity = total_similarity / pair_count

            # 多様性スコア = 1 - 平均類似度
            diversity_score = 1.0 - avg_similarity

            return float(np.clip(diversity_score, 0.0, 1.0))

        except Exception as e:
            logger.error(
                "Failed to calculate diversity score",
                error_code="DIVERSITY_SCORE_ERROR",
                vector_count=len(vectors),
                error=str(e)
            )
            return 0.0
