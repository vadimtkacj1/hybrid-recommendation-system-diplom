from __future__ import annotations

import logging
from typing import Any, Optional
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.watch_history import WatchHistory
from app.services.ml.hybrid_recommender import HybridRecommender
from app.services.ml.mmr_diversifier import MMRDiversifier
from app.services.ml.adaptive_weighting import AdaptiveWeighting
from app.services.ml.explainability import RecommendationExplainer
from app.services.ml.cold_start_handler import ColdStartHandler
from app.services.recommendation.types import AlgoType

logger = logging.getLogger(__name__)


def find_similar_users(
    recommender: HybridRecommender,
    db: Session,
    user_id: str,
    top_k: int = 10,
    min_similarity: float = 0.0,
    algo: AlgoType = "hybrid",
    use_mmr: bool = False,
    mmr_lambda: float = 0.7,
    use_adaptive_weights: bool = False,
    include_explanations: bool = False,
) -> list[dict[str, Any]]:
    logger.info("find_similar_users user=%s algo=%s top_k=%d mmr=%s adaptive=%s explain=%s",
                user_id[:8], algo, top_k, use_mmr, use_adaptive_weights, include_explanations)

    # Check if cold start strategy should be used
    if ColdStartHandler.should_use_cold_start(db, user_id, min_videos=10):
        logger.info("Using cold start strategy for user=%s", user_id[:8])
        return ColdStartHandler.get_cold_start_recommendations(db, user_id, top_k)

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile is None or profile.interest_vector is None:
        logger.info("No profile found for user=%s, using cold start", user_id[:8])
        return ColdStartHandler.get_cold_start_recommendations(db, user_id, top_k)

    if algo == "semantic" and profile.semantic_vector is None:
        return []

    all_profiles = (
        db.query(UserProfile, User)
        .join(User, User.id == UserProfile.user_id)
        .filter(UserProfile.user_id != user_id)
        .filter(UserProfile.interest_vector.isnot(None))
        .all()
    )

    if not all_profiles:
        return []

    user_ids = [str(p[1].id) for p in all_profiles]

    # subquery avoids SQLite's 999-variable IN-clause limit when there are many users
    profile_subq = (
        db.query(UserProfile.user_id)
        .filter(UserProfile.user_id != user_id)
        .filter(UserProfile.interest_vector.isnot(None))
        .subquery()
    )

    watch_counts: dict[str, int] = {}
    for uid, cnt in (
        db.query(WatchHistory.user_id, func.count(WatchHistory.id))
        .filter(WatchHistory.user_id.in_(profile_subq))
        .group_by(WatchHistory.user_id)
        .all()
    ):
        watch_counts[str(uid)] = int(cnt)

    if algo == "semantic":
        target_vector = profile.semantic_vector
        profile_vectors = [p[0].semantic_vector for p in all_profiles]
    else:
        target_vector = profile.interest_vector
        profile_vectors = [p[0].interest_vector for p in all_profiles]

    target_video_ids: set[str] | None = None
    other_video_ids: dict[str, set[str]] | None = None
    content_weight = 0.7
    collab_weight = 0.3

    target_als_vector = None
    other_als_vectors: dict[str, Any] | None = None
    als_weight = 0.0

    if algo == "hybrid":
        target_video_ids = {
            str(r[0]) for r in db.query(WatchHistory.video_id)
            .filter(WatchHistory.user_id == user_id).all()
        }
        other_video_ids = {}
        rows = db.query(WatchHistory.user_id, WatchHistory.video_id)\
            .filter(WatchHistory.user_id.in_(profile_subq)).all()
        for uid, vid in rows:
            other_video_ids.setdefault(str(uid), set()).add(str(vid))

        # підключаємо ALS якщо вектор є у цільового користувача
        if profile.als_vector is not None:
            target_als_vector = profile.als_vector
            other_als_vectors = {
                str(p[0].user_id): p[0].als_vector
                for p in all_profiles
                if p[0].als_vector is not None
            }
            als_weight = 0.3
            logger.info(
                "ALS collaborative signal enabled for user=%s (als_weight=%.1f)",
                user_id[:8], als_weight,
            )

        # Apply adaptive weighting if enabled
        if use_adaptive_weights:
            video_count = int(profile.video_count) if profile.video_count else 0
            category_diversity = AdaptiveWeighting.calculate_category_diversity(
                profile.top_topics or []
            )

            # Calculate profile age
            profile_age_days = None
            if profile.computed_at:
                profile_age_days = (datetime.utcnow() - profile.computed_at).days

            content_weight, collab_weight = AdaptiveWeighting.get_weights(
                video_count=video_count,
                category_diversity=category_diversity,
                profile_age_days=profile_age_days,
            )

            logger.info(
                "Adaptive weights for user %s: content=%.2f, collab=%.2f (videos=%d, diversity=%.2f)",
                user_id[:8], content_weight, collab_weight, video_count, category_diversity
            )

    similarities = recommender.compute_similarities(
        target_vector,
        profile_vectors,
        user_ids,
        top_k=top_k * 3 if use_mmr else top_k,  # Get more candidates for MMR
        target_video_ids=target_video_ids,
        other_video_ids=other_video_ids,
        content_weight=content_weight,
        overlap_weight=collab_weight,
        algo=algo,
        return_explanations=include_explanations,
        target_als_vector=target_als_vector,
        other_als_vectors=other_als_vectors,
        als_weight=als_weight,
    )

    user_map: dict[str, User] = {str(p[1].id): p[1] for p in all_profiles}
    profile_map: dict[str, UserProfile] = {str(p[0].user_id): p[0] for p in all_profiles}

    # Build result list with full profile data
    candidates: list[dict[str, Any]] = []
    target_profile_data = {
        "top_topics": profile.top_topics or [],
        "video_count": int(profile.video_count or 0),
    }

    for sim in similarities:
        if sim["similarity"] < min_similarity:
            continue
        u = user_map.get(sim["user_id"])
        p = profile_map.get(sim["user_id"])

        candidate = {
            "user_id": sim["user_id"],
            "similarity": sim["similarity"],
            "name": u.name if u else None,
            "picture": u.picture_url if u else None,
            "top_topics": (p.top_topics or [])[:10] if p else [],
            "video_count": watch_counts.get(sim["user_id"], int(p.video_count or 0) if p else 0),
            "interest_vector": p.interest_vector if p else None,
        }

        if include_explanations and "_explanation_data" in sim:
            exp_data = sim["_explanation_data"]
            matched_user_data = {
                "top_topics": (p.top_topics or []) if p else [],
                "video_count": watch_counts.get(sim["user_id"], 0),
            }

            explanation = RecommendationExplainer.explain_match(
                target_user_data=target_profile_data,
                matched_user_data=matched_user_data,
                similarity_score=sim["similarity"],
                content_similarity=exp_data["content_similarity"],
                overlap_score=exp_data["overlap_score"],
                content_weight=exp_data["content_weight"],
                overlap_weight=exp_data["overlap_weight"],
                algo=algo,
            )
            explanation["shared_videos_count"] = exp_data["shared_videos"]
            explanation["match_strength"] = RecommendationExplainer.get_match_strength_label(
                sim["similarity"]
            )
            candidate["explanation"] = explanation

        candidates.append(candidate)

    # Apply MMR diversification if enabled
    if use_mmr and len(candidates) > top_k:
        logger.info("Applying MMR diversification (lambda=%.2f) to %d candidates",
                   mmr_lambda, len(candidates))
        candidates = MMRDiversifier.diversify(
            candidates=candidates,
            top_k=top_k,
            lambda_param=mmr_lambda,
            similarity_key="similarity",
            vector_key="interest_vector",
        )

        # Calculate diversity improvement
        diversity_score = MMRDiversifier.calculate_diversity_score(candidates)
        logger.info("MMR diversity score: %.4f", diversity_score)
    else:
        candidates = candidates[:top_k]

    # Remove interest_vector from final results (not needed in API response)
    result = []
    for candidate in candidates:
        candidate_copy = candidate.copy()
        candidate_copy.pop("interest_vector", None)
        result.append(candidate_copy)

    logger.info("find_similar_users → %d results for user=%s", len(result), user_id[:8])
    return result


