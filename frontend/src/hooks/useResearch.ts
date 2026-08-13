import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/apiClient";

// Mirrors useApi.ts's client-side staleTime, matching research.py's own
// server-side cache TTL relationship (5 min client re-check under a much
// longer 24h server-side OpenAlex cache).
const STALE_TIME_MS = 5 * 60 * 1000;
const RETRY = 1;

export function useResearchMeta() {
  return useQuery({
    queryKey: ["research-meta"],
    queryFn: apiClient.fetchResearchMeta,
    staleTime: STALE_TIME_MS,
    retry: RETRY,
    // Same pattern as useMeta(): the first-ever OpenAlex fetch can take a
    // little while, so poll until the cache has actually populated.
    refetchInterval: (query) =>
      query.state.data && query.state.data.total_papers > 0 ? false : 15_000,
  });
}

export function useResearchPapers(opts?: { year?: string }) {
  return useQuery({
    queryKey: ["research-papers", opts?.year ?? "all"],
    queryFn: () => apiClient.fetchResearchPapers(opts),
    staleTime: STALE_TIME_MS,
    retry: RETRY,
  });
}

export function useResearchers(limit = 50) {
  return useQuery({
    queryKey: ["researchers", limit],
    queryFn: () => apiClient.fetchResearchers({ limit: String(limit) }),
    staleTime: STALE_TIME_MS,
    retry: RETRY,
  });
}
