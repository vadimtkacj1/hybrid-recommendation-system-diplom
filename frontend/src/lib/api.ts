const API_BASE = import.meta.env.VITE_API_URL || "";

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = "ApiError";
  }
}

export async function fetchApi<T>(
  path: string,
  options?: RequestInit & { token?: string },
): Promise<T> {
  const { token, ...init } = options ?? {};
  const headers: HeadersInit = {
    ...(init.body != null ? { "Content-Type": "application/json" } : {}),
    ...(init.headers as Record<string, string>),
  };
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers, redirect: "manual" });
  if (!res.ok) {
    if (res.type === "opaqueredirect") {
      throw new ApiError("Unexpected redirect", 0);
    }
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(err.detail ?? res.statusText, res.status);
  }
  return res.json();
}

type AuthResponse = {
  access_token: string;
  user: {
    id: string;
    email: string;
    name: string;
    picture?: string;
    has_watch_history: boolean;
  };
};

export const api = {
  get: <T>(path: string, token?: string) =>
    fetchApi<T>(path, { token }),
  auth: {
    register: (email: string, password: string, name: string) =>
      fetchApi<AuthResponse>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password, name }),
      }),
    login: (email: string, password: string) =>
      fetchApi<AuthResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      }),
    me: (token: string) =>
      fetchApi<{
        id: string;
        email: string;
        name: string;
        picture?: string;
        has_watch_history: boolean;
      }>("/api/auth/me", {
        token,
      }),
  },
  users: {
    me: (token: string) =>
      fetchApi<{
        id: string;
        email: string;
        name: string;
        picture?: string;
        youtube_linked: boolean;
        has_watch_history: boolean;
      }>("/api/users/me", { token }),
    updateProfile: (token: string, name: string) =>
      fetchApi<{
        id: string;
        email: string;
        name: string;
        picture?: string;
        youtube_linked: boolean;
        has_watch_history: boolean;
      }>("/api/users/me", {
        method: "PATCH",
        token,
        body: JSON.stringify({ name }),
      }),
    uploadAvatar: async (token: string, file: File) => {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/api/users/me/avatar`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail ?? res.statusText);
      }
      return res.json() as Promise<{
        id: string;
        email: string;
        name: string;
        picture?: string;
        youtube_linked: boolean;
      }>;
    },
  },
  youtube: {
    uploadWatchHistory: (
      token: string,
      file: File,
      onProgress?: (pct: number) => void,
    ) =>
      new Promise<{ job_id: string }>((resolve, reject) => {
        const form = new FormData();
        form.append("file", file);
        const xhr = new XMLHttpRequest();
        xhr.open("POST", `${API_BASE}/api/youtube/watch-history`);
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) onProgress?.(Math.round((e.loaded / e.total) * 100));
        };
        xhr.onload = () => {
          let body: Record<string, unknown>;
          try { body = JSON.parse(xhr.responseText); } catch { body = {}; }
          if (xhr.status < 200 || xhr.status >= 300) {
            reject(new Error(typeof body.detail === "string" ? body.detail : xhr.statusText));
          } else {
            resolve(body as { job_id: string });
          }
        };
        xhr.onerror = () => reject(new Error("Network error"));
        xhr.send(form);
      }),
    jobStatus: (token: string, jobId: string) =>
      fetchApi<{
        job_id: string;
        status: string;
        progress: number;
        synced_count?: number | null;
        total_count?: number | null;
        profile_updated?: boolean | null;
        error?: string | null;
      }>(`/api/youtube/watch-history/job/${jobId}`, { token }),
    activeJob: (token: string) =>
      fetchApi<{
        job_id: string;
        status: string;
        progress: number;
        synced_count?: number | null;
        total_count?: number | null;
        profile_updated?: boolean | null;
        error?: string | null;
      } | null>(`/api/youtube/watch-history/active-job`, { token }),
    status: (token: string) =>
      fetchApi<{ video_count: number; profile_computed: boolean }>("/api/youtube/status", {
        token,
      }),
  },
  chat: {
    conversations: (token: string) =>
      fetchApi<
        {
          peer_id: string;
          peer_name: string | null;
          peer_picture: string | null;
          last_message: string;
          last_message_at: string;
          unread_count: number;
        }[]
      >("/api/chat/conversations", { token }),
    unreadCount: (token: string) =>
      fetchApi<{ unread: number }>("/api/chat/unread-count", { token }),
  },
  recommendations: {
    similarUsers: (
      token: string,
      limit = 15,
      minSimilarity = 0.1,
    ) =>
      fetchApi<{
        users: {
          user_id: string;
          name: string | null;
          picture: string | null;
          similarity: number;
          top_topics: string[];
          video_count: number;
        }[];
        total: number;
      }>(
        `/api/recommendations/similar-users?limit=${limit}&min_similarity=${minSimilarity}&algo=hybrid`,
        { token },
      ),
    profile: (token: string) =>
      fetchApi<{
        video_count: number;
        has_interests?: boolean;
        top_categories?: string[];
        top_topics?: string[];
        youtube_connected?: boolean;
      }>("/api/recommendations/profile", { token }),
  },
};
