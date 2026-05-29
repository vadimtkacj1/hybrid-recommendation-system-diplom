from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WatchHistoryItemCreate(BaseModel):
    """Watch history row built from YouTube API video details."""
    user_id: str = ""
    video_id: str
    title: Optional[str] = None
    channel_id: Optional[str] = None
    channel_title: Optional[str] = None
    category_id: Optional[str] = None
    tags: Optional[str] = None
    description: Optional[str] = None
    watched_at: Optional[datetime] = None


class WatchHistorySyncResponse(BaseModel):
    synced_count: int
    total_count: int
    profile_updated: bool
    error: Optional[str] = None
    source_note: Optional[str] = None
