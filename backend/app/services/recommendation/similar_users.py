from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.watch_history import WatchHistory
from app.services.ml.hybrid_recommender import HybridRecommender
from app.services.recommendation.types import AlgoType

logger = logging.getLogger(__name__)


def find_similar_users(
    recommender: HybridRecommender,
    db: Session,
    user_id: str,
    top_k: int = 10,
    min_similarity: float = 0.0,
    algo: AlgoType = "hybrid",
) -> list[dict[str, Any]]:
    logger.info("find_similar_users user=%s algo=%s top_k=%d", user_id[:8], algo, top_k)

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile is None or profile.interest_vector is None:
        return []

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

    watch_counts: dict[str, int] = {}
    if user_ids:
        for uid, cnt in (
            db.query(WatchHistory.user_id, func.count(WatchHistory.id))
            .filter(WatchHistory.user_id.in_(user_ids))
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
    if algo == "hybrid":
        target_video_ids = {
            str(r[0]) for r in db.query(WatchHistory.video_id)
            .filter(WatchHistory.user_id == user_id).all()
        }
        other_video_ids = {}
        rows = db.query(WatchHistory.user_id, WatchHistory.video_id)\
            .filter(WatchHistory.user_id.in_(user_ids)).all()
        for uid, vid in rows:
            other_video_ids.setdefault(str(uid), set()).add(str(vid))

    similarities = recommender.compute_similarities(
        target_vector,
        profile_vectors,
        user_ids,
        top_k=top_k,
        target_video_ids=target_video_ids,
        other_video_ids=other_video_ids,
        algo=algo,
    )

    user_map: dict[str, User] = {str(p[1].id): p[1] for p in all_profiles}
    profile_map: dict[str, UserProfile] = {str(p[0].user_id): p[0] for p in all_profiles}

    result: list[dict[str, Any]] = []
    for sim in similarities:
        if sim["similarity"] < min_similarity:
            continue
        u = user_map.get(sim["user_id"])
        p = profile_map.get(sim["user_id"])
        result.append({
            "user_id": sim["user_id"],
            "similarity": sim["similarity"],
            "name": u.name if u else None,
            "picture": u.picture_url if u else None,
            "top_topics": (p.top_topics or [])[:10] if p else [],
            "video_count": watch_counts.get(sim["user_id"], int(p.video_count or 0) if p else 0),
        })
        if len(result) >= top_k:
            break

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
