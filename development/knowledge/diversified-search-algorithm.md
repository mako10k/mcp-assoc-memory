# Diversified Search Algorithm for Associative Memory

## Overview
This document outlines a proposed enhancement to the MCP Associative Memory Server's search functionality to improve creative thinking and reduce redundancy in search results.

## Problem Statement
Current similarity-based search algorithms tend to return very similar results, potentially limiting creative thinking and diverse idea generation. Users may get stuck in "similarity bubbles" that reduce the breadth of associative memory exploration.

## Proposed Solution: Diversified Search Algorithm

### Algorithm Steps
1. **Expanded Initial Search**: When N results are requested, perform similarity search for N×2 (or N×3) items
2. **Diversity Selection Process**:
   - Pick the highest similarity item → Memory A
   - Exclude other results that are too similar to Memory A
   - From remaining results, pick the next highest similarity item → Memory B
   - Continue exclusion process for Memory B
   - Repeat until N diverse results are obtained
3. **Fallback Expansion**: If filtered results < N, expand search to N×3 and repeat filtering
4. **Return Results**: Provide N diversified results or maximum available

### Academic Foundation
This approach is based on established research in "Search Result Diversification":

- **Core Concept**: Balance relevance with diversity to avoid redundant results
- **Applications**: Used in web search, recommendation systems, information retrieval
- **Key Papers**:
  - "Diversifying search results" (Agrawal et al., 2009) - 1,429 citations
  - "Multi-dimensional search result diversification" (Dou et al., 2011) - 122 citations
  - "Result diversification in search and recommendation: A survey" (Wu et al., 2024)

## User-Proposed Algorithm (Original Japanese Specification)

### Detailed Steps (Original Proposal)
ユーザから提案された具体的なアルゴリズム：

1. **要求されたN個の連想検索結果**に対して
2. **N×2程度の余裕をもって類似検索**を実行
3. **最高類似度の記憶をピックアップ** → 記憶A
4. **記憶Aと特に類似度の高いものを除外**
5. **残りの検索結果に対しても同様の除外処理**を継続
6. **フィルタ結果がN個未満の場合**、N×3で追加検索＋フィルタ実施
7. **結果N個（または検索結果が増加しなくなった時点）**で応答返却

### Benefits of This Approach
- **冗長性の削減**: 類似した内容の重複を避ける
- **創造性の向上**: より多様な連想結果を提供
- **段階的拡張**: 必要に応じて検索範囲を拡大

### Implementation Challenges
- **計算負荷の増加**: 類似度計算とフィルタリング処理
- **最適化の必要性**: 既存の類似アルゴリズムとの組み合わせ
- **閾値調整**: 除外判定の類似度閾値設定

## Implementation Considerations

### Performance Impact
- **Computational Cost**: 2-3x more similarity calculations
- **Memory Usage**: Larger initial result sets
- **Latency**: Additional filtering steps

### Optimization Strategies
1. **Threshold-based Filtering**: Define similarity thresholds for exclusion
2. **Incremental Processing**: Process results in batches
3. **Caching**: Cache diversity calculations for frequently accessed content
4. **Parallel Processing**: Compute similarities in parallel

### Configuration Parameters
```python
class DiversifiedSearchConfig:
    expansion_factor: float = 2.0          # Initial search multiplier
    diversity_threshold: float = 0.8       # Similarity threshold for exclusion
    max_expansion_factor: float = 3.0      # Maximum expansion for fallback
    enable_diversification: bool = True    # Feature toggle
```

## Algorithm Pseudocode

```python
async def diversified_search(
    query: str, 
    requested_count: int,
    config: DiversifiedSearchConfig
) -> List[Memory]:
    
    # Step 1: Expanded initial search
    initial_count = int(requested_count * config.expansion_factor)
    candidates = await similarity_search(query, initial_count)
    
    # Step 2: Diversity selection
    selected = []
    remaining = candidates.copy()
    
    while len(selected) < requested_count and remaining:
        # Pick highest similarity from remaining
        best = max(remaining, key=lambda x: x.similarity_score)
        selected.append(best)
        remaining.remove(best)
        
        # Remove similar items
        remaining = [
            item for item in remaining 
            if calculate_similarity(best, item) < config.diversity_threshold
        ]
    
    # Step 3: Fallback if needed
    if len(selected) < requested_count:
        fallback_count = int(requested_count * config.max_expansion_factor)
        # Repeat with larger search space
        
    return selected[:requested_count]
```

## Benefits
1. **Enhanced Creativity**: Expose users to diverse perspectives and ideas
2. **Reduced Echo Chambers**: Break out of similarity-based thinking patterns  
3. **Comprehensive Coverage**: Better representation of the memory space
4. **Customizable**: Adjustable diversity vs. relevance trade-off

## Potential Drawbacks
1. **Performance Overhead**: 2-3x computational cost
2. **Relevance Trade-off**: Some highly relevant results may be excluded
3. **Complexity**: More parameters to tune and maintain
4. **Threshold Sensitivity**: Requires careful tuning of diversity parameters

## Implementation Priority
- **Phase 1**: Research and prototype development
- **Phase 2**: A/B testing with configurable parameters
- **Phase 3**: Production deployment with user preferences
- **Phase 4**: Machine learning optimization of parameters

## Related Research Areas
- Maximum Marginal Relevance (MMR)
- Cluster-based diversification
- Intent-aware diversification
- Personalized diversification

## References
- Agrawal, R., et al. (2009). "Diversifying search results." WSDM 2009.
- Dou, Z., et al. (2011). "Multi-dimensional search result diversification." WSDM 2011.
- Wu, H., et al. (2024). "Result diversification in search and recommendation: A survey." IEEE Transactions.

## Implementation Status
**Status**: Proposal/Research Phase  
**Next Steps**: Prototype development and performance analysis  
**Target**: Future enhancement after core features stabilization
