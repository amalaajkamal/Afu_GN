import { useState } from "react";
import { LayoutGrid } from "lucide-react";
import { PageHeader } from "../components/layout/PageHeader";
import { KpiCard } from "../components/cards/KpiCard";
import { WorldImpactMap } from "../components/maps/WorldImpactMap";
import { RegionFilterTabs } from "../components/maps/RegionFilterTabs";
import { RegionDonutChart } from "../components/charts/RegionDonutChart";
import { RegionBarChart } from "../components/charts/RegionBarChart";
import { useDashboardData } from "../hooks/useDashboardData";
import { useInstitutionPoints } from "../hooks/useInstitutions";
import { useIndiaGeojson } from "../hooks/useStaticData";

export function GlobalOverviewPage() {
  const { isLoading, apiLive, countries, regions, kpis, uncoordinatedCountries } =
    useDashboardData();
  const indiaGeojsonQuery = useIndiaGeojson();
  const [selectedRegion, setSelectedRegion] = useState<string>("Global View");

  const mapCountries =
    selectedRegion === "Global View" ? countries : countries.filter((c) => c.region === selectedRegion);
  const points = useInstitutionPoints(mapCountries, apiLive);

  function handleSelectRegion(region: string) {
    setSelectedRegion((current) => (current === region ? "Global View" : region));
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader
        title="Global Overview"
        subtitle="Geographic & thematic snapshot of the AFU Global Network"
        icon={<LayoutGrid size={20} strokeWidth={2.25} />}
      />

      {isLoading ? (
        <div className="mb-3 h-20 shrink-0 animate-pulse rounded-xl bg-surface-muted" />
      ) : (
        <div className="mb-3 flex shrink-0 flex-wrap gap-2">
          <KpiCard value={kpis.totalInstitutions} label="Member Institutions" accent="terracotta" />
          <KpiCard value={`${kpis.naSharePct}%`} label="North America Share" accent="clay" />
          <KpiCard value={kpis.countries} label="Countries" accent="sage" />
          <KpiCard value={28} label="Best Practices" accent="amber" />
          <KpiCard value="14% / 18%" label="P5 & P7 Citation Rate" accent="rose" />
          <KpiCard value="13%" label="Submission Rate" accent="ocean" />
        </div>
      )}

      {!apiLive && !isLoading && (
        <p className="mb-3 shrink-0 rounded-lg border border-amber/40 bg-amber/10 px-3 py-2 text-sm text-text-primary">
          Live API unavailable — showing the static snapshot. Start it with{" "}
          <code className="rounded bg-surface-muted px-1 py-0.5 font-mono text-xs">
            uvicorn api:app --reload --port 8000
          </code>
          .
        </p>
      )}
      {uncoordinatedCountries.length > 0 && (
        <details className="mb-3 shrink-0 rounded-lg border border-border bg-surface-muted px-3 py-2 text-sm text-text-secondary">
          <summary className="cursor-pointer select-none font-medium text-text-primary">
            {uncoordinatedCountries.length} countries have no plotted coordinates yet
          </summary>
          <p className="mt-1">{uncoordinatedCountries.join(", ")}</p>
        </details>
      )}

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 overflow-hidden lg:grid-cols-[minmax(0,2.3fr)_minmax(0,1fr)]">
        <div className="flex min-h-0 flex-col gap-2 overflow-y-auto">
          <WorldImpactMap
            countries={countries}
            points={points}
            indiaGeojson={indiaGeojsonQuery.data}
            selectedRegion={selectedRegion}
          />
          <RegionFilterTabs
            regions={regions}
            total={kpis.totalInstitutions}
            selected={selectedRegion}
            onSelect={handleSelectRegion}
          />
        </div>
        <div className="flex min-h-0 flex-col gap-4 overflow-y-auto rounded-xl border border-border bg-surface p-4 shadow-sm">
          <RegionDonutChart regions={regions} selected={selectedRegion} onSelect={handleSelectRegion} />
          <RegionBarChart regions={regions} selected={selectedRegion} onSelect={handleSelectRegion} />
        </div>
      </div>
    </div>
  );
}
