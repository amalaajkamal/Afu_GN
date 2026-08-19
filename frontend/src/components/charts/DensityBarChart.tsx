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

const REGION_ORDER: RegionName[] = ["North America", "Europe", "Asia", "Oceania", "South America"];
const ROW_HEIGHT = 24;
const MIN_HEIGHT = 320;

export function DensityBarChart({ rows }: { rows: DensityRow[] }) {
  const { resolvedTheme } = useTheme();
  const theme = getMapTheme(resolvedTheme);
  const sorted = [...rows].sort((a, b) => b.perMillionSeniors - a.perMillionSeniors);
  const maxVal = Math.max(1, ...sorted.map((r) => r.perMillionSeniors));

  return (
    <div>
      <h3 className="mb-1 text-xs font-bold uppercase tracking-wide text-text-secondary">
        AFU Density per Million Seniors (2025)
      </h3>
      <div className="mb-2 flex flex-wrap gap-x-3 gap-y-1 text-xs text-text-secondary">
        {REGION_ORDER.map((region) => (
          <span key={region} className="inline-flex items-center gap-1.5">
            <span
              className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ background: theme.regionColors[region] }}
            />
            {region}
          </span>
        ))}
      </div>
      <div className="w-full" style={{ height: Math.max(MIN_HEIGHT, sorted.length * ROW_HEIGHT) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={sorted} layout="vertical" margin={{ left: 8, right: 44, top: 4, bottom: 4 }}>
            <XAxis type="number" domain={[0, Math.ceil(maxVal * 1.15)]} hide />
            <YAxis
              type="category"
              dataKey="country"
              width={130}
              tick={{ fill: theme.gridText, fontSize: 11 }}
              tickLine={false}
              axisLine={false}
            />
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
            <Bar dataKey="perMillionSeniors" radius={[0, 4, 4, 0]} barSize={12}>
              <LabelList
                dataKey="perMillionSeniors"
                position="right"
                formatter={((v: number) => v.toFixed(2)) as never}
                style={{ fill: theme.gridText, fontSize: 11, fontWeight: 600 }}
              />
              {sorted.map((r) => (
                <Cell key={r.country} fill={theme.regionColors[r.region as RegionName] ?? theme.gridText} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
