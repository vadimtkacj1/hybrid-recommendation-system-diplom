from __future__ import annotations

import logging
import re
from collections import Counter
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

STOP_WORDS = frozenset({
    "the", "and", "for", "with", "this", "that", "from", "your", "new", "all",
    "how", "what", "when", "where", "why", "who", "its", "our", "are", "was",
    "not", "but", "has", "had", "his", "her", "out", "get", "got", "just",
    "you", "can", "will", "one", "two", "more", "like", "make", "made", "way",
    "best", "top", "full", "guide", "tutorial", "video", "videos", "part",
    "episode", "series", "season", "official", "hd", "4k", "2024", "2025", "2026",
    "watch", "live", "stream", "clip", "vlog", "channel", "subscribe",
    "http", "https", "www", "com", "youtube", "youtu", "shorts",
})

NOISE_PATTERNS = [
    re.compile(r"https?://\S+", re.IGNORECASE),
    re.compile(r"www\.\S+", re.IGNORECASE),
    re.compile(r"\d{4}"),  # years
    re.compile(r"ep\s*\d+", re.IGNORECASE),  # episode numbers
    re.compile(r"s\d+e\d+", re.IGNORECASE),  # season/episode
]


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    for pattern in NOISE_PATTERNS:
        text = pattern.sub(" ", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_valid_topic(word: str) -> bool:
    if len(word) < 3:
        return False
    if word in STOP_WORDS:
        return False
    if word.isdigit():
        return False
    return True


def extract_topics_tfidf(
    items: list[dict[str, Any]],
    top_k: int = 12,
    max_items: int = 500,
) -> list[str]:
    if not items:
        return []

    # Collect channel names to filter them out later
    channel_names = set()
    for item in items[:max_items]:
        channel = item.get("channel_title") or ""
        if channel:
            channel_names.add(clean_text(channel))

    # Extract only from titles (not channels)
    texts = []
    for item in items[:max_items]:
        title = item.get("title") or item.get("video_title") or ""
        cleaned = clean_text(title)
        if cleaned:
            texts.append(cleaned)

    if len(texts) < 2:
        return []

    try:
        vectorizer = TfidfVectorizer(
            max_features=200,  # Increased to capture more topics
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.8,
            stop_words=list(STOP_WORDS),
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        feature_names = vectorizer.get_feature_names_out()

        # Sum TF-IDF scores across all documents to find most important terms
        scores = np.asarray(tfidf_matrix.sum(axis=0)).flatten()

        # Also count document frequency (how many videos mention this term)
        doc_freq = np.asarray((tfidf_matrix > 0).sum(axis=0)).flatten()

        # Combine TF-IDF score with document frequency for better ranking
        # Terms that appear in more videos get a boost
        combined_scores = scores * (1 + np.log1p(doc_freq))

        top_indices = combined_scores.argsort()[-top_k * 3:][::-1]

        topics = []
        for idx in top_indices:
            word = feature_names[idx]
            # Skip if it's a channel name or invalid
            if is_valid_topic(word) and word not in channel_names:
                topics.append(word.title())
                if len(topics) >= top_k:
                    break

        return topics
    except Exception as e:
        logger.warning("TF-IDF topic extraction failed: %s", e)
        return extract_topics_frequency(items, top_k)


def extract_topics_frequency(
    items: list[dict[str, Any]],
    top_k: int = 8,
    max_items: int = 500,
) -> list[str]:
    if not items:
        return []

    word_counts = Counter()

    for item in items[:max_items]:
        title = item.get("title") or item.get("video_title") or ""
        channel = item.get("channel_title") or ""
        combined = f"{title} {channel}"
        cleaned = clean_text(combined)

        words = cleaned.split()
        for word in words:
            if is_valid_topic(word):
                word_counts[word] += 1

    topics = []
    for word, count in word_counts.most_common(top_k * 2):
        if count >= 2:
            topics.append(word.title())
            if len(topics) >= top_k:
                break

    return topics


def extract_user_topics(
    items: list[dict[str, Any]],
    top_k: int = 8,
    method: str = "tfidf",
) -> list[str]:
    if method == "tfidf":
        return extract_topics_tfidf(items, top_k)
    else:
        return extract_topics_frequency(items, top_k)
