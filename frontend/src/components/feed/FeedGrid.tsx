import { Button } from "@/components/ui/button";
import { EmptyState } from "./EmptyState";
import { UserFeedCard } from "./UserFeedCard";
import type { FeedGridProps } from "@/types";

export function FeedGrid({
  pagedUsers,
  visibleCount,
  page,
  totalPages,
  setPage,
  onMessage,
  onResetFilters,
  onAdjustPreferences,
}: FeedGridProps) {
  if (visibleCount === 0) {
    return (
      <EmptyState
        title="No matches for current filter"
        description="Lower the minimum match threshold or update your preferences to find more people."
        onResetFilters={onResetFilters}
        onAdjustPreferences={onAdjustPreferences}
      />
    );
  }

  return (
    <>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 sm:gap-3">
        {pagedUsers.map((u) => (
          <UserFeedCard
            key={u.user_id}
            user={u}
            onMessage={onMessage}
          />
        ))}
      </div>

      <div className="mt-5 rounded-2xl bg-stone-900/35 px-3.5 py-2.5">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs text-stone-400">
            <span className="font-medium text-stone-200">Page {page}</span>
            <span className="text-stone-500"> of {totalPages}</span>
          </p>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              className="h-8 bg-stone-900/65 hover:bg-stone-800 text-xs min-w-[72px]"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="h-8 bg-stone-900/65 hover:bg-stone-800 text-xs min-w-[72px]"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}
