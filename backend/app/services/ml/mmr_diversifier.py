from __future__ import annotations

from typing import Any, Optional
import numpy as np


class MMRDiversifier:
    """
    Maximal Marginal Relevance (MMR) for diversifying recommendations.
    Used by Google, Bing for search result diversification.

    Balances relevance and diversity:
    - lambda=1.0: pure relevance (no diversification)
    - lambda=0.5: equal balance
    - lambda=0.0: pure diversity (ignore relevance)
    """

    @staticmethod
    def diversify(
        candidates: list[dict[str, Any]],
        top_k: int,
        lambda_param: float = 0.7,
        similarity_key: str = "similarity",
        vector_key: str = "interest_vector",
    ) -> list[dict[str, Any]]:
        """
        Apply MMR to diversify recommendations.

        Args:
            candidates: List of candidate recommendations with similarity scores
            top_k: Number of items to return
            lambda_param: Balance between relevance (1.0) and diversity (0.0)
            similarity_key: Key for relevance score in candidate dict
            vector_key: Key for feature vector in candidate dict

        Returns:
            Diversified list of top_k recommendations
        """
        if not candidates or len(candidates) <= 1:
            return candidates[:top_k]

        if len(candidates) <= top_k:
            return candidates

        selected = []
        remaining = candidates.copy()

        # Select most relevant first
        best = max(remaining, key=lambda x: x.get(similarity_key, 0))
        selected.append(best)
        remaining.remove(best)

        # Iteratively select items that balance relevance and diversity
        while len(selected) < top_k and remaining:
            scores = []

            for candidate in remaining:
                relevance = candidate.get(similarity_key, 0)

                # Calculate maximum similarity to already selected items
                max_sim_to_selected = 0.0
                candidate_vector = candidate.get(vector_key)

                if candidate_vector is not None:
                    for selected_item in selected:
                        selected_vector = selected_item.get(vector_key)
                        if selected_vector is not None:
                            sim = MMRDiversifier._cosine_similarity(
                                candidate_vector, selected_vector
                            )
                            max_sim_to_selected = max(max_sim_to_selected, sim)
                else:
                    # Fallback: use category/topic overlap
                    candidate_topics = set(candidate.get("top_topics", []))
                    if candidate_topics:
                        for selected_item in selected:
                            selected_topics = set(selected_item.get("top_topics", []))
                            if selected_topics:
                                overlap = len(candidate_topics & selected_topics) / len(
                                    candidate_topics | selected_topics
                                )
                                max_sim_to_selected = max(max_sim_to_selected, overlap)

                # MMR score: balance relevance and diversity
                mmr_score = (
                    lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected
                )
                scores.append((candidate, mmr_score))

            # Select candidate with highest MMR score
            best_candidate, _ = max(scores, key=lambda x: x[1])
            selected.append(best_candidate)
            remaining.remove(best_candidate)

        return selected

    @staticmethod
    def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        if vec_a is None or vec_b is None:
            return 0.0

        if not isinstance(vec_a, np.ndarray):
            vec_a = np.array(vec_a)
        if not isinstance(vec_b, np.ndarray):
            vec_b = np.array(vec_b)

        if vec_a.shape != vec_b.shape:
            return 0.0

        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        sim = np.dot(vec_a, vec_b) / (norm_a * norm_b)
        return float((sim + 1) / 2)  # Normalize to [0, 1]

    @staticmethod
    def calculate_diversity_score(recommendations: list[dict[str, Any]]) -> float:
        """
        Calculate diversity score for a list of recommendations.
        Higher score = more diverse recommendations.

        Returns:
            Diversity score in [0, 1] where 1 is most diverse
        """
        if len(recommendations) <= 1:
            return 1.0

        total_dissimilarity = 0.0
        count = 0

        for i in range(len(recommendations)):
            for j in range(i + 1, len(recommendations)):
                vec_i = recommendations[i].get("interest_vector")
                vec_j = recommendations[j].get("interest_vector")

                if vec_i is not None and vec_j is not None:
                    sim = MMRDiversifier._cosine_similarity(vec_i, vec_j)
                    total_dissimilarity += 1.0 - sim
                    count += 1
                else:
                    # Fallback: topic-based diversity
                    topics_i = set(recommendations[i].get("top_topics", []))
                    topics_j = set(recommendations[j].get("top_topics", []))
                    if topics_i and topics_j:
                        overlap = len(topics_i & topics_j) / len(topics_i | topics_j)
                        total_dissimilarity += 1.0 - overlap
                        count += 1

        if count == 0:
            return 0.0

        return total_dissimilarity / count
