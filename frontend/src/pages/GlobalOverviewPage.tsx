import { useMemo, useState } from "react";
import { ArrowLeft, ExternalLink, GraduationCap, LayoutGrid } from "lucide-react";
import { PageHeader } from "../components/layout/PageHeader";
import { KpiCard } from "../components/cards/KpiCard";
import { StatChip } from "../components/cards/StatChip";
import { WorldImpactMap } from "../components/maps/WorldImpactMap";
import { RegionFilterTabs } from "../components/maps/RegionFilterTabs";
import { RegionDonutChart } from "../components/charts/RegionDonutChart";
import { useDashboardData } from "../hooks/useDashboardData";
import { useInstitutionPoints, useInstitutionsByCountry } from "../hooks/useInstitutions";
import { useIndiaGeojson } from "../hooks/useStaticData";

export function GlobalOverviewPage() {
  const { isLoading, apiLive, countries, regions, kpis, uncoordinatedCountries } =
    useDashboardData();
  const indiaGeojsonQuery = useIndiaGeojson();
  const [selectedRegion, setSelectedRegion] = useState<string>("Global View");
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);

  const mapCountries =
    selectedRegion === "Global View" ? countries : countries.filter((c) => c.region === selectedRegion);
  const points = useInstitutionPoints(mapCountries, apiLive);

  const regionCountries = useMemo(
    () =>
      selectedRegion === "Global View"
        ? []
        : countries.filter((c) => c.region === selectedRegion).sort((a, b) => b.afuMembers - a.afuMembers),
    [countries, selectedRegion],
  );
  const institutionsByCountry = useInstitutionsByCountry(selectedCountry ? [selectedCountry] : [], apiLive);
  const countryInstitutions = selectedCountry ? (institutionsByCountry[selectedCountry] ?? []) : [];

  const regionStat = regions.find((r) => r.region === selectedRegion);
  const countryStat = countries.find((c) => c.country === selectedCountry);

  function handleSelectRegion(region: string) {
    setSelectedRegion((current) => (current === region ? "Global View" : region));
    setSelectedCountry(null);
  }

  function handleSelectCountry(country: string) {
    setSelectedCountry((current) => (current === country ? null : country));
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader
        title="Global Overview"
        subtitle="Geographic & thematic snapshot — drill down from region to country to institution"
        icon={<LayoutGrid size={20} strokeWidth={2.25} />}
        actions={
          <a
            href="https://www.afugn.org/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-sm font-medium text-text-secondary transition-colors hover:bg-surface-muted hover:text-text-primary"
          >
            Institution data from the AFU Global Network
            <ExternalLink size={14} strokeWidth={2.25} />
          </a>
        }
      />

      {isLoading ? (
        <div className="mb-3 h-20 shrink-0 animate-pulse rounded-xl bg-surface-muted" />
      ) : (
        <div className="mb-3 flex shrink-0 flex-wrap gap-2">
          <KpiCard value={kpis.totalInstitutions} label="Member Institutions" accent="terracotta" />
          <KpiCard value={`${kpis.naSharePct}%`} label="North America Share" accent="clay" />
          <KpiCard value={kpis.countries} label="Countries" accent="sage" />
          <KpiCard value={28} label="Best Practices" accent="amber" />
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
            countries={mapCountries}
            points={points}
            indiaGeojson={indiaGeojsonQuery.data}
            selectedRegion={selectedRegion}
            selectedCountry={selectedCountry}
          />
          <div className="shrink-0 rounded-xl border border-border bg-surface p-3 shadow-sm">
            <RegionFilterTabs
              regions={regions}
              total={kpis.totalInstitutions}
              selected={selectedRegion}
              onSelect={handleSelectRegion}
            />

            {selectedRegion !== "Global View" && (
              <div
                key={selectedCountry ?? selectedRegion}
                className="animate-fade-slide-in mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-border pt-3"
              >
                {selectedCountry && countryStat ? (
                  <>
                    <StatChip value={countryStat.afuMembers} label="AFU Members" accent="terracotta" />
                    <span className="text-sm font-semibold text-text-primary">
                      {selectedCountry}{" "}
                      <span className="font-normal text-text-secondary">— {countryStat.region}</span>
                    </span>
                  </>
                ) : regionStat ? (
                  <>
                    <StatChip value={regionStat.afuInstitutions} label="Institutions" accent="terracotta" />
                    <StatChip
                      value={`${regionStat.countriesInAfu}/${regionStat.totalCountries}`}
                      label="Countries in AFU"
                      accent="sage"
                    />
                    <StatChip value={`${regionStat.countryCoveragePct}%`} label="Coverage" accent="amber" />
                  </>
                ) : null}
              </div>
            )}
          </div>
        </div>

        <div className="flex min-h-0 flex-col gap-2 overflow-y-auto rounded-xl border border-border bg-surface p-4 shadow-sm">
          {selectedCountry ? (
            <div key={selectedCountry} className="animate-fade-slide-in flex min-h-0 flex-1 flex-col gap-2">
              <button
                type="button"
                onClick={() => handleSelectCountry(selectedCountry)}
                className="mb-1 flex shrink-0 items-center gap-1 self-start text-xs font-semibold text-ink-terracotta transition-transform hover:-translate-x-0.5 hover:underline"
              >
                <ArrowLeft size={12} /> Back to {selectedRegion} countries
              </button>
              <h3 className="mb-1 flex shrink-0 items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-text-secondary">
                <GraduationCap size={14} /> Institutions in {selectedCountry} ({countryInstitutions.length})
              </h3>
              <ul className="flex min-h-0 flex-1 flex-col gap-1.5 overflow-y-auto">
                {countryInstitutions.map((inst) => (
                  <li
                    key={inst.name}
                    className="rounded-lg border-l-4 border-terracotta bg-surface-muted px-2.5 py-2 text-sm transition-all duration-150 hover:translate-x-0.5 hover:bg-terracotta-soft/60 hover:shadow-sm"
                  >
                    {inst.url ? (
                      <a
                        href={inst.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-ink-terracotta underline decoration-1 underline-offset-2"
                      >
                        {inst.name}
                        <ExternalLink size={12} className="shrink-0" />
                      </a>
                    ) : (
                      inst.name
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ) : selectedRegion !== "Global View" ? (
            <div key={selectedRegion} className="animate-fade-slide-in flex min-h-0 flex-1 flex-col gap-2">
              <h3 className="mb-2 shrink-0 text-xs font-bold uppercase tracking-wide text-text-secondary">
                Countries in {selectedRegion}
              </h3>
              <div className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto">
                {regionCountries.map((c) => (
                  <button
                    key={c.country}
                    type="button"
                    onClick={() => handleSelectCountry(c.country)}
                    className="flex min-h-11 items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-left text-sm text-text-primary transition-all duration-150 hover:translate-x-0.5 hover:bg-surface-muted hover:shadow-sm"
                  >
                    <span className="truncate">{c.country}</span>
                    <span className="tabular-nums text-text-secondary">{c.afuMembers}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div key="donut" className="animate-fade-slide-in">
              <RegionDonutChart regions={regions} selected={selectedRegion} onSelect={handleSelectRegion} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
