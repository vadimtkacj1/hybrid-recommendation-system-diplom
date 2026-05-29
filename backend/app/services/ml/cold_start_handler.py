from __future__ import annotations

import logging
from typing import Any, Optional
from collections import Counter

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user_profile import UserProfile
from app.models.watch_history import WatchHistory, VideoMetadata

logger = logging.getLogger(__name__)


class ColdStartHandler:
    """
    Handle recommendations for new users with minimal watch history.

    Strategies:
    1. Category-based matching: Find users who watch similar categories
    2. Popular users: Recommend well-connected users as fallback
    3. Manual interest templates: Use explicitly stated interests
    """

    @staticmethod
    def get_cold_start_recommendations(
        db: Session,
        user_id: str,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get recommendations for cold start users.

        Args:
            db: Database session
            user_id: Target user ID
            top_k: Number of recommendations to return

        Returns:
            List of recommended users with metadata
        """
        logger.info("Cold start recommendations for user=%s", user_id[:8])

        user_history = (
            db.query(WatchHistory, VideoMetadata)
            .outerjoin(VideoMetadata, VideoMetadata.id == WatchHistory.video_id)
            .filter(WatchHistory.user_id == user_id)
            .all()
        )

        if not user_history:
            return ColdStartHandler._get_popular_users(db, user_id, top_k)

        user_categories = []
        for wh, vm in user_history:
            if vm and vm.category_id:
                user_categories.append(vm.category_id)

        if not user_categories:
            return ColdStartHandler._get_popular_users(db, user_id, top_k)

        category_matches = ColdStartHandler._find_users_by_categories(
            db, user_id, user_categories, top_k
        )

        if len(category_matches) >= top_k:
            return category_matches[:top_k]

        popular_users = ColdStartHandler._get_popular_users(
            db, user_id, top_k - len(category_matches)
        )

        return category_matches + popular_users

    @staticmethod
    def _find_users_by_categories(
        db: Session,
        user_id: str,
        user_categories: list[str],
        top_k: int,
    ) -> list[dict[str, Any]]:
        """
        Find users who watch similar categories.

        Uses category overlap as similarity metric.
        """
        category_counter = Counter(user_categories)
        top_categories = [cat for cat, _ in category_counter.most_common(5)]

        if not top_categories:
            return []

        candidate_users = (
            db.query(WatchHistory.user_id, func.count(WatchHistory.id).label("match_count"))
            .join(VideoMetadata, VideoMetadata.id == WatchHistory.video_id)
            .filter(WatchHistory.user_id != user_id)
            .filter(VideoMetadata.category_id.in_(top_categories))
            .group_by(WatchHistory.user_id)
            .order_by(func.count(WatchHistory.id).desc())
            .limit(top_k * 2)
            .all()
        )

        if not candidate_users:
            return []

        candidate_ids = [uid for uid, _ in candidate_users]

        profiles = (
            db.query(UserProfile)
            .filter(UserProfile.user_id.in_(candidate_ids))
            .all()
        )

        profile_map = {p.user_id: p for p in profiles}

        results = []
        for uid, match_count in candidate_users:
            profile = profile_map.get(uid)
            if not profile:
                continue

            total_videos = int(profile.video_count or 0)
            if total_videos == 0:
                continue

            similarity = min(1.0, match_count / max(len(user_categories), total_videos))

            results.append({
                "user_id": uid,
                "similarity": round(similarity, 4),
                "name": None,
                "picture": None,
                "top_topics": (profile.top_topics or [])[:10],
                "video_count": total_videos,
                "match_type": "category_match",
                "shared_categories": len(set(user_categories) & set(profile.top_categories or [])),
            })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    @staticmethod
    def _get_popular_users(
        db: Session,
        user_id: str,
        top_k: int,
    ) -> list[dict[str, Any]]:
        """
        Get popular users (those with many videos watched) as fallback.
        """
        profiles = (
            db.query(UserProfile)
            .filter(UserProfile.user_id != user_id)
            .filter(UserProfile.interest_vector.isnot(None))
            .all()
        )

        if not profiles:
            return []

        profiles_with_counts = [
            (p, int(p.video_count or 0)) for p in profiles
        ]
        profiles_with_counts.sort(key=lambda x: x[1], reverse=True)

        results = []
        for profile, video_count in profiles_with_counts[:top_k]:
            results.append({
                "user_id": profile.user_id,
                "similarity": 0.5,
                "name": None,
                "picture": None,
                "top_topics": (profile.top_topics or [])[:10],
                "video_count": video_count,
                "match_type": "popular_user",
            })

        return results

    @staticmethod
    def should_use_cold_start(
        db: Session,
        user_id: str,
        min_videos: int = 10,
    ) -> bool:
        """
        Determine if cold start strategy should be used.

        Args:
            db: Database session
            user_id: Target user ID
            min_videos: Minimum videos to consider user "warm"

        Returns:
            True if cold start should be used
        """
        video_count = (
            db.query(func.count(WatchHistory.id))
            .filter(WatchHistory.user_id == user_id)
            .scalar()
        ) or 0

        return video_count < min_videos
