from __future__ import annotations

import logging
from typing import Optional, Any
from datetime import datetime, timedelta
from threading import Lock

import numpy as np

logger = logging.getLogger(__name__)


class VectorCache:
    """
    In-memory cache for user profile vectors to avoid repeated database queries.

    Features:
    - TTL-based expiration (default 1 hour)
    - Thread-safe operations
    - Separate caches for TF-IDF and semantic vectors
    - Cache statistics for monitoring
    """

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self._tfidf_cache: dict[str, tuple[np.ndarray, datetime]] = {}
        self._semantic_cache: dict[str, tuple[np.ndarray, datetime]] = {}
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def get_tfidf_vector(self, user_id: str) -> Optional[np.ndarray]:
        """
        Get cached TF-IDF vector for user.

        Args:
            user_id: User ID

        Returns:
            Cached vector or None if not found/expired
        """
        with self._lock:
            if user_id not in self._tfidf_cache:
                self._misses += 1
                return None

            vector, cached_at = self._tfidf_cache[user_id]

            if self._is_expired(cached_at):
                del self._tfidf_cache[user_id]
                self._misses += 1
                return None

            self._hits += 1
            return vector

    def get_semantic_vector(self, user_id: str) -> Optional[np.ndarray]:
        """
        Get cached semantic vector for user.

        Args:
            user_id: User ID

        Returns:
            Cached vector or None if not found/expired
        """
        with self._lock:
            if user_id not in self._semantic_cache:
                self._misses += 1
                return None

            vector, cached_at = self._semantic_cache[user_id]

            if self._is_expired(cached_at):
                del self._semantic_cache[user_id]
                self._misses += 1
                return None

            self._hits += 1
            return vector

    def set_tfidf_vector(self, user_id: str, vector: np.ndarray) -> None:
        """
        Cache TF-IDF vector for user.

        Args:
            user_id: User ID
            vector: Vector to cache
        """
        with self._lock:
            self._tfidf_cache[user_id] = (vector, datetime.utcnow())

    def set_semantic_vector(self, user_id: str, vector: np.ndarray) -> None:
        """
        Cache semantic vector for user.

        Args:
            user_id: User ID
            vector: Vector to cache
        """
        with self._lock:
            self._semantic_cache[user_id] = (vector, datetime.utcnow())

    def invalidate_user(self, user_id: str) -> None:
        """
        Invalidate cached vectors for a specific user.

        Args:
            user_id: User ID to invalidate
        """
        with self._lock:
            self._tfidf_cache.pop(user_id, None)
            self._semantic_cache.pop(user_id, None)
            logger.debug("Invalidated cache for user=%s", user_id[:8])

    def invalidate_all(self) -> None:
        """Clear all cached vectors."""
        with self._lock:
            self._tfidf_cache.clear()
            self._semantic_cache.clear()
            self._hits = 0
            self._misses = 0
            logger.info("All vector caches cleared")

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        with self._lock:
            now = datetime.utcnow()
            removed = 0

            expired_tfidf = [
                uid for uid, (_, cached_at) in self._tfidf_cache.items()
                if (now - cached_at).total_seconds() > self.ttl_seconds
            ]
            for uid in expired_tfidf:
                del self._tfidf_cache[uid]
                removed += 1

            expired_semantic = [
                uid for uid, (_, cached_at) in self._semantic_cache.items()
                if (now - cached_at).total_seconds() > self.ttl_seconds
            ]
            for uid in expired_semantic:
                del self._semantic_cache[uid]
                removed += 1

            if removed > 0:
                logger.info("Cleaned up %d expired cache entries", removed)

            return removed

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                "tfidf_cache_size": len(self._tfidf_cache),
                "semantic_cache_size": len(self._semantic_cache),
                "total_cached_users": len(set(self._tfidf_cache.keys()) | set(self._semantic_cache.keys())),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),
                "ttl_seconds": self.ttl_seconds,
            }

    def _is_expired(self, cached_at: datetime) -> bool:
        """Check if a cache entry is expired."""
        age_seconds = (datetime.utcnow() - cached_at).total_seconds()
        return age_seconds > self.ttl_seconds


_global_vector_cache: Optional[VectorCache] = None


def get_vector_cache(ttl_seconds: int = 3600) -> VectorCache:
    """
    Get the global vector cache instance.

    Args:
        ttl_seconds: TTL for cache entries (default 1 hour)

    Returns:
        Global VectorCache instance
    """
    global _global_vector_cache
    if _global_vector_cache is None:
        _global_vector_cache = VectorCache(ttl_seconds=ttl_seconds)
        logger.info("Initialized global vector cache (TTL=%ds)", ttl_seconds)
    return _global_vector_cache
