import re
from typing import List, Optional
from functools import lru_cache


class TextProcessor:
    HTML_PATTERN = re.compile(r"<[^>]+>")
    NON_ALPHA_PATTERN = re.compile(r"[^\w\s]", re.UNICODE)
    MULTI_SPACE_PATTERN = re.compile(r"\s+")

    STOP_WORDS = frozenset({
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
        "be", "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "can", "video", "watch",
        "youtube", "channel", "subscribe", "click", "like", "share",
        "і", "в", "на", "з", "для", "та", "або", "як", "що", "це", "не",
    })

    @classmethod
    def clean(cls, text: Optional[str]) -> str:
        if not text or not isinstance(text, str):
            return ""
        text = text.lower().strip()
        text = cls.HTML_PATTERN.sub(" ", text)
        text = cls.NON_ALPHA_PATTERN.sub(" ", text)
        text = cls.MULTI_SPACE_PATTERN.sub(" ", text)
        return text.strip()

    @classmethod
    def tokenize(cls, text: str, remove_stop_words: bool = True) -> List[str]:
        cleaned = cls.clean(text)
        tokens = [t for t in cleaned.split() if t]
        if remove_stop_words:
            tokens = [t for t in tokens if t not in cls.STOP_WORDS]
        return tokens

    @classmethod
    def get_text_for_embedding(cls, texts: List[Optional[str]], join_char: str = " ") -> str:
        parts = [cls.clean(t) for t in texts if t]
        return join_char.join(parts)
