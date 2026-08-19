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
    // api.py's /research/papers never blocks on a cold cache -- it returns
    // an empty result immediately while a background OpenAlex fetch runs
    // (which can take up to ~30s the first time). Poll until papers show up
    // instead of leaving the page stuck on an empty state.
    refetchInterval: (query) => (query.state.data && query.state.data.count > 0 ? false : 5_000),
  });
}

export function useResearchers(limit = 50) {
  return useQuery({
    queryKey: ["researchers", limit],
    queryFn: () => apiClient.fetchResearchers({ limit: String(limit) }),
    staleTime: STALE_TIME_MS,
    retry: RETRY,
    refetchInterval: (query) => (query.state.data && query.state.data.count > 0 ? false : 5_000),
  });
}
