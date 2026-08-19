import { NavLink, Outlet } from "react-router-dom";
import { NAV_ITEMS } from "./navConfig";
import { ThemeToggle } from "./ThemeToggle";

function navLinkClasses(isActive: boolean) {
  return [
    "flex items-center gap-3 rounded-full px-4 py-2.5 text-base font-medium transition-colors",
    isActive
      ? "bg-terracotta-soft text-ink-terracotta"
      : "text-text-secondary hover:bg-surface-muted hover:text-text-primary",
  ].join(" ");
}

export function AppShell() {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-bg text-text-primary">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-full focus:bg-surface focus:px-4 focus:py-2 focus:shadow-md"
      >
        Skip to content
      </a>

      {/* ── Top bar ─────────────────────────────────────────────────────── */}
      <header className="shrink-0 border-b border-border bg-bg/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-2.5">
            <div className="leading-tight">
              <h1 className="text-lg font-bold sm:text-xl">AFU Global Network</h1>
              <p className="hidden text-sm text-text-secondary sm:block">
                Implementation Gap Dashboard
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* ── Body (everything below the navbar fills the rest of the viewport) ── */}
      <div className="mx-auto flex min-h-0 w-full max-w-7xl flex-1 gap-6 px-4 py-4 sm:px-6">
        {/* ── Desktop sidebar nav ───────────────────────────────────────── */}
        <nav
          aria-label="Main navigation"
          className="hidden h-fit w-64 shrink-0 flex-col gap-1 md:flex"
        >
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) => navLinkClasses(isActive)}
            >
              <item.icon size={20} strokeWidth={2} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* ── Page content ──────────────────────────────────────────────── */}
        <main id="main-content" className="min-h-0 min-w-0 flex-1 overflow-hidden">
          <Outlet />
        </main>
      </div>

      {/* ── Mobile bottom tab bar ─────────────────────────────────────────── */}
      <nav
        aria-label="Main navigation"
        className="flex shrink-0 border-t border-border bg-surface/95 backdrop-blur md:hidden"
      >
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              [
                "flex flex-1 flex-col items-center gap-1 py-2.5 text-xs font-medium transition-colors",
                isActive ? "text-ink-terracotta" : "text-text-secondary",
              ].join(" ")
            }
          >
            <item.icon size={22} strokeWidth={2} />
            {item.shortLabel}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
