import { useEffect, useRef, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { fetchApi } from "@/lib/api";
import { resolvePictureUrl } from "@/lib/media";
import { Loader2, Send, X } from "lucide-react";
import type { ChatPanelProps, Message } from "@/types";

export function ChatPanel({ token, currentUserId, peer, onClose }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchApi<Message[]>(`/api/chat/messages/${peer.id}`, { token })
      .then((msgs) => setMessages(msgs))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [peer.id, token]);

  useEffect(() => {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/api/chat/ws?token=${token}`);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      const msg: Message & { sender_name?: string; sender_picture?: string } = JSON.parse(e.data);
      const inConversation =
        (msg.sender_id === currentUserId && msg.receiver_id === peer.id) ||
        (msg.sender_id === peer.id && msg.receiver_id === currentUserId);
      if (inConversation) {
        setMessages((prev) => {
          if (prev.some((m) => m.id === msg.id)) return prev;
          return [...prev, msg];
        });
      }
    };

    wsRef.current = ws;
    return () => ws.close();
  }, [token, currentUserId, peer.id]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = () => {
    const text = input.trim();
    if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ receiver_id: peer.id, content: text }));
    setInput("");
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const peerInitial = (peer.name ?? "?")[0].toUpperCase();

  return (
    <div className="flex flex-col h-full bg-stone-950 border border-stone-800 rounded-none sm:rounded-2xl overflow-hidden shadow-2xl">
      <div className="flex items-center gap-3 px-4 py-3 border-b border-stone-800 bg-stone-900/60">
        <Avatar className="h-8 w-8 border border-stone-700">
          <AvatarImage src={resolvePictureUrl(peer.picture)} />
          <AvatarFallback className="bg-stone-800 text-stone-200 text-xs font-bold">
            {peerInitial}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-stone-100 text-sm truncate">{peer.name ?? "User"}</p>
          <p className={`text-xs ${connected ? "text-emerald-500" : "text-stone-600"}`}>
            {connected ? "Online" : "Connecting..."}
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="text-stone-500 hover:text-stone-200 shrink-0 px-2"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 min-h-0">
        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-stone-600" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-center">
            <p className="text-stone-600 text-sm">No messages yet.</p>
            <p className="text-stone-700 text-xs">Be the first to write</p>
          </div>
        ) : (
          messages.map((m) => {
            const isMe = m.sender_id === currentUserId;
            return (
              <div key={m.id} className={`flex ${isMe ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[75%] px-3.5 py-2 rounded-2xl text-sm leading-relaxed ${
                    isMe
                      ? "bg-amber-500 text-stone-950 rounded-br-sm"
                      : "bg-stone-800 text-stone-100 rounded-bl-sm"
                  }`}
                >
                  {m.content}
                  <p className={`text-[10px] mt-1 ${isMe ? "text-stone-800/70" : "text-stone-500"}`}>
                    {new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      <div className="px-4 py-3 border-t border-stone-800 bg-stone-900/40">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Write a message..."
            maxLength={2000}
            className="flex-1 bg-stone-800 border border-stone-700 rounded-xl px-4 py-2 text-sm text-stone-100 placeholder-stone-600 outline-none focus:border-stone-600 transition-colors"
          />
          <Button
            onClick={send}
            disabled={!input.trim() || !connected}
            size="sm"
            className="bg-amber-500 hover:bg-amber-400 text-stone-950 rounded-xl px-3 disabled:opacity-40"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
