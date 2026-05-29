import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { AppHeader } from "@/components/layout";
import {
  PreferencesPanel,
  ProfileStats,
  UploadErrorBanner,
  JobProgressBanner,
} from "@/components/profile";
import { RecommendTab } from "@/components/feed";
import { ChatOverlay } from "@/components/chat";
import { useAuth } from "@/context/AuthContext";
import { useSimilarUsers } from "@/hooks/useSimilarUsers";
import { useWatchHistoryUpload } from "@/hooks/useWatchHistoryUpload";
import { api } from "@/lib/api";
import type { ChatPeer, DashboardTab } from "@/types";
import { MessageSquare, Pencil } from "lucide-react";

export function Dashboard() {
  const { user, token } = useAuth();
  const { similarUsers, profile, loading, refetch } = useSimilarUsers(token);

  const [activeChat, setActiveChat] = useState<ChatPeer | null>(null);
  const [showInbox, setShowInbox] = useState(false);
  const [unread, setUnread] = useState(0);
  const [tab, setTab] = useState<DashboardTab>("recommend");
  const [editingPrefs, setEditingPrefs] = useState(false);

  const {
    upload,
    cancel: cancelUpload,
    loading: uploadLoading,
    progress: uploadProgress,
    stage: uploadStage,
    error: uploadError,
    clearError: clearUploadError,
  } = useWatchHistoryUpload(async () => {
    await refetch();
    setEditingPrefs(false);
  });

  useEffect(() => {
    if (!token) return;
    api.chat.unreadCount(token).then((r) => setUnread(r.unread)).catch(() => {});
  }, [token, activeChat]);

  const hasProfile = profile != null && profile.video_count > 0;

  const handleYoutubeFile = (f: File) => {
    clearUploadError();
    void upload(f);
  };

  const openPrefsEdit = () => {
    setEditingPrefs(true);
    clearUploadError();
  };

  const cancelPrefsEdit = () => {
    setEditingPrefs(false);
    clearUploadError();
  };

  const showJobBanner = uploadLoading && hasProfile && !editingPrefs;

  const subtitle = hasProfile
    ? null
    : "Upload your YouTube history to find similar people.";

  return (
    <div className="min-h-screen bg-stone-950 text-stone-100">
      <AppHeader />

      <main className="max-w-4xl mx-auto px-4 sm:px-5 py-6 md:py-12">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-3 mb-6 sm:mb-8">
          <div>
            <h1 className="text-lg sm:text-xl font-semibold tracking-tight">
              {hasProfile ? "Find like-minded people" : "Set up your profile"}
            </h1>
            {subtitle && <p className="text-stone-600 mt-0.5 text-xs sm:text-sm leading-snug">{subtitle}</p>}
          </div>

          <div className="flex gap-2 shrink-0">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowInbox((v) => !v)}
              className="relative text-stone-400 hover:text-stone-100 hover:bg-stone-800 h-8 px-3"
            >
              <MessageSquare className="h-4 w-4" />
              {unread > 0 && (
                <span className="absolute -top-1 -right-1 text-[10px] font-bold bg-amber-500 text-stone-950 rounded-full min-w-[16px] h-4 flex items-center justify-center px-0.5">
                  {unread > 9 ? "9+" : unread}
                </span>
              )}
            </Button>

            {hasProfile && (
              <Button
                variant="outline"
                size="sm"
                onClick={editingPrefs ? cancelPrefsEdit : openPrefsEdit}
                disabled={uploadLoading}
                className="border-stone-700 hover:bg-stone-800 hover:border-stone-600 text-stone-300 h-8 text-xs gap-1.5 disabled:opacity-50"
              >
                <Pencil className="h-3.5 w-3.5" />
                {editingPrefs ? "Cancel" : "Edit preferences"}
              </Button>
            )}
          </div>
        </div>

        {/* Persistent upload progress  visible even when PreferencesPanel is closed */}
        {showJobBanner && (
          <JobProgressBanner progress={uploadProgress} stage={uploadStage} onCancel={cancelUpload} />
        )}

        {(!hasProfile || editingPrefs) && (
          <PreferencesPanel
            onYoutubeFile={handleYoutubeFile}
            onYoutubeCancel={cancelUpload}
            youtubeLoading={uploadLoading}
            youtubeStage={uploadStage}
            youtubeProgress={uploadProgress}
            error={uploadError}
          />
        )}

        {uploadError && !editingPrefs && (
          <UploadErrorBanner message={uploadError} onClose={clearUploadError} />
        )}

        {hasProfile && !editingPrefs && (
          <>
            <div className="flex p-1 rounded-xl bg-stone-900/50 border border-stone-800 mb-8">
              {(["recommend", "stats"] as DashboardTab[]).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setTab(t)}
                  className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-sm font-medium rounded-lg transition-colors ${
                    tab === t
                      ? "bg-stone-800 text-stone-100 shadow-sm"
                      : "text-stone-500 hover:text-stone-300"
                  }`}
                >
                  {t === "recommend" ? "Recommendations" : "Statistics"}
                </button>
              ))}
            </div>

            {tab === "stats" && profile && (
              <ProfileStats profile={profile} matchCount={similarUsers.length} similarUsers={similarUsers} />
            )}

            {tab === "recommend" && (
              <RecommendTab
                similarUsers={similarUsers}
                profile={profile}
                loading={loading}
                onMessage={setActiveChat}
                onAdjustPreferences={openPrefsEdit}
              />
            )}
          </>
        )}
      </main>

      {token && user && (
        <ChatOverlay
          token={token}
          currentUserId={user.id}
          activeChat={activeChat}
          showInbox={showInbox}
          onSelectPeer={setActiveChat}
          onCloseChat={() => setActiveChat(null)}
          onCloseInbox={() => setShowInbox(false)}
        />
      )}
    </div>
  );
}

export default Dashboard;
