from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings


def _normalize_db_url(url: str) -> str:
    # aiosqlite requires async context and causes MissingGreenlet in sync code
    if "aiosqlite" in url:
        return url.replace("sqlite+aiosqlite", "sqlite", 1)
    return url


def _get_engine_kwargs() -> dict:
    url = _normalize_db_url(settings.DATABASE_URL)
    kwargs = {"echo": settings.DEBUG}
    if url.startswith("sqlite"):
        # NullPool: every session gets its own connection — prevents "cannot rollback"
        # crashes when background threads (job worker) share a connection with request sessions.
        kwargs.update(
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )
    else:
        kwargs.update(
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return kwargs


engine = create_engine(_normalize_db_url(settings.DATABASE_URL), **_get_engine_kwargs())


# WAL mode lets background writers and readers run concurrently without blocking each other.
@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _record):
    if _normalize_db_url(settings.DATABASE_URL).startswith("sqlite"):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
