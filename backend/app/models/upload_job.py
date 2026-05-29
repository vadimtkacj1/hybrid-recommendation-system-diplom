"""UploadJob  tracks async watch-history processing jobs."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class UploadJob(Base):
    __tablename__ = "upload_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    # pending | processing | completed | failed
    status = Column(String, default="pending", nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    synced_count = Column(Integer, nullable=True)
    total_count = Column(Integer, nullable=True)
    profile_updated = Column(String, nullable=True)  # "true" | "false"
    error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
