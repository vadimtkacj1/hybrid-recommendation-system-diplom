import { Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { EmptyStateProps } from "@/types";

export function EmptyState({
  title = "No matches yet",
  description = "No other users share enough overlap with your profile right now. Check back after more people join.",
  onResetFilters,
  onAdjustPreferences,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-28 text-center gap-4">
      <div className="w-10 h-10 rounded-xl bg-stone-800/50 border border-stone-700/50 flex items-center justify-center">
        <Users className="h-5 w-5 text-stone-600" />
      </div>
      <div>
        <p className="text-stone-400 text-sm font-medium mb-1">{title}</p>
        <p className="text-stone-600 text-sm max-w-xs">{description}</p>
      </div>
      {(onResetFilters || onAdjustPreferences) && (
        <div className="flex items-center gap-2">
          {onResetFilters && (
            <Button variant="secondary" size="sm" onClick={onResetFilters} className="text-xs">
              Reset filters
            </Button>
          )}
          {onAdjustPreferences && (
            <Button variant="outline" size="sm" onClick={onAdjustPreferences} className="text-xs border-stone-700">
              Update preferences
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
