import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { useTheme } from "../../theme/ThemeProvider";
import { getMapTheme } from "../../lib/mapTheme";
import type { RegionRow } from "../../hooks/useDashboardData";
import type { RegionName } from "../../types/institution";

interface Props {
  regions: RegionRow[];
  selected: string;
  onSelect: (region: string) => void;
}

export function RegionDonutChart({ regions, selected, onSelect }: Props) {
  const { resolvedTheme } = useTheme();
  const theme = getMapTheme(resolvedTheme);
  const total = regions.reduce((s, r) => s + r.afuInstitutions, 0);

  return (
    <div>
      <h3 className="mb-1 text-xs font-bold uppercase tracking-wide text-text-secondary">
        Regional Share
      </h3>
      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={regions}
              dataKey="afuInstitutions"
              nameKey="region"
              innerRadius="55%"
              outerRadius="82%"
              paddingAngle={2}
              onClick={(entry) => onSelect((entry as unknown as RegionRow).region)}
              cursor="pointer"
            >
              {regions.map((r) => {
                const isSel = selected === "Global View" || selected === r.region;
                return (
                  <Cell
                    key={r.region}
                    fill={theme.regionColors[r.region as RegionName] ?? theme.gridText}
                    opacity={isSel ? 1 : 0.25}
                    stroke={theme.bg}
                    strokeWidth={2}
                  />
                );
              })}
            </Pie>
            <Tooltip
              formatter={((value: number, _name: unknown, entry: { payload?: RegionRow }) => [
                `${value} institutions (${total ? Math.round((value / total) * 100) : 0}%)`,
                entry?.payload?.region,
              ]) as never}
              contentStyle={{
                background: "var(--surface)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                color: "var(--text-primary)",
                fontSize: 14,
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <details className="mt-1 text-sm text-text-secondary">
        <summary className="cursor-pointer select-none">View as table</summary>
        <table className="mt-2 w-full text-left text-sm">
          <thead>
            <tr className="text-text-secondary">
              <th className="py-1 pr-2 font-medium">Region</th>
              <th className="py-1 font-medium">Institutions</th>
            </tr>
          </thead>
          <tbody>
            {regions.map((r) => (
              <tr key={r.region} className="border-t border-border">
                <td className="py-1 pr-2">{r.region}</td>
                <td className="py-1 tabular-nums">{r.afuInstitutions}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
