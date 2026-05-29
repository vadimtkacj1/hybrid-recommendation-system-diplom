from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
import numpy as np


class TemporalWeighting:
    """
    Time-based weighting for watch history to give more importance to recent videos.

    Uses exponential decay: weight = exp(-lambda * days_ago)
    - Recent videos (last week): ~100% weight
    - 1 month old: ~60% weight
    - 3 months old: ~30% weight
    - 6+ months old: <10% weight
    """

    @staticmethod
    def calculate_weights(
        watched_dates: list[datetime],
        decay_rate: float = 0.02,
        reference_date: Optional[datetime] = None,
    ) -> np.ndarray:
        """
        Calculate temporal weights for watch history items.

        Args:
            watched_dates: List of datetime objects when videos were watched
            decay_rate: Decay rate (lambda). Higher = faster decay. Default 0.02 gives half-life ~35 days
            reference_date: Reference date for age calculation (default: now)

        Returns:
            Array of weights in [0, 1] with same length as watched_dates
        """
        if not watched_dates:
            return np.array([])

        if reference_date is None:
            reference_date = datetime.utcnow()

        weights = []
        for watched_at in watched_dates:
            if watched_at is None:
                weights.append(0.5)
                continue

            days_ago = (reference_date - watched_at).total_seconds() / 86400
            days_ago = max(0, days_ago)

            weight = np.exp(-decay_rate * days_ago)
            weights.append(weight)

        return np.array(weights)

    @staticmethod
    def apply_temporal_weighting(
        vectors: np.ndarray,
        watched_dates: list[datetime],
        decay_rate: float = 0.02,
    ) -> np.ndarray:
        """
        Apply temporal weighting to a matrix of item vectors.

        Args:
            vectors: Matrix of shape (n_items, n_features)
            watched_dates: List of datetime objects (length n_items)
            decay_rate: Decay rate parameter

        Returns:
            Weighted average vector of shape (n_features,)
        """
        if len(vectors) == 0:
            return np.array([])

        if len(vectors) != len(watched_dates):
            raise ValueError(
                f"Mismatch: {len(vectors)} vectors but {len(watched_dates)} dates"
            )

        weights = TemporalWeighting.calculate_weights(watched_dates, decay_rate)

        if weights.sum() == 0:
            return vectors.mean(axis=0)

        weights = weights / weights.sum()
        weighted_vector = np.average(vectors, axis=0, weights=weights)

        return weighted_vector

    @staticmethod
    def get_decay_rate_for_half_life(half_life_days: int) -> float:
        """
        Calculate decay rate that gives desired half-life.

        Args:
            half_life_days: Number of days for weight to decay to 50%

        Returns:
            Decay rate (lambda)
        """
        return np.log(2) / half_life_days

    @staticmethod
    def get_weight_stats(
        watched_dates: list[datetime],
        decay_rate: float = 0.02,
    ) -> dict:
        """
        Get statistics about temporal weights for debugging/analysis.

        Returns:
            Dict with min, max, mean, median weights and date range
        """
        if not watched_dates:
            return {
                "count": 0,
                "min_weight": 0,
                "max_weight": 0,
                "mean_weight": 0,
                "median_weight": 0,
            }

        weights = TemporalWeighting.calculate_weights(watched_dates, decay_rate)
        valid_dates = [d for d in watched_dates if d is not None]

        return {
            "count": len(weights),
            "min_weight": float(weights.min()),
            "max_weight": float(weights.max()),
            "mean_weight": float(weights.mean()),
            "median_weight": float(np.median(weights)),
            "oldest_date": min(valid_dates) if valid_dates else None,
            "newest_date": max(valid_dates) if valid_dates else None,
            "date_range_days": (max(valid_dates) - min(valid_dates)).days if valid_dates else 0,
        }
