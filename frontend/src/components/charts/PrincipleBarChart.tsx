import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";
import { useTheme } from "../../theme/ThemeProvider";
import { getMapTheme } from "../../lib/mapTheme";
import type { Principle } from "../../types/staticData";

export function PrincipleBarChart({ principles, height = 380 }: { principles: Principle[]; height?: number }) {
  const { resolvedTheme } = useTheme();
  const theme = getMapTheme(resolvedTheme);
  const sorted = [...principles].sort((a, b) => a.pct - b.pct);
  const maxPct = Math.max(88, ...sorted.map((p) => p.pct));

  return (
    <div>
      <h3 className="mb-1 text-xs font-bold uppercase tracking-wide text-text-secondary">
        Principle Citation Frequency (% of submissions)
      </h3>
      <div className="w-full" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={sorted} layout="vertical" margin={{ left: 8, right: 40, top: 4, bottom: 4 }}>
            <XAxis type="number" domain={[0, Math.ceil(maxPct * 1.15)]} hide />
            <YAxis
              type="category"
              dataKey="shortLabel"
              width={190}
              tick={{ fill: theme.gridText, fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <ReferenceLine x={50} stroke={theme.gridText} strokeDasharray="3 3" />
            <Bar dataKey="pct" radius={[0, 6, 6, 0]} barSize={16}>
              <LabelList
                dataKey="pct"
                position="right"
                formatter={((v: number) => `${v}%`) as never}
                style={{ fill: theme.gridText, fontSize: 12, fontWeight: 600 }}
              />
              {sorted.map((p) => (
                <Cell key={p.principleNumber} fill={theme.gapColors[p.gapFlag]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <details className="mt-1 text-sm text-text-secondary">
        <summary className="cursor-pointer select-none">View as table</summary>
        <table className="mt-2 w-full text-left text-sm">
          <thead>
            <tr className="text-text-secondary">
              <th className="py-1 pr-2 font-medium">Principle</th>
              <th className="py-1 pr-2 font-medium">Citation %</th>
              <th className="py-1 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {principles.map((p) => (
              <tr key={p.principleNumber} className="border-t border-border">
                <td className="py-1 pr-2">{p.shortLabel.replace(/\n/g, " ")}</td>
                <td className="py-1 pr-2 tabular-nums">{p.pct}%</td>
                <td className="py-1">{p.gapFlag}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
