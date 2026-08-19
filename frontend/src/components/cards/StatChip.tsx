interface StatChipProps {
  value: string | number;
  label: string;
  accent?: "terracotta" | "clay" | "sage" | "amber" | "rose" | "ocean";
}

const DOT_CLASSES: Record<NonNullable<StatChipProps["accent"]>, string> = {
  terracotta: "bg-terracotta",
  clay: "bg-clay",
  sage: "bg-sage",
  amber: "bg-amber",
  rose: "bg-rose",
  ocean: "bg-ocean",
};

/** Compact inline stat, for contextual/secondary numbers that shouldn't
 * compete with KpiCard's large headline treatment (e.g. drill-down details
 * shown alongside the region tabs they're scoped to). */
export function StatChip({ value, label, accent = "terracotta" }: StatChipProps) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-surface-muted px-3 py-1.5 text-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-sm">
      <span className={`h-2 w-2 shrink-0 rounded-full ${DOT_CLASSES[accent]}`} aria-hidden="true" />
      <span className="font-extrabold tabular-nums text-text-primary">{value}</span>
      <span className="text-xs font-medium uppercase tracking-wide text-text-secondary">{label}</span>
    </span>
  );
}
