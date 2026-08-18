import type { ReactNode } from "react";
import { Info, TriangleAlert } from "lucide-react";

interface Props {
  tone?: "warning" | "info";
  children: ReactNode;
}

export function Callout({ tone = "warning", children }: Props) {
  const isWarning = tone === "warning";
  return (
    <div
      className={[
        "flex items-start gap-2.5 rounded-lg border px-3.5 py-3 text-sm",
        isWarning ? "border-rose/40 bg-rose/10 text-text-primary" : "border-ocean/40 bg-ocean/10 text-text-primary",
      ].join(" ")}
    >
      {isWarning ? (
        <TriangleAlert size={18} strokeWidth={2.25} className="mt-0.5 shrink-0 text-ink-rose" />
      ) : (
        <Info size={18} strokeWidth={2.25} className="mt-0.5 shrink-0 text-ink-ocean" />
      )}
      <div>{children}</div>
    </div>
  );
}
