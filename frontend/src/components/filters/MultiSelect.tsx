import { useRef, useState } from "react";
import { ChevronDown, X } from "lucide-react";

interface Option {
  value: string;
  label: string;
}

interface Props {
  label: string;
  options: Option[];
  selected: string[];
  onChange: (values: string[]) => void;
}

export function MultiSelect({ label, options, selected, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  function toggle(value: string) {
    onChange(selected.includes(value) ? selected.filter((v) => v !== value) : [...selected, value]);
  }

  return (
    <div className="relative" ref={containerRef}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="listbox"
        className="flex min-h-11 w-full items-center justify-between gap-2 rounded-lg border border-border bg-surface px-3.5 py-2.5 text-left text-base"
      >
        <span className="truncate">
          {label}
          {selected.length > 0 && (
            <span className="ml-1.5 rounded-full bg-terracotta-soft px-2 py-0.5 text-xs font-semibold text-ink-terracotta">
              {selected.length}
            </span>
          )}
        </span>
        <ChevronDown size={18} className="shrink-0 text-text-secondary" />
      </button>

      {open && (
        <>
          <button
            type="button"
            aria-label="Close filter menu"
            className="fixed inset-0 z-40 cursor-default"
            onClick={() => setOpen(false)}
          />
          <div
            role="listbox"
            aria-label={label}
            className="absolute z-50 mt-1.5 max-h-72 w-full min-w-[16rem] overflow-y-auto rounded-lg border border-border bg-surface p-2 shadow-md"
          >
            {selected.length > 0 && (
              <button
                type="button"
                onClick={() => onChange([])}
                className="mb-1 flex w-full items-center gap-1.5 rounded-md px-2 py-1.5 text-sm font-medium text-text-secondary hover:bg-surface-muted"
              >
                <X size={14} /> Clear selection
              </button>
            )}
            {options.map((opt) => (
              <label
                key={opt.value}
                className="flex min-h-11 cursor-pointer items-center gap-2.5 rounded-md px-2 py-1.5 text-base hover:bg-surface-muted"
              >
                <input
                  type="checkbox"
                  checked={selected.includes(opt.value)}
                  onChange={() => toggle(opt.value)}
                  className="h-5 w-5 accent-[var(--color-terracotta)]"
                />
                {opt.label}
              </label>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
