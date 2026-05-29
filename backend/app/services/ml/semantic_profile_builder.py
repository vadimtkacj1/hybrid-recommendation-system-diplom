from typing import List, Dict, Any, Optional
import logging
import numpy as np
from .text_processor import TextProcessor
from .temporal_weighting import TemporalWeighting
from app.core.config import settings

logger = logging.getLogger(__name__)


class SemanticProfileBuilder:

    MODEL_NAME = "all-MiniLM-L6-v2"
    VECTOR_DIM = 384

    def __init__(self, model_name: Optional[str] = None):
        self._model = None
        self._unavailable = False  # set True if model fails to load
        self.model_name = model_name or settings.SEMANTIC_MODEL_NAME or self.MODEL_NAME

    def _get_model(self):
        if self._unavailable:
            return None
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                logger.info("Sentence-transformer model loaded: %s", self.model_name)
            except Exception as e:
                logger.warning("Sentence-transformer unavailable (%s)  semantic vectors disabled", e)
                self._unavailable = True
                return None
        return self._model

    def _item_to_text(self, item: Dict[str, Any]) -> str:
        parts = []
        title = item.get("video_title") or item.get("title", "")
        if title:
            parts.append(str(title))
        tags = item.get("tags", "")
        if tags:
            if isinstance(tags, str):
                parts.extend(t.strip() for t in tags.split(",") if t.strip())
        cat = item.get("category") or item.get("category_id", "")
        if cat:
            parts.append(str(cat))
        ch = item.get("channel_title", "")
        if ch:
            parts.append(str(ch))
        return TextProcessor.get_text_for_embedding(parts)

    _MAX_ENCODE_ITEMS = 500

    def build_vector(
        self,
        items: List[Dict[str, Any]],
        use_temporal_weighting: bool = True,
        temporal_decay_rate: float = 0.02,
    ) -> Optional[np.ndarray]:
        if not items:
            return None
        model = self._get_model()
        if model is None:
            return None
        sample = items[: self._MAX_ENCODE_ITEMS]
        texts = [self._item_to_text(item) or "unknown" for item in sample]
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False, batch_size=64)

        if use_temporal_weighting:
            watched_dates = [item.get("watched_at") for item in sample]
            if any(d is not None for d in watched_dates):
                weights = TemporalWeighting.calculate_weights(
                    watched_dates, decay_rate=temporal_decay_rate
                )
                if weights.sum() > 0:
                    weights = weights / weights.sum()
                    vector = np.average(embeddings, axis=0, weights=weights)
                    norm = np.linalg.norm(vector)
                    if norm > 0:
                        vector = vector / norm
                    return vector

        vector = embeddings.mean(axis=0)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector
