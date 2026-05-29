from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import TYPE_CHECKING

from app.core.database import SessionLocal
from app.models.upload_job import UploadJob

if TYPE_CHECKING:
    from app.services.recommendation import RecommendationService

logger = logging.getLogger(__name__)

_MIN_HISTORY_VIDEOS = 10
_pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="job-worker")


def _set_job(job_id: str, **kwargs) -> None:
    db = SessionLocal()
    try:
        job = db.query(UploadJob).filter(UploadJob.id == job_id).first()
        if job is None:
            return
        for k, v in kwargs.items():
            setattr(job, k, v)
        job.updated_at = datetime.utcnow()
        db.commit()
    except Exception:
        logger.exception("_set_job failed for job=%s", job_id[:8])
    finally:
        db.close()


def _run(job_id: str, user_id: str, raw: bytes, service: "RecommendationService") -> None:
    from app.models.watch_history import WatchHistory
    from app.services.recommendation.watch_sync import persist_watch_history_items
    from app.services.takeout_parser import parse_takeout_json

    _set_job(job_id, status="processing", progress=5)

    try:
        raw_items = parse_takeout_json(raw)
    except Exception as exc:
        logger.warning("job=%s parse error: %s", job_id[:8], exc)
        _set_job(job_id, status="failed", progress=0, error=str(exc))
        return

    if not raw_items:
        _set_job(
            job_id,
            status="failed",
            progress=0,
            error="No watch entries with recognizable YouTube video links were found in this file.",
        )
        return

    _set_job(job_id, progress=35)

    db = SessionLocal()
    try:
        # Remove synthetic manual-interest placeholders before importing real history.
        db.query(WatchHistory).filter(
            WatchHistory.user_id == user_id,
            WatchHistory.video_id.like("int_%"),
        ).delete(synchronize_session=False)
        db.commit()

        def _persist_progress(current: int, total_items: int) -> None:
            if total_items > 0:
                pct = 35 + int((current / total_items) * 30)
                _set_job(job_id, progress=pct)

        synced, total = persist_watch_history_items(db, user_id, raw_items, on_progress=_persist_progress)
        _set_job(job_id, progress=65, synced_count=synced, total_count=total)

        if total < _MIN_HISTORY_VIDEOS:
            _set_job(
                job_id,
                status="failed",
                progress=0,
                error=(
                    f"Your watch history contains only {total} video(s). "
                    f"Upload a file with at least {_MIN_HISTORY_VIDEOS} watched videos "
                    "to build a meaningful profile."
                ),
            )
            return

        _set_job(job_id, progress=80)
        updated = service.ensure_user_profile_updated(db, user_id)

        _set_job(
            job_id,
            status="completed",
            progress=100,
            synced_count=synced,
            total_count=total,
            profile_updated=str(updated),
        )
        logger.info(
            "job=%s user=%s synced=%d total=%d profile=%s",
            job_id[:8], user_id[:8], synced, total, updated,
        )
    except Exception as exc:
        logger.exception("job=%s failed during persist/profile", job_id[:8])
        _set_job(job_id, status="failed", progress=0, error=str(exc))
    finally:
        db.close()


def create_and_submit(
    user_id: str,
    raw: bytes,
    service: "RecommendationService",
) -> str:
    job_id = str(uuid.uuid4())

    # Create the job row before submitting so the polling endpoint can find it
    # even if the worker thread hasn't started yet.
    db = SessionLocal()
    try:
        db.add(UploadJob(id=job_id, user_id=user_id, status="pending", progress=0))
        db.commit()
    finally:
        db.close()

    _pool.submit(_run, job_id, user_id, raw, service)
    logger.info("queued job=%s user=%s bytes=%d", job_id[:8], user_id[:8], len(raw))
    return job_id
