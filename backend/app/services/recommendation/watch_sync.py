from __future__ import annotations

import logging
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.models.watch_history import VideoMetadata, WatchHistory
from app.schemas.watch_history import WatchHistoryItemCreate
from app.services.takeout_parser import parse_takeout_json

logger = logging.getLogger(__name__)


def persist_watch_history_items(
    db: Session,
    user_id: str,
    raw_items: list[WatchHistoryItemCreate],
    on_progress: Callable[[int, int], None] | None = None,
) -> tuple[int, int]:
    synced = 0
    total_items = len(raw_items)
    report_every = max(1, total_items // 20)
    for i, item in enumerate(raw_items):
        if on_progress and i % report_every == 0:
            on_progress(i, total_items)
        video_id = item.video_id
        vm = db.query(VideoMetadata).filter(VideoMetadata.id == video_id).first()
        if vm is None:
            vm = VideoMetadata(
                id=video_id,
                title=item.title,
                channel_id=item.channel_id,
                channel_title=item.channel_title,
                category_id=item.category_id,
                tags=item.tags,
                description=(item.description or "")[:2000],
            )
            db.add(vm)
            db.flush()

        existing = db.query(WatchHistory).filter(
            WatchHistory.user_id == user_id,
            WatchHistory.video_id == video_id,
        ).first()
        if not existing:
            db.add(WatchHistory(
                user_id=user_id,
                video_id=video_id,
                watched_at=item.watched_at,
            ))
            synced += 1

    db.commit()
    total = db.query(WatchHistory).filter(WatchHistory.user_id == user_id).count()
    return synced, total


def import_watch_history_json(
    db: Session,
    user_id: str,
    json_bytes: bytes,
    *,
    ensure_profile_updated: Callable[[Session, str], bool],
) -> dict[str, Any]:
    total_before = db.query(WatchHistory).filter(WatchHistory.user_id == user_id).count()
    try:
        raw_items = parse_takeout_json(json_bytes)
    except ValueError as e:
        return {
            "synced_count": 0,
            "total_count": total_before,
            "profile_updated": False,
            "error": str(e),
        }

    if not raw_items:
        return {
            "synced_count": 0,
            "total_count": total_before,
            "profile_updated": False,
            "error": "No watch entries with recognizable YouTube video links were found in this file.",
        }

    db.query(WatchHistory).filter(
        WatchHistory.user_id == user_id,
        WatchHistory.video_id.like("int_%"),
    ).delete(synchronize_session=False)
    db.commit()

    synced, total = persist_watch_history_items(db, user_id, raw_items)
    profile_updated = ensure_profile_updated(db, user_id)
    logger.info(
        "watch-history json user=%s new=%d total=%d profile=%s",
        user_id[:8], synced, total, profile_updated,
    )
    return {
        "synced_count": synced,
        "total_count": total,
        "profile_updated": profile_updated,
    }


