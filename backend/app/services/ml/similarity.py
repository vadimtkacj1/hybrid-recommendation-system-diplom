from typing import List, Tuple, Optional
import numpy as np


class SimilarityEngine:

    @staticmethod
    def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        sim = np.dot(vec_a, vec_b) / (norm_a * norm_b)
        # Normalize from [-1, 1] to [0, 1]
        return float((sim + 1) / 2)

    @staticmethod
    def cosine_distance(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        return 1.0 - SimilarityEngine.cosine_similarity(vec_a, vec_b)

    @staticmethod
    def find_similar_users(
        user_vector: np.ndarray,
        all_vectors: np.ndarray,
        user_ids: List[int],
        top_k: int = 10,
        exclude_user_id: Optional[int] = None,
    ) -> List[Tuple[int, float]]:
        similarities = []
        for i, vec in enumerate(all_vectors):
            uid = user_ids[i]
            if exclude_user_id is not None and uid == exclude_user_id:
                continue
            sim = SimilarityEngine.cosine_similarity(user_vector, vec)
            similarities.append((uid, float(sim)))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    @staticmethod
    def hybrid_similarity(
        content_sim: float,
        overlap_score: float,
        content_weight: float = 0.7,
        overlap_weight: float = 0.3,
    ) -> float:
        return content_weight * content_sim + overlap_weight * overlap_score
