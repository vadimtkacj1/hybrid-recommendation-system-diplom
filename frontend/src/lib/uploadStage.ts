import type { UploadStage } from "@/types";

export function getUploadStageLabel(stage: UploadStage, progress: number): string {
  if (stage === "uploading") return "Uploading…";
  if (stage === "processing") return progress >= 95 ? "Building profile…" : "Processing history…";
  return "Analyzing…";
}

export function getUploadStageHint(stage: UploadStage): string {
  if (stage === "uploading") return "Do not close this page";
  if (stage === "processing") return "Analyzing your watch history in the background…";
  return "";
}
