import { useEffect, useMemo, useState } from "react";
import type { SimilarUser, SortBy, UserProfile } from "@/types";

const USERS_PER_PAGE = 24;

export function useDashboardFilters(
  similarUsers: SimilarUser[],
  profile: UserProfile | null,
) {
  const [minMatch, setMinMatch] = useState(35);
  const [sortBy, setSortBy] = useState<SortBy>("match_desc");
  const [searchQuery, setSearchQuery] = useState("");
  const [topicFilter, setTopicFilter] = useState("all");
  const [onlyShared, setOnlyShared] = useState(false);
  const [page, setPage] = useState(1);

  const myCategoryLabelsLower = useMemo(
    () => new Set((profile?.top_topics ?? []).map((t) => t.toLowerCase())),
    [profile?.top_topics],
  );

  const availableTopics = useMemo(() => {
    const uniq = new Set<string>();
    for (const u of similarUsers) {
      for (const topic of u.top_topics ?? []) {
        const t = topic.trim();
        if (t) uniq.add(t);
      }
    }
    return Array.from(uniq).sort((a, b) => a.localeCompare(b)).slice(0, 80);
  }, [similarUsers]);

  const visibleUsers = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    const filtered = similarUsers.filter((u) => {
      if (Math.round(u.similarity * 100) < minMatch) return false;
      if (topicFilter !== "all") {
        const sel = topicFilter.toLowerCase();
        const hasTopic = u.top_topics.some((t) => {
          const n = t.toLowerCase();
          return n === sel || n.includes(sel) || sel.includes(n);
        });
        if (!hasTopic) return false;
      }
      if (onlyShared) {
        const sharedCount = u.top_topics.filter((t) =>
          myCategoryLabelsLower.has(t.toLowerCase()),
        ).length;
        if (sharedCount === 0) return false;
      }
      if (!q) return true;
      const name = (u.name ?? "").toLowerCase();
      const topics = (u.top_topics ?? []).join(" ").toLowerCase();
      return name.includes(q) || topics.includes(q);
    });

    const sorted = [...filtered];
    if (sortBy === "match_desc") sorted.sort((a, b) => b.similarity - a.similarity);
    if (sortBy === "match_asc") sorted.sort((a, b) => a.similarity - b.similarity);
    if (sortBy === "name") sorted.sort((a, b) => (a.name ?? "").localeCompare(b.name ?? ""));
    if (sortBy === "shared_desc") {
      sorted.sort((a, b) => {
        const aS = a.top_topics.filter((t) => myCategoryLabelsLower.has(t.toLowerCase())).length;
        const bS = b.top_topics.filter((t) => myCategoryLabelsLower.has(t.toLowerCase())).length;
        return bS !== aS ? bS - aS : b.similarity - a.similarity;
      });
    }
    return sorted;
  }, [similarUsers, minMatch, sortBy, searchQuery, topicFilter, onlyShared, myCategoryLabelsLower]);

  const totalPages = Math.max(1, Math.ceil(visibleUsers.length / USERS_PER_PAGE));
  const pagedUsers = useMemo(() => {
    const start = (page - 1) * USERS_PER_PAGE;
    return visibleUsers.slice(start, start + USERS_PER_PAGE);
  }, [visibleUsers, page]);

  useEffect(() => { setPage(1); }, [minMatch, sortBy, searchQuery, topicFilter, onlyShared, similarUsers.length]);
  useEffect(() => { if (page > totalPages) setPage(totalPages); }, [page, totalPages]);

  const resetFilters = () => {
    setMinMatch(35);
    setSortBy("match_desc");
    setSearchQuery("");
    setTopicFilter("all");
    setOnlyShared(false);
    setPage(1);
  };

  return {
    minMatch, setMinMatch,
    sortBy, setSortBy,
    searchQuery, setSearchQuery,
    topicFilter, setTopicFilter,
    onlyShared, setOnlyShared,
    page, setPage,
    totalPages,
    visibleUsers,
    pagedUsers,
    availableTopics,
    myCategoryLabelsLower,
    resetFilters,
  };
}