def compare_algorithms(
    recommender: HybridRecommender,
    db: Session,
    user_id: str,
    top_k: int = 10,
) -> dict[str, Any]:
    results: dict[str, dict[str, Any]] = {}
    for algo in ("tfidf", "semantic", "hybrid"):
        users = find_similar_users(recommender, db, user_id, top_k=top_k, algo=algo)
        avg_sim = sum(u["similarity"] for u in users) / len(users) if users else 0.0
        results[algo] = {
            "users": users,
            "avg_similarity": round(avg_sim, 4),
            "count": len(users),
        }

    ids_tfidf = {u["user_id"] for u in results["tfidf"]["users"]}
    ids_semantic = {u["user_id"] for u in results["semantic"]["users"]}
    ids_hybrid = {u["user_id"] for u in results["hybrid"]["users"]}

    metrics = {
        "overlap_tfidf_semantic": len(ids_tfidf & ids_semantic),
        "overlap_tfidf_hybrid": len(ids_tfidf & ids_hybrid),
        "overlap_semantic_hybrid": len(ids_semantic & ids_hybrid),
        "overlap_all_three": len(ids_tfidf & ids_semantic & ids_hybrid),
        "unique_to_tfidf": len(ids_tfidf - ids_semantic - ids_hybrid),
        "unique_to_semantic": len(ids_semantic - ids_tfidf - ids_hybrid),
        "unique_to_hybrid": len(ids_hybrid - ids_tfidf - ids_semantic),
    }

    return {
        "tfidf": results["tfidf"],
        "semantic": results["semantic"],
        "hybrid": results["hybrid"],
        "metrics": metrics,
    }
