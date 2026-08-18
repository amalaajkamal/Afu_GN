import { useMemo } from "react";
import { useQueries } from "@tanstack/react-query";
import { apiClient } from "../lib/apiClient";
import { toApiCountryName } from "../lib/countryNameMap";
import { jitteredPoint } from "../lib/jitter";
import { useCountrySnapshot } from "./useStaticData";
import type { CountryRow } from "./useDashboardData";

export interface InstitutionPoint {
  name: string;
  url: string | null;
  country: string;
  region: string;
  latitude: number;
  longitude: number;
  geocoded: boolean;
}

interface InstitutionRaw {
  name: string;
  url: string | null;
  latitude: number | null;
  longitude: number | null;
}

/** For each requested country, live institution list (name + url + lat/lon)
 * if the API has it, else falls back to the static name-only list — ports
 * get_institutions_for_country() from app.py. */
export function useInstitutionsByCountry(countries: string[], apiLive: boolean) {
  const snapshotQuery = useCountrySnapshot();

  const queries = useQueries({
    queries: countries.map((country) => ({
      queryKey: ["members", "country", country],
      queryFn: () => apiClient.fetchMembers({ country: toApiCountryName(country) }),
      enabled: apiLive,
      staleTime: 5 * 60 * 1000,
    })),
  });

  return useMemo(() => {
    const result: Record<string, InstitutionRaw[]> = {};
    countries.forEach((country, i) => {
      const live = queries[i]?.data;
      if (apiLive && live && live.results.length > 0) {
        result[country] = live.results.map((m) => ({
          name: m.name,
          url: m.url,
          latitude: m.latitude,
          longitude: m.longitude,
        }));
      } else {
        const names = snapshotQuery.data?.institutionsByCountry[country] ?? [];
        result[country] = names.map((name) => ({
          name,
          url: null,
          latitude: null,
          longitude: null,
        }));
      }
    });
    return result;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [countries.join("|"), apiLive, snapshotQuery.data, ...queries.map((q) => q.data)]);
}

/** Expands country rows into one marker per institution, using real
 * coordinates where geocoded and a deterministic jittered fallback
 * otherwise — ports institution_points() from app.py. */
export function useInstitutionPoints(countries: CountryRow[], apiLive: boolean): InstitutionPoint[] {
  const countryNames = countries.map((c) => c.country);
  const byCountry = useInstitutionsByCountry(countryNames, apiLive);

  return useMemo(() => {
    const points: InstitutionPoint[] = [];
    for (const row of countries) {
      const insts = byCountry[row.country] ?? [];
      const n = row.afuMembers;
      for (let i = 0; i < n; i++) {
        const inst = insts[i] ?? { name: `${row.country} institution ${i + 1}`, url: null, latitude: null, longitude: null };
        const hasCoords = inst.latitude != null && inst.longitude != null;
        const { latitude, longitude } = hasCoords
          ? { latitude: inst.latitude as number, longitude: inst.longitude as number }
          : jitteredPoint(`${row.country}|${i}`, row.latitude, row.longitude);
        points.push({
          name: inst.name,
          url: inst.url,
          country: row.country,
          region: row.region,
          latitude,
          longitude,
          geocoded: hasCoords,
        });
      }
    }
    return points;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [countries, byCountry]);
}
