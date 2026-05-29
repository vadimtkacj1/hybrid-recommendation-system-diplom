from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Literal


class SimilarUserResponse(BaseModel):
    """Один схожий користувач"""
    user_id: str
    name: Optional[str] = None
    picture: Optional[str] = None
    similarity: float
    top_topics: List[str] = []
    video_count: int = 0


class SimilarUserList(BaseModel):
    """Список схожих користувачів"""
    users: List[SimilarUserResponse]
    total: int


class SimilarityResult(BaseModel):
    """Результат пошуку схожого користувача"""
    user_id: str
    display_name: str | None
    similarity_score: float
    shared_interests_count: int = 0


class SimilarUsersResponse(BaseModel):
    """Відповідь API зі списком схожих користувачів"""
    results: List[SimilarityResult]
    total_found: int


class AlgoResultItem(BaseModel):
    """Results from one algorithm"""
    users: List[SimilarUserResponse]
    avg_similarity: float
    count: int


class CompareMetrics(BaseModel):
    """Overlap and uniqueness metrics between algorithms"""
    overlap_tfidf_semantic: int
    overlap_tfidf_hybrid: int
    overlap_semantic_hybrid: int
    overlap_all_three: int
    unique_to_tfidf: int
    unique_to_semantic: int
    unique_to_hybrid: int


class AlgorithmCompareResponse(BaseModel):
    """A/B comparison of all 3 recommendation algorithms"""
    tfidf: AlgoResultItem
    semantic: AlgoResultItem
    hybrid: AlgoResultItem
    metrics: CompareMetrics


class QualityMetrics(BaseModel):
    """Quality metrics for recommendation algorithm"""
    precision_at_k: float
    recall_at_k: float
    f1_score: float
    ndcg_at_k: float
    diversity_score: float
    coverage: float
    avg_similarity: float
    map_score: float
    mrr_score: float


class HybridSpecificMetrics(BaseModel):
    """Metrics specific to hybrid recommendation systems"""
    content_contribution: float
    collaborative_contribution: float
    balance_score: float
    synergy_score: float
    content_only_precision: float
    collaborative_only_precision: float
    hybrid_improvement: float
    weight_effectiveness: float


class AlgorithmQualityMetrics(BaseModel):
    """Quality metrics for each algorithm"""
    tfidf: QualityMetrics
    semantic: QualityMetrics
    hybrid: QualityMetrics
    hybrid_specific: HybridSpecificMetrics
    evaluated_users: int
    top_k: int
    min_shared_categories: int


class QualityMetricsResponse(BaseModel):
    """Response with quality metrics for all algorithms"""
    metrics: AlgorithmQualityMetrics
    timestamp: str
