import { BarChart2, Tv2, Tags, TrendingUp, Users } from "lucide-react";
import { buildMatchDistribution } from "@/lib/profileStats";
import type { ProfileStatsProps, StatProps } from "@/types";

export function ProfileStats({ profile, matchCount, similarUsers = [] }: ProfileStatsProps) {
  const categories = profile.top_categories ?? [];
  const isManual = profile.has_interests === true;

  const dist = buildMatchDistribution(similarUsers);
  const maxCount = Math.max(...dist.map((d) => d.count), 1);
  const avgMatch = similarUsers.length
    ? Math.round((similarUsers.reduce((s, u) => s + u.similarity, 0) / similarUsers.length) * 100)
    : null;
  const topMatch = similarUsers.length
    ? Math.round(Math.max(...similarUsers.map((u) => u.similarity)) * 100)
    : null;

  return (
    <div className="mb-8 rounded-2xl border border-stone-800 bg-stone-900/40 overflow-hidden space-y-0">

      <div className="px-5 py-3 border-b border-stone-800 flex items-center gap-2">
        <BarChart2 className="h-4 w-4 text-amber-500/70" />
        <span className="text-sm font-medium text-stone-300">Profile Analytics</span>
        {profile.computed_at && (
          <span className="ml-auto text-xs text-stone-600">
            {new Date(profile.computed_at).toLocaleDateString()}
          </span>
        )}
      </div>

      <div className="grid grid-cols-3 divide-x divide-stone-800">
        <Stat
          label={isManual ? "Selected categories" : "Videos analyzed"}
          value={isManual ? categories.length : profile.video_count}
          icon={<Tv2 className="h-4 w-4 text-amber-500/60" />}
        />
        <Stat
          label="Categories"
          value={categories.length}
          icon={<Tags className="h-4 w-4 text-amber-500/60" />}
        />
        <Stat
          label="Total matches"
          value={matchCount}
          icon={<Users className="h-4 w-4 text-amber-500/60" />}
        />
      </div>

      {similarUsers.length > 0 && (
        <div className="px-5 py-5 border-t border-stone-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-amber-500/70" />
              <p className="text-sm font-medium text-stone-300">Match distribution</p>
            </div>
            <div className="flex gap-4 text-xs text-stone-500">
              {topMatch !== null && (
                <span>Top: <span className="text-emerald-400 font-semibold">{topMatch}%</span></span>
              )}
              {avgMatch !== null && (
                <span>Avg: <span className="text-amber-400 font-semibold">{avgMatch}%</span></span>
              )}
            </div>
          </div>

          <div className="space-y-2.5">
            {dist.map((b) => (
              <div key={b.label} className="flex items-center gap-3">
                <span className="text-[11px] text-stone-500 w-14 shrink-0 tabular-nums">{b.label}</span>
                <div className="flex-1 h-5 bg-stone-800/60 rounded-md overflow-hidden">
                  <div
                    className={`h-full ${b.color} rounded-md transition-all duration-500`}
                    style={{ width: `${(b.count / maxCount) * 100}%`, minWidth: b.count > 0 ? "4px" : "0" }}
                  />
                </div>
                <span className="text-[11px] text-stone-400 w-6 text-right tabular-nums shrink-0">
                  {b.count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {categories.length > 0 && (
        <div className="px-5 py-4 border-t border-stone-800">
          <p className="text-[11px] text-stone-600 uppercase tracking-widest mb-3">Your categories</p>
          <div className="flex flex-wrap gap-1.5">
            {categories.map((c) => (
              <span
                key={c}
                className="px-2.5 py-1 rounded-lg bg-stone-800/60 border border-stone-700/40 text-amber-500/70 text-xs font-medium"
              >
                {c}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, icon, valueClass = "text-stone-100" }: StatProps) {
  return (
    <div className="flex flex-col gap-1 px-2 py-3 sm:px-5 sm:py-4">
      <div className="flex items-center gap-1.5">
        <span className="hidden sm:block">{icon}</span>
        <span className="text-[10px] sm:text-[11px] text-stone-600 uppercase tracking-widest leading-tight">{label}</span>
      </div>
      <span className={`text-lg sm:text-xl font-semibold tabular-nums ${valueClass}`}>{value}</span>
    </div>
  );
}
