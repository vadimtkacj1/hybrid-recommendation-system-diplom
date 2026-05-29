from __future__ import annotations

from app.services.ml.dynamic_topic_extractor import extract_user_topics


def resolve_user_display_categories(
    items: list[dict[str, str]],
    top_youtube_category_names: list[str],
    top_channel_names: list[str],
    *,
    max_lines_for_classifier: int = 400,
    preview_limit: int = 12,
) -> tuple[list[str], list[str], list[str]]:
    dynamic_topics = extract_user_topics(items, top_k=preview_limit, method="tfidf")

    if dynamic_topics:
        display_categories = dynamic_topics
        top_topics_preview = dynamic_topics[:preview_limit]
        ml_taxonomy = dynamic_topics
    else:
        display_categories = top_youtube_category_names if top_youtube_category_names else top_channel_names[:preview_limit]
        top_topics_preview = display_categories[:preview_limit]
        ml_taxonomy = []

    return display_categories, top_topics_preview, ml_taxonomy
