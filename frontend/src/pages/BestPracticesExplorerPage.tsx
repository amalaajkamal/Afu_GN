import { useMemo, useState } from "react";
import { ExternalLink, GraduationCap } from "lucide-react";
import { PageHeader } from "../components/layout/PageHeader";
import { KpiCard } from "../components/cards/KpiCard";
import { MultiSelect } from "../components/filters/MultiSelect";
import { BestPracticeCard } from "../components/cards/BestPracticeCard";
import { PrincipleBarChart } from "../components/charts/PrincipleBarChart";
import { useBestPractices } from "../hooks/useStaticData";
import type { Principle } from "../types/staticData";

const PRINCIPLE_OPTIONS = Array.from({ length: 10 }, (_, i) => ({
  value: String(i + 1),
  label: `Principle ${i + 1}`,
}));

export function BestPracticesExplorerPage() {
  const { data: bestPractices = [], isLoading } = useBestPractices();
  const [principleFilter, setPrincipleFilter] = useState<string[]>([]);
  const [universityFilter, setUniversityFilter] = useState<string[]>([]);

  const universityOptions = useMemo(
    () =>
      [...new Set(bestPractices.map((bp) => bp.university))]
        .sort()
        .map((u) => ({ value: u, label: u })),
    [bestPractices],
  );

  const filtered = useMemo(() => {
    return bestPractices.filter((bp) => {
      if (principleFilter.length > 0) {
        const wanted = principleFilter.map(Number);
        if (!bp.principles.some((p) => wanted.includes(p))) return false;
      }
      if (universityFilter.length > 0 && !universityFilter.includes(bp.university)) return false;
      return true;
    });
  }, [bestPractices, principleFilter, universityFilter]);

  const ongoing = filtered.filter((bp) => bp.type.toLowerCase().includes("ongoing")).length;
  const oneTime = filtered.filter((bp) => bp.type.toLowerCase().includes("one-time")).length;
  const uniqueUniversities = new Set(filtered.map((bp) => bp.university)).size;

  const filteredPrincipleCounts = useMemo<Principle[]>(() => {
    const counts = new Map<number, number>();
    for (const bp of filtered) {
      for (const p of bp.principles) counts.set(p, (counts.get(p) ?? 0) + 1);
    }
    const total = filtered.length || 1;
    return Array.from({ length: 10 }, (_, i) => {
      const num = i + 1;
      const mentions = counts.get(num) ?? 0;
      return {
        principleNumber: num,
        shortLabel: `P${num}`,
        mentions,
        pct: Math.round((mentions / total) * 100),
        gapFlag:
          mentions / total >= 0.4
            ? "Well Implemented"
            : mentions / total >= 0.2
              ? "Moderately Implemented"
              : "Underimplemented",
      };
    });
  }, [filtered]);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader
        title="Best Practices Explorer"
        subtitle="All submissions from the AFU GN Best Practices Database"
        icon={<GraduationCap size={20} strokeWidth={2.25} />}
        actions={
          <div className="flex flex-col items-end gap-1">
            <a
              href="https://airtable.com/appcW4hq3850mytJX/shrOrioKpp8IsmtcY/tblKGptn0ITbmceeg/viwopw5izbORstgTi"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm font-medium text-text-secondary transition-colors hover:bg-surface-muted hover:text-text-primary"
            >
              View source data
              <ExternalLink size={14} strokeWidth={2.25} />
            </a>
            <p className="text-right text-xs text-text-secondary">
              Data last downloaded and updated: June 2026.
            </p>
          </div>
        }
      />

      <div className="mb-3 grid shrink-0 grid-cols-1 gap-3 sm:grid-cols-2 sm:max-w-xl">
        <MultiSelect
          label="Filter by Principle"
          options={PRINCIPLE_OPTIONS}
          selected={principleFilter}
          onChange={setPrincipleFilter}
        />
        <MultiSelect
          label="Filter by University"
          options={universityOptions}
          selected={universityFilter}
          onChange={setUniversityFilter}
        />
      </div>

      {isLoading ? (
        <div className="h-24 shrink-0 animate-pulse rounded-xl bg-surface-muted" />
      ) : (
        <>
          <p className="mb-2 shrink-0 text-sm font-medium text-text-secondary">
            Showing {filtered.length} of {bestPractices.length} submissions
          </p>

          <div className="mb-3 flex shrink-0 flex-wrap gap-2">
            <KpiCard value={ongoing} label="Ongoing Activities" accent="sage" />
            <KpiCard value={oneTime} label="One-Time Activities" accent="amber" />
            <KpiCard value={uniqueUniversities} label="Unique Universities" accent="ocean" />
          </div>

          <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 overflow-hidden lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
            {filtered.length > 0 && (
              <div className="min-h-0 overflow-y-auto rounded-xl border border-border bg-surface p-4 shadow-sm">
                <PrincipleBarChart principles={filteredPrincipleCounts} height={320} />
              </div>
            )}

            <div className="min-h-0 space-y-3 overflow-y-auto pr-1">
              {filtered.map((bp, i) => (
                <BestPracticeCard key={`${bp.title}-${i}`} bp={bp} />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
