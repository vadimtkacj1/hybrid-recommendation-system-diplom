from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.schemas.watch_history import WatchHistoryItemCreate
from app.services.ml.hybrid_recommender import HybridRecommender
from app.services.recommendation import profile_update, similar_users, user_profile_read, watch_sync
from app.services.recommendation.types import AlgoType


class RecommendationService:

    def __init__(self) -> None:
        self._recommender: Optional[HybridRecommender] = None

    def _get_recommender(self) -> HybridRecommender:
        if self._recommender is None:
            self._recommender = HybridRecommender()
        return self._recommender

    def find_similar_users(
        self,
        db: Session,
        user_id: str,
        top_k: int = 10,
        min_similarity: float = 0.0,
        algo: AlgoType = "hybrid",
    ) -> list[dict[str, Any]]:
        return similar_users.find_similar_users(
            self._get_recommender(), db, user_id, top_k, min_similarity, algo,
        )

    def compare_algorithms(
        self,
        db: Session,
        user_id: str,
        top_k: int = 10,
    ) -> dict[str, Any]:
        return similar_users.compare_algorithms(self._get_recommender(), db, user_id, top_k)

    def rebuild_all_profiles(self, db: Session) -> int:
        return profile_update.rebuild_all_profiles(
            self._get_recommender(),
            db,
            lambda session, uid: profile_update.ensure_user_profile_updated(
                self._get_recommender(), session, uid,
            ),
        )

    def ensure_user_profile_updated(self, db: Session, user_id: str) -> bool:
        return profile_update.ensure_user_profile_updated(self._get_recommender(), db, user_id)

    def persist_watch_history_items(
        self,
        db: Session,
        user_id: str,
        raw_items: list[WatchHistoryItemCreate],
    ) -> tuple[int, int]:
        return watch_sync.persist_watch_history_items(db, user_id, raw_items)

    def import_watch_history_json(self, db: Session, user_id: str, json_bytes: bytes) -> dict[str, Any]:
        return watch_sync.import_watch_history_json(
            db,
            user_id,
            json_bytes,
            ensure_profile_updated=lambda session, uid: self.ensure_user_profile_updated(session, uid),
        )

    def get_user_sync_status(self, db: Session, user_id: str) -> dict[str, Any]:
        return user_profile_read.get_user_sync_status(db, user_id)

    def get_user_profile(self, db: Session, user_id: str) -> Optional[dict[str, Any]]:
        return user_profile_read.get_user_profile(db, user_id)


_recommendation_service_instance: Optional[RecommendationService] = None


def get_recommendation_service() -> RecommendationService:
    global _recommendation_service_instance
    if _recommendation_service_instance is None:
        _recommendation_service_instance = RecommendationService()
    return _recommendation_service_instance
