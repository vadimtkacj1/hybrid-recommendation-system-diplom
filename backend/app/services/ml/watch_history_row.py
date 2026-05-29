from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WatchHistoryRowIn:
    video_id: str
    has_video_metadata: bool
    title: str | None = None
    channel_title: str | None = None
    category_id: str | None = None
    description: str | None = None
    tags: str | None = None
    watched_at: datetime | None = None
