import type { LucideIcon } from "lucide-react";
import type { ReactNode, ElementType } from "react";

// ─── Domain ──────────────────────────────────────────────────────────────────

export interface SimilarUser {
  user_id: string;
  name: string | null;
  picture: string | null;
  similarity: number;
  top_topics: string[];
  video_count: number;
}

export interface UserProfile {
  video_count: number;
  has_interests?: boolean;
  top_categories?: string[];
  top_topics?: string[];
  computed_at?: string | null;
  youtube_connected?: boolean;
}

export interface ChatPeer {
  id: string;
  name: string | null;
  picture: string | null;
}

export interface Message {
  id: string;
  sender_id: string;
  receiver_id: string;
  content: string;
  created_at: string;
  is_read?: boolean;
}

export interface Conversation {
  peer_id: string;
  peer_name: string | null;
  peer_picture: string | null;
  last_message: string;
  last_message_at: string;
  unread_count: number;
}

export interface Category {
  name: string;
  icon: LucideIcon;
}

// ─── UI ───────────────────────────────────────────────────────────────────────

export type DashboardTab = "recommend" | "stats";
export type OnboardingStep = "youtube";
export type SortBy = "match_desc" | "match_asc" | "name" | "shared_desc";
export type PreferencesMethod = "youtube";

// ─── Props ────────────────────────────────────────────────────────────────────

export interface MethodCardProps {
  icon: ElementType;
  title: string;
  description: string;
  onClick: () => void;
}

export interface StatProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  valueClass?: string;
}

export interface ChatPanelProps {
  token: string;
  currentUserId: string;
  peer: ChatPeer;
  onClose: () => void;
}

export interface ConversationsPanelProps {
  token: string;
  onSelectPeer: (peer: ChatPeer) => void;
  onClose: () => void;
}

export interface EmptyStateProps {
  title?: string;
  description?: string;
  onResetFilters?: () => void;
  onAdjustPreferences?: () => void;
}

export interface FeedFiltersProps {
  minMatch: number;
  setMinMatch: (v: number) => void;
  searchQuery: string;
  setSearchQuery: (v: string) => void;
  topicFilter: string;
  setTopicFilter: (v: string) => void;
  sortBy: SortBy;
  setSortBy: (v: SortBy) => void;
  onlyShared: boolean;
  setOnlyShared: (v: boolean) => void;
  availableTopics: string[];
}

export interface FeedGridProps {
  pagedUsers: SimilarUser[];
  visibleCount: number;
  page: number;
  totalPages: number;
  setPage: (updater: number | ((prev: number) => number)) => void;
  onMessage: (peer: ChatPeer) => void;
  onResetFilters: () => void;
  onAdjustPreferences: () => void;
}

export interface RecommendTabProps {
  similarUsers: SimilarUser[];
  profile: UserProfile | null;
  loading: boolean;
  onMessage: (peer: ChatPeer) => void;
  onAdjustPreferences: () => void;
}

export interface ChatOverlayProps {
  token: string;
  currentUserId: string;
  activeChat: ChatPeer | null;
  showInbox: boolean;
  onSelectPeer: (peer: ChatPeer) => void;
  onCloseChat: () => void;
  onCloseInbox: () => void;
}

export interface UploadErrorBannerProps {
  message: string;
  onClose: () => void;
}

export interface ProfileStatsProps {
  profile: UserProfile;
  matchCount: number;
  similarUsers?: SimilarUser[];
}

export interface UserFeedCardProps {
  user: SimilarUser;
  onMessage: (peer: ChatPeer) => void;
}

export interface PreferencesPanelProps {
  onYoutubeFile: (file: File) => void;
  onYoutubeCancel?: () => void;
  youtubeLoading: boolean;
  youtubeStage?: UploadStage;
  youtubeProgress?: number;
  error?: string | null;
}

export type UploadStage = "idle" | "uploading" | "processing" | "done";

export interface WatchHistoryUploadProps {
  layout: "hero" | "inline";
  onFile: (file: File) => void;
  loading: boolean;
  progress?: number;
  stage?: UploadStage;
  disabled?: boolean;
  onCancel?: () => void;
}

export interface ProfilePhotoPickerProps {
  token: string;
  onUploaded: () => void;
  children: (open: () => void, busy: boolean) => ReactNode;
}

export interface InterestPickerProps {
  onSave: (categories: string[]) => void;
  loading: boolean;
  initialCategories?: string[];
}
