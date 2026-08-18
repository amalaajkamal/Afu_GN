import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../lib/apiClient";

// Client-side staleTime mirrors api.py's 12h server-side cache TTL: no point
// refetching more often than the server would return fresh data anyway.
const STALE_TIME_MS = 5 * 60 * 1000; // re-check every 5 min while a tab stays open
const RETRY = 1;

export function useMeta() {
  return useQuery({
    queryKey: ["meta"],
    queryFn: apiClient.fetchMeta,
    staleTime: STALE_TIME_MS,
    retry: RETRY,
    // api.py's /meta doesn't block on the initial scrape, so a request that
    // lands while the first scrape is still running reads total_institutions:
    // 0 and we'd otherwise be stuck showing "unavailable" until something
    // else (window focus, remount) triggers a refetch. Poll until live.
    refetchInterval: (query) =>
      query.state.data && query.state.data.total_institutions > 0 ? false : 15_000,
  });
}

export function useRegions() {
  return useQuery({
    queryKey: ["regions"],
    queryFn: apiClient.fetchRegions,
    staleTime: STALE_TIME_MS,
    retry: RETRY,
  });
}

export function useCountries(region?: string) {
  return useQuery({
    queryKey: ["countries", region ?? "all"],
    queryFn: () => apiClient.fetchCountries(region ? { region } : undefined),
    staleTime: STALE_TIME_MS,
    retry: RETRY,
  });
}

export function useMembers(opts?: { region?: string; country?: string }) {
  return useQuery({
    queryKey: ["members", opts?.region ?? "all", opts?.country ?? "all"],
    queryFn: () => apiClient.fetchMembers(opts),
    staleTime: STALE_TIME_MS,
    retry: RETRY,
    enabled: true,
  });
}
