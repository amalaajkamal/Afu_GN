import { Moon, Sun } from "lucide-react";
import { useTheme } from "../../theme/ThemeProvider";

export function ThemeToggle() {
  const { resolvedTheme, toggle } = useTheme();
  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-text-primary transition-colors hover:bg-surface-muted"
    >
      {isDark ? <Sun size={20} strokeWidth={2} /> : <Moon size={20} strokeWidth={2} />}
    </button>
  );
}
