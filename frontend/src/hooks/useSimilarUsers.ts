import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SimilarUser, UserProfile } from "@/types";

export function useSimilarUsers(token: string | null) {
  const [similarUsers, setSimilarUsers] = useState<SimilarUser[]>([]);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    if (!token) {
      setLoading(false);
      setSimilarUsers([]);
      setProfile(null);
      return;
    }
    setLoading(true);
    try {
      const [similarRes, profileRes] = await Promise.all([
        api.recommendations.similarUsers(token, 1000, 0.0),
        api.recommendations.profile(token).catch(() => null),
      ]);
      setSimilarUsers(similarRes?.users ?? []);
      setProfile(profileRes ?? null);
    } catch {
      setSimilarUsers([]);
      setProfile(null);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { similarUsers, profile, loading, refetch: fetchData };
}
