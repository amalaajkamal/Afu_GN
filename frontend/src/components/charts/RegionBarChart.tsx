import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { useTheme } from "../../theme/ThemeProvider";
import { getMapTheme } from "../../lib/mapTheme";
import type { RegionRow } from "../../hooks/useDashboardData";
import type { RegionName } from "../../types/institution";

interface Props {
  regions: RegionRow[];
  selected: string;
  onSelect: (region: string) => void;
}

export function RegionBarChart({ regions, selected, onSelect }: Props) {
  const { resolvedTheme } = useTheme();
  const theme = getMapTheme(resolvedTheme);
  const sorted = [...regions].sort((a, b) => a.afuInstitutions - b.afuInstitutions);

  return (
    <div>
      <h3 className="mb-1 text-xs font-bold uppercase tracking-wide text-text-secondary">
        Institutions per Region
      </h3>
      <div className="h-52 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={sorted} layout="vertical" margin={{ left: 8, right: 24, top: 4, bottom: 4 }}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="region"
              width={90}
              tick={{ fill: theme.gridText, fontSize: 13 }}
              tickLine={false}
              axisLine={false}
            />
            <Bar
              dataKey="afuInstitutions"
              radius={[0, 6, 6, 0]}
              onClick={(entry) => onSelect((entry as unknown as RegionRow).region)}
              cursor="pointer"
            >
              <LabelList
                dataKey="afuInstitutions"
                position="right"
                style={{ fill: theme.gridText, fontSize: 13, fontWeight: 600 }}
              />
              {sorted.map((r) => {
                const isSel = selected === "Global View" || selected === r.region;
                return (
                  <Cell
                    key={r.region}
                    fill={theme.regionColors[r.region as RegionName] ?? theme.gridText}
                    opacity={isSel ? 1 : 0.3}
                  />
                );
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
