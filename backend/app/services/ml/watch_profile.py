from __future__ import annotations

from app.services.ml.watch_history_row import WatchHistoryRowIn
from app.services.ml.youtube_category_map import YOUTUBE_CATEGORY_ID_TO_NAME


def materialize_watch_items_and_counters(
    rows: list[WatchHistoryRowIn],
) -> tuple[list[dict], dict[str, int], dict[str, int]]:
    items: list[dict] = []
    category_counter: dict[str, int] = {}
    channel_counter: dict[str, int] = {}

    for r in rows:
        if r.has_video_metadata:
            items.append({
                "video_title": r.title or "",
                "title": r.title or "",
                "channel_title": r.channel_title or "",
                "category": r.category_id or "",
                "tags": r.tags or "",
                "channel_description": r.description or "",
                "description": r.description or "",
                "watched_at": r.watched_at,
            })
            ch = (r.channel_title or "").strip()
            if ch:
                channel_counter[ch] = channel_counter.get(ch, 0) + 1
            cat_name = YOUTUBE_CATEGORY_ID_TO_NAME.get(str(r.category_id or "").strip())
            if cat_name:
                category_counter[cat_name] = category_counter.get(cat_name, 0) + 1
        else:
            vid = r.video_id or ""
            items.append({
                "video_title": vid,
                "title": vid,
                "channel_title": "",
                "category": "",
                "tags": "",
                "channel_description": "",
                "description": "",
                "watched_at": r.watched_at,
            })

    return items, category_counter, channel_counter
