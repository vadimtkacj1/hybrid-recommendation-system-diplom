import { EmptyState } from "./EmptyState";
import { UserFeedSkeletonGrid } from "./UserFeedCard";
import { FeedFilters } from "./FeedFilters";
import { FeedGrid } from "./FeedGrid";
import { useDashboardFilters } from "@/hooks/useDashboardFilters";
import type { RecommendTabProps } from "@/types";

export function RecommendTab({ similarUsers, profile, loading, onMessage, onAdjustPreferences }: RecommendTabProps) {
  const {
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
    resetFilters,
  } = useDashboardFilters(similarUsers, profile);

  if (loading) return <UserFeedSkeletonGrid />;

  if (similarUsers.length === 0) {
    return <EmptyState onAdjustPreferences={onAdjustPreferences} />;
  }

  return (
    <>
      <FeedFilters
        minMatch={minMatch} setMinMatch={setMinMatch}
        searchQuery={searchQuery} setSearchQuery={setSearchQuery}
        topicFilter={topicFilter} setTopicFilter={setTopicFilter}
        sortBy={sortBy} setSortBy={setSortBy}
        onlyShared={onlyShared} setOnlyShared={setOnlyShared}
        availableTopics={availableTopics}
      />
      <FeedGrid
        pagedUsers={pagedUsers}
        visibleCount={visibleUsers.length}
        page={page}
        totalPages={totalPages}
        setPage={setPage}
        onMessage={onMessage}
        onResetFilters={resetFilters}
        onAdjustPreferences={onAdjustPreferences}
      />
    </>
  );
}
