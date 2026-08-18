import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CircleAlert, CircleCheck, RefreshCw } from "lucide-react";
import { useMeta } from "../../hooks/useApi";
import { apiClient } from "../../lib/apiClient";

function formatAge(scrapedAt: number | null): string {
  if (!scrapedAt) return "unknown";
  const ageMin = Math.floor((Date.now() / 1000 - scrapedAt) / 60);
  if (ageMin < 1) return "just now";
  if (ageMin < 120) return `${ageMin} min ago`;
  return `${Math.floor(ageMin / 60)} hr ago`;
}

export function LiveStatusBadge() {
  const { data, isError, isLoading } = useMeta();
  const queryClient = useQueryClient();
  const [refreshing, setRefreshing] = useState(false);

  const isLive = !isLoading && !isError && !!data && data.total_institutions > 0;

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await apiClient.triggerRefresh();
      await queryClient.invalidateQueries();
    } catch {
      // best-effort — badge will just keep showing the current status
    } finally {
      setRefreshing(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1.5 text-sm text-text-secondary">
        <span className="h-2 w-2 animate-pulse rounded-full bg-text-secondary" />
        Checking API…
      </div>
    );
  }

  if (!isLive) {
    return (
      <div className="flex items-center gap-2 rounded-full border border-rose/40 bg-rose/10 px-3 py-1.5 text-sm text-ink-rose">
        <CircleAlert size={16} strokeWidth={2.25} />
        <span className="hidden sm:inline">Live API unavailable — static snapshot</span>
        <span className="sm:hidden">API offline</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-2 rounded-full border border-sage/40 bg-sage/10 px-3 py-1.5 text-sm text-ink-sage">
        <CircleCheck size={16} strokeWidth={2.25} />
        <span className="hidden sm:inline">
          Connected — {data!.total_institutions} institutions, updated {formatAge(data!.scraped_at)}
        </span>
        <span className="sm:hidden tabular-nums">{data!.total_institutions} institutions</span>
      </div>
      <button
        type="button"
        onClick={handleRefresh}
        disabled={refreshing}
        aria-label="Refresh live data"
        title="Refresh live data"
        className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-text-primary transition-colors hover:bg-surface-muted disabled:opacity-50"
      >
        <RefreshCw size={18} strokeWidth={2} className={refreshing ? "animate-spin" : ""} />
      </button>
    </div>
  );
}
