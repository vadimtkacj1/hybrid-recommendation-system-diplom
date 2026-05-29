import { useEffect, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { fetchApi } from "@/lib/api";
import { resolvePictureUrl } from "@/lib/media";
import { pickCover } from "@/lib/covers";
import { Loader2, X } from "lucide-react";
import type { Conversation, ConversationsPanelProps } from "@/types";

export function ConversationsPanel({ token, onSelectPeer, onClose }: ConversationsPanelProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi<Conversation[]>("/api/chat/conversations", { token })
      .then(setConversations)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <div className="flex flex-col h-full bg-stone-950 border border-stone-800 rounded-none sm:rounded-2xl overflow-hidden shadow-2xl">
      <div className="flex items-center justify-between px-4 py-3 border-b border-stone-800 bg-stone-900/60">
        <h3 className="font-semibold text-stone-100 text-sm">Messages</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="text-stone-500 hover:text-stone-200 px-2"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto min-h-0">
        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-stone-600" />
          </div>
        ) : conversations.length === 0 ? (
          <p className="text-stone-600 text-sm text-center py-10 px-4">
            No conversations yet. Start a chat!
          </p>
        ) : (
          conversations.map((c) => (
            <button
              key={c.peer_id}
              onClick={() => {
                onSelectPeer({ id: c.peer_id, name: c.peer_name, picture: c.peer_picture });
                onClose();
              }}
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-stone-900/60 transition-colors border-b border-stone-800/50 last:border-b-0"
            >
              <Avatar className="h-9 w-9 shrink-0 border border-stone-700">
                <AvatarImage src={resolvePictureUrl(c.peer_picture) || pickCover(c.peer_id)} />
                <AvatarFallback className="bg-stone-800 text-stone-200 text-xs font-bold">
                  {(c.peer_name ?? "?")[0].toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0 text-left">
                <p className="text-sm font-medium text-stone-200 truncate">
                  {c.peer_name ?? "User"}
                </p>
                <p className="text-xs text-stone-500 truncate">{c.last_message}</p>
              </div>
              {c.unread_count > 0 && (
                <span className="shrink-0 text-xs font-bold bg-amber-500 text-stone-950 rounded-full min-w-[20px] h-5 flex items-center justify-center px-1">
                  {c.unread_count > 9 ? "9+" : c.unread_count}
                </span>
              )}
            </button>
          ))
        )}
      </div>
    </div>
  );
}
