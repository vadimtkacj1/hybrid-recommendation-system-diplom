from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "Social Search by YouTube"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "sqlite:///./social_search.db"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def normalize_sqlite_url(cls, v: str) -> str:
        # aiosqlite requires async context; replace with sync driver
        if "aiosqlite" in v:
            return v.replace("sqlite+aiosqlite", "sqlite", 1)
        return v

    # JWT
    SECRET_KEY: str = "dev-secret-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 2  # 2 hours

    # CORS (Vite dev server uses port 5000 in this project)
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ]

    # ML settings
    EMBEDDING_DIM: int = 128
    MIN_WATCH_COUNT: int = 5  # Minimum videos for profile
    SIMILARITY_TOP_K: int = 20
    CONTENT_WEIGHT: float = 0.6  # Hybrid: content vs behavioral
    COLLABORATIVE_WEIGHT: float = 0.4
    SEMANTIC_MODEL_NAME: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore unknown env vars (e.g. APP_ENV)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
