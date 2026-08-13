import { Bar, BarChart, LabelList, Legend, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { useTheme } from "../../theme/ThemeProvider";
import { getMapTheme } from "../../lib/mapTheme";
import type { RegionRow } from "../../hooks/useDashboardData";

export function CoverageStackedBarChart({ regions }: { regions: RegionRow[] }) {
  const { resolvedTheme } = useTheme();
  const theme = getMapTheme(resolvedTheme);

  return (
    <div>
      <h3 className="mb-1 text-xs font-bold uppercase tracking-wide text-text-secondary">
        Country Coverage Gap by Region
      </h3>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={regions} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
            <XAxis type="number" tick={{ fill: theme.gridText, fontSize: 12 }} axisLine={false} />
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
              dataKey="countriesInAfu"
              name="In AFU GN"
              stackId="coverage"
              fill="var(--color-terracotta)"
              radius={[6, 0, 0, 6]}
            >
              <LabelList dataKey="countriesInAfu" position="inside" style={{ fill: "#fff", fontSize: 11 }} />
            </Bar>
            <Bar
              dataKey="countriesMissing"
              name="Not in AFU GN"
              stackId="coverage"
              fill="var(--color-terracotta-soft)"
              radius={[0, 6, 6, 0]}
            >
              <LabelList
                dataKey="countriesMissing"
                position="inside"
                style={{ fill: theme.gridText, fontSize: 11 }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
