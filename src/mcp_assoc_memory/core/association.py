"""
関連性管理コア機能
記憶間の関連性の自動生成と管理
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

from ..models.memory import Memory, MemoryDomain
from ..models.association import Association
from ..core.similarity import SimilarityCalculator, SimilarityMetric
from ..utils.logging import get_memory_logger


logger = get_memory_logger(__name__)


class AssociationType(Enum):
    """関連性の種類"""
    SEMANTIC = "semantic"  # 意味的関連
    TEMPORAL = "temporal"  # 時間的関連
    CAUSAL = "causal"     # 因果関連
    SIMILAR = "similar"   # 類似関連
    CONTEXTUAL = "contextual"  # 文脈的関連


class AssociationStrength(Enum):
    """関連強度レベル"""
    WEAK = (0.0, 0.3)
    MODERATE = (0.3, 0.7)
    STRONG = (0.7, 1.0)


class AssociationEngine:
    """関連性エンジン"""
    
    def __init__(
        self,
        similarity_calculator: Optional[SimilarityCalculator] = None,
        temporal_threshold_hours: int = 24,
        semantic_threshold: float = 0.7,
        context_window_size: int = 5
    ):
        self.similarity_calculator = (
            similarity_calculator or SimilarityCalculator()
        )
        self.temporal_threshold = timedelta(hours=temporal_threshold_hours)
        self.semantic_threshold = semantic_threshold
        self.context_window_size = context_window_size
    
    async def generate_associations(
        self,
        target_memory: Memory,
        target_embedding: np.ndarray,
        candidate_memories: List[Tuple[Memory, np.ndarray]],
        association_types: Optional[List[AssociationType]] = None
    ) -> List[Association]:
        """指定した記憶に対する関連性を生成"""
        if association_types is None:
            association_types = list(AssociationType)
        
        associations = []
        
        try:
            for assoc_type in association_types:
                type_associations = await self._generate_type_associations(
                    target_memory,
                    target_embedding,
                    candidate_memories,
                    assoc_type
                )
                associations.extend(type_associations)
            
            # 重複除去（同じペアで複数の関連タイプがある場合）
            associations = self._deduplicate_associations(associations)
            
            logger.info(
                "Associations generated",
                extra_data={
                    "target_memory_id": target_memory.id,
                    "candidate_count": len(candidate_memories),
                    "association_count": len(associations),
                    "association_types": [t.value for t in association_types]
                }
            )
            
            return associations
            
        except Exception as e:
            logger.error(
                "Failed to generate associations",
                error_code="ASSOCIATION_GENERATION_ERROR",
                target_memory_id=target_memory.id,
                error=str(e)
            )
            return []
    
    async def _generate_type_associations(
        self,
        target_memory: Memory,
        target_embedding: np.ndarray,
        candidate_memories: List[Tuple[Memory, np.ndarray]],
        association_type: AssociationType
    ) -> List[Association]:
        """特定タイプの関連性を生成"""
        associations = []
        
        for candidate_memory, candidate_embedding in candidate_memories:
            # 自己関連を除外
            if candidate_memory.id == target_memory.id:
                continue
            
            # ドメイン適合性チェック
            if not self._is_domain_compatible(
                target_memory.domain,
                candidate_memory.domain
            ):
                continue
            
            # 関連性計算
            strength = await self._calculate_association_strength(
                target_memory,
                target_embedding,
                candidate_memory,
                candidate_embedding,
                association_type
            )
            
            if strength > 0.1:  # 最小閾値
                association = Association(
                    source_memory_id=target_memory.id,
                    target_memory_id=candidate_memory.id,
                    association_type=association_type.value,
                    strength=strength,
                    auto_generated=True,
                    metadata={
                        "generation_method": association_type.value,
                        "calculated_at": datetime.utcnow().isoformat()
                    }
                )
                associations.append(association)
        
        return associations
    
    async def _calculate_association_strength(
        self,
        memory1: Memory,
        embedding1: np.ndarray,
        memory2: Memory,
        embedding2: np.ndarray,
        association_type: AssociationType
    ) -> float:
        """関連強度を計算"""
        try:
            if association_type == AssociationType.SEMANTIC:
                return self._calculate_semantic_strength(
                    embedding1, embedding2
                )
            
            elif association_type == AssociationType.TEMPORAL:
                return self._calculate_temporal_strength(memory1, memory2)
            
            elif association_type == AssociationType.SIMILAR:
                return self._calculate_similarity_strength(
                    embedding1, embedding2
                )
            
            elif association_type == AssociationType.CONTEXTUAL:
                return self._calculate_contextual_strength(memory1, memory2)
            
            elif association_type == AssociationType.CAUSAL:
                return self._calculate_causal_strength(
                    memory1, embedding1, memory2, embedding2
                )
            
            else:
                logger.warning(
                    f"Unknown association type: {association_type}"
                )
                return 0.0
                
        except Exception as e:
            logger.error(
                "Failed to calculate association strength",
                error_code="STRENGTH_CALC_ERROR",
                association_type=association_type.value,
                error=str(e)
            )
            return 0.0
    
    def _calculate_semantic_strength(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """意味的関連強度を計算"""
        similarity = self.similarity_calculator.calculate_similarity(
            embedding1,
            embedding2,
            SimilarityMetric.COSINE
        )
        
        # 意味的関連は高い類似度が必要
        if similarity >= self.semantic_threshold:
            return similarity
        
        return 0.0
    
    def _calculate_temporal_strength(
        self,
        memory1: Memory,
        memory2: Memory
    ) -> float:
        """時間的関連強度を計算"""
        time_diff = abs(memory1.created_at - memory2.created_at)
        
        if time_diff <= self.temporal_threshold:
            # 時間差が小さいほど強い関連
            strength = 1.0 - (
                time_diff.total_seconds() /
                self.temporal_threshold.total_seconds()
            )
            return max(0.0, strength)
        
        return 0.0
    
    def _calculate_similarity_strength(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """類似関連強度を計算"""
        similarity = self.similarity_calculator.calculate_similarity(
            embedding1,
            embedding2,
            SimilarityMetric.EUCLIDEAN
        )
        
        # 類似関連は中程度の類似度から有効
        if similarity >= 0.5:
            return similarity
        
        return 0.0
    
    def _calculate_contextual_strength(
        self,
        memory1: Memory,
        memory2: Memory
    ) -> float:
        """文脈的関連強度を計算"""
        strength = 0.0
        
        # タグの重複度
        common_tags = set(memory1.tags) & set(memory2.tags)
        if common_tags:
            tag_overlap = len(common_tags) / max(
                len(memory1.tags), len(memory2.tags)
            )
            strength += tag_overlap * 0.5
        
        # メタデータの類似性
        metadata_similarity = self._calculate_metadata_similarity(
            memory1.metadata,
            memory2.metadata
        )
        strength += metadata_similarity * 0.3
        
        # ドメイン関連性
        domain_strength = self._calculate_domain_strength(
            memory1.domain,
            memory2.domain
        )
        strength += domain_strength * 0.2
        
        return min(1.0, strength)
    
    def _calculate_causal_strength(
        self,
        memory1: Memory,
        embedding1: np.ndarray,
        memory2: Memory,
        embedding2: np.ndarray
    ) -> float:
        """因果関連強度を計算"""
        # 時間的順序の確認
        if memory1.created_at >= memory2.created_at:
            return 0.0  # 因果関係には時間順序が必要
        
        # 意味的関連の確認
        semantic_similarity = self.similarity_calculator.calculate_similarity(
            embedding1,
            embedding2,
            SimilarityMetric.COSINE
        )
        
        # 時間的近接度
        temporal_strength = self._calculate_temporal_strength(memory1, memory2)
        
        # 因果関連は意味的関連と時間的近接の組み合わせ
        if semantic_similarity >= 0.6 and temporal_strength > 0.2:
            return min(semantic_similarity * temporal_strength, 1.0)
        
        return 0.0
    
    def _calculate_metadata_similarity(
        self,
        metadata1: Dict[str, Any],
        metadata2: Dict[str, Any]
    ) -> float:
        """メタデータ類似度を計算"""
        if not metadata1 or not metadata2:
            return 0.0
        
        common_keys = set(metadata1.keys()) & set(metadata2.keys())
        if not common_keys:
            return 0.0
        
        matches = 0
        for key in common_keys:
            if metadata1[key] == metadata2[key]:
                matches += 1
        
        return matches / len(common_keys)
    
    def _calculate_domain_strength(
        self,
        domain1: MemoryDomain,
        domain2: MemoryDomain
    ) -> float:
        """ドメイン間関連強度を計算"""
        if domain1 == domain2:
            return 1.0
        
        # ドメイン階層による関連度
        domain_hierarchy = {
            MemoryDomain.SESSION: 0,
            MemoryDomain.PROJECT: 1,
            MemoryDomain.USER: 2,
            MemoryDomain.GLOBAL: 3
        }
        
        level1 = domain_hierarchy.get(domain1, 0)
        level2 = domain_hierarchy.get(domain2, 0)
        
        # レベル差が小さいほど関連が強い
        level_diff = abs(level1 - level2)
        strength = 1.0 - (level_diff / 3.0)
        
        return max(0.0, strength)
    
    def _is_domain_compatible(
        self,
        domain1: MemoryDomain,
        domain2: MemoryDomain
    ) -> bool:
        """ドメイン間の互換性チェック"""
        # セッションドメインは同一セッション内のみ関連可能
        # （実際の実装では session_id も確認する必要がある）
        incompatible_pairs = [
            (MemoryDomain.SESSION, MemoryDomain.GLOBAL),
        ]
        
        for d1, d2 in incompatible_pairs:
            if (domain1 == d1 and domain2 == d2) or \
               (domain1 == d2 and domain2 == d1):
                return False
        
        return True
    
    def _deduplicate_associations(
        self,
        associations: List[Association]
    ) -> List[Association]:
        """重複関連性を除去"""
        seen_pairs = set()
        deduplicated = []
        
        # 関連強度順でソート
        associations.sort(key=lambda a: a.strength, reverse=True)
        
        for assoc in associations:
            pair_key = (assoc.source_memory_id, assoc.target_memory_id)
            reverse_pair_key = (assoc.target_memory_id, assoc.source_memory_id)
            
            if (pair_key not in seen_pairs and
                    reverse_pair_key not in seen_pairs):
                seen_pairs.add(pair_key)
                deduplicated.append(assoc)
        
        return deduplicated
    
    def get_association_strength_level(
        self,
        strength: float
    ) -> AssociationStrength:
        """関連強度のレベルを取得"""
        for level in AssociationStrength:
            min_val, max_val = level.value
            if min_val <= strength <= max_val:
                return level
        
        return AssociationStrength.WEAK
    
    def filter_associations_by_strength(
        self,
        associations: List[Association],
        min_level: AssociationStrength = AssociationStrength.MODERATE
    ) -> List[Association]:
        """関連強度でフィルタリング"""
        min_strength = min_level.value[0]
        return [
            assoc for assoc in associations
            if assoc.strength >= min_strength
        ]
    
    def get_association_statistics(
        self,
        associations: List[Association]
    ) -> Dict[str, Any]:
        """関連性統計を取得"""
        if not associations:
            return {
                "total_count": 0,
                "by_type": {},
                "by_strength_level": {},
                "avg_strength": 0.0
            }
        
        # タイプ別統計
        by_type = {}
        for assoc in associations:
            assoc_type = assoc.association_type
            by_type[assoc_type] = by_type.get(assoc_type, 0) + 1
        
        # 強度レベル別統計
        by_strength_level = {}
        for assoc in associations:
            level = self.get_association_strength_level(assoc.strength)
            level_name = level.name.lower()
            by_strength_level[level_name] = (
                by_strength_level.get(level_name, 0) + 1
            )
        
        # 平均強度
        avg_strength = (
            sum(a.strength for a in associations) / len(associations)
        )
        
        return {
            "total_count": len(associations),
            "by_type": by_type,
            "by_strength_level": by_strength_level,
            "avg_strength": avg_strength,
            "max_strength": max(a.strength for a in associations),
            "min_strength": min(a.strength for a in associations)
        }
