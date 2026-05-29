import type { FeedFiltersProps } from "@/types";

export function FeedFilters({
  minMatch, setMinMatch,
  searchQuery, setSearchQuery,
  topicFilter, setTopicFilter,
  sortBy, setSortBy,
  onlyShared, setOnlyShared,
  availableTopics,
}: FeedFiltersProps) {
  return (
    <div className="mb-5 p-3.5 rounded-2xl border border-stone-700/70 bg-gradient-to-b from-stone-900/70 to-stone-900/35 backdrop-blur-sm grid gap-3 items-center shadow-[0_8px_30px_rgba(0,0,0,0.25)]">
      <div className="flex items-center gap-3">
        <label className="text-xs text-stone-400 shrink-0 px-2 py-1 rounded-md bg-stone-800/70 border border-stone-700/70 whitespace-nowrap">
          <span className="hidden sm:inline">Min. match: </span>
          <span className="sm:hidden">≥ </span>
          <span className="text-stone-200 font-semibold">{minMatch}%</span>
        </label>
        <input
          type="range"
          min={20}
          max={95}
          step={5}
          value={minMatch}
          onChange={(e) => setMinMatch(Number(e.target.value))}
          className="w-full accent-amber-500 h-2"
        />
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-2 items-center">
        <input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by name or topic"
          className="h-8 bg-stone-800/90 border border-stone-700 rounded-lg px-2.5 text-xs text-stone-200 placeholder:text-stone-500 hover:border-stone-600 focus:outline-none focus:border-amber-500/60"
        />
        <select
          value={topicFilter}
          onChange={(e) => setTopicFilter(e.target.value)}
          className="h-8 bg-stone-800/90 border border-stone-700 rounded-lg px-2.5 text-xs text-stone-200 hover:border-stone-600 transition-colors"
        >
          <option value="all">All topics</option>
          {availableTopics.map((topic) => (
            <option key={topic} value={topic}>{topic}</option>
          ))}
        </select>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
          className="h-8 bg-stone-800/90 border border-stone-700 rounded-lg px-2.5 text-xs text-stone-200 hover:border-stone-600 transition-colors"
        >
          <option value="match_desc">Best match</option>
          <option value="match_asc">Worst match</option>
          <option value="shared_desc">Most in common</option>
          <option value="name">By name</option>
        </select>
        <label className="h-8 px-2.5 rounded-lg border border-stone-700 bg-stone-800/60 text-xs text-stone-300 inline-flex items-center gap-2">
          <input
            type="checkbox"
            checked={onlyShared}
            onChange={(e) => setOnlyShared(e.target.checked)}
            className="accent-amber-500"
          />
          Shared topics only
        </label>
      </div>
    </div>
  );
}
