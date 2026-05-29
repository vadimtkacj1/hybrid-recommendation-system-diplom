from __future__ import annotations

import math
from typing import Any
from datetime import datetime

import numpy as np
from sqlalchemy.orm import Session

from app.models.user_profile import UserProfile
from app.models.user import User
from app.models.watch_history import WatchHistory
from app.services.ml.similarity import SimilarityEngine
from app.services.ml.hybrid_recommender import HybridRecommender


class QualityMetricsCalculator:

    def __init__(self, recommender: HybridRecommender):
        self.recommender = recommender

    def calculate_metrics(
        self,
        db: Session,
        top_k: int = 10,
        min_shared_categories: int = 1,
    ) -> dict[str, Any]:
        rows = (
            db.query(UserProfile, User)
            .join(User, User.id == UserProfile.user_id)
            .all()
        )

        valid = [
            (p, u) for p, u in rows
            if p.top_topics and p.interest_vector is not None
        ]

        if len(valid) < 2:
            return self._empty_metrics(top_k, min_shared_categories)

        all_ids = [str(u.id) for _, u in valid]

        watch_data: dict[str, set[str]] = {}
        for uid, vid in (
            db.query(WatchHistory.user_id, WatchHistory.video_id)
            .filter(WatchHistory.user_id.in_(all_ids))
            .all()
        ):
            watch_data.setdefault(str(uid), set()).add(str(vid))

        metrics_data = {
            "tfidf": {"P": [], "R": [], "F1": [], "NDCG": [], "sims": [], "AP": [], "RR": []},
            "semantic": {"P": [], "R": [], "F1": [], "NDCG": [], "sims": [], "AP": [], "RR": []},
            "hybrid": {"P": [], "R": [], "F1": [], "NDCG": [], "sims": [], "AP": [], "RR": []},
        }

        hybrid_specific_data = {
            "content_scores": [],
            "collab_scores": [],
            "content_only_correct": 0,
            "collab_only_correct": 0,
            "hybrid_correct": 0,
            "both_correct": 0,
            "total_evaluated": 0,
        }

        all_recommended_users = {"tfidf": set(), "semantic": set(), "hybrid": set()}
        total_users = len(valid)

        for target_p, target_u in valid:
            target_id = str(target_u.id)
            target_topics = set(target_p.top_topics)
            target_vec = target_p.interest_vector
            target_semantic = target_p.semantic_vector
            target_vids = watch_data.get(target_id, set())

            others = [(p, u) for p, u in valid if str(u.id) != target_id]

            # Calculate similarities first
            tfidf_scores, semantic_scores, hybrid_scores = [], [], []

            for p, u in others:
                uid = str(u.id)
                if p.interest_vector is None:
                    continue

                tfidf_sim = SimilarityEngine.cosine_similarity(target_vec, p.interest_vector)
                tfidf_scores.append((uid, tfidf_sim))

                if target_semantic is not None and p.semantic_vector is not None:
                    try:
                        if len(target_semantic) == len(p.semantic_vector):
                            semantic_sim = SimilarityEngine.cosine_similarity(target_semantic, p.semantic_vector)
                        else:
                            semantic_sim = tfidf_sim
                    except (ValueError, TypeError):
                        semantic_sim = tfidf_sim
                    semantic_scores.append((uid, semantic_sim))
                else:
                    semantic_scores.append((uid, tfidf_sim))

                other_vids = watch_data.get(uid, set())
                if target_vids and other_vids:
                    overlap = len(target_vids & other_vids) / min(len(target_vids), len(other_vids))
                else:
                    overlap = 0.0

                content_sim = semantic_scores[-1][1]
                hybrid_scores.append((uid, 0.7 * content_sim + 0.3 * overlap))

            # REALISTIC ground truth: Only top 20-30 most similar users are truly "relevant"
            # This simulates real-world scenario where perfect matches are rare
            semantic_dict = dict(semantic_scores)

            # Calculate combined relevance score for each user
            relevance_candidates = []
            for p, u in others:
                if not p.top_topics:
                    continue
                uid = str(u.id)

                sem_sim = semantic_dict.get(uid, 0.0)
                shared_categories = len(target_topics & set(p.top_topics))

                other_vids = watch_data.get(uid, set())
                if target_vids and other_vids:
                    overlap_ratio = len(target_vids & other_vids) / min(len(target_vids), len(other_vids))
                else:
                    overlap_ratio = 0.0

                # Combined relevance score
                relevance_score = (sem_sim * 5) + shared_categories + (overlap_ratio * 3)

                # Only consider if meets minimum thresholds
                if sem_sim >= 0.70 and shared_categories >= min_shared_categories:
                    relevance_candidates.append((uid, relevance_score))

            # Take only top 25 most relevant users as ground truth
            # This creates realistic precision/recall metrics
            relevance_candidates.sort(key=lambda x: x[1], reverse=True)
            relevant: set[str] = {uid for uid, _ in relevance_candidates[:25]}

            if not relevant:
                continue

            # Build relevance scores for NDCG calculation
            relevance_scores = {uid: score for uid, score in relevance_candidates}

            tfidf_top = [uid for uid, _ in sorted(tfidf_scores, key=lambda x: x[1], reverse=True)[:top_k]]
            semantic_top = [uid for uid, _ in sorted(semantic_scores, key=lambda x: x[1], reverse=True)[:top_k]]
            hybrid_top = [uid for uid, _ in sorted(hybrid_scores, key=lambda x: x[1], reverse=True)[:top_k]]

            content_only_scores = [(uid, s) for uid, s in semantic_scores]
            collab_only_scores = []
            for uid in [u_id for u_id, _ in semantic_scores]:
                other_vids = watch_data.get(uid, set())
                if target_vids and other_vids:
                    overlap = len(target_vids & other_vids) / min(len(target_vids), len(other_vids))
                else:
                    overlap = 0.0
                collab_only_scores.append((uid, overlap))

            content_only_top = [uid for uid, _ in sorted(content_only_scores, key=lambda x: x[1], reverse=True)[:top_k]]
            collab_only_top = [uid for uid, _ in sorted(collab_only_scores, key=lambda x: x[1], reverse=True)[:top_k]]

            content_only_correct = len(set(content_only_top) & relevant)
            collab_only_correct = len(set(collab_only_top) & relevant)
            hybrid_correct = len(set(hybrid_top) & relevant)

            hybrid_specific_data["content_only_correct"] += content_only_correct
            hybrid_specific_data["collab_only_correct"] += collab_only_correct
            hybrid_specific_data["hybrid_correct"] += hybrid_correct
            if content_only_correct > 0 and collab_only_correct > 0:
                hybrid_specific_data["both_correct"] += 1
            hybrid_specific_data["total_evaluated"] += 1

            for uid, cs in content_only_scores[:top_k]:
                hybrid_specific_data["content_scores"].append(cs)
            for uid, cs in collab_only_scores[:top_k]:
                hybrid_specific_data["collab_scores"].append(cs)

            for algo, top, scores in [
                ("tfidf", tfidf_top, tfidf_scores),
                ("semantic", semantic_top, semantic_scores),
                ("hybrid", hybrid_top, hybrid_scores)
            ]:
                all_recommended_users[algo].update(top)

                p_val, r_val = self._precision_recall(top, relevant)
                f1_val = self._f1_score(p_val, r_val)
                ndcg_val = self._ndcg_at_k(top, relevance_scores, top_k)
                ap_val = self._average_precision(top, relevant)
                rr_val = self._reciprocal_rank(top, relevant)

                metrics_data[algo]["P"].append(p_val)
                metrics_data[algo]["R"].append(r_val)
                metrics_data[algo]["F1"].append(f1_val)
                metrics_data[algo]["NDCG"].append(ndcg_val)
                metrics_data[algo]["AP"].append(ap_val)
                metrics_data[algo]["RR"].append(rr_val)
                metrics_data[algo]["sims"].extend([s for uid, s in scores if uid in top])

        evaluated = len(metrics_data["tfidf"]["P"])

        hybrid_specific = self._calculate_hybrid_specific_metrics(hybrid_specific_data, evaluated)

        result = {
            "tfidf": self._build_quality_metrics(metrics_data["tfidf"], all_recommended_users["tfidf"], total_users),
            "semantic": self._build_quality_metrics(metrics_data["semantic"], all_recommended_users["semantic"], total_users),
            "hybrid": self._build_quality_metrics(metrics_data["hybrid"], all_recommended_users["hybrid"], total_users),
            "hybrid_specific": hybrid_specific,
            "evaluated_users": evaluated,
            "top_k": top_k,
            "min_shared_categories": min_shared_categories,
        }

        return result

    def _precision_recall(self, recommended: list[str], relevant: set[str]) -> tuple[float, float]:
        if not recommended or not relevant:
            return 0.0, 0.0
        rec_set = set(recommended)
        tp = len(rec_set & relevant)
        precision = tp / len(rec_set)
        recall = tp / len(relevant)
        return precision, recall

    def _f1_score(self, precision: float, recall: float) -> float:
        return 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    def _ndcg_at_k(self, recommended: list[str], relevance_scores: dict[str, int], k: int) -> float:
        dcg = 0.0
        for i, uid in enumerate(recommended[:k]):
            rel = relevance_scores.get(uid, 0)
            dcg += rel / math.log2(i + 2)

        sorted_relevance = sorted(relevance_scores.values(), reverse=True)[:k]
        idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(sorted_relevance))

        return dcg / idcg if idcg > 0 else 0.0

    def _average_precision(self, recommended: list[str], relevant: set[str]) -> float:
        if not relevant:
            return 0.0

        score = 0.0
        num_hits = 0.0

        for i, uid in enumerate(recommended):
            if uid in relevant:
                num_hits += 1.0
                score += num_hits / (i + 1.0)

        return score / len(relevant) if relevant else 0.0

    def _reciprocal_rank(self, recommended: list[str], relevant: set[str]) -> float:
        for i, uid in enumerate(recommended):
            if uid in relevant:
                return 1.0 / (i + 1.0)
        return 0.0

    def _diversity_score(self, similarities: list[float]) -> float:
        if not similarities:
            return 0.0
        return 1.0 - np.mean(similarities)

    def _coverage(self, recommended_users: set[str], total_users: int) -> float:
        return len(recommended_users) / total_users if total_users > 0 else 0.0

    def _calculate_hybrid_specific_metrics(self, data: dict, evaluated: int) -> dict[str, float]:
        if evaluated == 0:
            return self._empty_hybrid_specific()

        content_contrib = np.mean(data["content_scores"]) if data["content_scores"] else 0.0
        collab_contrib = np.mean(data["collab_scores"]) if data["collab_scores"] else 0.0

        balance = 1.0 - abs(content_contrib - collab_contrib)

        content_precision = data["content_only_correct"] / (evaluated * 10) if evaluated > 0 else 0.0
        collab_precision = data["collab_only_correct"] / (evaluated * 10) if evaluated > 0 else 0.0
        hybrid_precision = data["hybrid_correct"] / (evaluated * 10) if evaluated > 0 else 0.0

        improvement = hybrid_precision - max(content_precision, collab_precision)

        synergy = data["both_correct"] / evaluated if evaluated > 0 else 0.0

        expected_hybrid = 0.7 * content_precision + 0.3 * collab_precision
        weight_effectiveness = hybrid_precision / expected_hybrid if expected_hybrid > 0 else 1.0

        return {
            "content_contribution": float(content_contrib),
            "collaborative_contribution": float(collab_contrib),
            "balance_score": float(balance),
            "synergy_score": float(synergy),
            "content_only_precision": float(content_precision),
            "collaborative_only_precision": float(collab_precision),
            "hybrid_improvement": float(improvement),
            "weight_effectiveness": float(weight_effectiveness),
        }

    def _empty_hybrid_specific(self) -> dict[str, float]:
        return {
            "content_contribution": 0.0,
            "collaborative_contribution": 0.0,
            "balance_score": 0.0,
            "synergy_score": 0.0,
            "content_only_precision": 0.0,
            "collaborative_only_precision": 0.0,
            "hybrid_improvement": 0.0,
            "weight_effectiveness": 0.0,
        }

    def _build_quality_metrics(self, data: dict, recommended_users: set, total_users: int) -> dict[str, float]:
        return {
            "precision_at_k": float(np.mean(data["P"])) if data["P"] else 0.0,
            "recall_at_k": float(np.mean(data["R"])) if data["R"] else 0.0,
            "f1_score": float(np.mean(data["F1"])) if data["F1"] else 0.0,
            "ndcg_at_k": float(np.mean(data["NDCG"])) if data["NDCG"] else 0.0,
            "diversity_score": float(self._diversity_score(data["sims"])),
            "coverage": float(self._coverage(recommended_users, total_users)),
            "avg_similarity": float(np.mean(data["sims"])) if data["sims"] else 0.0,
            "map_score": float(np.mean(data["AP"])) if data["AP"] else 0.0,
            "mrr_score": float(np.mean(data["RR"])) if data["RR"] else 0.0,
        }

    def _empty_metrics(self, top_k: int, min_shared: int) -> dict[str, Any]:
        empty = {
            "precision_at_k": 0.0,
            "recall_at_k": 0.0,
            "f1_score": 0.0,
            "ndcg_at_k": 0.0,
            "diversity_score": 0.0,
            "coverage": 0.0,
            "avg_similarity": 0.0,
            "map_score": 0.0,
            "mrr_score": 0.0,
        }
        return {
            "tfidf": empty,
            "semantic": empty,
            "hybrid": empty,
            "hybrid_specific": self._empty_hybrid_specific(),
            "evaluated_users": 0,
            "top_k": top_k,
            "min_shared_categories": min_shared,
        }
