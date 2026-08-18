import type { RegionName } from "../types/institution";

// Plotly can't read CSS custom properties, so the palette is duplicated here
// as literal hex values matching index.css's light/dark tokens. Keep these
// two files in sync if the palette ever changes.
export interface MapTheme {
  bg: string;
  land: string;
  ocean: string;
  coast: string;
  country: string;
  gridText: string;
  regionColors: Record<RegionName, string>;
  /** Darkened (WCAG AA, >=4.5:1 with white text) region colors, for use as a
   * solid fill behind white text (e.g. an active region tab/pill) — the
   * plain regionColors are only safe as large graphical marks. */
  regionColorsInk: Record<RegionName, string>;
  gapColors: Record<string, string>;
}

const LIGHT: MapTheme = {
  bg: "#faf6f1",
  land: "#e6d3ba",
  ocean: "#d7e6ea",
  coast: "#a8916f",
  country: "#c9b79f",
  gridText: "#6b5d4f",
  regionColors: {
    "North America": "#d97757",
    Europe: "#6e8fa8",
    Asia: "#e0a458",
    Oceania: "#a487a0",
    "South America": "#6ea89a",
  },
  regionColorsInk: {
    "North America": "#a34425",
    Europe: "#496479",
    Asia: "#885719",
    Oceania: "#765972",
    "South America": "#3f695f",
  },
  gapColors: {
    "Well Implemented": "#8fa888",
    "Moderately Implemented": "#e0a458",
    Underimplemented: "#c96a6a",
  },
};

const DARK: MapTheme = {
  bg: "#211d1a",
  land: "#332c27",
  ocean: "#241e2b",
  coast: "#40372f",
  country: "#40372f",
  gridText: "#b8a996",
  regionColors: {
    "North America": "#e38a68",
    Europe: "#7fa9ba",
    Asia: "#e3b06b",
    Oceania: "#b79bb2",
    "South America": "#7fbaac",
  },
  regionColorsInk: {
    "North America": "#e38a68",
    Europe: "#7fa9ba",
    Asia: "#e3b06b",
    Oceania: "#b79bb2",
    "South America": "#7fbaac",
  },
  gapColors: {
    "Well Implemented": "#7e9c77",
    "Moderately Implemented": "#e3b06b",
    Underimplemented: "#d97f7f",
  },
};

export function getMapTheme(resolvedTheme: "light" | "dark"): MapTheme {
  return resolvedTheme === "dark" ? DARK : LIGHT;
}
