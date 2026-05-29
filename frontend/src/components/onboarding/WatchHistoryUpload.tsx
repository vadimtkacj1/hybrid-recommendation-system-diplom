import { useRef } from "react";
import { Button } from "@/components/ui/button";
import { FileUp, Loader2, X } from "lucide-react";
import { getUploadStageLabel, getUploadStageHint } from "@/lib/uploadStage";
import type { WatchHistoryUploadProps } from "@/types";

export function WatchHistoryUpload({
  layout,
  onFile,
  loading,
  progress = 0,
  stage = "idle",
  disabled,
  onCancel,
}: WatchHistoryUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const trigger = () => inputRef.current?.click();

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (f) onFile(f);
  };

  if (layout === "inline") {
    return (
      <>
        <input
          ref={inputRef}
          type="file"
          accept=".json,application/json"
          className="hidden"
          onChange={onChange}
        />
        <div className="flex items-center gap-1.5">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={trigger}
            disabled={disabled}
            className="border-stone-700 hover:bg-stone-800 hover:border-stone-600 text-stone-300 h-8 text-xs gap-1.5"
          >
            {loading ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <FileUp className="h-3.5 w-3.5" />
            )}
            {loading ? getUploadStageLabel(stage, progress) : "watch-history.json"}
          </Button>
          {loading && onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="flex items-center justify-center h-8 w-8 rounded-md text-stone-500 hover:text-stone-300 hover:bg-stone-800 transition-colors"
              title="Cancel upload"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </>
    );
  }

  const isUploading = stage === "uploading";
  const isProcessing = stage === "processing";
  const showPulse = loading && (isProcessing || progress >= 100);

  return (
    <div className="rounded-2xl border border-stone-800 p-6 sm:p-8 text-left max-w-xl mx-auto mb-8">
      <h2 className="text-lg font-semibold text-stone-100 mb-2">Connect your YouTube history</h2>
      <p className="text-sm text-stone-500 mb-5 leading-relaxed">
        Upload your{" "}
        <span className="text-stone-300 font-medium">watch-history.json</span> from Google Takeout
        to get accurate recommendations based on what you actually watch.
      </p>
      <ol className="text-sm text-stone-500 space-y-2.5 mb-6 list-decimal list-inside leading-relaxed">
        <li>Go to <span className="text-stone-300 font-medium">takeout.google.com</span> and select only YouTube.</li>
        <li>Download and unzip the archive, find <span className="text-stone-300 font-medium">watch-history.json</span>.</li>
        <li>Upload it below  you can update it anytime to refresh your matches.</li>
      </ol>
      <input
        ref={inputRef}
        type="file"
        accept=".json,application/json"
        className="hidden"
        onChange={onChange}
      />
      {loading ? (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-stone-400 mb-1">
            <span className="flex items-center gap-2">
              <Loader2 className="h-3.5 w-3.5 animate-spin text-amber-500" />
              {getUploadStageLabel(stage, progress)}
            </span>
            <div className="flex items-center gap-2">
              {(isUploading || isProcessing) && (
                <span className="text-amber-400 font-semibold tabular-nums">{progress}%</span>
              )}
              {onCancel && (
                <button
                  type="button"
                  onClick={onCancel}
                  className="flex items-center justify-center h-5 w-5 rounded-full text-stone-500 hover:text-stone-300 hover:bg-stone-800 transition-colors"
                  title="Cancel upload"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          </div>
          <div className="w-full h-2 bg-stone-800 rounded-full overflow-hidden">
            {showPulse ? (
              <div className="h-full bg-amber-500/60 rounded-full animate-pulse w-full" />
            ) : (
              <div
                className="h-full bg-amber-500 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            )}
          </div>
          <p className="text-xs text-stone-600 text-center">{getUploadStageHint(stage)}</p>
          <div className="pt-1">
            <button
              type="button"
              onClick={trigger}
              disabled={disabled}
              className="text-xs text-stone-500 hover:text-stone-300 underline underline-offset-2 transition-colors disabled:opacity-40"
            >
              Select a different file
            </button>
          </div>
        </div>
      ) : (
        <Button
          type="button"
          onClick={trigger}
          disabled={disabled}
          className="bg-amber-500 hover:bg-amber-400 text-stone-950 font-semibold rounded-xl gap-2"
        >
          <FileUp className="h-4 w-4" />
          Upload watch-history.json
        </Button>
      )}
    </div>
  );
}
