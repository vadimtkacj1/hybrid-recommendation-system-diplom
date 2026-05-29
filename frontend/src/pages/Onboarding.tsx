import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { WatchHistoryUpload } from "@/components/onboarding";
import { useWatchHistoryUpload } from "@/hooks/useWatchHistoryUpload";
import { useAuth } from "@/context/AuthContext";

export function Onboarding() {
  const navigate = useNavigate();
  const { refreshUser, logout } = useAuth();

  const {
    upload,
    loading: uploadLoading,
    progress: uploadProgress,
    stage: uploadStage,
    error: uploadError,
  } = useWatchHistoryUpload(async () => {
    await refreshUser();
    navigate("/dashboard", { replace: true });
  });

  useEffect(() => {}, [uploadLoading]);

  return (
    <div className="min-h-screen bg-stone-950 flex flex-col items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">

        <div className="mb-8">
          <h1 className="text-2xl font-semibold tracking-tight text-stone-100 mb-2">
            Build your profile
          </h1>
          <p className="text-sm text-stone-500 leading-relaxed">
            Upload your YouTube watch history to find people with similar interests.
          </p>
        </div>

        <WatchHistoryUpload
          layout="hero"
          onFile={upload}
          loading={uploadLoading}
          progress={uploadProgress}
          stage={uploadStage}
        />

        {uploadError && (
          <p className="text-red-400 text-sm text-center mt-3">{uploadError}</p>
        )}

        <div className="text-center mt-8">
          <button
            type="button"
            onClick={logout}
            className="text-xs text-stone-600 hover:text-stone-400 transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>
    </div>
  );
}
