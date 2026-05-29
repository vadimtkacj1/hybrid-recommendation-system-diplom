import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import type { UploadStage } from "@/types";

const POLL_MS = 1500;
const JOB_KEY = "likemind_upload_job_id";

export function useWatchHistoryUpload(onSuccess: () => void) {
  const { token } = useAuth();

  // Keep latest values in refs so intervals can read them without stale closures.
  const onSuccessRef = useRef(onSuccess);
  onSuccessRef.current = onSuccess;
  const tokenRef = useRef(token);
  tokenRef.current = token;

  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState<UploadStage>("idle");
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = () => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  };

  const resetToIdle = () => {
    setLoading(false);
    setProgress(0);
    setStage("idle");
  };

  // Starts an interval that polls job status until completion or failure.
  // Used both by the new-upload path and the resume-on-mount path.
  const startPolling = (job_id: string) => {
    clearTimer();
    timerRef.current = setInterval(async () => {
      const tok = tokenRef.current;
      if (!tok) return;
      try {
        const s = await api.youtube.jobStatus(tok, job_id);
        if (s.status === "completed") {
          clearTimer();
          localStorage.removeItem(JOB_KEY);
          setProgress(100);
          // Brief pause so the user sees 100 %, then clean up and signal success.
          setTimeout(() => {
            resetToIdle();
            onSuccessRef.current();
          }, 500);
        } else if (s.status === "failed") {
          clearTimer();
          localStorage.removeItem(JOB_KEY);
          setError(s.error ?? "Processing failed");
          resetToIdle();
        } else {
          // pending | processing  map server 0-100 to display 50-95
          setProgress(50 + Math.round((s.progress ?? 0) * 0.45));
        }
      } catch {
        // Network hiccup  stay quiet and retry on the next tick.
      }
    }, POLL_MS);
  };

  // On mount (and whenever token becomes available): look for an in-progress job.
  // Priority: localStorage → server fallback.
  useEffect(() => {
    if (!token) return;

    const tryResume = async (jobId: string) => {
      try {
        const s = await api.youtube.jobStatus(token, jobId);
        if (s.status === "pending" || s.status === "processing") {
          setLoading(true);
          setStage("processing");
          setProgress(50 + Math.round((s.progress ?? 0) * 0.45));
          startPolling(jobId);
        } else {
          localStorage.removeItem(JOB_KEY);
          if (s.status === "completed") onSuccessRef.current();
        }
      } catch {
        localStorage.removeItem(JOB_KEY);
      }
    };

    const saved = localStorage.getItem(JOB_KEY);
    if (saved) {
      void tryResume(saved);
      return () => clearTimer();
    }

    // Fallback: ask the server (covers cleared localStorage / different device, etc.)
    api.youtube
      .activeJob(token)
      .then((job) => {
        if (job && (job.status === "pending" || job.status === "processing")) {
          localStorage.setItem(JOB_KEY, job.job_id);
          setLoading(true);
          setStage("processing");
          setProgress(50 + Math.round((job.progress ?? 0) * 0.45));
          startPolling(job.job_id);
        }
      })
      .catch(() => {});

    return () => clearTimer();
    // startPolling is stable within a render; token is the only real dep here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const upload = async (file: File) => {
    if (!token) {
      setError("Not authenticated. Please sign in again.");
      return;
    }
    setLoading(true);
    setProgress(0);
    setStage("uploading");
    setError(null);

    try {
      // ── Phase 1: transfer file (progress 0 → 45 %) ────────────────────
      const { job_id } = await api.youtube.uploadWatchHistory(token, file, (pct) => {
        setProgress(Math.round(pct * 0.45));
      });

      localStorage.setItem(JOB_KEY, job_id);

      // ── Phase 2: wait for server processing (progress 50 → 100 %) ────
      setStage("processing");
      setProgress(50);

      await new Promise<void>((resolve, reject) => {
        clearTimer();
        timerRef.current = setInterval(async () => {
          try {
            const s = await api.youtube.jobStatus(token, job_id);
            if (s.status === "completed") {
              clearTimer();
              localStorage.removeItem(JOB_KEY);
              setProgress(100);
              resolve();
            } else if (s.status === "failed") {
              clearTimer();
              localStorage.removeItem(JOB_KEY);
              reject(new Error(s.error ?? "Processing failed"));
            } else {
              setProgress(50 + Math.round((s.progress ?? 0) * 0.45));
            }
          } catch {
            clearTimer();
            reject(new Error("Network error during processing"));
          }
        }, POLL_MS);
      });

      onSuccessRef.current();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      clearTimer();
      localStorage.removeItem(JOB_KEY);
      resetToIdle();
    }
  };

  const cancel = () => {
    clearTimer();
    localStorage.removeItem(JOB_KEY);
    resetToIdle();
  };

  return { upload, cancel, loading, progress, stage, error, clearError: () => setError(null) };
}
