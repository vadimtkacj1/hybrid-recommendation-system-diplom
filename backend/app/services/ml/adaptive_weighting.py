from __future__ import annotations

from typing import Optional


class AdaptiveWeighting:
    """
    Context-aware adaptive weighting for hybrid recommendation systems.
    Adjusts content vs collaborative weights based on user profile characteristics.

    Based on research: Context-Aware Recommender Systems (Adomavicius & Tuzhilin)
    """

    @staticmethod
    def get_weights(
        video_count: int,
        category_diversity: float,
        profile_age_days: Optional[int] = None,
    ) -> tuple[float, float]:
        """
        Calculate adaptive weights for content and collaborative components.

        Args:
            video_count: Number of videos in user's watch history
            category_diversity: Diversity of categories (0-1, higher = more diverse)
            profile_age_days: Age of user profile in days

        Returns:
            (content_weight, collaborative_weight) tuple that sums to 1.0
        """
        # Base weights based on data availability
        if video_count < 5:
            # Very new users: rely almost entirely on content
            content_w = 0.95
            collab_w = 0.05
        elif video_count < 10:
            # New users: mostly content
            content_w = 0.85
            collab_w = 0.15
        elif video_count < 30:
            # Growing users: transition to balanced
            content_w = 0.70
            collab_w = 0.30
        elif video_count < 100:
            # Established users: more collaborative
            content_w = 0.60
            collab_w = 0.40
        else:
            # Power users: balanced or collaborative-heavy
            content_w = 0.50
            collab_w = 0.50

        # Adjust for category diversity
        # Diverse users benefit more from content-based (explore different topics)
        # Focused users benefit more from collaborative (similar users)
        if category_diversity > 0.7:
            # High diversity: boost content
            content_w = min(1.0, content_w + 0.10)
        elif category_diversity < 0.3:
            # Low diversity (focused): boost collaborative
            collab_w = min(1.0, collab_w + 0.10)

        # Adjust for profile age (optional)
        if profile_age_days is not None:
            if profile_age_days < 7:
                # Very new profile: boost content
                content_w = min(1.0, content_w + 0.05)
            elif profile_age_days > 180:
                # Mature profile: boost collaborative
                collab_w = min(1.0, collab_w + 0.05)

        # Normalize to ensure sum = 1.0
        total = content_w + collab_w
        content_w /= total
        collab_w /= total

        return content_w, collab_w

    @staticmethod
    def calculate_category_diversity(categories: list[str]) -> float:
        """
        Calculate diversity of categories in user profile.

        Args:
            categories: List of category names

        Returns:
            Diversity score in [0, 1] where 1 is most diverse
        """
        if not categories:
            return 0.0

        unique_count = len(set(categories))
        total_count = len(categories)

        if total_count == 0:
            return 0.0

        # Shannon entropy-based diversity
        from collections import Counter
        import math

        counts = Counter(categories)
        entropy = 0.0

        for count in counts.values():
            p = count / total_count
            if p > 0:
                entropy -= p * math.log2(p)

        # Normalize by maximum possible entropy
        max_entropy = math.log2(unique_count) if unique_count > 1 else 1.0
        diversity = entropy / max_entropy if max_entropy > 0 else 0.0

        return diversity

    @staticmethod
    def get_weight_explanation(
        video_count: int,
        category_diversity: float,
        content_weight: float,
        collaborative_weight: float,
    ) -> str:
        """
        Generate human-readable explanation of why these weights were chosen.

        Returns:
            Explanation string
        """
        reasons = []

        # Video count reasoning
        if video_count < 10:
            reasons.append(
                f"New user ({video_count} videos) → favor content-based recommendations"
            )
        elif video_count < 50:
            reasons.append(
                f"Growing profile ({video_count} videos) → balanced approach"
            )
        else:
            reasons.append(
                f"Established user ({video_count} videos) → leverage collaborative filtering"
            )

        # Diversity reasoning
        if category_diversity > 0.7:
            reasons.append(
                f"High diversity ({category_diversity:.2f}) → boost content exploration"
            )
        elif category_diversity < 0.3:
            reasons.append(
                f"Focused interests ({category_diversity:.2f}) → boost collaborative filtering"
            )

        # Final weights
        reasons.append(
            f"Final weights: {content_weight:.0%} content, {collaborative_weight:.0%} collaborative"
        )

        return " | ".join(reasons)
