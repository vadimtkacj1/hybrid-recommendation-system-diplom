from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import scipy.sparse as sp

logger = logging.getLogger(__name__)

FACTORS = 32
ITERATIONS = 20
REGULARIZATION = 0.1
ALPHA_CONFIDENCE = 40.0


def build_user_channel_matrix(
    db,
) -> tuple[sp.csr_matrix, list[str], list[str]]:
    """
    Будує розріджену матрицю User × Channel з БД.
    Значення = кількість переглядів каналу користувачем.
    Повертає матрицю, список user_id, список channel назв.
    """
    from app.models.watch_history import WatchHistory, VideoMetadata

    rows = (
        db.query(WatchHistory.user_id, VideoMetadata.channel_title)
        .join(VideoMetadata, VideoMetadata.id == WatchHistory.video_id)
        .filter(VideoMetadata.channel_title.isnot(None))
        .filter(VideoMetadata.channel_title != "")
        .all()
    )

    if not rows:
        return sp.csr_matrix((0, 0)), [], []

    user_ids: list[str] = sorted(set(str(r[0]) for r in rows))
    channels: list[str] = sorted(set(str(r[1]) for r in rows))

    user_idx = {u: i for i, u in enumerate(user_ids)}
    chan_idx = {c: i for i, c in enumerate(channels)}

    data, row_ind, col_ind = [], [], []
    counts: dict[tuple[int, int], int] = {}
    for uid, ch in rows:
        u = user_idx[str(uid)]
        c = chan_idx[str(ch)]
        counts[(u, c)] = counts.get((u, c), 0) + 1

    for (u, c), cnt in counts.items():
        row_ind.append(u)
        col_ind.append(c)
        data.append(float(cnt))

    matrix = sp.csr_matrix(
        (data, (row_ind, col_ind)),
        shape=(len(user_ids), len(channels)),
    )
    logger.info(
        "User×Channel matrix: %d users × %d channels, %d interactions",
        len(user_ids), len(channels), len(data),
    )
    return matrix, user_ids, channels


def train_als(
    user_channel_matrix: sp.csr_matrix,
    factors: int = FACTORS,
    iterations: int = ITERATIONS,
    regularization: float = REGULARIZATION,
    alpha: float = ALPHA_CONFIDENCE,
) -> Optional[np.ndarray]:
    """
    Тренує ALS модель на матриці User×Channel.
    Повертає user_factors — матрицю (N_users, factors).
    """
    if user_channel_matrix.shape[0] < 2 or user_channel_matrix.shape[1] < 2:
        logger.warning("Matrix too small for ALS: %s", user_channel_matrix.shape)
        return None

    try:
        from implicit.als import AlternatingLeastSquares

        # confidence = 1 + alpha * частота
        confidence_matrix = (user_channel_matrix * alpha).astype(np.float32)

        model = AlternatingLeastSquares(
            factors=factors,
            iterations=iterations,
            regularization=regularization,
            use_gpu=False,
        )
        # implicit очікує item×user формат
        model.fit(confidence_matrix.T.tocsr(), show_progress=False)

        user_factors = model.user_factors  # (N_users, factors)
        logger.info("ALS trained: user_factors shape=%s", user_factors.shape)
        return np.array(user_factors, dtype=np.float32)

    except Exception as e:
        logger.error("ALS training failed: %s", e)
        return None


def compute_als_vectors(db) -> dict[str, np.ndarray]:
    """
    Будує матрицю, тренує ALS, повертає словник user_id → вектор.
    """
    matrix, user_ids, _ = build_user_channel_matrix(db)
    if not user_ids:
        return {}

    user_factors = train_als(matrix)
    if user_factors is None:
        return {}

    result: dict[str, np.ndarray] = {}
    for i, uid in enumerate(user_ids):
        vec = user_factors[i]
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        result[uid] = vec.astype(np.float32)

    logger.info("ALS vectors computed for %d users", len(result))
    return result
