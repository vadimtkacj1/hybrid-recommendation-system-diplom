import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.watch_history import WatchHistory

logger = logging.getLogger(__name__)


class AuthService:

    @staticmethod
    def hash_password(password: str) -> str:
        encoded = password.encode("utf-8")
        if len(encoded) > 72:
            raise ValueError("Password must be 72 characters or fewer.")
        return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def verify_token(token: str, db: Session) -> Optional[User]:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return db.query(User).filter(User.id == user_id).first()
        except JWTError:
            return None

    @staticmethod
    def register(email: str, password: str, name: str, db: Session) -> tuple[dict, dict]:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError("Email already registered")
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=email,
            name=name,
            password_hash=AuthService.hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("New user registered %s", email)
        token = AuthService.create_access_token({"sub": user.id, "email": user.email})
        return (
            {"access_token": token, "token_type": "bearer"},
            {"id": user.id, "email": user.email, "name": user.name, "picture": user.picture_url, "has_watch_history": False},
        )

    @staticmethod
    def login(email: str, password: str, db: Session) -> tuple[dict, dict]:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.password_hash:
            raise ValueError("Invalid email or password")
        if not AuthService.verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")
        logger.info("User logged in %s", email)
        token = AuthService.create_access_token({"sub": user.id, "email": user.email})
        has_history = db.query(WatchHistory).filter(WatchHistory.user_id == user.id).first() is not None
        return (
            {"access_token": token, "token_type": "bearer"},
            {"id": user.id, "email": user.email, "name": user.name, "picture": user.picture_url, "has_watch_history": has_history},
        )
