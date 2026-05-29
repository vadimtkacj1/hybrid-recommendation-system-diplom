from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_recommendation_service
from app.models.user import User
from app.schemas.similarity import (
    SimilarUserList, SimilarUserResponse,
    AlgorithmCompareResponse, AlgoResultItem, CompareMetrics,
    QualityMetricsResponse, AlgorithmQualityMetrics, QualityMetrics,
    HybridSpecificMetrics,
)
from app.services.recommendation import RecommendationService
from app.services.quality_metrics import QualityMetricsCalculator
from app.core.config import settings
from datetime import datetime

router = APIRouter(tags=["Recommendations"])


@router.get("/similar-users", response_model=SimilarUserList)
def get_similar_users(
    limit: int = Query(default=50, ge=1, le=1000),
    min_similarity: float = Query(default=0.1, ge=0.0, le=1.0),
    algo: Literal["tfidf", "semantic", "hybrid"] = Query(
        default="hybrid",
        description=f"Algorithm: 'tfidf' (keyword-based), 'semantic' (sentence-transformers), "
                    f"'hybrid' ({settings.CONTENT_WEIGHT:.0%} content + {settings.COLLABORATIVE_WEIGHT:.0%} overlap)",
    ),
    use_mmr: bool = Query(
        default=False,
        description="Enable MMR diversification for more diverse recommendations"
    ),
    use_adaptive: bool = Query(
        default=True,
        description="Use adaptive weighting based on user profile maturity"
    ),
    explain: bool = Query(
        default=False,
        description="Include explanations for why users were matched"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    from app.services.recommendation.similar_users_enhanced import find_similar_users

    similar = find_similar_users(
        recommender=recommendation_service._get_recommender(),
        db=db,
        user_id=current_user.id,
        top_k=limit,
        min_similarity=min_similarity,
        algo=algo,
        use_mmr=use_mmr,
        use_adaptive_weights=use_adaptive,
        include_explanations=explain,
    )
    return SimilarUserList(
        users=[SimilarUserResponse(**u) for u in similar],
        total=len(similar),
    )


@router.get("/compare", response_model=AlgorithmCompareResponse)
def compare_algorithms(
    limit: int = Query(default=50, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    data = recommendation_service.compare_algorithms(
        db=db,
        user_id=current_user.id,
        top_k=limit,
    )

    def to_algo_result(d: dict) -> AlgoResultItem:
        return AlgoResultItem(
            users=[SimilarUserResponse(**u) for u in d["users"]],
            avg_similarity=d["avg_similarity"],
            count=d["count"],
        )

    return AlgorithmCompareResponse(
        tfidf=to_algo_result(data["tfidf"]),
        semantic=to_algo_result(data["semantic"]),
        hybrid=to_algo_result(data["hybrid"]),
        metrics=CompareMetrics(**data["metrics"]),
    )


@router.get("/profile")
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    profile = recommendation_service.get_user_profile(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found. Sync your YouTube history first.",
        )
    return profile


@router.get("/quality-metrics", response_model=QualityMetricsResponse)
def get_quality_metrics(
    top_k: int = Query(default=10, ge=1, le=100),
    min_shared_categories: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    calculator = QualityMetricsCalculator(recommendation_service._get_recommender())
    metrics_data = calculator.calculate_metrics(db, top_k, min_shared_categories)

    return QualityMetricsResponse(
        metrics=AlgorithmQualityMetrics(
            tfidf=QualityMetrics(**metrics_data["tfidf"]),
            semantic=QualityMetrics(**metrics_data["semantic"]),
            hybrid=QualityMetrics(**metrics_data["hybrid"]),
            hybrid_specific=HybridSpecificMetrics(**metrics_data["hybrid_specific"]),
            evaluated_users=metrics_data["evaluated_users"],
            top_k=metrics_data["top_k"],
            min_shared_categories=metrics_data["min_shared_categories"],
        ),
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/cache-stats")
def get_cache_stats():
    """Get vector cache statistics for monitoring."""
    from app.services.ml.vector_cache import get_vector_cache

    cache = get_vector_cache()
    stats = cache.get_stats()

    return {
        "cache_stats": stats,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/cache-cleanup")
def cleanup_cache():
    """Manually trigger cache cleanup of expired entries."""
    from app.services.ml.vector_cache import get_vector_cache

    cache = get_vector_cache()
    removed = cache.cleanup_expired()

    return {
        "removed_entries": removed,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/cold-start-check")
def check_cold_start_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check if current user is in cold start mode."""
    from app.services.ml.cold_start_handler import ColdStartHandler

    is_cold_start = ColdStartHandler.should_use_cold_start(db, current_user.id)

    from sqlalchemy import func
    from app.models.watch_history import WatchHistory

    video_count = (
        db.query(func.count(WatchHistory.id))
        .filter(WatchHistory.user_id == current_user.id)
        .scalar()
    ) or 0

    return {
        "is_cold_start": is_cold_start,
        "video_count": video_count,
        "threshold": 10,
        "recommendation_strategy": "cold_start" if is_cold_start else "standard",
    }
