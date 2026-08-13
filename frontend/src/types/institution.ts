export interface Institution {
  name: string;
  region: string;
  country: string | null;
  state_province: string | null;
  url: string | null;
  latitude: number | null;
  longitude: number | null;
}

export interface MembersResponse {
  count: number;
  results: Institution[];
}

export interface RegionsResponse {
  count: number;
  total_institutions: number;
  regions: Record<string, number>;
}

export interface CountriesResponse {
  count: number;
  total_institutions: number;
  countries: Record<string, number>;
}

export interface StatesResponse {
  count: number;
  total_institutions: number;
  states: Record<string, number>;
}

export interface MetaInfo {
  total_institutions: number;
  scraped_at: number | null;
  cache_age_seconds: number | null;
  regions: string[];
}

export type RegionName = "North America" | "Europe" | "Asia" | "Oceania" | "South America";

export const REGION_NAMES: RegionName[] = [
  "North America",
  "Europe",
  "Asia",
  "Oceania",
  "South America",
];
