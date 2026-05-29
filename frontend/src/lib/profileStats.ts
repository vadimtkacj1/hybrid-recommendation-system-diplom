import type { SimilarUser } from "@/types";

export const MATCH_BUCKETS = [
  { label: "90–100%", min: 0.9, color: "bg-emerald-500" },
  { label: "80–89%",  min: 0.8, color: "bg-amber-400" },
  { label: "70–79%",  min: 0.7, color: "bg-amber-500/70" },
  { label: "60–69%",  min: 0.6, color: "bg-stone-500" },
  { label: "< 60%",   min: 0,   color: "bg-stone-700" },
] as const;

export type MatchBucket = (typeof MATCH_BUCKETS)[number] & { count: number };

export function buildMatchDistribution(users: SimilarUser[]): MatchBucket[] {
  return MATCH_BUCKETS.map((b, i) => {
    const max = MATCH_BUCKETS[i - 1]?.min ?? 1.01;
    const count = users.filter((u) => u.similarity >= b.min && u.similarity < max).length;
    return { ...b, count };
  });
}
