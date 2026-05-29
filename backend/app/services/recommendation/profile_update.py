from __future__ import annotations

import logging
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user_profile import UserProfile
from app.models.watch_history import VideoMetadata, WatchHistory
from app.services.ml.als_collaborative import compute_als_vectors
from app.services.ml.hybrid_recommender import HybridRecommender
from app.services.ml.user_category_profile import resolve_user_display_categories
from app.services.ml.watch_history_row import WatchHistoryRowIn
from app.services.ml.watch_profile import materialize_watch_items_and_counters

logger = logging.getLogger(__name__)


def ensure_tfidf_fitted(recommender: HybridRecommender, db: Session) -> None:
    if recommender.profile_builder._fitted:
        return
    all_vms = db.query(VideoMetadata).all()
    if not all_vms:
        return
    all_docs = [
        {"title": vm.title or "", "tags": vm.tags or "",
         "channel_title": vm.channel_title or "", "category": vm.category_id or ""}
        for vm in all_vms
    ]
    recommender.profile_builder.fit(all_docs)
    logger.info("TF-IDF re-fitted on %d videos after restart", len(all_docs))


def rebuild_all_profiles(recommender: HybridRecommender, db: Session, ensure_profile_fn) -> int:
    logger.info("rebuild_all_profiles: fitting TF-IDF on full corpus…")

    recommender.profile_builder._fitted = False

    all_vms = db.query(VideoMetadata).all()
    all_docs = [
        {"title": vm.title or "", "tags": vm.tags or "",
         "channel_title": vm.channel_title or "", "category": vm.category_id or ""}
        for vm in all_vms
    ]
    if all_docs:
        recommender.profile_builder.fit(all_docs)

    user_ids = [r[0] for r in db.query(WatchHistory.user_id).distinct().all()]
    logger.info("rebuild_all_profiles: %d users to process", len(user_ids))
    count = 0
    for uid in user_ids:
        if ensure_profile_fn(db, uid):
            count += 1
    logger.info("rebuild_all_profiles done: %d/%d profiles built", count, len(user_ids))

    # тренуємо ALS на матриці User×Channel і зберігаємо вектори
    logger.info("rebuild_all_profiles: training ALS on User×Channel matrix...")
    als_vectors = compute_als_vectors(db)
    if als_vectors:
        updated = 0
        for uid, vec in als_vectors.items():
            profile = db.query(UserProfile).filter(UserProfile.user_id == uid).first()
            if profile is not None:
                profile.als_vector = vec
                updated += 1
        db.commit()
        logger.info("ALS vectors saved for %d/%d users", updated, len(als_vectors))

    return count


def ensure_user_profile_updated(recommender: HybridRecommender, db: Session, user_id: str) -> bool:
    ensure_tfidf_fitted(recommender, db)

    MIN_VIDEOS = 10

    total_watches = (
        db.query(func.count(WatchHistory.id))
        .filter(WatchHistory.user_id == user_id)
        .scalar()
    ) or 0
    if total_watches < MIN_VIDEOS:
        logger.info("skip profile build user=%s: only %d videos", user_id[:8], total_watches)
        return False

    history = (
        db.query(WatchHistory, VideoMetadata)
        .outerjoin(VideoMetadata, VideoMetadata.id == WatchHistory.video_id)
        .filter(WatchHistory.user_id == user_id)
        .order_by(WatchHistory.watched_at.desc())
        .all()
    )

    rows: list[WatchHistoryRowIn] = []
    for wh, vm in history:
        if vm is not None:
            rows.append(WatchHistoryRowIn(
                video_id=wh.video_id or "",
                has_video_metadata=True,
                title=vm.title,
                channel_title=vm.channel_title,
                category_id=vm.category_id,
                description=vm.description,
                tags=vm.tags,
                watched_at=wh.watched_at,
            ))
        else:
            rows.append(WatchHistoryRowIn(
                video_id=wh.video_id or "",
                has_video_metadata=False,
                watched_at=wh.watched_at,
            ))

    items, category_counter, channel_counter = materialize_watch_items_and_counters(rows)

    vector = recommender.build_profile_vector(items)
    if vector is None:
        logger.warning("build_profile_vector returned None for user=%s", user_id[:8])
        return False

    semantic_vector = recommender.build_semantic_vector(items)
    logger.info(
        "profile built user=%s videos=%d (watch_rows=%d) tfidf_dim=%s semantic=%s",
        user_id[:8], len(items), total_watches,
        vector.shape if vector is not None else None,
        semantic_vector.shape if semantic_vector is not None else None,
    )

    top_channels = [c for c, _ in sorted(channel_counter.items(), key=lambda x: -x[1])[:5]]
    top_cats = [c for c, _ in sorted(category_counter.items(), key=lambda x: -x[1])[:6]]

    display_categories, top_topics, ml_taxonomy = resolve_user_display_categories(
        items, top_cats, top_channels,
    )

    logger.info(
        "profile user=%s | videos=%d | categories=%s | ml_taxonomy=%s | yt_categories=%s | channels=%s",
        user_id[:8], total_watches, display_categories[:4], ml_taxonomy[:4] if ml_taxonomy else [],
        top_cats, top_channels[:3],
    )

    db.query(UserProfile).filter(UserProfile.user_id == user_id).delete()
    db.flush()
    db.add(UserProfile(
        id=user_id,
        user_id=user_id,
        interest_vector=vector,
        semantic_vector=semantic_vector,
        video_count=str(total_watches),
        top_topics=top_topics,
        top_categories=display_categories[:5],
    ))
    db.commit()
    return True
