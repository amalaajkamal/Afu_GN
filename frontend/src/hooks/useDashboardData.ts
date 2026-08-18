import { useMemo } from "react";
import { useQueries } from "@tanstack/react-query";
import { useCountries, useMeta, useRegions } from "./useApi";
import { useCountrySnapshot } from "./useStaticData";
import { apiClient } from "../lib/apiClient";
import { toStaticCountryName } from "../lib/countryNameMap";
import { REGION_NAMES } from "../types/institution";
import type { StaticCountry, StaticRegion } from "../types/staticData";

export interface CountryRow extends StaticCountry {
  uncoordinated?: boolean;
}

export interface RegionRow extends StaticRegion {
  countriesMissing: number;
  countryCoveragePct: number;
}

export interface DashboardData {
  isLoading: boolean;
  apiLive: boolean;
  countries: CountryRow[];
  regions: RegionRow[];
  uncoordinatedCountries: string[];
  kpis: {
    totalInstitutions: number;
    countries: number;
    naMembers: number;
    naSharePct: number;
  };
  meta: ReturnType<typeof useMeta>["data"];
}

/** Ports app.py's merge_live_country_data / merge_live_regional_data: overlay
 * live counts from api.py onto the static lat/lon + country-total table, so
 * the map/charts always have coordinates even when the API is fresher than
 * the static snapshot (or unreachable, in which case we just show static). */
export function useDashboardData(): DashboardData {
  const metaQuery = useMeta();
  const regionsQuery = useRegions();
  const countriesQuery = useCountries();
  const snapshotQuery = useCountrySnapshot();

  const apiLive =
    !metaQuery.isError && !!metaQuery.data && metaQuery.data.total_institutions > 0;

  const perRegionCountryQueries = useQueries({
    queries: REGION_NAMES.map((region) => ({
      queryKey: ["countries", region],
      queryFn: () => apiClient.fetchCountries({ region }),
      enabled: apiLive,
      staleTime: 5 * 60 * 1000,
    })),
  });

  return useMemo(() => {
    const snapshot = snapshotQuery.data;
    const isLoading =
      metaQuery.isLoading ||
      regionsQuery.isLoading ||
      countriesQuery.isLoading ||
      snapshotQuery.isLoading;

    if (!snapshot) {
      return {
        isLoading: true,
        apiLive: false,
        countries: [],
        regions: [],
        uncoordinatedCountries: [],
        kpis: { totalInstitutions: 0, countries: 0, naMembers: 0, naSharePct: 0 },
        meta: metaQuery.data,
      };
    }

    // ── Countries: overlay live counts onto static lat/lon table ──────────
    const liveCountryCounts: Record<string, number> = {};
    if (apiLive && countriesQuery.data) {
      for (const [name, count] of Object.entries(countriesQuery.data.countries)) {
        const canonical = toStaticCountryName(name);
        liveCountryCounts[canonical] = (liveCountryCounts[canonical] ?? 0) + count;
      }
    }
    const staticNames = new Set(snapshot.countries.map((c) => c.country));
    const countries: CountryRow[] = snapshot.countries.map((c) => ({
      ...c,
      afuMembers: liveCountryCounts[c.country] ?? c.afuMembers,
    }));
    const uncoordinatedCountries =
      apiLive && countriesQuery.data
        ? Object.keys(liveCountryCounts).filter((name) => !staticNames.has(name)).sort()
        : [];

    // ── Regions: overlay live institution counts + distinct-country-in-AFU
    // counts (derived per-region, since the region endpoint alone doesn't
    // break countries out by region) ───────────────────────────────────────
    const liveRegionCounts = apiLive ? regionsQuery.data?.regions : undefined;
    const liveCountriesInAfu: Record<string, number> = {};
    if (apiLive) {
      REGION_NAMES.forEach((region, i) => {
        const q = perRegionCountryQueries[i];
        if (q.data) {
          const names = new Set(
            Object.keys(q.data.countries).map((n) => toStaticCountryName(n)),
          );
          liveCountriesInAfu[region] = names.size;
        }
      });
    }

    const regions: RegionRow[] = snapshot.regions.map((r) => {
      const afuInstitutions = liveRegionCounts?.[r.region] ?? r.afuInstitutions;
      const countriesInAfu = liveCountriesInAfu[r.region] ?? r.countriesInAfu;
      return {
        ...r,
        afuInstitutions,
        countriesInAfu,
        countriesMissing: r.totalCountries - countriesInAfu,
        countryCoveragePct:
          r.totalCountries > 0 ? Math.round((countriesInAfu / r.totalCountries) * 1000) / 10 : 0,
      };
    });

    const totalInstitutions =
      apiLive && metaQuery.data
        ? metaQuery.data.total_institutions
        : regions.reduce((sum, r) => sum + r.afuInstitutions, 0);
    const countriesKpi =
      apiLive && countriesQuery.data
        ? Object.keys(liveCountryCounts).length
        : regions.reduce((sum, r) => sum + r.countriesInAfu, 0);
    const naMembers = regions.find((r) => r.region === "North America")?.afuInstitutions ?? 0;
    const naSharePct = totalInstitutions ? Math.round((naMembers / totalInstitutions) * 100) : 0;

    return {
      isLoading,
      apiLive,
      countries,
      regions,
      uncoordinatedCountries,
      kpis: {
        totalInstitutions,
        countries: countriesKpi,
        naMembers,
        naSharePct,
      },
      meta: metaQuery.data,
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    metaQuery.data,
    metaQuery.isLoading,
    regionsQuery.data,
    regionsQuery.isLoading,
    countriesQuery.data,
    countriesQuery.isLoading,
    snapshotQuery.data,
    snapshotQuery.isLoading,
    apiLive,
    ...perRegionCountryQueries.map((q) => q.data),
  ]);
}
