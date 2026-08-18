import { Bar, BarChart, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { useTheme } from "../../theme/ThemeProvider";
import { getMapTheme } from "../../lib/mapTheme";
import type { BestPractice } from "../../types/staticData";

export function AudienceBarChart({ bestPractices }: { bestPractices: BestPractice[] }) {
  const { resolvedTheme } = useTheme();
  const theme = getMapTheme(resolvedTheme);

  const counts = new Map<string, number>();
  for (const bp of bestPractices) {
    for (const audience of bp.audience) {
      counts.set(audience, (counts.get(audience) ?? 0) + 1);
    }
  }
  const data = [...counts.entries()]
    .map(([audience, count]) => ({ audience, count }))
    .sort((a, b) => a.count - b.count);

  return (
    <div>
      <h3 className="mb-1 text-xs font-bold uppercase tracking-wide text-text-secondary">
        Who Do Activities Target?
      </h3>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 8, right: 30, top: 4, bottom: 4 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="audience"
              width={210}
              tick={{ fill: theme.gridText, fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <Bar dataKey="count" radius={[0, 6, 6, 0]} fill="var(--color-terracotta)" barSize={16}>
              <LabelList
                dataKey="count"
                position="right"
                style={{ fill: theme.gridText, fontSize: 12, fontWeight: 600 }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
