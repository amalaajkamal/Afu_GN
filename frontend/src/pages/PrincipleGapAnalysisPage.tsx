import { Ruler } from "lucide-react";
import { PageHeader } from "../components/layout/PageHeader";
import { KpiCard } from "../components/cards/KpiCard";
import { PrincipleBarChart } from "../components/charts/PrincipleBarChart";
import { AudienceBarChart } from "../components/charts/AudienceBarChart";
import { usePrinciples, useBestPractices } from "../hooks/useStaticData";

export function PrincipleGapAnalysisPage() {
  const principlesQuery = usePrinciples();
  const bestPracticesQuery = useBestPractices();
  const principles = principlesQuery.data ?? [];

  const well = principles.filter((p) => p.gapFlag === "Well Implemented").length;
  const moderate = principles.filter((p) => p.gapFlag === "Moderately Implemented").length;
  const under = principles.filter((p) => p.gapFlag === "Under Implemented").length;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader
        title="Principle Implementation Analysis"
        subtitle="Based on Best Practice submissions from AFU GN member institutions"
        icon={<Ruler size={20} strokeWidth={2.25} />}
      />

      <div className="mb-3 flex shrink-0 flex-wrap gap-2">
        <KpiCard value={well} label="Well Implemented" accent="sage" />
        <KpiCard value={moderate} label="Moderately Implemented" accent="amber" />
        <KpiCard value={under} label="Under Implemented" accent="rose" />
        <KpiCard value="18%" label="Submission Rate" accent="ocean" />
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 overflow-hidden lg:grid-cols-2">
        <div className="flex min-h-0 flex-col gap-3 overflow-y-auto rounded-xl border border-border bg-surface p-4 shadow-sm [scrollbar-gutter:stable]">
          {principlesQuery.isLoading ? (
            <div className="h-80 animate-pulse rounded-lg bg-surface-muted" />
          ) : (
            <PrincipleBarChart principles={principles} />
          )}
        </div>

        <div className="min-h-0 overflow-y-auto rounded-xl border border-border bg-surface p-4 shadow-sm">
          {bestPracticesQuery.isLoading ? (
            <div className="h-72 animate-pulse rounded-lg bg-surface-muted" />
          ) : (
            <AudienceBarChart bestPractices={bestPracticesQuery.data ?? []} />
          )}
        </div>
      </div>
    </div>
  );
}
