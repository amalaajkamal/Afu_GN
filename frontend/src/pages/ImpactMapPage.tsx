import { useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { ExternalLink, GraduationCap, Map } from "lucide-react";
import { PageHeader } from "../components/layout/PageHeader";
import { KpiCard } from "../components/cards/KpiCard";
import { WorldImpactMap } from "../components/maps/WorldImpactMap";
import { useDashboardData } from "../hooks/useDashboardData";
import { useInstitutionPoints, useInstitutionsByCountry } from "../hooks/useInstitutions";
import { useIndiaGeojson } from "../hooks/useStaticData";
import { getMapTheme } from "../lib/mapTheme";
import { useTheme } from "../theme/ThemeProvider";
import type { RegionName } from "../types/institution";

export function ImpactMapPage() {
  const { isLoading, apiLive, countries, regions, kpis } = useDashboardData();
  const indiaGeojsonQuery = useIndiaGeojson();
  const { resolvedTheme } = useTheme();
  const theme = getMapTheme(resolvedTheme);
  const [params, setParams] = useSearchParams();

  const selectedRegion = params.get("region");
  const selectedCountry = params.get("country");

  function selectRegion(region: string) {
    if (region === selectedRegion) {
      setParams({});
    } else {
      setParams({ region });
    }
  }

  function selectCountry(country: string) {
    if (country === selectedCountry) {
      setParams(selectedRegion ? { region: selectedRegion } : {});
    } else {
      setParams(selectedRegion ? { region: selectedRegion, country } : { country });
    }
  }

  const regionCountries = useMemo(
    () =>
      selectedRegion
        ? countries.filter((c) => c.region === selectedRegion).sort((a, b) => b.afuMembers - a.afuMembers)
        : [],
    [countries, selectedRegion],
  );

  const mapCountries = selectedRegion ? regionCountries : countries;
  const points = useInstitutionPoints(mapCountries, apiLive);
  const institutionsByCountry = useInstitutionsByCountry(selectedCountry ? [selectedCountry] : [], apiLive);
  const countryInstitutions = selectedCountry ? (institutionsByCountry[selectedCountry] ?? []) : [];

  const regionStat = regions.find((r) => r.region === selectedRegion);
  const countryStat = countries.find((c) => c.country === selectedCountry);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader
        title="Impact Map"
        subtitle="Drill down from region to country to institution"
        icon={<Map size={20} strokeWidth={2.25} />}
      />

      <div
        role="tablist"
        aria-label="Filter by region"
        className="mb-3 flex shrink-0 flex-wrap gap-2 sm:flex-nowrap sm:overflow-x-auto"
      >
        {regions.map((r) => {
          const isActive = selectedRegion === r.region;
          const color = theme.regionColorsInk[r.region as RegionName];
          return (
            <button
              key={r.region}
              type="button"
              role="tab"
              aria-selected={isActive}
              onClick={() => selectRegion(r.region)}
              style={
                isActive
                  ? { background: color, color: "var(--text-inverse)", borderColor: color }
                  : undefined
              }
              className={[
                "flex min-h-11 shrink-0 items-center gap-1.5 rounded-full border px-3.5 py-2 text-sm font-semibold transition-colors",
                isActive ? "" : "border-border bg-surface text-text-secondary hover:bg-surface-muted",
              ].join(" ")}
            >
              {r.region}
              <span className="tabular-nums opacity-80">{r.afuInstitutions}</span>
            </button>
          );
        })}
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 overflow-hidden lg:grid-cols-[auto_1fr_auto]">
        {selectedRegion && (
          <aside className="order-2 flex min-h-0 w-full flex-col rounded-xl border border-border bg-surface p-3 shadow-sm lg:order-1 lg:w-56">
            <h3 className="mb-2 shrink-0 text-xs font-bold uppercase tracking-wide text-text-secondary">
              Countries
            </h3>
            <div className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto">
              {regionCountries.map((c) => {
                const isSel = selectedCountry === c.country;
                return (
                  <button
                    key={c.country}
                    type="button"
                    onClick={() => selectCountry(c.country)}
                    aria-pressed={isSel}
                    className={[
                      "flex min-h-11 items-center justify-between gap-2 rounded-lg px-2.5 py-2 text-left text-sm transition-colors",
                      isSel
                        ? "bg-terracotta-soft font-semibold text-ink-terracotta"
                        : "text-text-primary hover:bg-surface-muted",
                    ].join(" ")}
                  >
                    <span className="truncate">{c.country}</span>
                    <span className="tabular-nums text-text-secondary">{c.afuMembers}</span>
                  </button>
                );
              })}
            </div>
          </aside>
        )}

        <div className="order-1 flex min-h-0 flex-col overflow-y-auto lg:order-2">
          {isLoading ? (
            <div className="h-[460px] animate-pulse rounded-xl bg-surface-muted" />
          ) : (
            <WorldImpactMap
              countries={mapCountries}
              points={points}
              indiaGeojson={indiaGeojsonQuery.data}
              selectedRegion={selectedRegion}
              selectedCountry={selectedCountry}
              height={420}
            />
          )}

          <div className="mt-3 flex flex-wrap gap-3">
            {selectedCountry && countryStat ? (
              <>
                <KpiCard value={countryStat.afuMembers} label="AFU Members" accent="terracotta" />
                <KpiCard
                  value={`${selectedCountry} — ${countryStat.region}`}
                  label="Country / Region"
                  accent="ocean"
                />
              </>
            ) : selectedRegion && regionStat ? (
              <>
                <KpiCard value={regionStat.afuInstitutions} label="Institutions" accent="terracotta" />
                <KpiCard
                  value={`${regionStat.countriesInAfu}/${regionStat.totalCountries}`}
                  label="Countries in AFU"
                  accent="sage"
                />
                <KpiCard value={`${regionStat.countryCoveragePct}%`} label="Coverage" accent="amber" />
              </>
            ) : (
              <>
                <KpiCard value={kpis.totalInstitutions} label="Institutions" accent="terracotta" />
                <KpiCard value={kpis.countries} label="Countries" accent="sage" />
                <KpiCard value={5} label="Regions" accent="amber" />
                <KpiCard value={`${kpis.naSharePct}%`} label="N. America Share" accent="rose" />
              </>
            )}
          </div>
        </div>

        {selectedCountry && (
          <aside className="order-3 flex min-h-0 w-full flex-col rounded-xl border border-border bg-surface p-3 shadow-sm lg:w-72">
            <h3 className="mb-2 flex shrink-0 items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-text-secondary">
              <GraduationCap size={14} /> Institutions ({countryInstitutions.length})
            </h3>
            <ul className="flex min-h-0 flex-1 flex-col gap-1.5 overflow-y-auto">
              {countryInstitutions.map((inst) => (
                <li
                  key={inst.name}
                  className="rounded-lg border-l-4 border-terracotta bg-surface-muted px-2.5 py-2 text-sm"
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
          </aside>
        )}
      </div>
    </div>
  );
}
