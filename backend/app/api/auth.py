from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.deps import get_auth_service, get_db
from app.models.watch_history import WatchHistory
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserInfo
from app.services.auth import AuthService

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        tokens, user_info = AuthService.register(request.email, request.password, request.name, db)
        return TokenResponse(access_token=tokens["access_token"], user=UserInfo(**user_info))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        tokens, user_info = AuthService.login(request.email, request.password, db)
        return TokenResponse(access_token=tokens["access_token"], user=UserInfo(**user_info))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=UserInfo)
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
):
    user = auth_service.verify_token(credentials.credentials, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    has_history = db.query(WatchHistory).filter(WatchHistory.user_id == user.id).first() is not None
    return UserInfo(
        id=str(user.id),
        email=user.email,
        name=user.name,
        picture=user.picture_url,
        has_watch_history=has_history,
    )
