import { useTheme } from "../../theme/ThemeProvider";
import { getMapTheme } from "../../lib/mapTheme";
import type { Principle } from "../../types/staticData";

export function PrincipleTable({ principles, title }: { principles: Principle[]; title?: string }) {
  const { resolvedTheme } = useTheme();
  const theme = getMapTheme(resolvedTheme);

  return (
    <div>
      {title && (
        <h3 className="mb-2 text-xs font-bold uppercase tracking-wide text-text-secondary">{title}</h3>
      )}
      <table className="w-full text-left text-sm">
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
              <td className="py-1">
                <span className="inline-flex items-center gap-1.5">
                  <span
                    aria-hidden="true"
                    className="inline-block h-2 w-2 shrink-0 rounded-full"
                    style={{ background: theme.gapColors[p.gapFlag] }}
                  />
                  {p.gapFlag}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
