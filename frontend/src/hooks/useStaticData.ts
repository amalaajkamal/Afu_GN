import { useQuery } from "@tanstack/react-query";
import { staticData } from "../lib/staticData";

// Static files never change at runtime, so cache them for the life of the tab.
const STATIC_STALE_TIME_MS = Infinity;

export function usePrinciples() {
  return useQuery({
    queryKey: ["static", "principles"],
    queryFn: staticData.principles,
    staleTime: STATIC_STALE_TIME_MS,
  });
}

export function useBestPractices() {
  return useQuery({
    queryKey: ["static", "best-practices"],
    queryFn: staticData.bestPractices,
    staleTime: STATIC_STALE_TIME_MS,
  });
}

export function usePopulation65() {
  return useQuery({
    queryKey: ["static", "population-65"],
    queryFn: staticData.population65,
    staleTime: STATIC_STALE_TIME_MS,
  });
}

export function useCountrySnapshot() {
  return useQuery({
    queryKey: ["static", "country-snapshot"],
    queryFn: staticData.countrySnapshot,
    staleTime: STATIC_STALE_TIME_MS,
  });
}

export function useIndiaGeojson() {
  return useQuery({
    queryKey: ["static", "india-geojson"],
    queryFn: staticData.indiaGeojson,
    staleTime: STATIC_STALE_TIME_MS,
  });
}
