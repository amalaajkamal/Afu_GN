import { useMemo, useState } from "react";
import { HeartHandshake, Loader2, Search } from "lucide-react";
import { PageHeader } from "../components/layout/PageHeader";
import { KpiCard } from "../components/cards/KpiCard";
import { PaperCard } from "../components/cards/PaperCard";
import { MultiSelect } from "../components/filters/MultiSelect";
import {
  useSocialIsolationMeta,
  useSocialIsolationPapers,
  useSocialIsolationResearchers,
} from "../hooks/useSocialIsolationResearch";
import { useLongWait } from "../hooks/useLongWait";

export function SocialIsolationResearchPage() {
  const { data: meta, isLoading: metaLoading } = useSocialIsolationMeta();
  const { data: papersData, isLoading: papersLoading } = useSocialIsolationPapers();
  const { data: researchersData, isLoading: researchersLoading } = useSocialIsolationResearchers(25);
  const [yearFilter, setYearFilter] = useState<string[]>([]);
  const [authorFilter, setAuthorFilter] = useState("");

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
    const authorQuery = authorFilter.trim().toLowerCase();
    return papers.filter((p) => {
      if (yearFilter.length > 0) {
        if (p.publication_year == null || !yearFilter.includes(String(p.publication_year))) return false;
      }
      if (authorQuery) {
        const hasMatch = p.authorships.some((a) =>
          a.author_name?.toLowerCase().includes(authorQuery),
        );
        if (!hasMatch) return false;
      }
      return true;
    });
  }, [papers, yearFilter, authorFilter]);

  const isLoading = metaLoading || papersLoading || researchersLoading;
  // See ResearchPage.tsx's isBootstrapping -- same non-blocking cold-cache
  // backend behavior, same fix (not keyed off isFetching, which flickers
  // false between polls and would flash an empty "0 papers" list).
  const isBootstrapping = !isLoading && papers.length === 0;
  const waitedLong = useLongWait(isBootstrapping);
  // Server-computed and cached -- see ResearchPage.tsx's totalCitations.
  const totalCitations = meta?.total_citations ?? 0;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader
        title="Social Isolation Research & Researchers"
        subtitle="Social isolation & loneliness research among older adults, indexed via OpenAlex, ranked by citation impact"
        icon={<HeartHandshake size={20} strokeWidth={2.25} />}
      />

      {isLoading ? (
        <div className="h-24 shrink-0 animate-pulse rounded-xl bg-surface-muted" />
      ) : isBootstrapping ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center">
          <Loader2 size={28} className="animate-spin text-ink-terracotta" />
          <p className="font-semibold">Fetching research papers from the backend…</p>
          <p className="max-w-sm text-sm text-text-secondary">
            The first request after a while takes up to a minute to pull fresh results from
            OpenAlex. It's cached after that, so this page will load instantly for a while.
          </p>
          {waitedLong && (
            <p className="max-w-sm text-sm text-text-secondary">
              Still waiting — OpenAlex (the upstream data source) may be temporarily rate-limited.
              This page will pick up the results automatically once it's back; no need to reload.
            </p>
          )}
        </div>
      ) : (
        <>
          <div className="mb-3 flex shrink-0 flex-wrap gap-2">
            <KpiCard value={meta?.total_papers ?? 0} label="Papers" accent="terracotta" />
            <KpiCard value={meta?.total_researchers ?? 0} label="Researchers" accent="ocean" />
            <KpiCard value={totalCitations} label="Total Citations" accent="sage" />
          </div>

          <div className="mb-3 grid shrink-0 grid-cols-1 gap-3 sm:max-w-xl sm:grid-cols-2">
            <MultiSelect
              label="Filter by Year"
              options={yearOptions}
              selected={yearFilter}
              onChange={setYearFilter}
            />
            <div className="relative">
              <Search
                size={18}
                className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-text-secondary"
              />
              <input
                type="text"
                value={authorFilter}
                onChange={(e) => setAuthorFilter(e.target.value)}
                placeholder="Search by author or co-author"
                aria-label="Search by author or co-author"
                className="min-h-11 w-full rounded-lg border border-border bg-surface py-2.5 pl-10 pr-3.5 text-base placeholder:text-text-secondary"
              />
            </div>
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
