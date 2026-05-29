from __future__ import annotations

from typing import Any, Optional
import numpy as np


class RecommendationExplainer:
    """
    Generate human-readable explanations for why users were matched.
    Helps users understand the recommendation algorithm and builds trust.
    """

    @staticmethod
    def explain_match(
        target_user_data: dict[str, Any],
        matched_user_data: dict[str, Any],
        similarity_score: float,
        content_similarity: float,
        overlap_score: float,
        content_weight: float,
        overlap_weight: float,
        algo: str = "hybrid",
    ) -> dict[str, Any]:
        """
        Generate explanation for a user match.

        Args:
            target_user_data: Data about the target user (categories, channels, etc.)
            matched_user_data: Data about the matched user
            similarity_score: Final similarity score
            content_similarity: Content-based similarity component
            overlap_score: Collaborative overlap component
            content_weight: Weight given to content similarity
            overlap_weight: Weight given to overlap
            algo: Algorithm used (tfidf, semantic, hybrid)

        Returns:
            Dict with explanation data
        """
        explanation = {
            "similarity_score": round(similarity_score, 4),
            "algorithm": algo,
            "components": {},
            "shared_interests": [],
            "match_reasons": [],
        }

        if algo == "hybrid":
            explanation["components"] = {
                "content_similarity": round(content_similarity, 4),
                "overlap_score": round(overlap_score, 4),
                "content_weight": round(content_weight, 2),
                "overlap_weight": round(overlap_weight, 2),
            }

            if content_similarity > 0.7:
                explanation["match_reasons"].append(
                    f"Strong content match ({content_similarity:.0%})"
                )
            elif content_similarity > 0.5:
                explanation["match_reasons"].append(
                    f"Good content match ({content_similarity:.0%})"
                )

            if overlap_score > 0.3:
                explanation["match_reasons"].append(
                    f"Watched {int(overlap_score * 100)}% similar videos"
                )

        target_topics = set(target_user_data.get("top_topics", []))
        matched_topics = set(matched_user_data.get("top_topics", []))
        shared_topics = target_topics & matched_topics

        if shared_topics:
            explanation["shared_interests"] = sorted(list(shared_topics))[:5]
            explanation["match_reasons"].append(
                f"Share {len(shared_topics)} interest categories"
            )

        if not explanation["match_reasons"]:
            if similarity_score > 0.7:
                explanation["match_reasons"].append("High overall similarity")
            elif similarity_score > 0.5:
                explanation["match_reasons"].append("Moderate similarity")
            else:
                explanation["match_reasons"].append("Some common interests")

        return explanation

    @staticmethod
    def calculate_category_rarity_scores(
        all_user_categories: list[list[str]],
    ) -> dict[str, float]:
        """
        Calculate IDF-style rarity scores for categories.
        Rare categories get higher scores.

        Args:
            all_user_categories: List of category lists for all users

        Returns:
            Dict mapping category name to rarity score [0, 1]
        """
        if not all_user_categories:
            return {}

        category_counts: dict[str, int] = {}
        total_users = len(all_user_categories)

        for categories in all_user_categories:
            unique_cats = set(categories)
            for cat in unique_cats:
                category_counts[cat] = category_counts.get(cat, 0) + 1

        rarity_scores = {}
        for cat, count in category_counts.items():
            idf = np.log(total_users / (1 + count))
            max_idf = np.log(total_users)
            rarity_scores[cat] = idf / max_idf if max_idf > 0 else 0.0

        return rarity_scores

    @staticmethod
    def get_match_strength_label(similarity: float) -> str:
        """
        Convert similarity score to human-readable label.

        Args:
            similarity: Similarity score in [0, 1]

        Returns:
            Label like "Excellent match", "Good match", etc.
        """
        if similarity >= 0.9:
            return "Excellent match"
        elif similarity >= 0.75:
            return "Very good match"
        elif similarity >= 0.6:
            return "Good match"
        elif similarity >= 0.4:
            return "Moderate match"
        else:
            return "Weak match"

    @staticmethod
    def explain_algorithm_choice(
        video_count: int,
        has_semantic: bool,
        algo: str,
    ) -> str:
        """
        Explain why a particular algorithm was used.

        Returns:
            Human-readable explanation
        """
        if algo == "semantic":
            if has_semantic:
                return "Using semantic embeddings for deep content understanding"
            else:
                return "Semantic embeddings not available, falling back to TF-IDF"
        elif algo == "tfidf":
            return "Using keyword-based matching (TF-IDF)"
        elif algo == "hybrid":
            if video_count < 10:
                return "Using hybrid approach with emphasis on content (limited watch history)"
            elif video_count < 50:
                return "Using balanced hybrid approach (content + collaborative)"
            else:
                return "Using hybrid approach with strong collaborative filtering (rich watch history)"
        return f"Using {algo} algorithm"
