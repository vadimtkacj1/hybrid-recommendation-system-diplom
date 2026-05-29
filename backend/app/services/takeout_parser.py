import json
import logging
import re
from typing import List

from app.schemas.watch_history import WatchHistoryItemCreate

logger = logging.getLogger(__name__)

_VID_RE = re.compile(
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([A-Za-z0-9_-]{11})"
)
_MAX_ROWS = 200_000


def parse_takeout_json(raw: bytes, max_rows: int = _MAX_ROWS) -> List[WatchHistoryItemCreate]:
    text = raw.decode("utf-8", errors="strict")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        trimmed = text.strip().rstrip(",")
        if trimmed.startswith("{") and "},{" in trimmed:
            try:
                data = json.loads(f"[{trimmed}]")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}") from e
        else:
            raise ValueError(f"Invalid JSON: {e}") from e
    except UnicodeDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    if isinstance(data, dict):
        for k in ("watch-history", "watchHistory", "history"):
            if k in data and isinstance(data[k], list):
                data = data[k]
                break
        if isinstance(data, dict):
            data = [data]

    if not isinstance(data, list):
        raise ValueError("Expected a JSON array (YouTube export: watch-history.json).")

    seen: set = set()
    items: List[WatchHistoryItemCreate] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        url = row.get("titleUrl") or row.get("titleURL") or ""
        m = _VID_RE.search(url or "")
        if not m:
            continue
        vid = m.group(1)
        if vid in seen:
            continue
        seen.add(vid)
        title = row.get("title")
        if isinstance(title, str) and title.startswith("Watched "):
            title = title[len("Watched "):].strip()
        channel_title = None
        subtitles = row.get("subtitles")
        if isinstance(subtitles, list) and subtitles:
            first = subtitles[0]
            if isinstance(first, dict):
                raw_name = first.get("name")
                if isinstance(raw_name, str):
                    channel_title = raw_name.strip() or None
        watched_at = row.get("time")
        items.append(WatchHistoryItemCreate(
            user_id="",
            video_id=vid,
            title=(title or None) if isinstance(title, str) else None,
            channel_title=channel_title,
            watched_at=watched_at if isinstance(watched_at, str) else None,
        ))
        if len(items) >= max_rows:
            logger.warning("Takeout import truncated at %d rows", max_rows)
            break

    return items
