import { Bar, BarChart, LabelList, Legend, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { useTheme } from "../../theme/ThemeProvider";
import { getMapTheme } from "../../lib/mapTheme";
import type { RegionRow } from "../../hooks/useDashboardData";

export function CoverageStackedBarChart({ regions }: { regions: RegionRow[] }) {
  const { resolvedTheme } = useTheme();
  const theme = getMapTheme(resolvedTheme);
  // Raw counts skew regions with very different total-country counts (e.g.
  // Europe's 44 vs Oceania's 14) into looking similarly "full" -- normalizing
  // to the same coverage-% split used in the table below surfaces the actual
  // gap at a glance instead of just relative bar length.
  const data = [...regions]
    .sort((a, b) => b.countryCoveragePct - a.countryCoveragePct)
    .map((r) => ({
      region: r.region,
      inAfuPct: r.countryCoveragePct,
      missingPct: Math.round((100 - r.countryCoveragePct) * 10) / 10,
    }));

  return (
    <div>
      <h3 className="mb-1 text-xs font-bold uppercase tracking-wide text-text-secondary">
        Country Coverage Gap by Region
      </h3>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
            <XAxis
              type="number"
              domain={[0, 100]}
              tickFormatter={((v: number) => `${v}%`) as never}
              tick={{ fill: theme.gridText, fontSize: 12 }}
              axisLine={false}
            />
            <YAxis
              type="category"
              dataKey="region"
              width={100}
              tick={{ fill: theme.gridText, fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <Legend wrapperStyle={{ fontSize: 12, color: theme.gridText }} />
            <Bar
              dataKey="inAfuPct"
              name="In AFU GN"
              stackId="coverage"
              fill="var(--color-terracotta)"
              radius={[6, 0, 0, 6]}
            >
              <LabelList
                dataKey="inAfuPct"
                position="inside"
                formatter={((v: number) => `${v}%`) as never}
                style={{ fill: "#fff", fontSize: 11, fontWeight: 600 }}
              />
            </Bar>
            <Bar
              dataKey="missingPct"
              name="Not in AFU GN"
              stackId="coverage"
              fill="var(--color-terracotta-soft)"
              radius={[0, 6, 6, 0]}
            >
              <LabelList
                dataKey="missingPct"
                position="inside"
                formatter={((v: number) => `${v}%`) as never}
                style={{ fill: theme.gridText, fontSize: 11 }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
