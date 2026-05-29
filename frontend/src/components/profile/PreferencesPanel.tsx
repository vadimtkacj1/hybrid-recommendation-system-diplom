import { WatchHistoryUpload } from "../onboarding/WatchHistoryUpload";
import type { PreferencesPanelProps } from "@/types";

export function PreferencesPanel({
  onYoutubeFile,
  onYoutubeCancel,
  youtubeLoading,
  youtubeStage,
  youtubeProgress,
  error,
}: PreferencesPanelProps) {
  return (
    <div className="rounded-2xl border border-stone-800 bg-stone-900/40 overflow-hidden mb-8">
      <div className="p-5 sm:p-6">
        <WatchHistoryUpload
          layout="hero"
          onFile={onYoutubeFile}
          loading={youtubeLoading}
          stage={youtubeStage}
          progress={youtubeProgress}
          onCancel={onYoutubeCancel}
        />
        {error && (
          <p className="text-red-400 text-sm mt-3 text-center">{error}</p>
        )}
      </div>
    </div>
  );
}
