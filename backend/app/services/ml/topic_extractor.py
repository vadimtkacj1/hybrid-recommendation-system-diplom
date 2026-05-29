from __future__ import annotations

import logging
import re
from typing import Any

import numpy as np

from app.core.config import settings
from app.services.ml.semantic_profile_builder import SemanticProfileBuilder

logger = logging.getLogger(__name__)

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

_NOISE = frozenset({
    "http", "https", "www", "com", "youtu", "youtube", "shorts", "short",
    "twitch", "tiktok", "instagram", "facebook", "twitter", "x",
    "watch", "watched", "video", "videos", "channel", "subscribe", "live",
    "stream", "streaming", "clip", "clips", "vlog", "official",
})

_STOP = frozenset({
    "the", "and", "for", "with", "this", "that", "from", "your", "new", "all",
    "how", "what", "when", "where", "why", "who", "its", "our", "are", "was",
    "not", "but", "has", "had", "his", "her", "out", "get", "got", "just",
    "як", "що", "це", "для", "від", "про", "та", "або", "все", "вже", "ще",
    "как", "что", "это", "для", "или", "все", "ещё", "уже", "так", "там",
    "тип", "типа", "просто", "очень", "самый", "самое", "мой", "твой",
    "топ", "top", "full", "guide", "quick", "remix",
})

_MODEL = None
_UNAVAILABLE = False
_MODEL_NAME = settings.SEMANTIC_MODEL_NAME or SemanticProfileBuilder.MODEL_NAME


def _get_model() -> Any | None:
    global _MODEL, _UNAVAILABLE
    if _UNAVAILABLE:
        return None
    if _MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer

            _MODEL = SentenceTransformer(_MODEL_NAME)
            logger.info("Topic extractor loaded model %s", _MODEL_NAME)
        except Exception as e:
            logger.warning("Topic extractor: model unavailable (%s)", e)
            _UNAVAILABLE = True
            return None
    return _MODEL


def _strip_urls(text: str) -> str:
    return _URL_RE.sub(" ", text or "")


def _clean_title(title: str) -> str:
    t = _strip_urls(title or "")
    t = re.sub(r"#(\w+)", r" \1 ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def line_from_watch_item(item: dict[str, Any]) -> str:
    title = _clean_title(item.get("title") or item.get("video_title") or "")
    ch = (item.get("channel_title") or "").strip()
    if ch and title:
        return f"{ch}. {title}"
    return title or ch or ""


def is_noise_topic(token: str) -> bool:
    t = (token or "").strip().lower()
    if len(t) < 3:
        return True
    if t in _NOISE:
        return True
    if t in _STOP:
        return True
    if _URL_RE.search(t):
        return True
    if "youtube.com" in t or "youtu.be" in t:
        return True
    return False


def classify_watch_history_to_categories(
    items: list[dict[str, Any]],
    top_k: int = 8,
    min_similarity: float = 0.14,
    max_lines: int = 400,
) -> list[str]:
    from app.services.ml.interest_taxonomy import INTEREST_CATEGORY_ORDER, INTEREST_LABEL_TEXTS

    lines: list[str] = []
    for it in items[:max_lines]:
        line = line_from_watch_item(it)
        if line:
            lines.append(line)

    if len(lines) < 2:
        return []

    model = _get_model()
    if model is None:
        return []

    labels: list[str] = list(INTEREST_CATEGORY_ORDER)
    proto_texts = [INTEREST_LABEL_TEXTS[k] for k in labels]

    try:
        line_embs = model.encode(
            lines,
            convert_to_numpy=True,
            show_progress_bar=False,
            batch_size=32,
        )
        line_embs = line_embs / (np.linalg.norm(line_embs, axis=1, keepdims=True) + 1e-9)
        user_emb = np.mean(line_embs, axis=0)
        user_emb = user_emb / (np.linalg.norm(user_emb) + 1e-9)

        proto_emb = model.encode(
            proto_texts,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        proto_emb = proto_emb / (np.linalg.norm(proto_emb, axis=1, keepdims=True) + 1e-9)

        sims = proto_emb @ user_emb
        order = np.argsort(-sims)

        out: list[str] = []
        for idx in order:
            if float(sims[idx]) < min_similarity:
                continue
            out.append(labels[int(idx)])
            if len(out) >= top_k:
                break

        if not out:
            for idx in order[:3]:
                out.append(labels[int(idx)])

        return out[:top_k]
    except Exception as e:
        logger.warning("classify_watch_history_to_categories failed: %s", e)
        return []
