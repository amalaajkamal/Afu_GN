import { ChevronDown } from "lucide-react";
import type { BestPractice } from "../../types/staticData";

export function BestPracticeCard({ bp }: { bp: BestPractice }) {
  return (
    <details className="group rounded-xl border border-border bg-surface shadow-sm">
      <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3.5">
        <div className="min-w-0">
          <p className="truncate font-semibold">{bp.title}</p>
          <p className="truncate text-sm text-text-secondary">{bp.university}</p>
        </div>
        <ChevronDown
          size={20}
          className="shrink-0 text-text-secondary transition-transform group-open:rotate-180"
        />
      </summary>
      <div className="grid grid-cols-1 gap-4 border-t border-border px-4 py-4 sm:grid-cols-[2fr_1fr]">
        <div className="space-y-2 text-sm">
          <p>
            <span className="font-semibold">Purpose: </span>
            {bp.purpose || "N/A"}
          </p>
          <p>
            <span className="font-semibold">Outcomes: </span>
            {bp.outcomes || "N/A"}
          </p>
          <p>
            <span className="font-semibold">What makes it unique: </span>
            {bp.unique || "N/A"}
          </p>
        </div>
        <div className="space-y-2 text-sm">
          <p>
            <span className="font-semibold">Principles: </span>
            {bp.principles.map((p) => `P${p}`).join(", ") || "N/A"}
          </p>
          <p>
            <span className="font-semibold">Type: </span>
            {bp.type || "N/A"}
          </p>
          <p>
            <span className="font-semibold">Duration: </span>
            {bp.duration || "N/A"}
          </p>
        </div>
      </div>
    </details>
  );
}
