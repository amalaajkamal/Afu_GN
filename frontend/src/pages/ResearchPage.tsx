import { useMemo, useState } from "react";
import { BookOpenText } from "lucide-react";
import { PageHeader } from "../components/layout/PageHeader";
import { KpiCard } from "../components/cards/KpiCard";
import { PaperCard } from "../components/cards/PaperCard";
import { MultiSelect } from "../components/filters/MultiSelect";
import { useResearchMeta, useResearchPapers, useResearchers } from "../hooks/useResearch";

export function ResearchPage() {
  const { data: meta, isLoading: metaLoading } = useResearchMeta();
  const { data: papersData, isLoading: papersLoading } = useResearchPapers();
  const { data: researchersData, isLoading: researchersLoading } = useResearchers(25);
  const [yearFilter, setYearFilter] = useState<string[]>([]);

  const papers = papersData?.results ?? [];
  const researchers = researchersData?.results ?? [];

  const yearOptions = useMemo(
    () =>
      [...new Set(papers.map((p) => p.publication_year).filter((y): y is number => y != null))]
        .sort((a, b) => b - a)
        .map((y) => ({ value: String(y), label: String(y) })),
    [papers],
  );

  const filteredPapers = useMemo(() => {
    if (yearFilter.length === 0) return papers;
    return papers.filter((p) => p.publication_year != null && yearFilter.includes(String(p.publication_year)));
  }, [papers, yearFilter]);

  const isLoading = metaLoading || papersLoading || researchersLoading;
  const totalCitations = papers.reduce((sum, p) => sum + p.cited_by_count, 0);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader
        title="Research Papers & Researchers"
        subtitle="AFU-related research indexed via OpenAlex, ranked by citation impact"
        icon={<BookOpenText size={20} strokeWidth={2.25} />}
      />

      {isLoading ? (
        <div className="h-24 shrink-0 animate-pulse rounded-xl bg-surface-muted" />
      ) : (
        <>
          <div className="mb-3 flex shrink-0 flex-wrap gap-2">
            <KpiCard value={meta?.total_papers ?? 0} label="Papers" accent="terracotta" />
            <KpiCard value={meta?.total_researchers ?? 0} label="Researchers" accent="ocean" />
            <KpiCard value={totalCitations} label="Total Citations" accent="sage" />
          </div>

          <div className="mb-3 grid shrink-0 grid-cols-1 gap-3 sm:max-w-xs">
            <MultiSelect
              label="Filter by Year"
              options={yearOptions}
              selected={yearFilter}
              onChange={setYearFilter}
            />
          </div>

          <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 overflow-hidden lg:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)]">
            <div className="min-h-0 overflow-y-auto rounded-xl border border-border bg-surface p-4 shadow-sm">
              <h3 className="mb-3 text-sm font-bold uppercase tracking-wide text-text-secondary">
                Top Researchers
              </h3>
              <div className="space-y-1">
                {researchers.map((r, i) => (
                  <div
                    key={r.id}
                    className="flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-surface-muted"
                  >
                    <span className="w-6 shrink-0 tabular-nums text-sm font-semibold text-text-secondary">
                      {i + 1}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-semibold">{r.name}</p>
                      <p className="truncate text-xs text-text-secondary">
                        {r.institutions.join(", ") || "Unknown institution"} · {r.paper_count} paper
                        {r.paper_count === 1 ? "" : "s"}
                      </p>
                    </div>
                    <span className="shrink-0 tabular-nums text-sm font-semibold text-ink-terracotta">
                      {r.total_citations}
                    </span>
                  </div>
                ))}
                {researchers.length === 0 && (
                  <p className="text-sm text-text-secondary">No researchers found.</p>
                )}
              </div>
            </div>

            <div className="min-h-0 space-y-3 overflow-y-auto pr-1">
              <p className="text-sm font-medium text-text-secondary">
                Showing {filteredPapers.length} of {papers.length} papers
              </p>
              {filteredPapers.map((p, i) => (
                <PaperCard key={p.id ?? i} paper={p} />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
