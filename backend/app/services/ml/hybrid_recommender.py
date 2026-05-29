from __future__ import annotations

from typing import Optional

import numpy as np

from app.services.ml.algo_types import AlgoType
from app.services.ml.profile_builder import ProfileBuilder
from app.services.ml.semantic_profile_builder import SemanticProfileBuilder
from app.services.ml.similarity import SimilarityEngine


class HybridRecommender:

    def __init__(self, top_n: int = 20):
        self.top_n = top_n
        self.profile_builder = ProfileBuilder()
        self.semantic_builder = SemanticProfileBuilder()

    def fit(self, all_items: list[dict]) -> "HybridRecommender":
        self.profile_builder.fit(all_items)
        return self

    def _item_to_dict(self, row) -> dict:
        video = getattr(row, "video", None) or row
        return {
            "video_title": getattr(video, "title", None) or video.get("title", ""),
            "channel_title": getattr(video, "channel_title", None) or video.get("channel_title", ""),
            "category": getattr(video, "category_id", None) or video.get("category_id", ""),
            "tags": getattr(video, "tags", None) or video.get("tags", ""),
            "channel_description": getattr(video, "description", None) or video.get("description", "")[:500],
        }

    def build_profile_vector(
        self,
        watch_items: list,
        use_temporal_weighting: bool = True,
    ) -> Optional[np.ndarray]:
        if not watch_items:
            return None
        items = []
        for row in watch_items:
            if isinstance(row, dict):
                items.append({
                    "video_title": row.get("title", row.get("video_title", "")),
                    "channel_title": row.get("channel_title", ""),
                    "category": str(row.get("category_id", row.get("category", ""))),
                    "tags": row.get("tags", ""),
                    "channel_description": str(row.get("description", ""))[:500],
                    "watched_at": row.get("watched_at"),
                })
            else:
                item_dict = self._item_to_dict(row)
                item_dict["watched_at"] = getattr(row, "watched_at", None)
                items.append(item_dict)
        return self.profile_builder.build_vector(
            items, use_temporal_weighting=use_temporal_weighting
        )

    def build_semantic_vector(
        self,
        watch_items: list,
        use_temporal_weighting: bool = True,
    ) -> Optional[np.ndarray]:
        if not watch_items:
            return None
        items = []
        for row in watch_items:
            if isinstance(row, dict):
                items.append({
                    "video_title": row.get("title", row.get("video_title", "")),
                    "channel_title": row.get("channel_title", ""),
                    "category": str(row.get("category_id", row.get("category", ""))),
                    "tags": row.get("tags", ""),
                    "watched_at": row.get("watched_at"),
                })
            else:
                item_dict = self._item_to_dict(row)
                item_dict["watched_at"] = getattr(row, "watched_at", None)
                items.append(item_dict)
        return self.semantic_builder.build_vector(
            items, use_temporal_weighting=use_temporal_weighting
        )

    def compute_similarities(
        self,
        target_vector: np.ndarray,
        other_vectors: list[Optional[np.ndarray]],
        user_ids: list[str],
        top_k: Optional[int] = None,
        min_similarity: float = 0.0,
        target_video_ids: Optional[set[str]] = None,
        other_video_ids: Optional[dict[str, set[str]]] = None,
        content_weight: float = 0.7,
        overlap_weight: float = 0.3,
        algo: AlgoType = "hybrid",
        return_explanations: bool = False,
        target_als_vector: Optional[np.ndarray] = None,
        other_als_vectors: Optional[dict[str, np.ndarray]] = None,
        als_weight: float = 0.0,
    ) -> list[dict[str, str | float]]:
        use_overlap = (
            algo == "hybrid"
            and target_video_ids is not None
            and other_video_ids is not None
            and len(target_video_ids) > 0
        )
        use_als = (
            algo == "hybrid"
            and target_als_vector is not None
            and other_als_vectors is not None
            and als_weight > 0
        )

        # якщо є ALS — перенормалізовуємо ваги щоб сума = 1
        if use_als:
            total_w = content_weight + overlap_weight + als_weight
            content_weight = content_weight / total_w
            overlap_weight = overlap_weight / total_w
            als_weight = als_weight / total_w

        results: list[dict[str, str | float]] = []
        for i, vec in enumerate(other_vectors):
            if vec is None or not isinstance(vec, np.ndarray) or not np.any(vec):
                continue
            if vec.shape != target_vector.shape:
                continue
            uid = str(user_ids[i]) if i < len(user_ids) else str(i)

            content_sim = SimilarityEngine.cosine_similarity(target_vector, vec)
            overlap_score = 0.0
            als_sim = 0.0

            if use_overlap and uid in other_video_ids:
                other_vids = other_video_ids[uid]
                if len(other_vids) > 0 and len(target_video_ids) > 0:
                    shared = len(target_video_ids & other_vids)
                    overlap_score = shared / min(len(target_video_ids), len(other_vids))

            if use_als:
                other_als = other_als_vectors.get(uid)
                if other_als is not None:
                    als_sim = float(np.dot(target_als_vector, other_als))
                    als_sim = max(0.0, min(1.0, (als_sim + 1) / 2))

            if use_als:
                final_sim = (
                    content_weight * content_sim
                    + overlap_weight * overlap_score
                    + als_weight * als_sim
                )
            elif use_overlap:
                final_sim = SimilarityEngine.hybrid_similarity(
                    content_sim, overlap_score, content_weight, overlap_weight
                )
            else:
                final_sim = content_sim

            if final_sim >= min_similarity:
                result = {"user_id": str(uid), "similarity": float(final_sim)}

                if return_explanations:
                    result["_explanation_data"] = {
                        "content_similarity": float(content_sim),
                        "overlap_score": float(overlap_score),
                        "als_similarity": float(als_sim),
                        "content_weight": float(content_weight),
                        "overlap_weight": float(overlap_weight),
                        "als_weight": float(als_weight),
                        "shared_videos": len(target_video_ids & other_video_ids.get(uid, set())) if use_overlap else 0,
                    }

                results.append(result)

        results.sort(key=lambda x: x["similarity"], reverse=True)
        if top_k is None:
            return results[: self.top_n]
        return results[:top_k]
