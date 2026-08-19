interface KpiCardProps {
  value: string | number;
  label: string;
  accent?: "terracotta" | "clay" | "sage" | "amber" | "rose" | "ocean";
}

const ACCENT_CLASSES: Record<NonNullable<KpiCardProps["accent"]>, string> = {
  terracotta: "border-t-terracotta text-ink-terracotta",
  clay: "border-t-clay text-ink-clay",
  sage: "border-t-sage text-ink-sage",
  amber: "border-t-amber text-ink-amber",
  rose: "border-t-rose text-ink-rose",
  ocean: "border-t-ocean text-ink-ocean",
};

export function KpiCard({ value, label, accent = "terracotta" }: KpiCardProps) {
  const accentClasses = ACCENT_CLASSES[accent];
  return (
    <div
      className={`animate-fade-slide-in flex min-w-[8.5rem] flex-1 flex-col items-center gap-1 rounded-xl border border-t-4 border-border bg-surface px-4 py-3 text-center shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md ${accentClasses}`}
    >
      <span className="tabular-nums text-2xl font-extrabold sm:text-3xl">{value}</span>
      <span className="text-xs font-semibold uppercase tracking-wide text-text-secondary">
        {label}
      </span>
    </div>
  );
}
