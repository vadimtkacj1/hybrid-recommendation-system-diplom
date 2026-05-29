import { Loader2, X } from "lucide-react";
import { getUploadStageLabel } from "@/lib/uploadStage";
import type { UploadStage } from "@/types";

interface JobProgressBannerProps {
  progress: number;
  stage: UploadStage;
  onCancel?: () => void;
}

export function JobProgressBanner({ progress, stage, onCancel }: JobProgressBannerProps) {
  return (
    <div className="mb-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 px-4 py-3.5">
      <div className="flex items-center justify-between mb-2">
        <span className="flex items-center gap-2 text-sm font-medium text-amber-400">
          <Loader2 className="h-4 w-4 animate-spin" />
          {getUploadStageLabel(stage, progress)}
        </span>
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold tabular-nums text-amber-400">{progress}%</span>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="flex items-center justify-center h-5 w-5 rounded-full text-amber-400/60 hover:text-amber-400 hover:bg-amber-500/10 transition-colors"
              title="Cancel upload"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>

      <div className="w-full h-1.5 bg-stone-800 rounded-full overflow-hidden mb-2">
        <div
          className="h-full bg-amber-500 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
