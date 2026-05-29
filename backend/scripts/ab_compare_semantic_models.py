from __future__ import annotations

import argparse
import math
import time
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, init_db
from app.models.user_profile import UserProfile
from app.services.ml.hybrid_recommender import HybridRecommender
from app.services.ml.semantic_profile_builder import SemanticProfileBuilder
from app.services.recommendation.profile_update import rebuild_all_profiles, ensure_user_profile_updated
from app.services.recommendation.similar_users import find_similar_users


@dataclass
class EvalResult:
    model_name: str
    users_evaluated: int
    rebuild_seconds: float
    avg_query_ms: float
    p_at_1: float
    p_at_3: float
    p_at_5: float
    map_at_5: float
    ndcg_at_5: float


def precision_at_k(predicted_ids: list[str], relevant: set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top_k = predicted_ids[:k]
    hits = sum(1 for uid in top_k if uid in relevant)
    return hits / k


def average_precision_at_k(predicted_ids: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    top_k = predicted_ids[:k]
    hits = 0
    acc = 0.0
    for rank, uid in enumerate(top_k, start=1):
        if uid in relevant:
            hits += 1
            acc += hits / rank
    denom = min(len(relevant), k)
    return acc / denom if denom > 0 else 0.0


def ndcg_at_k(predicted_ids: list[str], relevant: set[str], k: int) -> float:
    top_k = predicted_ids[:k]
    dcg = 0.0
    for rank, uid in enumerate(top_k, start=1):
        rel = 1.0 if uid in relevant else 0.0
        dcg += rel / math.log2(rank + 1)

    ideal_hits = min(len(relevant), k)
    idcg = 0.0
    for rank in range(1, ideal_hits + 1):
        idcg += 1.0 / math.log2(rank + 1)
    return dcg / idcg if idcg > 0 else 0.0


def evaluate_model(db: Session, model_name: str, top_k_eval: int = 5) -> EvalResult:
    recommender = HybridRecommender(top_n=1000)
    recommender.semantic_builder = SemanticProfileBuilder(model_name=model_name)

    t0 = time.perf_counter()
    rebuild_all_profiles(
        recommender,
        db,
        ensure_profile_fn=lambda db_sess, uid: ensure_user_profile_updated(recommender, db_sess, uid),
    )
    rebuild_seconds = time.perf_counter() - t0

    profiles = db.query(UserProfile).filter(UserProfile.interest_vector.isnot(None)).all()
    topic_map: dict[str, set[str]] = {
        str(p.user_id): {t.strip().lower() for t in (p.top_topics or []) if str(t).strip()}
        for p in profiles
    }
    user_ids = [str(p.user_id) for p in profiles]

    p1_scores: list[float] = []
    p3_scores: list[float] = []
    p5_scores: list[float] = []
    map5_scores: list[float] = []
    ndcg5_scores: list[float] = []
    query_times_ms: list[float] = []

    for uid in user_ids:
        source_topics = topic_map.get(uid, set())
        if not source_topics:
            continue

        relevant = {
            other_uid
            for other_uid in user_ids
            if other_uid != uid and len(source_topics & topic_map.get(other_uid, set())) > 0
        }
        if not relevant:
            continue

        q0 = time.perf_counter()
        recs = find_similar_users(
            recommender,
            db,
            uid,
            top_k=50,
            min_similarity=0.0,
            algo="hybrid",
        )
        query_times_ms.append((time.perf_counter() - q0) * 1000.0)

        predicted = [str(r["user_id"]) for r in recs]
        p1_scores.append(precision_at_k(predicted, relevant, 1))
        p3_scores.append(precision_at_k(predicted, relevant, 3))
        p5_scores.append(precision_at_k(predicted, relevant, 5))
        map5_scores.append(average_precision_at_k(predicted, relevant, top_k_eval))
        ndcg5_scores.append(ndcg_at_k(predicted, relevant, top_k_eval))

    users_evaluated = len(p1_scores)
    if users_evaluated == 0:
        return EvalResult(model_name, 0, rebuild_seconds, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    return EvalResult(
        model_name=model_name,
        users_evaluated=users_evaluated,
        rebuild_seconds=rebuild_seconds,
        avg_query_ms=sum(query_times_ms) / len(query_times_ms),
        p_at_1=sum(p1_scores) / users_evaluated,
        p_at_3=sum(p3_scores) / users_evaluated,
        p_at_5=sum(p5_scores) / users_evaluated,
        map_at_5=sum(map5_scores) / users_evaluated,
        ndcg_at_5=sum(ndcg5_scores) / users_evaluated,
    )


def print_table(results: list[EvalResult]) -> None:
    print("\nA/B semantic model benchmark (hybrid as production baseline)\n")
    print(
        f"{'Model':34} {'Users':>7} {'P@1':>7} {'P@3':>7} {'P@5':>7} "
        f"{'MAP@5':>8} {'NDCG@5':>8} {'Avg ms':>9} {'Rebuild s':>10}"
    )
    print("-" * 106)
    for r in results:
        print(
            f"{r.model_name:34} {r.users_evaluated:7d} {r.p_at_1:7.3f} {r.p_at_3:7.3f} {r.p_at_5:7.3f} "
            f"{r.map_at_5:8.3f} {r.ndcg_at_5:8.3f} {r.avg_query_ms:9.2f} {r.rebuild_seconds:10.2f}"
        )

    best_quality = max(results, key=lambda x: (x.ndcg_at_5, x.map_at_5, x.p_at_3))
    best_speed = min(results, key=lambda x: (x.avg_query_ms, x.rebuild_seconds))
    print("\nSummary:")
    print(f"- Best quality: {best_quality.model_name}")
    print(f"- Best speed:   {best_speed.model_name}")
    print("- Production baseline remains: hybrid recommender")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models",
        nargs=2,
        default=["all-MiniLM-L6-v2", "all-mpnet-base-v2"],
        help="Two sentence-transformer model names for A/B comparison.",
    )
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        results = [evaluate_model(db, m) for m in args.models]
        print_table(results)
    finally:
        db.close()


if __name__ == "__main__":
    main()

