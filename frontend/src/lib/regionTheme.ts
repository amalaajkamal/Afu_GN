import type { RegionName } from "../types/institution";

// Region color identities kept close to the original dashboard's hue
// mapping, re-mixed into the pastel-terracotta palette (see index.css
// --color-region-* tokens, which flip to their dark-mode variants
// automatically).
export const REGION_COLOR_VAR: Record<RegionName, string> = {
  "North America": "var(--color-region-na)",
  Europe: "var(--color-region-europe)",
  Asia: "var(--color-region-asia)",
  Oceania: "var(--color-region-oceania)",
  "South America": "var(--color-region-samerica)",
};

export const REGION_ABBREV: Record<string, string> = {
  "Global View": "All",
  "North America": "N. Amer",
  Europe: "Europe",
  Asia: "Asia",
  Oceania: "Oceania",
  "South America": "S. Amer",
};

export const GAP_COLOR_VAR: Record<string, string> = {
  "Well Implemented": "var(--color-sage)",
  "Moderately Implemented": "var(--color-amber)",
  Underimplemented: "var(--color-rose)",
};

export function regionColor(region: string): string {
  return REGION_COLOR_VAR[region as RegionName] ?? "var(--color-ocean)";
}
