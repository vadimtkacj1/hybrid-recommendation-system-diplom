from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class VideoMetadata(Base):
    __tablename__ = "video_metadata"

    id = Column(String, primary_key=True, index=True)  # video_id
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    channel_id = Column(String, nullable=True)
    channel_title = Column(String, nullable=True)
    category_id = Column(String, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array or comma-separated
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    watch_records = relationship("WatchHistory", back_populates="video")


class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(String, ForeignKey("video_metadata.id", ondelete="CASCADE"), nullable=False)
    watched_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="watch_history")
    video = relationship("VideoMetadata", back_populates="watch_records")
