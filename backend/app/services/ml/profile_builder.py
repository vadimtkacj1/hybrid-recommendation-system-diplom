from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler

from .text_processor import TextProcessor
from .temporal_weighting import TemporalWeighting


class ProfileBuilder:

    def __init__(
        self,
        max_features: int = 500,
        ngram_range: tuple = (1, 2),
        min_df: int = 1,
        max_df: float = 0.95,
    ):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=min_df,
            max_df=max_df,
            sublinear_tf=True,
        )
        self.scaler = StandardScaler()
        self._fitted = False

    def _item_to_parts(self, item: Dict[str, Any]) -> List[str]:
        parts = []
        title = item.get("video_title") or item.get("title", "")
        if title:
            parts.append(str(title))
        tags = item.get("tags")
        if tags:
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            parts.extend(tags)
        cat = item.get("category") or item.get("category_id", "")
        if cat:
            parts.append(str(cat))
        ch = item.get("channel_title", "")
        if ch:
            parts.append(str(ch))
        desc = item.get("channel_description") or item.get("description", "")
        if desc:
            parts.append(str(desc)[:500])
        return parts

    def _build_text_features(self, items: List[Dict[str, Any]]) -> List[str]:
        docs = []
        for item in items:
            parts = self._item_to_parts(item)
            text = TextProcessor.get_text_for_embedding(parts)
            docs.append(text if text else "unknown")
        return docs

    def fit(self, all_items: List[Dict[str, Any]]) -> "ProfileBuilder":
        docs = self._build_text_features(all_items)
        self.vectorizer.fit(docs)
        self._fitted = True
        return self

    def build_vector(
        self,
        items: List[Dict[str, Any]],
        use_temporal_weighting: bool = True,
        temporal_decay_rate: float = 0.02,
    ) -> np.ndarray:
        if not items:
            return np.zeros(self.vectorizer.max_features)
        docs = self._build_text_features(items)
        if not docs:
            return np.zeros(self.vectorizer.max_features)
        if not self._fitted:
            self.vectorizer.fit(docs)
            self._fitted = True
        matrix = self.vectorizer.transform(docs)

        if use_temporal_weighting:
            watched_dates = [item.get("watched_at") for item in items]
            if any(d is not None for d in watched_dates):
                weights = TemporalWeighting.calculate_weights(
                    watched_dates, decay_rate=temporal_decay_rate
                )
                if weights.sum() > 0:
                    weights = weights / weights.sum()
                    vector = np.asarray(
                        np.average(matrix.toarray(), axis=0, weights=weights)
                    ).flatten()
                    return vector

        vector = np.asarray(matrix.mean(axis=0)).flatten()
        return vector

    def build_vector_sparse_sum(self, items: List[Dict[str, Any]]) -> np.ndarray:
        if not self._fitted:
            raise ValueError("ProfileBuilder must be fitted before calling build_vector")
        docs = self._build_text_features(items)
        if not docs:
            return np.zeros(self.vectorizer.max_features)
        matrix = self.vectorizer.transform(docs)
        vector = np.asarray(matrix.sum(axis=0)).flatten()
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector
