import { AlertTriangle } from "lucide-react";
import type { UploadErrorBannerProps } from "@/types";

export function UploadErrorBanner({ message, onClose }: UploadErrorBannerProps) {
  return (
    <div className="mb-6 flex items-start gap-3 px-4 py-3 rounded-xl border border-red-500/20 bg-red-500/5 text-red-300/90 text-sm">
      <AlertTriangle className="h-4 w-4 mt-0.5 shrink-0 text-red-400/70" />
      <span className="flex-1 leading-relaxed">{message}</span>
      <button
        type="button"
        onClick={onClose}
        className="text-xs text-red-400/80 underline shrink-0"
      >
        Dismiss
      </button>
    </div>
  );
}
