import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/apiClient";

// Mirrors useResearch.ts's caching strategy for the independent
// social-isolation topic/dataset (see research.py).
const STALE_TIME_MS = 5 * 60 * 1000;
const RETRY = 1;

export function useSocialIsolationMeta() {
  return useQuery({
    queryKey: ["social-isolation-research-meta"],
    queryFn: apiClient.fetchSocialIsolationMeta,
    staleTime: STALE_TIME_MS,
    retry: RETRY,
    refetchInterval: (query) =>
      query.state.data && query.state.data.total_papers > 0 ? false : 15_000,
  });
}

export function useSocialIsolationPapers(opts?: { year?: string }) {
  return useQuery({
    queryKey: ["social-isolation-research-papers", opts?.year ?? "all"],
    queryFn: () => apiClient.fetchSocialIsolationPapers(opts),
    staleTime: STALE_TIME_MS,
    retry: RETRY,
    // See useResearch.ts's useResearchPapers -- same non-blocking
    // cold-cache behavior on the backend, same poll-until-populated fix.
    refetchInterval: (query) => (query.state.data && query.state.data.count > 0 ? false : 5_000),
  });
}

export function useSocialIsolationResearchers(limit = 50) {
  return useQuery({
    queryKey: ["social-isolation-researchers", limit],
    queryFn: () => apiClient.fetchSocialIsolationResearchers({ limit: String(limit) }),
    staleTime: STALE_TIME_MS,
    retry: RETRY,
    refetchInterval: (query) => (query.state.data && query.state.data.count > 0 ? false : 5_000),
  });
}
