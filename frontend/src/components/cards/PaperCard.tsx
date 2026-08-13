import { ChevronDown, ExternalLink } from "lucide-react";
import type { Paper } from "../../types/research";

export function PaperCard({ paper }: { paper: Paper }) {
  const link = paper.oa_url || paper.doi || undefined;
  const authorNames = paper.authorships
    .map((a) => a.author_name)
    .filter((n): n is string => Boolean(n));

  return (
    <details className="group rounded-xl border border-border bg-surface shadow-sm">
      <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3.5">
        <div className="min-w-0">
          <p className="truncate font-semibold">{paper.title || "Untitled"}</p>
          <p className="truncate text-sm text-text-secondary">
            {authorNames.slice(0, 3).join(", ")}
            {authorNames.length > 3 ? ", et al." : ""}
            {paper.publication_year ? ` · ${paper.publication_year}` : ""}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <span className="tabular-nums text-sm font-semibold text-ink-terracotta">
            {paper.cited_by_count} citations
          </span>
          <ChevronDown
            size={20}
            className="shrink-0 text-text-secondary transition-transform group-open:rotate-180"
          />
        </div>
      </summary>
      <div className="space-y-2 border-t border-border px-4 py-4 text-sm">
        <p>
          <span className="font-semibold">Venue: </span>
          {paper.venue || "N/A"}
        </p>
        <p>
          <span className="font-semibold">Authors: </span>
          {authorNames.join(", ") || "N/A"}
        </p>
        {link && (
          <a
            href={link}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 font-medium text-ink-terracotta underline-offset-2 hover:underline"
          >
            View paper
            <ExternalLink size={14} strokeWidth={2.25} />
          </a>
        )}
      </div>
    </details>
  );
}
