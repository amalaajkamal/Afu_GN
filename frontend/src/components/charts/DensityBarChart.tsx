import { useTheme } from "../../theme/ThemeProvider";
import { getMapTheme } from "../../lib/mapTheme";
import type { RegionName } from "../../types/institution";

export interface DensityRow {
  country: string;
  region: string;
  afuMembers: number;
  pop65M: number;
  perMillionSeniors: number;
}

export function DensityBarChart({ rows }: { rows: DensityRow[] }) {
  const { resolvedTheme } = useTheme();
  const theme = getMapTheme(resolvedTheme);
  // A linear bar chart across ~20 countries with wildly different
  // magnitudes (a couple of small, senior-heavy countries dwarfing the
  // rest) squashes most bars down to unreadable slivers -- a sortable
  // table lets every value be compared exactly instead.
  const sorted = [...rows].sort((a, b) => b.perMillionSeniors - a.perMillionSeniors);

  return (
    <div>
      <h3 className="mb-1 text-xs font-bold uppercase tracking-wide text-text-secondary">
        AFU Density per Million Seniors (2025)
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="text-text-secondary">
              <th className="py-1 pr-2 font-medium">Country</th>
              <th className="py-1 pr-2 font-medium">AFU Members</th>
              <th className="py-1 pr-2 font-medium">Seniors (65+, M)</th>
              <th className="py-1 font-medium">Per Million Seniors</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((r) => (
              <tr key={r.country} className="border-t border-border">
                <td className="py-1.5 pr-2">
                  <span className="inline-flex items-center gap-1.5">
                    <span
                      className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
                      style={{ background: theme.regionColors[r.region as RegionName] ?? theme.gridText }}
                    />
                    {r.country}
                  </span>
                </td>
                <td className="py-1.5 pr-2 tabular-nums">{r.afuMembers}</td>
                <td className="py-1.5 pr-2 tabular-nums">{r.pop65M}</td>
                <td className="py-1.5 font-semibold tabular-nums">{r.perMillionSeniors.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
