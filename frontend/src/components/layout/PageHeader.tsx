import type { ReactNode } from "react";

export function PageHeader({
  title,
  subtitle,
  icon,
  actions,
}: {
  title: string;
  subtitle?: string;
  icon?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-3 flex shrink-0 items-start justify-between gap-3">
      <div className="flex min-w-0 items-start gap-3">
        {icon && (
          <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-terracotta-soft text-ink-terracotta">
            {icon}
          </span>
        )}
        <div className="min-w-0">
          <h2 className="text-xl font-bold sm:text-2xl">{title}</h2>
          {subtitle && <p className="mt-0.5 truncate text-sm text-text-secondary">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="shrink-0">{actions}</div>}
    </div>
  );
}
