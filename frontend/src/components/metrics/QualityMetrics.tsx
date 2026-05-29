import { useEffect, useState } from "react";
import { BarChart3, TrendingUp, Target, Layers, Award, Zap, Scale } from "lucide-react";
import { api } from "@/lib/api";

interface QualityMetric {
  precision_at_k: number;
  recall_at_k: number;
  f1_score: number;
  ndcg_at_k: number;
  diversity_score: number;
  coverage: number;
  avg_similarity: number;
  map_score: number;
  mrr_score: number;
}

interface HybridSpecificMetrics {
  content_contribution: number;
  collaborative_contribution: number;
  balance_score: number;
  synergy_score: number;
  content_only_precision: number;
  collaborative_only_precision: number;
  hybrid_improvement: number;
  weight_effectiveness: number;
}

interface AlgorithmQualityMetrics {
  tfidf: QualityMetric;
  semantic: QualityMetric;
  hybrid: QualityMetric;
  hybrid_specific: HybridSpecificMetrics;
  evaluated_users: number;
  top_k: number;
  min_shared_categories: number;
}

interface QualityMetricsResponse {
  metrics: AlgorithmQualityMetrics;
  timestamp: string;
}

export function QualityMetrics() {
  const [data, setData] = useState<QualityMetricsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const response = await api.get<QualityMetricsResponse>("/recommendations/quality-metrics?top_k=10&min_shared_categories=1");
      setData(response);
      setError(null);
    } catch (err) {
      setError("Failed to load quality metrics");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-2xl border border-stone-800 bg-stone-900/40 p-8 text-center">
        <div className="text-stone-500">Loading quality metrics...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-2xl border border-stone-800 bg-stone-900/40 p-8 text-center">
        <div className="text-red-500">{error || "No data available"}</div>
      </div>
    );
  }

  const algorithms = [
    { key: "tfidf" as const, label: "TF-IDF", color: "text-blue-400", bgColor: "bg-blue-500/20" },
    { key: "semantic" as const, label: "Semantic", color: "text-purple-400", bgColor: "bg-purple-500/20" },
    { key: "hybrid" as const, label: "Hybrid", color: "text-emerald-400", bgColor: "bg-emerald-500/20" },
  ];

  const metricDefinitions = [
    { key: "precision_at_k" as const, label: "Precision@K", icon: Target, description: "Accuracy of recommendations" },
    { key: "recall_at_k" as const, label: "Recall@K", icon: Layers, description: "Coverage of relevant items" },
    { key: "f1_score" as const, label: "F1 Score", icon: Award, description: "Harmonic mean of P&R" },
    { key: "ndcg_at_k" as const, label: "NDCG@K", icon: TrendingUp, description: "Ranking quality" },
    { key: "map_score" as const, label: "MAP", icon: Target, description: "Mean Average Precision" },
    { key: "mrr_score" as const, label: "MRR", icon: Zap, description: "Mean Reciprocal Rank" },
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-stone-800 bg-stone-900/40 overflow-hidden">
        <div className="px-5 py-3 border-b border-stone-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-amber-500/70" />
            <span className="text-sm font-medium text-stone-300">Recommendation Quality Metrics</span>
          </div>
          <div className="text-xs text-stone-600">
            {data.metrics.evaluated_users} users evaluated | Top-{data.metrics.top_k}
          </div>
        </div>

        <div className="p-6 space-y-6">
          {metricDefinitions.map((metric) => (
            <div key={metric.key} className="space-y-3">
              <div className="flex items-center gap-2">
                <metric.icon className="h-4 w-4 text-amber-500/60" />
                <span className="text-sm font-medium text-stone-300">{metric.label}</span>
                <span className="text-xs text-stone-600">— {metric.description}</span>
              </div>

              <div className="grid grid-cols-3 gap-4">
                {algorithms.map((algo) => {
                  const value = data.metrics[algo.key][metric.key];
                  const percentage = (value * 100).toFixed(1);

                  return (
                    <div key={algo.key} className="rounded-lg border border-stone-800 bg-stone-900/60 p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className={`text-xs font-medium ${algo.color}`}>{algo.label}</span>
                        <span className="text-lg font-semibold text-stone-100">{percentage}%</span>
                      </div>
                      <div className="h-2 bg-stone-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${algo.bgColor} transition-all duration-500`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-stone-800 bg-stone-900/40 overflow-hidden">
        <div className="px-5 py-3 border-b border-stone-800">
          <span className="text-sm font-medium text-stone-300">Algorithm Comparison</span>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-3 gap-4">
            {algorithms.map((algo) => {
              const metrics = data.metrics[algo.key];

              return (
                <div key={algo.key} className="rounded-lg border border-stone-800 bg-stone-900/60 p-4 space-y-3">
                  <div className={`text-sm font-semibold ${algo.color}`}>{algo.label}</div>

                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-stone-500">Avg Similarity</span>
                      <span className="text-stone-300 font-medium">{(metrics.avg_similarity * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-stone-500">F1 Score</span>
                      <span className="text-stone-300 font-medium">{(metrics.f1_score * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-stone-500">NDCG</span>
                      <span className="text-stone-300 font-medium">{(metrics.ndcg_at_k * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-stone-500">Diversity</span>
                      <span className="text-stone-300 font-medium">{(metrics.diversity_score * 100).toFixed(2)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-stone-500">Coverage</span>
                      <span className="text-stone-300 font-medium">{(metrics.coverage * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-stone-800 bg-stone-900/40 overflow-hidden">
        <div className="px-5 py-3 border-b border-stone-800 flex items-center gap-2">
          <Scale className="h-4 w-4 text-amber-500/70" />
          <span className="text-sm font-medium text-stone-300">Hybrid System Analysis</span>
        </div>

        <div className="p-6 space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="text-xs text-stone-500 uppercase tracking-widest">Component Contributions</div>
              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-stone-400">Content-Based</span>
                    <span className="text-purple-400 font-semibold">{(data.metrics.hybrid_specific.content_contribution * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-stone-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-purple-500/60"
                      style={{ width: `${data.metrics.hybrid_specific.content_contribution * 100}%` }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-stone-400">Collaborative</span>
                    <span className="text-blue-400 font-semibold">{(data.metrics.hybrid_specific.collaborative_contribution * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-stone-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500/60"
                      style={{ width: `${data.metrics.hybrid_specific.collaborative_contribution * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="text-xs text-stone-500 uppercase tracking-widest">Hybrid Performance</div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-stone-800/40 p-3">
                  <div className="text-[10px] text-stone-600 uppercase tracking-wider mb-1">Balance</div>
                  <div className="text-lg font-semibold text-emerald-400">{(data.metrics.hybrid_specific.balance_score * 100).toFixed(1)}%</div>
                </div>
                <div className="rounded-lg bg-stone-800/40 p-3">
                  <div className="text-[10px] text-stone-600 uppercase tracking-wider mb-1">Synergy</div>
                  <div className="text-lg font-semibold text-amber-400">{(data.metrics.hybrid_specific.synergy_score * 100).toFixed(1)}%</div>
                </div>
                <div className="rounded-lg bg-stone-800/40 p-3">
                  <div className="text-[10px] text-stone-600 uppercase tracking-wider mb-1">Improvement</div>
                  <div className="text-lg font-semibold text-blue-400">{(data.metrics.hybrid_specific.hybrid_improvement * 100).toFixed(2)}%</div>
                </div>
                <div className="rounded-lg bg-stone-800/40 p-3">
                  <div className="text-[10px] text-stone-600 uppercase tracking-wider mb-1">Weight Eff.</div>
                  <div className="text-lg font-semibold text-purple-400">{data.metrics.hybrid_specific.weight_effectiveness.toFixed(3)}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-stone-800">
            <div className="text-xs text-stone-500 uppercase tracking-widest mb-3">Component-Only Performance</div>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-xs text-stone-500 mb-1">Content Only</div>
                <div className="text-2xl font-semibold text-purple-400">{(data.metrics.hybrid_specific.content_only_precision * 100).toFixed(1)}%</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-stone-500 mb-1">Collaborative Only</div>
                <div className="text-2xl font-semibold text-blue-400">{(data.metrics.hybrid_specific.collaborative_only_precision * 100).toFixed(1)}%</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-stone-500 mb-1">Hybrid Combined</div>
                <div className="text-2xl font-semibold text-emerald-400">{(data.metrics.hybrid.precision_at_k * 100).toFixed(1)}%</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="text-xs text-stone-600 text-center">
        Last updated: {new Date(data.timestamp).toLocaleString()}
      </div>
    </div>
  );
}
