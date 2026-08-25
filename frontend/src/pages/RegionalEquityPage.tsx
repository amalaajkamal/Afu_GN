import { Compass } from "lucide-react";
import { PageHeader } from "../components/layout/PageHeader";
import { CoverageStackedBarChart } from "../components/charts/CoverageStackedBarChart";
import { DensityBarChart } from "../components/charts/DensityBarChart";
import type { DensityRow } from "../components/charts/DensityBarChart";
import { useDashboardData } from "../hooks/useDashboardData";
import { usePopulation65 } from "../hooks/useStaticData";

export function RegionalEquityPage() {
  const { isLoading, countries, regions } = useDashboardData();
  const population65Query = usePopulation65();

  const density: DensityRow[] = countries
    .map((c) => {
      const pop = population65Query.data?.[c.country];
      if (!pop) return null;
      return {
        country: c.country,
        region: c.region,
        afuMembers: c.afuMembers,
        pop65M: Math.round((pop.pop65 / 1e6) * 100) / 100,
        perMillionSeniors: pop.perMillionSeniors,
      };
    })
    .filter((r): r is DensityRow => r !== null && r.perMillionSeniors > 0);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader
        title="Regional Distribution"
        subtitle="Country coverage gaps and age-adjusted AFU density"
        icon={<Compass size={20} strokeWidth={2.25} />}
      />

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 overflow-hidden lg:grid-cols-2">
        <div className="flex min-h-0 flex-col overflow-y-auto rounded-xl border border-border bg-surface p-4 shadow-sm">
          {isLoading ? (
            <div className="h-72 animate-pulse rounded-lg bg-surface-muted" />
          ) : (
            <>
              <CoverageStackedBarChart regions={regions} />
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="text-text-secondary">
                      <th className="py-1 pr-2 font-medium">Region</th>
                      <th className="py-1 pr-2 font-medium">In AFU GN</th>
                      <th className="py-1 pr-2 font-medium">Total</th>
                      <th className="py-1 pr-2 font-medium">Not Rep.</th>
                      <th className="py-1 font-medium">Coverage %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {regions.map((r) => (
                      <tr key={r.region} className="border-t border-border">
                        <td className="py-1.5 pr-2">{r.region}</td>
                        <td className="py-1.5 pr-2 tabular-nums">{r.countriesInAfu}</td>
                        <td className="py-1.5 pr-2 tabular-nums">{r.totalCountries}</td>
                        <td className="py-1.5 pr-2 tabular-nums">{r.countriesMissing}</td>
                        <td className="py-1.5 tabular-nums">{r.countryCoveragePct}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>

        <div className="flex min-h-0 flex-col overflow-y-auto rounded-xl border border-border bg-surface p-4 shadow-sm">
          {isLoading || population65Query.isLoading ? (
            <div className="h-80 animate-pulse rounded-lg bg-surface-muted" />
          ) : (
            <DensityBarChart rows={density} />
          )}
        </div>
      </div>
    </div>
  );
}
