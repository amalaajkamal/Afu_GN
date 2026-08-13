import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
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
  const sorted = [...rows].sort((a, b) => b.perMillionSeniors - a.perMillionSeniors);

  return (
    <div>
      <h3 className="mb-1 text-xs font-bold uppercase tracking-wide text-text-secondary">
        AFU Density per Million Seniors (2025)
      </h3>
      <div className="h-80 w-full overflow-x-auto">
        <div style={{ height: "100%", minWidth: Math.max(640, sorted.length * 46) }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sorted} margin={{ top: 24, right: 8, left: 0, bottom: 70 }}>
              <XAxis
                dataKey="country"
                tick={{ fill: theme.gridText, fontSize: 11 }}
                angle={-45}
                textAnchor="end"
                interval={0}
                axisLine={false}
              />
              <YAxis tick={{ fill: theme.gridText, fontSize: 11 }} axisLine={false} />
              <Tooltip
                formatter={((value: number, _name: unknown, entry: { payload?: DensityRow }) => [
                  `${value.toFixed(2)} per million seniors (${entry?.payload?.afuMembers} institutions, ${entry?.payload?.pop65M}M seniors)`,
                  entry?.payload?.country,
                ]) as never}
                contentStyle={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                  color: "var(--text-primary)",
                  fontSize: 13,
                }}
              />
              <Bar dataKey="perMillionSeniors" radius={[4, 4, 0, 0]}>
                <LabelList
                  dataKey="perMillionSeniors"
                  position="top"
                  formatter={((v: number) => v.toFixed(2)) as never}
                  style={{ fill: theme.gridText, fontSize: 11, fontWeight: 600 }}
                  angle={-45}
                  offset={10}
                />
                {sorted.map((r) => (
                  <Cell key={r.country} fill={theme.regionColors[r.region as RegionName] ?? theme.gridText} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
