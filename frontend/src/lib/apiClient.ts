import type {
  CountriesResponse,
  MembersResponse,
  MetaInfo,
  RegionsResponse,
  StatesResponse,
} from "../types/institution";
import type { PapersResponse, ResearchersResponse, ResearchMeta } from "../types/research";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {}

async function getJson<T>(path: string, params?: Record<string, string | undefined>): Promise<T> {
  const url = new URL(path, API_BASE_URL);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value) url.searchParams.set(key, value);
    }
  }
  let res: Response;
  try {
    res = await fetch(url.toString());
  } catch (err) {
    throw new ApiError(`AFU-API unreachable at ${API_BASE_URL}: ${(err as Error).message}`);
  }
  if (!res.ok) {
    throw new ApiError(`AFU-API request to ${path} failed with status ${res.status}`);
  }
  return (await res.json()) as T;
}

export const apiClient = {
  baseUrl: API_BASE_URL,

  fetchMeta: () => getJson<MetaInfo>("/meta"),

  fetchMembers: (opts?: { region?: string; country?: string }) =>
    getJson<MembersResponse>("/members", opts),

  fetchRegions: () => getJson<RegionsResponse>("/members/regions"),

  fetchCountries: (opts?: { region?: string }) =>
    getJson<CountriesResponse>("/members/countries", opts),

  fetchStates: (opts?: { country?: string }) => getJson<StatesResponse>("/members/states", opts),

  triggerRefresh: async (opts?: { region?: string }) => {
    const url = new URL("/refresh", API_BASE_URL);
    if (opts?.region) url.searchParams.set("region", opts.region);
    const res = await fetch(url.toString(), { method: "POST" });
    if (!res.ok) throw new ApiError(`Refresh request failed with status ${res.status}`);
    return (await res.json()) as { status: string; regions?: string[] | string };
  },

  fetchResearchPapers: (opts?: { year?: string }) =>
    getJson<PapersResponse>("/research/papers", opts),

  fetchResearchers: (opts?: { limit?: string }) =>
    getJson<ResearchersResponse>("/research/researchers", opts),

  fetchResearchMeta: () => getJson<ResearchMeta>("/research/meta"),

  triggerResearchRefresh: async () => {
    const url = new URL("/research/refresh", API_BASE_URL);
    const res = await fetch(url.toString(), { method: "POST" });
    if (!res.ok) throw new ApiError(`Research refresh request failed with status ${res.status}`);
    return (await res.json()) as { status: string };
  },

  fetchSocialIsolationPapers: (opts?: { year?: string }) =>
    getJson<PapersResponse>("/research/social-isolation/papers", opts),

  fetchSocialIsolationResearchers: (opts?: { limit?: string }) =>
    getJson<ResearchersResponse>("/research/social-isolation/researchers", opts),

  fetchSocialIsolationMeta: () => getJson<ResearchMeta>("/research/social-isolation/meta"),

  triggerSocialIsolationRefresh: async () => {
    const url = new URL("/research/social-isolation/refresh", API_BASE_URL);
    const res = await fetch(url.toString(), { method: "POST" });
    if (!res.ok)
      throw new ApiError(`Social isolation research refresh request failed with status ${res.status}`);
    return (await res.json()) as { status: string };
  },
};
