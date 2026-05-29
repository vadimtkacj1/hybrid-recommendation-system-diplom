import { ChatPanel } from "./ChatPanel";
import { ConversationsPanel } from "./ConversationsPanel";
import type { ChatOverlayProps } from "@/types";

export function ChatOverlay({
  token,
  currentUserId,
  activeChat,
  showInbox,
  onSelectPeer,
  onCloseChat,
  onCloseInbox,
}: ChatOverlayProps) {
  return (
    <>
      {showInbox && (
        <div className="fixed inset-0 sm:inset-auto sm:bottom-6 sm:right-6 sm:w-[320px] sm:h-[440px] z-50 shadow-2xl">
          <ConversationsPanel
            token={token}
            onSelectPeer={(peer) => { onSelectPeer(peer); onCloseInbox(); }}
            onClose={onCloseInbox}
          />
        </div>
      )}
      {activeChat && (
        <div className="fixed inset-0 sm:inset-auto sm:bottom-6 sm:right-6 sm:w-[340px] sm:h-[480px] z-50 shadow-2xl">
          <ChatPanel
            token={token}
            currentUserId={currentUserId}
            peer={activeChat}
            onClose={onCloseChat}
          />
        </div>
      )}
    </>
  );
}
