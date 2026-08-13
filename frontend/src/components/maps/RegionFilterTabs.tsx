import { useTheme } from "../../theme/ThemeProvider";
import { getMapTheme } from "../../lib/mapTheme";
import { REGION_ABBREV } from "../../lib/regionTheme";
import type { RegionRow } from "../../hooks/useDashboardData";
import type { RegionName } from "../../types/institution";

interface Props {
  regions: RegionRow[];
  total: number;
  selected: string;
  onSelect: (region: string) => void;
}

export function RegionFilterTabs({ regions, total, selected, onSelect }: Props) {
  const { resolvedTheme } = useTheme();
  const theme = getMapTheme(resolvedTheme);

  const tabs = [
    { region: "Global View", count: total },
    ...regions.map((r) => ({ region: r.region, count: r.afuInstitutions })),
  ];

  return (
    <div
      role="tablist"
      aria-label="Filter map by region"
      className="mt-3 flex flex-wrap gap-2 sm:flex-nowrap sm:overflow-x-auto"
    >
      {tabs.map(({ region, count }) => {
        const isActive = selected === region;
        const color =
          region === "Global View"
            ? "var(--color-ink-terracotta)"
            : theme.regionColorsInk[region as RegionName];
        return (
          <button
            key={region}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onSelect(region)}
            title={region}
            style={
              isActive
                ? { background: color, color: "var(--text-inverse)", borderColor: color }
                : undefined
            }
            className={[
              "flex min-h-11 shrink-0 items-center gap-1.5 rounded-full border px-3.5 py-2 text-sm font-semibold transition-colors",
              isActive
                ? ""
                : "border-border bg-surface text-text-secondary hover:bg-surface-muted",
            ].join(" ")}
          >
            {REGION_ABBREV[region] ?? region}
            <span className="tabular-nums opacity-80">{count}</span>
          </button>
        );
      })}
    </div>
  );
}
