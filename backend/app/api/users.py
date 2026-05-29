from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_recommendation_service
from app.models.user import User
from app.models.watch_history import WatchHistory
from app.schemas.user import UserResponse
from app.schemas.watch_history import WatchHistorySyncResponse
from app.services.recommendation import RecommendationService

router = APIRouter()

AVATAR_DIR = Path("uploads") / "avatars"
_MAX_AVATAR_BYTES = 3 * 1024 * 1024
_ALLOWED_AVATAR_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def _user_response(current_user: User, db: Session) -> UserResponse:
    has_history = db.query(WatchHistory).filter(WatchHistory.user_id == current_user.id).first() is not None
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture_url,
        youtube_linked=False,
        has_watch_history=has_history,
        created_at=current_user.created_at,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _user_response(current_user, db)


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    body: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.name is not None:
        name = body.name.strip()
        if not name or len(name) > 80:
            raise HTTPException(status_code=400, detail="Name must be 1–80 characters.")
        current_user.name = name
        current_user.updated_at = datetime.utcnow()
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    return _user_response(current_user, db)


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ctype = (file.content_type or "").split(";")[0].strip().lower()
    if ctype not in _ALLOWED_AVATAR_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Allowed formats: JPEG, PNG, WebP.",
        )
    ext = _ALLOWED_AVATAR_TYPES[ctype]
    raw = await file.read()
    if len(raw) > _MAX_AVATAR_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 3 MB).")

    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    for old in AVATAR_DIR.glob(f"{current_user.id}.*"):
        try:
            old.unlink()
        except OSError:
            pass

    dest = AVATAR_DIR / f"{current_user.id}{ext}"
    dest.write_bytes(raw)

    base = str(request.base_url).rstrip("/")
    current_user.picture_url = f"{base}/uploads/avatars/{dest.name}"
    current_user.updated_at = datetime.utcnow()
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return _user_response(current_user, db)


