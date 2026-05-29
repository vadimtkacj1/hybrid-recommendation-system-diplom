import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_recommendation_service
from app.models.upload_job import UploadJob
from app.models.user import User
from app.schemas.upload_job import UploadJobQueued, UploadJobStatus
from app.services import job_worker
from app.services.recommendation import RecommendationService

router = APIRouter(tags=["YouTube"])
logger = logging.getLogger(__name__)

_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("/watch-history", response_model=UploadJobQueued)
async def upload_watch_history_json(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    raw = await file.read()

    if len(raw) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large (max {_MAX_UPLOAD_BYTES // (1024 * 1024)} MB).",
        )
    if not raw.strip():
        raise HTTPException(status_code=400, detail="Empty file.")

    job_id = job_worker.create_and_submit(current_user.id, raw, recommendation_service)
    return UploadJobQueued(job_id=job_id)


@router.get("/watch-history/active-job", response_model=UploadJobStatus | None)
async def get_active_upload_job(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job: UploadJob | None = (
        db.query(UploadJob)
        .filter(
            UploadJob.user_id == current_user.id,
            UploadJob.status.in_(["pending", "processing"]),
        )
        .order_by(UploadJob.created_at.desc())
        .first()
    )
    if job is None:
        return None
    return UploadJobStatus(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        synced_count=job.synced_count,
        total_count=job.total_count,
        profile_updated=(job.profile_updated == "true") if job.profile_updated is not None else None,
        error=job.error,
    )


@router.get("/watch-history/job/{job_id}", response_model=UploadJobStatus)
async def get_upload_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job: UploadJob | None = (
        db.query(UploadJob)
        .filter(UploadJob.id == job_id, UploadJob.user_id == current_user.id)
        .first()
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    return UploadJobStatus(
        job_id=job.id,
        status=job.status,
        progress=job.progress,
        synced_count=job.synced_count,
        total_count=job.total_count,
        profile_updated=(job.profile_updated == "true") if job.profile_updated is not None else None,
        error=job.error,
    )


@router.get("/status")
async def youtube_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    status = recommendation_service.get_user_sync_status(db, current_user.id)
    return status
