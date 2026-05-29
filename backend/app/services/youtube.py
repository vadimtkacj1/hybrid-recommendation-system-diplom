"""
Інтеграція з YouTube Data API v3 для отримання історії переглядів.
"""
import logging
from typing import List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from app.schemas.watch_history import WatchHistoryItemCreate

logger = logging.getLogger(__name__)


class YouTubeService:
    """Сервіс для роботи з YouTube API."""

    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.youtube = build("youtube", "v3", credentials=credentials)

    def _get_watch_history_playlist_id(self) -> Optional[str]:
        """Get the user's watch history playlist ID from their channel."""
        response = self.youtube.channels().list(
            part="contentDetails",
            mine=True,
        ).execute()
        items = response.get("items", [])
        if not items:
            return None
        return items[0].get("contentDetails", {}).get("relatedPlaylists", {}).get("watchHistory")

    def get_watch_history(self, max_results: Optional[int] = None) -> List[WatchHistoryItemCreate]:
        """
        Fetch real watch history via YouTube Data API.
        ``max_results=None`` (default): paginate until the playlist ends (full history).
        If set, stop after that many videos.
        """
        try:
            playlist_id = self._get_watch_history_playlist_id()
            if not playlist_id:
                raise ValueError(
                    "YouTube does not expose a watch-history playlist for this account via the Data API. "
                    "Google has restricted third-party access; older data in the app is unchanged."
                )

            video_ids: List[str] = []
            next_page_token: Optional[str] = None

            while True:
                if max_results is not None and len(video_ids) >= max_results:
                    break
                page_size = 50
                if max_results is not None:
                    page_size = min(50, max_results - len(video_ids))
                    if page_size <= 0:
                        break

                request = self.youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=page_size,
                    pageToken=next_page_token,
                )
                response = request.execute()
                for item in response.get("items", []):
                    vid = item.get("contentDetails", {}).get("videoId")
                    if vid:
                        video_ids.append(str(vid))
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

            if max_results is not None:
                video_ids = video_ids[:max_results]

            if not video_ids:
                return []

            logger.info("YouTube watch-history playlist returned %d video ids", len(video_ids))
            if len(video_ids) < 100:
                logger.warning(
                    "YouTube Data API returned a short watch-history list (%d items); "
                    "third-party apps often cannot see the full account history.",
                    len(video_ids),
                )

            # Крок 2: збагачуємо деталями відео
            details = self.get_video_details(video_ids)

            items = []
            for vid in video_ids:
                info = details.get(vid, {})
                items.append(
                    WatchHistoryItemCreate(
                        user_id="",
                        video_id=vid,
                        title=info.get("title", ""),
                        channel_id=info.get("channel_id", ""),
                        channel_title=info.get("channel_title", ""),
                        category_id=info.get("category_id", ""),
                        tags=",".join(info.get("tags", [])),
                        description=info.get("description", "")[:1000],
                    )
                )
            return items

        except HttpError as e:
            if "403" in str(e) or "disabled" in str(e).lower():
                raise ValueError(
                    "YouTube watch history is not accessible. "
                    "Ensure the youtube.readonly scope is granted."
                )
            raise

    def get_video_details(self, video_ids: List[str]) -> dict:
        """Отримання детальної метаданих відео по ID (для збагачення даних)."""
        if not video_ids:
            return {}
        result = {}
        for i in range(0, len(video_ids), 50):  # API limit 50 per request
            batch = video_ids[i : i + 50]
            request = self.youtube.videos().list(
                part="snippet,statistics",
                id=",".join(batch),
            )
            response = request.execute()
            for v in response.get("items", []):
                snippet = v.get("snippet", {})
                result[v["id"]] = {
                    "title": snippet.get("title", ""),
                    "channel_id": snippet.get("channelId", ""),
                    "channel_title": snippet.get("channelTitle", ""),
                    "category_id": snippet.get("categoryId", ""),
                    "tags": snippet.get("tags", []),
                    "description": snippet.get("description", "")[:1000],
                }
        return result
