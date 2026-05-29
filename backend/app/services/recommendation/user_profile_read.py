from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.watch_history import WatchHistory


def get_user_sync_status(db: Session, user_id: str) -> dict[str, Any]:
    count = db.query(WatchHistory).filter(WatchHistory.user_id == user_id).count()
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    return {
        "video_count": count,
        "profile_computed": profile is not None and profile.interest_vector is not None,
    }


def get_user_profile(db: Session, user_id: str) -> Optional[dict[str, Any]]:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        return None
    user = db.query(User).filter(User.id == user_id).first()

    real_count = (
        db.query(func.count(WatchHistory.id))
        .filter(WatchHistory.user_id == user_id, ~WatchHistory.video_id.like("int_%"))
        .scalar()
    ) or 0

    total_count = db.query(WatchHistory).filter(WatchHistory.user_id == user_id).count()
    has_interests = total_count > 0 and real_count == 0

    return {
        "video_count": real_count,
        "has_interests": has_interests,
        "top_categories": profile.top_categories or [],
        "top_topics": profile.top_topics or [],
        "computed_at": profile.computed_at.isoformat() if profile.computed_at else None,
        "has_semantic_vector": profile.semantic_vector is not None,
        "youtube_connected": bool(user and False),
    }
