import { useMemo } from "react";
import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import { useTheme } from "../../theme/ThemeProvider";
import { getMapTheme } from "../../lib/mapTheme";
import { REGION_BOUNDS } from "./regionBounds";
import type { CountryRow } from "../../hooks/useDashboardData";
import type { InstitutionPoint } from "../../hooks/useInstitutions";
import type { RegionName } from "../../types/institution";

interface Props {
  countries: CountryRow[];
  points: InstitutionPoint[];
  indiaGeojson?: GeoJSON.FeatureCollection;
  /** "Global View" (or null) shows everything at full opacity. */
  selectedRegion: string | null;
  selectedCountry?: string | null;
  height?: number;
}

export function WorldImpactMap({
  countries,
  points,
  indiaGeojson,
  selectedRegion,
  selectedCountry,
  height = 460,
}: Props) {
  const { resolvedTheme } = useTheme();
  const theme = getMapTheme(resolvedTheme);
  const regionActive = selectedRegion && selectedRegion !== "Global View";
  const bounds = REGION_BOUNDS[selectedRegion ?? "Global View"] ?? REGION_BOUNDS["Global View"];

  const data = useMemo<Data[]>(() => {
    const traces: Data[] = [];

    // India's boundary as per the Indian Constitution/Government of India —
    // see CLAUDE.md — overlaid on top of Plotly's default (incorrect) atlas.
    if (indiaGeojson) {
      traces.push({
        type: "choropleth",
        geojson: indiaGeojson as unknown as object,
        locations: ["India"],
        featureidkey: "properties.name",
        z: [1],
        colorscale: [
          [0, theme.land],
          [1, theme.land],
        ],
        showscale: false,
        marker: { line: { color: theme.country, width: 0.6 } },
        hoverinfo: "skip",
        showlegend: false,
        zmin: 0,
        zmax: 1,
      } as unknown as Data);
    }

    const regionGroups = new Map<string, CountryRow[]>();
    for (const c of countries) {
      if (!regionGroups.has(c.region)) regionGroups.set(c.region, []);
      regionGroups.get(c.region)!.push(c);
    }

    for (const [region, rows] of regionGroups) {
      const color = theme.regionColors[region as RegionName] ?? theme.gridText;
      const opacity = regionActive ? (region === selectedRegion ? 1 : 0.12) : 1;

      traces.push({
        type: "scattergeo",
        lat: rows.map((r) => r.latitude),
        lon: rows.map((r) => r.longitude),
        mode: "markers+text",
        name: region,
        marker: {
          size: rows.map((r) => Math.max(10, Math.min(46, r.afuMembers / 2.3))),
          color,
          opacity,
          line: { width: 1.5, color: theme.bg },
        },
        text: rows.map((r) => String(r.afuMembers)),
        textfont: { size: 9, color: theme.bg === "#211d1a" ? "#211d1a" : "#ffffff" },
        textposition: "middle center",
        customdata: rows.map((r) => [r.country, r.afuMembers]),
        hovertemplate: "<b>%{customdata[0]}</b><br>AFU Members: %{customdata[1]}<extra></extra>",
      } as unknown as Data);
    }

    if (points.length) {
      const visiblePoints = regionActive ? points.filter((p) => p.region === selectedRegion) : points;
      const filtered = selectedCountry
        ? visiblePoints.filter((p) => p.country === selectedCountry)
        : visiblePoints;
      traces.push({
        type: "scattergeo",
        lat: filtered.map((p) => p.latitude),
        lon: filtered.map((p) => p.longitude),
        mode: "markers",
        showlegend: false,
        marker: {
          size: 4.5,
          color: theme.bg === "#211d1a" ? "#f3eae1" : "#ffffff",
          opacity: 0.9,
          line: {
            width: 1,
            color: filtered.map((p) => theme.regionColors[p.region as RegionName] ?? theme.gridText),
          },
        },
        customdata: filtered.map((p) => [p.name, p.country]),
        hovertemplate: "<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
      } as unknown as Data);
    }

    return traces;
  }, [countries, points, indiaGeojson, regionActive, selectedRegion, selectedCountry, theme]);

  const layout = useMemo<Partial<Layout>>(
    () => ({
      height,
      margin: { l: 0, r: 0, t: 0, b: 0 },
      paper_bgcolor: theme.bg,
      plot_bgcolor: theme.bg,
      showlegend: false,
      geo: {
        showframe: false,
        showcoastlines: true,
        coastlinecolor: theme.coast,
        showland: true,
        landcolor: theme.land,
        showocean: true,
        oceancolor: theme.ocean,
        showlakes: true,
        lakecolor: theme.ocean,
        showcountries: true,
        countrycolor: theme.country,
        countrywidth: 0.6,
        bgcolor: theme.bg,
        projection: { type: "natural earth" },
        lataxis: { range: bounds.lat },
        lonaxis: { range: bounds.lon },
      },
      font: { color: theme.gridText },
    }),
    [height, theme, bounds],
  );

  return (
    <div className="overflow-hidden rounded-xl border border-border bg-surface" aria-label="World map of AFU Global Network member institutions">
      <Plot
        data={data}
        layout={layout}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%", height }}
        useResizeHandler
      />
    </div>
  );
}
